using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace PilouBureau;

// Petites activités avec Pilou : deux ou trois clics, quelques secondes, jamais bloquantes.
// Chaque gain s'affiche (« +10 xp ») et s'ajoute au profil de ce PC (Profil.cs), partagé entre PC
// via le dossier de partage. Les niveaux débloquent les récompenses (Recompenses.cs).
public sealed partial class FenetrePilou
{
    private enum Jeu { Aucun, Etoile, Bulles, TapeCinq, Peche, Cuisine }

    private sealed class BulleSavon
    {
        public Pixels Forme = null!;
        public double Nee, X0, Phase;
        public bool Eclatee;
    }

    private sealed class Flottant
    {
        public Pixels Texte = null!;
        public double Ne, X, Y;
    }

    private readonly Canvas _jeu = new();
    private Jeu _jeuEnCours = Jeu.Aucun;
    private double _jeuDebut, _prochainJeu = 7 * 60_000;
    private Pixels? _etoile;
    private Point _etoilePos;
    private Pixels? _main;
    private readonly List<BulleSavon> _bullesJeu = new();
    private int _bullesEclatees;
    private readonly List<Flottant> _flottants = new();
    private Profil _profil = new();
    private int _xpTotal;              // tous les PC du dossier de partage
    private int _dernierNiveau = -1;
    private double _totalLu = -1e9;
    private bool _dortBureau;

    private static readonly Brush OrangeJeu = Geler(Color.FromRgb(0xf6, 0x9d, 0x50));
    private static readonly Brush OrangeClair = Geler(Color.FromRgb(0xff, 0xd8, 0xb0));
    private static readonly Brush BulleFond = Geler(Color.FromArgb(0x55, 0x6c, 0xb6, 0xff));
    private static readonly Brush Blanc = Geler(Colors.White);
    private static readonly Brush ContourXp = Geler(Color.FromRgb(0x1c, 0x21, 0x28));

    // Motifs des jeux, au pixel de Pilou (4 unités).
    private static readonly int[,] MotifEtoile = Pixels.Motif(
        "0001000", "0001000", "0012100", "1112111", "0122210", "0012100", "0110110", "0100010");
    private static readonly int[,] MotifEtoile2 = Pixels.Motif(
        "0001000", "0001000", "0013100", "1113111", "0133310", "0013100", "0110110", "0100010");
    private static readonly int[,] MotifBulle = Pixels.Motif(
        "001110", "012221", "123222", "122222", "122222", "012220", "001100");
    private static readonly int[,] MotifMain = Pixels.Motif(
        "01010100", "01010100", "01010101", "01111101", "11111111", "01111110", "00111110", "00111100");
    private static readonly Brush BleuClair = Geler(Color.FromRgb(0xb4, 0xdb, 0xff));
    private static readonly Brush ContourBleu = Geler(Color.FromRgb(0x1f, 0x4f, 0x8a));
    private static readonly Brush Creme = Geler(Color.FromRgb(0xf6, 0xf8, 0xfa));

    private static Pixels Cliquable(Pixels p)
    {
        p.Cursor = Cursors.Hand;
        return p;
    }

    // ---- Zones de clic des jeux
    // Une fenêtre WPF transparente (AllowsTransparency) laisse passer les clics sur ses pixels entièrement
    // transparents : seuls les pixels dessinés d'un sprite les recevaient (un clic entre deux doigts de la main
    // passait au bureau). Chaque cible a donc, dessous, un capteur presque invisible (alpha 1/255) qui la déborde
    // de Clics.MargeCible ; il réagit à l'appui (MouseDown), comme la cible elle-même.
    private static readonly Brush Capte = Geler(Color.FromArgb(1, 0, 0, 0));
    private readonly List<(FrameworkElement Cible, Rectangle Capteur)> _capteurs = new();
    private Pixels? _indice;
    private FrameworkElement? _indiceSur;

    private void Cibler(FrameworkElement cible, Action action)
    {
        cible.Cursor = Cursors.Hand;
        cible.MouseLeftButtonDown += (_, e) =>
        {
            action();
            e.Handled = true;
        };
        var capteur = new Rectangle { Fill = Capte, Cursor = Cursors.Hand, Visibility = Visibility.Collapsed, ContextMenu = _scene.ContextMenu };
        capteur.MouseLeftButtonDown += (_, e) =>
        {
            if (cible.Visibility == Visibility.Visible && _jeu.Children.Contains(cible)) action();
            e.Handled = true;
        };
        _jeu.Children.Insert(0, capteur); // sous les éléments du jeu (et au-dessus de Pilou)
        _capteurs.Add((cible, capteur));
    }

