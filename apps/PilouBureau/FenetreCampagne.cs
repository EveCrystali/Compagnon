using System.Net.Http;
using System.Text;
using System.Windows.Threading;

namespace PilouBureau;

// Campagnes (Campagnes.cs, docs/CAMPAGNES.md) : ce que la fenêtre fait du moteur. Le carnet vit dans le profil ; cette
// partie le tient à jour (attentes qui finissent, récompenses versées une fois), le publie sur le sujet des campagnes
// du relais et y lit celui des autres appareils du groupe (PC et téléphone). L'interface : PresenceCampagne.cs (Pilou
// occupé, retour, menus) et FenetreAventure.cs (la fenêtre « Aventure »).
//
// Façade :
//   EtatCampagne                 l'état courant (null : aucune partie), rafraîchi à chaque lecture des sessions
//   CarnetCampagnes              le carnet (fil des messages, non lus, historique) ; CampagneOuverte : la campagne en cours
//   CampagneEnAttente            Pilou est parti (attente) ou se repose : pas d'expédition ni de visite pendant ce temps
//   CampagneDemarrer(id), CampagneChoisir(option), CampagneContinuer(), CampagneEpreuve(reussie), CampagneAuDe(),
//   CampagneAbandonner()         chacune renvoie null si c'est fait, sinon la raison (à montrer telle quelle)
//   CampagneMarquerLu()          le fil est lu (CarnetCampagnes.NonLus retombe à zéro)
//   --essai=campagne:<id>        déroule la campagne en accéléré dans la bulle (rien n'est écrit, rien n'est publié)
//   --essai=campagne:lecture|attente|retour|epreuve|fin : la fenêtre Aventure et Pilou sur une partie de démonstration
//                                (le prologue, en mémoire : le profil n'est ni lu pour elle ni écrit)
//   --essai=campagne:bibliotheque : la bibliothèque à carnet vide, plus la campagne d'essai fermée par un haut fait
//                                (lue dans le dépôt : android/app/src/test/resources/campagnes-essai/haut-fait)
public sealed partial class FenetrePilou
{
    private Campagnes.Carnet? _essaiCamp;
    private Campagnes.Etat? _campEtat;
    private double _campVu = -1e12, _campChange = -1e12, _campEnvoi = -1e12, _campLu = -1e12, _campPause = -1e12;
    private string _campSignature = "", _campEnvoyee = "";
    private bool _campEnvoiEnCours, _campLectureEnCours;

    private Campagnes.Carnet CarnetCamp => _essaiCamp ?? _profil.CarnetCampagnes;

    internal Campagnes.Carnet CarnetCampagnes => CarnetCamp;
    internal Campagnes.Etat? EtatCampagne => _campEtat;
    internal Campagnes.Campagne? CampagneOuverte => CarnetCamp.Courante is { } p ? Campagnes.Charger(p.Campagne) : null;

    // Pilou est parti pour sa campagne (attente) ou s'en remet (repos) : il n'est pas là pour autre chose.
    internal bool CampagneEnAttente => !_essaiCampRapide && _campEtat is { EnAttente: true } e && Epoque < e.Fin;

    // Pourquoi Pilou ne peut pas faire « quoi » (expedition, visite, defense, jeu) pendant sa campagne ; "" s'il le peut.
    private string RefusPendantCampagne(string quoi) => _essaiCampRapide ? "" : Aventure.RefusPendant(quoi, _campEtat, (long)Epoque) ?? "";

    private string OccupationCampagne() => RefusPendantCampagne("expedition");

    // Pourquoi Pilou ne peut pas répondre à sa campagne maintenant (expédition, visite, Défense), null s'il le peut.
    internal string? RefusCampagne() => Aventure.RefusDecision(EnExpedition, _visites.Sortie is not null, _defense is not null);

