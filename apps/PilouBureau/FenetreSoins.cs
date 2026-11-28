using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace PilouBureau;

// Soins sur le PC : une couche légère et passive par-dessus Pilou. Rien ne s'affiche tant que tout va bien ;
// sous le seuil, une seule petite icône près de sa tête (◒ faim, ✦ propreté, ♥ moral), et un clic la comble.
// « Prendre soin de Pilou » (clic droit) comble tout d'un coup. Négligé, il boude : moue et sourcils froncés,
// petit nuage gris, bras croisés (Nimbus), parfois le dos tourné, il marche plus lentement et ses gains d'XP et
// de po passent à × 0,6 ; soigné, il se laisse amadouer une demi-heure puis se déride. Bien soigné, il rayonne
// (× 1,2). Rien d'autre : ni maladie, ni fugue, ni perte.
public sealed partial class FenetrePilou
{
    private EtatSoins? _soinsEtat;
    private double _soinsCalcul = -1e12, _soinsDossierLu = -1e12, _soinsPlie = -1e12;
    private double _derniereCaresseSoin = -1e12, _dernierJeuSoin = -1e12;
    private double _toiletteJusque = -1e9, _repasDebut = -1e9;
    private Pixels? _iconeSoin, _repas;
    private string _iconeBesoin = "";
    private int _humeurSoins = -1; // 0 : content, 1 : il boude, 2 : il se laisse amadouer (-1 : pas encore vu)
    private double _prochainHmpf;
    private bool _boudeur; // il marche plus lentement
    private bool _essaiDos;

    // État des soins maintenant (recalculé au plus toutes les 2 s : c'est une fonction pure du journal).
    private EtatSoins SoinsMaintenant()
    {
        if (_soinsEtat is null || Maintenant - _soinsCalcul > 2000)
        {
            Soins.Initialiser(_profil.Soins, Epoque, IdAppareil);
            _soinsEtat = Soins.Etat(_profil.Soins, Epoque);
            _soinsCalcul = Maintenant;
        }
        return _soinsEtat;
    }

    private void SoinsChanges() => _soinsCalcul = -1e12;

    // Une action de soin : au journal (partagé avec le groupe et le téléphone), puis recalcul.
    private void FaireSoin(string type, string objet = "")
    {
        Soins.Initialiser(_profil.Soins, Epoque, IdAppareil);
        Soins.Ajouter(_profil.Soins, Soins.Action(type, Epoque, objet));
        _profil.Ecrire(DossierPartage);
        SoinsChanges();
        if (type is "soin" or "nourrir" or "laver" or "calin")
        {
            Signaler("soin", 1);
            Vecu(f => f.So++, "soins");
        }
    }

    // Le meilleur en-cas possédé (consommé), sinon des croquettes gratuites.
    private string ChoisirRepas()
    {
        foreach (var (id, _) in Soins.EnCas)
        {
            if (id == "croquettes" || _profil.Bourse.Consommables.GetValueOrDefault(id) <= 0) continue;
            _profil.Bourse.Consommables[id]--;
            return id;
        }
        if (_profil.Bourse.Consommables.GetValueOrDefault("croquettes") > 0) _profil.Bourse.Consommables["croquettes"]--;
        return "croquettes";
    }

    // Un clic sur l'icône : ce besoin-là est comblé.
    private void Combler(string besoin)
    {
        switch (besoin)
        {
            case Soins.Faim:
                var repas = ChoisirRepas();
                FaireSoin("nourrir", repas);
                Manger(repas);
                EnergieRepas(repas);
                break;
            case Soins.Proprete:
                FaireSoin("laver");
                _toiletteJusque = Maintenant + 2000;
                Dire("✦ tout propre !", 2200);
                break;
            default:
                FaireSoin("calin");
                _tCaresse = Maintenant;
                Dire("♥ merci !", 2000);
                break;
        }
    }

    // « Prendre soin de Pilou » : tout d'un coup (repas, toilette, câlin).
    private void PrendreSoin()
    {
        var e = SoinsMaintenant();
        string repas = e.Faim < 80 ? ChoisirRepas() : "";
        FaireSoin("soin", repas);
        if (repas != "")
        {
            Manger(repas);
            EnergieRepas(repas);
        }
        if (e.Proprete < 80) _toiletteJusque = Maintenant + 2000;
        _tCaresse = Maintenant;
        Dire("♥ Pilou est aux petits soins", 2500);
    }

    // Petit repas : l'en-cas près de sa bouche, croqué en trois bouchées.
    private void Manger(string repas)
    {
        if (_repas is not null) _jeu.Children.Remove(_repas);
        _repas = Pixels.Sprite("encas-" + repas) ?? Pixels.Sprite(repas); // en-cas de route : leur propre dessin
        if (_repas is null) return;
        _repas.IsHitTestVisible = false;
        _repas.RenderTransformOrigin = new Point(0.5, 0.5);
        _jeu.Children.Add(_repas);
        // Près de sa bouche, du côté de la place (miroir exact d'un côté à l'autre).
        Canvas.SetLeft(_repas, Placement.ACote(_aGauche, CoteJeu, 20, _repas.Width));
        Canvas.SetTop(_repas, TeteY + 34);
        _repasDebut = Maintenant;
    }