    private static bool Place(FrameworkElement e) => !double.IsNaN(Canvas.GetLeft(e)) && !double.IsNaN(Canvas.GetTop(e));

    private void SuivreCapteurs()
    {
        foreach (var (cible, capteur) in _capteurs)
        {
            if (!_jeu.Children.Contains(cible) || cible.Visibility != Visibility.Visible || !Place(cible))
            {
                capteur.Visibility = Visibility.Collapsed;
                continue;
            }
            var z = new Clics.Zone(Canvas.GetLeft(cible), Canvas.GetTop(cible), cible.Width, cible.Height).Elargie(Clics.MargeCible);
            Canvas.SetLeft(capteur, z.X);
            Canvas.SetTop(capteur, z.Y);
            capteur.Width = z.Largeur;
            capteur.Height = z.Hauteur;
            capteur.Visibility = Visibility.Visible;
        }
        // Indice : un petit ▼ pixel qui clignote au-dessus de ce qu'il faut cliquer (fixe si les animations sont coupées).
        if (_indiceSur is { } c && _jeu.Children.Contains(c) && c.Visibility == Visibility.Visible && Place(c))
        {
            _indice ??= new Pixels(Pixels.Texte("▼"), new Brush?[] { null, OrangeJeu }, ContourXp, 2) { IsHitTestVisible = false };
            if (!_jeu.Children.Contains(_indice)) _jeu.Children.Add(_indice);
            int phase = Bandeau.Anime ? (int)(Maintenant / 300) % 2 : 0;
            Canvas.SetLeft(_indice, Math.Round(Canvas.GetLeft(c) + c.Width / 2 - _indice.Width / 2));
            Canvas.SetTop(_indice, Math.Round(Canvas.GetTop(c) - _indice.Height - 2 - phase * 4));
        }
        else if (_indice is not null) _jeu.Children.Remove(_indice);
    }

    private void OterCapteurs()
    {
        foreach (var (_, capteur) in _capteurs) _jeu.Children.Remove(capteur);
        _capteurs.Clear();
        if (_indice is not null) _jeu.Children.Remove(_indice);
        _indiceSur = null;
    }

    // Clic court sur Pilou pendant un jeu (appui à tAppui) : tape m'en cinq, ferrer, remuer. Renvoie s'il a servi.
    private bool ClicJeuSurPilou(double tAppui)
    {
        if (!Clics.ClicSurPilouCompte(IdJeu(_jeuEnCours))) return false;
        switch (_jeuEnCours)
        {
            case Jeu.TapeCinq when _main is not null:
                TapeReussi();
                return true;
            case Jeu.Peche when _bouchon is not null && !_resultat:
                ClicBouchon(tAppui);
                return true;
            case Jeu.Cuisine when _marmite is not null && !_resultat:
                Remuer();
                return true;
            default:
                return false;
        }
    }

    private void TapeReussi()
    {
        if (_main is null) return;
        Gagner(10, new Point(TeteX - 18, TeteY - 30));
        Signaler("jeu", 1);
        Arreter("ouais !");
        _salueJusque = Maintenant + 1800;
        _tSaut = Maintenant;
    }

    private static Brush Geler(Color c)
    {
        var b = new SolidColorBrush(c);
        b.Freeze();
        return b;
    }

    // Repères dans la fenêtre (unités avant mise à l'échelle) : sommet de la tête de Pilou.
    private double TeteX => Placement.TeteX(_aGauche);
    private double TeteY => Placement.TeteY;
    // Courbe actuelle, jamais sous le plus haut niveau acquis (de cet appareil et du groupe).
    private int Niveau => Acces.Niveau(_xpTotal, NiveauAcquisGroupe());
    private string DossierPartage => _reglages.Partage(_dossier);

    private void InitialiserJeux()
    {
        _profil = _demo ? Tournage.ProfilDemo(Epoque) : Profil.Lire(DossierPartage);
        _xpTotal = TotalXp();
        // Anciennes récompenses gratuites → inventaire, niveau acquis (rien de ce qui était acquis n'est perdu).
        if (_profil.Evolution.Migre < 1)
        {
            Migration.Appliquer(_profil, _xpTotal, _reglages);
            _profil.Ecrire(DossierPartage);
        }
        _dernierNiveau = Niveau;
        // L'énergie des expéditions s'affiche dans tous les bandeaux (menu, boutique, info-bulle).
        Bandeau.Energie = () => Jauge.Affiche(Exp.Energie);
        Grid.SetRowSpan(_jeu, 2);
        _racine.Children.Add(_jeu);
    }

