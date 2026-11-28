using System.IO;
using System.Net.Http;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace PilouBureau;

// La présence de Pilou au quotidien (docs/PRESENCE.md) sur le PC : petits mots rares (au plus trois par jour, à des
// moments calmes, par la retenue commune), complicité qui grandit, dates fêtées une fois, journal du jour, prénom
// demandé une seule fois. Le moteur est dans Presence.cs ; ici, ce que l'overlay observe et montre.
// Tout est protégé : une erreur coupe la présence au quotidien (Pilou continue comme avant), jamais Pilou lui-même.
public sealed partial class FenetrePilou
{
    private EtatPresence? _presence;
    private bool _presenceDemo;
    private int _presenceErreurs;
    private double _presenceVu = -1e12, _presenceEcrit = -1e12;
    private bool _presenceChange, _presenceUrgent;
    private bool _visiteVue, _expeditionVue;
    private int _filVu = -1;
    private HashSet<string>? _finiesVues;
    private string _presJour = "";
    private string _presEnvoyee = "";
    private double _presEnvoi = -1e12, _presLu = -1e12, _presPause = -1e12;
    private bool _presEnvoiEnCours, _presLectureEnCours;
    private FenetreJournal? _fenetreJournal;
    private DispatcherTimer? _essaiMots;

    private bool PresenceCoupee => _presenceErreurs >= 3;

    private void Quotidien(Action a)
    {
        if (PresenceCoupee) return;
        try
        {
            a();
        }
        catch (Exception e) when (e is not OutOfMemoryException)
        {
            _presenceErreurs++;
            System.Diagnostics.Debug.WriteLine($"Présence : {e}");
        }
    }

    private string CheminPresence => Path.Combine(_dossier, "presence.txt");

    internal EtatPresence Pres
    {
        get
        {
            if (_presence is not null) return _presence;
            if (_demo) _presence = PresenceDemo();
            else
            {
                try
                {
                    _presence = File.Exists(CheminPresence) ? EtatPresence.Lire(File.ReadAllText(CheminPresence, Encoding.UTF8)) : new EtatPresence();
                }
                catch (Exception e) when (e is IOException or UnauthorizedAccessException)
                {
                    _presence = new EtatPresence();
                }
                _presence.Moi.Id = IdAppareil;
                _presence.Moi.Sorte = "pc";
            }
            return _presence;
        }
    }

    private void EcrirePresence()
    {
        if (_presence is null || _demo || _presenceDemo) return;
        try
        {
            Directory.CreateDirectory(_dossier);
            var tmp = CheminPresence + ".tmp";
            File.WriteAllText(tmp, _presence.Texte(), new UTF8Encoding(false));
            File.Move(tmp, CheminPresence, true);
            _presenceChange = false;
            _presenceEcrit = Maintenant;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // gardé en mémoire, réécrit au prochain passage
        }
    }

    // ---- Ce qui s'est passé (faits du jour pour le journal, gestes pour la complicité)

    // Un fait du jour (et le compteur de complicité qui va avec : caresses, soins, jeux). Rien en démonstration.
    private void Vecu(Action<FaitsDuJour> modif, string compteur = "", int n = 1) => Quotidien(() =>
    {
        if (_demo || _presenceDemo) return;
        var e = Pres;
        var now = DateTime.Now;
        if (e.JournalActif) modif(e.Aujourdhui(Presence.JourTexte(now)));
        if (compteur != "") e.Ajouter(compteur, n, now);
        else e.Marquer(Presence.Jour(now));
        _presenceChange = true;
    });

    private void VecuPrise(Prise p) => Vecu(f =>
    {
        f.Pc++;
        var nom = Presence.AvecArticle(p.Id, p.Nom);
        if (f.Px == "" || (int)p.Rarete > f.Pq || ((int)p.Rarete == f.Pq && string.CompareOrdinal(nom, f.Px) < 0)) (f.Px, f.Pq) = (nom, (int)p.Rarete);
    });

    private void VecuPlat(string id, string nom, bool invente) => Vecu(f =>
    {
        f.Cu++;
        if (!invente && f.Cx == "") f.Cx = Presence.AvecArticle(id, nom);
    });

    private void VecuMetier(string nom, int grade) => Vecu(f =>
    {
        if (grade > f.Mg || f.Mo == "") (f.Mo, f.Mg) = (Presence.Propre(nom), grade);
    });

