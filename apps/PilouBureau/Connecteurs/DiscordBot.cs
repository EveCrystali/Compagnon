using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

// Un message reçu sur la passerelle Discord (MESSAGE_CREATE), réduit à ce dont Pilou a besoin.
public sealed record MessageDiscord(string Id, string Salon, string Serveur, string Auteur, string AuteurId, string Contenu,
    bool Bot, IReadOnlyList<string> Mentions);

// Protocole de la passerelle Discord (Gateway v10), sans réseau : on lui donne chaque message reçu, il dit quoi
// renvoyer. Testé seul (séquence hello → identify → ready → heartbeat → message).
public sealed class PasserelleDiscord
{
    // GUILDS (noms des salons), GUILD_MESSAGES, MESSAGE_CONTENT (texte des messages : intent privilégié, à cocher
    // dans le Developer Portal ; sans lui, Discord n'envoie le texte que pour les mentions du bot).
    public const int Intents = (1 << 0) | (1 << 9) | (1 << 15);
    public const string Url = "wss://gateway.discord.gg/?v=10&encoding=json";

    private readonly string _jeton;
    private readonly Dictionary<string, string> _salons = new();

    public PasserelleDiscord(string jeton, string sessionId = "", int? sequence = null, string urlReprise = "")
    {
        _jeton = jeton;
        SessionId = sessionId;
        Sequence = sequence;
        UrlReprise = urlReprise;
    }

    public int? Sequence { get; private set; }
    public string SessionId { get; private set; }
    public string UrlReprise { get; private set; }
    public int IntervalleBattement { get; private set; }
    public string IdBot { get; private set; } = "";
    public bool Pret { get; private set; }
    // Battement envoyé sans accusé : connexion « zombie », à rouvrir.
    public bool AccuseAttendu { get; set; }
    public IReadOnlyDictionary<string, string> Salons => _salons;

    public sealed record Reaction(List<string> AEnvoyer, MessageDiscord? Message = null, bool Reconnecter = false, bool Reprendre = false);

    public string Battement() => new JsonObject { ["op"] = 1, ["d"] = Sequence is { } s ? JsonValue.Create(s) : null }.ToJsonString();

    public string Identifier() => new JsonObject
    {
        ["op"] = 2,
        ["d"] = new JsonObject
        {
            ["token"] = _jeton,
            ["intents"] = Intents,
            ["properties"] = new JsonObject { ["os"] = "windows", ["browser"] = "pilou", ["device"] = "pilou" },
        },
    }.ToJsonString();

    public string Reprise() => new JsonObject
    {
        ["op"] = 6,
        ["d"] = new JsonObject { ["token"] = _jeton, ["session_id"] = SessionId, ["seq"] = Sequence },
    }.ToJsonString();

    public Reaction Recevoir(string json)
    {
        var o = Lire(json);
        var aEnvoyer = new List<string>();
        if (o is null) return new Reaction(aEnvoyer);
        int op = (int)L(o, "op");
        switch (op)
        {
            case 10: // HELLO
                IntervalleBattement = (int)L(o["d"], "heartbeat_interval");
                aEnvoyer.Add(SessionId != "" && Sequence is not null ? Reprise() : Identifier());
                return new Reaction(aEnvoyer);
            case 11: // HEARTBEAT_ACK
                AccuseAttendu = false;
                return new Reaction(aEnvoyer);
            case 1: // le serveur demande un battement tout de suite
                aEnvoyer.Add(Battement());
                return new Reaction(aEnvoyer);
            case 7: // RECONNECT : reprendre la session sur une nouvelle connexion
                return new Reaction(aEnvoyer, Reconnecter: true, Reprendre: true);
            case 9: // INVALID_SESSION (d = reprise possible ?)
                bool reprenable = o["d"] is JsonValue v && v.TryGetValue<bool>(out var r) && r;
                if (!reprenable)
                {
                    SessionId = "";
                    Sequence = null;
                }
                return new Reaction(aEnvoyer, Reconnecter: true, Reprendre: reprenable);
            case 0: // DISPATCH
                if (o["s"] is JsonValue sv && sv.TryGetValue<int>(out var seq)) Sequence = seq;
                return Distribuer(S(o, "t"), o["d"], aEnvoyer);
        }
        return new Reaction(aEnvoyer);
    }

