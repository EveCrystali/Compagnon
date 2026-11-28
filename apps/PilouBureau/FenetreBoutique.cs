using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace PilouBureau;

// Boutique rétro (gratuite, aucune vraie monnaie) : bandeau niveau / XP / po, enseigne néon, onglets
// pixel par rayon, étagères par rangée de niveau, aperçu à gauche (essayer, acheter, porter).
// Chaque état d'un objet a un signe de forme, pas seulement une couleur :
//   cadenas + « NIV 15 » (fermé), ◉ (achetable), ◌ + « manque N » (trop cher), ✓ (à toi), ★ (porté),
//   ⌛ (saison : jours restants, ou « revient en … »), ✧ (de passage en vitrine). Rareté : un liseré de couleur
//   et son signe (· ◇ ◆ ✦ ★ ✺). Onglet « Ensembles » : progression 3/6, bonus porté ; compteur de collection.
internal sealed class FenetreBoutique : Window
{
    private const string Vitrine = "vitrine";

    private readonly FenetrePilou _pilou;
    private readonly int _vuAvant;
    private readonly Bandeau _bandeau = new();
    private readonly WrapPanel _onglets = new() { Margin = new Thickness(0, 0, 0, 6) };
    private readonly StackPanel _etageres = new() { Margin = new Thickness(0, 0, 8, 12) };
    private readonly ScrollViewer _defile;
    // Hauteur : celle de Pilou en dessin fin au zoom net le plus grand (4 unités par pixel de grille : 224), plus sa marge.
    private readonly Grid _scene = new() { Width = 256, Height = 228, ClipToBounds = true };
    private uint[]? _pilouPixels;
    private readonly TextePixel _nom = Texte(15, Bandeau.ArgentClair, gras: true);
    private readonly TextePixel _detail = Texte(11.5, Bandeau.Argent);
    private readonly TextePixel _message = Texte(11.5, Bandeau.Violet);
    private readonly TextePixel _collection = Texte(11.5, Bandeau.ArgentClair, gras: true);
    private readonly StackPanel _jaugeCollection = new() { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
    private readonly BoutonPixel _essayer = Bouton("Essayer"), _acheter = Bouton("Acheter", true), _porter = Bouton("Porter");
    private readonly DispatcherTimer _horloge = new() { Interval = TimeSpan.FromMilliseconds(140) };
    private readonly List<Pixels> _pieces = new();
    private readonly Grid _enseigne;
    private readonly TextePixel _enseigneTexte;
    private List<(int[,] Motif, Brush?[] Palette)> _imagesPiece = new();
    private string _rayon = Vitrine;
    private Article? _choisi;
    private bool _essai = true;
    private double _t;
    private Image? _pilouVu;

    private static readonly Brush Fond = Gel("#0f1324"), Planche = Gel("#3b4654"), PlancheClaire = Gel("#768390"),
        Case = Gel("#1f2540"), CaseSurvol = Gel("#2a3156"), Ferme = Gel("#3b4654"), Achetable = Gel("#6cb6ff"), TropCher = Gel("#768390"),
        AToi = Gel("#9b8cff"), Porte = Gel("#f69d50"), Neon = Gel("#f69d50"), NeonClair = Gel("#ffd8b0"), NeonViolet = Gel("#9b8cff"),
        Sol = Gel("#16365e"), Ciel = Gel("#0d2a4d");

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    // Police pixel de Pilou (docs/STYLE.md) : les anciennes tailles du système deviennent « corps » (plancher de lisibilité de
    // docs/STYLE.md : jamais de minuscules en « petit ») ; gras : la police « titre ».
    private static TextePixel Texte(double taille, Brush couleur, bool gras = false) =>
        StylePixel.Texte("", couleur, taille >= 20 ? StylePixel.Grand : StylePixel.Corps, gras);

    private static BoutonPixel Bouton(string texte, bool principal = false) =>
        new(texte, principal, StylePixel.Corps) { Margin = new Thickness(0, 0, 6, 4) };

    public FenetreBoutique(FenetrePilou pilou, int vuAvant, string rayon = Vitrine)
    {
        _pilou = pilou;
        _vuAvant = vuAvant;
        _rayon = rayon;
        Title = "Boutique de Pilou";
        Width = 1060;
        Height = 760;
        MinWidth = 780;
        MinHeight = 520;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = Fond;
        UseLayoutRounding = true;

        // Enseigne néon « BOUTIQUE » : orange qui grésille doucement (immobile si les animations sont coupées).
        _enseigne = StylePixel.Enseigne("BOUTIQUE", Neon, NeonViolet, 5);
        _enseigne.HorizontalAlignment = HorizontalAlignment.Center;
        _enseigne.Margin = new Thickness(0, 0, 0, 4);
        _enseigneTexte = (TextePixel)_enseigne.Children[^1];
        var sousTitre = Texte(11.5, Bandeau.Argent);
        sousTitre.Texte = "Ton niveau ouvre les rangées, tes pièces d'or achètent. Tout est gratuit : les po se gagnent en quêtes.";
        sousTitre.HorizontalAlignment = HorizontalAlignment.Center;

        var racine = new Grid { Margin = new Thickness(14, 10, 14, 10) };
        racine.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        racine.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        racine.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        racine.Children.Add(_bandeau);
        var tete = new StackPanel { Margin = new Thickness(0, 4, 0, 8) };
        tete.Children.Add(_enseigne);
        tete.Children.Add(sousTitre);
        _collection.HorizontalAlignment = HorizontalAlignment.Center;
        _collection.Margin = new Thickness(0, 4, 0, 2);
        tete.Children.Add(_collection);
        tete.Children.Add(_jaugeCollection);
        Grid.SetRow(tete, 1);
        racine.Children.Add(tete);

        var corps = new Grid();
        corps.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(330) });
        corps.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        Grid.SetRow(corps, 2);
        racine.Children.Add(corps);
        corps.Children.Add(PanneauApercu());
        _defile = new ScrollViewer { Content = _etageres, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        var droite = new DockPanel { Margin = new Thickness(14, 0, 0, 0) };
        DockPanel.SetDock(_onglets, Dock.Top);
        droite.Children.Add(_onglets);
        droite.Children.Add(_defile);
        Grid.SetColumn(droite, 1);
        corps.Children.Add(droite);
        Content = racine;
        StylePixel.Defileur(this);
        HabillageFenetre.Poser(this);

        _essayer.Click += (_, _) =>
        {
            _essai = !_essai;
            MontrerApercu();
        };
        _acheter.Click += (_, _) => Acheter();
        _porter.Click += (_, _) => Porter();
        if (Pixels.DeSprite("po-tourne") is not null)
            for (int i = 0; i < 8; i++)
                if (Pixels.DeSprite("po-tourne", i * 120) is { } d) _imagesPiece.Add(d);
        _horloge.Tick += (_, _) => Animer();
        Loaded += (_, _) => { if (Bandeau.Anime) _horloge.Start(); };
        Closed += (_, _) => _horloge.Stop();
        PreviewKeyDown += (_, e) => { if (e.Key == Key.Escape) Close(); };
        Remplir();
    }

