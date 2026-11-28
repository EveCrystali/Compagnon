using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;

namespace PilouBureau;

// Petite fenêtre rétro des expéditions (même habit que la boutique) : bandeau niveau / XP / po / ⚡, les lieux
// (un clic : il part), l'équipement léger (un outil, un talisman), le dernier journal et la collection
// (trophées, éclats, butin exclusif). Chaque état a un signe de forme : ▣ fermé, ▶ possible, ◌ pas maintenant,
// ⚔ en route ; issue ★ victoire, ◐ à moitié, ✕ défaite.
internal sealed class FenetreExpeditions : Window
{
    private readonly FenetrePilou _pilou;
    private readonly Bandeau _bandeau = new(compact: true);
    private readonly StackPanel _lieux = new();
    private readonly StackPanel _droite = new() { Margin = new Thickness(14, 0, 0, 0) };
    private readonly TextePixel _etat = Texte(12, Bandeau.Argent);
    private readonly DispatcherTimer _horloge = new() { Interval = TimeSpan.FromSeconds(2) };
    private string _cle = "";

    private static readonly Brush Fond = Gel("#0f1324"), Case = Gel("#1f2540"), Ferme = Gel("#3b4654"), Creme = Gel("#f6f8fa"),
        Parchemin = Gel("#e8d5b0"), Encre = Gel("#1c2128"), Jaune = Gel("#f5d76e");

