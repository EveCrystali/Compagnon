namespace PilouBureau;

// Vie du personnage, côté fenêtre (Vie.cs pour les règles) : sauts en arc et à ressort, antenne en retard, réception
// d'une chute, lumière du moment, poussière en marchant. Pilou ne bouge pas plus souvent qu'avant : seuls les
// mouvements déjà là changent de forme. Le réglage ✧ (animations complètes / réduites / aucune) décide de tout ;
// « aucune » garde exactement les mouvements d'avant.
public sealed partial class FenetrePilou
{
    // --essai=vie[:completes|reduites|aucune][:heure] : saut, marche, chute en boucle, au niveau et à l'heure voulus.
    private bool _essaiVie;
    private string? _essaiNiveauVie;
    private int? _essaiHeure;
    private double _essaiVieDebut = -1;
    private int _essaiVieEtape = -1;

    internal string NiveauVie => _essaiNiveauVie ?? AnimationsCampagne.Niveau(_reglages.AnimationsCampagnes, Bandeau.Anime);

    internal readonly record struct Mouvement(double Saut, double Etire, double Antenne, double Chute, double Atterri);

    // Le saut du moment (anciens pixels) et ses ressorts. Mêmes déclencheurs qu'avant : fête, caresse, petit saut.
    private Mouvement Bondir(Expr expr, double t, double depuis, string niveau)
    {
        if (niveau == AnimationsCampagne.Aucune)
        {
            double s = 0;
            if (expr == Expr.Fete) s = Math.Abs(Math.Sin(Math.PI * depuis / 450)) * 3;
            else if (expr == Expr.Caresse && t - _tCaresse < 400) s = Math.Sin(Math.PI * (t - _tCaresse) / 400) * 1.5;
            else if (t - _tSaut < 600) s = Math.Sin(Math.PI * (t - _tSaut) / 600) * 2;
            return new Mouvement(s, 0, 0, Math.Max(0, 1 - (t - _atterri) / 220), -1);
        }
        (int Saut, int Etire, int Antenne) b = (0, 0, 0);
        double atterri = -1;
        if (expr == Expr.Fete) b = Vie.Sautille((long)depuis, 450, 3000, niveau);
        else if (expr == Expr.Caresse && t - _tCaresse < Vie.DureeBond(400, niveau)) b = Vie.Bond((long)(t - _tCaresse), 400, 1500, niveau);
        else if (t - _tSaut < Vie.DureeBond(520, niveau))
        {
            b = Vie.Bond((long)(t - _tSaut), 520, 2000, niveau);
            if (niveau == AnimationsCampagne.Completes) atterri = t - _tSaut - Vie.Prep - 520;
        }
        // Lâché, il retombe : ressort amorti (complètes) ; réduites : l'écrasement d'avant.
        var (re, ra) = Vie.Recoit((long)(t - _atterri), niveau);
        double chute = niveau == AnimationsCampagne.Completes ? 0 : Math.Max(0, 1 - (t - _atterri) / 220);
        if (niveau == AnimationsCampagne.Completes && t - _atterri < 3 * Vie.BouffeeImage) atterri = t - _atterri;
        return new Mouvement(b.Saut / 1000.0, Math.Clamp((b.Etire + re) / 1000.0, -1, 1), Math.Clamp((b.Antenne + ra) / 1000.0, -1, 1),
            chute, atterri >= 0 ? atterri : -1);
    }

    // Lumière du moment sur Pilou, d'après l'heure et le temps qu'il fait (s'il est connu).
    private string LumiereVie(string niveau)
    {
        string etat = _essaiMeteo != "" ? _essaiMeteo
            : Meteo.Courante is { } m && _registre?.Trouver("meteo") is { } c && _registre.Actif(c) ? m.Etat : "";
        return Vie.Lumiere(_essaiHeure ?? DateTime.Now.Hour, etat, niveau);
    }

    // Après les autres habillages : si une visite, une expédition ou un geste a repris la hauteur du saut, ses
    // ressorts ne s'appliquent pas (pas d'écrasement sans saut).
    private void HabillerVie(Pose p, Mouvement mv, string niveau)
    {
        bool sien = p.Saut == mv.Saut && p.Assis < 0.5;
        p.Etire = sien ? mv.Etire : 0;
        p.Antenne = sien ? mv.Antenne : 0;
        p.Atterri = sien ? mv.Atterri : -1;
        p.Vie = niveau == AnimationsCampagne.Completes;
        p.Lumiere = LumiereVie(niveau);
    }

    private void EssaiVie(string nom)
    {
        _essaiVie = true;
        foreach (var part in nom.Split(':').Skip(1))
        {
            if (Array.IndexOf(AnimationsCampagne.Niveaux, part) >= 0) _essaiNiveauVie = part;
            else if (int.TryParse(part, out var h)) _essaiHeure = h;
        }
    }

    // Boucle de 9 s : petit saut, marche aller, marche retour, chute d'un peu haut ; rien d'autre ne démarre.
    private void AnimerEssaiVie(double t)
    {
        if (!_essaiVie) return;
        if (_essaiVieDebut < 0) _essaiVieDebut = t;
        _pauseJusque = Math.Max(_pauseJusque, t + 1000);
        int etape = (int)((t - _essaiVieDebut) / 1500) % 6;
        if (etape == _essaiVieEtape) return;
        _essaiVieEtape = etape;
        var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);
        switch (etape)
        {
            case 0:
                _tSaut = t;
                break;
            case 1:
                _geste = Geste.Marche;
                _cible = Math.Clamp(_x + 50 * K, min, max);
                break;
            case 2:
                _geste = Geste.Marche;
                _cible = Math.Clamp(_x - 50 * K, min, max);
                break;
            case 4:
                if (_auSol && _geste == Geste.Rien)
                {
                    _yPieds -= 26 * K;
                    _vy = 0;
                    _auSol = false;
                }
                break;
        }
    }
}
