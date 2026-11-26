using System.IO;
using System.Globalization;
using System.Net.Security;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

// Client IMAP minimal sur un flux (TLS en vrai, scénario enregistré dans les tests) : LOGIN, EXAMINE,
// UID SEARCH, UID FETCH des seuls en-têtes From/Subject (BODY.PEEK : rien n'est marqué comme lu), LOGOUT.
public sealed class ClientImap
{
    private readonly Stream _flux;
    private int _n;

    static ClientImap() => Encoding.RegisterProvider(CodePagesEncodingProvider.Instance); // windows-1252 & co

    public ClientImap(Stream flux) => _flux = flux;

    private async Task<string> Ligne(CancellationToken ct)
    {
        var b = new List<byte>(256);
        var un = new byte[1];
        while (true)
        {
            int lu = await _flux.ReadAsync(un, ct);
            if (lu == 0) throw new IOException("connexion IMAP fermée");
            if (un[0] == '\n') break;
            if (un[0] != '\r') b.Add(un[0]);
            if (b.Count > 64 * 1024) throw new IOException("ligne IMAP trop longue");
        }
        return Encoding.UTF8.GetString(b.ToArray());
    }

    private async Task<string> Litteral(int taille, CancellationToken ct)
    {
        var b = new byte[Math.Min(taille, 1 << 20)];
        int pris = 0;
        while (pris < b.Length)
        {
            int lu = await _flux.ReadAsync(b.AsMemory(pris), ct);
            if (lu == 0) throw new IOException("connexion IMAP fermée");
            pris += lu;
        }
        return Encoding.UTF8.GetString(b);
    }

    public async Task<string> Accueil(CancellationToken ct)
    {
        var l = await Ligne(ct);
        if (!l.StartsWith("* OK", StringComparison.OrdinalIgnoreCase)) throw new IOException("serveur IMAP : " + Court(l, 80));
        return l;
    }

