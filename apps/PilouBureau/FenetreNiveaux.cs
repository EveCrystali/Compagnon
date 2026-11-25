using System.Windows;
using System.Windows.Controls;

namespace PilouBureau;

// Niveaux : ils ouvrent l'accès (jeux, rayons de la boutique, stades d'évolution) et rapportent des
// pièces d'or ; l'évolution se joue au premier passage d'un palier (sauf pierre de calme).
public sealed partial class FenetrePilou
{
    private const double DureeEvolution = 4200;
    private double _evolutionDebut = -1;
    private int _evolutionCible;

    private bool Possede(string id) => Bourse().Inventaire.Contains(id);

    // Niveau acquis le plus haut : cet appareil, les PC du dossier partagé, ceux du relais.
    private int NiveauAcquisGroupe()
    {
        int n = _profil.Evolution.NiveauAcquis;
        if (_niveauAcquisCache.T > Maintenant - 5000) return Math.Max(n, _niveauAcquisCache.N);
        int autres = GroupeMem.Compteurs.Select(c => c.NiveauAcquis).DefaultIfEmpty(0).Max();
        autres = Math.Max(autres, _profil.AutresDuDossier(DossierPartage).Select(p => p.Evolution.NiveauAcquis).DefaultIfEmpty(0).Max());
        _niveauAcquisCache = (Maintenant, autres);
        return Math.Max(n, autres);
    }

    private (double T, int N) _niveauAcquisCache = (-1e12, 0);

    // Ce que les niveaux de (exclu) à a (inclus) ont ouvert : jeux, stade, titre, nombre d'articles.
    private List<string> Ouvertures(int de, int a)
    {
        var r = new List<string>();
        foreach (var j in Acces.Jeux.Where(j => j.Niveau > de && j.Niveau <= a)) r.Add(j.Nom.ToLowerInvariant());
        foreach (var s in Acces.Stades.Where(s => s.Niveau > de && s.Niveau <= a && s.Stade > 1)) r.Add($"évolution « {s.Nom} »");
        int articles = PilouBureau.Boutique.Catalogue.Count(x => x.NiveauMin > de && x.NiveauMin <= a);
        if (articles > 0) r.Add($"{articles} article{(articles > 1 ? "s" : "")} en boutique");
        var titre = Recompenses.Toutes.LastOrDefault(t => t.Type == TypeRecompense.Titre && t.Niveau > de && t.Niveau <= a);
        if (titre is not null) r.Add($"titre « {titre.Nom} »");
        return r;
    }

    // Pièces d'or des niveaux gagnés : une seule fois par niveau dans tout le groupe (maximum partagé).
    private void PayerNiveaux(int n)
    {
        var ev = _profil.Evolution;
        int deja = Math.Max(ev.NiveauPaye, GroupeMem.Compteurs.Select(c => c.NiveauPaye).DefaultIfEmpty(0).Max());
        if (ev.Migre < 1 || n <= deja)
        {
            if (deja > ev.NiveauPaye) ev.NiveauPaye = deja;
            return;
        }
        int po = Acces.PoMontee(deja, n);
        ev.NiveauPaye = n;
        _profil.Bourse.PoGagnes += po;
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
        FlotterPo($"+{po} po");
    }

    // ---- Évolution

    private void VerifierEvolution(int n)
    {
        var ev = _profil.Evolution;
        if (ev.Migre < 1 || _evolutionDebut >= 0 || !ev.Due(n)) return;
        if (ev.Retenue) return;
        if (_profil.Bourse.Consommables.GetValueOrDefault(PilouBureau.Boutique.PierreCalme) > 0)
        {
            _profil.Bourse.Consommables[PilouBureau.Boutique.PierreCalme]--;
            ev.Retenue = true;
            _profil.Ecrire(DossierPartage);
            Dire("la pierre de calme retient l'évolution (clic droit → Évolution pour la laisser faire)", 5000);
            return;
        }
        DemarrerEvolution(Acces.Stade(n));
    }

    private void DemarrerEvolution(int cible)
    {
        _evolutionCible = cible;
        _evolutionDebut = Maintenant;
        Dire("… quelque chose se passe !", 3000);
    }

    private double ProgresEvolution(double t)
    {
        if (_evolutionDebut < 0) return 0;
        double x = (t - _evolutionDebut) / DureeEvolution;
        if (x < 1) return Math.Max(0.001, x);
        _evolutionDebut = -1;
        _profil.Evolution.StadeAtteint = Math.Max(_profil.Evolution.StadeAtteint, _evolutionCible);
        _profil.Evolution.StadeAffiche = 0;
        _profil.Ecrire(DossierPartage);
        ChoisirVariante(_evolutionCible);
        Dire($"✦ Pilou est devenu {Acces.NomStade(_evolutionCible)} !", 5000);
        Flotter(Acces.NomStade(_evolutionCible).ToUpperInvariant(), 1.6, new Point(TeteX - 60, TeteY - 70));
        _salueJusque = t + 2500;
        _tSaut = t;
        return 0;
    }