    // Essai (--essai=<nom>) : déclenche tout de suite un jeu ou un état, pour les rendus de contrôle.
    // Rendus de contrôle : stade, tenue ou objet imposés (--essai=stade:3, --essai=tenue:code, --essai=objet:cape).
    private int _essaiStade;
    private string _essaiTenue = "", _essaiObjet = "", _essaiHumeur = "";

    private IReadOnlyDictionary<string, string> EquipeEssai(IReadOnlyDictionary<string, string> equipe)
    {
        if (_essaiObjet == "") return equipe;
        var d = new Dictionary<string, string>(equipe);
        var slot = Banque.Commune[_essaiObjet]?.Slot ?? "objet";
        d[PilouBureau.Boutique.Trouver(_essaiObjet)?.Slot is { } s && !PilouBureau.Boutique.SurPilou(s) ? s : slot] = _essaiObjet;
        return d;
    }

    public void Essai(string nom)
    {
        var t = Maintenant;
        // --essai=peche:gauche|droite (et mord:, cuisine:, tape:, etoile:, bulles:) : Pilou collé au bord gauche ou
        // droit de son écran (l'eau, la marmite, la main vont alors du côté de la place), puis le jeu.
        if (Tournage.EssaiAuBord(nom) is { } bord)
        {
            PlacerAuBord(bord.Gauche);
            nom = bord.Jeu;
        }
        if (nom.StartsWith("stade:") && int.TryParse(nom[6..], out var st)) _essaiStade = Math.Clamp(st, 1, 4);
        // --essai=tenue:voyage-marche (course, bateau, grimpe, nage, nuit, cache, attend) : tenues de voyage des campagnes.
        if (nom.StartsWith("tenue:")) _essaiTenue = nom[6..];
        // --essai=humeur:joie (peur, triste, surpris, determine, fatigue, tendre, colere, malice, neutre).
        if (nom.StartsWith("humeur:")) _essaiHumeur = nom[7..];
        // --essai=vie[:completes|reduites|aucune][:heure] : saut, marche et chute en boucle (VieFenetre.cs).
        if (nom == "vie" || nom.StartsWith("vie:")) EssaiVie(nom);
        if (nom == "saynete" || nom.StartsWith("saynete:")) EssaiSaynete(nom);
        if (nom == "eveil" || nom.StartsWith("eveil:")) EssaiEveil(nom);
        // --essai=dessin:origine : le rendu d'origine (grille 48 × 56) ; dessin:fin : le dessin fin.
        if (nom.StartsWith("dessin:"))
        {
            _reglages.DessinFin = nom[7..] != "origine";
            AppliquerTaille();
        }
        if (nom.StartsWith("objet:")) _essaiObjet = nom[6..];
        // --essai=mot, journal, complicite : la présence au quotidien, sur des données de démonstration (rien n'est écrit).
        if (nom is "mot" or "journal" or "complicite" or "traits") EssaiPresence(nom);
        if (nom.StartsWith("soins:")) EssaiSoins(nom[6..]);
        // --essai=fenetre:boutique… : une fenêtre sur le profil de démonstration, pour les captures (EssaiFenetres.cs).
        if (nom.StartsWith("fenetre:")) EssaiFenetre(nom[8..]);
        // --essai=menu[:jouer|apparence/accessoire…][:clair|sombre][:moment] : le vrai menu clic droit ouvert (MenuEssai.cs).
        if (nom == "menu" || nom.StartsWith("menu:")) EssaiMenu(nom[4..]);
        // --essai=bienvenue (avec un dossier de données neuf) : la première minute en accéléré, pour la filmer.
        if (nom == "bienvenue") _bienvenueVite = 5;
        // --essai=visite:depart|arrivee|jeu|retour : une visite chez un ami « Léo », sans réseau.
        if (nom.StartsWith("visite:")) EssaiVisite(nom[7..]);
        // --essai=expedition:depart|absent|retour|defaite|journal : une expédition sans attendre (rien n'est écrit).
        if (nom.StartsWith("expedition:")) EssaiExpedition(nom[11..]);
        // --essai=campagne:prologue : une campagne déroulée en accéléré dans la bulle (rien n'est écrit ni publié).
        if (nom.StartsWith("campagne:")) EssaiCampagne(nom[9..]);
        // --essai=clavier, photo, notif, notif:masque : les petits gestes sans conditions réelles.
        if (nom is "clavier" or "photo" or "notif" or "notif:masque") EssaiGeste(nom);
        // --essai=defense : une partie de Défense du bureau où Pilou joue seul (captures).
        if (nom == "defense") LancerDefense(demo: true);
        // --essai=meteo:pluie, meteo:pluie:parapluie, meteo:neige, meteo:chaleur, meteo:orage…
        if (nom.StartsWith("meteo:"))
        {
            var parts = nom[6..].Split(':');
            _essaiMeteo = parts[0];
            if (parts.Length > 1) _essaiObjet = parts[1];
        }
        // --essai=lieu:<campagne>:<décor> : la vue de scène seule (HD si le décor HD existe), pour les captures.
        if (nom.StartsWith("lieu:") && nom.Split(':') is [_, var lc, var ld]) new FenetreLieu(this, lc, ld).Show();
        // --essai=scene-evolution:2|3|4 : la scène d'évolution de ce stade, en démonstration (rien n'est gardé).
        if (nom.StartsWith("scene-evolution:") && int.TryParse(nom[16..], out int stadeScene)) OuvrirSceneEvolution(stadeScene, demo: true);
        if (nom == "evolution")
        {
            _essaiStade = 0;
            DemarrerEvolution(Math.Min(4, StadeAffiche() + 1));
        }
        switch (nom)
        {
            case "etoile": Demarrer(Jeu.Etoile, t); break;
            case "bulles": Demarrer(Jeu.Bulles, t - 1800); break;
            case "tape": Demarrer(Jeu.TapeCinq, t); break;
            case "etourdi": _etourdiJusque = t + 6000; Dire("ouh, la tête me tourne…", 5000); break;
            case "peche": Demarrer(Jeu.Peche, t); break;
            case "mord":
                Demarrer(Jeu.Peche, t - 800);
                _mordA = t + 250;
                break;
            case "prise":
                Demarrer(Jeu.Peche, t);
                FinPeche(Butin.Prises[^1], false, t);
                break;
            case "cuisine":
                if (!Butin.PeutCuisiner(_profil.Stock)) _profil.Stock["goujon"] = 2;
                Demarrer(Jeu.Cuisine, t - 3000);
                break;
            case "niveau": Flotter("+10 xp"); Flotter("NIVEAU 5", 1.6, new Point(TeteX - 50, TeteY - 70)); Dire("niveau 5 ! nouveau : lunettes de soleil", 5000); break;
        }
    }

