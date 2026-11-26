using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Threading;

namespace PilouBureau;

// Tournage (outils/tourner-ecran-gauche.ps1) : Pilou posé sur l'écran choisi pour cette session (--ecran=, --placer=),
// et la visite guidée (--visite-guidee) qui joue les vrais menus et fenêtres, l'une après l'autre (Tournage.Etapes),
// en mode démo : profil, amis et réglages fictifs en mémoire, sessions fictives du dossier de démo.
// La souris glisse d'elle-même (SetCursorPos) : le survol des menus est le vrai, celui de WPF.
public sealed partial class FenetrePilou
{
    private readonly bool _demo;
    private Point? _poseEcran;                 // pixels de ce processus
    private double? _marcheVers;               // promenade de la visite : là où il va (unités WPF)
    private readonly List<Moment> _chronologie = new();
    private string? _cheminChronologie;

    // ---- Placement pour cette session

    public void PoserSur(int x, int y) => _poseEcran = new Point(x, y);

    private bool PlacerSurDemande()
    {
        if (_poseEcran is not { } p) return false;
        var dip = VersWpf.Transform(p);
        _zone = ZoneSous(dip.X, dip.Y);
        double demi = Scene.Largeur / 2 * K;
        _x = Math.Clamp(dip.X, _zone.Left + demi, Math.Max(_zone.Left + demi, _zone.Right - demi));
        _yPieds = _zone.Bottom;
        _cible = _x;
        _zoneConnue = true;
        return true;
    }

    // Promenade de la visite : quelques pas, quelle que soit son humeur (les sessions fictives travaillent).
    private bool MarcheVisite(double dt, double min, double max)
    {
        if (_marcheVers is not { } vise) return false;
        vise = Math.Clamp(vise, min, max);
        double ecart = vise - _x;
        if (Math.Abs(ecart) < 2)
        {
            _marcheVers = null;
            return false;
        }
        _sens = Math.Sign(ecart);
        _x += _sens * Math.Min(Math.Abs(ecart), 46 * K * dt);
        return true;
    }

    // ---- Visite guidée

    public void VisiteGuidee(string? chronologie)
    {
        if (!_demo) return; // jamais sur le vrai Pilou : la visite s'appuie sur les données fictives
        _cheminChronologie = chronologie;
        // Les scènes que cet exe ne connaît pas encore (Défense du bureau, Expéditions, rayon Ensembles…) sont
        // sautées sans temps mort ; la chronologie les note jouee: false (carton « Bientôt » au montage).
        var plan = Tournage.Planifier(Tournage.Disponible);
        foreach (var (etape, debut, jouee) in plan)
        {
            var e = etape;
            if (jouee) Plus(debut * 1000, () => JouerEtape(e));
            else Plus(debut * 1000, () => _chronologie.Add(new Moment(e.Nom, (long)Epoque, false)));
        }
        double fin = plan.Count == 0 ? 0 : plan.Max(x => x.Debut + (x.Jouee ? x.Etape.Secondes : 0));
        Plus(fin * 1000, FinVisite);
    }

    private void Plus(double ms, Action action)
    {
        var m = new DispatcherTimer(DispatcherPriority.Normal, Dispatcher) { Interval = TimeSpan.FromMilliseconds(Math.Max(1, ms)) };
        m.Tick += (_, _) =>
        {
            m.Stop();
            try
            {
                action();
            }
            catch (Exception e)
            {
                // une étape qui rate ne doit pas arrêter le tournage : on la note pour le montage
                _chronologie.Add(new Moment("erreur : " + e.Message, (long)Epoque, false));
            }
        };
        m.Start();
    }