    // Visite guidée (FenetreVisite.cs) : un rayon, et un objet que Pilou essaie dans l'aperçu.
    internal void Visiter(string rayon, string? article = null)
    {
        _rayon = rayon;
        if (article is not null && Boutique.Trouver(article) is { } a)
        {
            _choisi = a;
            _essai = true;
            _message.Texte = "";
        }
        Remplir();
        _defile.ScrollToTop();
    }

    // ---- Aperçu (gauche)

    private UIElement PanneauApercu()
    {
        var pile = new StackPanel();
        var cadre = new Border
        {
            BorderBrush = Gel("#6a5acd"), BorderThickness = new Thickness(3), Background = Ciel, Child = _scene,
            HorizontalAlignment = HorizontalAlignment.Left, SnapsToDevicePixels = true,
        };
        RenderOptions.SetBitmapScalingMode(_scene, BitmapScalingMode.NearestNeighbor);
        pile.Children.Add(Titre("ESSAYAGE", Bandeau.Violet));
        pile.Children.Add(cadre);
        _nom.Margin = new Thickness(0, 8, 0, 0);
        pile.Children.Add(_nom);
        pile.Children.Add(_detail);
        var boutons = new WrapPanel { Margin = new Thickness(0, 8, 0, 4) };
        boutons.Children.Add(_essayer);
        boutons.Children.Add(_acheter);
        boutons.Children.Add(_porter);
        pile.Children.Add(boutons);
        _message.Margin = new Thickness(0, 4, 0, 0);
        pile.Children.Add(_message);
        return new Border
        {
            Background = Gel("#151a2e"), BorderBrush = Gel("#2d333b"), BorderThickness = new Thickness(2), Padding = new Thickness(12),
            Child = pile,
        };
    }

    // Titre d'enseigne (« ESSAYAGE », « RANGÉE NIV 5 ») : police « titre », ombre d'un pixel. taille 2 : petit ; 3 : corps.
    private static Grid Titre(string texte, Brush couleur, double taille = 2)
    {
        var t = StylePixel.Enseigne(texte, couleur, Bandeau.Encre, taille >= 3 ? StylePixel.Corps : StylePixel.Petit);
        t.Margin = new Thickness(0, 0, 0, 6);
        return t;
    }

    private Allure AllureApercu(Article? essai)
    {
        var (_, _, equipe) = _pilou.EtatBourse();
        var porte = Boutique.Porte(equipe);
        if (essai is not null && _essai && Boutique.Slots.Contains(essai.Slot)) porte[essai.Slot] = essai.Id;
        var a = new Allure
        {
            T = _t, Stade = _pilou.StadePilou,
            Couleur = Teinte(porte.GetValueOrDefault(Boutique.Couleur, "")) is { Length: > 0 } c ? c : _pilou.CouleurDeBase,
            Objets = porte.Where(kv => Boutique.SurPilou(kv.Key)).Select(kv => kv.Value).Concat(Boutique.BonusPortes(porte)).ToList(),
            Accessoire = essai is { Slot: Boutique.Accessoire } && _essai ? essai.Id : _pilou.AccessoireChoisi,
            Expr = essai is not null && _essai ? "fete" : "repos",
        };
        return a;
    }

    private static string Teinte(string id) => id.StartsWith("couleur-") ? id["couleur-".Length..] : id;

