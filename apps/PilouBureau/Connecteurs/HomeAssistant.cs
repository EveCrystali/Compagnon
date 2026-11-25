using System.Net.Http;
using System.Net.WebSockets;
using System.Text.Json.Nodes;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

// Protocole WebSocket de Home Assistant, sans réseau (testable) : auth_required → auth → auth_ok → subscribe_events.
public sealed class ProtocoleHomeAssistant
{
    private readonly string _jeton;
    private readonly HashSet<string> _entites;
    public bool Authentifie { get; private set; }
    public bool Abonne { get; private set; }

    public ProtocoleHomeAssistant(string jeton, IEnumerable<string> entites)
    {
        _jeton = jeton;
        _entites = entites.Select(e => e.ToLowerInvariant()).ToHashSet();
    }

    public sealed record Changement(string Entite, string Nom, string Avant, string Apres, string Unite);
    public sealed record Reaction(List<string> AEnvoyer, Changement? Changement);

    public static string Adresse(string url)
    {
        var u = new Uri(url.Trim().TrimEnd('/'));
        var ws = u.Scheme == "https" ? "wss" : "ws";
        return $"{ws}://{u.Authority}{u.AbsolutePath.TrimEnd('/')}/api/websocket";
    }

    public Reaction Recevoir(string texte)
    {
        var envoyer = new List<string>();
        var o = Lire(texte);
        switch (S(o, "type"))
        {
            case "auth_required":
                envoyer.Add(new JsonObject { ["type"] = "auth", ["access_token"] = _jeton }.ToJsonString());
                break;
            case "auth_invalid":
                throw new InvalidOperationException("Home Assistant refuse le jeton");
            case "auth_ok":
                Authentifie = true;
                envoyer.Add(new JsonObject { ["id"] = 1, ["type"] = "subscribe_events", ["event_type"] = "state_changed" }.ToJsonString());
                break;
            case "result" when L(o, "id") == 1:
                Abonne = B(o, "success");
                if (!Abonne) throw new InvalidOperationException("abonnement refusé : " + S(o?["error"], "message"));
                break;
            case "event":
                var d = o?["event"]?["data"];
                var id = S(d, "entity_id").ToLowerInvariant();
                if (!_entites.Contains(id)) break;
                var avant = S(d?["old_state"], "state");
                var apres = S(d?["new_state"], "state");
                if (apres == avant || apres == "") break; // simple mise à jour d'attribut
                var attr = d?["new_state"]?["attributes"];
                var nom = S(attr, "friendly_name");
                return new Reaction(envoyer, new Changement(id, nom == "" ? id : nom, avant, apres, S(attr, "unit_of_measurement")));
        }
        return new Reaction(envoyer, null);
    }

    public static string Etat(string etat) => etat switch
    {
        "on" => "allumé", "off" => "éteint", "open" => "ouvert", "closed" => "fermé",
        "home" => "à la maison", "not_home" => "absent", "locked" => "verrouillé", "unlocked" => "déverrouillé",
        "unavailable" => "indisponible", "playing" => "en lecture", "paused" => "en pause", _ => etat,
    };
}

// ------------------------------------------------------------------------------------------------------
// Home Assistant : les entités que tu choisis changent d'état (porte, lave-linge, capteur…) : Pilou l'annonce.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurHomeAssistant : Connecteur
{
    public override string Id => "homeassistant";
    public override string Nom => "Home Assistant";
    public override string Description => "Une entité choisie change d'état : « 🏠 Porte d'entrée : ouvert ». Connexion locale, rien ne sort de chez toi.";
    public override string Signe => "⌂";
    public override ModeConnecteur Mode => ModeConnecteur.Ecoute;

    public override string Aide =>
        "1. Adresse de Home Assistant, par ex. http://homeassistant.local:8123.\n" +
        "2. Dans Home Assistant : ton profil (en bas à gauche) → Sécurité → Jetons d'accès longue durée → Créer un jeton → colle-le.\n" +
        "3. Entités à suivre : Paramètres → Appareils et services → Entités → ouvre l'entité → Paramètres → « ID d'entité » " +
        "(ex. binary_sensor.porte_entree, sensor.lave_linge_etat), séparées par des virgules.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("url", "Adresse", TypeReglage.Texte, "", "http://homeassistant.local:8123"),
        new ReglageConnecteur("jeton", "Jeton longue durée", TypeReglage.Secret),
        new ReglageConnecteur("entites", "Entités suivies", TypeReglage.Texte, "ID séparés par des virgules"),
    };

    public override string? Manque(ContexteConnecteur ctx) =>
        !Uri.TryCreate(ctx.Lire("url"), UriKind.Absolute, out var u) || u.Scheme is not ("http" or "https") ? "adresse http(s)://… de Home Assistant"
        : ctx.Lire("jeton") == "" ? "jeton longue durée"
        : Liste(ctx.Lire("entites")).Count == 0 ? "au moins une entité" : null;

    private int _echecs;

    public override async Task Ecouter(ContexteConnecteur ctx, CancellationToken ct)
    {
        if (_echecs > 0) await Task.Delay(Repli(_echecs), ct);
        var p = new ProtocoleHomeAssistant(ctx.Lire("jeton"), Liste(ctx.Lire("entites")));
        using var ws = new ClientWebSocket();
        ws.Options.KeepAliveInterval = TimeSpan.FromSeconds(30);
        try
        {
            await ws.ConnectAsync(new Uri(ProtocoleHomeAssistant.Adresse(ctx.Lire("url"))), ct);
        }
        catch (WebSocketException)
        {
            _echecs++;
            throw new HttpRequestException("Home Assistant injoignable");
        }
        var envoi = new EnvoiWebSocket(ws);
        try
        {
            while (!ct.IsCancellationRequested)
            {
                var texte = await RecevoirTexte(ws, ct);
                if (texte is null) break;
                var r = p.Recevoir(texte);
                foreach (var a in r.AEnvoyer) await envoi.Envoyer(a, ct);
                if (p.Abonne) _echecs = 0;
                if (r.Changement is { } c)
                    ctx.Emettre(new EvenementPilou(Id, "notification", $"🏠 {Court(c.Nom, 40)}",
                        Court(ProtocoleHomeAssistant.Etat(c.Apres) + (c.Unite == "" ? "" : " " + c.Unite), 60)));
            }
        }
        finally
        {
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
}