    // ---- Toutes les 2 secondes (depuis Lire)

    private void SuivreQuotidien() => Quotidien(() =>
    {
        var t = Maintenant;
        if (t - _presenceVu < 2000) return;
        double dt = _presenceVu < 0 ? 0 : Math.Clamp((t - _presenceVu) / 1000.0, 0, 5);
        _presenceVu = t;
        if (_demo || _presenceDemo) return;
        var e = Pres;
        var now = DateTime.Now;
        long epoque = (long)Epoque;
        var jour = Presence.JourTexte(now);
        int auj = Presence.Jour(now);
        if (jour != _presJour)
        {
            _presJour = jour;
            e.Compacter(auj);
            _presenceChange = true;
        }
        bool present = _inactif < 60_000;
        // Le temps passé ensemble : la personne est là, et Pilou est à l'écran.
        if (present && IsVisible && !_discret && t >= _cacheJusque)
        {
            e.SecondesEnsemble += dt;
            if (e.SecondesEnsemble >= 60)
            {
                int m = (int)(e.SecondesEnsemble / 60);
                e.SecondesEnsemble -= m * 60;
                e.Ajouter("minutes", m, now);
                _presenceChange = true;
            }
        }
        if (e.JournalActif) FaitsDuQuotidien(e, jour, now, dt, present);
        Cadences.Observer(e.Cadence, epoque, now, present);
        if (Cadences.Pret(e.Cadence, epoque, e.Parle, CalmePourParler) is { } moment) Parler(moment, now, epoque);
        if (_presenceChange && t - _presenceEcrit > 60_000) EcrirePresence();
        PublierPresence(epoque, auj);
        LirePresence(epoque);
    });

    private static readonly HashSet<string> ActivitesTravail = new(Vivacite.Travail.Append("visio"));

    private void FaitsDuQuotidien(EtatPresence e, string jour, DateTime now, double dt, bool present)
    {
        if (e.ActJour != jour)
        {
            e.ActJour = jour;
            e.ActSec.Clear();
        }
        if (dt > 0 && (present || _activite is "video" or "musique" or "visio"))
        {
            var a = _activite is "" or "nuit" ? "autre" : _activite;
            e.ActSec[a] = e.ActSec.GetValueOrDefault(a) + dt;
        }
        var f = e.Aujourdhui(jour);
        f.Mn = Math.Max(f.Mn, (int)(e.ActSec.Values.Sum() / 60));
        f.Tv = Math.Max(f.Tv, (int)(e.ActSec.Where(kv => ActivitesTravail.Contains(kv.Key)).Sum(kv => kv.Value) / 60));
        if (e.ActSec.Where(kv => kv.Key != "autre").OrderByDescending(kv => kv.Value).ThenBy(kv => kv.Key, StringComparer.Ordinal)
                .FirstOrDefault() is { Key: not null } top && (int)(top.Value / 60) >= f.Am)
            (f.Ac, f.Am) = (top.Key, (int)(top.Value / 60));
        if (present && now.Hour >= 21) f.Ta = Math.Max(f.Ta, now.Hour * 60 + now.Minute);
        if (MeteoDuJour() is { Length: > 0 } me) f.Me = FaitsDuJour.Fusion(f, new FaitsDuJour { Me = me }).Me;
        // Visites et expéditions : un départ vu en direct.
        bool visite = _visites.Occupe;
        if (visite && !_visiteVue) f.Vi++;
        _visiteVue = visite;
        bool exp = Exp.Courante is not null;
        if (exp && !_expeditionVue && Expeditions.Trouver(Exp.Courante!.Lieu) is { } lieu) f.Ex = Presence.Propre(lieu.Nom);
        _expeditionVue = exp;
        // Campagnes : un message de Pilou de plus, une campagne finie (comptée aussi pour la complicité).
        var k = _profil.CarnetCampagnes;
        if (_filVu >= 0 && k.Fil.Count > _filVu) f.Ce += k.Fil.Count - _filVu;
        _filVu = k.Fil.Count;
        var finies = k.Historique.Where(kv => kv.Value.Finie > 0).Select(kv => kv.Key).ToList();
        foreach (var id in finies)
        {
            if (e.Moi.Finies.Add(Presence.Propre(id))) _presenceChange = true;
            if (_finiesVues is not null && !_finiesVues.Contains(id) && Campagnes.Charger(id) is { } c) f.Cf = Presence.Propre(c.Titre);
        }
        _finiesVues = finies.ToHashSet();
    }

