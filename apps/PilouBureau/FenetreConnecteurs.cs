using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PilouBureau;

// Les connecteurs dans Pilou : registre, API locale, événements reçus (bulle, humeur, quêtes), météo vécue.
public sealed partial class FenetrePilou
{
    private Registre? _registre;
    private ApiLocale? _api;
    private double _connecteursBattus = -1e12, _meteoMinute = -1e12, _prochainePlainte = -1e12;
    private string _meteoVue = "";
    private volatile string _etatApi = "{}";

    // Au chargement : registre (connecteurs intégrés + météo), API locale.
    private void DemarrerConnecteurs()
    {
        _registre = new Registre(_reglages.Connecteurs, new CoffreDpapi(_dossier), () => _reglages.Ecrire(_dossier));
        foreach (var c in ConnecteursIntegres()) _registre.Ajouter(c);
        _registre.Ajouter(new ConnecteurMeteo());
        // Deuxième vague : désactivés tant que tu ne les coches pas.
        _registre.Ajouter(new ConnecteurDiscordBot());
        _registre.Ajouter(new ConnecteurGitHub());
        _registre.Ajouter(new ConnecteurMail());
        _registre.Ajouter(new ConnecteurAgenda());
        _registre.Ajouter(new ConnecteurSpotify());
        _registre.Ajouter(new ConnecteurTwitch());
        _registre.Ajouter(new ConnecteurYouTube());
        _registre.Ajouter(new ConnecteurHomeAssistant());
        // Erreurs du fichier ouvert dans Visual Studio / VS Code (extensions de integrations/, POST /diagnostics).
        _registre.Ajouter(new ConnecteurEditeurs());
        ConnecteurAgenda.Inactivite = Natif.InactifMs;
        _registre.Evenement += e => Dispatcher.BeginInvoke(() => Recevoir(e));
        RelancerApi();
    }

    // Ce qui existe déjà, montré comme connecteurs (rien ne change dans leur fonctionnement).
    private IEnumerable<Connecteur> ConnecteursIntegres()
    {
        yield return new ConnecteurIntegre("claude", "Claude Code", "Sessions Claude : le mod « compagnon » écrit leur état, Pilou le lit.", "◐",
            () => _vivantes.Any(e => e.Claude) || System.IO.Directory.EnumerateFiles(_dossier, "etat-*.json").Any());
        yield return new ConnecteurIntegre("codex", "Codex et --signal", "Hooks de Codex (~/.codex/hooks.json) et toute commande « PilouBureau --signal ».", "⌘",
            () => Codex.Branche(), v => Dire(v ? Codex.Brancher(Environment.ProcessPath ?? "PilouBureau.exe") : Codex.Debrancher(), 4000));
        yield return new ConnecteurIntegre("activites", "Activités", "Pilou regarde l'appli au premier plan (rien ne sort du PC) : tenues, métiers.", "▣",
            () => _reglages.Activites, v => { _reglages.Activites = v; _reglages.Ecrire(_dossier); });
        yield return new ConnecteurIntegre("discord", "Discord (statut)", "Statut « Joue à Pilou » par l'app Discord locale.", "♫",
            () => _reglages.DiscordStatut, v => { _reglages.DiscordStatut = v && _reglages.DiscordApp != ""; _reglages.Ecrire(_dossier); });
        yield return new ConnecteurIntegre("webhook", "Alertes à distance", "Webhook Discord, Slack ou ntfy quand une IA t'attend.", "✉",
            () => Webhook.Valide(_reglages.Webhook));
        yield return new ConnecteurIntegre("telephone", "Téléphone", "L'app Android, par le relais chiffré.", "▯",
            () => PilouBureau.Telephone.Valide(_reglages.Telephone));
        yield return new ConnecteurIntegre("groupe", "Groupe d'appareils", "XP, pièces d'or et objets partagés entre tes PC et le téléphone.", "⇄",
            () => PilouBureau.Telephone.Valide(_reglages.Telephone));
    }

    internal Registre? RegistreConnecteurs => _registre;
    internal ApiLocale? Api => _api;

    internal void RelancerApi()
    {
        _api?.Dispose();
        _api = null;
        if (_registre is null || !_reglages.Connecteurs.Api) return;
        _api = new ApiLocale(() => _registre.JetonApi(), () => _etatApi, e => _registre.Recevoir(e), diagnostics: RecevoirDiagnostics);
        if (!_api.Demarrer(_reglages.Connecteurs.PortApi)) _registre.Noter("api", _api.Erreur ?? "API indisponible");
        else _registre.Noter("api", $"API locale sur http://127.0.0.1:{_api.Port}/");
    }

