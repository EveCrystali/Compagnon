namespace PilouBureau;

// Un point du plan (unités WPF de la fenêtre avant la mise à l'échelle K, ou de l'écran selon l'usage).
public readonly record struct Pt(double X, double Y);

// Ce qui est dessiné autour de Pilou pendant la pêche, en unités de la fenêtre (avant K) : tout est calculé
// à partir du sens (côté de la fenêtre où il y a de la place : +1 à droite de Pilou, −1 à gauche) et de la
// main de Pilou du côté de l'eau, pour que la canne parte de sa main et le fil du bout de la canne.
public sealed record GeoPeche(
    int Sens,
    Clics.Zone Eau,          // les pixels de l'eau (coin haut-gauche du premier pixel, largeur, hauteur)
    Pt Main,                 // centre de la main de Pilou qui tient la canne
    double CanneX, double CanneY, bool CanneMiroir, // coin de l'élément Pixels de la canne, dessin retourné ?
    Pt Bout,                 // bout de la canne : départ du fil
    Pt Attache);             // haut du bouchon posé sur l'eau : arrivée du fil

// Dessin fin (réglage « Dessin fin », activé par défaut) : Pilou et ce qui l'accompagne sont rendus sur la grille
// fine 96 × 112 (RenduPilou, échelle 2), et la fenêtre est mise à une échelle telle qu'un pixel fin tombe sur un
// nombre entier de pixels physiques (net à 100, 125, 150, 175, 200 %…). Désactivé : le rendu d'origine, tel quel.
public static class Finesse
{
    public static bool Active { get; set; } = true;
    public static int Echelle => Active ? 2 : 1;
    // Mise à l'échelle Windows de l'écran de Pilou (1 = 100 %, 1,25 = 125 %…) et pixels physiques par unité de la
    // fenêtre de Pilou (échelle de la fenêtre × mise à l'échelle) : tenus à jour par FenetrePilou.
    public static double Dpi { get; set; } = 1;
    public static double PhysiqueParUnite { get; set; } = 1;

    // Taille d'un pixel (unités de la fenêtre de Pilou) d'un dessin posé près de lui, ramenée à un nombre pair de
    // pixels physiques : son dessin fin (deux fois plus de pixels) tombe alors sur des pixels physiques entiers.
    public static double Net(double taille) => Active ? Placement.TailleNette(taille, PhysiqueParUnite) : taille;

    // Zoom d'une image de Pilou rendue en fin dans une autre fenêtre (boutique) : pixels fins entiers.
    public static double ZoomNet(double zoom) => Active ? Placement.TailleNette(zoom, Dpi) : zoom;
}

// Géométrie de la fenêtre de Pilou, sans WPF (testable) : repères dans la fenêtre, côté de la place, bornage
// à l'écran courant (qui peut être à gauche de l'écran principal, en X négatif), éléments posés « à côté »
// de Pilou en miroir exact d'un côté à l'autre. Les fenêtres l'appliquent ; les tests le balaient.
public static class Placement
{
    // Fenêtre de Pilou (FenetrePilou) : largeur et hauteur de la rangée de la bulle, avant la taille K.
    public const double LargeurBase = 380;
    public const double HauteurBulle = 150;

    // Scène (Scene.cs) : pixel de l'ancienne grille, « ancien » pixel, marges, grille 26 × 30.
    public const double P = 4;
    public const double PA = 5;
    public const int W = 26;
    public const int H = 30;
    public const double MargeX = 28;
    public const double MargeY = 26;
    public const double PX = W * P / RenduPilou.W;
    public const double LargeurScene = MargeX * 2 + W * P;
    public const double HauteurScene = MargeY + H * P + 6;
    public const double SolScene = MargeY + 28.75 * P;

    // Écart du bord de l'écran où Pilou disparaît quand il part (visite, expédition), en unités × K.
    public const double HorsEcran = 90;

    // ---- Dessin fin : un pixel de la grille fine (96 × 112) = un nombre entier de pixels physiques