    // Envoie « A1 commande » et lit jusqu'à la réponse étiquetée. Un littéral {N} est inclus dans la ligne.
    public async Task<List<string>> Commande(string commande, CancellationToken ct)
    {
        var etiquette = "A" + (++_n).ToString(CultureInfo.InvariantCulture);
        var octets = Encoding.UTF8.GetBytes($"{etiquette} {commande}\r\n");
        await _flux.WriteAsync(octets, ct);
        await _flux.FlushAsync(ct);
        var lignes = new List<string>();
        while (true)
        {
            var l = await Ligne(ct);
            var m = Regex.Match(l, @"\{(\d+)\}$");
            if (m.Success)
            {
                l = l + "\n" + await Litteral(int.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture), ct) + await Ligne(ct);
            }
            if (l.StartsWith(etiquette + " ", StringComparison.Ordinal))
            {
                var statut = l[(etiquette.Length + 1)..];
                if (!statut.StartsWith("OK", StringComparison.OrdinalIgnoreCase))
                    throw new IOException(commande.StartsWith("LOGIN") ? "identifiants refusés (mot de passe d'application ?)" : "IMAP : " + Court(statut, 80));
                return lignes;
            }
            lignes.Add(l);
        }
    }

    public static string Quoter(string s) => "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";

    public static long UidValidite(IEnumerable<string> lignes)
    {
        foreach (var l in lignes)
        {
            var m = Regex.Match(l, @"\[UIDVALIDITY (\d+)\]", RegexOptions.IgnoreCase);
            if (m.Success) return long.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
        }
        return 0;
    }

    public static long UidSuivant(IEnumerable<string> lignes)
    {
        foreach (var l in lignes)
        {
            var m = Regex.Match(l, @"\[UIDNEXT (\d+)\]", RegexOptions.IgnoreCase);
            if (m.Success) return long.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture);
        }
        return 0;
    }

    public static List<long> Uids(IEnumerable<string> lignes)
    {
        var l = new List<long>();
        foreach (var x in lignes)
            if (x.StartsWith("* SEARCH", StringComparison.OrdinalIgnoreCase))
                foreach (var t in x[8..].Split(' ', StringSplitOptions.RemoveEmptyEntries))
                    if (long.TryParse(t, NumberStyles.None, CultureInfo.InvariantCulture, out var u)) l.Add(u);
        return l;
    }

    // En-têtes From/Subject d'une réponse FETCH (pliage RFC 5322 et mots encodés RFC 2047 décodés).
    public static (string De, string Sujet) EnTetes(IEnumerable<string> lignes)
    {
        string de = "", sujet = "";
        var texte = string.Join("\n", lignes);
        var deplie = Regex.Replace(texte, @"\r?\n[ \t]+", " ");
        foreach (var l in deplie.Split('\n'))
        {
            if (l.StartsWith("From:", StringComparison.OrdinalIgnoreCase)) de = Decoder(l[5..].Trim());
            else if (l.StartsWith("Subject:", StringComparison.OrdinalIgnoreCase)) sujet = Decoder(l[8..].Trim());
        }
        return (de, sujet);
    }

    // « =?UTF-8?B?…?= » et « =?iso-8859-1?Q?…?= » → texte.
    public static string Decoder(string s)
    {
        var r = Regex.Replace(s, @"=\?([^?]+)\?([BbQq])\?([^?]*)\?=(\s+(?==\?))?", m =>
        {
            Encoding enc;
            try
            {
                enc = Encoding.GetEncoding(m.Groups[1].Value);
            }
            catch (ArgumentException)
            {
                enc = Encoding.UTF8;
            }
            byte[] octets;
            if (m.Groups[2].Value is "B" or "b")
            {
                try
                {
                    octets = Convert.FromBase64String(m.Groups[3].Value);
                }
                catch (FormatException)
                {
                    return m.Value;
                }
            }
            else
            {
                var q = m.Groups[3].Value.Replace('_', ' ');
                var b = new List<byte>();
                for (int i = 0; i < q.Length; i++)
                {
                    if (q[i] == '=' && i + 2 < q.Length && int.TryParse(q.AsSpan(i + 1, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var h))
                    {
                        b.Add((byte)h);
                        i += 2;
                    }
                    else b.AddRange(Encoding.ASCII.GetBytes(q[i].ToString()));
                }
                octets = b.ToArray();
            }
            return enc.GetString(octets);
        });
        return r.Trim();
    }

    // « Léa Martin <lea@exemple.fr> » → (« Léa Martin », « lea@exemple.fr »).
    public static (string Nom, string Adresse) Expediteur(string de)
    {
        var m = Regex.Match(de, @"^\s*""?([^""<]*?)""?\s*<([^>]+)>");
        if (m.Success) return (m.Groups[1].Value.Trim() is { Length: > 0 } n ? n : m.Groups[2].Value, m.Groups[2].Value.Trim());
        return (de.Trim(), de.Trim());
    }
}

