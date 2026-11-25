using System.IO;
using System.IO.Pipes;
using System.Net.Http;
using System.Text;
using System.Text.Json;

namespace PilouBureau;

// Statut Discord (« Joue à Pilou ») par le tuyau local de l'app Discord (Rich Presence) : rien ne sort
// de la machine, Discord affiche ce que Pilou lui donne. Il faut l'identifiant d'une application
// Discord (Developer Portal → New Application) ; une seule suffit pour tout le monde, elle n'est pas secrète.
public sealed class PresenceDiscord : IDisposable
{
    private readonly object _verrou = new();
    private NamedPipeClientStream? _tuyau;
    private string _id = "";
    private string _envoye = "";
    private DateTime _prochainEssai = DateTime.MinValue;
    private DateTime _dernierEnvoi = DateTime.MinValue;
    private readonly long _debut = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
    private bool _occupe;

    public bool Connecte => _tuyau is { IsConnected: true };

    // Appelé souvent (à chaque lecture) : n'envoie qu'un changement, au plus toutes les 15 s, en tâche de fond.
    public void Publier(string idApplication, string details, string etat)
    {
        if (string.IsNullOrWhiteSpace(idApplication))
        {
            Fermer();
            return;
        }
        var activite = $"{details}\n{etat}";
        lock (_verrou)
        {
            if (_occupe) return;
            if (activite == _envoye && Connecte) return;
            if (DateTime.UtcNow - _dernierEnvoi < TimeSpan.FromSeconds(15)) return;
            if (!Connecte && DateTime.UtcNow < _prochainEssai) return;
            _occupe = true;
        }
        Task.Run(() =>
        {
            try
            {
                if (_id != idApplication) Fermer();
                if (!Connecte) Connecter(idApplication);
                if (!Connecte) return;
                Envoyer(1, new
                {
                    cmd = "SET_ACTIVITY",
                    nonce = Guid.NewGuid().ToString(),
                    args = new
                    {
                        pid = Environment.ProcessId,
                        activity = new
                        {
                            details,
                            state = etat,
                            timestamps = new { start = _debut },
                            assets = new { large_image = "pilou", large_text = "Pilou, compagnon de code" },
                        },
                    },
                });
                _envoye = activite;
                _dernierEnvoi = DateTime.UtcNow;
            }
            catch (Exception e) when (e is IOException or ObjectDisposedException or TimeoutException or InvalidOperationException)
            {
                Fermer();
                _prochainEssai = DateTime.UtcNow.AddSeconds(30);
            }
            finally
            {
                lock (_verrou) _occupe = false;
            }
        });
    }

    private void Connecter(string idApplication)
    {
        // Discord ouvre discord-ipc-0 (ou -1… s'il y a plusieurs clients).
        for (int i = 0; i < 10; i++)
        {
            var t = new NamedPipeClientStream(".", $"discord-ipc-{i}", PipeDirection.InOut, PipeOptions.Asynchronous);
            try
            {
                t.Connect(300);
            }
            catch (Exception e) when (e is TimeoutException or IOException)
            {
                t.Dispose();
                continue;
            }
            _tuyau = t;
            _id = idApplication;
            Envoyer(0, new { v = 1, client_id = idApplication });
            Lire(); // READY, ou une erreur (identifiant inconnu) qui ferme le tuyau
            Task.Run(Vider);
            return;
        }
        _prochainEssai = DateTime.UtcNow.AddSeconds(30); // Discord fermé : on réessaie plus tard
    }

    private void Envoyer(int code, object charge)
    {
        var json = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(charge));
        var entete = new byte[8];
        BitConverter.TryWriteBytes(entete.AsSpan(0, 4), code);
        BitConverter.TryWriteBytes(entete.AsSpan(4, 4), json.Length);
        _tuyau!.Write(entete);
        _tuyau.Write(json);
        _tuyau.Flush();
    }

    private string Lire()
    {
        var entete = new byte[8];
        _tuyau!.ReadExactly(entete);
        int code = BitConverter.ToInt32(entete, 0), longueur = BitConverter.ToInt32(entete, 4);
        var corps = new byte[Math.Clamp(longueur, 0, 1 << 16)];
        _tuyau.ReadExactly(corps);
        if (code == 2) throw new IOException("Discord a refusé la connexion (identifiant d'application ?)");
        return Encoding.UTF8.GetString(corps);
    }

    // Les réponses de Discord sont lues et jetées : un tuyau plein bloquerait l'envoi.
    private void Vider()
    {
        try
        {
            while (Connecte) Lire();
        }
        catch (Exception e) when (e is IOException or ObjectDisposedException or EndOfStreamException or InvalidOperationException)
        {
            Fermer();
        }
    }

    public void Fermer()
    {
        var t = _tuyau;
        _tuyau = null;
        _envoye = "";
        try
        {
            t?.Dispose();
        }
        catch (IOException)
        {
            // déjà fermé
        }
    }

    public void Dispose() => Fermer();
}

// Prévenir ailleurs que sur l'écran (téléphone) quand une IA attend : un webhook Discord (salon à soi),
// ou tout service qui accepte un POST JSON {"content": …} (Slack : {"text": …}, ntfy : texte brut).
public static class Webhook
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(10) };

    public static bool Valide(string url) =>
        Uri.TryCreate(url, UriKind.Absolute, out var u) && u.Scheme == Uri.UriSchemeHttps;

    public static HttpContent Corps(string url, string texte)
    {
        var hote = new Uri(url).Host;
        if (hote.EndsWith("ntfy.sh", StringComparison.OrdinalIgnoreCase))
            return new StringContent(texte, Encoding.UTF8, "text/plain");
        object charge = hote.Contains("slack.com", StringComparison.OrdinalIgnoreCase)
            ? new { text = texte }
            : new { content = texte, username = "Pilou", allowed_mentions = new { parse = Array.Empty<string>() } };
        return new StringContent(JsonSerializer.Serialize(charge), Encoding.UTF8, "application/json");
    }

    // En tâche de fond ; renvoie true si le service a répondu 2xx.
    public static async Task<bool> Envoyer(string url, string texte)
    {
        if (!Valide(url)) return false;
        try
        {
            using var r = await Http.PostAsync(url, Corps(url, texte));
            return r.IsSuccessStatusCode;
        }
        catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
        {
            return false;
        }
    }
}
