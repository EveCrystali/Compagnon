using System.Text;

namespace PilouBureau;

// Notifications Windows dans la bulle de Pilou (docs/NOTIFICATIONS.md). Désactivé par défaut.
//
// CONFIDENTIALITÉ : le contenu d'une notification (appli, titre, texte) reste en mémoire le temps de
// l'afficher, puis il est oublié. Il n'est jamais écrit sur disque, jamais journalisé, jamais envoyé au
// téléphone, au groupe d'appareils, aux amis, au webhook ni à l'API locale. Seuls les NOMS des applis que
// tu coches dans les réglages (filtre « sauf… » / « seulement… ») sont gardés dans reglages.json.

public enum ModeApps { Toutes, Sauf, Seulement }

// Une notification lue chez Windows (ou fabriquée par --essai=notif).
public sealed record NotifRecue(string App, string Titre, string Texte, uint Id = 0);

// Ce que la bulle affiche.
public sealed record NotifAffichee(string App, string Titre, string Texte, bool Masquee, int Nombre = 1)
{
    // Initiale de l'appli, dans un petit carré (pas de logo : rien d'une marque n'est dessiné).
    public string Initiale => App.Trim() is { Length: > 0 } a ? char.ToUpperInvariant(a[0]).ToString() : "?";
}

public sealed record ReglagesNotifs(bool Actif, ModeApps Mode, IReadOnlyCollection<string> Apps, bool Masquer);

public static class FiltreNotifs
{
    public const int LongueurMax = 90;

    public static bool Admise(string app, ModeApps mode, IReadOnlyCollection<string> apps)
    {
        bool cochee = apps.Any(a => string.Equals(a.Trim(), app.Trim(), StringComparison.OrdinalIgnoreCase));
        return mode switch
        {
            ModeApps.Sauf => !cochee,
            ModeApps.Seulement => cochee,
            _ => true,
        };
    }

    // Une ligne propre : sans retour à la ligne ni caractère de contrôle, coupée avec « … ».
    public static string Ligne(string? texte, int max = LongueurMax)
    {
        if (string.IsNullOrWhiteSpace(texte)) return "";
        var sb = new StringBuilder();
        foreach (var c in texte)
        {
            if (char.IsControl(c) || (char.IsSeparator(c) && c != (char)32) || c == (char)0x2028 || c == (char)0x2029) sb.Append((char)32);
            else sb.Append(c);
        }
        var l = string.Join(' ', sb.ToString().Split(' ', StringSplitOptions.RemoveEmptyEntries));
        return l.Length <= max ? l : l[..(max - 1)].TrimEnd() + "…";
    }

    // Que montrer de cette notification ? null : rien (option coupée, heures calmes, Pilou caché pour ne pas
    // gêner, appli filtrée, notification vide). Masquée : seulement « 1 message de X ».
    public static NotifAffichee? Preparer(NotifRecue n, ReglagesNotifs r, bool calme, bool discret)
    {
        if (!r.Actif || calme || discret) return null;
        var app = Ligne(n.App, 40);
        if (app == "") app = "une appli";
        if (!Admise(app, r.Mode, r.Apps)) return null;
        var titre = Ligne(n.Titre);
        var texte = Ligne(n.Texte);
        if (titre == "" && texte == "") return null;
        return r.Masquer ? new NotifAffichee(app, "", "", true) : new NotifAffichee(app, titre, texte, false);
    }

    // « 1 message de X », « 3 messages de X ».
    public static string Resume(NotifAffichee n) =>
        $"{n.Nombre} message{(n.Nombre > 1 ? "s" : "")} de {n.App}";
}

// File des notifications à montrer, une à la fois, quelques secondes chacune. En mode masqué, celles d'une
// même appli arrivées pendant qu'elle est affichée ou en attente se regroupent (« 3 messages de X »).
public sealed class FileNotifs
{
    public const double Duree = 8000;
    public const int Max = 5;

    private readonly List<NotifAffichee> _attente = new();
    private NotifAffichee? _courante;
    private double _depuis;

    public void Ajouter(NotifAffichee n, double t)
    {
        if (n.Masquee)
        {
            if (_courante is { Masquee: true } c && c.App == n.App && t - _depuis < Duree)
            {
                _courante = c with { Nombre = c.Nombre + 1 };
                _depuis = t; // on la laisse un peu plus longtemps
                return;
            }
            int i = _attente.FindIndex(a => a.Masquee && a.App == n.App);
            if (i >= 0)
            {
                _attente[i] = _attente[i] with { Nombre = _attente[i].Nombre + 1 };
                return;
            }
        }
        _attente.Add(n);
        // Une rafale de notifications ne fait pas une file sans fin : les plus anciennes en attente s'en vont.
        while (_attente.Count > Max) _attente.RemoveAt(0);
    }

    // La notification à montrer maintenant (null : aucune).
    public NotifAffichee? Courante(double t)
    {
        if (_courante is not null && t - _depuis >= Duree) _courante = null;
        if (_courante is null && _attente.Count > 0)
        {
            _courante = _attente[0];
            _attente.RemoveAt(0);
            _depuis = t;
        }
        return _courante;
    }

    // Depuis combien de temps la courante est affichée (pour l'enveloppe brandie au début).
    public double Age(double t) => _courante is null ? double.PositiveInfinity : t - _depuis;

    public int EnAttente => _attente.Count;

    // Clic sur la bulle, option coupée : tout est oublié.
    public void Vider()
    {
        _attente.Clear();
        _courante = null;
    }
}

// Une source de notifications (Windows, ou un essai). Toutes passent par FiltreNotifs avant d'être montrées.
public interface ISourceNotifications : IDisposable
{
    event Action<NotifRecue>? Recue;
    // Où en est la source, en clair, pour le menu (« active », « accès refusé dans Windows »…).
    string Etat { get; }
    bool Disponible { get; }
    Task DemarrerAsync();
}
