namespace PilouBureau;

// Saynètes de repos sur le PC (Saynetes.cs ; docs/SPRITES.md, « Saynètes de repos ») : au calme, une petite scène de
// 3 à 8 s tirée au sort de temps en temps, à la place d'une occupation ordinaire. Retenue : jamais pendant la saisie
// (Vivacite.EnSaisie), espacées d'au moins EspaceSaynete (le double quand tu travailles), coupées par le réglage ✧
// (niveau « aucune »), interrompues dès que quelque chose se passe (caresse, IA qui attend, jeu, campagne…). Rien à
// gagner : aucune xp, aucune pièce.
public sealed partial class FenetrePilou
{
    private const double EspaceSaynete = 40_000;
    private Saynetes.Saynete? _saynete;
    private double _sayneteDebut, _sayneteFin = -1e12, _sayneteProchaine = 20_000;
    private int _sayneteSens = 1;
    private string _sayneteDerniere = "";
    // Essai (--essai=saynete[:<id>][:<niveau>]) : les saynètes l'une après l'autre (ou une seule, en boucle).
    private string? _essaiSaynete;
    private string? _essaiNiveauSaynete;
    private int _essaiSayneteRang;

    private bool EssaiEveille => _essaiVie || _essaiSaynete is not null;

    private string NiveauSaynete => _essaiNiveauSaynete ?? NiveauVie;

    private Saynetes.Contexte ContexteSaynete(bool travail)
    {
        var equipe = EquipeEssai(EquipeCourant());
        var portes = equipe.Values.Where(v => !string.IsNullOrEmpty(v)).ToList();
        int stade = _essaiStade > 0 ? _essaiStade : StadeAffiche();
        var maintenant = DateTime.Now;
        return new Saynetes.Contexte(_essaiHeure ?? maintenant.Hour, maintenant.Month, stade, portes,
            !string.IsNullOrEmpty(equipe.GetValueOrDefault(PilouBureau.Boutique.Compagnon)),
            string.IsNullOrEmpty(equipe.GetValueOrDefault(PilouBureau.Boutique.Main)), travail);
    }

    // Au calme, à la place d'une occupation : peut-être une saynète. Vrai si elle commence.
    private bool TenterSaynete(double t, bool travail, double min, double max)
    {
        if (_essaiSaynete is not null || EnSaisie || t < _sayneteProchaine) return false;
        string niveau = NiveauSaynete;
        if (niveau == AnimationsCampagne.Aucune) return false;
        if (_hasard.NextDouble() >= (travail ? 0.15 : 0.3)) return false;
        var banque = Saynetes.Commune;
        string id = Saynetes.Tirer(banque, _hasard.Next(10000), ContexteSaynete(travail), _sayneteDerniere);
        if (Saynetes.Trouver(banque, id) is not { } s) return false;
        Commencer(s, t, min, max);
        _sayneteProchaine = t + s.Duree + EspaceSaynete * (travail ? 2 : 1) * (0.75 + _hasard.NextDouble() * 0.5);
        return true;
    }

    private void Commencer(Saynetes.Saynete s, double t, double min, double max)
    {
        _saynete = s;
        _sayneteDebut = t;
        _sayneteDerniere = s.Id;
        // Une saynète « tourne » (le bord, le salut) regarde du côté du bord le plus proche.
        _sayneteSens = _x - min < max - _x ? -1 : 1;
        _geste = Geste.Saynete;
    }

    // Pendant Gestes() : la saynète finie, il reprend une pause ordinaire.
    private void AvancerSaynete(double t, double pause)
    {
        if (_saynete is { } s && t - _sayneteDebut < s.Duree) return;
        _saynete = null;
        _sayneteFin = t;
        _geste = Geste.Rien;
        _pauseJusque = t + (2000 + _hasard.NextDouble() * 4000) * pause;
    }

    // Ce que la saynète impose à la pose (après HabillerVie).
    private void HabillerSaynete(Pose p, double t)
    {
        if (_geste != Geste.Saynete) _saynete = null;
        if (_saynete is not { } s) return;
        if (Saynetes.Jouer(s, (long)(t - _sayneteDebut), NiveauSaynete, _sayneteSens) is not { } j) return;
        // Assis : la saynète tient la posture ; à la fin ou coupée, la douceur habituelle le relève (pas de coupe franche).
        _assis = Math.Max(_assis, j.Assis / 1000.0);
        p.Assis = _assis;
        p.Saut += j.Saut / 1000.0;
        p.Etire = j.Etire / 1000.0;
        p.Tremble += j.Penche / 1000.0;
        p.Regard = j.Regard;
        p.RegardY = j.RegardY;
        if (j.Expr != "repos") p.Humeur = j.Expr;
        p.Cligne |= j.Cligne;
        p.Baille = j.Baille;
        p.Salue |= j.Salue;
        p.Marche = false;
        if (j.Objets.Count > 0) p.Gestes = j.Objets;
    }

    private void EssaiSaynete(string nom)
    {
        _essaiSaynete = "";
        foreach (var part in nom.Split(':').Skip(1))
        {
            if (Array.IndexOf(AnimationsCampagne.Niveaux, part) >= 0) _essaiNiveauSaynete = part;
            else if (Saynetes.Trouver(Saynetes.Commune, part) is not null) _essaiSaynete = part;
        }
    }

    // Essai : rien d'autre ne démarre ; une saynète, 800 ms de pause, la suivante.
    private void AnimerEssaiSaynete(double t)
    {
        if (_essaiSaynete is null) return;
        _pauseJusque = Math.Max(_pauseJusque, t + 1000);
        _sayneteProchaine = double.MaxValue;
        if (_geste == Geste.Saynete || t < _sayneteFin + 800) return;
        var banque = Saynetes.Commune;
        if (banque.Count == 0) return;
        var s = _essaiSaynete != "" ? Saynetes.Trouver(banque, _essaiSaynete)! : banque[_essaiSayneteRang++ % banque.Count];
        var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);
        Commencer(s, t, min, max);
    }
}