    // Les caresses et les petits jeux remontent le moral (au plus une fois par heure / demi-heure au journal).
    private void SoinCaresse()
    {
        if (Maintenant - _derniereCaresseSoin < 3600_000) return;
        _derniereCaresseSoin = Maintenant;
        FaireSoin("caresse");
    }

    private void SoinJeu()
    {
        if (Maintenant - _dernierJeuSoin < 1800_000) return;
        _dernierJeuSoin = Maintenant;
        FaireSoin("jouer");
    }

    private bool Rayonnant => _profil.Soins.Base is not null && Soins.Rayonnant(SoinsMaintenant());

    // Tous ses gains d'XP et de po : × 0,6 s'il boude, × 1,2 s'il rayonne.
    private int BonusSoins(int gain) => _profil.Soins.Base is null ? gain : Soins.Bonus(gain, SoinsMaintenant());

    // Ce que la Pose ajoute : variante du stade, rayonnement, mousse ; bouderie (sourcils et moue, nuage gris,
    // bras croisés du Nimbus, dos tourné de temps en temps) ; amadoué, une éclaircie et la moue qui va et vient.
    private (IReadOnlyList<string> Objets, bool Boude, bool Dos) PoseSoins(int stade, double t)
    {
        var objets = new List<string>();
        if (stade >= 2 && _profil.Evolution.Variantes.TryGetValue(stade, out var v))
        {
            objets.Add($"variante-{v}-{stade}");
            objets.Add($"variante-{v}-{stade}-tete");
        }
        _boudeur = false;
        if (_profil.Soins.Base is null) return (objets, false, false);
        var e = SoinsMaintenant();
        if (Soins.Rayonnant(e)) objets.Add("rayonnant");
        if (t < _toiletteJusque) objets.Add("mousse");
        if (!Soins.Boudeur(e)) return (objets, false, false);
        _boudeur = true;
        if (Soins.Amadoue(e))
        {
            objets.Add("boude-eclaircie");
            return (objets, t % 9000 < 6000, false); // il se déride peu à peu : la moue revient de moins en moins
        }
        bool dos = _essaiDos || t % 47_000 > 41_000; // 6 s sur 47 : il tourne le dos
        objets.Add("boude-nuage");
        if (stade == 3 && !dos) objets.Add("boude-bras");
        return (objets, true, dos);
    }

    // Infobulle : « ☁ Pilou boude : gains ×0,6 » (ou amadoué), rien sinon.
    private string HumeurSoins()
    {
        if (_profil.Soins.Base is null) return "";
        var e = SoinsMaintenant();
        return Soins.Amadoue(e) ? "\n☁ Pilou se laisse amadouer : gains ×0,6"
            : Soins.Boudeur(e) ? "\n☁ Pilou boude : gains ×0,6" : "";
    }

    // Les petites phrases de la bouderie : à l'entrée, à la réconciliation, et de loin en loin (8 à 15 min).
    private void SuivreHumeur()
    {
        var e = SoinsMaintenant();
        int h = !Soins.Boudeur(e) ? 0 : Soins.Amadoue(e) ? 2 : 1;
        if (_humeurSoins >= 0 && h != _humeurSoins && !_discret)
        {
            if (h == 1) Dire("hmpf ! ☁", 2600);
            else if (h == 2) Dire("…hmpf. bon, d'accord.", 2800);
            else if (_humeurSoins == 2) Dire("♥ on est réconciliés", 2600);
        }
        if (h != _humeurSoins) _prochainHmpf = Maintenant + (8 + _hasard.NextDouble() * 7) * 60_000;
        _humeurSoins = h;
        if (h == 1 && Maintenant >= _prochainHmpf)
        {
            _prochainHmpf = Maintenant + (8 + _hasard.NextDouble() * 7) * 60_000;
            if (!_discret && _jeuEnCours == Jeu.Aucun) DireSpontane(Hmpf[_hasard.Next(Hmpf.Length)], 2400);
        }
    }

    private static readonly string[] Hmpf = { "hmpf.", "…pff.", "je boude. ☁", "hmpf !", "…" };

    // Appelé à chaque lecture (300 ms) : repli du journal, soins des autres PC du dossier, icône de besoin.
    private void SuivreSoins()
    {
        Soins.Initialiser(_profil.Soins, Epoque, IdAppareil);
        if (Maintenant - _soinsPlie > 600_000)
        {
            _soinsPlie = Maintenant;
            Soins.Plier(_profil.Soins, Epoque);
        }
        if (Maintenant - _soinsDossierLu > 60_000)
        {
            _soinsDossierLu = Maintenant;
            bool change = false;
            foreach (var autre in _profil.AutresDuDossier(DossierPartage))
            {
                change |= Soins.Fusionner(_profil.Soins, autre.Soins.Base, autre.Soins.Origine, autre.Soins.Actions);
                change |= FusionnerVariantes(autre.Evolution.Variantes);
            }
            if (change)
            {
                SoinsChanges();
                _profil.Ecrire(DossierPartage);
            }
        }
        MontrerIcone();
        SuivreHumeur();
    }