    private void PlacerAuBord(bool gauche)
    {
        if (!_zoneConnue) PlacerAuDepart();
        var (min, max) = Placement.BornesPieds(_zone.Left, _zone.Right, K);
        _x = _cible = gauche ? min : max;
        _marcheVers = null;
        Placer(Placement.AGauche(_x, _zone.Left, _zone.Right));
    }

    // ---- Niveaux et XP

    // Appelé à chaque lecture : XP venue de Claude (tours finis, commits, caresses), XP des autres PC.
    private void SuivreXp()
    {
        // L'XP du mod vient d'une session Claude (toutes portent la même) ; les autres sources sont créditées à part.
        var claude = _vivantes.Where(e => e.Claude).MaxBy(e => e.T);
        if (claude is { } c)
        {
            if (_profil.XpClaudeVue < 0)
            {
                // Premier passage : un profil neuf reprend l'XP déjà gagnée avec Claude.
                if (_profil.Xp == 0) _profil.Xp = c.Xp;
                _profil.XpClaudeVue = c.Xp;
                _profil.Ecrire(DossierPartage);
            }
            else if (c.Xp > _profil.XpClaudeVue)
            {
                int gain = BonusSoins(c.Xp - _profil.XpClaudeVue); // il boude : × 0,6 ; il rayonne : × 1,2
                _profil.XpClaudeVue = c.Xp;
                _profil.Xp += gain;
                _profil.Ecrire(DossierPartage);
                _xpTotal += gain;
                Flotter($"+{gain} xp");
            }
            else if (c.Xp < _profil.XpClaudeVue - 50)
            {
                _profil.XpClaudeVue = c.Xp; // magasin du mod remis à zéro
            }
        }
        if (Maintenant - _totalLu > 5000)
        {
            _xpTotal = TotalXp();
            _totalLu = Maintenant;
        }
        VerifierNiveau();
        var nom = _suivi.Courant?.Nom ?? "Pilou";
        int n = Niveau, suivant = Profil.XpPourNiveau(n + 1);
        var activite = TenueAffichee == "" ? "" : $" · {Activites.Signe(TenueAffichee)} {Activites.Nom(TenueAffichee)}";
        // Info-bulle de Pilou : le bandeau (niveau, XP, po, prochaine rangée), puis son nom et son activité.
        if (_infoBulle is null)
        {
            _infoBandeau = new Bandeau(compact: true);
            _infoTexte = new TextBlock { Margin = new Thickness(2, 4, 2, 0), FontSize = 11.5 };
            var pile = new StackPanel();
            pile.Children.Add(_infoBandeau);
            pile.Children.Add(_infoTexte);
            _infoBulle = new ToolTip { Content = pile, Padding = new Thickness(4) };
            _scene.ToolTip = _infoBulle;
        }
        _infoBandeau!.Mettre(n, _xpTotal, Bourse().Solde, Recompenses.Titre(n), Bandeau.ProchaineRangee(n, _xpTotal));
        _infoTexte!.Text = $"{nom} · {_xpTotal}/{suivant} xp{activite}{HumeurSoins()}";
    }