    // Appelé à chaque lecture des sessions : le temps passe (une attente finit), les récompenses se versent, la synchro suit.
    private void SuivreCampagne(double epoque)
    {
        if (_essaiCampRapide || epoque - _campVu < 1000) return;
        _campVu = epoque;
        if (_essaiCamp is { } essai)
        {
            // Démonstration (--essai=campagne:lecture…) : le carnet en mémoire, à l'heure réelle ; rien n'est versé ni publié.
            _campEtat = Prudemment(() => Campagnes.Actualiser(essai, Campagnes.Charger, (long)epoque), _campEtat);
            if (_essaiOptions is not null && _campEtat is not null) _campEtat.Options = _essaiOptions;
            foreach (var m in _essaiMessages)
                if (!essai.Fil.Contains(m)) essai.Fil.Add(m);
            SuivrePresence();
            return;
        }
        ActualiserCampagne(epoque);
        PublierCampagnes(epoque);
        LireCampagnes(epoque);
        SuivrePresence();
    }

    private void ActualiserCampagne(double epoque)
    {
        var k = _profil.CarnetCampagnes;
        var avant = Campagnes.Signature(k);
        _campEtat = Campagnes.Actualiser(k, Campagnes.Charger, (long)epoque);
        var v = Campagnes.Crediter(_profil, Campagnes.Charger);
        bool verse = v.Po > 0 || v.Xp > 0 || v.Objets.Count > 0;
        if (verse)
        {
            _bourseCache = null;
            int xpAvant = _xpTotal;
            _xpTotal = TotalXp();
            if (v.Po > 0) FlotterPo($"+{v.Po} po");
            if (_xpTotal > xpAvant) Flotter($"+{_xpTotal - xpAvant} xp");
            // Un objet exclusif gagné à une fin : il rejoint ses affaires (boutique, « Ce qu'il porte »).
            if (v.Objets.Count > 0)
                Dire($"✦ {string.Join(", ", v.Objets.Select(o => PilouBureau.Boutique.Trouver(o)?.Nom ?? o))} : objet exclusif, à porter depuis la boutique", 7000);
            VerifierNiveau();
        }
        if (verse || Campagnes.Signature(k) != avant) _profil.Ecrire(DossierPartage);
    }