    // Appelé à chaque lecture (300 ms) : relevés dus, météo vécue, état servi par l'API.
    private void BattreConnecteurs(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        if (_registre is null) return;
        if (Maintenant - _connecteursBattus >= 1000)
        {
            _connecteursBattus = Maintenant;
            _registre.Battre();
            _etatApi = EtatPourApi(vivantes, epoque);
        }
        VivreMeteo();
        VivreDiagnostics();
    }

    private string EtatPourApi(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        var m = Meteo.Courante;
        return JsonSerializer.Serialize(new Dictionary<string, object?>
        {
            ["nom"] = NomPilou,
            ["niveau"] = Niveau,
            ["humeur"] = _exprCourante.ToString().ToLowerInvariant(),
            ["sessions"] = PilouBureau.Telephone.Sessions(vivantes, epoque)
                .Select(s => new Dictionary<string, object> { ["source"] = s.Source, ["libelle"] = s.Libelle, ["etat"] = s.Etat }).ToList(),
            ["meteo"] = m is null ? null : Meteo.PourTelephone(m),
        });
    }

    // Ce que Pilou vit lui-même (une IA attend, quête réussie, évolution), vers les sorties que tu as activées.
    internal void PublierSortie(string titre, string texte) =>
        _registre?.Publier(new EvenementPilou("pilou", "notification", titre, texte));

    // Un événement d'un connecteur ou de l'API locale.
    private void Recevoir(EvenementPilou e)
    {
        // Ce qu'un connecteur demande en plus de la bulle : une quête, une tenue prêtée, une fête.
        if (e.Donnee("quete") != "") Signaler(e.Donnee("quete"), 1);
        if (e.Donnee("tenue") != "") PreterTenue(e.Donnee("tenue"), 10_000);
        if (e.Donnee("humeur") == "fete")
        {
            _salueJusque = Maintenant + 2500;
            _tSaut = Maintenant;
        }
        switch (e.Type)
        {
            case "session":
            case "attente":
            case "fin":
            case "erreur":
                // Une ligne dans la bulle, comme Codex : même chemin que « PilouBureau --signal ».
                var geste = e.Type switch { "session" => "tour", "attente" => "permission", "fin" => "fin", _ => "erreur" };
                var session = e.Donnee("session") != "" ? e.Donnee("session") : e.Titre;
                Signal.Ecrire(_dossier, e.Source, new Evenement(geste, session, Libelle: e.Titre), Epoque);
                break;
            case "message":
            case "notification":
                Dire($"{(e.Gravite >= 2 ? "❗" : "✉")} {e.Titre}{(e.Texte == "" ? "" : " — " + e.Texte)}", e.Gravite >= 1 ? 6000 : 4000);
                _tSaut = Maintenant;
                if (e.Gravite >= 2) _alerteJusque = Maintenant + 5000;
                break;
            case "meteo":
                _meteoVue = "";        // le nouvel état sera commenté au prochain passage de VivreMeteo
                _prochainePlainte = -1e12;
                break;
        }
    }

    // Ce que Pilou porte, pour la météo (objets de boutique + accessoire sous la forme « acc-<nom> »).
    private List<string> PortesMeteo()
    {
        var l = EquipeCourant().Values.ToList();
        var acc = _reglages.Porte(DateTime.Now, a => Possede(Recompenses.IdAccessoire(a)));
        if (acc is not (Accessoire.Aucun or Accessoire.Saison)) l.Add("acc-" + acc.ToString().ToLowerInvariant());
        if (_essaiObjet != "") l.Add(_essaiObjet);
        return l;
    }

    internal EffetMeteo EffetMeteoCourant(double t)
    {
        if (_essaiMeteo != "") return Meteo.Effet(_essaiMeteo, PortesMeteo(), t);
        if (Meteo.Courante is not { } m || _registre?.Trouver("meteo") is not { } c || !_registre.Actif(c)) return EffetMeteo.Aucun;
        return Meteo.Effet(m.Etat, PortesMeteo(), t);
    }

    private string _essaiMeteo = "";