    private ToolTip? _infoBulle;
    private Bandeau? _infoBandeau;
    private TextBlock? _infoTexte;

    private void VerifierNiveau()
    {
        int n = Niveau;
        if (_dernierNiveau > 0 && n > _dernierNiveau)
        {
            var ouvert = Ouvertures(_dernierNiveau, n);
            Sons.Jouer(Son.Succes);
            Dire(ouvert.Count > 0 ? $"niveau {n} ! accès : {string.Join(", ", ouvert)}" : $"niveau {n} !", 5500);
            // Nouvelles rangées en boutique : une petite fenêtre « Voir en boutique ».
            if (PilouBureau.Boutique.Debloques(_dernierNiveau, n).Count > 0) MontrerRangees(_dernierNiveau, n);
            _nouveautesLu = -1e12;
            Flotter($"NIVEAU {n}", 1.6, new Point(TeteX - 50, TeteY - 70));
            Vecu(f => f.Nv = Math.Max(f.Nv, n));
            _salueJusque = Maintenant + 2500;
            _tSaut = Maintenant;
        }
        _dernierNiveau = n;
        if (n > _profil.Evolution.NiveauAcquis && _profil.Evolution.Migre >= 1)
        {
            _profil.Evolution.NiveauAcquis = n;
            _profil.Ecrire(DossierPartage);
        }
        PayerNiveaux(n);
        VerifierEvolution(n);
    }

    private static string Nom(Accessoire a) => a switch
    {
        Accessoire.Bonnet => "Bonnet de laine",
        Accessoire.Casque => "Casque audio",
        Accessoire.Noeud => "Nœud papillon",
        Accessoire.Feuille => "Feuille d'automne",
        Accessoire.Lunettes => "Lunettes de soleil",
        Accessoire.Couronne => "Couronne",
        Accessoire.ChapeauPeche => "Chapeau de pêcheur",
        Accessoire.Toque => "Toque de chef",
        Accessoire.Tablier => "Tablier",
        Accessoire.EtoileMer => "Étoile de mer",
        Accessoire.Aucun => "Aucun",
        _ => "Selon la saison",
    };

    private void Gagner(int xp, Point ou)
    {
        xp = BonusSoins(xp);
        SoinJeu();
        Vecu(f => f.Jx++, "jeux");
        _profil.Xp += xp;
        _profil.JeuxGagnes++;
        _profil.Ecrire(DossierPartage);
        _xpTotal += xp;
        Flotter($"+{xp} xp", 1, ou);
        VerifierNiveau();
    }

    // « +10 xp » qui monte et s'efface au-dessus de la tête (ou d'un point donné).
    private void Flotter(string texte, double taille = 1, Point? ou = null)
    {
        var tb = new Pixels(Pixels.Texte(texte), new Brush?[] { null, OrangeJeu }, ContourXp, taille >= 1.5 ? 3 : 2) { IsHitTestVisible = false };
        var p = ou ?? new Point(TeteX - 18, TeteY - 10);
        _jeu.Children.Add(tb);
        // Un long mot (« PILOU NIMBUS ») ne déborde ni de la fenêtre ni de l'écran de Pilou.
        double x = Placement.Borner(p.X, tb.Width, _visible.X0 + 2, _visible.X1 - 2);
        _flottants.Add(new Flottant { Texte = tb, Ne = Maintenant, X = x, Y = p.Y });
    }

