using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace PilouBureau;

// Quêtes et pièces d'or (po) sur le PC : signaux venus des jeux, de la pêche, de la cuisine, des sessions
// Claude/Codex (tours, commits, tests), du téléphone et de la présence ; récompenses annoncées par une
// pièce qui monte ; menus « Quêtes » et « Boutique… ».
public sealed partial class FenetrePilou
{
    private readonly Dictionary<string, (int Commits, int Tests)> _compteursVus = new();
    private double _presenceVue = -1e12, _quetesEcrites = -1e12;
    private (double T, int Solde, List<string> Inventaire, Dictionary<string, Port> Equipe)? _bourseCache;

    // Point d'entrée générique : Signaler("peche", 1), Signaler("activite:code", 15)…
    public void Signaler(string cle, int quantite)
    {
        var gains = Quetes.Signaler(_profil.Quetes, cle, quantite, DateTime.Now, IdAppareil);
        if (gains.Count > 0) Recompenser(gains);
        else if (Maintenant - _quetesEcrites > 30_000)
        {
            // La progression est écrite au plus toutes les 30 s (pas à chaque minute de présence).
            _quetesEcrites = Maintenant;
            _profil.Ecrire(DossierPartage);
        }
    }

    private void Recompenser(IReadOnlyList<RecompenseQuete> gains)
    {
        if (gains.Count == 0) return;
        // Soins : po et XP × 0,6 s'il boude, × 1,2 s'il rayonne (ajustés avant d'être crédités : le compteur
        // de po gagnées ne fait que monter).
        var (po, xp) = Quetes.Appliquer(_profil, gains.Select(g => g with { Po = BonusSoins(g.Po), Xp = BonusSoins(g.Xp) }));
        EnergieQuete(gains.Count(g => !g.Coffre)); // bien travailler recharge l'énergie des expéditions
        Vecu(f => f.Qu += gains.Count(g => !g.Coffre));
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
        _xpTotal = TotalXp();
        FlotterPo($"+{po} po");
        if (xp > 0) Flotter($"+{xp} xp", 1, new Point(TeteX - 18, TeteY - 30));
        var coffre = gains.FirstOrDefault(g => g.Coffre);
        var quete = gains.FirstOrDefault(g => !g.Coffre);
        Dire(coffre is not null ? $"✦ {coffre.Texte} !" : $"✦ quête réussie : {quete?.Texte}", 4200);
        PublierSortie(coffre is not null ? $"✦ {coffre.Texte}" : "✦ Quête réussie", coffre is null ? quete?.Texte ?? "" : "");
        _salueJusque = Maintenant + 1800;
        _tSaut = Maintenant;
        VerifierNiveau();
    }

    // « +30 po » : une pièce d'or en pixels suivie du texte, qui monte et s'efface.
    private void FlotterPo(string texte)
    {
        var ou = new Point(TeteX + 14, TeteY - 22);
        var piece = new Pixels(Pixels.Motif("01110", "12221", "12321", "12221", "01110"),
            new Brush?[] { null, OrangeJeu, OrangeClair, Blanc }, ContourXp, 2) { IsHitTestVisible = false };
        _jeu.Children.Add(piece);
        _flottants.Add(new Flottant { Texte = piece, Ne = Maintenant, X = ou.X - 16, Y = ou.Y });
        Flotter(texte, 1, ou);
    }

    // Appelé à chaque lecture des sessions : tours finis, commits et tests, présence.
    private void SuivreQuetes(IReadOnlyList<EtatSession> vivantes)
    {
        foreach (var e in vivantes)
        {
            if (_compteursVus.TryGetValue(e.Session, out var vu))
            {
                if (e.Commits > vu.Commits) Signaler("commit", Math.Min(10, e.Commits - vu.Commits));
                if (e.Tests > vu.Tests) Signaler("tests", Math.Min(10, e.Tests - vu.Tests));
            }
            _compteursVus[e.Session] = (e.Commits, e.Tests);
        }
        // Présence : une minute comptée par minute passée au clavier (2 min sans geste : on n'est plus là).
        var t = Maintenant;
        if (t - _presenceVue >= 60_000)
        {
            bool premier = _presenceVue < 0;
            _presenceVue = t;
            if (!premier && Natif.InactifMs() < 120_000) Signaler("presence", 1);
        }
    }