    // Une fois par minute : quête météo du jour, progression si Pilou est bien équipé ; de temps en temps,
    // il commente (et râle s'il subit).
    private void VivreMeteo()
    {
        var etat = _essaiMeteo != "" ? _essaiMeteo : Meteo.Courante?.Etat;
        if (string.IsNullOrEmpty(etat)) return;
        var effet = EffetMeteoCourant(Maintenant);
        if (effet == EffetMeteo.Aucun) return;
        if (Maintenant - _meteoMinute >= 60_000)
        {
            bool premiere = _meteoMinute < 0;
            _meteoMinute = Maintenant;
            if (Quetes.AjouterMeteo(_profil.Quetes, etat, DateTime.Now, IdAppareil) is { } q)
                Dire($"✦ quête météo : {q.Texte}", 5000);
            if (!premiere && effet.Protege && Meteo.Quete(etat) is { } m) Signaler(m.Cle, 1);
        }
        bool commenter = _registre?.Trouver("meteo") is { } c && _registre.Contexte(c).Lire("phrases") != "non";
        if (!commenter && _essaiMeteo == "") return;
        // Nouvel état : un mot (s'il ne vient pas de parler, et pas en pleine saisie) ; ensuite, s'il subit, il
        // râle de loin en loin (8 à 15 min, une fois sur deux environ).
        if (_meteoVue != etat || (effet.Inconfort != "" && Maintenant >= _prochainePlainte))
        {
            bool nouveau = _meteoVue != etat;
            _meteoVue = etat;
            _prochainePlainte = Maintenant + 480_000 + _hasard.NextDouble() * 420_000;
            var phrase = Meteo.Phrase(etat, effet, _hasard.Next());
            if (phrase != "" && _essaiMeteo != "" && nouveau) Dire(phrase, 4500); // essai : tout de suite
            else if (phrase != "") DireSpontane(phrase, 4500);
        }
    }

    private MenuItem MenuConnecteurs()
    {
        var m = new MenuItem { Header = "Connecteurs…" };
        m.Click += (_, _) =>
        {
            if (_registre is not null) new FenetreDesConnecteurs(this, _registre).Show();
        };
        return m;
    }

    internal void SauverReglages() => _reglages.Ecrire(_dossier);
    internal ReglagesConnecteurs ReglagesDesConnecteurs => _reglages.Connecteurs;
}

// Fenêtre « Connecteurs » : chaque connecteur avec son interrupteur, son état, son dernier événement, ses
// réglages typés et ses actions ; l'API locale (port, jeton à copier) ; le journal des 50 derniers événements.
internal sealed class FenetreDesConnecteurs : Window
{
    private readonly FenetrePilou _pilou;
    private readonly Registre _r;
    private readonly StackPanel _corps = new() { Margin = new Thickness(16) };
    private static readonly Brush Bleu = Geler("#2f7ed8"), Orange = Geler("#c86a1c"), Argent = Geler("#57606a");

