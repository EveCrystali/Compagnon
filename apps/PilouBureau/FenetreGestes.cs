using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PilouBureau;

// Petits gestes : Pilou tape avec toi au clavier, photographie tes captures d'écran, t'apporte les
// notifications Windows dans sa bulle (docs/NOTIFICATIONS.md). Trois cases dans le menu, rien d'imposé.
public sealed partial class FenetrePilou
{
    private readonly CompteurFrappes _frappes = new();
    private readonly SceneClavier _clavier = new();
    private readonly ScenePhoto _photo = new();
    private readonly AntiDoublon _doublon = new();
    private readonly FileNotifs _notifs = new();
    private CrochetClavier? _crochet;
    private GuetteurCaptures? _guetteur;
    private ISourceNotifications? _sourceNotifs;
    // Noms des applis vues cette session (pour cocher le filtre) : des noms seulement, jamais de contenu.
    private readonly SortedSet<string> _appsVues = new(StringComparer.OrdinalIgnoreCase);
    private double _essaiFrappesJusque = -1e12, _prochaineFrappeEssai;
    private bool _essaiNotif;

    private bool GesteEnCours => _clavier.Active || _photo.Active(Maintenant);

    private void DemarrerGestes()
    {
        AppliquerGestes();
    }

    // Pose ou retire les crochets selon les trois cases.
    private void AppliquerGestes()
    {
        bool clavier = _reglages.GesteClavier, photo = _reglages.GestePhoto;
        if (clavier || photo)
        {
            if (_crochet is null)
            {
                _crochet = new CrochetClavier();
                _crochet.Frappe += () => _frappes.Frappe(Maintenant);
                _crochet.ImprEcran += () => Capture(SourceCapture.ImprEcran);
                if (!_crochet.Installer()) _crochet = null;
            }
        }
        else
        {
            _crochet?.Dispose();
            _crochet = null;
        }
        if (photo && _nous != IntPtr.Zero)
        {
            if (_guetteur is null)
            {
                _guetteur = new GuetteurCaptures();
                _guetteur.Capture += Capture;
                _guetteur.Demarrer(_nous, Dispatcher);
            }
        }
        else
        {
            _guetteur?.Dispose();
            _guetteur = null;
            _photo.Arreter();
        }
        if (_reglages.NotifsWindows)
        {
            if (_sourceNotifs is null)
            {
                var s = new SourceNotifsWindows(Dispatcher);
                s.Recue += RecevoirNotif;
                _sourceNotifs = s;
                _ = s.DemarrerAsync();
            }
        }
        else
        {
            _sourceNotifs?.Dispose();
            _sourceNotifs = null;
            _notifs.Vider();
        }
    }

    private void ArreterGestes()
    {
        _crochet?.Dispose();
        _guetteur?.Dispose();
        _sourceNotifs?.Dispose();
    }

    // Pilou peut-il se lancer dans un geste ? Jamais caché (plein écran, jeu, visio), en visite, pendant un
    // mini-jeu, quand une IA t'attend, ni quand on le tient par la souris.
    private bool GestePermis => !_discret && !_visites.Occupe && _jeuEnCours == Jeu.Aucun && !_attend && !_attrape && _auSol;

    private void Capture(SourceCapture source)
    {
        var t = Maintenant;
        if (source != SourceCapture.Essai && !_reglages.GestePhoto) return;
        if (!_doublon.Accepter(t)) return;               // écho de la même capture
        if (!GestePermis || _clavier.Active) return;     // pas de photo au milieu d'autre chose
        if (_photo.Declencher(t))
        {
            _profil.Captures++;
            _profil.Ecrire(DossierPartage);
        }
    }

    private void RecevoirNotif(NotifRecue n)
    {
        var r = _essaiNotif ? _reglages.FiltreDesNotifs() with { Actif = true } : _reglages.FiltreDesNotifs();
        if (n.App.Trim() != "") _appsVues.Add(FiltreNotifs.Ligne(n.App, 40));
        // Caché par discrétion (plein écran, présentation, visio) ou heures calmes : la notification n'est pas montrée
        // (elle reste dans le centre de notifications de Windows).
        var a = FiltreNotifs.Preparer(n, r, HeureCalme && !_essaiNotif, _discret);
        if (a is null) return;
        _notifs.Ajouter(a, Maintenant);
        Bulle(_vivantes, Epoque);
    }