    // ---- Sommeil de bureau

    // Personne au clavier depuis 10 min et rien qui tourne : il s'endort. Le premier geste le réveille.
    private Expr Sommeil(Expr expr, double t)
    {
        // Tu t'absentes (10 min, ou 2 min la nuit) et aucune IA ne travaille ni n'attend : il s'endort (Saynetes.Endormi).
        bool personne = Saynetes.Endormi(_essaiHeure ?? DateTime.Now.Hour, _inactif) && !_vivantes.Any(e => e.EnTour || e.Attente != "");
        if (personne && !_dortBureau)
        {
            _dortBureau = true;
            Arreter("");
        }
        if (_dortBureau && _inactif < 2500)
        {
            _dortBureau = false;
            _tSaut = t;
            // Un bonjour l'attend (petit mot du jour, FenetrePresence.cs) : c'est lui qui parlera.
            if (!MotEnAttente) Dire("bien dormi !", 2500);
        }
        return _dortBureau && expr is Expr.Repos or Expr.Inquiet ? Expr.Dort : expr;
    }

    // ---- Activités

    private void ProposerJeu(double t, Expr expr)
    {
        if (!_reglages.Jeux || _jeuEnCours != Jeu.Aucun || t < _prochainJeu) return;
        if (expr is not Expr.Repos || _dortBureau || _inactif > 60_000 || _geste == Geste.SauteSouris || _attrape) return;
        // Pas en pleine saisie ni juste après une autre réaction : il repasse une minute plus tard.
        if (!Dosage.Libre(t, EnSaisie))
        {
            _prochainJeu = t + 60_000;
            return;
        }
        Dosage.Noter(t);
        // Toutes les 14 à 28 min environ (8 à 16 avant), pour ne pas te sortir de ton travail trop souvent.
        _prochainJeu = t + (8 + _hasard.NextDouble() * 8) * Vivacite.EspacementJeux * 60_000;
        // Une fois sur trois, une partie de pêche (tu es là : à toi de ferrer).
        Demarrer(_hasard.NextDouble() < 0.33 && Acces.JeuOuvert("peche", Niveau) ? Jeu.Peche : JeuAuHasard(), t);
    }

    private static string IdJeu(Jeu j) => j switch
    {
        Jeu.Etoile => "etoile", Jeu.Bulles => "bulles", Jeu.TapeCinq => "tape", Jeu.Peche => "peche", Jeu.Cuisine => "cuisine", _ => "",
    };

    // Un jeu au hasard parmi ceux que le niveau ouvre (étoile, bulles, tape m'en cinq).
    private Jeu JeuAuHasard()
    {
        var ouverts = new[] { Jeu.Etoile, Jeu.Bulles, Jeu.TapeCinq }.Where(j => Acces.JeuOuvert(IdJeu(j), Niveau)).ToList();
        return ouverts.Count == 0 ? Jeu.Etoile : ouverts[_hasard.Next(ouverts.Count)];
    }