    private void MontrerApercu()
    {
        var (solde, inventaire, equipe) = _pilou.EtatBourse();
        _scene.Children.Clear();
        var porte = Boutique.Porte(equipe);
        string fond = _choisi is { Slot: Boutique.Fond } && _essai ? _choisi.Id : porte.GetValueOrDefault(Boutique.Fond, "");
        if (fond != "" && Apercu.Sprite(fond, _t) is { } decor)
            _scene.Children.Add(Apercu.Vue(decor, 4));
        else
        {
            // Sans décor : un sol de scène et quelques étoiles.
            _scene.Children.Add(new Border { Background = Sol, Height = 40, VerticalAlignment = VerticalAlignment.Bottom });
            foreach (var (x, y) in new[] { (20, 18), (70, 40), (200, 26), (230, 70), (140, 12), (40, 90) })
                _scene.Children.Add(new Border
                {
                    Width = 4, Height = 4, Background = Gel("#b4dbff"), HorizontalAlignment = HorizontalAlignment.Left,
                    VerticalAlignment = VerticalAlignment.Top, Margin = new Thickness(x, y, 0, 0),
                });
        }
        // Dessin fin : Pilou sur la grille 96 × 112, au zoom le plus proche de 3,4 qui met un pixel fin sur un nombre
        // entier de pixels physiques.
        _pilouPixels = null;
        _pilouVu = Apercu.Vue(Apercu.ImageSiChange(AllureApercu(_choisi), ref _pilouPixels, fin: true)!, Finesse.ZoomNet(3.4));
        _pilouVu.HorizontalAlignment = HorizontalAlignment.Center;
        _pilouVu.VerticalAlignment = VerticalAlignment.Bottom;
        _pilouVu.Margin = new Thickness(0, 0, 0, 2);
        _scene.Children.Add(_pilouVu);
        // Cadre de bulle essayé (ou porté) : une petite bulle au-dessus de Pilou.
        string bulle = _choisi is { Slot: Boutique.Bulle } && _essai ? _choisi.Id : porte.GetValueOrDefault(Boutique.Bulle, "");
        if (Boutique.Style(bulle) is { } st) _scene.Children.Add(BulleEssai(st));
        // Bonus et consommables : leur icône à côté de Pilou.
        if (_choisi is not null && Boutique.RayonDe(_choisi.Slot) == Boutique.Speciaux && _choisi.Slot != Boutique.Accessoire
            && Apercu.Sprite(Icone(_choisi.Id)) is { } ic)
        {
            var im = Apercu.Vue(ic, 3);
            im.HorizontalAlignment = HorizontalAlignment.Right;
            im.VerticalAlignment = VerticalAlignment.Bottom;
            im.Margin = new Thickness(0, 0, 12, 10);
            _scene.Children.Add(im);
        }

        if (_choisi is null)
        {
            _nom.Texte = "Choisis un objet sur les étagères";
            _detail.Texte = "Clic sur un objet : Pilou l'essaie ici. Les rangées s'ouvrent avec ton niveau.";
            _essayer.Visibility = _acheter.Visibility = _porter.Visibility = Visibility.Collapsed;
            return;
        }
        var a = _choisi;
        int niveau = _pilou.NiveauActuel, prix = Boutique.Prix(a, Jour);
        bool consommable = a.Slot == Boutique.Consommable, bonus = a.Slot == Boutique.Bonus;
        bool possede = !consommable && inventaire.Contains(a.Id);
        bool porteIci = EstPorte(a, equipe);
        if (a.Recompense) possede = Boutique.PeutPorter(inventaire, a.Slot, a.Id);
        bool dispo = Boutique.Disponible(a, Jour);
        _nom.Texte = $"{Boutique.SigneRarete(a.Rarete)} {a.Nom}";
        string etat = a.Recompense ? (possede ? (porteIci ? "★ porté" : "✓ gagné") : $"▣ à gagner : {CommentGagner(a)}")
            : !Boutique.Ouvert(a, niveau) ? $"🔒 rangée fermée : niveau {a.NiveauMin} (encore {Math.Max(0, Profil.XpPourNiveau(a.NiveauMin) - _pilou.XpTotal)} xp)"
            : porteIci ? "★ porté" : possede ? (bonus ? "✓ actif" : "✓ à toi")
            : !dispo ? Indispo(a)
            : solde >= prix ? $"◉ {prix} po{(prix < a.Prix ? $" (au lieu de {a.Prix})" : "")}"
            : $"◌ {prix} po · il manque {prix - solde} po";
        _detail.Texte = $"{Boutique.Signe(a.Slot)} {Boutique.NomSlot(Boutique.RayonDe(a.Slot))} · {Boutique.NomRarete(a.Rarete)}"
            + (a.Recompense ? "" : $" · rangée niveau {a.NiveauMin}") + $"\n{etat}" + Precisions(a, inventaire)
            + (consommable ? $"\nEn réserve : {_pilou.Reserve(a.Id)}" : "");
        bool essayable = Boutique.Slots.Contains(a.Slot) || a.Slot == Boutique.Accessoire;
        _essayer.Visibility = essayable ? Visibility.Visible : Visibility.Collapsed;
        _essayer.Libelle = _essai ? "Enlever l'essai" : "Essayer";
        _acheter.Visibility = possede || a.Recompense ? Visibility.Collapsed : Visibility.Visible;
        _acheter.Libelle = dispo ? $"Acheter · {prix} po" : a.Passage ? "✧ pas en vitrine" : "⌛ hors saison";
        _acheter.IsEnabled = Boutique.Ouvert(a, niveau) && solde >= prix && dispo;
        _porter.Visibility = possede && !bonus ? Visibility.Visible : Visibility.Collapsed;
        _porter.Libelle = porteIci ? "Retirer" : "Porter";
    }

    // « ⌛ hors saison · revient le 1er déc. (hiver) » ; « ✧ de passage seulement · prochain passage le 14 déc. ».
    private static string Indispo(Article a)
    {
        if (a.Saison != "" && !Boutique.EnSaison(a.Saison, Jour))
            return $"⌛ hors saison · revient {(Boutique.Retour(a.Saison, Jour) is { } r ? "le " + Date(r) : "")} ({Boutique.NomSaison(a.Saison)})";
        return $"✧ de passage seulement{(Boutique.ProchainPassage(a, Jour) is { } d ? " · prochain passage le " + Date(d) : "")}";
    }

    private static string Date(DateOnly d) => d.ToString("d MMM", new System.Globalization.CultureInfo("fr-FR"));

    // Saison, passage, ensemble : une ligne de plus sous l'état.
    private static string Precisions(Article a, List<string> inventaire)
    {
        var l = new List<string>();
        if (a.Saison != "" && Boutique.EnSaison(a.Saison, Jour)) l.Add($"⌛ {Boutique.NomSaison(a.Saison)} : encore {Boutique.JoursRestants(a.Saison, Jour)} j");
        if (Boutique.DePassage(a, Jour)) l.Add($"✧ de passage en vitrine : encore {Boutique.PassageRestant(a, Jour)} j");
        foreach (var e in Boutique.Ensembles.Where(e => e.Pieces.Contains(a.Id)))
            l.Add($"{e.Signe} ensemble {e.Nom} : {Boutique.Possedes(e, inventaire)}/{e.Pieces.Count}");
        return l.Count == 0 ? "" : "\n" + string.Join(" · ", l);
    }

    private static string CommentGagner(Article a)
    {
        if (Boutique.EnsembleDe(a.Ensemble) is { } e) return $"compléter l'ensemble {e.Nom}";
        var p = Boutique.PaliersCollection.FirstOrDefault(x => x.Id == a.Id);
        return p is null ? "?" : p.Nombre == 0 ? "toute la collection" : $"{p.Nombre} objets en collection";
    }

