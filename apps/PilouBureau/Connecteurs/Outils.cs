using System.IO;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json.Nodes;

namespace PilouBureau;

// Petits outils communs aux connecteurs : listes saisies à la main, textes courts, JSON tolérant, WebSocket.
public static class OutilsConnecteur
{
    // « a, b ; c » → [a, b, c] (vides retirés, doublons aussi).
    public static List<string> Liste(string saisie) =>
        saisie.Split(new[] { ',', ';', '\n', ' ' }, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Distinct(StringComparer.OrdinalIgnoreCase).ToList();

    // Texte d'une bulle : une ligne, borné.
    public static string Court(string texte, int max = 120)
    {
        var t = string.Join(' ', texte.Split(new[] { '\r', '\n', '\t' }, StringSplitOptions.RemoveEmptyEntries)).Trim();
        while (t.Contains("  ")) t = t.Replace("  ", " ");
        return t.Length <= max ? t : t[..(max - 1)].TrimEnd() + "…";
    }

    public static bool Oui(string valeur) => valeur is "oui" or "true" or "1";

    public static string S(JsonNode? n, string cle) =>
        n?[cle] is JsonValue v && v.TryGetValue<string>(out var s) ? s : n?[cle] is JsonValue w ? w.ToString() : "";

    public static long L(JsonNode? n, string cle) =>
        n?[cle] is JsonValue v && v.TryGetValue<long>(out var l) ? l
        : n?[cle] is JsonValue w && long.TryParse(w.ToString(), out var m) ? m : 0;

    public static bool B(JsonNode? n, string cle) => n?[cle] is JsonValue v && v.TryGetValue<bool>(out var b) && b;

    public static JsonNode? Lire(string json)
    {
        try
        {
            return JsonNode.Parse(json);
        }
        catch (System.Text.Json.JsonException)
        {
            return null;
        }
    }

    // Un message texte complet (les trames fragmentées sont réassemblées) ; null quand le serveur ferme.
    public static async Task<string?> RecevoirTexte(WebSocket ws, CancellationToken ct)
    {
        var tampon = new byte[16 * 1024];
        using var tout = new MemoryStream();
        while (true)
        {
            var r = await ws.ReceiveAsync(tampon, ct);
            if (r.MessageType == WebSocketMessageType.Close) return null;
            tout.Write(tampon, 0, r.Count);
            if (tout.Length > 4 * 1024 * 1024) throw new InvalidOperationException("message trop gros");
            if (r.EndOfMessage) return Encoding.UTF8.GetString(tout.ToArray());
        }
    }

    // Délai d'attente avant de se reconnecter après n échecs : 2, 4, 8… jusqu'à 5 min.
    public static TimeSpan Repli(int echecs) => TimeSpan.FromSeconds(Math.Min(300, Math.Pow(2, Math.Clamp(echecs, 1, 9))));
}

// Envois sur un WebSocket : un seul à la fois (ClientWebSocket n'accepte pas deux SendAsync en parallèle).
public sealed class EnvoiWebSocket
{
    private readonly WebSocket _ws;
    private readonly SemaphoreSlim _un = new(1, 1);

    public EnvoiWebSocket(WebSocket ws) => _ws = ws;

    public async Task Envoyer(string texte, CancellationToken ct)
    {
        await _un.WaitAsync(ct);
        try
        {
            await _ws.SendAsync(Encoding.UTF8.GetBytes(texte), WebSocketMessageType.Text, true, ct);
        }
        finally
        {
            _un.Release();
        }
    }
}