    // Pixels physiques par pixel fin pour la Taille choisie (0,75 ; 1 ; 1,3) et la mise à l'échelle de l'écran
    // (1 = 100 %) : l'entier le plus proche de la taille voulue (PX × taille × dpi / 2), au moins 1. Les trois
    // tailles du menu restent ordonnées : « Grand » fait toujours un cran de plus que « Normal », « Petit » un cran
    // de moins quand il en reste un (à 100 % : 1, 1 et 2 pixels physiques par pixel fin).
    public static int PixelsParPixelFin(double taille, double dpi)
    {
        if (!(dpi > 0)) dpi = 1;
        int Proche(double t) => Math.Max(1, (int)Math.Round(PX * t * dpi / 2, MidpointRounding.AwayFromZero));
        int normal = Proche(1), n = Proche(taille);
        if (taille > 1.15) n = Math.Max(n, normal + 1);
        else if (taille < 0.9) n = Math.Max(1, Math.Min(n, normal - 1));
        return n;
    }

    // Échelle à donner à la fenêtre (à la place de la Taille) : en dessin fin, celle qui met un pixel fin sur un
    // nombre entier de pixels physiques ; sinon la Taille telle quelle.
    public static double Echelle(double taille, double dpi, bool fin)
    {
        if (!fin) return taille;
        if (!(dpi > 0)) dpi = 1;
        return 2.0 * PixelsParPixelFin(taille, dpi) / (PX * dpi);
    }

    // Largeur de la grille de Pilou (48 pixels de grille) en pixels physiques : 96 × n en dessin fin.
    public static double LargeurPhysique(double taille, double dpi, bool fin) =>
        fin ? 2.0 * RenduPilou.W * PixelsParPixelFin(taille, dpi) : W * P * taille * (dpi > 0 ? dpi : 1);

    // Taille d'un pixel de dessin (en unités, « physique » pixels physiques par unité) ramenée à un nombre pair de
    // pixels physiques (au moins 2) : chaque moitié — un pixel fin — est alors un nombre entier de pixels physiques.
    public static double TailleNette(double taille, double physique)
    {
        if (!(physique > 0)) return taille;
        return 2.0 * Math.Max(1, (int)Math.Round(taille * physique / 2, MidpointRounding.AwayFromZero)) / physique;
    }

    // Une coordonnée d'écran (unités WPF) ramenée sur un pixel physique entier.
    public static double Aligner(double v, double dpi) => dpi > 0 ? Math.Round(v * dpi, MidpointRounding.AwayFromZero) / dpi : v;

    // ---- Repères dans la fenêtre

    // Pilou dans la moitié gauche de son écran : il est à gauche de sa fenêtre, la place est à sa droite.
    public static bool AGauche(double x, double zoneGauche, double zoneDroite) => x < (zoneGauche + zoneDroite) / 2;

    // Côté de la fenêtre où il y a de la place (où vont l'eau, la marmite, la main du tape m'en cinq…).
    public static int Sens(bool aGauche) => aGauche ? 1 : -1;

    public static double SceneX(bool aGauche) => aGauche ? 0 : LargeurBase - LargeurScene;
    public static double TeteX(bool aGauche) => SceneX(aGauche) + LargeurScene / 2;
    public static double SolY => HauteurBulle + SolScene;
    public static double TeteY => SolY - 15 * PA;

    // Un pixel (gx, gy) de la grille fine 48 × 56 de Pilou, en unités de la fenêtre (son centre).
    public static Pt Grille(bool aGauche, double gx, double gy) =>
        new(SceneX(aGauche) + MargeX + (gx + 0.5) * PX, HauteurBulle + MargeY + (gy + 0.5) * PX);

    // La main de Pilou du côté sens (+1 : sa main de droite à l'écran ; −1 : celle de gauche).
    public static Pt MainDe(bool aGauche, Geometrie geo, int sens)
    {
        var (mx, my) = RenduPilou.AncreMain(geo, sens);
        return Grille(aGauche, mx, my);
    }

    // Coin gauche d'un élément de largeur l posé à « ecart » de l'axe de Pilou, du côté sens : miroir exact.
    public static double ACote(bool aGauche, int sens, double ecart, double largeur) =>
        sens > 0 ? TeteX(aGauche) + ecart : TeteX(aGauche) - ecart - largeur;

    // ---- Fenêtre et écran (unités WPF de l'écran)

    // Distance du bord gauche de la fenêtre aux pieds de Pilou.
    public static double PiedsDansFenetre(bool aGauche, double k) => TeteX(aGauche) * k;

    public static double GaucheFenetre(double x, bool aGauche, double k) => Math.Round(x - PiedsDansFenetre(aGauche, k));

    public static double HautFenetre(double pieds, double k) => Math.Round(pieds - SolY * k);