    // Solde, inventaire et équipement du groupe (relus au plus toutes les 5 s : le dossier partagé est sur disque).
    private (int Solde, List<string> Inventaire, Dictionary<string, Port> Equipe) Bourse()
    {
        if (_bourseCache is { } c && Maintenant - c.T < 5000) return (c.Solde, c.Inventaire, c.Equipe);
        var autres = _profil.AutresDuDossier(DossierPartage);
        var solde = Math.Max(0, Groupe.SoldePo(_profil, autres, GroupeMem.Compteurs));
        var inventaire = Groupe.Inventaire(_profil, autres, GroupeMem.Compteurs);
        var equipe = Groupe.Equipe(_profil, autres, GroupeMem.Compteurs);
        _bourseCache = (Maintenant, solde, inventaire, equipe);
        return (solde, inventaire, equipe);
    }

    private IReadOnlyDictionary<string, string> EquipeCourant() => PilouBureau.Boutique.Porte(Bourse().Equipe);

    // Titre affiché : celui que Pilou porte (boutique, ensemble, collection), sinon le titre de son niveau.
    internal string TitreAffiche(int niveau)
    {
        var (_, _, equipe) = EtatBourse();
        return PilouBureau.Boutique.NomTitre(equipe.GetValueOrDefault(PilouBureau.Boutique.Titre)?.Id) ?? Recompenses.Titre(niveau);
    }

    // ---- Menus

    private MenuItem MenuQuetes()
    {
        var maintenant = DateTime.Now;
        Quetes.Actualiser(_profil.Quetes, maintenant, IdAppareil);
        int serie = Quetes.Serie(_profil.Quetes, maintenant);
        var m = new MenuItem { Header = $"Quêtes · {Bourse().Solde} po{(serie > 0 ? $" · série {serie} j" : "")}" };
        foreach (var p in new[] { Periode.Jour, Periode.Semaine, Periode.Mois })
        {
            var liste = _profil.Quetes.Liste.Where(q => q.Periode == p).ToList();
            if (liste.Count == 0) continue;
            if (m.Items.Count > 0) m.Items.Add(new Separator());
            m.Items.Add(new MenuItem { Header = $"{Quetes.Signe(p)}  {Quetes.NomPeriode(p)} · {Quetes.Reste(p, maintenant)}", IsEnabled = false });
            foreach (var q in liste)
                m.Items.Add(new MenuItem
                {
                    Header = (q.Reussie ? "✓  " : "○  ") + $"{q.Texte}   {q.Fait}/{q.Objectif}   · {q.Po} po",
                    IsEnabled = !q.Reussie,
                });
        }
        var jour = _profil.Quetes.Liste.Where(q => q.Periode == Periode.Jour).ToList();
        m.Items.Add(new Separator());
        m.Items.Add(new MenuItem
        {
            Header = _profil.Quetes.CoffreJour == Quetes.CleJour(maintenant) ? "▣  Coffre du jour ouvert"
                : $"▢  Coffre du jour : {jour.Count(q => q.Reussie)}/{jour.Count} quêtes",
            IsEnabled = false,
        });
        return m;
    }

    // Ouvre la boutique ; ce qui s'est ouvert depuis la dernière visite y clignote (« rangée débloquée ! »).
    private void OuvrirBoutique() => OuvrirBoutique("vitrine");

    private void OuvrirBoutique(string rayon)
    {
        int vu = _reglages.BoutiqueVue;
        _reglages.BoutiqueVue = Math.Max(vu, Niveau);
        _reglages.BoutiqueOffresVues = DateTime.Now.ToString("yyyy-MM-dd");
        _reglages.Ecrire(_dossier);
        _nouveautesLu = -1e12;
        new FenetreBoutique(this, vu, rayon).ShowDialog();
        _nouveautesLu = -1e12;
    }

    // Nouveautés : articles des rangées ouvertes depuis la dernière visite (pas encore à nous) + offres du jour pas vues.
    private int NouveautesBoutique()
    {
        int n = Niveau;
        var (_, inventaire, _) = Bourse();
        int vu = _reglages.BoutiqueVue;
        int neufs = vu <= 0
            ? PilouBureau.Boutique.Catalogue.Count(a => PilouBureau.Boutique.Ouvert(a, n) && !inventaire.Contains(a.Id) && a.Slot != PilouBureau.Boutique.Consommable)
            : PilouBureau.Boutique.Debloques(vu, n).Count(a => !inventaire.Contains(a.Id));
        if (_reglages.BoutiqueOffresVues != DateTime.Now.ToString("yyyy-MM-dd"))
            neufs += PilouBureau.Boutique.OffresDuJour(DateOnly.FromDateTime(DateTime.Now))
                .Count(a => PilouBureau.Boutique.Ouvert(a, n) && !inventaire.Contains(a.Id));
        return neufs;
    }

