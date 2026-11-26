using System.Globalization;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json.Nodes;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

// ------------------------------------------------------------------------------------------------------
// GitHub : tes notifications (revue demandée, mention, commentaire, CI), et tes PR fusionnées (fête).
// Un jeton personnel en lecture ; relevé toutes les 2 min avec ETag (une réponse 304 ne coûte rien).
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurGitHub : Connecteur
{
    public override string Id => "github";
    public override string Nom => "GitHub";
    public override string Description =>
        "Revue demandée, mention, commentaire, CI rouge ou verte, PR fusionnée : Pilou te le dit. " +
        "Il lit seulement tes notifications et tes PR, avec un jeton en lecture.";
    public override string Signe => "⑂";
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(2);

    public override string Aide =>
        "1. github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token.\n" +
        "2. Coche seulement « notifications » et « repo » (lecture des PR privées) ; durée au choix.\n" +
        "   (Un jeton « fine-grained » marche aussi pour les PR, mais l'API des notifications exige un jeton classique.)\n" +
        "3. Colle le jeton ci-dessous. Il est chiffré sur ce PC (Windows) et ne sert qu'à lire.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("jeton", "Jeton personnel", TypeReglage.Secret, "lecture : notifications, repo"),
        new ReglageConnecteur("revues", "Revues demandées et mentions", TypeReglage.Case, "", "oui"),
        new ReglageConnecteur("commentaires", "Commentaires", TypeReglage.Case, "", "oui"),
        new ReglageConnecteur("ci", "CI rouge ou verte", TypeReglage.Case, "", "oui"),
        new ReglageConnecteur("fusions", "Mes PR fusionnées (Pilou fait la fête)", TypeReglage.Case, "", "oui"),
        new ReglageConnecteur("vus", "", TypeReglage.Texte, Visible: false),
    };

    public override string? Manque(ContexteConnecteur ctx) => ctx.Lire("jeton") == "" ? "colle un jeton personnel GitHub" : null;

    public const string Api = "https://api.github.com";
    private readonly Dictionary<string, string> _etags = new();
    private readonly Dictionary<string, string> _caches = new();

    // GET avec ETag : la réponse précédente est resservie sur un 304 (rien de nouveau) ; null = rien de neuf.
    public async Task<string?> Obtenir(ContexteConnecteur ctx, string chemin, CancellationToken ct)
    {
        using var req = new HttpRequestMessage(HttpMethod.Get, Api + chemin);
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", ctx.Lire("jeton"));
        req.Headers.Accept.ParseAdd("application/vnd.github+json");
        req.Headers.Add("X-GitHub-Api-Version", "2022-11-28");
        if (_etags.TryGetValue(chemin, out var etag)) req.Headers.TryAddWithoutValidation("If-None-Match", etag);
        using var r = await ctx.Http.SendAsync(req, ct);
        if (r.StatusCode == HttpStatusCode.NotModified) return null;
        if (r.StatusCode == HttpStatusCode.Unauthorized) throw new InvalidOperationException("jeton GitHub refusé (expiré ?)");
        r.EnsureSuccessStatusCode();
        var corps = await r.Content.ReadAsStringAsync(ct);
        if (r.Headers.ETag is { } e) _etags[chemin] = e.ToString();
        _caches[chemin] = corps;
        return corps;
    }

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        var vus = Liste(ctx.Lire("vus")).ToHashSet();
        bool premier = vus.Count == 0;
        var nouveaux = new List<EvenementPilou>();

        if (await Obtenir(ctx, "/notifications?participating=false&per_page=30", ct) is { } notes)
            nouveaux.AddRange(LireNotifications(notes, vus, Options(ctx)));

        if (Oui(ctx.Lire("fusions")))
        {
            var depuis = ctx.Maintenant.AddDays(-7).ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
            if (await Obtenir(ctx, $"/search/issues?q=is:pr+author:@me+is:merged+merged:%3E%3D{depuis}&per_page=20", ct) is { } fus)
                nouveaux.AddRange(LireFusions(fus, vus));
        }

        // Premier relevé : on note ce qui existe déjà sans rien annoncer (pas d'avalanche à l'activation).
        if (!premier)
            foreach (var e in nouveaux.Take(6)) ctx.Emettre(e);
        ctx.Ecrire("vus", string.Join(",", vus.TakeLast(300)));
        if (premier && vus.Count == 0) ctx.Ecrire("vus", "debut");
    }

    public sealed record OptionsGitHub(bool Revues = true, bool Commentaires = true, bool Ci = true);

    private static OptionsGitHub Options(ContexteConnecteur ctx) =>
        new(Oui(ctx.Lire("revues")), Oui(ctx.Lire("commentaires")), Oui(ctx.Lire("ci")));

    private static string Depot(JsonNode? n) => S(n?["repository"], "full_name") is { Length: > 0 } f ? f.Split('/').Last() : "";

    // Notifications → événements (une seule fois chacune : clé id + date de mise à jour, ajoutée à « vus »).
    public static List<EvenementPilou> LireNotifications(string json, ISet<string> vus, OptionsGitHub o)
    {
        var l = new List<EvenementPilou>();
        if (Lire(json) is not JsonArray a) return l;
        foreach (var n in a)
        {
            var cle = $"n{S(n, "id")}@{S(n, "updated_at")}";
            if (!vus.Add(cle)) continue;
            var raison = S(n, "reason");
            var titre = Court(S(n?["subject"], "title"), 90);
            var type = S(n?["subject"], "type");
            var depot = Depot(n);
            EvenementPilou? e = raison switch
            {
                "review_requested" when o.Revues => new("github", "notification", $"👀 Revue demandée · {depot}", titre, 1),
                "mention" or "team_mention" when o.Revues => new("github", "notification", $"@ Mentionné · {depot}", titre, 1),
                "comment" or "author" when o.Commentaires && type != "CheckSuite" => new("github", "notification", $"💬 Commentaire · {depot}", titre),
                "ci_activity" when o.Ci => Ci(depot, titre),
                _ => null,
            };
            if (e is not null) l.Add(e);
        }
        return l;
    }

    // « CI workflow run failed for main branch » → rouge ; « succeeded / passed » → verte.
    private static EvenementPilou Ci(string depot, string titre)
    {
        var t = titre.ToLowerInvariant();
        bool rouge = t.Contains("fail") || t.Contains("cancel") || t.Contains("timed out") || t.Contains("échou");
        return rouge
            ? new EvenementPilou("github", "notification", $"✕ CI rouge · {depot}", titre, 1)
            : new EvenementPilou("github", "notification", $"✓ CI verte · {depot}", titre, 0,
                0, new Dictionary<string, string> { ["quete"] = "tests" });
    }

    public static List<EvenementPilou> LireFusions(string json, ISet<string> vus)
    {
        var l = new List<EvenementPilou>();
        if (Lire(json)?["items"] is not JsonArray a) return l;
        foreach (var pr in a)
        {
            if (!vus.Add($"f{S(pr, "id")}")) continue;
            var depot = S(pr, "repository_url").Split('/').LastOrDefault() ?? "";
            l.Add(new EvenementPilou("github", "notification", $"✦ PR fusionnée · {depot}", $"#{L(pr, "number")} {Court(S(pr, "title"), 80)}", 0,
                0, new Dictionary<string, string> { ["humeur"] = "fete" }));
        }
        return l;
    }
}
