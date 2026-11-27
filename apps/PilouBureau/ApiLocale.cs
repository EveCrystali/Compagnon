using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;

namespace PilouBureau;

// API locale de Pilou : http://127.0.0.1:<port>/ (jamais ailleurs que sur la machine elle-même).
// Un petit serveur HTTP/1.1 sur une socket de bouclage : pas d'HttpListener, donc aucun droit
// administrateur ni réservation d'URL. Chaque requête porte « Authorization: Bearer <jeton> ».
//   POST /evenements   un EvenementPilou en JSON → 202
//   GET  /etat         sessions, humeur, niveau (rien de privé) → 200
//   POST /diagnostics  erreurs du fichier ouvert dans l'éditeur (Diagnostics.cs, docs/EDITEURS.md) → 202
// Doc : docs/API.md.
public sealed class ApiLocale : IDisposable
{
    public const int PortParDefaut = 47821;
    private const int TailleMax = 64 * 1024;

    private readonly Func<string> _jeton;
    private readonly Func<string> _etat;
    private readonly Action<EvenementPilou> _recevoir;
    private readonly Func<double> _epoque;
    private readonly Func<RapportDiagnostics, bool>? _diagnostics;
    private TcpListener? _ecoute;
    private CancellationTokenSource? _arret;

    public int Port { get; private set; }
    public string? Erreur { get; private set; }

    public ApiLocale(Func<string> jeton, Func<string> etat, Action<EvenementPilou> recevoir, Func<double>? epoque = null,
        Func<RapportDiagnostics, bool>? diagnostics = null)
    {
        _diagnostics = diagnostics;
        _jeton = jeton;
        _etat = etat;
        _recevoir = recevoir;
        _epoque = epoque ?? (() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
    }

    public bool Demarrer(int port)
    {
        Arreter();
        try
        {
            _ecoute = new TcpListener(IPAddress.Loopback, port);
            _ecoute.Start();
            Port = ((IPEndPoint)_ecoute.LocalEndpoint).Port;
            Erreur = null;
        }
        catch (SocketException e)
        {
            Erreur = $"port {port} indisponible ({e.SocketErrorCode})";
            _ecoute = null;
            return false;
        }
        _arret = new CancellationTokenSource();
        var ct = _arret.Token;
        var ecoute = _ecoute;
        _ = Task.Run(async () =>
        {
            while (!ct.IsCancellationRequested)
            {
                TcpClient client;
                try
                {
                    client = await ecoute.AcceptTcpClientAsync(ct);
                }
                catch (Exception e) when (e is OperationCanceledException or ObjectDisposedException or SocketException)
                {
                    return;
                }
                _ = Task.Run(() => Servir(client, ct), ct);
            }
        }, ct);
        return true;
    }

    public void Arreter()
    {
        _arret?.Cancel();
        try
        {
            _ecoute?.Stop();
        }
        catch (SocketException)
        {
            // déjà fermé
        }
        _ecoute = null;
    }

    public void Dispose() => Arreter();

    private async Task Servir(TcpClient client, CancellationToken ct)
    {
        using (client)
        {
            try
            {
                client.ReceiveTimeout = 5000;
                var flux = client.GetStream();
                bool local = client.Client.RemoteEndPoint is IPEndPoint ip && IPAddress.IsLoopback(ip.Address);
                var (code, corps) = local ? await Lire(flux, ct) : (403, Erreur403);
                var octets = Encoding.UTF8.GetBytes(corps);
                var entete = $"HTTP/1.1 {code} {Raison(code)}\r\nContent-Type: application/json; charset=utf-8\r\n" +
                             $"Content-Length: {octets.Length}\r\nConnection: close\r\n\r\n";
                await flux.WriteAsync(Encoding.ASCII.GetBytes(entete), ct);
                await flux.WriteAsync(octets, ct);
            }
            catch (Exception e) when (e is IOException or SocketException or OperationCanceledException)
            {
                // client parti
            }
        }
    }

    private static readonly string Erreur403 = Json(new { erreur = "réservé à cette machine" });

    private async Task<(int, string)> Lire(NetworkStream flux, CancellationToken ct)
    {
        // En-têtes jusqu'à la ligne vide, puis Content-Length octets de corps.
        var tampon = new MemoryStream();
        var un = new byte[1];
        while (tampon.Length < 16 * 1024)
        {
            int n = await flux.ReadAsync(un, ct);
            if (n == 0) break;
            tampon.WriteByte(un[0]);
            var t = tampon.GetBuffer();
            long l = tampon.Length;
            if (l >= 4 && t[l - 4] == '\r' && t[l - 3] == '\n' && t[l - 2] == '\r' && t[l - 1] == '\n') break;
        }
        var lignes = Encoding.ASCII.GetString(tampon.ToArray()).Split("\r\n");
        var premiere = lignes[0].Split(' ');
        if (premiere.Length < 2) return (400, Json(new { erreur = "requête illisible" }));
        var entetes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var l in lignes.Skip(1))
        {
            int i = l.IndexOf(':');
            if (i > 0) entetes[l[..i].Trim()] = l[(i + 1)..].Trim();
        }
        string corps = "";
        if (entetes.TryGetValue("Content-Length", out var cl) && int.TryParse(cl, out var longueur) && longueur > 0)
        {
            if (longueur > TailleMax) return (413, Json(new { erreur = "corps trop long (64 Ko au plus)" }));
            var b = new byte[longueur];
            int lu = 0;
            while (lu < longueur)
            {
                int n = await flux.ReadAsync(b.AsMemory(lu), ct);
                if (n == 0) break;
                lu += n;
            }
            corps = Encoding.UTF8.GetString(b, 0, lu);
        }
        return Traiter(premiere[0], premiere[1], entetes, corps);
    }