    // Bornes des pieds de Pilou sur son écran (la scène entière reste dedans).
    public static (double Min, double Max) BornesPieds(double zoneGauche, double zoneDroite, double k)
    {
        double demi = LargeurScene / 2 * k;
        double min = zoneGauche + demi;
        return (min, Math.Max(min, zoneDroite - demi));
    }

    // Partie de la fenêtre (en unités avant K, dans [0, LargeurBase]) qui tombe sur l'écran courant : au-delà,
    // ce serait un autre écran (ou rien) ; la fenêtre y est découpée.
    public static (double X0, double X1) Visible(double gaucheFenetre, double k, double zoneGauche, double zoneDroite)
    {
        double x0 = Math.Clamp((zoneGauche - gaucheFenetre) / k, 0, LargeurBase);
        double x1 = Math.Clamp((zoneDroite - gaucheFenetre) / k, 0, LargeurBase);
        return (x0, Math.Max(x0, x1));
    }

    // Largeur maximale de la bulle (alignée du côté de Pilou) pour qu'elle reste sur l'écran courant.
    public static double LargeurBulle(bool aGauche, (double X0, double X1) visible)
    {
        double place = aGauche ? visible.X1 : LargeurBase - visible.X0;
        return Math.Max(60, Math.Min(LargeurBase - 8, place - 4));
    }

    // Un segment [x, x + largeur] ramené dans [min, max] (collé à min s'il est plus large).
    public static double Borner(double x, double largeur, double min, double max) =>
        Math.Max(min, Math.Min(x, max - largeur));

    // Sortie par le bord le plus proche (visite, expédition) : −1 à gauche, +1 à droite.
    public static int SensSortie(double x, double zoneGauche, double zoneDroite) => x - zoneGauche < zoneDroite - x ? -1 : 1;

    // Abscisse (pieds) où Pilou n'est plus sur son écran.
    public static double Sortie(int sens, double zoneGauche, double zoneDroite, double k) =>
        sens < 0 ? zoneGauche - HorsEcran * k : zoneDroite + HorsEcran * k;

    // Petite fenêtre posée près de Pilou (rangées débloquées…), gardée sur l'écran courant.
    public static (double X, double Y) PresDe(double gaucheFenetre, double hautFenetre, double k, bool aGauche, double largeur, double hauteur,
        double zoneGauche, double zoneHaut, double zoneDroite, double zoneBas)
    {
        double x = aGauche ? gaucheFenetre + LargeurBase * k - 40 : gaucheFenetre - largeur + 40;
        double y = hautFenetre + HauteurBulle * k - 60;
        return (Borner(x, largeur, zoneGauche, zoneDroite), Borner(y, hauteur, zoneHaut, zoneBas));
    }

    // ---- Défense du bureau : bande en bas de l'écran de Pilou (zone en unités WPF, échelle : pixels physiques par
    // unité), un pixel de jeu = k × k pixels physiques ; centrée sur cet écran, même à gauche du principal.
    public static (int K, int W, int H, double GauchePhys, double HautPhys) Bande(double zoneGauche, double zoneHaut, double zoneLargeur,
        double zoneHauteur, double echelle, double part, double partHauteur)
    {
        int hauteurPhys = (int)Math.Round(zoneHauteur * echelle * partHauteur);
        int largeurPhys = (int)Math.Round(zoneLargeur * echelle * Math.Clamp(part, 0.3, 1));
        int k = Math.Max(1, hauteurPhys / 200);
        int w = Math.Max(320, largeurPhys / k), h = Math.Max(150, hauteurPhys / k);
        double gauche = Math.Round(zoneGauche * echelle + (zoneLargeur * echelle - w * k) / 2);
        double haut = Math.Round((zoneHaut + zoneHauteur) * echelle) - h * k;
        return (k, w, h, gauche, haut);
    }

    // ---- Pêche

    public const double LargeurEau = 28 * 4;
    public const double EcartEau = 70;       // de l'axe de Pilou au bord de l'eau
    public const double EcartBouchon = 121;  // de l'axe de Pilou au bouchon posé (au-dessus de l'eau)
    public const double TailleCanne = 1.2 * PX;