    private string MeteoDuJour()
    {
        if (_essaiMeteo != "") return _essaiMeteo;
        if (Meteo.Courante is not { } m || _registre?.Trouver("meteo") is not { } c || !_registre.Actif(c)) return "";
        return m.Etat;
    }

    // Les moments où un petit mot peut partir : personne ne tape, rien n'est caché, aucune IA n'attend, pas de jeu,
    // de visite, d'expédition ni de campagne en cours, pas d'autre phrase à l'écran, et la retenue commune le permet.
    private bool CalmePourParler =>
        !_demo && !EnSaisie && !_discret && !_attend && !CampagneOccupe && !_visites.Occupe && !EnExpedition && _jeuEnCours == Jeu.Aucun
        && !_attrape && !GesteEnCours && IsVisible && Maintenant >= _cacheJusque && Maintenant >= _messageJusque && !_dortBureau
        && Dosage.Libre(Maintenant, EnSaisie);

    // Un mot est-il en attente (Pilou va dire bonjour) ? Le réveil ne dit alors pas « bien dormi ».
    private bool MotEnAttente => !PresenceCoupee && _presence is { Cadence.Attente: "premier" or "retour" };

    private string NomVariante(int stade) => _profil.Evolution.Variantes.TryGetValue(stade, out var v) && v is "calin" or "espiegle" ? v : "";

    private string ObjetPorte(string jour)
    {
        var portes = EquipeCourant().Where(kv => kv.Value != "" && PilouBureau.Boutique.SurPilou(kv.Key))
            .Select(kv => PilouBureau.Boutique.Trouver(kv.Value)?.Nom ?? "").Where(n => n != "").OrderBy(n => n, StringComparer.Ordinal).ToList();
        return portes.Count == 0 ? "" : portes[Presence.Tirer(jour + "|objet", portes.Count)];
    }

    private static string Souvenir(EtatPresence e, Presence.Totaux t, string jour)
    {
        var finies = e.Moi.Finies.Union(e.Autres.Values.SelectMany(a => a.Finies)).Distinct().OrderBy(x => x, StringComparer.Ordinal).ToList();
        return finies.Count == 0 || t.Palier < 1 ? "" : finies[Presence.Tirer(jour + "|souvenir", finies.Count)];
    }

    internal Presence.Contexte ContexteQuotidien(Presence.Moment m, DateTime now, long epoque)
    {
        var e = Pres;
        var tot = e.Totaux();
        int auj = Presence.Jour(now);
        var jour = Presence.JourTexte(now);
        var date = m is Presence.Moment.Premier ? Presence.DateAFeter(tot, auj) : "";
        int nouveau = m is Presence.Moment.Premier && tot.Palier > tot.PalierAnnonce ? tot.Palier : -1;
        // Le prénom : demandé une seule fois, gentiment, quand on se connaît un peu (et pas tous les jours où c'est possible).
        bool demander = m is Presence.Moment.Retour && !tot.PrenomDemande && tot.Prenom == "" && tot.Palier >= 1 && Presence.Tirer(jour + "|prenom?", 3) == 0;
        var hier = e.FaitsDu(Presence.JourTexte(auj - 1));
        var ajd = e.FaitsDu(jour);
        int stade = StadeAffiche();
        return new Presence.Contexte(now, m, e.Cadence.AttenteAbsence, e.Cadence.PresenceJourMin, Cadences.SeanceMin(e.Cadence, epoque),
            _activite, MeteoDuJour(), tot.Palier, stade, NomVariante(stade), tot.Prenom,
            Metier: ajd.Mo != "" ? ajd.Mo : hier.Mo, Niveau: ajd.Nv, Objet: ObjetPorte(jour), Prise: hier.Px, Plat: hier.Cx,
            Souvenir: Souvenir(e, tot, jour), DateAFeter: date, PalierNouveau: nouveau, DemanderPrenom: demander, JoursEnsemble: tot.Jours,
            Annees: date.StartsWith('a') && int.TryParse(date[1..], out var a) ? a : 0);
    }