    // Appelé à chaque image, après la pose de base : ce que les gestes y changent.
    private void HabillerGestes(Pose p, double t)
    {
        // Essai : des frappes simulées pendant quelques secondes.
        if (t < _essaiFrappesJusque && t >= _prochaineFrappeEssai)
        {
            _frappes.Frappe(t);
            _prochaineFrappeEssai = t + 140;
        }
        bool essai = t < _essaiFrappesJusque + SceneClavier.SilenceSortie;
        bool permis = (_reglages.GesteClavier || essai) && GestePermis && !_photo.Active(t) && p.Pancarte == "";
        if (_clavier.Avancer(t, _frappes.Rafale(t), _frappes.Silence(t), permis))
        {
            _profil.SeancesClavier++;
            _profil.Ecrire(DossierPartage);
            if (_dit.Add("clavier-" + DateTime.Now.ToString("yyyyMMdd"))) Dire("tap tap tap… je tape avec toi !", 3000);
        }
        var d = _clavier.Active ? _clavier.Dessin(t) : _photo.Dessin(t);
        if (d.Objets.Count > 0)
        {
            p.Gestes = d.Objets;
            p.Regard = d.Regard;
            p.Dos = d.Dos;
            if (d.Assis > 0)
            {
                p.Assis = d.Assis;
                p.Marche = false;
                p.Course = false;
                p.Saut = 0;
            }
            if (d.Concentre && p.Expr is Expr.Repos or Expr.Caresse) p.Expr = Expr.Concentre;
            p.Flash = d.Flash;
            p.Bruit = d.Bruit;
            return;
        }
        // Notification : il lève la tête et brandit l'enveloppe les premières secondes.
        if (_notifs.Courante(t) is { } n && _notifs.Age(t) < 3500 && GestePermis)
        {
            p.Gestes = new[] { n.Masquee ? "enveloppe-close" : "enveloppe-notif" };
            p.RegardY = -1;
            if (p.Expr == Expr.Repos) p.Expr = Expr.Attente;
        }
    }

    // ---- Bulle : la notification en tête (initiale de l'appli, nom, titre, une ligne).

    private UIElement? BlocNotif()
    {
        if (_notifs.Courante(Maintenant) is not { } n) return null;
        var c = Couleurs;
        var pile = new StackPanel { Margin = new Thickness(0, 1, 0, 3) };
        var entete = new StackPanel { Orientation = Orientation.Horizontal };
        // Initiale de l'appli dans un carré (forme + lettre : lisible sans couleur), pas de logo.
        entete.Children.Add(new Border
        {
            Width = 16, Height = 16, Background = c.Bleu, Margin = new Thickness(0, 0, 6, 0),
            Child = new TextBlock
            {
                Text = n.Initiale, Foreground = Brushes.White, FontWeight = FontWeights.Bold, FontSize = 11,
                HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Center,
            },
        });
        entete.Children.Add(new TextBlock
        {
            Text = n.Masquee ? "✉ " + FiltreNotifs.Resume(n) : "✉ " + n.App,
            FontFamily = new FontFamily("Segoe UI"), FontSize = 12.5, FontWeight = FontWeights.SemiBold,
            Foreground = c.Orange, TextTrimming = TextTrimming.CharacterEllipsis, MaxWidth = LargeurBase - 60,
        });
        pile.Children.Add(entete);
        if (!n.Masquee)
        {
            if (n.Titre != "")
                pile.Children.Add(new TextBlock
                {
                    Text = n.Titre, FontFamily = new FontFamily("Segoe UI"), FontSize = 12.5, FontWeight = FontWeights.SemiBold,
                    Foreground = c.Texte, TextTrimming = TextTrimming.CharacterEllipsis, Margin = new Thickness(22, 0, 0, 0),
                });
            if (n.Texte != "")
                pile.Children.Add(new TextBlock
                {
                    Text = n.Texte, FontFamily = new FontFamily("Segoe UI"), FontSize = 11.5, Foreground = c.Pale,
                    TextTrimming = TextTrimming.CharacterEllipsis, Margin = new Thickness(22, 0, 0, 0),
                });
        }
        return pile;
    }

