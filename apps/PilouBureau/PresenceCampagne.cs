using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media;

namespace PilouBureau;

// Les campagnes sur l'overlay (docs/CAMPAGNES.md, « Sur Windows ») : Pilou « présent mais occupé » pendant une
// attente (tenue de voyage, il marche sur place, rame, grimpe ou dort ; ni promenade, ni petits jeux, ni réactions
// cosmétiques), cabossé pendant un repos ; une ligne discrète dans la bulle, sous les sessions ; à son retour, UNE
// annonce (petit saut, bulle) puis un signe « ! » discret tant que la fenêtre Aventure n'a pas été ouverte.
// Jamais de fenêtre qui s'ouvre toute seule. Tout ce qui est nouveau ici est protégé : une erreur coupe la présence
// de la campagne (Pilou reste visible, comme avant), elle n'arrête jamais Pilou.
public sealed partial class FenetrePilou
{
    private FenetreAventure? _fenetreAventure;
    private Aventure.Retour _retour = Aventure.Aucun;
    private Campagnes.Phase _campPhaseVue = Campagnes.Phase.Aucune;
    private bool _campPhaseConnue, _campPret, _essaiCampRapide;
    private double _campPretAuPlusTard = 25_000;
    private Pixels? _badgeRetour;
    private string _messageTag = "", _essaiAnnoncee = "";
    private int _aventureErreurs;
    private string _infobulleMise = "";

    // Trois erreurs dans ces chemins neufs : on les coupe pour cette session (Pilou continue comme avant).
    private bool AventureCoupee => _aventureErreurs >= 3;

    private void Prudemment(Action a)
    {
        if (AventureCoupee) return;
        try
        {
            a();
        }
        catch (Exception e) when (e is not OutOfMemoryException)
        {
            _aventureErreurs++;
            System.Diagnostics.Debug.WriteLine($"Aventure : {e}");
        }
    }

    private T Prudemment<T>(Func<T> f, T repli)
    {
        if (AventureCoupee) return repli;
        try
        {
            return f();
        }
        catch (Exception e) when (e is not OutOfMemoryException)
        {
            _aventureErreurs++;
            System.Diagnostics.Debug.WriteLine($"Aventure : {e}");
            return repli;
        }
    }

    // Pilou est en route ou se repose (essai accéléré dans la bulle : non, il déroule tout seul).
    private bool CampagneOccupe => !_essaiCampRapide && !AventureCoupee && _campEtat is { EnAttente: true } e && Epoque < e.Fin;

    // Tenue de voyage à dessiner pendant l'attente : « voyage-<tenue> » ; il court rejoindre la souris si une IA t'attend.
    private string TenueCampagne()
    {
        if (!CampagneOccupe || _campEtat is not { } e) return "";
        if (_court) return "voyage-course";
        var mode = Array.IndexOf(RenduPilou.Voyages, e.Tenue) >= 0 ? e.Tenue : e.Phase == Campagnes.Phase.Repos ? "nuit" : "marche";
        return "voyage-" + mode;
    }

    // Ce que la campagne change à la pose : tenue de voyage, humeur du dernier message (au calme), pansement au repos.
    private void HabillerCampagne(Pose p) => Prudemment(() =>
    {
        if (!CampagneOccupe || _campEtat is not { } e) return;
        if (_essaiTenue == "") p.Tenue = TenueCampagne();
        if (_essaiHumeur == "" && p.Expr == Expr.Repos && e.Phase == Campagnes.Phase.Attente && e.Humeur is not ("" or "neutre")) p.Humeur = e.Humeur;
        p.Reaction = "";
        if (e.Phase == Campagnes.Phase.Repos) p.Soins = p.Soins.Append("pansement").ToList();
    });

    // ---- Suivi (environ chaque seconde, SuivreCampagne) : départ, retour, annonce, signe

    private void SuivrePresence() => Prudemment(() =>
    {
        var e = _campEtat;
        var phase = e?.Phase ?? Campagnes.Phase.Aucune;
        // Le départ vu en direct (pas au démarrage) : un petit saut, l'antenne qui salue.
        if (_campPhaseConnue && phase == Campagnes.Phase.Attente && _campPhaseVue != Campagnes.Phase.Attente)
        {
            _tSaut = Maintenant;
            _salueJusque = Maintenant + 1400;
        }
        _campPhaseVue = phase;
        _campPhaseConnue = true;
        if (CampagneOccupe && _jeuEnCours != Jeu.Aucun) Arreter("");

        if (!_campPret && (Maintenant > _campPretAuPlusTard || !DansUnGroupe || _essaiCamp is not null || _demo)) _campPret = true;
        var ouverte = _fenetreAventure is { IsVisible: true } f && f.WindowState != WindowState.Minimized;
        var ctx = new Aventure.Contexte(ouverte, Amis.Calme(DateTime.Now.Hour, _reglages.CalmeDebut, _reglages.CalmeFin) && !_demo,
            _discret || Maintenant < _cacheJusque, EnExpedition || _visites.Sortie is not null, _campPret && (Maintenant > 6000 || _essaiCamp is not null),
            _reglages.AnnonceAventure == "signe");
        _retour = Aventure.Evaluer(CarnetCamp, e, _essaiCamp is not null ? _essaiAnnoncee : _reglages.CampagneAnnoncee, ctx);
        switch (_retour.Geste)
        {
            case Aventure.Geste.Annoncer:
                NoterAnnonce(_retour.Cle);
                AnnoncerRetour(_retour);
                break;
            case Aventure.Geste.Taire:
                NoterAnnonce(_retour.Cle);
                break;
        }
        MettreInfobulle(_retour.Signe ? "Pilou t'attend pour son aventure !" : MenuNotification.Infobulle);
    });