    // Repères d'un dessin de canne non retourné (colonnes, rangées) : le bout (pixel le plus haut, le plus à
    // droite) et la prise (un dixième de la canne au-dessus du talon, là où la main la tient).
    public static (Pt Prise, Pt Bout) ReperesCanne(int[,] motif)
    {
        int h = motif.GetLength(0), w = motif.GetLength(1);
        int haut = -1, bas = -1;
        for (int y = 0; y < h && haut < 0; y++)
            for (int x = 0; x < w; x++)
                if (motif[y, x] != 0) { haut = y; break; }
        for (int y = h - 1; y >= 0 && bas < 0; y--)
            for (int x = 0; x < w; x++)
                if (motif[y, x] != 0) { bas = y; break; }
        if (haut < 0) return (new Pt(0, h - 1), new Pt(w - 1, 0));
        int boutX = 0, talonX = w - 1;
        for (int x = 0; x < w; x++)
        {
            if (motif[haut, x] != 0) boutX = x;
            if (motif[bas, w - 1 - x] != 0) talonX = w - 1 - x;
        }
        var bout = new Pt(boutX, haut);
        var talon = new Pt(talonX, bas);
        var prise = new Pt(Math.Round(talon.X + (bout.X - talon.X) * 0.12), Math.Round(talon.Y + (bout.Y - talon.Y) * 0.12));
        return (prise, bout);
    }

    // Tout le décor de la pêche. motifW : largeur du dessin de la canne (colonnes) ; reperes : ReperesCanne du
    // dessin non retourné ; taille : taille d'un pixel de la canne. La canne est retournée quand l'eau est à gauche.
    public static GeoPeche Peche(bool aGauche, Geometrie geo, int motifW, (Pt Prise, Pt Bout) reperes, double taille = TailleCanne)
    {
        int sens = Sens(aGauche);
        double tete = TeteX(aGauche);
        var eau = new Clics.Zone(sens > 0 ? tete + EcartEau : tete - EcartEau - LargeurEau, SolY - 12, LargeurEau, 12);
        var main = MainDe(aGauche, geo, sens);
        bool miroir = sens < 0;
        double Col(double c) => miroir ? motifW - 1 - c : c;
        // Pixels dessine la cellule (c, r) en ((c + 1) × t, (r + 1) × t) : centre en (c + 1,5) × t.
        double canneX = main.X - (Col(reperes.Prise.X) + 1.5) * taille;
        double canneY = main.Y - (reperes.Prise.Y + 1.5) * taille;
        var bout = new Pt(canneX + (Col(reperes.Bout.X) + 1.5) * taille, canneY + (reperes.Bout.Y + 1.5) * taille);
        var attache = new Pt(tete + sens * EcartBouchon, SolY - 28);
        return new GeoPeche(sens, eau, main, canneX, canneY, miroir, bout, attache);
    }

    // Bouchon pendant le lancer (0..1) : du bout de la canne à l'eau, en arc.
    public static Pt Lancer(GeoPeche g, double lance)
    {
        lance = Math.Clamp(lance, 0, 1);
        return new Pt(g.Bout.X + (g.Attache.X - g.Bout.X) * lance,
            g.Bout.Y + (g.Attache.Y - g.Bout.Y) * lance - Math.Sin(Math.PI * lance) * 30);
    }

    // ---- Cuisine : la marmite sur son feu, du côté de la place.

    public const double EcartMarmite = 60;

    // Coins de la marmite et du feu (éléments Pixels de largeurs données) ; basMarmite : bas des pixels dessinés de
    // la marmite depuis le haut de l'élément ; hautFeu/basFeu : idem pour le feu. Le feu touche le sol, la marmite
    // pose dessus et le recouvre d'un tiers.
    public static (Pt Marmite, Pt Feu) Cuisine(bool aGauche, double largeurMarmite, double basMarmite, double largeurFeu,
        double hautFeu, double basFeu)
    {
        int sens = Sens(aGauche);
        double x = ACote(aGauche, sens, EcartMarmite, largeurMarmite);
        var feu = new Pt(x + (largeurMarmite - largeurFeu) / 2, SolY - basFeu);
        double flamme = basFeu - hautFeu;
        var marmite = new Pt(x, SolY - flamme * 0.66 - basMarmite);
        return (marmite, feu);
    }

    // Lignes dessinées (premier et dernier rang non vides) d'un motif.
    public static (int Haut, int Bas) Rangs(int[,] motif)
    {
        int h = motif.GetLength(0), w = motif.GetLength(1), haut = -1, bas = -1;
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            if (motif[y, x] == 0) continue;
            if (haut < 0) haut = y;
            bas = y;
            break;
        }
        return haut < 0 ? (0, h - 1) : (haut, bas);
    }
}