    private void Demarrer(Jeu jeu, double t)
    {
        // Pas de petit jeu pendant une expédition (Pilou n'est pas là).
        if (jeu != Jeu.Aucun && EnExpedition)
        {
            Dire("Pilou est en expédition : on jouera à son retour", 3000);
            return;
        }
        // Ni pendant l'attente d'une campagne : il est en route, ou se repose.
        if (jeu != Jeu.Aucun && RefusPendantCampagne("jeu") is { Length: > 0 } refus)
        {
            Dire(refus, 3000);
            return;
        }
        if (jeu != Jeu.Aucun && !Acces.JeuOuvert(IdJeu(jeu), Niveau))
        {
            Dire($"{Acces.Jeux.First(x => x.Id == IdJeu(jeu)).Nom} : niveau {Acces.NiveauJeu(IdJeu(jeu))}", 3000);
            return;
        }
        Arreter("");
        _jeuEnCours = jeu;
        _jeuDebut = t;
        _geste = Geste.Rien;
        switch (jeu)
        {
            case Jeu.Etoile:
                _etoile = Pixels.Sprite("etoile", 2.2) ?? new Pixels(MotifEtoile, new Brush?[] { null, OrangeJeu, OrangeClair, Blanc }, ContourXp);
                // Dans la partie de la fenêtre qui est sur l'écran de Pilou (Borner), pas sur l'écran voisin.
                _etoilePos = new Point(Placement.Borner(TeteX + (_hasard.NextDouble() * 2 - 1) * 120, _etoile.Width + 12,
                    _visible.X0 + 16, _visible.X1 - 12), 24 + _hasard.NextDouble() * 70);
                _jeu.Children.Add(_etoile);
                Cibler(_etoile, () =>
                {
                    if (_etoile is null) return;
                    Gagner(10, _etoilePos);
                    Signaler("jeu", 1);
                    Arreter("bien vu !");
                    _salueJusque = Maintenant + 1500;
                });
                _indiceSur = _etoile;
                Dire("une étoile filante ! clique dessus", 2600);
                break;
            case Jeu.Bulles:
                _bullesEclatees = 0;
                for (int i = 0; i < 3; i++)
                {
                    var b = new BulleSavon
                    {
                        Forme = Cliquable(Pixels.Sprite("bulle", 2.2) ?? new Pixels(MotifBulle, new Brush?[] { null, Creme, BulleFond, Blanc }, null)),
                        Nee = t + i * 450,
                        X0 = TeteX + (i - 1) * 34,
                        Phase = _hasard.NextDouble() * 6,
                    };
                    b.Forme.Visibility = Visibility.Hidden;
                    _bullesJeu.Add(b);
                    _jeu.Children.Add(b.Forme);
                    Cibler(b.Forme, () =>
                    {
                        if (b.Eclatee || _jeuEnCours != Jeu.Bulles) return;
                        b.Eclatee = true;
                        _bullesEclatees++;
                        var ou = new Point(Canvas.GetLeft(b.Forme), Canvas.GetTop(b.Forme));
                        _jeu.Children.Remove(b.Forme);
                        Gagner(5, ou);
                        if (_bullesEclatees == 3)
                        {
                            Gagner(5, new Point(TeteX - 30, TeteY - 40));
                            Signaler("jeu", 1);
                            Arreter("toutes ! bonus");
                            _salueJusque = Maintenant + 1500;
                        }
                    });
                }
                Dire("pop les bulles ! clique dessus", 2400);
                break;
            case Jeu.Peche:
                DemarrerPeche(t);
                break;
            case Jeu.Cuisine:
                DemarrerCuisine(t);
                break;
            case Jeu.TapeCinq:
                // Le pouce vers Pilou, des deux côtés (dessin retourné quand la main est à sa droite).
                _main = Pixels.Sprite("main", 2.2, 0, CoteJeu > 0) ?? new Pixels(MotifMain, new Brush?[] { null, Creme }, ContourBleu);
                _jeu.Children.Add(_main);
                Cibler(_main, TapeReussi);
                _indiceSur = _main;
                Dire("tape m'en cinq ! clique sur la main (ou sur moi)", 3000);
                break;
        }
    }

    private void Arreter(string mot)
    {
        if (_etoile is not null) _jeu.Children.Remove(_etoile);
        if (_main is not null) _jeu.Children.Remove(_main);
        foreach (var b in _bullesJeu) _jeu.Children.Remove(b.Forme);
        _etoile = null;
        _main = null;
        _bullesJeu.Clear();
        OterCapteurs();
        ArreterPeche();
        _jeuEnCours = Jeu.Aucun;
        if (mot != "") Dire(mot, 1800);
    }

    private static System.Windows.Shapes.Path EtoileVectorielle()
    {
        var g = new StreamGeometry();
        using (var c = g.Open())
        {
            for (int i = 0; i < 10; i++)
            {
                double a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 == 0 ? 13 : 5.5;
                var pt = new Point(13 + Math.Cos(a) * r, 13 + Math.Sin(a) * r);
                if (i == 0) c.BeginFigure(pt, true, true);
                else c.LineTo(pt, true, false);
            }
        }
        g.Freeze();
        return new System.Windows.Shapes.Path
        {
            Data = g,
            Fill = OrangeJeu,
            Stroke = OrangeClair,
            StrokeThickness = 1.5,
            Cursor = Cursors.Hand,
            RenderTransformOrigin = new Point(0.5, 0.5),
            RenderTransform = new RotateTransform(),
        };
    }