    // Pendant l'évolution : le stade visé (le dessin fond l'ancien dans le nouveau selon Pose.Evolution).
    private int StadeAffiche() => _evolutionDebut >= 0 ? _evolutionCible : _profil.Evolution.Affiche;

    // ---- Menus

    private MenuItem MenuNiveaux()
    {
        int n = Niveau;
        var m = new MenuItem { Header = $"Niveau {n} · {_xpTotal}/{Profil.XpPourNiveau(n + 1)} xp · {Recompenses.Titre(n)}" };
        if (_xpTotal < Profil.XpPourNiveau(n))
            m.Items.Add(new MenuItem { Header = $"Encore {Profil.XpPourNiveau(n + 1) - _xpTotal} xp avant le niveau {n + 1} (niveau acquis gardé)", IsEnabled = false });
        m.Items.Add(new MenuItem { Header = $"Prochain niveau : +{Acces.PoNiveau(n + 1)} po", IsEnabled = false });
        m.Items.Add(new Separator());
        m.Items.Add(new MenuItem { Header = "Jeux", IsEnabled = false });
        foreach (var j in Acces.Jeux)
            m.Items.Add(new MenuItem { Header = (n >= j.Niveau ? "✓  " : $"niv {j.Niveau}  ") + j.Nom, IsEnabled = n >= j.Niveau });
        m.Items.Add(new MenuItem { Header = "Évolution", IsEnabled = false });
        foreach (var s in Acces.Stades)
            m.Items.Add(new MenuItem { Header = (n >= s.Niveau ? "✓  " : $"niv {s.Niveau}  ") + s.Nom, IsEnabled = n >= s.Niveau });
        int ouverts = PilouBureau.Boutique.Catalogue.Count(a => a.NiveauMin <= n);
        m.Items.Add(new MenuItem { Header = $"Boutique : {ouverts}/{PilouBureau.Boutique.Catalogue.Count} articles accessibles", IsEnabled = false });
        var titres = new MenuItem { Header = "Titres" };
        foreach (var t in Recompenses.Toutes.Where(r => r.Type == TypeRecompense.Titre))
            titres.Items.Add(new MenuItem { Header = (n >= t.Niveau ? "✓  " : $"niv {t.Niveau}  ") + t.Nom, IsEnabled = n >= t.Niveau });
        m.Items.Add(titres);
        return m;
    }

    private MenuItem MenuEvolution()
    {
        var ev = _profil.Evolution;
        int atteint = Math.Max(1, ev.StadeAtteint);
        var m = new MenuItem { Header = $"Évolution · {Acces.NomStade(atteint)}" };
        if (ev.Retenue && ev.Due(Niveau))
            m.Items.Add(Entree($"Laisser Pilou évoluer ({Acces.NomStade(Acces.Stade(Niveau))})", () =>
            {
                ev.Retenue = false;
                _profil.Ecrire(DossierPartage);
                DemarrerEvolution(Acces.Stade(Niveau));
            }));
        else if (ev.Retenue)
            m.Items.Add(Entree("Ne plus retenir l'évolution", () =>
            {
                ev.Retenue = false;
                _profil.Ecrire(DossierPartage);
            }));
        int pierres = _profil.Bourse.Consommables.GetValueOrDefault(PilouBureau.Boutique.PierreCalme);
        m.Items.Add(new MenuItem { Header = $"Pierres de calme : {pierres}", IsEnabled = false });
        m.Items.Add(new Separator());
        m.Items.Add(new MenuItem { Header = "Forme affichée", IsEnabled = false });
        var auto = new MenuItem { Header = "La plus grande atteinte", IsCheckable = true, IsChecked = ev.StadeAffiche == 0 };
        auto.Click += (_, _) => ChoisirForme(0);
        m.Items.Add(auto);
        foreach (var s in Acces.Stades.Where(s => s.Stade <= atteint))
        {
            var f = new MenuItem { Header = s.Nom, IsCheckable = true, IsChecked = ev.StadeAffiche == s.Stade };
            f.Click += (_, _) => ChoisirForme(s.Stade);
            m.Items.Add(f);
        }
        return m;
    }

    private void ChoisirForme(int stade)
    {
        _profil.Evolution.StadeAffiche = stade;
        _profil.Ecrire(DossierPartage);
    }
}