    // Le cœur, sans socket (testé directement).
    public (int Code, string Corps) Traiter(string methode, string chemin, IReadOnlyDictionary<string, string> entetes, string corps)
    {
        // Une page web ne doit pas pouvoir parler à Pilou à travers le navigateur.
        if (entetes.ContainsKey("Origin")) return (403, Json(new { erreur = "appel depuis une page web refusé" }));
        var jeton = _jeton();
        if (jeton == "" || !entetes.TryGetValue("Authorization", out var a) || !Egaux(a, "Bearer " + jeton))
            return (401, Json(new { erreur = "jeton manquant ou faux (en-tête Authorization: Bearer <jeton>)" }));
        var route = chemin.Split('?')[0].TrimEnd('/');
        switch (methode.ToUpperInvariant(), route)
        {
            case ("GET", "/etat"):
                return (200, _etat());
            case ("POST", "/evenements"):
                var e = EvenementPilou.Lire(corps, _epoque(), out var erreur);
                if (e is null) return (400, Json(new { erreur }));
                _recevoir(e);
                return (202, Json(new { recu = true }));
            case ("POST", "/diagnostics") when _diagnostics is not null:
                var d = RapportDiagnostics.Lire(corps, _epoque(), out var erreurD);
                if (d is null) return (400, Json(new { erreur = erreurD }));
                // recu = false : le connecteur « Éditeurs » est coupé (rien n'est gardé).
                return (202, Json(new { recu = _diagnostics(d) }));
            case (_, "/etat" or "/evenements"):
            case (_, "/diagnostics") when _diagnostics is not null:
                return (405, Json(new { erreur = "méthode non permise" }));
            default:
                return (404, Json(new { erreur = "inconnu : GET /etat, POST /evenements, POST /diagnostics" }));
        }
    }

    // Comparaison en temps constant (le jeton ne fuit pas par la durée de la réponse).
    private static bool Egaux(string a, string b) =>
        System.Security.Cryptography.CryptographicOperations.FixedTimeEquals(Encoding.UTF8.GetBytes(a), Encoding.UTF8.GetBytes(b));

    private static string Json(object o) => JsonSerializer.Serialize(o);

    private static string Raison(int code) => code switch
    {
        200 => "OK", 202 => "Accepted", 400 => "Bad Request", 401 => "Unauthorized", 403 => "Forbidden", 404 => "Not Found",
        405 => "Method Not Allowed", 413 => "Payload Too Large", _ => "Error",
    };
}