    // Une image : positions, délais, fin des jeux, XP qui flotte.
    private void AnimerJeux(double t)
    {
        var age = t - _jeuDebut;
        switch (_jeuEnCours)
        {
            case Jeu.Etoile when _etoile is not null:
                if (age > Clics.DureeEtoile)
                {
                    Arreter("trop tard, elle est partie…");
                    break;
                }
                // Alignée sur la grille de pixels ; elle scintille au lieu de tourner.
                Canvas.SetLeft(_etoile, Math.Round((_etoilePos.X + Math.Sin(t / 400) * 6) / 4) * 4);
                Canvas.SetTop(_etoile, Math.Round((_etoilePos.Y + Math.Cos(t / 520) * 4) / 4) * 4);
                if (Banque.Commune["etoile"] is not null) _etoile.Changer("etoile", t);
                else _etoile.Changer((int)(t / 220) % 2 == 0 ? MotifEtoile : MotifEtoile2);
                // Elle pâlit sur la fin, sans disparaître : on la voit encore pour cliquer.
                _etoile.Opacity = age > Clics.DureeEtoile - 1500 ? Math.Max(0.4, (Clics.DureeEtoile - age) / 1500) : 1;
                break;
            case Jeu.Bulles:
            {
                bool restent = false;
                foreach (var b in _bullesJeu)
                {
                    if (b.Eclatee) continue;
                    double vie = t - b.Nee;
                    if (vie < 0) continue;
                    double y = TeteY - 10 - vie / 1000 * Clics.VitesseBulles;
                    if (y < -30) { b.Eclatee = true; _jeu.Children.Remove(b.Forme); continue; }
                    restent = true;
                    b.Forme.Visibility = Visibility.Visible;
                    Canvas.SetLeft(b.Forme, Math.Round((b.X0 - 16 + Math.Sin(vie / 600 + b.Phase) * 14) / 4) * 4);
                    Canvas.SetTop(b.Forme, Math.Round(y / 4) * 4);
                }
                if (!restent && age > 1500) Arreter(_bullesEclatees > 0 ? "" : "plus de bulles…");
                break;
            }
            case Jeu.Peche:
                AnimerPeche(t);
                break;
            case Jeu.Cuisine:
                AnimerCuisine(t);
                break;
            case Jeu.TapeCinq when _main is not null:
                if (age > Clics.DureeTapeCinq)
                {
                    Arreter("bon… plus tard");
                    break;
                }
                // Elle s'agite d'un pixel, au lieu de grossir (le pixel reste net).
                _main.Palette = new Brush?[] { null, (int)(t / 250) % 2 == 0 ? Creme : OrangeClair };
                // À côté de sa tête, du côté où il y a de la place dans la fenêtre (miroir exact).
                Canvas.SetLeft(_main, Placement.ACote(_aGauche, CoteJeu, 34, _main.Width));
                Canvas.SetTop(_main, TeteY - 6 + ((int)(t / 200) % 2) * 4);
                if ((int)(age / 900) != (int)((age - 33) / 900)) _tSaut = t;
                break;
        }

        if (_jeuEnCours != Jeu.Aucun) SuivreCapteurs();

        for (int i = _flottants.Count - 1; i >= 0; i--)
            if (t - _flottants[i].Ne >= Flottants.Vie)
            {
                _jeu.Children.Remove(_flottants[i].Texte);
                _flottants.RemoveAt(i);
            }
        if (_flottants.Count == 0) return;
        // Jamais sur la bulle ni l'un sur l'autre (Flottants.cs) : remonté au-dessus, ou caché le temps qu'elle se range.
        var obstacles = new List<Flottants.Boite>();
        if (BoiteBulle() is { } bulle) obstacles.Add(bulle);
        foreach (var f in _flottants)
        {
            double k = (t - f.Ne) / Flottants.Vie;
            double y = f.Y - k * Flottants.Montee;
            if (Flottants.Placer(f.X, y, f.Texte.Width, f.Texte.Height, obstacles, (1 - k) * Flottants.Montee) is not { } p)
            {
                f.Ne = t;
                f.Texte.Opacity = 0;
                continue;
            }
            f.Y += p - y;
            Canvas.SetLeft(f.Texte, f.X);
            Canvas.SetTop(f.Texte, p);
            f.Texte.Opacity = k < 0.7 ? 1 : (1 - k) / 0.3;
            obstacles.Add(new Flottants.Boite(f.X, p, f.X + f.Texte.Width, p + f.Texte.Height));
        }
    }

    // Le cadre de la bulle dans le calque des jeux, ou null quand elle est rangée.
    private Flottants.Boite? BoiteBulle()
    {
        if (_pileBulle.Visibility != Visibility.Visible || !_bulle.IsVisible || _bulle.ActualWidth <= 0) return null;
        var r = _bulle.TransformToVisual(_jeu).TransformBounds(new Rect(0, 0, _bulle.ActualWidth, _bulle.ActualHeight));
        return Flottants.DeBulle(r.Left, r.Top, r.Right, r.Bottom);
    }
}
