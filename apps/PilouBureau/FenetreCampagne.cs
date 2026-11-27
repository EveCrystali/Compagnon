using System.Net.Http;
using System.Text;
using System.Windows.Threading;

namespace PilouBureau;

// Campagnes (Campagnes.cs, docs/CAMPAGNES.md) : ce que la fenêtre fait du moteur, SANS interface encore. Le carnet vit
// dans le profil ; cette partie le tient à jour (attentes qui finissent, récompenses versées une fois), le publie sur le
// sujet des campagnes du relais et y lit celui des autres appareils du groupe (PC et téléphone).
//
// Pour l'interface à venir :
//   EtatCampagne                 l'état courant (null : aucune partie), rafraîchi à chaque lecture des sessions
//   CarnetCampagnes              le carnet (fil des messages, non lus, historique) ; CampagneOuverte : la campagne en cours
//   CampagneEnAttente            Pilou est parti (attente) ou se repose : pas d'expédition ni de visite pendant ce temps
//   CampagneDemarrer(id), CampagneChoisir(option), CampagneContinuer(), CampagneEpreuve(reussie), CampagneAuDe(),
//   CampagneAbandonner()         chacune renvoie null si c'est fait, sinon la raison (à montrer telle quelle)
//   --essai=campagne:<id>        déroule la campagne en accéléré dans la bulle (rien n'est écrit, rien n'est publié)
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
    internal bool CampagneEnAttente => _essaiCamp is null && _campEtat is { EnAttente: true } e && Epoque < e.Fin;

    private string OccupationCampagne() =>
        CampagneEnAttente && _campEtat is { } e ? $"Pilou est en campagne ({Campagnes.Ligne(e, DateTimeOffset.FromUnixTimeMilliseconds(e.Fin).LocalDateTime)})" : "";

    // Pourquoi Pilou ne peut pas répondre à sa campagne maintenant (expédition, visite), null s'il le peut.
    internal string? RefusCampagne() =>
        EnExpedition ? "Pilou est en expédition : la campagne attendra son retour"
        : _visites.Sortie is not null ? "Pilou est en visite chez un ami : la campagne attendra son retour"
        : null;

    // Appelé à chaque lecture des sessions : le temps passe (une attente finit), les récompenses se versent, la synchro suit.
    private void SuivreCampagne(double epoque)
    {
        if (_essaiCamp is not null || epoque - _campVu < 1000) return;
        _campVu = epoque;
        ActualiserCampagne(epoque);
        PublierCampagnes(epoque);
        LireCampagnes(epoque);
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
        return r;
    }

    internal string? CampagneDemarrer(string id, bool neuf = false) =>
        DeciderCampagne((k, c, t) => Campagnes.Demarrer(k, c, Niveau, t, IdAppareil, Campagnes.Charger, null, neuf), id);

    internal string? CampagneChoisir(string option) => DeciderCampagne((k, c, t) => Campagnes.Choisir(k, c, t, IdAppareil, option));

    internal string? CampagneContinuer() => DeciderCampagne((k, c, t) => Campagnes.Continuer(k, c, t, IdAppareil));

    internal string? CampagneEpreuve(bool reussie) => DeciderCampagne((k, c, t) => Campagnes.Epreuve(k, c, t, IdAppareil, reussie));

    internal string? CampagneAuDe() => DeciderCampagne((k, c, t) => Campagnes.EpreuveAuDe(k, c, t, IdAppareil));

    // Abandonner reste possible quand Pilou est occupé ailleurs.
    internal string? CampagneAbandonner() => DeciderCampagne((k, c, t) => Campagnes.Abandonner(k, c, t, IdAppareil), memeOccupe: true);

    // ---- Essai sans attendre : --essai=campagne:<id> déroule la campagne en accéléré dans la bulle. Le carnet d'essai
    // vit en mémoire (rien n'est écrit, rien n'est publié) ; l'horloge de l'essai saute par-dessus les attentes.

    private void EssaiCampagne(string id)
    {
        var c = Campagnes.Charger(id);
        if (c is null)
        {
            Dire($"campagne « {id} » introuvable (connues : {string.Join(", ", Campagnes.Disponibles())})", 8000);
            return;
        }
        _essaiCamp = new Campagnes.Carnet();
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
