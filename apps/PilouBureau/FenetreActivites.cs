using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace PilouBureau;

// Activités : toutes les 2 s, Pilou regarde ce que fait la personne (fenêtre au premier plan, plein écran,
// son, caméra), se cache quand il gênerait, porte la tenue de l'activité, compte le temps de chaque métier
// et annonce les succès. Le titre de la fenêtre n'est ni gardé ni envoyé : seule l'activité déduite compte.
public sealed partial class FenetrePilou
{
    private DispatcherTimer? _activites;
    private List<Activites.Regle> _regles = new();
    private DateTime _reglesLues = DateTime.MinValue;
    private readonly Activites.Observateur _observateur = new();
    private string _activite = "", _tenue = "";
    private bool _discret;
    private string _raisonDiscret = "";
    private float _crete;
    private double _cpu;
    private double _dernierActivites = -1;
    private double _serieCode, _horsCode;
    private double _visioDepuis = -1, _presentationDepuis = -1;
    private bool _reunionComptee, _presentationComptee;
    private readonly Dictionary<string, double> _ditActivite = new();
    private double _secondesNonEcrites;
    private readonly Dictionary<string, double> _secondesQuetes = new();

    private string CheminRegles => Path.Combine(_dossier, "activites.json");

    private void DemarrerActivites()
    {
        ChargerRegles();
        _activites = new DispatcherTimer(TimeSpan.FromSeconds(2), DispatcherPriority.Background, (_, _) => Regarder(), Dispatcher);
        _activites.Start();
    }

    private void ChargerRegles()
    {
        string? perso = null;
        try
        {
            if (File.Exists(CheminRegles))
            {
                perso = File.ReadAllText(CheminRegles);
                _reglesLues = File.GetLastWriteTimeUtc(CheminRegles);
            }
        }
        catch (IOException)
        {
            // fichier en cours d'écriture : relu au tour suivant
        }
        _regles = Activites.Charger(perso);
    }

    private void Regarder()
    {
        var t = Maintenant;
        double dt = _dernierActivites < 0 ? 0 : Math.Clamp((t - _dernierActivites) / 1000.0, 0, 5);
        _dernierActivites = t;
        if (!_reglages.Activites)
        {
            _activite = _tenue = "";
            _discret = false;
            return;
        }
        // Règles personnelles modifiées : relues sans redémarrer.
        try
        {
            if (File.Exists(CheminRegles) && File.GetLastWriteTimeUtc(CheminRegles) != _reglesLues) ChargerRegles();
        }
        catch (IOException)
        {
        }

        var premier = Sondes.PremierPlan();
        var c = new Activites.Contexte(
            premier?.Processus ?? "", premier?.Titre ?? "", premier?.Chemin ?? "", Sondes.Ecran(),
            Sondes.EnCours("webcam"), Sondes.EnCours("microphone"), Sondes.Sons(), DateTime.Now, Sondes.Cpu(), Natif.InactifMs());
        _cpu = c.Cpu;

        // Discrétion d'abord : jamais devant un jeu, une présentation ou une visio.
        var options = new Activites.OptionsDiscretion(_reglages.CacherPleinEcran, _reglages.CacherPresentation, _reglages.CacherVisio);
        (_discret, _raisonDiscret) = Activites.Discretion(c, options, _attend);
        // Connecteur Agenda : une réunion en cours vaut une visio (même sans appli de visio au premier plan).
        if (!_discret && _reglages.CacherVisio && !_attend && ConnecteurAgenda.EnReunion) (_discret, _raisonDiscret) = (true, "reunion");

        var activite = Activites.Detecter(c, _regles);
        // Connecteur Spotify : un morceau qui joue, c'est de la musique, même fenêtre fermée.
        if (activite == "" && ConnecteurSpotify.Lecture is { EnCours: true }) activite = "musique";
        if (_reglages.ActivitesCoupees.Contains(activite)) activite = "";
        _activite = activite;
        _crete = activite == "musique" ? Activites.Crete(c, _regles) : 0;
        if (_observateur.Observer(activite, t))
        {
            _tenue = _observateur.Tenue;
            if (_tenue != "" && (!_ditActivite.TryGetValue(_tenue, out var dit) || t - dit > 30 * 60_000))
            {
                _ditActivite[_tenue] = t;
                // Pas à chaque changement d'appli : une fois sur deux environ, et jamais en pleine saisie.
                if (!_discret) DireSpontane(Activites.Accueil(_tenue), 3500);
            }
        }
        // Processeur à fond pendant le code : il transpire (et le dit, de temps en temps).
        if (_tenue == "code" && _cpu > 0.8 && (!_ditActivite.TryGetValue("sueur", out var s) || t - s > 15 * 60_000))
        {
            _ditActivite["sueur"] = t;
            if (!_discret) DireSpontane("ça chauffe !", 3000);
        }

        Compter(c, activite, dt);
    }