    private void Parler(Presence.Moment m, DateTime now, long epoque)
    {
        var e = Pres;
        var c = ContexteQuotidien(m, now, epoque);
        var tot = e.Totaux();
        var choix = Presence.Mot(c, Presence.Mots, e.Dits, $"{Presence.JourTexte(now)}|{e.Moi.Id}|{e.Cadence.Dits}");
        Cadences.Noter(e.Cadence, epoque, m);
        _presenceChange = true;
        if (choix is null) return;
        Presence.Retenir(e.Dits, choix.Ligne.Id, Presence.Jour(now));
        if (choix.Famille.StartsWith("date-", StringComparison.Ordinal))
        {
            e.Moi.Fetes.Add(c.DateAFeter);
            _presenceUrgent = true;
        }
        if (choix.Famille.StartsWith("palier-", StringComparison.Ordinal))
        {
            e.Moi.PalierAnnonce = Math.Max(e.Moi.PalierAnnonce, tot.Palier);
            _presenceUrgent = true;
        }
        Dosage.Noter(Maintenant);
        bool question = choix.Famille == "prenom-demande";
        if (question)
        {
            e.Moi.PrenomDemande = true;
            _presenceUrgent = true;
        }
        Sons.Jouer(choix.Famille.StartsWith("palier-", StringComparison.Ordinal) ? Son.Palier : Son.Mot);
        Dire(choix.Texte, question ? 15000 : 7000);
        if (question)
        {
            _messageTag = "prenom";
            Bulle(_vivantes, Epoque);
        }
        // Petits gestes de complicité : il te fait signe quand tu reviens (Copain), il se tourne vers toi d'un clin d'œil
        // (Meilleur ami).
        if (e.Gestes && m is Presence.Moment.Premier or Presence.Moment.Retour)
        {
            if (tot.Palier >= 1)
            {
                _salueJusque = Maintenant + 1800;
                _tSaut = Maintenant;
            }
            if (tot.Palier >= 3) _clinFin = Maintenant + 450;
        }
        EcrirePresence();
    }

    // Tard le soir, quand tu travailles encore, il s'assoupit (à partir d'Ami ; réglage « Petits gestes »).
    private Expr NuitTardive(Expr expr, double t)
    {
        if (PresenceCoupee || _presence is not { Gestes: true } e || expr != Expr.Repos || !AuTravail || EnSaisie) return expr;
        int h = DateTime.Now.Hour;
        if (h is >= 1 and < 23) return expr;
        if (_presTotauxLus < 0 || t - _presTotauxLus > 60_000)
        {
            _presPalier = Quotidien2(() => e.Totaux().Palier, 0);
            _presTotauxLus = t;
        }
        return _presPalier >= 2 && (int)(t / 20_000) % 3 == 2 ? Expr.Dort : expr;
    }

    private double _presTotauxLus = -1;
    private int _presPalier;

    private T Quotidien2<T>(Func<T> f, T repli)
    {
        if (PresenceCoupee) return repli;
        try
        {
            return f();
        }
        catch (Exception e) when (e is not OutOfMemoryException)
        {
            _presenceErreurs++;
            return repli;
        }
    }

    // ---- Le prénom (facultatif ; refuser est aussi simple qu'accepter)

    private void DemanderPrenom() => Quotidien(() =>
    {
        var e = Pres;
        var w = new FenetrePrenom(e.Prenom);
        w.Choisi += (prenom, refus) => Quotidien(() =>
        {
            if (_presenceDemo) return;
            if (refus) e.Moi.PrenomDemande = true;
            else e.ChoisirPrenom(prenom, (long)Epoque);
            _presenceUrgent = true;
            _presenceChange = true;
            EcrirePresence();
            var famille = refus ? "prenom-refus" : "prenom-merci";
            var v = new Dictionary<string, string>();
            if (!refus && e.Prenom != "") v["prenom"] = e.Prenom;
            var l = Presence.Choisir(Presence.Mots, famille, new Presence.Qui(9, 2, ""), v, e.Dits, $"{Presence.JourTexte(DateTime.Now)}|{e.Moi.Id}|{famille}");
            if (l is not null && (refus ? e.Prenom == "" : e.Prenom != "")) Dire(Presence.Remplir(l.Texte, v), 5000);
        });
        w.Show();
    });