    private Reaction Distribuer(string type, JsonNode? d, List<string> aEnvoyer)
    {
        switch (type)
        {
            case "READY":
                SessionId = S(d, "session_id");
                UrlReprise = S(d, "resume_gateway_url");
                IdBot = S(d?["user"], "id");
                Pret = true;
                break;
            case "RESUMED":
                Pret = true;
                break;
            case "GUILD_CREATE":
                if (d?["channels"] is JsonArray canaux)
                    foreach (var c in canaux)
                        if (S(c, "id") != "") _salons[S(c, "id")] = S(c, "name");
                break;
            case "CHANNEL_CREATE":
            case "CHANNEL_UPDATE":
                if (S(d, "id") != "") _salons[S(d, "id")] = S(d, "name");
                break;
            case "MESSAGE_CREATE":
                var mentions = d?["mentions"] is JsonArray m ? m.Select(x => S(x, "id")).Where(x => x != "").ToList() : new List<string>();
                var auteur = d?["author"];
                var nom = S(d?["member"], "nick");
                if (nom == "") nom = S(auteur, "global_name");
                if (nom == "") nom = S(auteur, "username");
                return new Reaction(aEnvoyer, new MessageDiscord(S(d, "id"), S(d, "channel_id"), S(d, "guild_id"), nom, S(auteur, "id"),
                    S(d, "content"), B(auteur, "bot"), mentions));
        }
        return new Reaction(aEnvoyer);
    }

    // Ce que Pilou annonce d'un message, ou null s'il ne le concerne pas : mention du bot ou de toi, ou message
    // dans un salon suivi. Jamais tes propres messages ni ceux des bots.
    public static (string Titre, string Texte, int Gravite)? Annonce(MessageDiscord m, string idBot, string idUtilisateur,
        IReadOnlyCollection<string> salonsSuivis, bool masquer, IReadOnlyDictionary<string, string> nomsSalons)
    {
        if (m.Bot || (idUtilisateur != "" && m.AuteurId == idUtilisateur)) return null;
        bool mention = (idBot != "" && m.Mentions.Contains(idBot)) || (idUtilisateur != "" && m.Mentions.Contains(idUtilisateur));
        if (!mention && !salonsSuivis.Contains(m.Salon)) return null;
        var salon = nomsSalons.TryGetValue(m.Salon, out var n) && n != "" ? "#" + n : "un salon";
        var titre = $"💬 {salon} · {Court(m.Auteur, 32)}";
        if (masquer || m.Contenu == "") return (titre, mention ? "t'a mentionné" : "a écrit", mention ? 1 : 0);
        var texte = Regex.Replace(m.Contenu, @"<@!?(\d+)>", x => x.Groups[1].Value == idUtilisateur || x.Groups[1].Value == idBot ? "@toi" : "@…");
        texte = Regex.Replace(texte, @"<#(\d+)>", x => nomsSalons.TryGetValue(x.Groups[1].Value, out var s) ? "#" + s : "#…");
        return (titre, Court(texte, 140), mention ? 1 : 0);
    }
}

