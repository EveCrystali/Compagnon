using System.Windows;
using System.Windows.Controls;

namespace PilouBureau;

// « Défense du bureau » depuis Pilou : le menu « Jouer », le lancement (jamais tout seul : à la demande, par le
// menu ou l'icône près de l'horloge), et le crédit des parties (gains bornés, record, quête « jeu », succès).
// Pendant la partie, Pilou est dans la bande : l'overlay habituel se cache et revient à la fermeture.
public sealed partial class FenetrePilou
{
    private FenetreDefense? _defense;

    private MenuItem MenuJouer()
    {
        var m = new MenuItem { Header = "Jouer" };
        m.Items.Add(Entree("Petit jeu au hasard", () => Demarrer(JeuAuHasard(), Maintenant)));
        bool ouvert = Acces.JeuOuvert("defense", Niveau);
        m.Items.Add(Entree(ouvert ? "Défense du bureau" : $"Défense du bureau — niveau {Acces.NiveauJeu("defense")}", () => LancerDefense()));
        m.Items.Add(new Separator());
        m.Items.Add(Choix("Défense : largeur de la bande", new[] { ("Tout l'écran", 1.0), ("Deux tiers", 0.66), ("Moitié", 0.5) },
            _reglages.DefenseLargeur, v => _reglages.DefenseLargeur = v));
        m.Items.Add(Case("Défense : réduire les flashs", _reglages.DefenseFlashsReduits, v => _reglages.DefenseFlashsReduits = v));
        if (_profil.Defense.Meilleur > 0)
            m.Items.Add(new MenuItem { Header = $"Record : {_profil.Defense.Meilleur} (vague {_profil.Defense.MeilleureVague})", IsEnabled = false });
        return m;
    }

    // demo : Pilou joue seul (--essai=defense), sans niveau requis ni gain ni record.
    public void LancerDefense(bool demo = false)
    {
        if (_defense is not null)
        {
            _defense.Activate();
            return;
        }
        if (!demo && !Acces.JeuOuvert("defense", Niveau))
        {
            Dire($"Défense du bureau : niveau {Acces.NiveauJeu("defense")}", 3000);
            return;
        }
        if (!demo && _visites.Sortie is not null)
        {
            Dire("je suis en visite, on jouera à mon retour", 3000);
            return;
        }
        // En route pour sa campagne (ou au repos) : on jouera à son retour (FenetreCampagne.cs).
        if (!demo && RefusPendantCampagne("defense") is { Length: > 0 } refus)
        {
            Dire(refus, 3000);
            return;
        }
        if (_nous == IntPtr.Zero) return;
        Arreter("");
        if (!_zoneConnue) PlacerAuDepart();
        var zone = ZoneSous(_x, _yPieds - 10);
        var allure = Scene.Allure(_scene.Pose);
        allure.Tenue = "";
        allure.Reaction = "";
        allure.Objets = _scene.Pose.Equipe.Where(kv => PilouBureau.Boutique.SurPilou(kv.Key) && kv.Value != "").Select(kv => kv.Value).ToList();
        var l = new LancementDefense(zone, VersEcran.M11 > 0 ? VersEcran.M11 : 1, _reglages.DefenseLargeur, demo, _reglages.DefenseFlashsReduits,
            demo ? 0 : _profil.Defense.Meilleur, (ulong)Environment.TickCount64 ^ (ulong)_hasard.Next(), allure, CrediterDefense, () => _attend,
            v =>
            {
                _reglages.DefenseFlashsReduits = v;
                _reglages.Ecrire(_dossier);
            });
        _defense = new FenetreDefense(l);
        _defense.Closed += (_, _) =>
        {
            _defense = null;
            _cacheJusque = -1e9;
        };
        _cacheJusque = double.MaxValue; // Pilou est dans la bande
        _defense.Show();
    }

    private ResultatDefense CrediterDefense(PartieDefense p)
    {
        var r = GainsDefense.Crediter(_profil.Defense, DateTime.Now, p.Score, p.VaguesFinies, p.VagueAtteinte, p.BossVaincus);
        int xp = r.Xp > 0 ? BonusSoins(r.Xp) : 0;
        _profil.Bourse.PoGagnes += r.Po;
        if (r.Xp > 0) Gagner(r.Xp, new Point(TeteX - 18, TeteY - 30)); // écrit aussi le profil
        else _profil.Ecrire(DossierPartage);
        if (p.VaguesFinies >= 1) Signaler("jeu", 1);
        VerifierSucces(_activite);
        return r with { Xp = xp };
    }
}