    // Temps des métiers : seulement si la personne est là (sauf vidéo et musique, qu'on écoute sans bouger).
    private void Compter(Activites.Contexte c, string activite, double dt)
    {
        if (dt <= 0) return;
        bool present = c.InactifMs < 120_000 || activite is "video" or "musique" or "visio";
        // Énergie des expéditions : le temps passé dans une appli de travail, la personne présente (jamais les frappes).
        EnergieTravail(activite, c.InactifMs < 120_000 && c.Ecran != Activites.Ecran.Verrouille, dt);
        if (activite != "" && activite != "nuit" && present && c.Ecran != Activites.Ecran.Verrouille)
        {
            _profil.Activites[activite] = (_profil.Activites.TryGetValue(activite, out var v) ? v : 0) + (long)Math.Round(dt);
            _secondesNonEcrites += dt;
            // Quêtes « Code pendant N min », « Joue N min »… : une minute signalée par minute passée.
            var cle = activite == "jeu-mmo" ? "jeu" : activite;
            _secondesQuetes[cle] = _secondesQuetes.GetValueOrDefault(cle) + dt;
            if (_secondesQuetes[cle] >= 60)
            {
                int minutes = (int)(_secondesQuetes[cle] / 60);
                _secondesQuetes[cle] -= minutes * 60;
                Signaler("activite:" + cle, minutes);
            }
        }
        // Série de code : coupée après 10 min sans code.
        if (activite == "code" && present)
        {
            _serieCode += dt;
            _horsCode = 0;
        }
        else if ((_horsCode += dt) > 600) _serieCode = 0;

        // Une réunion compte après 2 min de caméra ou de micro ; une présentation après 1 min.
        var t = Maintenant;
        if (c.Camera || c.Micro)
        {
            if (_visioDepuis < 0) _visioDepuis = t;
            if (!_reunionComptee && t - _visioDepuis > 120_000)
            {
                _reunionComptee = true;
                _profil.Reunions.Add(DateTime.Now);
            }
        }
        else
        {
            _visioDepuis = -1;
            _reunionComptee = false;
        }
        if (c.Ecran == Activites.Ecran.Presentation)
        {
            if (_presentationDepuis < 0) _presentationDepuis = t;
            if (!_presentationComptee && t - _presentationDepuis > 60_000)
            {
                _presentationComptee = true;
                _profil.Presentations++;
            }
        }
        else
        {
            _presentationDepuis = -1;
            _presentationComptee = false;
        }
        _profil.Reunions.RemoveAll(d => DateTime.Now - d > TimeSpan.FromDays(7));

        // Métier qui monte, succès débloqués : annonce et XP (avec les heures de tout le groupe).
        MonterMetiers(CumulGroupe());
        VerifierSucces(activite);
        // Le profil est réécrit au plus une fois par minute pour le temps qui passe.
        if (_secondesNonEcrites >= 60)
        {
            _secondesNonEcrites = 0;
            _profil.Ecrire(DossierPartage);
        }
    }

    private Dictionary<string, int>? _niveauxMetiers;