// ------------------------------------------------------------------------------------------------------
// Discord (bot) : un bot que TU crées et invites sur tes serveurs. Entrée : mentions et salons suivis ;
// sortie : un salon où Pilou raconte ce qui se passe. Jamais ton compte personnel (selfbot interdit).
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurDiscordBot : Connecteur
{
    public override string Id => "discord-bot";
    public override string Nom => "Discord (bot)";
    public override string Description =>
        "Un bot à toi sur tes serveurs : Pilou annonce les mentions et les messages des salons choisis, et peut raconter " +
        "ce qui se passe (une IA attend, quête réussie, évolution) dans un salon de sortie.";
    public override string Signe => "♯";
    public override ModeConnecteur Mode => ModeConnecteur.Ecoute;
    public override bool Sortie => true;

    public override string Aide =>
        "1. Va sur discord.com/developers/applications → New Application (nomme-la « Pilou »).\n" +
        "2. Onglet Bot → Reset Token → copie le jeton dans « Jeton du bot » ci-dessous. Coche aussi « Message Content Intent » " +
        "(sinon Pilou ne verra que les mentions).\n" +
        "3. Onglet OAuth2 → URL Generator : coche « bot », puis les permissions View Channels, Send Messages et Read Message History ; " +
        "ouvre l'URL et invite le bot sur ton serveur.\n" +
        "4. Discord → Paramètres → Avancés → Mode développeur. Clic droit sur toi → Copier l'identifiant (ton ID) ; " +
        "clic droit sur un salon → Copier l'identifiant (salons suivis, salon de sortie).\n" +
        "Pilou ne se connecte JAMAIS avec ton compte personnel : automatiser un compte utilisateur (« selfbot ») est interdit " +
        "par Discord et peut le faire bannir. Seul un bot invité voit les salons où tu l'as invité, pas tes messages privés.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("jeton", "Jeton du bot", TypeReglage.Secret, "Developer Portal → Bot → Reset Token"),
        new ReglageConnecteur("utilisateur", "Ton ID Discord", TypeReglage.Texte, "pour être prévenu quand on te mentionne"),
        new ReglageConnecteur("salons", "Salons suivis (IDs)", TypeReglage.Texte, "séparés par des virgules ; vide : mentions seulement"),
        new ReglageConnecteur("masquer", "Masquer le contenu des messages", TypeReglage.Case, "Pilou dit seulement qui a écrit", "non"),
        new ReglageConnecteur("sortie", "Salon de sortie (ID)", TypeReglage.Texte, "vide : Pilou ne poste rien"),
    };

    public override IReadOnlyList<ActionConnecteur> Actions => new[]
    {
        new ActionConnecteur("Tester le salon de sortie", async (ctx, ct) =>
        {
            if (ctx.Lire("sortie") == "") return "indique d'abord le salon de sortie";
            await Poster(ctx, "👋 Pilou est branché ici.", ct);
            return "message envoyé";
        }),
    };

    public override string? Manque(ContexteConnecteur ctx) => ctx.Lire("jeton") == "" ? "colle le jeton du bot" : null;

    // Session gardée en mémoire entre deux connexions (reprise sans tout recevoir à nouveau).
    private string _session = "", _urlReprise = "";
    private int? _sequence;
    private int _echecs;
    private DateTime _dernierPost = DateTime.MinValue;

    public override async Task Ecouter(ContexteConnecteur ctx, CancellationToken ct)
    {
        if (_echecs > 0) await Task.Delay(Repli(_echecs), ct);
        var p = new PasserelleDiscord(ctx.Lire("jeton"), _session, _sequence, _urlReprise);
        using var ws = new ClientWebSocket();
        var url = p.SessionId != "" && p.UrlReprise != "" ? p.UrlReprise.TrimEnd('/') + "/?v=10&encoding=json" : PasserelleDiscord.Url;
        try
        {
            await ws.ConnectAsync(new Uri(url), ct);
        }
        catch (WebSocketException)
        {
            _echecs++;
            throw new HttpRequestException("passerelle Discord injoignable");
        }
        var envoi = new EnvoiWebSocket(ws);
        using var fin = CancellationTokenSource.CreateLinkedTokenSource(ct);
        Task? battements = null;
        try
        {
            while (!fin.IsCancellationRequested)
            {
                var texte = await RecevoirTexte(ws, fin.Token);
                if (texte is null)
                {
                    var code = (int?)ws.CloseStatus ?? 0;
                    // 4004 : jeton refusé ; 4014 : intent privilégié non autorisé — inutile d'insister vite.
                    if (code == 4004) throw new InvalidOperationException("jeton du bot refusé");
                    if (code == 4014) throw new InvalidOperationException("coche « Message Content Intent » dans le Developer Portal");
                    if (code is 4007 or 4009) { _session = ""; _sequence = null; }
                    break;
                }
                var r = p.Recevoir(texte);
                foreach (var a in r.AEnvoyer) await envoi.Envoyer(a, fin.Token);
                if (p.IntervalleBattement > 0 && battements is null)
                    battements = Battre(p, envoi, ws, fin);
                if (p.Pret)
                {
                    _echecs = 0;
                    _session = p.SessionId;
                    _urlReprise = p.UrlReprise;
                }
                _sequence = p.Sequence;
                if (r.Message is { } m)
                {
                    var salons = Liste(ctx.Lire("salons"));
                    if (PasserelleDiscord.Annonce(m, p.IdBot, ctx.Lire("utilisateur").Trim(), salons, Oui(ctx.Lire("masquer")), p.Salons) is { } an)
                        ctx.Emettre(new EvenementPilou(Id, "message", an.Titre, an.Texte, an.Gravite, 0,
                            new Dictionary<string, string> { ["salon"] = m.Salon }));
                }
                if (r.Reconnecter)
                {
                    if (!r.Reprendre) { _session = ""; _sequence = null; }
                    break;
                }
            }
        }
        finally
        {
            fin.Cancel();
            if (ws.State == WebSocketState.Open)
                try
                {
                    await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                }
                catch (WebSocketException)
                {
                }
        }
    }

    // Battements : premier après intervalle × hasard, puis à l'intervalle ; sans accusé, on coupe (reconnexion).
    private static async Task Battre(PasserelleDiscord p, EnvoiWebSocket envoi, ClientWebSocket ws, CancellationTokenSource fin)
    {
        try
        {
            await Task.Delay((int)(p.IntervalleBattement * Random.Shared.NextDouble()), fin.Token);
            while (!fin.IsCancellationRequested)
            {
                if (p.AccuseAttendu)
                {
                    ws.Abort();
                    fin.Cancel();
                    return;
                }
                p.AccuseAttendu = true;
                await envoi.Envoyer(p.Battement(), fin.Token);
                await Task.Delay(p.IntervalleBattement, fin.Token);
            }
        }
        catch (OperationCanceledException)
        {
        }
        catch (WebSocketException)
        {
            fin.Cancel();
        }
    }

    // Sortie : ce qui arrive à Pilou, posté dans le salon choisi (au plus un message toutes les 3 s).
    public override async Task Sortir(ContexteConnecteur ctx, EvenementPilou e, CancellationToken ct)
    {
        if (ctx.Lire("sortie") == "" || e.Source == Id) return;
        if (DateTime.UtcNow - _dernierPost < TimeSpan.FromSeconds(3)) await Task.Delay(TimeSpan.FromSeconds(3), ct);
        await Poster(ctx, e.Texte == "" ? e.Titre : $"{e.Titre} — {e.Texte}", ct);
    }

    private async Task Poster(ContexteConnecteur ctx, string texte, CancellationToken ct)
    {
        var salon = new string(ctx.Lire("sortie").Where(char.IsAsciiDigit).ToArray());
        if (salon == "") return;
        for (int essai = 0; essai < 2; essai++)
        {
            using var req = new HttpRequestMessage(HttpMethod.Post, $"https://discord.com/api/v10/channels/{salon}/messages")
            {
                Content = new StringContent(new JsonObject
                {
                    ["content"] = Court(texte, 1900),
                    ["allowed_mentions"] = new JsonObject { ["parse"] = new JsonArray() },
                }.ToJsonString(), Encoding.UTF8, "application/json"),
            };
            req.Headers.Authorization = new AuthenticationHeaderValue("Bot", ctx.Lire("jeton"));
            using var r = await ctx.Http.SendAsync(req, ct);
            _dernierPost = DateTime.UtcNow;
            if ((int)r.StatusCode == 429)
            {
                // Limite de débit : on attend ce que Discord demande (borné à 10 s), puis un seul nouvel essai.
                var corps = Lire(await r.Content.ReadAsStringAsync(ct));
                var attente = corps?["retry_after"] is JsonValue v && v.TryGetValue<double>(out var sec) ? sec : 2;
                await Task.Delay(TimeSpan.FromSeconds(Math.Clamp(attente, 0.5, 10)), ct);
                continue;
            }
            if (r.StatusCode is HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden)
                throw new InvalidOperationException("le bot n'a pas le droit d'écrire dans ce salon");
            r.EnsureSuccessStatusCode();
            return;
        }
    }
}
