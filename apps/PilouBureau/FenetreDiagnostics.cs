using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Media;

namespace PilouBureau;

// Erreurs du fichier ouvert dans l'éditeur (Diagnostics.cs) : une ligne courte dans la bulle, une petite grimace
// quand elles augmentent, un petit saut et « ✓ propre ! » quand on repasse à zéro. Sinon, rien.
public sealed partial class FenetrePilou
{
    private readonly SuiviDiagnostics _diagnostics = new();
    private AnnonceDiagnostics? _diagAnnonce;
    private double _diagJusque = -1e9, _grimaceDiagJusque = -1e9;
    private volatile bool _diagActifs = true;

    private Connecteur? ConnecteurDiagnostics => _registre?.Trouver(ConnecteurEditeurs.Cle);

    // Depuis l'API locale (n'importe quel fil) : faux si le connecteur est coupé (rien n'est gardé).
    private bool RecevoirDiagnostics(RapportDiagnostics r)
    {
        if (!_diagActifs) return false;
        _diagnostics.Recevoir(r);
        return true;
    }

    // À chaque lecture (300 ms) : réglages, puis annonce éventuelle.
    private void VivreDiagnostics()
    {
        if (_registre is null || ConnecteurDiagnostics is not { } c) return;
        _diagActifs = _registre.Actif(c);
        if (!_diagActifs)
        {
            _diagAnnonce = null;
            return;
        }
        var ctx = _registre.Contexte(c);
        _diagnostics.AvecNom = ctx.Lire("nom") != "non";
        _diagnostics.AvecMessage = ctx.Lire("message") == "oui";
        if (_diagnostics.Battre(Epoque, EnSaisie) is not { } a) return;
        _diagAnnonce = a;
        _diagJusque = Maintenant + (a.Ton == TonDiagnostics.Erreurs ? 5000 : 3500);
        switch (a.Reaction)
        {
            case ReactionDiagnostics.Grimace:
                _grimaceDiagJusque = Maintenant + 1100;
                break;
            case ReactionDiagnostics.Saut:
                _tSaut = Maintenant;
                Signaler("propre", 1);
                break;
        }
        Dosage.Noter(Maintenant); // pas de réaction cosmétique juste après
        _registre.Noter(c.Id, a.Ligne);
    }

    // Petite grimace (sur Pilou au repos seulement) quand les erreurs augmentent.
    private Expr ExprDiagnostics(Expr montre, double t) =>
        t < _grimaceDiagJusque && montre == Expr.Repos ? Expr.Grimace : montre;

    // La ligne de la bulle : signe (forme) + couleur, orange pour les erreurs, bleu sinon. Au survol, l'état courant.
    private UIElement? BlocDiagnostics()
    {
        var c = Couleurs;
        if (_diagAnnonce is { } a && Maintenant < _diagJusque)
        {
            var teinte = a.Ton == TonDiagnostics.Erreurs ? c.Orange : c.Bleu;
            var tb = new TextBlock
            {
                FontFamily = new FontFamily("Segoe UI"),
                FontSize = 12.5,
                Foreground = c.Texte,
                TextTrimming = TextTrimming.CharacterEllipsis,
                MaxWidth = 300,
                Margin = new Thickness(0, 1, 0, 1),
            };
            tb.Inlines.Add(new Run(a.Signe) { Foreground = teinte, FontWeight = FontWeights.Bold, FontFamily = new FontFamily("Segoe UI Symbol") });
            tb.Inlines.Add(new Run(" "));
            tb.Inlines.Add(new Run(a.Texte) { Foreground = teinte, FontWeight = FontWeights.SemiBold });
            return tb;
        }
        if (_survol && _diagActifs && _diagnostics.Resume(Epoque) is { } resume) return Discret(resume);
        return null;
    }
}
