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
        var (po, xp) = Quetes.Appliquer(_profil, gains);
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
        _xpTotal = TotalXp();
        FlotterPo($"+{po} po");
        if (xp > 0) Flotter($"+{xp} xp", 1, new Point(TeteX - 18, TeteY - 30));
        var coffre = gains.FirstOrDefault(g => g.Coffre);
        var quete = gains.FirstOrDefault(g => !g.Coffre);
        Dire(coffre is not null ? $"✦ {coffre.Texte} !" : $"✦ quête réussie : {quete?.Texte}", 4200);
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

    private void OuvrirBoutique() => new FenetreBoutique(this).ShowDialog();

    // Pour la fenêtre de la boutique.
    internal (int Solde, List<string> Inventaire, Dictionary<string, Port> Equipe) EtatBourse() => Bourse();

    internal int NiveauActuel => Niveau;

    internal string? Acheter(string id)
    {
        var (solde, inventaire, _) = Bourse();
        if (inventaire.Contains(id)) return "déjà dans l'inventaire";
        var refus = PilouBureau.Boutique.Acheter(_profil.Bourse, id, Niveau, solde, DateOnly.FromDateTime(DateTime.Now));
        if (refus is not null) return refus;
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
        Dire($"nouveau : {PilouBureau.Boutique.Trouver(id)?.Nom} !", 3000);
        return null;
    }

    internal void Equiper(string slot, string id)
    {
        // Un objet acheté sur un autre appareil du groupe est aussi à nous.
        if (id != "" && !_profil.Bourse.Inventaire.Contains(id) && Bourse().Inventaire.Contains(id)) _profil.Bourse.Inventaire.Add(id);
        if (!PilouBureau.Boutique.Equiper(_profil.Bourse, slot, id, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds())) return;
        _profil.Ecrire(DossierPartage);
        _bourseCache = null;
    }
}

// Boutique (gratuite) : solde, offres du jour, catalogue par emplacement ; acheter, équiper, retirer.
internal sealed class FenetreBoutique : Window
{
    private readonly FenetrePilou _pilou;
    private readonly StackPanel _corps = new() { Margin = new Thickness(16) };
    private readonly TextBlock _solde = new() { FontSize = 18, FontWeight = FontWeights.Bold };
    private readonly TextBlock _message = new() { FontSize = 12, Margin = new Thickness(0, 4, 0, 8), Foreground = Brushes.Gray };

    private static readonly Brush Bleu = Geler("#2f7ed8"), Orange = Geler("#c86a1c"), Argent = Geler("#768390");

    private static Brush Geler(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    public FenetreBoutique(FenetrePilou pilou)
    {
        _pilou = pilou;
        Title = "Boutique de Pilou";
        Width = 560;
        Height = 640;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Content = new ScrollViewer { Content = _corps, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        Remplir();
    }

    private void Remplir()
    {
        var (solde, inventaire, equipe) = _pilou.EtatBourse();
        var jour = DateOnly.FromDateTime(DateTime.Now);
        int niveau = _pilou.NiveauActuel;
        _corps.Children.Clear();
        _solde.Text = $"◉ {solde} po";
        _corps.Children.Add(_solde);
        _corps.Children.Add(new TextBlock
        {
            Text = "Les pièces d'or se gagnent en quêtes (clic droit → Quêtes). Tout est gratuit : aucune vraie monnaie.",
            TextWrapping = TextWrapping.Wrap,
            FontSize = 12,
            Foreground = Brushes.Gray,
        });
        _corps.Children.Add(_message);

        Section("◆ Offres du jour");
        foreach (var a in PilouBureau.Boutique.OffresDuJour(jour)) Ligne(a, solde, inventaire, equipe, jour, niveau);
        foreach (var slot in PilouBureau.Boutique.Slots)
        {
            var articles = PilouBureau.Boutique.Catalogue.Where(a => a.Slot == slot).ToList();
            Section($"{PilouBureau.Boutique.Signe(slot)} {PilouBureau.Boutique.NomSlot(slot)}");
            foreach (var a in articles) Ligne(a, solde, inventaire, equipe, jour, niveau);
        }
    }

    private void Section(string titre) =>
        _corps.Children.Add(new TextBlock { Text = titre, FontSize = 14, FontWeight = FontWeights.Bold, Margin = new Thickness(0, 14, 0, 4) });

    private void Ligne(Article a, int solde, List<string> inventaire, Dictionary<string, Port> equipe, DateOnly jour, int niveau)
    {
        bool possede = inventaire.Contains(a.Id);
        bool porte = equipe.TryGetValue(a.Slot, out var p) && p.Id == a.Id;
        bool enVente = PilouBureau.Boutique.EnVente(a, jour);
        int prix = PilouBureau.Boutique.Prix(a, jour);
        var rangee = new DockPanel { Margin = new Thickness(0, 2, 0, 2) };
        var bouton = new Button { MinWidth = 110, Padding = new Thickness(8, 3, 8, 3), Margin = new Thickness(8, 0, 0, 0) };
        DockPanel.SetDock(bouton, Dock.Right);
        if (possede)
        {
            bouton.Content = porte ? "Retirer" : "Porter";
            bouton.Click += (_, _) =>
            {
                _pilou.Equiper(a.Slot, porte ? "" : a.Id);
                Remplir();
            };
        }
        else
        {
            bouton.Content = !enVente ? "pas aujourd'hui" : niveau < a.NiveauMin ? $"niveau {a.NiveauMin}" : $"Acheter · {prix} po";
            bouton.IsEnabled = enVente && niveau >= a.NiveauMin && solde >= prix;
            bouton.Click += (_, _) =>
            {
                var refus = _pilou.Acheter(a.Id);
                Remplir();
                _message.Text = refus is null ? $"✓ {a.Nom} est à toi." : $"✕ {refus}";
            };
        }
        rangee.Children.Add(bouton);
        var texte = new TextBlock { VerticalAlignment = VerticalAlignment.Center, TextWrapping = TextWrapping.Wrap };
        texte.Inlines.Add(new System.Windows.Documents.Run($"{Butin.Signe(a.Rarete)} {a.Nom}")
        {
            FontWeight = porte ? FontWeights.Bold : FontWeights.Normal,
            Foreground = a.Rarete >= Rarete.Epique ? Orange : a.Rarete == Rarete.Rare ? Bleu : Brushes.Black,
        });
        var detail = possede ? (porte ? "  · porté" : "  · à toi")
            : prix < a.Prix ? $"  · promo -25 % ({a.Prix} po)" : "";
        texte.Inlines.Add(new System.Windows.Documents.Run(detail) { Foreground = Argent, FontSize = 11 });
        rangee.Children.Add(texte);
        _corps.Children.Add(rangee);
    }
}