    private static UIElement BulleEssai(StyleBulle st)
    {
        var b = new Border
        {
            BorderBrush = Gel(st.Bord), BorderThickness = new Thickness(st.Epaisseur), CornerRadius = new CornerRadius(st.Rayon),
            Background = st.Fond is { } f ? Gel(f) : Gel("#f6f8fa"), Padding = new Thickness(8, 3, 8, 4),
            HorizontalAlignment = HorizontalAlignment.Center, VerticalAlignment = VerticalAlignment.Top, Margin = new Thickness(0, 6, 0, 0),
            Child = StylePixel.Texte("ça te va bien !", st.Sombre ? Gel("#e6ecf2") : Gel("#1c2128")),
        };
        return b;
    }

    // ---- Étagères (droite)

    private static DateOnly Jour => DateOnly.FromDateTime(DateTime.Now);

    private void Remplir()
    {
        var (solde, inventaire, equipe) = _pilou.EtatBourse();
        int niveau = _pilou.NiveauActuel;
        _bandeau.Mettre(niveau, _pilou.XpTotal, solde, _pilou.TitreAffiche(niveau), Bandeau.ProchaineRangee(niveau, _pilou.XpTotal));
        _pieces.Clear();
        Onglets(niveau, inventaire);
        _etageres.Children.Clear();
        Collection(inventaire);
        if (_rayon == Vitrine) RemplirVitrine(niveau, solde, inventaire, equipe);
        else if (_rayon == Boutique.RayonEnsembles) RemplirEnsembles(niveau, solde, inventaire, equipe);
        else
        {
            // Titres et cadres gagnés (ensembles, collection) : en tête de leur rayon.
            var gagnables = Boutique.Trophees.Where(t => t.Slot == _rayon).ToList();
            if (gagnables.Count > 0)
            {
                Entete(_rayon == Boutique.Titre ? "TITRES À GAGNER" : "CADRES DE COLLECTION",
                    $"{gagnables.Count(t => Boutique.PeutPorter(inventaire, t.Slot, t.Id))}/{gagnables.Count} gagnés · ensembles complets et paliers de collection",
                    AToi, null);
                Etagere(gagnables.Select(a => Tuile(a, niveau, solde, inventaire, equipe, null)));
            }
            foreach (var (palier, articles) in Boutique.Rangees(_rayon))
                Rangee(palier, articles, niveau, solde, inventaire, equipe);
        }
        MontrerApercu();
    }

    // « Collection 37/249 » et une jauge en cases ; le prochain palier et ce qu'il offre.
    private void Collection(List<string> inventaire)
    {
        int n = Boutique.Collection(inventaire), total = Boutique.TotalCollection;
        var p = Boutique.ProchainPalierCollection(n);
        _collection.Texte = $"❖ Collection {n}/{total}" + (p is null ? " · tout est à toi !" : $" · à {Boutique.Seuil(p)} : {p.Nom}");
        _jaugeCollection.Children.Clear();
        const int cases = 30;
        int pleines = total == 0 ? 0 : n * cases / total;
        for (int i = 0; i < cases; i++)
            _jaugeCollection.Children.Add(new Border
            {
                Width = 9, Height = 6, Margin = new Thickness(0, 0, 2, 0), Background = i < pleines ? AToi : Case,
                BorderBrush = Gel("#6a5acd"), BorderThickness = new Thickness(i < pleines ? 0 : 1),
            });
    }

    // Onglet Ensembles : chaque ensemble, sa progression (3/6), son bonus ; porter d'un coup ce qu'on en a.
    private void RemplirEnsembles(int niveau, int solde, List<string> inventaire, Dictionary<string, Port> equipe)
    {
        var porte = Boutique.Porte(equipe);
        foreach (var e in Boutique.Ensembles)
        {
            int a = Boutique.Possedes(e, inventaire);
            bool complet = a == e.Pieces.Count, actif = Boutique.PorteEnEntier(e, porte);
            var saison = e.Pieces.Select(Boutique.Trouver).FirstOrDefault(x => x is { Saison.Length: > 0 })?.Saison ?? "";
            string sous = $"{a}/{e.Pieces.Count} · " + (actif ? "★ bonus actif" : complet ? $"✓ complet : titre {e.Titre} gagné" : $"complet : titre {e.Titre} + effet")
                + (saison == "" ? "" : Boutique.EnSaison(saison, Jour) ? $" · ⌛ {Boutique.NomSaison(saison)} : encore {Boutique.JoursRestants(saison, Jour)} j"
                    : $" · ⌛ {Boutique.NomSaison(saison)}");
            Entete($"{e.Signe} {e.Nom.ToUpperInvariant()}", sous, actif ? Porte : complet ? AToi : Achetable, null);
            if (a > 0 && !actif)
            {
                var tout = Bouton($"Porter les {a} pièces");
                tout.Margin = new Thickness(0, 0, 0, 6);
                tout.HorizontalAlignment = HorizontalAlignment.Left;
                tout.Click += (_, _) =>
                {
                    foreach (var id in e.Pieces.Where(inventaire.Contains))
                        if (Boutique.Trouver(id) is { } x) _pilou.Equiper(x.Slot, id);
                    _message.Texte = $"★ Pilou porte l'ensemble {e.Nom} ({a}/{e.Pieces.Count})";
                    Remplir();
                };
                _etageres.Children.Add(tout);
            }
            Etagere(e.Pieces.Select(Boutique.Trouver).OfType<Article>().Select(x => Tuile(x, niveau, solde, inventaire, equipe, null)));
        }
    }

    private void Onglets(int niveau, List<string> inventaire)
    {
        _onglets.Children.Clear();
        _onglets.Children.Add(Onglet(Vitrine, "◆ Vitrine", false));
        foreach (var r in Boutique.Rayons)
        {
            // Pastille « ! » sur un rayon qui a une rangée toute neuve (depuis la dernière visite).
            bool neuf = Boutique.Catalogue.Any(a => Boutique.RayonDe(a.Slot) == r && a.NiveauMin > _vuAvant && a.NiveauMin <= niveau
                && !inventaire.Contains(a.Id));
            _onglets.Children.Add(Onglet(r, $"{Boutique.Signe(r)} {Boutique.NomSlot(r)}", neuf));
        }
    }

