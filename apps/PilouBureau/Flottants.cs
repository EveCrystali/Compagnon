namespace PilouBureau;

// Les gains qui montent (« +30 po », « +10 xp », « SUCCES ! ») ne passent jamais sur la bulle ni les uns sur les
// autres : un gain qui touche la bulle ou un gain déjà placé est remonté juste au-dessus et continue d'y monter. S'il
// n'y a pas la place (bulle très haute), il attend, caché, que la bulle se range. Sans WPF : testé dans FlottantsTests.cs.
public static class Flottants
{
    // Distance parcourue par un gain pendant sa vie (en unités de la fenêtre) et son temps de vie (ms).
    public const double Montee = 38;
    public const double Vie = 1400;

    // Écart gardé autour de la bulle, et entre deux gains.
    public const double MargeBulle = 3;
    public const double MargeGain = 1;

    // Fixe : la bulle, qui ne monte pas ; un gain qui la croiserait plus haut dans sa montée part tout de suite au-dessus
    // (pas de saut à travers elle). Les gains montent tous à la même vitesse : seule leur place du moment compte.
    public readonly record struct Boite(double Gauche, double Haut, double Droite, double Bas, double Marge = MargeGain, bool Fixe = false);

    public static Boite DeBulle(double gauche, double haut, double droite, double bas) => new(gauche, haut, droite, bas, MargeBulle, true);

    public static bool Touche(double x, double y, double l, double h, Boite o, double reste = 0)
    {
        double haut = o.Fixe ? y - reste : y;
        return x < o.Droite + o.Marge && x + l > o.Gauche - o.Marge && haut < o.Bas + o.Marge && y + h > o.Haut - o.Marge;
    }

    // Haut où dessiner un gain de largeur l et de hauteur h voulu en (x, y), à qui il reste « reste » à monter, hors de
    // tous les obstacles (la bulle, les gains déjà placés). Null : repoussé au-dessus du plafond (le haut de la fenêtre).
    public static double? Placer(double x, double y, double l, double h, IReadOnlyList<Boite> obstacles, double reste = 0, double plafond = 0)
    {
        bool pousse = false;
        for (int tour = 0; tour <= obstacles.Count; tour++)
        {
            double? dessus = null;
            foreach (var o in obstacles)
                if (Touche(x, y, l, h, o, reste))
                    dessus = Math.Min(dessus ?? double.MaxValue, o.Haut - o.Marge - h);
            if (dessus is not { } d) return pousse && y < plafond ? null : y;
            y = d;
            pousse = true;
        }
        return null;
    }
}