    private void JouerEtape(EtapeVisite etape)
    {
        var nom = etape.Nom;
        _chronologie.Add(new Moment(nom, (long)Epoque));
        double duree = etape.Secondes * 1000;
        double demi = Scene.Largeur / 2 * K;
        switch (nom)
        {
            case "accueil":
                ToutLu();
                _tSaut = Maintenant;
                Dire("salut ! moi c'est Pilou", 2800);
                break;
            case "promenade":
                _marcheVers = _x - 160 * K;
                Plus(duree * 0.55, () => _marcheVers = _x + 110 * K);
                break;
            case "attente":
                // Une IA t'attend (session fictive « site ») : il court sous la souris, qui part vers la gauche.
                var depart = VersEcran.Transform(new Point(_x + 140 * K, _zone.Bottom - 260 * K));
                var arrivee = VersEcran.Transform(new Point(Math.Max(_zone.Left + demi, _x - 260 * K), _zone.Bottom - 260 * K));
                Glisser(depart, 400, () =>
                {
                    SessionDemo("demo-site", "permission");
                    Plus(500, () => Glisser(arrivee, 2600));
                });
                Plus(duree - 500, () =>
                {
                    SessionDemo("demo-site", "");
                    ToutLu();
                });
                break;
            case "menu":
                MenuVisite(duree);
                break;
            case "boutique":
            {
                var b = new FenetreBoutique(this, Math.Max(0, Niveau - 4));
                PoserSurEcran(b);
                b.Show();
                Plus(3500, () => b.Visiter(PilouBureau.Boutique.Tete));
                Plus(5800, () => b.Visiter(PilouBureau.Boutique.Tete, "haut-de-forme"));
                Plus(duree - 600, b.Close);
                break;
            }
            case "amis":
            {
                var a = new FenetreListeAmis(this);
                PoserSurEcran(a);
                a.Show();
                Plus(duree - 600, a.Close);
                break;
            }
            case "boutique-ensembles" when Tournage.RayonEnsembles() is { } rayon:
            {
                var b = new FenetreBoutique(this, Math.Max(0, Niveau - 4), rayon);
                PoserSurEcran(b);
                b.Show();
                Plus(duree - 600, b.Close);
                break;
            }
            case "visite-jeu":
                _visites.Sortie = null; // rentré : il peut recevoir Léo
                Essai("visite:jeu");
                Plus(duree - 300, () => Appliquer(_visites.Congedier(MesAmis.Moi.Code, Epoque, "fini")));
                break;
            case "meteo":
                Essai("meteo:pluie:parapluie");
                Plus(duree - 300, () =>
                {
                    _essaiMeteo = "";
                    _essaiObjet = "";
                });
                break;
            case "etoile":
                Essai("etoile");
                Plus(duree - 300, () => Arreter(""));
                break;
            case "tape":
                Essai("tape");
                Plus(duree - 300, () => Arreter(""));
                break;
            case "icone":
                IconeVisite(duree);
                break;
            case "fin":
                _salueJusque = Maintenant + 2200;
                Dire("à bientôt !", 2600);
                break;
            default:
                // Scène --essai= (clavier, photo, visite, évolution, et les nouvelles : défense, expéditions…).
                if (etape.Scene is not { } scene) break;
                Essai(scene);
                if (etape.Optionnelle) Plus(duree - 300, () => { if (_jeuEnCours != Jeu.Aucun) Arreter(""); });
                break;
        }
    }

    private void FinVisite()
    {
        _chronologie.Add(new Moment("fin-visite", (long)Epoque));
        if (_cheminChronologie is { } chemin)
        {
            try
            {
                File.WriteAllText(chemin, Tournage.Chronologie(_chronologie, Mise.Actuelle));
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException)
            {
                // pas de chronologie : la vidéo reste bonne
            }
        }
        Application.Current.Shutdown();
    }

    // Une session fictive du dossier de démo qui se met à attendre (ou n'attend plus). Jamais hors démo.
    private void SessionDemo(string session, string attente)
    {
        if (!_demo) return;
        var chemin = Path.Combine(_dossier, $"etat-{session}.json");
        try
        {
            if (JsonNode.Parse(File.ReadAllText(chemin)) is not JsonObject e) return;
            long t = (long)Epoque;
            e["attente"] = attente;
            e["t"] = t;
            e["debutOutil"] = t;
            File.WriteAllText(chemin, e.ToJsonString());
        }
        catch (Exception e) when (e is IOException or JsonException or UnauthorizedAccessException)
        {
            // pas de session fictive : l'étape passe sans
        }
    }

    // Une fenêtre de Pilou (boutique, amis) au milieu de l'écran où il est, à la taille de cet écran.
    private void PoserSurEcran(Window w)
    {
        var z = ZoneSous(_x, _yPieds - 10);
        w.WindowStartupLocation = WindowStartupLocation.Manual;
        w.Width = Math.Min(w.Width, z.Width * 0.94);
        w.Height = Math.Min(w.Height, z.Height * 0.92);
        w.MinWidth = Math.Min(w.MinWidth, w.Width);
        w.MinHeight = Math.Min(w.MinHeight, w.Height);
        w.Left = z.Left + (z.Width - w.Width) / 2;
        w.Top = z.Top + (z.Height - w.Height) / 2;
    }

    // ---- Souris

    // La souris glisse jusqu'à un point (pixels de ce processus), en douceur, puis « ensuite ».
    private void Glisser(Point cible, double ms, Action? ensuite = null)
    {
        var (sx, sy) = Natif.Souris();
        var depart = sx == int.MinValue ? cible : new Point(sx, sy);
        var chrono = Stopwatch.StartNew();
        var m = new DispatcherTimer(DispatcherPriority.Input, Dispatcher) { Interval = TimeSpan.FromMilliseconds(15) };
        m.Tick += (_, _) =>
        {
            double a = Math.Min(1, chrono.Elapsed.TotalMilliseconds / Math.Max(1, ms)), e = a * a * (3 - 2 * a);
            Natif.PlacerSouris((int)Math.Round(depart.X + (cible.X - depart.X) * e), (int)Math.Round(depart.Y + (cible.Y - depart.Y) * e));
            if (a < 1) return;
            m.Stop();
            ensuite?.Invoke();
        };
        m.Start();
    }