    private void NoterAnnonce(string cle)
    {
        if (_essaiCamp is not null)
        {
            _essaiAnnoncee = cle; // démonstration : en mémoire seulement
            return;
        }
        if (cle == "" || cle == _reglages.CampagneAnnoncee) return;
        _reglages.CampagneAnnoncee = cle;
        if (_essaiCamp is null && !_demo) _reglages.Ecrire(_dossier);
    }

    // UNE annonce : un petit saut, l'antenne qui s'agite, une bulle qui dit qu'il est là et où (sans rien dévoiler).
    private void AnnoncerRetour(Aventure.Retour r)
    {
        Sons.Jouer(Son.Campagne);
        _tSaut = Maintenant;
        _salueJusque = Maintenant + 2200;
        Dire(r.Lieu == "" ? $"✉ {r.Texte}" : $"✉ {r.Texte} · ▸ {r.Lieu}", 9000);
        _messageTag = "aventure";
        Bulle(_vivantes, Epoque);
        if (_essaiCamp is null && !_demo) PublierSortie("✉ Pilou est revenu de son aventure", r.Lieu == "" ? "il t'attend" : $"{r.Lieu} · il t'attend");
    }

    // ---- Bulle : la ligne d'attente, sous les statuts des sessions (prioritaires)

    private void LignesCampagne() => Prudemment(() =>
    {
        if (!CampagneOccupe || _campEtat is not { } e) return;
        if (_reglages.Bulle == ModeBulle.Masquee && !_survol) return;
        var c = Couleurs;
        var tb = new TextBlock
        {
            FontFamily = new FontFamily("Segoe UI"), FontSize = 11.5, Foreground = c.Pale, Margin = new Thickness(0, 2, 0, 1),
            TextTrimming = TextTrimming.CharacterEllipsis, Tag = "aventure", Cursor = System.Windows.Input.Cursors.Hand,
        };
        tb.Inlines.Add(new Run("⚑ ") { Foreground = c.Orange, FontFamily = new FontFamily("Segoe UI Symbol") });
        tb.Inlines.Add(new Run(Aventure.LigneBulle(e)[2..]));
        _lignes.Children.Add(tb);
        // Au survol : le chapitre et le lieu.
        if (_survol)
        {
            var d = Aventure.DetailBulle(e).Replace("\n", "  ·  ");
            _lignes.Children.Add(new TextBlock
            {
                Text = "   " + d, FontFamily = new FontFamily("Segoe UI"), FontSize = 10.5, Foreground = c.Pale, Opacity = 0.85,
                Margin = new Thickness(0, 0, 0, 1), TextTrimming = TextTrimming.CharacterEllipsis, Tag = "aventure",
            });
        }
    });

    // Un clic dans la bulle sur ce qui parle de l'aventure (la ligne d'attente, l'annonce) ouvre la fenêtre. La bulle
    // est recomposée souvent : on lit l'étiquette de l'élément sous la souris au moment du clic, pas une référence.
    private bool ClicAventure(object? source)
    {
        for (DependencyObject? d = source as DependencyObject; d is not null;
             d = d is FrameworkContentElement fce ? fce.Parent : d is FrameworkElement fe ? fe.Parent ?? VisualTreeHelper.GetParent(fe) : null)
        {
            if (ReferenceEquals(d, _bulle)) return false;
            if (d is FrameworkElement { Tag: "aventure" } || d is FrameworkContentElement { Tag: "aventure" })
            {
                OuvrirAventure();
                return true;
            }
            // L'annonce d'une évolution (FenetreNiveaux.AnnoncerScene) : « evolution:<stade> » ouvre sa scène.
            var etiquette = (d as FrameworkElement)?.Tag ?? (d as FrameworkContentElement)?.Tag;
            if (etiquette is string tag && tag.StartsWith("evolution:", StringComparison.Ordinal)
                && int.TryParse(tag[10..], System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out int stade))
            {
                _message = "";
                OuvrirSceneEvolution(stade);
                return true;
            }
        }
        return false;
    }

    // ---- Le signe « ! » près de Pilou, tant qu'il t'attend et que la fenêtre n'est pas ouverte

    private static readonly Brush OrangeSigne = Gel(0xff, 0xf6, 0x9d, 0x50), CremeSigne = Gel(0xff, 0xff, 0xf6, 0xe0), EncreSigne = Gel(0xff, 0x1c, 0x21, 0x28);