    private bool FusionnerVariantes(IReadOnlyDictionary<int, string> autres)
    {
        var fusion = Groupe.FusionVariantes(new[] { (IReadOnlyDictionary<int, string>)_profil.Evolution.Variantes, autres });
        if (fusion.Count == _profil.Evolution.Variantes.Count && fusion.All(kv => _profil.Evolution.Variantes.GetValueOrDefault(kv.Key) == kv.Value))
            return false;
        _profil.Evolution.Variantes = fusion;
        return true;
    }

    // Un compteur du groupe reçu : ses soins et ses variantes rejoignent les nôtres.
    private void RecevoirSoinsGroupe(IEnumerable<Groupe.Compteur> compteurs)
    {
        bool change = false;
        foreach (var c in compteurs)
        {
            change |= Soins.Fusionner(_profil.Soins, c.SoinsBase, c.SoinsOrigine, c.Actions);
            change |= FusionnerVariantes(c.Formes);
        }
        if (!change) return;
        SoinsChanges();
        _profil.Ecrire(DossierPartage);
    }

    // Au passage d'un stade : la qualité des soins des derniers jours choisit la variante (une fois pour toutes).
    private void ChoisirVariante(int stade)
    {
        if (stade < 2 || _profil.Evolution.Variantes.ContainsKey(stade)) return;
        var v = Soins.Variante(SoinsMaintenant().Score);
        _profil.Evolution.Variantes[stade] = v;
        _profil.Ecrire(DossierPartage);
        Dire($"✦ un Pilou {Soins.NomVariante(v)} !", 4000);
    }

    // Une seule icône, la plus pressante, près de la tête ; un clic la comble.
    private void MontrerIcone()
    {
        if (_profil.Soins.Base is null) return;
        var e = SoinsMaintenant();
        var besoin = _discret || _jeuEnCours != Jeu.Aucun ? "" : Soins.Manques(e).FirstOrDefault() ?? "";
        if (besoin != _iconeBesoin)
        {
            if (_iconeSoin is not null) _jeu.Children.Remove(_iconeSoin);
            _iconeSoin = null;
            _iconeBesoin = besoin;
            if (besoin == "") return;
            _iconeSoin = Pixels.Sprite("soin-" + besoin);
            if (_iconeSoin is null) return;
            _iconeSoin.Cursor = Cursors.Hand;
            _iconeSoin.ToolTip = besoin switch
            {
                Soins.Faim => "Pilou a un petit creux — clic : le nourrir",
                Soins.Proprete => "Pilou aimerait une toilette — clic : le laver",
                _ => "Pilou a besoin d'un câlin — clic : un câlin",
            };
            var b = besoin;
            _iconeSoin.MouseLeftButtonUp += (_, ev) =>
            {
                ev.Handled = true;
                Combler(b);
            };
            _jeu.Children.Add(_iconeSoin);
        }
    }

    // Animations des soins (à chaque image) : icône qui flotte doucement, repas croqué.
    private void AnimerSoins(double t)
    {
        if (_iconeSoin is not null)
        {
            Canvas.SetLeft(_iconeSoin, Placement.ACote(_aGauche, -CoteJeu, 24, _iconeSoin.Width));
            Canvas.SetTop(_iconeSoin, TeteY + 4 + Math.Sin(t / 600) * 2);
        }
        if (_repas is not null)
        {
            double x = (t - _repasDebut) / 1400;
            if (x >= 1)
            {
                _jeu.Children.Remove(_repas);
                _repas = null;
                _tSaut = t;
                Dire("miam !", 1600);
            }
            else
            {
                double s = 1 - Math.Floor(x * 3) / 3 * 0.8;
                _repas.RenderTransform = new ScaleTransform(s, s);
            }
        }
    }

    // Rendus de contrôle : --essai=soins:faim|proprete|moral|boude|amadoue|dos|rayonnant|lavage|calin|espiegle.
    private void EssaiSoins(string quoi)
    {
        var e = Soins.Neuf(Epoque);
        switch (quoi)
        {
            case Soins.Faim: e.Faim = 18; break;
            case Soins.Proprete: e.Proprete = 18; break;
            case Soins.Moral: e.Moral = 18; break;
            case "boude" or "dos":
                e.Faim = e.Moral = 12;
                e.Boude = true;
                _essaiDos = quoi == "dos";
                break;
            case "amadoue": e.Boude = true; e.FinBouderie = Epoque + Soins.Rancune; break;
            case "rayonnant": e.Score = 95; break;
            case "lavage": _toiletteJusque = double.MaxValue; break;
            case "calin" or "espiegle":
                if (_essaiStade < 2) _essaiStade = 2;
                _profil.Evolution.Variantes[_essaiStade] = quoi;
                break;
        }
        _profil.Soins = new CarnetSoins { Base = e, Origine = IdAppareil };
        _soinsDossierLu = double.MaxValue; // l'essai ne lit pas les autres PC
        SoinsChanges();
    }

}