    private static Point? Centre(FrameworkElement e)
    {
        if (!e.IsVisible || PresentationSource.FromVisual(e) is null) return null;
        return e.PointToScreen(new Point(Math.Min(e.ActualWidth / 2, 60), e.ActualHeight / 2));
    }

    // Survol d'une entrée ; dans un sous-menu, la main va d'abord à l'horizontale (sinon, en passant en diagonale
    // sur les entrées voisines du menu parent, WPF refermerait le sous-menu en route).
    private void Survoler(FrameworkElement? e, double ms = 380, bool horizontalDabord = false)
    {
        if (e is null || Centre(e) is not { } p) return;
        var (sx, sy) = Natif.Souris();
        if (horizontalDabord && sx != int.MinValue) Glisser(new Point(p.X, sy), ms * 0.6, () => Glisser(p, ms * 0.4));
        else Glisser(p, ms);
    }

    // ---- Le vrai menu clic droit : ouvert sur Pilou, survol de quelques entrées, sous-menus

    private static MenuItem? EntreeMenu(ItemsControl parent, string debut) =>
        parent.Items.OfType<MenuItem>().FirstOrDefault(m => m.Header is string h && h.StartsWith(debut, StringComparison.Ordinal));

    private void MenuVisite(double duree)
    {
        if (_scene.ContextMenu is not { } menu) return;
        var tete = VersEcran.Transform(new Point(_x, _yPieds - 14 * Scene.PA * K));
        Glisser(tete, 600, () =>
        {
            menu.PlacementTarget = _scene;
            menu.Placement = PlacementMode.MousePoint;
            menu.IsOpen = true;
        });
        Plus(1600, () => Survoler(EntreeMenu(menu, "🛒 Boutique")));
        Plus(2500, () => Survoler(EntreeMenu(menu, "♥ Caresser")));
        double t = 3400;
        foreach (var (nom, enfants) in new[] { ("Couleur", 2), ("Ce qu'il porte", 1), ("Intégrations", 2), ("Quêtes", 1) })
        {
            SousMenu(menu, nom, t, enfants);
            t += 1100 + enfants * 700;
        }
        Plus(duree - 800, () =>
        {
            foreach (var m in menu.Items.OfType<MenuItem>()) m.IsSubmenuOpen = false;
            menu.IsOpen = false;
        });
    }

    private void SousMenu(ContextMenu menu, string nom, double t, int enfants)
    {
        Plus(t, () =>
        {
            if (!menu.IsOpen) return;
            foreach (var autre in menu.Items.OfType<MenuItem>().Where(m => m.IsSubmenuOpen)) autre.IsSubmenuOpen = false;
            Survoler(EntreeMenu(menu, nom));
        });
        Plus(t + 500, () =>
        {
            if (menu.IsOpen && EntreeMenu(menu, nom) is { HasItems: true } m) m.IsSubmenuOpen = true;
        });
        for (int i = 0; i < enfants; i++)
        {
            int n = i;
            Plus(t + 1100 + i * 700, () =>
            {
                if (!menu.IsOpen || EntreeMenu(menu, nom) is not { IsSubmenuOpen: true } m) return;
                var cible = m.Items.OfType<MenuItem>().Where(x => x.IsEnabled).Skip(n).FirstOrDefault()
                            ?? m.Items.OfType<MenuItem>().Skip(n).FirstOrDefault();
                Survoler(cible, 420, horizontalDabord: n == 0);
            });
        }
    }

    // ---- L'icône près de l'horloge et son menu

    private void IconeVisite(double duree)
    {
        if (_zoneNotif is null) return;
        // Sur cet écran : près de l'icône si elle y est ; sinon en bas à droite, là où est l'horloge.
        var pieds = VersEcran.Transform(new Point(_x, _yPieds - 10));
        var travail = Natif.ZoneTravail((int)pieds.X, (int)pieds.Y);
        var (x, y) = (travail.Right - 30, travail.Bottom - 4);
        if (_zoneNotif.PositionIcone() is { } icone && icone.X >= travail.Left && icone.X < travail.Right
            && icone.Y >= travail.Top - 2 && icone.Y <= travail.Bottom + 80)
            (x, y) = icone;
        Glisser(new Point(x, y), 700, () =>
        {
            Plus(duree - 1400, ZoneNotification.FermerMenu);
            // Le menu natif est modal : il rend la main à sa fermeture (les minuteurs tournent pendant).
            Dispatcher.BeginInvoke(() => _zoneNotif?.MontrerMenu(x, y));
        });
    }
}