    // Une étiquette ronde, pointe vers Pilou, un « ! » crème dedans : la forme dit « il t'attend », pas seulement l'orange.
    private static readonly int[,] MotifSigne = Pixels.Motif(
        "0111110",
        "1112111",
        "1112111",
        "1112111",
        "1111111",
        "1112111",
        "0111110",
        "0001000");

    private void AnimerRetour(double t) => Prudemment(() =>
    {
        bool montrer = _retour.Signe && !EnExpedition && _visites.Sortie is null && _jeuEnCours == Jeu.Aucun;
        if (montrer && _badgeRetour is null)
        {
            _badgeRetour = new Pixels(MotifSigne, new Brush?[] { null, OrangeSigne, CremeSigne }, EncreSigne, Finesse.Net(2.4))
            {
                Cursor = System.Windows.Input.Cursors.Hand,
                ToolTip = "Pilou t'attend pour son aventure — clic pour lui répondre",
            };
            _badgeRetour.MouseLeftButtonUp += (_, ev) =>
            {
                ev.Handled = true;
                OuvrirAventure();
            };
            _jeu.Children.Add(_badgeRetour);
        }
        else if (!montrer && _badgeRetour is not null)
        {
            _jeu.Children.Remove(_badgeRetour);
            _badgeRetour = null;
        }
        if (_badgeRetour is null) return;
        // Il flotte doucement (immobile si les animations de Windows sont coupées).
        double dy = Bandeau.Anime ? Math.Round(Math.Sin(t / 520) * 2) : 0;
        Canvas.SetLeft(_badgeRetour, Placement.ACote(_aGauche, -CoteJeu, 22, _badgeRetour.Width));
        Canvas.SetTop(_badgeRetour, TeteY - 8 + dy);
    });

    private void MettreInfobulle(string texte)
    {
        if (texte == _infobulleMise) return;
        _infobulleMise = texte;
        _zoneNotif?.Infobulle(texte);
    }

    // ---- Menus : clic droit et icône près de l'horloge

    private string EtatAventureCourt() => Prudemment(() => Aventure.EtatCourt(CarnetCamp, _campEtat, (long)Epoque), "");

    // Texte de l'entrée « Aventure » du menu de l'icône (natif) : l'état en clair, et « ! » quand il t'attend.
    internal string TexteMenuIcone()
    {
        var etat = EtatAventureCourt();
        return etat == "" ? "Aventure…" : _retour.Signe ? "Aventure… (! il t'attend)" : $"Aventure… ({etat})";
    }

    // ---- La fenêtre

    internal void OuvrirAventure() => Prudemment(() =>
    {
        if (_fenetreAventure is { IsVisible: true } f)
        {
            if (f.WindowState == WindowState.Minimized) f.WindowState = WindowState.Normal;
            f.Rafraichir();
            f.Activate();
            return;
        }
        try
        {
            var w = new FenetreAventure(this);
            w.Closed += (_, _) =>
            {
                if (ReferenceEquals(_fenetreAventure, w)) _fenetreAventure = null;
                // Ce qu'il y avait à dire a été vu : rien à annoncer en refermant (même en plein milieu d'un message).
                NoterAnnonce(Aventure.CleRetour(CarnetCamp));
            };
            _fenetreAventure = w;
            if (_demo) PoserPresDePilou(w);
            w.Show();
            Sons.Jouer(Son.Aventure);
        }
        catch (InvalidOperationException)
        {
            // fenêtre principale en cours de fermeture
        }
    });

    // Pour la fenêtre.
    internal int NiveauAventure => Niveau;
    internal double EpoqueAventure => Epoque;
    internal Allure AllurePortrait(string humeur, double t, string tenue = "")
    {
        var a = Scene.Allure(_scene.Pose);
        var porte = EquipeCourant().Where(kv => PilouBureau.Boutique.SurPilou(kv.Key) && kv.Value != "").Select(kv => kv.Value).ToList();
        return new Allure
        {
            Expr = humeur is "" ? "repos" : humeur,
            T = t,
            Couleur = a.Couleur,
            Accessoire = a.Accessoire,
            Objets = porte,
            Stade = a.Stade,
            Tenue = tenue,
            Cligne = (int)(t / 3100) % 7 == 3 && t % 3100 < 140,
        };
    }

    // Fin d'une démonstration (visite guidée) : la partie en mémoire est oubliée, Pilou redevient libre.
    private void FinEssaiAventure()
    {
        if (_essaiCampRapide) return;
        _essaiCamp = null;
        _campEtat = null;
        _retour = Aventure.Aucun;
        _campVu = -1e12;
    }

    // Une décision prise dans la fenêtre : Pilou réagit tout de suite sur l'écran (il prend la route, ou il est content).
    internal void ApresDecision() => Prudemment(() =>
    {
        _campVu = -1e12;
        SuivreCampagne(Epoque);
        Bulle(_vivantes, Epoque);
    });
}