    private static Brush Gel(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    // Police pixel de Pilou (docs/STYLE.md) : les anciennes tailles du système deviennent « petit » (détails), « corps »
    // (à partir de 14) ou « grand » (à partir de 20, un signe seul) ; gras : la police « titre ».
    private static TextePixel Texte(double taille, Brush couleur, bool gras = false) =>
        StylePixel.Texte("", couleur, taille >= 20 ? StylePixel.Grand : StylePixel.Corps, gras);

    private static TextePixel Texte(string texte, double taille, Brush couleur, bool gras = false)
    {
        var t = Texte(taille, couleur, gras);
        t.Texte = texte;
        return t;
    }

    private static BoutonPixel Bouton(string texte, bool principal, Action action)
    {
        var b = new BoutonPixel(texte, principal, StylePixel.Corps) { VerticalAlignment = VerticalAlignment.Center };
        b.Click += (_, _) => action();
        return b;
    }

    private static UIElement Titre(string texte)
    {
        var t = StylePixel.Enseigne(texte, Bandeau.Violet, Bandeau.Encre, StylePixel.Petit);
        t.Margin = new Thickness(0, 10, 0, 6);
        return t;
    }

    public FenetreExpeditions(FenetrePilou pilou)
    {
        _pilou = pilou;
        Title = "Expéditions de Pilou";
        Width = 1100;
        Height = 760;
        MinWidth = 900;
        MinHeight = 600;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Background = Fond;
        UseLayoutRounding = true;

        var racine = new DockPanel { Margin = new Thickness(14, 10, 14, 10) };
        DockPanel.SetDock(_bandeau, Dock.Top);
        racine.Children.Add(_bandeau);
        var tete = new StackPanel { Margin = new Thickness(0, 8, 0, 6) };
        var enseigne = StylePixel.Enseigne("EXPÉDITIONS", Bandeau.OrangePo, Gel("#6a5acd"), 4);
        enseigne.HorizontalAlignment = HorizontalAlignment.Center;
        tete.Children.Add(enseigne);
        _etat.HorizontalAlignment = HorizontalAlignment.Center;
        _etat.Centre = true;
        _etat.Margin = new Thickness(0, 6, 0, 0);
        tete.Children.Add(_etat);
        DockPanel.SetDock(tete, Dock.Top);
        racine.Children.Add(tete);

        var corps = new Grid();
        corps.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        corps.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        var gauche = new ScrollViewer { Content = _lieux, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        corps.Children.Add(gauche);
        var droite = new ScrollViewer { Content = _droite, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        Grid.SetColumn(droite, 1);
        corps.Children.Add(droite);
        racine.Children.Add(corps);
        Content = racine;
        StylePixel.Defileur(this);

        _horloge.Tick += (_, _) => Rafraichir();
        Loaded += (_, _) =>
        {
            Rafraichir();
            _horloge.Start();
        };
        Closed += (_, _) => _horloge.Stop();
        KeyDown += (_, e) =>
        {
            if (e.Key == Key.Escape) Close();
        };
    }

    // Recompose la fenêtre quand quelque chose a changé (énergie, compte à rebours à la minute, équipement…).
    public void Rafraichir()
    {
        var e = _pilou.EtatExpeditions;
        double t = _pilou.EpoqueExpedition;
        var autres = _pilou.ExpeditionsDuGroupe;
        int energie = Jauge.Affiche(e.Energie), niveau = _pilou.NiveauExpedition;
        var cle = $"{energie}|{niveau}|{e.Courante?.Id}|{e.Dernier?.Id}|{e.Arme}|{e.Talisman}|{e.Fragments}|{e.Trophees.Count}|{(long)(t / 60_000)}"
                  + $"|{_pilou.ObjetsPossedes.Count}|{_pilou.OccupationExpedition}|{Expeditions.Restantes(e, DateTime.Now, autres)}";
        _bandeau.Mettre(niveau, _pilou.XpTotal, _pilou.SoldeExpedition, _pilou.TitreAffiche(niveau));
        if (cle == _cle) return;
        _cle = cle;
        int reste = Expeditions.Restantes(e, DateTime.Now, autres);
        double libre = Expeditions.LibreA(e, autres);
        _etat.Texte = e.Courante is { } x
            ? $"⚔ En route vers {Expeditions.De(Expeditions.Trouver(x.Lieu)?.Nom ?? "l'aventure")} · retour vers {Amis.Heure(DateTime.Now.AddMilliseconds(x.Fin - t))}"
            : reste <= 0 ? $"⚡ {energie}/100 · trois expéditions aujourd'hui : Pilou repart demain"
            : t < libre ? $"⚡ {energie}/100 · Pilou se repose encore {Statut.Duree(libre - t)} · {reste} expédition{(reste > 1 ? "s" : "")} possible{(reste > 1 ? "s" : "")} aujourd'hui"
            : $"⚡ {energie}/100 · {reste} expédition{(reste > 1 ? "s" : "")} possible{(reste > 1 ? "s" : "")} aujourd'hui · Pilou part seul, revient seul";
        RemplirLieux(e, t, autres, niveau);
        RemplirDroite(e);
    }

    private void RemplirLieux(EtatExpedition e, double t, ExpeditionsAutres autres, int niveau)
    {
        _lieux.Children.Clear();
        _lieux.Children.Add(Titre("OÙ PARTIR ?"));
        if (e.Courante is { } x)
        {
            var carte = Carte(Bandeau.OrangePo);
            var pile = new StackPanel();
            pile.Children.Add(Texte($"⚔ {Expeditions.Trouver(x.Lieu)?.Nom}", 15, Bandeau.ArgentClair, true));
            pile.Children.Add(Texte($"Parti à {Amis.Heure(DateTimeOffset.FromUnixTimeMilliseconds((long)x.Debut).LocalDateTime)}, retour vers "
                                    + $"{Amis.Heure(DateTime.Now.AddMilliseconds(x.Fin - t))}. Il se débrouille : rien à faire.", 12, Bandeau.Argent));
            var rappel = Bouton("↩ Rappeler (il rentre les mains vides)", false, () =>
            {
                _pilou.RappelerExpedition();
                Rafraichir();
            });
            rappel.HorizontalAlignment = HorizontalAlignment.Left;
            rappel.Margin = new Thickness(0, 8, 0, 0);
            pile.Children.Add(rappel);
            carte.Child = pile;
            _lieux.Children.Add(carte);
        }
        foreach (var l in Expeditions.Lieux)
        {
            bool ferme = niveau < l.Niveau;
            var refus = Expeditions.Refus(e, l, niveau, t, DateTime.Now, autres, _pilou.OccupationExpedition);
            var carte = Carte(ferme ? Ferme : refus is null ? Bandeau.BleuXp : Bandeau.Bord);
            var g = new Grid();
            g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            var bete = Apercu.Sprite("crea-" + l.Boss, 0, ferme);
            UIElement icone = bete is not null ? Apercu.Vue(bete, Math.Min(2.5, 40.0 / Math.Max(bete.PixelWidth, bete.PixelHeight)))
                : Texte(l.Signe, 26, Bandeau.Argent, true);
            if (icone is FrameworkElement fe)
            {
                fe.Margin = new Thickness(0, 0, 10, 0);
                fe.VerticalAlignment = VerticalAlignment.Center;
                fe.Width = Math.Max(fe.Width, 44);
            }
            g.Children.Add(icone);
            var pile = new StackPanel();
            pile.Children.Add(Texte($"{l.Signe}  {l.Nom}", 14.5, ferme ? Bandeau.Argent : Bandeau.ArgentClair, true));
            pile.Children.Add(Texte(ferme ? $"▣ s'ouvre au niveau {l.Niveau}" : l.Accroche, 11.5, Bandeau.Argent));
            pile.Children.Add(Texte($"⚡ {l.Cout}  ·  {Expeditions.Duree(l.Minutes)}  ·  risque {Expeditions.Risque(l)}  ·  boss : {Expeditions.Bete(l.Boss).Nom}",
                11.5, ferme ? Bandeau.Argent : Jaune));
            if (!ferme && Expeditions.AideAuDepart(l, niveau) is { Length: > 0 } aide) pile.Children.Add(Texte("↑ " + aide, 11.5, Bandeau.BleuXp));
            if (!ferme && refus is not null && e.Courante is null) pile.Children.Add(Texte("◌ " + refus, 11.5, Bandeau.Violet));
            Grid.SetColumn(pile, 1);
            g.Children.Add(pile);
            if (!ferme && e.Courante is null)
            {
                var partir = Bouton("▶ Partir", refus is null, () =>
                {
                    _pilou.PartirExpedition(l.Id);
                    Rafraichir();
                });
                partir.IsEnabled = refus is null;
                partir.ToolTip = refus ?? $"Pilou part {Expeditions.Duree(l.Minutes)} ; ⚡ −{l.Cout}";
                Grid.SetColumn(partir, 2);
                g.Children.Add(partir);
            }
            carte.Child = g;
            _lieux.Children.Add(carte);
        }
        _lieux.Children.Add(Texte("⚡ L'énergie remonte toute seule jusqu'à 50 (≈ +5/h), surtout en travaillant : +1 toutes les 6 min "
                                  + "dans une appli de travail, quand une IA finit, à chaque quête (40 par jour au plus) ; et en mangeant : plats "
                                  + "cuisinés, en-cas de route de la boutique (40 par jour au plus). Pilou boudeur : deux fois moins vite.",
            11, Bandeau.Argent));
    }

    private static Border Carte(Brush bord) => new()
    {
        Background = Case, BorderBrush = bord, BorderThickness = new Thickness(2), Padding = new Thickness(10, 8, 10, 8),
        Margin = new Thickness(0, 0, 0, 8),
    };

    private void RemplirDroite(EtatExpedition e)
    {
        _droite.Children.Clear();
        var possedes = _pilou.ObjetsPossedes;
        _droite.Children.Add(Titre("ÉQUIPEMENT"));
        _droite.Children.Add(Choix("arme", "Arme ou outil", e.Arme == "" ? Expeditions.EpeeBois : e.Arme, possedes));
        _droite.Children.Add(Choix("talisman", "Talisman", e.Talisman, possedes));

        _droite.Children.Add(Titre("JOURNAL"));
        if (e.Dernier is { } d)
        {
            var feuille = new Border
            {
                Background = Parchemin, BorderBrush = Gel("#8a6e4b"), BorderThickness = new Thickness(3), Padding = new Thickness(12, 8, 12, 10),
            };
            var pile = new StackPanel();
            pile.Children.Add(Texte($"{Expeditions.SigneIssue(d.Issue)} {Expeditions.Trouver(d.Lieu)?.Nom} · {Expeditions.NomIssue(d.Issue)}"
                                    + $" · {Amis.Heure(DateTimeOffset.FromUnixTimeMilliseconds((long)d.Fin).LocalDateTime)}", 13.5, Encre, true));
            foreach (var ligne in d.Journal)
            {
                var l = Texte(ligne, 12, Encre);
                l.Margin = new Thickness(0, 3, 0, 0);
                pile.Children.Add(l);
            }
            var gains = new List<string>();
            if (d.Po > 0) gains.Add($"+{d.Po} po");
            if (d.Xp > 0) gains.Add($"+{d.Xp} xp");
            if (d.Fragments > 0) gains.Add($"◆ {d.Fragments} éclat{(d.Fragments > 1 ? "s" : "")}");
            if (d.Objet != "") gains.Add("✦ " + Expeditions.NomCourt(d.Objet));
            if (d.Trophee != "") gains.Add("★ trophée");
            if (gains.Count > 0) pile.Children.Add(Texte(string.Join("   ", gains), 12.5, Gel("#7a4210"), true));
            feuille.Child = pile;
            _droite.Children.Add(feuille);
        }
        else _droite.Children.Add(Texte("Pas encore d'expédition : choisis un lieu à gauche, Pilou s'occupe du reste.", 12, Bandeau.Argent));

        _droite.Children.Add(Titre("COLLECTION"));
        var vitrine = new WrapPanel();
        foreach (var l in Expeditions.Lieux)
        {
            var id = Expeditions.Trophee(l.Boss);
            bool a = e.Trophees.Contains(id);
            vitrine.Children.Add(Vignette(id, !a, a ? $"Trophée : {Expeditions.Bete(l.Boss).Nom} ({l.Nom})" : $"Trophée à gagner : battre le boss de {Expeditions.De(l.Nom)}"));
        }
        foreach (var x in Expeditions.Exclusifs)
        {
            bool a = possedes.Contains(x.Id);
            vitrine.Children.Add(Vignette(x.Id, !a, a ? $"{Expeditions.NomCourt(x.Id)} : à toi (introuvable en boutique)" : "Butin exclusif encore inconnu"));
        }
        _droite.Children.Add(vitrine);
        _droite.Children.Add(Texte($"◆ Éclats de cristal : {e.Fragments}/{Expeditions.Forge} (à {Expeditions.Forge}, Pilou forge un butin exclusif)"
                                   + $"   ·   {e.Total} expédition{(e.Total > 1 ? "s" : "")}, {e.Victoires} victoire{(e.Victoires > 1 ? "s" : "")}",
            11.5, Bandeau.Argent));
    }

    private static UIElement Vignette(string id, bool silhouette, string info)
    {
        var im = Apercu.Sprite(id, 0, silhouette);
        UIElement contenu = im is null ? Texte(silhouette ? "?" : "★", 20, Bandeau.Argent, true)
            : Apercu.Vue(im, Math.Min(3, 36.0 / Math.Max(im.PixelWidth, im.PixelHeight)));
        return new Border
        {
            Width = 52, Height = 52, Margin = new Thickness(0, 0, 6, 6), Background = Bandeau.Nuit2,
            BorderBrush = silhouette ? Ferme : Bandeau.OrangePo, BorderThickness = new Thickness(2), ToolTip = info,
            Child = new Viewbox { Child = contenu, Stretch = Stretch.Uniform, Margin = new Thickness(4) },
        };
    }

    // ◀ objet ▶ : on fait défiler les objets possédés de cet emplacement (un clic par objet).
    private UIElement Choix(string emplacement, string titre, string actuel, IReadOnlyCollection<string> possedes)
    {
        var liste = Expeditions.Disponibles(emplacement, possedes).Select(o => o.Id).ToList();
        if (emplacement == "talisman") liste.Insert(0, "");
        int i = Math.Max(0, liste.IndexOf(actuel));
        var o = Expeditions.OutilDe(liste[i]);
        var g = new Grid { Margin = new Thickness(0, 0, 0, 8) };
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(110) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
        g.Children.Add(Texte(titre, 12, Bandeau.Argent, true));
        var avant = Bouton("◀", false, () => Changer(emplacement, liste, i - 1));
        avant.MinWidth = 30;
        Grid.SetColumn(avant, 1);
        g.Children.Add(avant);
        var pile = new StackPanel { Margin = new Thickness(8, 0, 8, 0) };
        pile.Children.Add(Texte(o?.Nom ?? "aucun talisman", 13, Bandeau.ArgentClair, true));
        pile.Children.Add(Texte(o is null ? "rien de plus" : Expeditions.Effet(o), 11, Bandeau.BleuXp));
        Grid.SetColumn(pile, 2);
        g.Children.Add(pile);
        var apres = Bouton("▶", false, () => Changer(emplacement, liste, i + 1));
        apres.MinWidth = 30;
        Grid.SetColumn(apres, 3);
        g.Children.Add(apres);
        avant.IsEnabled = apres.IsEnabled = liste.Count > 1;
        if (liste.Count <= 1)
            g.ToolTip = emplacement == "arme" ? "D'autres outils (épée en mousse, lanterne, baguette…) s'achètent en boutique"
                : "Talismans : médaille, auréole, collier de perles… (boutique), ou trouvés en expédition";
        return g;
    }

    private void Changer(string emplacement, List<string> liste, int i)
    {
        if (liste.Count == 0) return;
        _pilou.ChoisirOutil(emplacement, liste[((i % liste.Count) + liste.Count) % liste.Count]);
        _cle = "";
        Rafraichir();
    }
}
