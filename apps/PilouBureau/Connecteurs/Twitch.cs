using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json.Nodes;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

public sealed record LiveTwitch(string Login, string Nom, string Titre, string Jeu);

// ------------------------------------------------------------------------------------------------------
// Twitch : « X est en live ». Jeton d'application (Client ID + secret) ; chaînes saisies à la main.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurTwitch : Connecteur
{
    public override string Id => "twitch";
    public override string Nom => "Twitch";
    public override string Description => "Une chaîne que tu suis passe en live : Pilou te le dit. Aucun compte Twitch connecté.";
    public override string Signe => "▶";
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(3);

    public override string Aide =>
        "1. dev.twitch.tv/console → Register Your Application (nom : Pilou ; OAuth Redirect URL : http://localhost ; catégorie : Application Integration).\n" +
        "2. Ouvre l'app → copie le Client ID, puis « New Secret » → copie le secret.\n" +
        "3. Écris les chaînes à suivre (leur nom dans l'adresse twitch.tv/<nom>), séparées par des virgules.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("client", "Client ID", TypeReglage.Texte),
        new ReglageConnecteur("secret", "Client secret", TypeReglage.Secret),
        new ReglageConnecteur("chaines", "Chaînes suivies", TypeReglage.Texte, "noms séparés par des virgules (100 au plus)"),
    };

    public override string? Manque(ContexteConnecteur ctx) =>
        ctx.Lire("client") == "" || ctx.Lire("secret") == "" ? "Client ID et secret de ton app Twitch"
        : Liste(ctx.Lire("chaines")).Count == 0 ? "écris au moins une chaîne" : null;

    private string _jeton = "";
    private DateTime _expire = DateTime.MinValue;
    private HashSet<string>? _enLive;

    private async Task Jeton(ContexteConnecteur ctx, CancellationToken ct)
    {
        using var r = await ctx.Http.PostAsync("https://id.twitch.tv/oauth2/token", new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["client_id"] = ctx.Lire("client"), ["client_secret"] = ctx.Lire("secret"), ["grant_type"] = "client_credentials",
        }), ct);
        var o = Lire(await r.Content.ReadAsStringAsync(ct));
        if (!r.IsSuccessStatusCode || S(o, "access_token") == "") throw new InvalidOperationException("Twitch refuse le Client ID ou le secret");
        _jeton = S(o, "access_token");
        _expire = ctx.Maintenant.AddSeconds(L(o, "expires_in") - 120);
    }

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        if (_jeton == "" || ctx.Maintenant >= _expire) await Jeton(ctx, ct);
        var chaines = Liste(ctx.Lire("chaines")).Select(c => c.ToLowerInvariant()).Take(100).ToList();
        var url = "https://api.twitch.tv/helix/streams?first=100&" + string.Join("&", chaines.Select(c => "user_login=" + Uri.EscapeDataString(c)));
        using var req = new HttpRequestMessage(HttpMethod.Get, url);
        req.Headers.Add("Client-Id", ctx.Lire("client"));
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _jeton);
        using var r = await ctx.Http.SendAsync(req, ct);
        if (r.StatusCode == HttpStatusCode.Unauthorized)
        {
            _jeton = "";
            return;
        }
        r.EnsureSuccessStatusCode();
        foreach (var e in Comparer(LireLives(await r.Content.ReadAsStringAsync(ct)))) ctx.Emettre(e);
    }

    // Seuls les passages hors ligne → en live sont annoncés ; le premier relevé sert de point de départ.
    public List<EvenementPilou> Comparer(List<LiveTwitch> lives)
    {
        var sortie = new List<EvenementPilou>();
        var maintenant = lives.Select(l => l.Login).ToHashSet();
        if (_enLive is not null)
            foreach (var l in lives.Where(l => !_enLive.Contains(l.Login)))
                sortie.Add(new EvenementPilou(Id, "notification", $"▶ {Court(l.Nom, 32)} est en live",
                    Court(l.Jeu == "" ? l.Titre : $"{l.Jeu} · {l.Titre}", 100), 0));
        _enLive = maintenant;
        return sortie;
    }

    public static List<LiveTwitch> LireLives(string json) =>
        Lire(json)?["data"] is JsonArray a
            ? a.Select(x => new LiveTwitch(S(x, "user_login").ToLowerInvariant(), S(x, "user_name"), S(x, "title"), S(x, "game_name")))
                .Where(x => x.Login != "").ToList()
            : new List<LiveTwitch>();
}