    // Onglet d'un rayon : cadre pixel sans ombre. Ouvert : fond et bord violets, texte clair (la forme : le cadre plein).
    // « ! » : du nouveau dans ce rayon (pastille orange, carrée).
    private UIElement Onglet(string rayon, string texte, bool neuf)
    {
        bool actif = _rayon == rayon;
        var contenu = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(5, 0, 5, 0) };
        var libelle = StylePixel.Etiquette(texte, actif ? Brushes.White : Bandeau.Argent);
        libelle.VerticalAlignment = VerticalAlignment.Center;
        contenu.Children.Add(libelle);
        if (neuf)
            contenu.Children.Add(new Border
            {
                Background = Porte, Margin = new Thickness(5, 0, 0, 0), Padding = new Thickness(3, 0, 2, 0), VerticalAlignment = VerticalAlignment.Center,
                Child = StylePixel.Texte("!", Bandeau.Encre, StylePixel.Petit, true),
            });
        var cadre = new CadrePixel
        {
            U = 2, AvecOmbre = false, Retrait = 0, Child = contenu, Margin = new Thickness(0, 0, 4, 4), Cursor = Cursors.Hand,
            Fond = actif ? Gel("#6a5acd") : Gel("#1f2540"), Couleur = actif ? Gel("#d2caff") : Gel("#3b4654"),
        };
        cadre.MouseEnter += (_, _) => { if (!actif) cadre.Couleur = Bandeau.Violet; cadre.InvalidateVisual(); };
        cadre.MouseLeave += (_, _) => { if (!actif) cadre.Couleur = Gel("#3b4654"); cadre.InvalidateVisual(); };
        cadre.MouseLeftButtonUp += (_, _) =>
        {
            _rayon = rayon;
            Remplir();
            _defile.ScrollToTop();
        };
        return cadre;
    }

    private void RemplirVitrine(int niveau, int solde, List<string> inventaire, Dictionary<string, Port> equipe)
    {
        var offres = Boutique.OffresDuJour(Jour);
        Entete("OFFRES DU JOUR", "la première à -25 % · elles changent chaque jour", Achetable, null);
        Etagere(offres.Select((a, i) => Tuile(a, niveau, solde, inventaire, equipe, i == 0 ? "-25 %" : Boutique.Pluie() && a.Id == "parapluie" ? "PLUIE" : null)));
        var passages = Boutique.Passages(Jour);
        if (passages.Count > 0)
        {
            Entete("DE PASSAGE", "rares : quelques jours par mois seulement, ne les laisse pas filer", Gel("#f5d76e"), null);
            Etagere(passages.Select(a => Tuile(a, niveau, solde, inventaire, equipe, $"✧ {Boutique.PassageRestant(a, Jour)} J")));
        }
        var saison = Boutique.Catalogue.Where(a => a.Saison != "" && Boutique.EnSaison(a.Saison, Jour) && !inventaire.Contains(a.Id))
            .OrderBy(a => Boutique.JoursRestants(a.Saison, Jour)).ThenBy(a => a.Prix).Take(8).ToList();
        if (saison.Count > 0)
        {
            Entete("DE SAISON", "ils repartent à la fin de leur saison (⌛ jours restants)", Achetable, null);
            Etagere(saison.Select(a => Tuile(a, niveau, solde, inventaire, equipe, null)));
        }
        var neufs = Boutique.Debloques(_vuAvant, niveau).Where(a => !inventaire.Contains(a.Id)).ToList();
        if (_vuAvant > 0 && neufs.Count > 0)
        {
            Entete("RANGÉES DÉBLOQUÉES !", $"{neufs.Count} nouveauté{(neufs.Count > 1 ? "s" : "")} depuis ta dernière visite", Porte, null, flash: true);
            Etagere(neufs.Take(12).Select(a => Tuile(a, niveau, solde, inventaire, equipe, "NEUF")));
        }
        int p = Boutique.ProchainPalier(niveau);
        if (p > 0)
        {
            var bientot = Boutique.Debloques(niveau, p).Where(a => a.NiveauMin == p).ToList();
            int reste = Math.Max(0, Profil.XpPourNiveau(p) - _pilou.XpTotal);
            Entete($"PROCHAINE RANGÉE : NIV {p}", $"encore {reste} xp · {string.Join(", ", Boutique.RayonsDuPalier(p).Select(Boutique.NomSlot))}", Ferme, p);
            Etagere(bientot.Take(12).Select(a => Tuile(a, niveau, solde, inventaire, equipe, null)));
        }
        // À ta portée : ce qui est ouvert, pas encore à toi, et que tes po peuvent payer.
        var portee = Boutique.Catalogue.Where(a => Boutique.Ouvert(a, niveau) && !inventaire.Contains(a.Id) && a.Slot != Boutique.Consommable
            && Boutique.Disponible(a, Jour) && Boutique.Prix(a, Jour) <= solde).OrderByDescending(a => a.Prix).Take(8).ToList();
        if (portee.Count > 0)
        {
            Entete("À TA PORTÉE", "ouvert et dans tes moyens", AToi, null);
            Etagere(portee.Select(a => Tuile(a, niveau, solde, inventaire, equipe, null)));
        }
    }

    private void Rangee(int palier, List<Article> articles, int niveau, int solde, List<string> inventaire, Dictionary<string, Port> equipe)
    {
        bool ouvert = niveau >= palier;
        bool neuf = ouvert && palier > _vuAvant && _vuAvant > 0;
        string sous = ouvert ? $"{articles.Count(a => inventaire.Contains(a.Id))}/{articles.Count} à toi"
            : $"encore {Math.Max(0, Profil.XpPourNiveau(palier) - _pilou.XpTotal)} xp";
        Entete(neuf ? $"RANGÉE NIV {palier} DÉBLOQUÉE !" : $"RANGÉE NIV {palier}", sous, neuf ? Porte : ouvert ? Achetable : Ferme,
            ouvert ? null : palier, flash: neuf);
        Etagere(articles.Select(a => Tuile(a, niveau, solde, inventaire, equipe, null)));
    }

    private void Entete(string titre, string sous, Brush couleur, int? ferme, bool flash = false)
    {
        var ligne = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 14, 0, 6) };
        if (ferme is not null && Pixels.Sprite("cadenas", 2) is { } cad)
        {
            cad.Margin = new Thickness(0, 0, 6, 0);
            cad.VerticalAlignment = VerticalAlignment.Center;
            ligne.Children.Add(cad);
        }
        var t = Titre(titre, couleur, 3);
        t.Margin = new Thickness(0, -2, 0, 0);
        t.VerticalAlignment = VerticalAlignment.Center;
        ligne.Children.Add(t);
        var s = Texte(11, Bandeau.Argent);
        s.Texte = sous;
        s.Margin = new Thickness(10, 0, 0, 0);
        s.VerticalAlignment = VerticalAlignment.Center;
        ligne.Children.Add(s);
        if (flash && Bandeau.Anime)
        {
            // « Rangée débloquée ! » : le titre clignote quelques fois, puis reste allumé.
            var anim = new DoubleAnimation(1, 0.25, TimeSpan.FromMilliseconds(260)) { AutoReverse = true, RepeatBehavior = new RepeatBehavior(4) };
            t.BeginAnimation(OpacityProperty, anim);
        }
        _etageres.Children.Add(ligne);
    }

    // Une étagère : les cases posées sur une planche de métal (reflet clair sur le dessus).
    private void Etagere(IEnumerable<UIElement> tuiles)
    {
        var rang = new WrapPanel();
        foreach (var t in tuiles) rang.Children.Add(t);
        if (rang.Children.Count == 0) return;
        var pile = new StackPanel();
        pile.Children.Add(rang);
        pile.Children.Add(new Border { Height = 3, Background = PlancheClaire });
        pile.Children.Add(new Border { Height = 7, Background = Planche });
        pile.Children.Add(new Border { Height = 3, Background = Bandeau.Encre, Margin = new Thickness(6, 0, 6, 0) });
        _etageres.Children.Add(pile);
    }

    private static bool EstPorte(Article a, IReadOnlyDictionary<string, Port> equipe) =>
        a.Slot != Boutique.Accessoire && equipe.TryGetValue(a.Slot, out var p) && p.Id == a.Id;

    // Icône d'un article : Pilou qui le porte (objets, couleurs, accessoires), le décor, la bulle, ou l'icône du bonus.
    private UIElement Vignette(Article a, bool ferme)
    {
        if (a.Slot == Boutique.Fond && Apercu.Sprite(a.Id, 0, ferme) is { } decor) return Apercu.Vue(decor, 1.3);
        if (a.Slot == Boutique.Bulle && Boutique.Style(a.Id) is { } st)
            return new Border
            {
                Width = 70, Height = 40, BorderBrush = ferme ? Ferme : Gel(st.Bord), BorderThickness = new Thickness(st.Epaisseur),
                CornerRadius = new CornerRadius(st.Rayon), Background = ferme ? Case : st.Fond is { } f ? Gel(f) : Gel("#f6f8fa"),
                Child = Centre(StylePixel.Texte("…", ferme ? Ferme : st.Sombre ? Gel("#e6ecf2") : Gel("#1c2128"), StylePixel.Corps, true)),
            };
        if (a.Slot == Boutique.Titre)
            return new Border
            {
                Width = 92, Height = 40, BorderBrush = ferme ? Ferme : Gel(Boutique.CouleurRarete(a.Rarete)), BorderThickness = new Thickness(2),
                Background = Gel("#151a2e"), Padding = new Thickness(3),
                Child = new TextePixel(StylePixel.Capitales(a.Nom), ferme ? Bandeau.Argent : Bandeau.ArgentClair)
                    { Taille = StylePixel.Petit, Titre = true, Centre = true, MaxLignes = 3, VerticalAlignment = VerticalAlignment.Center, PhysiqueParUnite = () => StylePixel.Physique(this) },
            };
        if (Boutique.RayonDe(a.Slot) == Boutique.Speciaux && a.Slot != Boutique.Accessoire)
            return Apercu.Sprite(Icone(a.Id), 0, ferme) is { } ic ? Apercu.Vue(ic, Math.Min(4, 48.0 / Math.Max(ic.PixelWidth, ic.PixelHeight)))
                : StylePixel.Texte(Boutique.Signe(a.Slot), Bandeau.Argent, StylePixel.Grand);
        var allure = new Allure { T = _t, Stade = 2, Expr = "repos" };
        if (a.Slot == Boutique.Couleur) allure.Couleur = Teinte(a.Id);
        else if (a.Slot == Boutique.Accessoire) allure.Accessoire = a.Id;
        else allure.Objets = new[] { a.Id };
        return Apercu.Vue(Apercu.Image(allure, ferme), 1.5);
    }

    private static FrameworkElement Centre(FrameworkElement e)
    {
        e.HorizontalAlignment = HorizontalAlignment.Center;
        e.VerticalAlignment = VerticalAlignment.Center;
        return e;
    }

    private static string Icone(string id) => id switch
    {
        "pomme" or "soupe" or "gateau" => "encas-" + id,
        _ => id,
    };

    private UIElement Tuile(Article a, int niveau, int solde, List<string> inventaire, Dictionary<string, Port> equipe, string? ruban)
    {
        bool consommable = a.Slot == Boutique.Consommable;
        bool possede = a.Recompense ? Boutique.PeutPorter(inventaire, a.Slot, a.Id) : !consommable && inventaire.Contains(a.Id);
        bool ouvert = a.Recompense ? possede : Boutique.Ouvert(a, niveau);
        bool porte = possede && (a.Slot == Boutique.Accessoire ? _pilou.AccessoireChoisi == a.Id : EstPorte(a, equipe));
        bool dispo = Boutique.Disponible(a, Jour);
        int prix = Boutique.Prix(a, Jour);
        bool choisi = _choisi?.Id == a.Id;
        // État → bord et signe (forme + couleur, jamais la couleur seule).
        var (bord, epaisseur, signe) = !ouvert ? (Ferme, 2.0, "")
            : porte ? (Porte, 3.0, "★")
            : possede ? (AToi, 2.0, "✓")
            : !dispo ? (Ferme, 2.0, a.Passage ? "✧" : "⌛")
            : solde >= prix ? (Achetable, 2.0, "◉")
            : (TropCher, 2.0, "◌");
        // Saison en cours : ruban « ⌛ 12 J » (sauf si un autre ruban est déjà là).
        if (ruban is null && !possede && a.Saison != "" && Boutique.EnSaison(a.Saison, Jour)) ruban = $"⌛ {Boutique.JoursRestants(a.Saison, Jour)} J";

        var pile = new StackPanel { Width = 138 };
        var haut = new Grid { Height = 88 };
        var vignette = Vignette(a, !ouvert);
        if (vignette is FrameworkElement fe)
        {
            fe.HorizontalAlignment = HorizontalAlignment.Center;
            fe.VerticalAlignment = VerticalAlignment.Center;
            fe.Opacity = ouvert ? 1 : 0.8;
        }
        haut.Children.Add(vignette);
        if (signe != "")
        {
            var etat = StylePixel.Texte(signe, bord, StylePixel.Petit, true);
            etat.Margin = new Thickness(0, 1, 4, 0);
            etat.HorizontalAlignment = HorizontalAlignment.Right;
            etat.VerticalAlignment = VerticalAlignment.Top;
            haut.Children.Add(etat);
        }
        if (ruban is not null)
            haut.Children.Add(new Border
            {
                Background = Porte, Padding = new Thickness(4, 0, 4, 1), HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Top,
                Child = StylePixel.Etiquette(ruban, Bandeau.Encre),
            });
        // Rareté : son signe, dans sa couleur, en bas à gauche ; le signe de l'ensemble à côté.
        var ens = Boutique.Ensembles.FirstOrDefault(e => e.Pieces.Contains(a.Id));
        var rarete = StylePixel.Texte(Boutique.SigneRarete(a.Rarete) + (ens is null ? "" : " " + ens.Signe), Gel(Boutique.CouleurRarete(a.Rarete)), StylePixel.Petit, true);
        rarete.Margin = new Thickness(5, 0, 0, 0);
        rarete.HorizontalAlignment = HorizontalAlignment.Left;
        rarete.VerticalAlignment = VerticalAlignment.Bottom;
        haut.Children.Add(rarete);
        pile.Children.Add(new Border { Height = 3, Background = Gel(Boutique.CouleurRarete(a.Rarete)), Margin = new Thickness(6, 0, 6, 2) });
        pile.Children.Add(haut);
        var nom = Texte(10.5, ouvert ? Bandeau.ArgentClair : Bandeau.Argent);
        nom.Texte = a.Nom;
        nom.Centre = true;
        nom.MaxLignes = 2;
        nom.MinHeight = 48; // deux lignes de « corps » : toutes les tuiles d'une étagère ont la même hauteur
        nom.Margin = new Thickness(4, 0, 4, 6);
        pile.Children.Add(nom);
        pile.Children.Add(Etiquette(a, ouvert, possede, porte, consommable, prix, solde, bord, dispo));

        var tuile = new Border
        {
            Child = pile, Background = choisi ? CaseSurvol : Case, BorderBrush = choisi ? Bandeau.ArgentClair : bord,
            BorderThickness = new Thickness(choisi ? 3 : epaisseur), Margin = new Thickness(0, 0, 8, 6), Padding = new Thickness(0, 2, 0, 4),
            Cursor = Cursors.Hand, SnapsToDevicePixels = true,
            ToolTip = $"{a.Nom} — {Boutique.NomRarete(a.Rarete)}" + (ens is null ? "" : $" · ensemble {ens.Nom}")
                + (a.Recompense ? "" : !ouvert ? $" · rangée du niveau {a.NiveauMin}" : !dispo ? " · " + Indispo(a) : ""),
        };
        tuile.MouseEnter += (_, _) => { if (!choisi) tuile.Background = CaseSurvol; };
        tuile.MouseLeave += (_, _) => { if (!choisi) tuile.Background = Case; };
        tuile.MouseLeftButtonUp += (_, _) =>
        {
            _choisi = a;
            _essai = true;
            _message.Texte = "";
            Remplir();
        };
        return tuile;
    }

    // Étiquette de prix : pièce qui tourne + prix ; ou cadenas « NIV 15 », « ✓ à toi », « ★ porté ».
    private UIElement Etiquette(Article a, bool ouvert, bool possede, bool porte, bool consommable, int prix, int solde, Brush bord, bool dispo)
    {
        var ligne = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Center };
        var fond = new Border
        {
            Background = Bandeau.Encre, BorderBrush = bord, BorderThickness = new Thickness(1), Padding = new Thickness(5, 1, 6, 1),
            HorizontalAlignment = HorizontalAlignment.Center, Child = ligne,
        };
        TextePixel T(string s, Brush c)
        {
            var t = StylePixel.Etiquette(s, c);
            t.VerticalAlignment = VerticalAlignment.Center;
            return t;
        }
        if (a.Recompense && !possede) ligne.Children.Add(T("▣ à gagner", Bandeau.Argent));
        else if (!ouvert)
        {
            if (Pixels.Sprite("cadenas", 1) is { } c)
            {
                c.Margin = new Thickness(0, 0, 4, 0);
                ligne.Children.Add(c);
            }
            ligne.Children.Add(T($"NIV {a.NiveauMin}", Bandeau.Argent));
        }
        else if (porte) ligne.Children.Add(T("★ porté", Porte));
        else if (possede) ligne.Children.Add(T(a.Recompense ? "✓ gagné" : "✓ à toi", AToi));
        else if (!dispo)
            ligne.Children.Add(T(a.Passage ? (Boutique.ProchainPassage(a, Jour) is { } d ? $"✧ {Date(d)}" : "✧ vitrine")
                : $"⌛ {Boutique.NomSaison(a.Saison)}", Bandeau.Argent));
        else
        {
            if (_imagesPiece.Count > 0)
            {
                var piece = new Pixels(_imagesPiece[0].Motif, _imagesPiece[0].Palette, null, 1) { Margin = new Thickness(0, 0, 3, 0), VerticalAlignment = VerticalAlignment.Center };
                _pieces.Add(piece);
                ligne.Children.Add(piece);
            }
            ligne.Children.Add(T(prix.ToString(), solde >= prix ? Neon : Bandeau.Argent));
            if (prix < a.Prix) ligne.Children.Add(T($" ({a.Prix})", Bandeau.Argent));
            if (solde < prix) ligne.Children.Add(T(" ◌", Bandeau.Argent));
            if (consommable && _pilou.Reserve(a.Id) > 0) ligne.Children.Add(T($" ×{_pilou.Reserve(a.Id)}", AToi));
        }
        return fond;
    }

    // ---- Actions

    private void Acheter()
    {
        if (_choisi is null) return;
        var a = _choisi;
        var refus = _pilou.Acheter(a.Id);
        if (refus is null) Sons.Jouer(Son.Achat);
        _message.Texte = refus is null ? $"✓ {a.Nom} est à toi !" : $"✕ {refus}";
        // Un objet portable acheté se porte tout de suite (on peut le retirer).
        if (refus is null && Boutique.Slots.Contains(a.Slot)) _pilou.Equiper(a.Slot, a.Id);
        Remplir();
    }

    private void Porter()
    {
        if (_choisi is null) return;
        var a = _choisi;
        var (_, _, equipe) = _pilou.EtatBourse();
        bool porte = a.Slot == Boutique.Accessoire ? _pilou.AccessoireChoisi == a.Id : EstPorte(a, equipe);
        _pilou.Equiper(a.Slot, porte ? "" : a.Id);
        _message.Texte = porte ? $"{a.Nom} rangé." : $"★ Pilou porte : {a.Nom}";
        Remplir();
    }

    // Animation légère : pièces qui tournent, enseigne qui grésille, objets animés de l'aperçu.
    private void Animer()
    {
        _t += 140;
        if (_imagesPiece.Count > 0)
        {
            var (m, p) = _imagesPiece[(int)(_t / 140) % _imagesPiece.Count];
            foreach (var piece in _pieces)
            {
                piece.Palette = p;
                piece.Changer(m);
            }
        }
        int k = (int)(_t / 140);
        _enseigneTexte.Couleur = k % 37 == 0 || k % 37 == 2 ? NeonClair : Neon;
        if (_pilouVu is not null && Apercu.ImageSiChange(AllureApercu(_choisi), ref _pilouPixels, fin: true) is { } image) _pilouVu.Source = image;
    }
}