    // Grades de métier : payés une fois dans le groupe (Metiers.Monter). Un grade monté grâce aux heures d'un
    // autre PC, qui l'a déjà payé, s'annonce ici d'un petit texte, sans XP.
    private void MonterMetiers(Groupe.Cumul cumul)
    {
        var niveaux = Metiers.Niveaux(cumul.Secondes);
        // Premier calcul : les grades de ce PC seul ont été payés par les versions précédentes.
        if (_niveauxMetiers is null)
            foreach (var m in Metiers.Tous)
                if (Metiers.Niveau(m, Metiers.Secondes(m, _profil.Activites)) is > 0 and var seul && seul > _profil.MetiersPayes.GetValueOrDefault(m.Id))
                    _profil.MetiersPayes[m.Id] = seul;
        foreach (var x in Metiers.Monter(niveaux, _niveauxMetiers, _profil.MetiersPayes, cumul.PayesAutres))
        {
            var texte = $"{x.Metier.Nom} : {Metiers.Grades[x.Niveau]}";
            VecuMetier(x.Metier.Nom, x.Niveau);
            if (x.Discret) Flotter(texte);
            else
            {
                GagnerActivite(x.Xp);
                Dire(texte + " !", 4500);
            }
        }
        _niveauxMetiers = niveaux;
    }

    // Après une lecture du groupe : succès des autres PC (sans XP), grades montés ailleurs, succès franchis à plusieurs.
    private void MetiersEtSuccesDuGroupe()
    {
        var cumul = CumulGroupe();
        if (Groupe.UnirSucces(_profil, cumul).Count > 0) _secondesNonEcrites = 60;
        MonterMetiers(cumul);
        VerifierSucces(_activite);
    }

    private Stats StatsActuelles(string activite) =>
        Groupe.StatsGroupe(CumulGroupe(), _serieCode, _profil.Reunions.Count, DateTime.Now, activite);

    // Succès débloqués : annonce et XP (activités, et à la fin d'une partie de Défense du bureau). Un succès déjà
    // obtenu par un autre PC du groupe est repris sans XP (Groupe.UnirSucces) : il n'est crédité qu'une fois.
    private void VerifierSucces(string activite)
    {
        Groupe.UnirSucces(_profil, CumulGroupe());
        foreach (var d in Succes.Nouveaux(StatsActuelles(activite), _profil.Succes))
        {
            _profil.Succes.Add(d.Id);
            GagnerActivite(d.Xp);
            Flotter("SUCCES !", 1.6, new Point(TeteX - 46, TeteY - 70));
            Sons.Jouer(Son.Succes);
            Dire($"succès débloqué : {d.Nom} !", 5000);
            _secondesNonEcrites = 60;
        }
    }

    private void GagnerActivite(int xp)
    {
        xp = BonusSoins(xp);
        _profil.Xp += xp;
        _profil.Ecrire(DossierPartage);
        _xpTotal += xp;
        Flotter($"+{xp} xp");
        VerifierNiveau();
    }

    // ---- Ce que la scène reçoit (appelé à chaque image)

    // Une tenue prêtée quelques secondes par un connecteur (casquette de facteur pour un mail…).
    private string _tenuePretee = "";
    private double _tenuePreteeJusque = -1e12;

    internal void PreterTenue(string tenue, double ms)
    {
        _tenuePretee = tenue;
        _tenuePreteeJusque = Maintenant + ms;
    }

    private string TenueAffichee => !_reglages.Activites ? "" : Maintenant < _tenuePreteeJusque ? _tenuePretee : _tenue;

    // En route pour sa campagne : ni danse ni sueur (réactions cosmétiques coupées, il est occupé).
    private string ReactionAffichee =>
        !_reglages.Activites || CampagneOccupe ? ""
        : _tenue == "musique" && (_crete > Activites.SeuilSon || ConnecteurSpotify.Lecture is { EnCours: true }) ? "danse"
        : _tenue == "code" && _cpu > 0.8 ? "sueur"
        : "";

    // Musique : il se balance au rythme du niveau sonore ; au vrai tempo du morceau si Spotify le donne
    // (un aller-retour toutes les deux pulsations).
    private double Balancement(double t)
    {
        if (ReactionAffichee != "danse") return 0;
        // Ampleur modeste, plus encore quand tu travailles (frappe ou souris récente, appli de travail).
        double ampleur = Math.Max(_crete > 0 ? Math.Min(1, _crete * 2.5) : 0, ConnecteurSpotify.Lecture is not null ? 0.6 : 0)
                         * (AuTravail ? 0.45 : 0.6);
        return ConnecteurSpotify.Lecture is { Tempo: > 30 and < 260 } l
            ? Math.Sin(t * Math.PI * l.Tempo / 60_000.0) * ampleur
            : Math.Sin(t / 220.0) * ampleur;
    }

    // ---- Menu