    // ---- Menu

    private MenuItem MenuGestes()
    {
        var m = new MenuItem { Header = "Clavier, photo, notifications" };
        m.Items.Add(Case("Pilou tape avec moi au clavier (compte les frappes, jamais lesquelles)", _reglages.GesteClavier, v =>
        {
            _reglages.GesteClavier = v;
            AppliquerGestes();
        }));
        m.Items.Add(Case("Appareil photo à chaque capture d'écran", _reglages.GestePhoto, v =>
        {
            _reglages.GestePhoto = v;
            AppliquerGestes();
        }));
        m.Items.Add(Case("Notifications Windows dans la bulle", _reglages.NotifsWindows, v =>
        {
            _reglages.NotifsWindows = v;
            AppliquerGestes();
        }));
        if (_reglages.NotifsWindows)
            m.Items.Add(new MenuItem { Header = "   état : " + (_sourceNotifs?.Etat ?? "démarrage…"), IsEnabled = false });

        var notifs = new MenuItem { Header = "Notifications : réglages" };
        notifs.Items.Add(Choix("Applis", new[] { ("Toutes", ModeApps.Toutes), ("Toutes sauf celles cochées", ModeApps.Sauf), ("Seulement celles cochées", ModeApps.Seulement) },
            _reglages.NotifsMode, v => _reglages.NotifsMode = v));
        var apps = _appsVues.Union(_reglages.NotifsApps, StringComparer.OrdinalIgnoreCase).OrderBy(a => a, StringComparer.OrdinalIgnoreCase).ToList();
        if (apps.Count == 0) notifs.Items.Add(new MenuItem { Header = "   (les applis apparaîtront ici à leur première notification)", IsEnabled = false });
        foreach (var a in apps)
            notifs.Items.Add(Case("   " + a, _reglages.NotifsApps.Contains(a, StringComparer.OrdinalIgnoreCase), v =>
            {
                _reglages.NotifsApps.RemoveAll(x => string.Equals(x, a, StringComparison.OrdinalIgnoreCase));
                if (v) _reglages.NotifsApps.Add(a);
            }));
        notifs.Items.Add(new Separator());
        notifs.Items.Add(Case("Masquer le contenu (seulement « 1 message de X »)", _reglages.NotifsMasquer, v => _reglages.NotifsMasquer = v));
        notifs.Items.Add(Entree("Paramètres Windows : Ne pas déranger…", () => Ouvrir("ms-settings:notifications")));
        notifs.Items.Add(Entree("Comment ça marche (et ce qui manque)…", () => Ouvrir("https://github.com/EveCrystali/Compagnon/blob/main/docs/NOTIFICATIONS.md")));
        m.Items.Add(notifs);
        return m;
    }

    // ---- Essais (--essai=clavier, --essai=photo, --essai=notif, --essai=notif:masque)

    private void EssaiGeste(string nom)
    {
        var t = Maintenant;
        switch (nom)
        {
            case "clavier":
                _essaiFrappesJusque = t + 6000;
                _prochaineFrappeEssai = t;
                for (int i = 0; i < CompteurFrappes.Seuil; i++) _frappes.Frappe(t);
                break;
            case "photo":
                Capture(SourceCapture.Essai);
                break;
            case "notif":
            case "notif:masque":
            {
                bool masque = nom.EndsWith(":masque");
                bool avant = _reglages.NotifsMasquer;
                _reglages.NotifsMasquer = masque;
                _essaiNotif = true;
                RecevoirNotif(new NotifRecue("Messagerie", "Léo", "On se voit à midi pour le déjeuner ?"));
                if (masque) RecevoirNotif(new NotifRecue("Messagerie", "Léo", "Je réserve ?"));
                _essaiNotif = false;
                _reglages.NotifsMasquer = avant;
                break;
            }
        }
    }
}