// « NIVEAU 15 ! Rangées débloquées » : petite fenêtre près de Pilou au passage d'un palier, avec les objets
// qui viennent d'entrer en rayon et un bouton « Voir en boutique ». Se ferme seule au bout de 12 s.
internal sealed class FenetreRangees : Window
{
    public FenetreRangees(int avant, int apres, Action<string> voir)
    {
        WindowStyle = WindowStyle.None;
        AllowsTransparency = true;
        Background = Brushes.Transparent;
        ShowInTaskbar = false;
        ShowActivated = false;
        Topmost = true;
        ResizeMode = ResizeMode.NoResize;
        SizeToContent = SizeToContent.WidthAndHeight;

        var neufs = Boutique.Debloques(avant, apres);
        var rayons = Boutique.Rayons.Where(r => neufs.Any(a => Boutique.RayonDe(a.Slot) == r)).ToList();
        var pile = new StackPanel();
        var niveau = StylePixel.Enseigne($"NIVEAU {apres} !", Bandeau.OrangePo, Bandeau.Bord, StylePixel.Grand);
        niveau.Margin = new Thickness(0, 0, 0, 4);
        pile.Children.Add(niveau);
        var sous = StylePixel.Enseigne("RANGÉES DÉBLOQUÉES", Bandeau.Violet, Bandeau.Encre, StylePixel.Petit);
        sous.Margin = new Thickness(0, 0, 0, 6);
        pile.Children.Add(sous);
        // Signe et nom insécables : une ligne ne coupe jamais « ▲ Tête » en deux.
        var noms = StylePixel.Texte(string.Join(" · ", rayons.Select(r => $"{Boutique.Signe(r)}\u00a0{Boutique.NomSlot(r)}")), Bandeau.ArgentClair, StylePixel.Corps);
        noms.MaxWidth = 420;
        noms.HorizontalAlignment = HorizontalAlignment.Left;
        pile.Children.Add(noms);
        var vitrine = new WrapPanel { Margin = new Thickness(0, 8, 0, 8), MaxWidth = 420 };
        foreach (var a in neufs.Where(a => Boutique.SurPilou(a.Slot) && Boutique.Slots.Contains(a.Slot)).Take(5))
            vitrine.Children.Add(new Border
            {
                Background = Bandeau.Nuit2, BorderBrush = Bandeau.BleuXp, BorderThickness = new Thickness(2), Margin = new Thickness(0, 0, 4, 0),
                Child = Apercu.Vue(Apercu.Image(new Allure { Objets = new[] { a.Id }, Expr = "fete" }), 1.1), ToolTip = a.Nom,
            });
        if (vitrine.Children.Count > 0) pile.Children.Add(vitrine);
        var boutons = new StackPanel { Orientation = Orientation.Horizontal };
        var aller = new BoutonPixel("Voir en boutique", true, StylePixel.Corps);
        aller.Click += (_, _) =>
        {
            Close();
            voir(rayons.FirstOrDefault() ?? "vitrine");
        };
        var plusTard = new BoutonPixel("Plus tard", false, StylePixel.Corps) { Margin = new Thickness(6, 0, 0, 0) };
        plusTard.Click += (_, _) => Close();
        boutons.Children.Add(aller);
        boutons.Children.Add(plusTard);
        pile.Children.Add(boutons);
        pile.Margin = new Thickness(10, 8, 10, 8);
        Content = new CadrePixel { U = 3, Child = pile };
        var fin = new DispatcherTimer { Interval = TimeSpan.FromSeconds(12) };
        fin.Tick += (_, _) =>
        {
            fin.Stop();
            if (IsVisible) Close();
        };
        Loaded += (_, _) =>
        {
            fin.Start();
            // Entrée en fondu (immobile si les animations de Windows sont coupées).
            if (Bandeau.Anime) BeginAnimation(OpacityProperty, new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(280)));
        };
    }
}