// ------------------------------------------------------------------------------------------------------
// Mail : Pilou facteur. IMAP sur TLS avec un mot de passe d'application ; seuls l'expéditeur et le sujet des
// nouveaux mails sont lus (jamais le corps), et rien n'est marqué comme lu.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurMail : Connecteur
{
    public override string Id => "mail";
    public override string Nom => "Mail";
    public override string Description =>
        "Un nouveau mail : Pilou enfile sa casquette de facteur. Il lit seulement l'expéditeur et le sujet (jamais le contenu), " +
        "sans rien marquer comme lu.";
    public override string Signe => "✉";
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(3);

    public override string Aide =>
        "Il faut un « mot de passe d'application » (ton mot de passe habituel ne marche pas, et c'est mieux ainsi) :\n" +
        "• Gmail : active la validation en deux étapes, puis myaccount.google.com/apppasswords → crée « Pilou ». Serveur imap.gmail.com.\n" +
        "• iCloud : appleid.apple.com → Mots de passe pour app. Serveur imap.mail.me.com.\n" +
        "• Fastmail, Proton (Bridge), OVH, Infomaniak… : mot de passe d'application ou IMAP du fournisseur.\n" +
        "• Outlook.com / Microsoft 365 : Microsoft a coupé l'IMAP par mot de passe ; seuls certains comptes pro l'autorisent encore.\n" +
        "Port 993 (TLS). Le mot de passe est chiffré sur ce PC.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("serveur", "Serveur IMAP", TypeReglage.Texte, "ex. imap.gmail.com", "imap.gmail.com"),
        new ReglageConnecteur("port", "Port", TypeReglage.Texte, "993 (TLS)", "993"),
        new ReglageConnecteur("utilisateur", "Adresse mail", TypeReglage.Texte),
        new ReglageConnecteur("motdepasse", "Mot de passe d'application", TypeReglage.Secret),
        new ReglageConnecteur("importants", "Expéditeurs importants", TypeReglage.Texte, "adresses ou domaines, séparés par des virgules"),
        new ReglageConnecteur("seulement", "Seulement les importants", TypeReglage.Case, "", "non"),
        new ReglageConnecteur("masquer", "Masquer le sujet", TypeReglage.Case, "", "non"),
        new ReglageConnecteur("curseur", "", TypeReglage.Texte, Visible: false),
    };

    public override string? Manque(ContexteConnecteur ctx) =>
        ctx.Lire("utilisateur") == "" || ctx.Lire("motdepasse") == "" ? "adresse et mot de passe d'application" : null;

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        int port = int.TryParse(ctx.Lire("port"), out var p) ? p : 993;
        using var tcp = new TcpClient();
        using var delai = CancellationTokenSource.CreateLinkedTokenSource(ct);
        delai.CancelAfter(TimeSpan.FromSeconds(30));
        await tcp.ConnectAsync(ctx.Lire("serveur").Trim(), port, delai.Token);
        await using var ssl = new SslStream(tcp.GetStream());
        await ssl.AuthenticateAsClientAsync(ctx.Lire("serveur").Trim());
        foreach (var e in await Relever(new ClientImap(ssl), ctx, delai.Token)) ctx.Emettre(e);
    }

    // Toute la conversation IMAP, testable avec un flux enregistré.
    public async Task<List<EvenementPilou>> Relever(ClientImap imap, ContexteConnecteur ctx, CancellationToken ct)
    {
        var sortie = new List<EvenementPilou>();
        await imap.Accueil(ct);
        await imap.Commande($"LOGIN {ClientImap.Quoter(ctx.Lire("utilisateur").Trim())} {ClientImap.Quoter(ctx.Lire("motdepasse"))}", ct);
        try
        {
            var boite = await imap.Commande("EXAMINE INBOX", ct);
            long validite = ClientImap.UidValidite(boite), suivant = ClientImap.UidSuivant(boite);
            var uids = ClientImap.Uids(await imap.Commande("UID SEARCH UNSEEN", ct));
            var (validiteVue, dernier) = Curseur(ctx.Lire("curseur"));
            long max = uids.Count > 0 ? uids.Max() : 0;
            if (validiteVue != validite)
            {
                // Première fois (ou boîte réindexée) : un seul résumé, pas un mail par mail ; le curseur part
                // du dernier mail existant, lu ou non.
                if (validiteVue == 0 && uids.Count > 0)
                    sortie.Add(new EvenementPilou(Id, "notification", $"📬 {uids.Count} mail{(uids.Count > 1 ? "s" : "")} non lu{(uids.Count > 1 ? "s" : "")}", ""));
                ctx.Ecrire("curseur", $"{validite}:{Math.Max(max, suivant - 1)}");
                return sortie;
            }
            else
            {
                var importants = Liste(ctx.Lire("importants"));
                foreach (var uid in uids.Where(u => u > dernier).OrderByDescending(u => u).Take(5).Reverse())
                {
                    var (de, sujet) = ClientImap.EnTetes(await imap.Commande($"UID FETCH {uid} (BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])", ct));
                    var (nom, adresse) = ClientImap.Expediteur(de);
                    bool important = importants.Any(i => adresse.EndsWith(i.TrimStart('@'), StringComparison.OrdinalIgnoreCase));
                    if (Oui(ctx.Lire("seulement")) && !important) continue;
                    sortie.Add(new EvenementPilou(Id, "notification", $"✉ {Court(nom, 40)}",
                        Oui(ctx.Lire("masquer")) ? "nouveau mail" : Court(sujet, 100), important ? 1 : 0,
                        0, new Dictionary<string, string> { ["tenue"] = "mail" }));
                }
            }
            ctx.Ecrire("curseur", $"{validite}:{Math.Max(max, dernier)}");
        }
        finally
        {
            try
            {
                await imap.Commande("LOGOUT", ct);
            }
            catch (IOException)
            {
                // le serveur ferme souvent sans attendre
            }
        }
        return sortie;
    }

    private static (long Validite, long Dernier) Curseur(string s)
    {
        var p = s.Split(':');
        return p.Length == 2 && long.TryParse(p[0], out var v) && long.TryParse(p[1], out var d) ? (v, d) : (0, 0);
    }
}