    private MenuItem MenuActivites()
    {
        var m = new MenuItem { Header = "Métiers et succès" };
        var stats = StatsActuelles(_activite);
        var titre = _tenue != "" ? $"en ce moment : {Activites.Signe(_tenue)} {Activites.Nom(_tenue)}" : "en ce moment : rien de reconnu";
        if (_discret) titre += _raisonDiscret switch
        {
            "presentation" => " · caché (présentation)",
            "visio" => " · caché (visio)",
            "reunion" => " · caché (réunion à l'agenda)",
            _ => " · caché (plein écran)",
        };
        m.Items.Add(new MenuItem { Header = titre, IsEnabled = false });
        m.Items.Add(new Separator());
        foreach (var me in Metiers.Tous)
        {
            var sec = Metiers.Secondes(me, stats.Secondes); // heures de tout le groupe
            int n = Metiers.Niveau(me, sec);
            m.Items.Add(new MenuItem { Header = $"{me.Nom} — {Metiers.Grades[n]} · {Metiers.Progres(me, sec)}", IsEnabled = sec > 0 });
        }
        m.Items.Add(new Separator());
        var succes = new MenuItem { Header = $"Succès ({_profil.Succes.Count}/{Succes.Tous.Count})" };
        foreach (var d in Succes.Tous)
        {
            bool ok = _profil.Succes.Contains(d.Id);
            var progres = ok ? "" : Succes.Progres(d, stats);
            succes.Items.Add(new MenuItem
            {
                Header = (ok ? "✓  " : "·  ") + $"{d.Nom} — {d.Description}" + (progres == "" ? "" : $" ({progres})"),
                IsEnabled = ok,
            });
        }
        m.Items.Add(succes);

        var reglages = new MenuItem { Header = "Activités : réglages" };
        reglages.Items.Add(Case("Pilou regarde mes fenêtres (rien ne sort du PC)", _reglages.Activites, v =>
        {
            _reglages.Activites = v;
            if (!v) _tenue = "";
        }));
        reglages.Items.Add(Case("Se cacher en plein écran (jeu, vidéo)", _reglages.CacherPleinEcran, v => _reglages.CacherPleinEcran = v));
        reglages.Items.Add(Case("Se cacher en présentation", _reglages.CacherPresentation, v => _reglages.CacherPresentation = v));
        reglages.Items.Add(Case("Se cacher en visio (caméra ou micro)", _reglages.CacherVisio, v => _reglages.CacherVisio = v));
        reglages.Items.Add(new Separator());
        foreach (var a in Activites.Toutes)
            reglages.Items.Add(Case($"{Activites.Signe(a)}  {Activites.Nom(a)}", !_reglages.ActivitesCoupees.Contains(a), v =>
            {
                if (v) _reglages.ActivitesCoupees.Remove(a);
                else if (!_reglages.ActivitesCoupees.Contains(a)) _reglages.ActivitesCoupees.Add(a);
            }));
        reglages.Items.Add(new Separator());
        reglages.Items.Add(Entree("Ajouter mes logiciels… (activites.json)", OuvrirRegles));
        m.Items.Add(reglages);
        return m;
    }

    // Ouvre le fichier de règles personnelles (créé avec un exemple s'il n'existe pas).
    private void OuvrirRegles()
    {
        try
        {
            if (!File.Exists(CheminRegles))
            {
                Directory.CreateDirectory(_dossier);
                File.WriteAllText(CheminRegles, """
                    {
                      "_aide": "Tes règles s'ajoutent à celles de Pilou (\"remplacer\": true pour les remplacer). processus : nom du programme sans .exe ; titre / chemin : expressions régulières ; priorite : la plus haute gagne ; activite vide = ignorer ce programme. Activités : code, tableur, jeu-mmo, jeu, musique, video, lecture, dessin, visio, mail, texte, diaporama.",
                      "regles": [
                        { "activite": "code", "priorite": 50, "processus": ["monediteur"] },
                        { "activite": "", "priorite": 60, "processus": ["programme-a-ignorer"] }
                      ]
                    }
                    """);
            }
            Process.Start(new ProcessStartInfo(CheminRegles) { UseShellExecute = true });
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException or System.ComponentModel.Win32Exception)
        {
            Dire("impossible d'ouvrir le fichier de règles", 3500);
        }
    }
}
