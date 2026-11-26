using System.Diagnostics;
using System.Globalization;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

// OAuth 2 « PKCE » (RFC 7636) : pas de secret d'application sur le PC, un vérificateur tiré au hasard à chaque
// connexion et son empreinte SHA-256 envoyée au service.
public static class Pkce
{
    private const string Alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~";

    public static string Verificateur(int longueur = 64)
    {
        var c = new char[longueur];
        for (int i = 0; i < longueur; i++) c[i] = Alphabet[RandomNumberGenerator.GetInt32(Alphabet.Length)];
        return new string(c);
    }

    public static string Defi(string verificateur) => Base64Url(SHA256.HashData(Encoding.ASCII.GetBytes(verificateur)));

    public static string Base64Url(byte[] b) => Convert.ToBase64String(b).TrimEnd('=').Replace('+', '-').Replace('/', '_');
}

public sealed record LectureSpotify(string Id, string Titre, string Artiste, bool EnCours, double Tempo);

// ------------------------------------------------------------------------------------------------------
// Spotify : ce que tu écoutes. Pilou enfile ses écouteurs et danse au tempo du morceau.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurSpotify : Connecteur
{
    public override string Id => "spotify";
    public override string Nom => "Spotify";
    public override string Description =>
        "Le morceau en cours : Pilou met ses écouteurs, danse au tempo et dit « ♪ titre — artiste ». " +
        "Connexion par ton compte Spotify (lecture du morceau en cours seulement).";
    public override string Signe => "♪";
    public override TimeSpan Intervalle => TimeSpan.FromSeconds(20);

    public const int PortParDefaut = 47822;

    public override string Aide =>
        "1. developer.spotify.com/dashboard → Create app (nom : Pilou ; API : Web API).\n" +
        $"2. Redirect URI : http://127.0.0.1:{PortParDefaut}/callback (le même port que ci-dessous) → Save.\n" +
        "3. Copie le « Client ID » ci-dessous (pas besoin du Client secret).\n" +
        "4. « Se connecter à Spotify » : ton navigateur s'ouvre, accepte, et reviens ici.\n" +
        "Une app Spotify en mode développement ne sert qu'aux comptes que tu y ajoutes (User Management).";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("client", "Client ID", TypeReglage.Texte, "developer.spotify.com/dashboard"),
        new ReglageConnecteur("port", "Port de retour", TypeReglage.Texte, "", PortParDefaut.ToString(CultureInfo.InvariantCulture)),
        new ReglageConnecteur("annoncer", "Annoncer chaque morceau", TypeReglage.Case, "", "oui"),
        new ReglageConnecteur("acces", "", TypeReglage.Secret, Visible: false),
        new ReglageConnecteur("rafraichir", "", TypeReglage.Secret, Visible: false),
        new ReglageConnecteur("expire", "", TypeReglage.Texte, Visible: false),
    };

    public override IReadOnlyList<ActionConnecteur> Actions => new[] { new ActionConnecteur("Se connecter à Spotify", Connecter) };

    public override string? Manque(ContexteConnecteur ctx) =>
        ctx.Lire("client") == "" ? "colle le Client ID de ton app Spotify"
        : ctx.Lire("rafraichir") == "" ? "« Se connecter à Spotify »" : null;

    // Lu par la fenêtre de Pilou : musique en cours (tenue musique, tempo de la danse).
    public static volatile LectureSpotify? Lecture;

    private int Port(ContexteConnecteur ctx) => int.TryParse(ctx.Lire("port"), out var p) && p is > 1024 and < 65536 ? p : PortParDefaut;
    private string Retour(ContexteConnecteur ctx) => $"http://127.0.0.1:{Port(ctx)}/callback";

    public static string UrlAutorisation(string client, string retour, string defi, string etat) =>
        "https://accounts.spotify.com/authorize?response_type=code&client_id=" + Uri.EscapeDataString(client) +
        "&scope=" + Uri.EscapeDataString("user-read-currently-playing user-read-playback-state") +
        "&redirect_uri=" + Uri.EscapeDataString(retour) + "&code_challenge_method=S256&code_challenge=" + defi +
        "&state=" + Uri.EscapeDataString(etat);

    private async Task<string> Connecter(ContexteConnecteur ctx, CancellationToken ct)
    {
        if (ctx.Lire("client") == "") return "colle d'abord le Client ID";
        var verif = Pkce.Verificateur();
        var etat = Pkce.Verificateur(24);
        using var ecoute = new HttpListener();
        ecoute.Prefixes.Add($"http://127.0.0.1:{Port(ctx)}/callback/");
        ecoute.Start();
        Process.Start(new ProcessStartInfo(UrlAutorisation(ctx.Lire("client"), Retour(ctx), Pkce.Defi(verif), etat)) { UseShellExecute = true });
        using var delai = CancellationTokenSource.CreateLinkedTokenSource(ct);
        delai.CancelAfter(TimeSpan.FromMinutes(3));
        var attente = ecoute.GetContextAsync();
        await Task.WhenAny(attente, Task.Delay(Timeout.Infinite, delai.Token)).ConfigureAwait(false);
        if (!attente.IsCompleted) return "pas de réponse de Spotify (3 min)";
        var c = attente.Result;
        var code = c.Request.QueryString["code"] ?? "";
        bool ok = code != "" && c.Request.QueryString["state"] == etat;
        var page = Encoding.UTF8.GetBytes(ok
            ? "<meta charset=utf-8><p style='font:16px sans-serif'>Pilou est connecté à Spotify ♪ — tu peux fermer cet onglet.</p>"
            : "<meta charset=utf-8><p style='font:16px sans-serif'>Connexion refusée ou expirée.</p>");
        c.Response.ContentType = "text/html; charset=utf-8";
        await c.Response.OutputStream.WriteAsync(page, ct);
        c.Response.Close();
        if (!ok) return "connexion refusée";
        await Jetons(ctx, new Dictionary<string, string>
        {
            ["grant_type"] = "authorization_code", ["code"] = code, ["redirect_uri"] = Retour(ctx),
            ["client_id"] = ctx.Lire("client"), ["code_verifier"] = verif,
        }, ct);
        return "connecté ✓";
    }

    private static async Task Jetons(ContexteConnecteur ctx, Dictionary<string, string> formulaire, CancellationToken ct)
    {
        using var r = await ctx.Http.PostAsync("https://accounts.spotify.com/api/token", new FormUrlEncodedContent(formulaire), ct);
        var corps = Lire(await r.Content.ReadAsStringAsync(ct));
        if (!r.IsSuccessStatusCode || S(corps, "access_token") == "")
        {
            if (formulaire["grant_type"] == "refresh_token") ctx.Ecrire("rafraichir", "");
            throw new InvalidOperationException("Spotify a refusé la connexion : reconnecte-toi");
        }
        ctx.Ecrire("acces", S(corps, "access_token"));
        if (S(corps, "refresh_token") != "") ctx.Ecrire("rafraichir", S(corps, "refresh_token"));
        ctx.Ecrire("expire", ctx.Maintenant.AddSeconds(L(corps, "expires_in") - 60).ToString("o", CultureInfo.InvariantCulture));
    }

    private string _dernier = "";
    private bool _sansTempo;

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        if (!DateTime.TryParse(ctx.Lire("expire"), CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out var exp) || ctx.Maintenant >= exp)
            await Jetons(ctx, new Dictionary<string, string>
            {
                ["grant_type"] = "refresh_token", ["refresh_token"] = ctx.Lire("rafraichir"), ["client_id"] = ctx.Lire("client"),
            }, ct);
        using var req = new HttpRequestMessage(HttpMethod.Get, "https://api.spotify.com/v1/me/player/currently-playing");
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", ctx.Lire("acces"));
        using var r = await ctx.Http.SendAsync(req, ct);
        if (r.StatusCode == HttpStatusCode.NoContent)
        {
            Lecture = null;
            return;
        }
        if (r.StatusCode == HttpStatusCode.Unauthorized)
        {
            ctx.Ecrire("expire", "");
            return;
        }
        r.EnsureSuccessStatusCode();
        var l = LireLecture(await r.Content.ReadAsStringAsync(ct));
        if (l is null || !l.EnCours)
        {
            Lecture = null;
            return;
        }
        double tempo = Lecture?.Id == l.Id ? Lecture.Tempo : 0;
        if (tempo == 0 && !_sansTempo) tempo = await Tempo(ctx, l.Id, ct);
        Lecture = l with { Tempo = tempo };
        if (l.Id != _dernier)
        {
            _dernier = l.Id;
            if (Oui(ctx.Lire("annoncer")))
                ctx.Emettre(new EvenementPilou(Id, "notification", $"♪ {Court(l.Titre, 60)}", Court(l.Artiste, 60), 0,
                    0, new Dictionary<string, string> { ["tenue"] = "musique" }));
        }
    }

    // Tempo du morceau (/audio-features) : les apps Spotify récentes n'y ont plus droit (403) ; on s'en passe alors.
    private async Task<double> Tempo(ContexteConnecteur ctx, string id, CancellationToken ct)
    {
        using var req = new HttpRequestMessage(HttpMethod.Get, "https://api.spotify.com/v1/audio-features/" + Uri.EscapeDataString(id));
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", ctx.Lire("acces"));
        using var r = await ctx.Http.SendAsync(req, ct);
        if (r.StatusCode is HttpStatusCode.Forbidden or HttpStatusCode.NotFound)
        {
            _sansTempo = true;
            return 0;
        }
        if (!r.IsSuccessStatusCode) return 0;
        return Lire(await r.Content.ReadAsStringAsync(ct))?["tempo"] is JsonValue v && v.TryGetValue<double>(out var t) ? t : 0;
    }

    public static LectureSpotify? LireLecture(string json)
    {
        var o = Lire(json);
        var item = o?["item"];
        if (item is null) return null;
        var artistes = item["artists"] is JsonArray a ? string.Join(", ", a.Select(x => S(x, "name")).Where(x => x != "")) : "";
        if (artistes == "") artistes = S(item["show"], "name"); // podcast
        return new LectureSpotify(S(item, "id"), S(item, "name"), artistes, B(o, "is_playing"), 0);
    }
}