    private bool ClicPrenom(object? source)
    {
        for (DependencyObject? d = source as DependencyObject; d is not null;
             d = d is FrameworkContentElement fce ? fce.Parent : d is FrameworkElement fe ? fe.Parent ?? System.Windows.Media.VisualTreeHelper.GetParent(fe) : null)
        {
            if (ReferenceEquals(d, _bulle)) return false;
            if (d is FrameworkElement { Tag: "prenom" } || d is FrameworkContentElement { Tag: "prenom" })
            {
                _messageJusque = -1e9;
                DemanderPrenom();
                return true;
            }
        }
        return false;
    }

    // Une petite jauge de signes (jamais de rouge ni de vert) : ■■■□□.
    internal static string JaugeComplicite(int points, int bas, int haut)
    {
        int n = haut <= bas ? 5 : Math.Clamp((int)Math.Round(5.0 * (points - bas) / (haut - bas)), 0, 5);
        return new string('■', n) + new string('□', 5 - n);
    }

    internal void OuvrirJournal(string? jour = null) => Quotidien(() =>
    {
        if (_fenetreJournal is { IsVisible: true } f)
        {
            f.Aller(jour);
            f.Activate();
            return;
        }
        var w = new FenetreJournal(this, jour);
        w.Closed += (_, _) => _fenetreJournal = null;
        _fenetreJournal = w;
        if (_demo || _presenceDemo) PoserPresDePilou(w);
        w.Show();
    });

    // ---- Synchronisation (sujet à part du relais, chiffré avec le code du groupe ; jamais vers les amis)