    private static Brush Geler(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    public FenetreDesConnecteurs(FenetrePilou pilou, Registre r)
    {
        _pilou = pilou;
        _r = r;
        Title = "Connecteurs de Pilou";
        Width = 600;
        Height = 720;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Content = new ScrollViewer { Content = _corps, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        Remplir();
    }

    private static TextBlock Texte(string t, double taille = 12, Brush? couleur = null, bool gras = false) => new()
    {
        Text = t, FontSize = taille, TextWrapping = TextWrapping.Wrap, Foreground = couleur ?? Brushes.Black,
        FontWeight = gras ? FontWeights.Bold : FontWeights.Normal,
    };

    private void Remplir()
    {
        _corps.Children.Clear();
        _corps.Children.Add(Texte("Chaque service branché sur Pilou est un connecteur : coche ceux que tu veux. " +
            "Les jetons et mots de passe sont chiffrés sur ce PC (jamais dans reglages.json).", 12, Argent));
        foreach (var c in _r.Liste) Carte(c);
        Api();
        Nouvelles();
        Journal();
    }

    private static string NomEtat(EtatConnecteur e) => e switch
    {
        EtatConnecteur.Actif => "● actif", EtatConnecteur.Erreur => "✕ en erreur", EtatConnecteur.AConfigurer => "◌ à régler",
        _ => "○ coupé",
    };

    private void Carte(Connecteur c)
    {
        var ctx = _r.Contexte(c);
        var bord = new Border
        {
            BorderBrush = Geler("#d0d9e4"), BorderThickness = new Thickness(1), CornerRadius = new CornerRadius(8),
            Padding = new Thickness(12), Margin = new Thickness(0, 10, 0, 0),
        };
        var pile = new StackPanel();
        bord.Child = pile;
        var etat = _r.Etat(c);
        var titre = new DockPanel();
        var actif = new CheckBox
        {
            IsChecked = _r.Actif(c), VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(8, 0, 0, 0),
            IsEnabled = c is not ConnecteurIntegre i || i.Basculable,
            Content = "actif",
        };
        actif.Click += (_, _) =>
        {
            _r.Activer(c, actif.IsChecked == true);
            Remplir();
        };
        DockPanel.SetDock(actif, Dock.Right);
        titre.Children.Add(actif);
        var nom = Texte($"{c.Signe}  {c.Nom}", 14, null, true);
        titre.Children.Add(nom);
        pile.Children.Add(titre);
        pile.Children.Add(Texte(c.Description, 11, Argent));
        if (c.Aide != "")
            pile.Children.Add(new Expander
            {
                Header = Texte("Comment l'activer ?", 11, Bleu),
                Content = Texte(c.Aide, 11),
                Margin = new Thickness(0, 4, 0, 0),
            });
        var ligneEtat = NomEtat(etat);
        if (etat == EtatConnecteur.AConfigurer && c.Manque(ctx) is { } manque) ligneEtat += " : " + manque;
        if (etat == EtatConnecteur.Erreur && _r.Erreur(c.Id) is { } err) ligneEtat += " : " + err;
        if (_r.Dernier(c.Id) is { } d) ligneEtat += $"   · dernier : {d.Titre}";
        pile.Children.Add(Texte(ligneEtat, 11, etat == EtatConnecteur.Erreur ? Orange : etat == EtatConnecteur.Actif ? Bleu : Argent));

        foreach (var reg in c.Reglages.Where(r => r.Visible)) pile.Children.Add(Reglage(ctx, reg));
        if (c.Actions.Count > 0)
        {
            var actions = new WrapPanel { Margin = new Thickness(0, 6, 0, 0) };
            var retour = Texte("", 11, Argent);
            foreach (var a in c.Actions)
            {
                var b = new Button { Content = a.Nom, Padding = new Thickness(10, 3, 10, 3), Margin = new Thickness(0, 0, 8, 4) };
                b.Click += async (_, _) =>
                {
                    b.IsEnabled = false;
                    try
                    {
                        retour.Text = await a.Faire(ctx, CancellationToken.None);
                    }
                    catch (Exception e)
                    {
                        retour.Text = e is System.Net.Http.HttpRequestException ? "service injoignable (réseau ?)" : e.Message;
                    }
                    b.IsEnabled = true;
                    _r.Maintenant(c.Id);
                };
                actions.Children.Add(b);
            }
            pile.Children.Add(actions);
            pile.Children.Add(retour);
        }
        _corps.Children.Add(bord);
    }

    private UIElement Reglage(ContexteConnecteur ctx, ReglageConnecteur reg)
    {
        var ligne = new DockPanel { Margin = new Thickness(0, 6, 0, 0) };
        var etiquette = Texte(reg.Nom, 12);
        etiquette.Width = 170;
        etiquette.VerticalAlignment = VerticalAlignment.Center;
        DockPanel.SetDock(etiquette, Dock.Left);
        ligne.Children.Add(etiquette);
        switch (reg.Type)
        {
            case TypeReglage.Case:
                var cb = new CheckBox { IsChecked = ctx.Lire(reg.Cle) != "non", VerticalAlignment = VerticalAlignment.Center };
                cb.Click += (_, _) => ctx.Ecrire(reg.Cle, cb.IsChecked == true ? "oui" : "non");
                ligne.Children.Add(cb);
                break;
            case TypeReglage.Liste:
                var liste = new ComboBox { ItemsSource = reg.Choix ?? Array.Empty<string>(), SelectedItem = ctx.Lire(reg.Cle) };
                liste.SelectionChanged += (_, _) => ctx.Ecrire(reg.Cle, liste.SelectedItem as string ?? "");
                ligne.Children.Add(liste);
                break;
            case TypeReglage.Secret:
                var mdp = new PasswordBox { ToolTip = reg.Aide };
                bool connu = ctx.Lire(reg.Cle) != "";
                var etat = Texte(connu ? "  ● enregistré (chiffré)" : "  ○ vide", 11, Argent);
                DockPanel.SetDock(etat, Dock.Right);
                ligne.Children.Add(etat);
                mdp.LostFocus += (_, _) =>
                {
                    if (mdp.Password == "") return;
                    ctx.Ecrire(reg.Cle, mdp.Password);
                    mdp.Password = "";
                    etat.Text = "  ● enregistré (chiffré)";
                };
                ligne.Children.Add(mdp);
                break;
            default:
                var champ = new TextBox { Text = ctx.Lire(reg.Cle), ToolTip = reg.Aide, Padding = new Thickness(3, 2, 3, 2) };
                champ.LostFocus += (_, _) => ctx.Ecrire(reg.Cle, champ.Text.Trim());
                ligne.Children.Add(champ);
                break;
        }
        return ligne;
    }

    // Carte « Nouvelles » de l'app Android : les 5 derniers événements des connecteurs, par le relais chiffré.
    private void Nouvelles()
    {
        var reglages = _pilou.ReglagesDesConnecteurs;
        _corps.Children.Add(Texte("Téléphone : nouvelles", 14, null, true));
        _corps.Children.Add(Texte("Les 5 derniers messages et notifications des connecteurs, sur l'accueil de l'app " +
            "(par le relais chiffré de bout en bout).", 11, Argent));
        var rangee = new WrapPanel { Margin = new Thickness(0, 6, 0, 14) };
        var envoyer = new CheckBox { Content = "Envoyer au téléphone", IsChecked = reglages.AnnoncesTelephone, Margin = new Thickness(0, 0, 12, 0) };
        var masquer = new CheckBox { Content = "Titre seulement (sans le contenu)", IsChecked = reglages.AnnoncesSansContenu };
        envoyer.Click += (_, _) =>
        {
            reglages.AnnoncesTelephone = envoyer.IsChecked == true;
            _pilou.SauverReglages();
        };
        masquer.Click += (_, _) =>
        {
            reglages.AnnoncesSansContenu = masquer.IsChecked == true;
            _pilou.SauverReglages();
        };
        rangee.Children.Add(envoyer);
        rangee.Children.Add(masquer);
        _corps.Children.Add(rangee);
    }

    private void Api()
    {
        var reglages = _pilou.ReglagesDesConnecteurs;
        _corps.Children.Add(Texte("API locale", 14, null, true));
        _corps.Children.Add(Texte("Pour tes scripts et applis : http://127.0.0.1:<port>/ (cette machine seulement), " +
            "en-tête « Authorization: Bearer <jeton> ». Mode d'emploi : docs/API.md.", 11, Argent));
        var api = _pilou.Api;
        _corps.Children.Add(Texte(api is null ? "○ coupée" : api.Erreur is { } e ? $"✕ {e}" : $"● en écoute sur le port {api.Port}", 11,
            api is null ? Argent : api.Erreur is null ? Bleu : Orange));
        var rangee = new WrapPanel { Margin = new Thickness(0, 6, 0, 0) };
        var actif = new CheckBox { Content = "API active", IsChecked = reglages.Api, Margin = new Thickness(0, 0, 12, 0), VerticalAlignment = VerticalAlignment.Center };
        actif.Click += (_, _) =>
        {
            reglages.Api = actif.IsChecked == true;
            _pilou.SauverReglages();
            _pilou.RelancerApi();
            Remplir();
        };
        rangee.Children.Add(actif);
        var port = new TextBox { Text = reglages.PortApi.ToString(), Width = 70, Margin = new Thickness(0, 0, 12, 0) };
        port.LostFocus += (_, _) =>
        {
            if (!int.TryParse(port.Text, out var p) || p is < 1024 or > 65535 || p == reglages.PortApi) return;
            reglages.PortApi = p;
            _pilou.SauverReglages();
            _pilou.RelancerApi();
            Remplir();
        };
        rangee.Children.Add(Texte("port ", 12));
        rangee.Children.Add(port);
        var copier = new Button { Content = "Copier le jeton", Padding = new Thickness(10, 3, 10, 3), Margin = new Thickness(0, 0, 8, 0) };
        copier.Click += (_, _) =>
        {
            Clipboard.SetText(_r.JetonApi());
            copier.Content = "✓ copié";
        };
        rangee.Children.Add(copier);
        var nouveau = new Button { Content = "Nouveau jeton", Padding = new Thickness(10, 3, 10, 3) };
        nouveau.Click += (_, _) =>
        {
            _r.NouveauJeton();
            Remplir();
        };
        rangee.Children.Add(nouveau);
        _corps.Children.Add(rangee);
    }

    private void Journal()
    {
        _corps.Children.Add(new TextBlock { Text = "Journal (50 derniers)", FontSize = 14, FontWeight = FontWeights.Bold, Margin = new Thickness(0, 16, 0, 4) });
        var lignes = _r.Journal();
        if (lignes.Count == 0) _corps.Children.Add(Texte("rien encore", 11, Argent));
        foreach (var l in lignes)
            _corps.Children.Add(Texte($"{l.T:HH:mm:ss}  {l.Connecteur}  ·  {l.Texte}", 11, Argent));
    }
}
