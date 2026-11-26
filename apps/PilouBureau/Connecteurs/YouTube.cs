using System.Globalization;
using System.Xml.Linq;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

public sealed record VideoYouTube(string Id, string Titre, string Chaine, DateTimeOffset Publiee);

// ------------------------------------------------------------------------------------------------------
// YouTube : nouvelle vidéo d'une chaîne suivie (flux RSS public, sans clé) ; live en cours si tu donnes une clé
// d'API (quota limité : relevé des lives toutes les heures, 3 chaînes au plus).
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurYouTube : Connecteur
{
    public override string Id => "youtube";
    public override string Nom => "YouTube";
    public override string Description =>
        "Nouvelle vidéo d'une chaîne suivie (sans compte ni clé). Avec une clé d'API, Pilou signale aussi les lives.";
    public override string Signe => "▷";
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(10);

    public override string Aide =>
        "1. Identifiant de chaîne : sur la page de la chaîne → À propos → Partager la chaîne → Copier l'ID (commence par UC…).\n" +
        "2. Écris les identifiants ci-dessous, séparés par des virgules. Les nouvelles vidéos marchent déjà.\n" +
        "3. Facultatif, pour les lives : console.cloud.google.com → nouveau projet → API « YouTube Data API v3 » → Activer → " +
        "Identifiants → Créer une clé d'API (restreins-la à cette API) → colle-la. Une recherche de live coûte 100 unités sur " +
        "10 000 par jour : Pilou ne regarde les lives que toutes les heures, pour 3 chaînes au plus.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("chaines", "Chaînes suivies (ID UC…)", TypeReglage.Texte),
        new ReglageConnecteur("cle", "Clé d'API (lives, facultatif)", TypeReglage.Secret),
        new ReglageConnecteur("vus", "", TypeReglage.Texte, Visible: false),
    };

    public override string? Manque(ContexteConnecteur ctx) => Liste(ctx.Lire("chaines")).Count == 0 ? "écris au moins un ID de chaîne" : null;

    private DateTime _lives = DateTime.MinValue;
    private readonly HashSet<string> _enLive = new();
    private bool _livesVus;

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        var chaines = Liste(ctx.Lire("chaines")).Take(15).ToList();
        var vus = Liste(ctx.Lire("vus")).ToHashSet();
        bool premier = vus.Count == 0;
        foreach (var ch in chaines)
        {
            string xml;
            try
            {
                xml = await ctx.Http.GetStringAsync("https://www.youtube.com/feeds/videos.xml?channel_id=" + Uri.EscapeDataString(ch), ct);
            }
            catch (System.Net.Http.HttpRequestException)
            {
                ctx.Journal($"chaîne {ch} introuvable");
                continue;
            }
            foreach (var v in LireFlux(xml).Take(5))
            {
                if (!vus.Add(v.Id) || premier) continue;
                if (ctx.Maintenant - v.Publiee.LocalDateTime > TimeSpan.FromDays(2)) continue;
                ctx.Emettre(new EvenementPilou(Id, "notification", $"▷ Nouvelle vidéo · {Court(v.Chaine, 32)}", Court(v.Titre, 100)));
            }
        }
        ctx.Ecrire("vus", vus.Count == 0 ? "debut" : string.Join(",", vus.TakeLast(200)));

        var cle = ctx.Lire("cle");
        if (cle == "" || ctx.Maintenant - _lives < TimeSpan.FromHours(1)) return;
        _lives = ctx.Maintenant;
        foreach (var ch in chaines.Take(3))
        {
            var url = "https://www.googleapis.com/youtube/v3/search?part=snippet&eventType=live&type=video&channelId=" +
                      Uri.EscapeDataString(ch) + "&key=" + Uri.EscapeDataString(cle);
            var json = await ctx.Http.GetStringAsync(url, ct);
            var live = Lire(json)?["items"] is System.Text.Json.Nodes.JsonArray a ? a.FirstOrDefault() : null;
            if (live is null)
            {
                _enLive.Remove(ch);
                continue;
            }
            if (_enLive.Add(ch) && _livesVus)
                ctx.Emettre(new EvenementPilou(Id, "notification", $"▷ {Court(S(live["snippet"], "channelTitle"), 32)} est en live",
                    Court(S(live["snippet"], "title"), 100)));
        }
        _livesVus = true;
    }

    private static readonly XNamespace Atom = "http://www.w3.org/2005/Atom", Yt = "http://www.youtube.com/xml/schemas/2015";

    public static List<VideoYouTube> LireFlux(string xml)
    {
        try
        {
            var doc = XDocument.Parse(xml);
            return doc.Root?.Elements(Atom + "entry").Select(e => new VideoYouTube(
                (string?)e.Element(Yt + "videoId") ?? "",
                (string?)e.Element(Atom + "title") ?? "",
                (string?)e.Element(Atom + "author")?.Element(Atom + "name") ?? "",
                DateTimeOffset.TryParse((string?)e.Element(Atom + "published"), CultureInfo.InvariantCulture, DateTimeStyles.None, out var d) ? d : DateTimeOffset.MinValue))
                .Where(v => v.Id != "").ToList() ?? new List<VideoYouTube>();
        }
        catch (System.Xml.XmlException)
        {
            return new List<VideoYouTube>();
        }
    }
}