    // Sur changement, au plus une fois par quart d'heure (tout de suite pour le prénom, une annonce ou une date), puis
    // toutes les 6 h (le relais garde 12 h).
    private void PublierPresence(long epoque, int auj)
    {
        var code = _reglages.Telephone;
        if (!DansUnGroupe || _presEnvoiEnCours || epoque < _presPause || _demo || _presenceDemo) return;
        var e = Pres;
        bool battement = epoque - _presEnvoi >= 6 * 3600_000;
        bool permis = _presenceUrgent || epoque - _presEnvoi >= 15 * 60_000;
        if (!battement && !permis) return;
        var message = e.Message(auj);
        if (message == _presEnvoyee && !battement) return;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Presence.Sujet(code)}";
        var corps = Telephone.Chiffrer(code, message);
        _presEnvoiEnCours = true;
        _presenceUrgent = false;
        _ = Task.Run(async () =>
        {
            try
            {
                using var r = await Relais.PostAsync(url, new StringContent(corps, Encoding.UTF8, "text/plain"));
                if ((int)r.StatusCode == 429) _presPause = Epoque + 5 * 60_000;
                else if (r.IsSuccessStatusCode)
                {
                    _presEnvoyee = message;
                    _presEnvoi = Epoque;
                }
                else _presPause = Epoque + 60_000;
            }
            catch (Exception x) when (x is HttpRequestException or TaskCanceledException)
            {
                _presPause = Epoque + 60_000;
            }
            finally
            {
                _presEnvoiEnCours = false;
            }
        });
    }

    // Les autres appareils du groupe : relus toutes les 3 min, fusionnés (maximum, union : idempotent).
    private void LirePresence(long epoque)
    {
        var code = _reglages.Telephone;
        if (!DansUnGroupe || _presLectureEnCours || epoque - _presLu < 180_000 || _demo || _presenceDemo) return;
        _presLu = epoque;
        _presLectureEnCours = true;
        var depuis = _reglages.PresenceDepuis == "" ? "12h" : _reglages.PresenceDepuis;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Presence.Sujet(code)}/json?poll=1&since={Uri.EscapeDataString(depuis)}";
        _ = Task.Run(async () =>
        {
            try
            {
                var texte = await Relais.GetStringAsync(url);
                var (messages, dernier) = Campagnes.LireRelais(code, texte);
                await Dispatcher.InvokeAsync(() => Quotidien(() =>
                {
                    var e = Pres;
                    int auj = Presence.Jour(DateTime.Now);
                    bool change = false;
                    foreach (var m in messages)
                        if (Appareil.LireMessage(m) is { } a) change |= e.Recevoir(a, auj);
                    if (dernier != "" && dernier != _reglages.PresenceDepuis)
                    {
                        _reglages.PresenceDepuis = dernier;
                        _reglages.Ecrire(_dossier);
                    }
                    if (change) EcrirePresence();
                }));
            }
            catch (Exception x) when (x is HttpRequestException or TaskCanceledException)
            {
                // hors ligne : on relira au prochain passage
            }
            finally
            {
                _presLectureEnCours = false;
            }
        });
    }

    // ---- Démonstration (--essai=mot, journal, complicite) : en mémoire, rien n'est écrit ni publié

    internal static EtatPresence PresenceDemo()
    {
        var e = new EtatPresence { Moi = new Appareil { Id = "pc-demo", Sorte = "pc" } };
        var auj = DateTime.Now.Date;
        var h = new Random(17);
        for (int d = 45; d >= 0; d--) if (d % 9 != 4) e.Marquer(Presence.Jour(auj.AddDays(-d)));
        e.Moi.Minutes = 4200;
        e.Moi.Caresses = 260;
        e.Moi.Soins = 90;
        e.Moi.Jeux = 110;
        e.Moi.Finies.Add("prologue");
        string[] acts = { "code", "texte", "tableur", "musique", "mail", "lecture" };
        string[] prises = { "un goujon bleu", "une truite argentée", "une perche rayée", "une perle de lune" };
        for (int d = 13; d >= 0; d--)
        {
            var f = e.Aujourdhui(Presence.JourTexte(auj.AddDays(-d)));
            f.Mn = 60 + h.Next(300);
            f.Tv = h.Next(f.Mn);
            (f.Ac, f.Am) = (acts[h.Next(acts.Length)], Math.Max(25, f.Tv / 2));
            f.Ca = h.Next(7);
            if (h.Next(3) == 0) (f.Pc, f.Px, f.Pq) = (1 + h.Next(3), prises[h.Next(prises.Length)], h.Next(4));
            if (h.Next(4) == 0) f.Cx = "une soupe du pêcheur";
            if (h.Next(5) == 0) f.Me = new[] { "pluie", "neige", "degage", "vent" }[h.Next(4)];
            if (d == 6) f.Nv = 18;
            if (d == 3) (f.Mo, f.Mg) = ("Codeur", 3);
            if (d == 9) f.Cf = "La colline d'en face";
            if (h.Next(3) == 0) f.Ta = 21 * 60 + h.Next(170);
        }
        return e;
    }

    private void EssaiPresence(string nom) => Quotidien(() =>
    {
        _presence = PresenceDemo();
        _presenceDemo = true;
        var e = _presence;
        switch (nom)
        {
            case "mot":
            {
                // Cinq petits mots, un toutes les 7 s, à des moments différents (la cadence réelle en dit trois par jour).
                var moments = new[] { Presence.Moment.Premier, Presence.Moment.Retour, Presence.Moment.Soir, Presence.Moment.Retour, Presence.Moment.Premier };
                int i = 0;
                void Un()
                {
                    var c = ContexteQuotidien(moments[i % moments.Length], DateTime.Now, (long)Epoque) with { DemanderPrenom = false };
                    if (Presence.Mot(c, Presence.Mots, e.Dits, $"essai|{DateTime.Now.Ticks}|{i}") is { } ch)
                    {
                        Presence.Retenir(e.Dits, ch.Ligne.Id, Presence.Jour(DateTime.Now) + i);
                        Dire(ch.Texte, 6000);
                        _salueJusque = Maintenant + 1800;
                        _tSaut = Maintenant;
                    }
                    i++;
                }
                Un();
                _essaiMots = new DispatcherTimer(DispatcherPriority.Background, Dispatcher) { Interval = TimeSpan.FromSeconds(7) };
                _essaiMots.Tick += (_, _) =>
                {
                    if (i >= 5) _essaiMots.Stop();
                    else Un();
                };
                _essaiMots.Start();
                break;
            }
            case "journal":
                OuvrirJournal();
                break;
            case "complicite":
            {
                var t = e.Totaux();
                var l = Presence.Choisir(Presence.Mots, "palier-" + Math.Max(1, t.Palier), new Presence.Qui(t.Palier, 2, ""),
                    new Dictionary<string, string>(), e.Dits, "essai-complicite");
                Dire(l?.Texte ?? "on est amis, toi et moi", 7000);
                _salueJusque = Maintenant + 2400;
                _tSaut = Maintenant;
                _clinFin = Maintenant + 450;
                var ouvrir = new DispatcherTimer(DispatcherPriority.Background, Dispatcher) { Interval = TimeSpan.FromSeconds(4) };
                ouvrir.Tick += (_, _) =>
                {
                    ouvrir.Stop();
                    OuvrirJournal();
                };
                ouvrir.Start();
                break;
            }
        }
    });
}