    // Le carnet vers le groupe : sur changement (regroupé sur 3 s), puis toutes les 6 h (le relais garde 12 h).
    private void PublierCampagnes(double epoque)
    {
        var code = _reglages.Telephone;
        if (!DansUnGroupe || _campEnvoiEnCours || epoque < _campPause || _profil.EnMemoire) return;
        var k = _profil.CarnetCampagnes;
        var signature = Campagnes.Signature(k);
        if (signature != _campSignature)
        {
            _campSignature = signature;
            _campChange = epoque;
        }
        bool change = signature != _campEnvoyee && epoque - _campChange >= 3000;
        bool battement = epoque - _campEnvoi >= 6 * 3600_000;
        var messages = Campagnes.Messages(k, IdAppareil, "pc");
        if ((!change && !battement) || messages.Count == 0) return;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Campagnes.Sujet(code)}";
        var corps = messages.Select(m => Telephone.Chiffrer(code, m)).ToList();
        _campEnvoiEnCours = true;
        _ = Task.Run(async () =>
        {
            try
            {
                foreach (var c in corps)
                {
                    using var r = await Relais.PostAsync(url, new StringContent(c, Encoding.UTF8, "text/plain"));
                    if ((int)r.StatusCode == 429) _campPause = Epoque + 5 * 60_000;
                    if (!r.IsSuccessStatusCode)
                    {
                        if ((int)r.StatusCode != 429) _campPause = Epoque + 60_000;
                        return;
                    }
                }
                _campEnvoyee = signature;
                _campEnvoi = Epoque;
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                _campPause = Epoque + 60_000; // hors ligne : on réessaie dans une minute
            }
            finally
            {
                _campEnvoiEnCours = false;
            }
        });
    }

    // Les carnets des autres appareils (PC et téléphone) : relus toutes les 90 s, fusionnés (idempotent).
    private void LireCampagnes(double epoque)
    {
        var code = _reglages.Telephone;
        if (!DansUnGroupe || _campLectureEnCours || epoque - _campLu < 90_000 || _profil.EnMemoire) return;
        _campLu = epoque;
        _campLectureEnCours = true;
        var depuis = _reglages.CampagnesDepuis == "" ? "12h" : _reglages.CampagnesDepuis;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Campagnes.Sujet(code)}/json?poll=1&since={Uri.EscapeDataString(depuis)}";
        var moi = IdAppareil;
        _ = Task.Run(async () =>
        {
            try
            {
                var texte = await Relais.GetStringAsync(url);
                var (messages, dernier) = Campagnes.LireRelais(code, texte);
                await Dispatcher.InvokeAsync(() =>
                {
                    bool change = false;
                    foreach (var m in messages) change |= Campagnes.Recevoir(_profil.CarnetCampagnes, m, moi, Campagnes.Charger, (long)Epoque);
                    if (dernier != "" && dernier != _reglages.CampagnesDepuis)
                    {
                        _reglages.CampagnesDepuis = dernier;
                        _reglages.Ecrire(_dossier);
                    }
                    if (!change) return;
                    ActualiserCampagne(Epoque);
                    _profil.Ecrire(DossierPartage);
                });
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                // hors ligne : on relira au prochain passage
            }
            finally
            {
                _campLectureEnCours = false;
                // Première lecture du groupe faite (ou impossible) : le retour peut s'annoncer, à jour (PresenceCampagne.cs).
                _ = Dispatcher.BeginInvoke(() => _campPret = true);
            }
        });
    }

    // ---- Décisions (pour l'interface) : null si c'est fait, sinon la raison

    private string? DeciderCampagne(Func<Campagnes.Carnet, Campagnes.Campagne, long, string?> decision, string? id = null, bool memeOccupe = false)
    {
        if (!memeOccupe && _essaiCamp is null && RefusCampagne() is { } refus) return refus;
        var k = CarnetCamp;
        var c = id is not null ? Campagnes.Charger(id) : k.Courante is { } p ? Campagnes.Charger(p.Campagne) : null;
        if (c is null) return id is null ? "aucune partie en cours" : "campagne inconnue";
        var r = decision(k, c, (long)Epoque);
        if (r is null && _essaiCamp is null)
        {
            ActualiserCampagne(Epoque);
            _profil.Ecrire(DossierPartage);
            _campChange = Epoque - 3000; // publier sans attendre
        }
        else if (r is null && !_essaiCampRapide) _campEtat = Campagnes.Actualiser(k, Campagnes.Charger, (long)Epoque);
        if (r is null) ApresDecision();
        return r;
    }

    internal string? CampagneDemarrer(string id, bool neuf = false) =>
        DeciderCampagne((k, c, t) => Campagnes.Demarrer(k, c, _essaiCamp is not null ? int.MaxValue : Niveau, t, IdAppareil, Campagnes.Charger, null, neuf,
            _essaiCamp is not null ? null : _profil.Succes), id);

    // Hauts faits qui ouvrent des campagnes (aucun pendant un essai) ; campagnes ajoutées à la bibliothèque par un essai.
    internal IReadOnlyCollection<string> SuccesAventure => _essaiCamp is not null ? Array.Empty<string>() : _profil.Succes;
    private readonly List<Campagnes.Campagne> _campagnesEnPlus = new();
    internal IReadOnlyList<Campagnes.Campagne> CampagnesEnPlus => _campagnesEnPlus;

    internal string? CampagneChoisir(string option) => DeciderCampagne((k, c, t) => Campagnes.Choisir(k, c, t, IdAppareil, option));

    internal string? CampagneContinuer() => DeciderCampagne((k, c, t) => Campagnes.Continuer(k, c, t, IdAppareil));

    internal string? CampagneEpreuve(bool reussie) => DeciderCampagne((k, c, t) => Campagnes.Epreuve(k, c, t, IdAppareil, reussie));

    internal string? CampagneAuDe() => DeciderCampagne((k, c, t) => Campagnes.EpreuveAuDe(k, c, t, IdAppareil));

    // Ce que les dés vont dire (pour animer le tirage avant de décider) ; null hors épreuve.
    internal bool? CampagneDeVa()
    {
        var k = CarnetCamp;
        if (k.Courante is not { } p || Campagnes.Charger(p.Campagne) is not { } c) return null;
        var e = Campagnes.Rejouer(c, p, (long)Epoque);
        return e.Phase == Campagnes.Phase.Epreuve ? Campagnes.DeDe(c, p, e) : null;
    }

    // Abandonner reste possible quand Pilou est occupé ailleurs.
    internal string? CampagneAbandonner() => DeciderCampagne((k, c, t) => Campagnes.Abandonner(k, c, t, IdAppareil), memeOccupe: true);

    // Tout le fil est lu (le repère de lecture est propre à cet appareil : il se garde dans le profil).
    internal void CampagneMarquerLu()
    {
        Campagnes.MarquerLu(CarnetCamp);
        if (_essaiCamp is null) _profil.Ecrire(DossierPartage);
    }

    // ---- Essai sans attendre : --essai=campagne:<id> déroule la campagne en accéléré dans la bulle. Le carnet d'essai
    // vit en mémoire (rien n'est écrit, rien n'est publié) ; l'horloge de l'essai saute par-dessus les attentes.

    // ---- Démonstrations : --essai=campagne:lecture|attente|retour|epreuve|fin. Une partie du prologue jouée d'avance en
    // mémoire (choix, attentes passées), puis la fenêtre Aventure ou l'overlay à l'heure réelle ; les décisions qu'on y
    // prend restent en mémoire. Le profil n'est pas touché, rien n'est publié.
    // « personnage » : La Grande Panne jouée jusqu'au premier choix où un personnage parle (portrait animé, décor animé).
    // « longue » : la lecture, puis le message le plus long des campagnes et le choix à quatre options du phare
    // (ch8-reunion-a), pour vérifier la mise en page au pire (TEST-JEU.md) ; affichage seulement, ce choix ne se joue pas.
    public static readonly string[] EssaisAventure = { "lecture", "attente", "retour", "epreuve", "fin", "personnage", "longue" };

    private void EssaiAventure(string quoi) => Prudemment(() =>
    {
        var c = Campagnes.Charger(quoi == "personnage" ? "grande-panne" : "prologue");
        if (c is null)
        {
            Dire("la campagne de démonstration est introuvable dans cet exe", 6000);
            return;
        }
        const string appareil = "essai";
        var k = new Campagnes.Carnet();
        long maintenant = (long)Epoque;
        long t = quoi == "attente" ? maintenant - 30_000 : maintenant - 20 * 3_600_000L;
        Campagnes.Demarrer(k, c, int.MaxValue, t, appareil, Campagnes.Charger, "vitrine");
        // Le premier choix mène, par la première attente, à la mare ; on y saute (épreuve) ou on s'arrête là (lecture).
        bool VersEpreuve(Campagnes.Etat e, Campagnes.OptionVue o) =>
            c.Noeud(c.Noeud(e.Noeud)?.Options.FirstOrDefault(x => x.Id == o.Id)?.Vers ?? "")?.Type == "epreuve";
        for (int pas = 0; pas < 400; pas++)
        {
            var e = Campagnes.Actualiser(k, Campagnes.Charger, t)!;
            bool arrete = quoi switch
            {
                "attente" => e.Phase == Campagnes.Phase.Attente,
                "retour" or "lecture" or "longue" => e.Phase == Campagnes.Phase.Choix && k.Fil.Any(m => m.Qui == "joueur"),
                "epreuve" => e.Phase == Campagnes.Phase.Epreuve,
                "personnage" => e.Phase == Campagnes.Phase.Choix && k.Fil.LastOrDefault(m => m.Qui == "pilou") is { } dm
                                && c.Noeud(dm.Noeud) is { Personnage.Length: > 0 } && k.Fil.Count(m => m.Qui == "joueur") >= 2,
                _ => !e.EnCours,
            };
            if (arrete || !e.EnCours) break;
            switch (e.Phase)
            {
                case Campagnes.Phase.Choix:
                    var o = quoi == "epreuve" ? e.Options.FirstOrDefault(x => VersEpreuve(e, x)) ?? e.Options[0] : e.Options[0];
                    Campagnes.Choisir(k, c, t += 3000, appareil, o.Id);
                    break;
                case Campagnes.Phase.Epreuve:
                    Campagnes.Epreuve(k, c, t += 3000, appareil, true);
                    break;
                case Campagnes.Phase.Depart:
                    Campagnes.Continuer(k, c, t += 3000, appareil);
                    break;
                default:
                    // Une attente : l'heure de l'essai saute à son retour (sans dépasser l'heure réelle pour l'attente montrée).
                    t = quoi == "attente" ? t + 1000 : e.Fin + 60_000;
                    break;
            }
        }
        var etat = Campagnes.Actualiser(k, Campagnes.Charger, Math.Max(t, maintenant))!;
        // Lu jusqu'à l'avant-dernier passage : ce que Pilou vient d'écrire s'écrit lettre à lettre (ou s'annonce, au retour).
        var pilou = k.Fil.Where(m => m.Qui == "pilou").ToList();
        if (quoi == "longue") PireMiseEnPage(k, etat, t);
        int garder = quoi switch { "retour" => 3, "lecture" or "fin" or "personnage" or "longue" => 2, _ => 0 };
        var lu = pilou.Count > garder ? pilou[^(garder + 1)] : null;
        k.Lu = lu is null ? "" : string.Create(System.Globalization.CultureInfo.InvariantCulture, $"{lu.P}.{lu.E}.{lu.I}");
        if (garder == 0) Campagnes.MarquerLu(k);
        _essaiCamp = k;
        _essaiCampRapide = false;
        _essaiAnnoncee = "";
        _campEtat = etat;
        _campVu = -1e12;
        if (quoi != "retour") OuvrirAventure();
    });

    // Essai « longue » : ajoute au fil le plus long message de toutes les campagnes et montre les quatre options de
    // ch8-reunion-a (phare). Le carnet reste en mémoire ; seul l'affichage compte. Le moteur réécrit la fin du fil à
    // chaque lecture : ces messages et ces options y sont remis à chaque fois (SuivreCampagne).
    private List<Campagnes.OptionVue>? _essaiOptions;
    private readonly List<Campagnes.Message> _essaiMessages = new();

    private void PireMiseEnPage(Campagnes.Carnet k, Campagnes.Etat etat, long t)
    {
        var tous = Campagnes.Disponibles().Select(Campagnes.Charger).OfType<Campagnes.Campagne>().ToList();
        var plusLong = tous.SelectMany(c => c.Noeuds.Values.SelectMany(n => n.Texte.Select(x => (Noeud: n, Texte: x))))
            .MaxBy(x => x.Texte.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length);
        if (plusLong.Noeud is null || k.Fil.Count == 0) return;
        var dernier = k.Fil[^1];
        _essaiMessages.Add(dernier with { I = dernier.I + 100, Qui = "pilou", Texte = plusLong.Texte, T = t });
        if (tous.FirstOrDefault(c => c.Id == "phare-eteint")?.Noeud("ch8-reunion-a") is { } quatre)
        {
            _essaiMessages.Add(dernier with { I = dernier.I + 101, Qui = "pilou", Texte = string.Join(" ", quatre.Texte), T = t });
            etat.Options = _essaiOptions = quatre.Options.Select((o, i) => new Campagnes.OptionVue(i, o.Id, o.Libelle)).ToList();
        }
        k.Fil.AddRange(_essaiMessages);
    }

    // Essai « bibliotheque » : rien de joué, la bibliothèque telle qu'un nouveau venu la voit, avec en plus la campagne
    // d'essai fermée par un haut fait (« Plume ») et par le prologue, pour voir la ligne de ce qu'il manque.
    private void EssaiBibliotheque() => Prudemment(() =>
    {
        var dir = new System.IO.DirectoryInfo(AppContext.BaseDirectory);
        const string rel = "android/app/src/test/resources/campagnes-essai/haut-fait";
        while (dir is not null && !System.IO.File.Exists(System.IO.Path.Combine(dir.FullName, rel, "campagne.json"))) dir = dir.Parent;
        if (dir is not null)
        {
            var dossier = System.IO.Path.Combine(dir.FullName, rel);
            if (Campagnes.Lire(System.IO.File.ReadAllText(System.IO.Path.Combine(dossier, "campagne.json")),
                    f => System.IO.File.Exists(System.IO.Path.Combine(dossier, f)) ? System.IO.File.ReadAllText(System.IO.Path.Combine(dossier, f)) : null) is { } c)
                _campagnesEnPlus.Add(c);
        }
        else Dire("la campagne d'essai fermée est introuvable (exe hors du dépôt) : la bibliothèque seule", 6000);
        _essaiCamp = new Campagnes.Carnet();
        _essaiCampRapide = false;
        _essaiAnnoncee = "";
        _campEtat = null;
        _campVu = -1e12;
        OuvrirAventure();
    });

    private void EssaiCampagne(string id)
    {
        if (id == "bibliotheque")
        {
            EssaiBibliotheque();
            return;
        }
        if (Array.IndexOf(EssaisAventure, id) >= 0)
        {
            EssaiAventure(id);
            return;
        }
        var c = Campagnes.Charger(id);
        if (c is null)
        {
            Dire($"campagne « {id} » introuvable (connues : {string.Join(", ", Campagnes.Disponibles())})", 8000);
            return;
        }
        _essaiCamp = new Campagnes.Carnet();
        _essaiCampRapide = true;
        long t = (long)Epoque;
        const string appareil = "essai";
        if (Campagnes.Demarrer(_essaiCamp, c, int.MaxValue, t, appareil, Campagnes.Charger, "essai") is { } refus)
        {
            Dire($"campagne « {id} » : {refus}", 6000);
            return;
        }
        Dire($"✉ {c.Titre} · {c.Noeuds.Count} nœuds, {c.Chapitres.Count} chapitres", 2400);
        int choix = 0, pas = 0;
        var minuteur = new DispatcherTimer(DispatcherPriority.Background, Dispatcher) { Interval = TimeSpan.FromSeconds(2.5) };
        minuteur.Tick += (_, _) =>
        {
            var k = _essaiCamp;
            var e = k is null ? null : Campagnes.Actualiser(k, Campagnes.Charger, t);
            if (k is null || e is null || ++pas > 600)
            {
                minuteur.Stop();
                return;
            }
            _campEtat = e;
            // D'abord ce que Pilou a écrit et qu'on n'a pas encore montré, un message à la fois.
            if (k.Fil.FirstOrDefault(m => Campagnes.NonLu(k, m)) is { } m)
            {
                k.Lu = string.Create(System.Globalization.CultureInfo.InvariantCulture, $"{m.P}.{m.E}.{m.I}");
                var texte = m.Texte.Length > 150 ? m.Texte[..149] + "…" : m.Texte;
                Dire(m.Qui == "joueur" ? $"▶ {texte}" : texte, 2400);
                return;
            }
            switch (e.Phase)
            {
                case Campagnes.Phase.Choix:
                    Campagnes.Choisir(k, c, t += 1000, appareil, e.Options[choix++ % e.Options.Count].Id);
                    break;
                case Campagnes.Phase.Epreuve:
                    Dire($"◆ épreuve « {e.Jeu} » (difficulté {e.Difficulte}) : aux dés, {e.Chance} %", 2400);
                    Campagnes.EpreuveAuDe(k, c, t += 1000, appareil);
                    break;
                case Campagnes.Phase.Depart:
                    Campagnes.Continuer(k, c, t += 1000, appareil);
                    break;
                case Campagnes.Phase.Attente:
                case Campagnes.Phase.Repos:
                    Dire($"… {Campagnes.Ligne(e, DateTimeOffset.FromUnixTimeMilliseconds(e.Fin).LocalDateTime)} (tenue : {e.Tenue}, {Statut.Duree(e.Fin - e.T)})", 2400);
                    t = e.Fin;
                    break;
                default:
                {
                    var (po, xp) = Campagnes.Acquis(k, c);
                    Dire(e.Phase == Campagnes.Phase.Fin ? $"✦ fin « {e.TitreFin} » ({e.Issue}) · {po} po, {xp} xp" : $"✕ campagne arrêtée ({e.Phase}) au nœud {e.Noeud}", 8000);
                    minuteur.Stop();
                    break;
                }
            }
        };
        minuteur.Start();
    }
}
