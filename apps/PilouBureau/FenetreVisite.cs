using System.Diagnostics;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Interop;
using System.Windows.Threading;

namespace PilouBureau;

// Tournage (outils/tourner-ecran-gauche.ps1) : Pilou posé sur l'écran choisi pour cette session (--ecran=, --placer=),
// et la visite guidée (--visite-guidee) qui joue les vrais menus et fenêtres, l'une après l'autre (Tournage.Etapes),
// en mode démo : profil, amis et réglages fictifs en mémoire, sessions fictives du dossier de démo.
// La souris glisse d'elle-même (SetCursorPos) : le survol des menus est le vrai, celui de WPF.
// Pendant la visite : un décor de bureau fictif derrière (DecorTournage.cs), Pilou en grand, les fenêtres posées à
// côté de lui, et un journal écrit au fil de l'eau (JournalVisite) : étapes, rectangles de cadrage pour le montage,
// erreurs. Une étape qui échoue est notée et la visite continue.
public sealed partial class FenetrePilou
{
    private readonly bool _demo;
    private Point? _poseEcran;                 // pixels de ce processus
    private double? _marcheVers;               // promenade de la visite : là où il va (unités WPF)
    private JournalVisite? _journal;
    private Cadreur? _cadreur;
    private DispatcherTimer? _cadrage;
    private FenetreDecor? _decor;
    private CadreEcran? _ecranVisite;

    // ---- Placement pour cette session

    public void PoserSur(int x, int y) => _poseEcran = new Point(x, y);