    private double _nouveautesLu = -1e12;
    private int _nouveautes;
    private Pixels? _badgeBoutique;

    // Badge discret près de Pilou (sac de boutique) quand une rangée s'ouvre ou qu'une offre du jour attend ; un clic ouvre la boutique.
    private void AnimerBoutique(double t)
    {
        if (t - _nouveautesLu > 4000)
        {
            _nouveautesLu = t;
            _nouveautes = NouveautesBoutique();
        }
        bool montrer = _nouveautes > 0 && _jeuEnCours == Jeu.Aucun;
        if (montrer && _badgeBoutique is null)
        {
            _badgeBoutique = Pixels.Sprite("badge-boutique", 2);
            if (_badgeBoutique is null) return;
            _badgeBoutique.Cursor = System.Windows.Input.Cursors.Hand;
            _badgeBoutique.MouseLeftButtonUp += (_, e) =>
            {
                e.Handled = true;
                OuvrirBoutique();
            };
            _jeu.Children.Add(_badgeBoutique);
        }
        else if (!montrer && _badgeBoutique is not null)
        {
            _jeu.Children.Remove(_badgeBoutique);
            _badgeBoutique = null;
        }
        if (_badgeBoutique is null) return;
        _badgeBoutique.ToolTip = $"Boutique : {_nouveautes} nouveauté{(_nouveautes > 1 ? "s" : "")} — clic pour y aller";
        if (Bandeau.Anime) _badgeBoutique.Changer("badge-boutique", t);
        Canvas.SetLeft(_badgeBoutique, Placement.ACote(_aGauche, CoteJeu, 34, _badgeBoutique.Width));
        Canvas.SetTop(_badgeBoutique, TeteY - 6 + (Bandeau.Anime ? Math.Round(Math.Sin(t / 500) * 2) : 0));
    }

    // Pour la fenêtre de la boutique.
    internal (int Solde, List<string> Inventaire, Dictionary<string, Port> Equipe) EtatBourse() => Bourse();

    internal int NiveauActuel => Niveau;

    internal int XpTotal => _xpTotal;

    internal int StadePilou => Math.Max(1, StadeAffiche());

    internal string CouleurDeBase => "bleu";

    internal string AccessoireChoisi => _reglages.Accessoire is Accessoire.Aucun or Accessoire.Saison ? "" : Recompenses.IdAccessoire(_reglages.Accessoire);

    internal int Reserve(string id) => _profil.Bourse.Consommables.GetValueOrDefault(id);

    internal string? Acheter(string id)
    {
        var (solde, inventaire, _) = Bourse();
        if (inventaire.Contains(id) && PilouBureau.Boutique.Trouver(id)?.Slot != PilouBureau.Boutique.Consommable) return "déjà dans l'inventaire";
        var refus = PilouBureau.Boutique.Acheter(_profil.Bourse, id, Niveau, solde, DateOnly.FromDateTime(DateTime.Now));
        if (refus is not null) return refus;
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
        Dire($"nouveau : {PilouBureau.Boutique.Trouver(id)?.Nom} !", 3000);
        if (PilouBureau.Boutique.Trouver(id) is { Slot: not PilouBureau.Boutique.Consommable } achat) Vecu(f => f.Ob = f.Ob == "" ? Presence.Propre(achat.Nom) : f.Ob);
        return null;
    }

    internal void Equiper(string slot, string id)
    {
        // Accessoire historique : porté via les réglages (« selon la saison » reste possible).
        if (slot == PilouBureau.Boutique.Accessoire)
        {
            var a = Enum.GetValues<Accessoire>().FirstOrDefault(x => Recompenses.IdAccessoire(x) == id);
            _reglages.Accessoire = id == "" ? Accessoire.Aucun : a;
            _reglages.Ecrire(_dossier);
            return;
        }
        // Un objet acheté sur un autre appareil du groupe est aussi à nous.
        if (id != "" && !_profil.Bourse.Inventaire.Contains(id) && Bourse().Inventaire.Contains(id)) _profil.Bourse.Inventaire.Add(id);
        double t = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        // Titre ou cadre gagné (ensemble complet, palier de collection) : compté sur l'inventaire de tout le groupe.
        if (PilouBureau.Boutique.TrouverTout(id) is { Recompense: true } && PilouBureau.Boutique.PeutPorter(Bourse().Inventaire, slot, id))
            _profil.Bourse.Equipe[slot] = new Port(id, t);
        else if (!PilouBureau.Boutique.Equiper(_profil.Bourse, slot, id, t)) return;
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
    }
}