    private bool PlacerSurDemande()
    {
        if (_poseEcran is not { } p) return false;
        var dip = VersWpf.Transform(p);
        _zone = ZoneSous(dip.X, dip.Y);
        // Tournage : Pilou en grand (×2 environ), pour cette session seulement (les réglages ne sont pas écrits).
        if (_demo)
        {
            _reglages.Taille = Tournage.TailleTournage(_zone.Height);
            AppliquerTaille();
        }
        var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);
        _x = Math.Clamp(dip.X, min, max);
        _yPieds = _zone.Bottom;
        _cible = _x;
        _zoneConnue = true;
        return true;
    }

    // Avec le décor, le sol est le haut de la fausse barre des tâches (pixels d'écran).
    private void SolDuDecor(ref Natif.Rect r, int x, int y)
    {
        if (_decor is not { } d || x < d.Ecran.X || x >= d.Ecran.Droite || y < d.Ecran.Y || y >= d.Ecran.Bas) return;
        r.Bottom = Math.Min(r.Bottom, d.HautBarre);
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

    // Avant tout : le journal (pour noter même une erreur du démarrage), l'écran filmé et son décor.
    public void PreparerVisite(string? chronologie, CadreEcran? ecran, FenetreDecor? decor)
    {
        if (!_demo) return;
        _ecranVisite = ecran;
        _decor = decor;
        _journal = new JournalVisite(chronologie, Mise.Actuelle, ecran, () => (long)Epoque);
    }

    // Une erreur qui a échappé aux étapes (minuteur, rendu…) : notée, et la visite continue.
    public void ErreurVisite(Exception e) => _journal?.Erreur(_journal.EtapeCourante is { Length: > 0 } x ? x : "demarrage", e);

    public void VisiteGuidee(string? chronologie)
    {
        if (!_demo) return; // jamais sur le vrai Pilou : la visite s'appuie sur les données fictives
        _journal ??= new JournalVisite(chronologie, Mise.Actuelle, _ecranVisite, () => (long)Epoque);
        // Les scènes que cet exe ne connaît pas encore (Défense du bureau, Expéditions, rayon Ensembles…) sont
        // sautées sans temps mort ; la chronologie les note jouee: false (carton « Bientôt » au montage).
        var plan = Tournage.Planifier(Tournage.Disponible);
        foreach (var (etape, debut, jouee) in plan)
        {
            var e = etape;
            if (jouee) Plus(debut * 1000, () => JouerEtape(e));
            else Plus(debut * 1000, () => _journal.Etape(e.Nom, false));
        }
        double fin = plan.Count == 0 ? 0 : plan.Max(x => x.Debut + (x.Jouee ? x.Etape.Secondes : 0));
        Plus(fin * 1000, FinVisite);
        // Cadrage pour le montage : la zone d'intérêt, observée cinq fois par seconde.
        if (_ecranVisite is { } ecran)
        {
            _cadreur = new Cadreur(ecran);
            _cadrage = new DispatcherTimer(TimeSpan.FromMilliseconds(200), DispatcherPriority.Background, (_, _) => Cadrer(), Dispatcher);
            _cadrage.Start();
        }
    }

    private void Plus(double ms, Action action)
    {
        var m = new DispatcherTimer(DispatcherPriority.Normal, Dispatcher) { Interval = TimeSpan.FromMilliseconds(Math.Max(1, ms)) };
        m.Tick += (_, _) =>
        {
            m.Stop();
            // une étape qui rate ne doit pas arrêter le tournage : on la note (chronologie, erreurs.txt) et on continue
            if (_journal is { } j) j.Executer(j.EtapeCourante, action);
            else
                try
                {
                    action();
                }
                catch (Exception e) when (e is InvalidOperationException or ArgumentException or NullReferenceException)
                {
                    // hors visite : rien à noter
                }
        };
        m.Start();
    }

    private void JouerEtape(EtapeVisite etape)
    {
        var nom = etape.Nom;
        // Ce qu'une étape précédente aurait laissé ouvert (elle a pu échouer en route) : rangé d'abord.
        _journal?.Executer(nom, RangerVisite);
        _journal?.Etape(nom);
        double duree = etape.Secondes * 1000;
        double demi = Scene.Largeur / 2 * K;
        switch (nom)
        {
            case "accueil":
                ToutLu();
                _tSaut = Maintenant;
                Dire("salut ! moi c'est Pilou", 2200);
                break;
            case "promenade":
                _marcheVers = _x - 120 * K;
                Plus(duree * 0.55, () => _marcheVers = _x + 90 * K);
                break;
            case "attente":
                // Une IA t'attend (session fictive « site ») : il court sous la souris, qui part vers la gauche.
                var depart = VersEcran.Transform(new Point(_x + 140 * K, _zone.Bottom - 200 * K));
                var arrivee = VersEcran.Transform(new Point(Math.Max(_zone.Left + demi, _x - 200 * K), _zone.Bottom - 200 * K));
                Glisser(depart, 300, () =>
                {
                    SessionDemo("demo-site", "permission");
                    Plus(300, () => Glisser(arrivee, 2200));
                });
                Plus(duree - 400, () =>
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
                PoserPresDePilou(b);
                b.Show();
                Plus(2000, () => b.Visiter(PilouBureau.Boutique.Tete));
                Plus(3800, () => b.Visiter(PilouBureau.Boutique.Tete, "haut-de-forme"));
                Plus(duree - 500, b.Close);
                break;
            }
            case "amis":
            {
                var a = new FenetreListeAmis(this);
                PoserPresDePilou(a);
                a.Show();
                Plus(duree - 400, a.Close);
                break;
            }
            case "boutique-ensembles" when Tournage.RayonEnsembles() is { } rayon:
            {
                var b = new FenetreBoutique(this, Math.Max(0, Niveau - 4), rayon);
                PoserPresDePilou(b);
                b.Show();
                Plus(duree - 400, b.Close);
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
            case "defense":
                // La bande de Défense du bureau, Pilou joue seul ; elle se referme avant l'étape suivante.
                Essai("defense");
                Plus(duree - 300, () => _defense?.Close());
                break;
            case "expedition-journal":
                Essai("expedition:journal");
                Plus(duree - 300, () => _fenetreExp?.Close());
                break;
            case "icone":
                IconeVisite(duree);
                break;
            case "fin":
                _salueJusque = Maintenant + 2000;
                Dire("à bientôt !", 2200);
                break;
            default:
                // Scène --essai= (clavier, photo, visite, évolution, et les nouvelles : défense, expéditions…).
                if (etape.Scene is not { } scene) break;
                Essai(scene);
                if (etape.Optionnelle) Plus(duree - 300, () => { if (_jeuEnCours != Jeu.Aucun) Arreter(""); });
                break;
        }
    }

    // Ferme ce qui traîne : menus, fenêtres de Pilou (pas Léo, pas le décor).
    private void RangerVisite()
    {
        if (_scene.ContextMenu is { IsOpen: true } menu)
        {
            foreach (var m in menu.Items.OfType<MenuItem>()) m.IsSubmenuOpen = false;
            menu.IsOpen = false;
        }
        ZoneNotification.FermerMenu();
        foreach (var w in Application.Current.Windows.OfType<Window>().ToList())
            if (w != this && w is not FenetreDecor && w is not FenetreInvite && w.IsVisible) w.Close();
    }

    private void FinVisite()
    {
        _cadrage?.Stop();
        if (_journal is { } j)
        {
            j.Cadre(_cadreur?.Fermer((long)Epoque));
            j.Etape("fin-visite");
            j.Terminer();
        }
        Application.Current.Shutdown();
    }

    // ---- Cadrage pour le montage

    private static CadreEcran? EnPixels(FrameworkElement e)
    {
        if (!e.IsVisible || e.ActualWidth <= 0 || PresentationSource.FromVisual(e) is null) return null;
        var a = e.PointToScreen(new Point(0, 0));
        var b = e.PointToScreen(new Point(e.ActualWidth, e.ActualHeight));
        return CadreEcran.DeBords((int)Math.Floor(Math.Min(a.X, b.X)), (int)Math.Floor(Math.Min(a.Y, b.Y)),
            (int)Math.Ceiling(Math.Max(a.X, b.X)), (int)Math.Ceiling(Math.Max(a.Y, b.Y)));
    }

    private static string NomFenetre(Window w) => w switch
    {
        FenetreBoutique => "boutique",
        FenetreListeAmis => "amis",
        FenetreExpeditions => "expeditions",
        FenetreDefense => "defense",
        FenetreInvite => "leo",
        _ => "fenetre",
    };

    // Ce qui compte à l'image en ce moment : Pilou et sa bulle, le menu et ses sous-menus, les fenêtres ouvertes,
    // ou le menu de l'icône près de l'horloge (avec l'icône).
    private void Cadrer()
    {
        if (_journal is not { } j || _cadreur is null) return;
        var t = (long)Epoque;
        var zone = new CadreEcran(0, 0, 0, 0);
        var quoi = new List<string>();
        if (Natif.MenuNatif() is { } natif)
        {
            zone = natif;
            if (_decor?.CadreIcone() is { } icone) zone = zone.Union(icone);
            quoi.Add("menu-icone");
        }
        else
        {
            if (IsVisible && EnPixels(_scene) is { } pilou)
            {
                zone = pilou;
                quoi.Add("pilou");
                if (_pileBulle.Visibility == Visibility.Visible && EnPixels(_bulle) is { } bulle)
                {
                    zone = zone.Union(bulle);
                    quoi.Add("bulle");
                }
            }
            var popups = Natif.FenetresPopup();
            if (popups.Count > 0)
            {
                foreach (var p in popups)
                    zone = zone.Union(new CadreEcran((int)p.X, (int)p.Y, (int)p.Largeur, (int)p.Hauteur));
                bool menu = _scene.ContextMenu is { IsOpen: true };
                quoi.Add(menu ? (popups.Count > 1 ? "menu+sous-menu" : "menu") : "info-bulle");
            }
            foreach (var w in Application.Current.Windows.OfType<Window>())
            {
                if (w == this || w is FenetreDecor || !w.IsVisible) continue;
                var h = new WindowInteropHelper(w).Handle;
                if (Natif.CadreFenetre(h) is not { } c) continue;
                zone = zone.Union(c);
                quoi.Add(NomFenetre(w));
            }
        }
        j.Cadre(_cadreur.Observer(j.EtapeCourante, string.Join("+", quoi), zone, t));
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

    // Une fenêtre de Pilou (boutique, amis, expéditions) posée à côté de lui, en bas de l'écran où il est
    // (Tournage.PoserPres) : Pilou et la fenêtre tiennent dans un même cadre, que le montage peut zoomer.
    private void PoserPresDePilou(Window w)
    {
        var z = ZoneSous(_x, _yPieds - 10);
        var p = Tournage.PoserPres(new Place(z.X, z.Y, z.Width, z.Height), _x, Scene.W * Scene.P / 2 * K, w.Width, w.Height);
        w.WindowStartupLocation = WindowStartupLocation.Manual;
        w.MinWidth = Math.Min(w.MinWidth, p.Largeur);
        w.MinHeight = Math.Min(w.MinHeight, p.Hauteur);
        w.Width = p.Largeur;
        w.Height = p.Hauteur;
        w.Left = p.X;
        w.Top = p.Y;
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
            if (ensuite is null) return;
            if (_journal is { } j) j.Executer(j.EtapeCourante, ensuite);
            else ensuite();
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
    private void Survoler(FrameworkElement? e, double ms = 340, bool horizontalDabord = false)
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
        Glisser(tete, 500, () =>
        {
            menu.PlacementTarget = _scene;
            menu.Placement = PlacementMode.MousePoint;
            menu.IsOpen = true;
        });
        Plus(1200, () => Survoler(EntreeMenu(menu, "🛒 Boutique")));
        double t = 1900;
        foreach (var (nom, enfants) in new[] { ("Couleur", 2), ("Intégrations", 2) })
        {
            SousMenu(menu, nom, t, enfants);
            t += 1000 + enfants * 650;
        }
        Plus(duree - 500, () =>
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
        Plus(t + 450, () =>
        {
            if (menu.IsOpen && EntreeMenu(menu, nom) is { HasItems: true } m) m.IsSubmenuOpen = true;
        });
        for (int i = 0; i < enfants; i++)
        {
            int n = i;
            Plus(t + 1000 + i * 650, () =>
            {
                if (!menu.IsOpen || EntreeMenu(menu, nom) is not { IsSubmenuOpen: true } m) return;
                var cible = m.Items.OfType<MenuItem>().Where(x => x.IsEnabled).Skip(n).FirstOrDefault()
                            ?? m.Items.OfType<MenuItem>().Skip(n).FirstOrDefault();
                Survoler(cible, 380, horizontalDabord: n == 0);
            });
        }
    }

    // ---- L'icône près de l'horloge et son menu

    private void IconeVisite(double duree)
    {
        if (_zoneNotif is null) return;
        int x, y;
        if (_decor?.PositionIcone() is { } fausse)
        {
            // Avec le décor : la fausse icône de Pilou, dans la fausse barre des tâches.
            (x, y) = fausse;
        }
        else
        {
            // Sur cet écran : près de l'icône si elle y est ; sinon en bas à droite, là où est l'horloge.
            var pieds = VersEcran.Transform(new Point(_x, _yPieds - 10));
            var travail = Natif.ZoneTravail((int)pieds.X, (int)pieds.Y);
            (x, y) = (travail.Right - 30, travail.Bottom - 4);
            if (_zoneNotif.PositionIcone() is { } icone && icone.X >= travail.Left && icone.X < travail.Right
                && icone.Y >= travail.Top - 2 && icone.Y <= travail.Bottom + 80)
                (x, y) = icone;
        }
        Glisser(new Point(x, y), 600, () =>
        {
            Plus(duree - 1100, ZoneNotification.FermerMenu);
            // Le menu natif est modal : il rend la main à sa fermeture (les minuteurs tournent pendant).
            Dispatcher.BeginInvoke(() => _journal?.Executer("icone", () => _zoneNotif?.MontrerMenu(x, y)));
        });
    }
}
