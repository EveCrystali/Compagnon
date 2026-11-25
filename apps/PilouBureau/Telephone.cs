using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace PilouBureau;

// Pilou sur le téléphone : l'overlay publie l'état des sessions sur un relais ntfy, chiffré de bout
// en bout. Le code d'appairage (16 caractères) donne à la fois le sujet ntfy et la clé AES-256-GCM :
// le relais ne voit qu'un texte illisible, et qui ne connaît pas le code ne trouve même pas le sujet.
// L'app Android (android/) fait exactement le même calcul (Chiffre.java).
public static class Telephone
{
    public const string RelaisParDefaut = "https://ntfy.sh";
    // ntfy transforme un message de plus de 4 096 octets en pièce jointe : on reste en dessous.
    public const int TailleMax = 3800;
    private const string Alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"; // sans 0/O, 1/I/L

    public static string NouveauCode()
    {
        var c = new char[16];
        for (int i = 0; i < c.Length; i++) c[i] = Alphabet[RandomNumberGenerator.GetInt32(Alphabet.Length)];
        return Formater(new string(c));
    }

    // « abcd efgh-… » → « ABCDEFGH… » (16 caractères utiles).
    public static string Normaliser(string code) =>
        new string(code.ToUpperInvariant().Where(ch => Alphabet.Contains(ch)).ToArray());

    public static string Formater(string code)
    {
        var n = Normaliser(code);
        return string.Join("-", Enumerable.Range(0, (n.Length + 3) / 4).Select(i => n.Substring(i * 4, Math.Min(4, n.Length - i * 4))));
    }

    public static bool Valide(string code) => Normaliser(code).Length == 16;

    private static byte[] Hmac(string code, string usage) =>
        HMACSHA256.HashData(Encoding.UTF8.GetBytes(Normaliser(code)), Encoding.UTF8.GetBytes(usage));

    public static string Sujet(string code) => "pilou-" + Convert.ToHexString(Hmac(code, "pilou-sujet-v1")).ToLowerInvariant()[..24];

    public static byte[] Cle(string code) => Hmac(code, "pilou-cle-v1");

    // base64(nonce 12 octets ‖ chiffré ‖ étiquette 16 octets) : la disposition de javax.crypto « AES/GCM/NoPadding ».
    public static string Chiffrer(string code, string texte, byte[]? nonce = null)
    {
        nonce ??= RandomNumberGenerator.GetBytes(12);
        var clair = Encoding.UTF8.GetBytes(texte);
        var chiffre = new byte[clair.Length];
        var etiquette = new byte[16];
        using (var aes = new AesGcm(Cle(code), 16)) aes.Encrypt(nonce, clair, chiffre, etiquette);
        return Convert.ToBase64String([.. nonce, .. chiffre, .. etiquette]);
    }

    public static string Dechiffrer(string code, string message)
    {
        var tout = Convert.FromBase64String(message);
        var clair = new byte[tout.Length - 28];
        using (var aes = new AesGcm(Cle(code), 16)) aes.Decrypt(tout[..12], tout[12..^16], tout[^16..], clair);
        return Encoding.UTF8.GetString(clair);
    }

    public static string Lien(string code, string relais) =>
        $"pilou://appairer?c={Normaliser(code)}" + (relais == RelaisParDefaut ? "" : $"&s={Uri.EscapeDataString(relais)}");

    // ---- Ce que voit le téléphone

    public sealed record SessionTel(string Id, string Source, string Libelle, string Etat, double Depuis, string Outil);

    // Une session réduite à ce qu'affiche le téléphone : permission, question, travail, fini, interrompu, erreur, calme.
    public static SessionTel Resumer(EtatSession e, double maintenant)
    {
        var lib = e.Libelle == "" ? e.Session : e.Libelle;
        if (lib.Length > 40) lib = lib[..39] + "…";
        string etat;
        double depuis;
        if (e.Attente != "") (etat, depuis) = (e.Attente == "question" ? "question" : "permission", e.DebutOutil);
        else if (e.EnTour) (etat, depuis) = ("travail", e.DebutTour);
        else if (e.FinTour > 0 && maintenant - e.FinTour < Statut.FiniVisible)
            (etat, depuis) = (e.FinRaison switch { "interrompu" => "interrompu", "erreur" => "erreur", _ => "fini" }, e.FinTour);
        else (etat, depuis) = ("calme", e.FinTour);
        return new SessionTel(e.Session, e.Source, lib, etat, depuis, e.EnTour ? e.Outil : "");
    }

    private static int Rang(string etat) => etat switch
    {
        "permission" or "question" => 0, "travail" => 1, "fini" or "erreur" or "interrompu" => 2, _ => 3,
    };

    public static List<SessionTel> Sessions(IEnumerable<EtatSession> vivantes, double maintenant) =>
        vivantes.Select(e => Resumer(e, maintenant))
            .Where(s => s.Etat != "calme")
            .OrderBy(s => Rang(s.Etat)).ThenByDescending(s => s.Depuis)
            .Take(8).ToList();

    // Ce qui mérite un message : un changement d'état (l'outil en cours et les durées, non :
    // le téléphone les calcule lui-même, et le relais gratuit limite le nombre de messages).
    public static string Signature(IReadOnlyList<SessionTel> sessions, int niveau, string humeur, string extra = "") =>
        $"{niveau}|{humeur}|{extra}|" + string.Join(";", sessions.Select(s => $"{s.Id}:{s.Etat}:{s.Depuis}"));

    // plus : champs optionnels (xp, accessoire, carnet, plats, recus…) ; un ancien téléphone les ignore.
    public static string Charge(IReadOnlyList<SessionTel> sessions, double maintenant, string nom, int niveau, string titre,
        string couleur, string humeur, int calmes, IReadOnlyDictionary<string, object>? plus = null)
    {
        var d = new Dictionary<string, object>
        {
            ["v"] = 1,
            ["t"] = maintenant,
            ["nom"] = nom,
            ["niveau"] = niveau,
            ["titre"] = titre,
            ["couleur"] = couleur,
            ["humeur"] = humeur,
            ["calmes"] = calmes,
            ["sessions"] = sessions.Select(s => new Dictionary<string, object>
            {
                ["id"] = s.Id, ["source"] = s.Source, ["libelle"] = s.Libelle, ["etat"] = s.Etat, ["depuis"] = s.Depuis, ["outil"] = s.Outil,
            }).ToList(),
        };
        if (plus is not null)
            foreach (var (k, v) in plus) d[k] = v;
        return JsonSerializer.Serialize(d);
    }

    // Ce que le PC dit de la progression au téléphone : XP, accessoire porté, carnet et livre de recettes,
    // et les derniers gains du téléphone qu'il a crédités (le téléphone les retire de sa file d'attente).
    public static Dictionary<string, object> Progression(Profil p, int xpTotal, string accessoire) => new()
    {
        ["xp"] = xpTotal,
        ["accessoire"] = accessoire,
        ["carnet"] = p.Carnet.Where(kv => kv.Value > 0).Select(kv => kv.Key).OrderBy(k => k).ToList(),
        ["plats"] = p.Plats.Where(x => !x.StartsWith("inv:")).OrderBy(x => x).ToList(),
        ["inventes"] = p.Plats.Count(x => x.StartsWith("inv:")),
        ["recus"] = p.Recus.TakeLast(10).ToList(),
        // Métiers (niveau par métier) et succès obtenus : pour un futur affichage sur le téléphone.
        ["metiers"] = Metiers.Niveaux(p.Activites).Where(kv => kv.Value > 0).ToDictionary(kv => kv.Key, kv => kv.Value),
        ["succes"] = p.Succes.ToList(),
        // Soins : l'état calculé maintenant (le téléphone y ajoute ses propres soins pas encore reçus ici)
        // et les variantes d'évolution.
        ["soins"] = Soins.JsonEtat(Soins.Etat(p.Soins, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds())),
        ["formes"] = p.Evolution.Variantes.ToDictionary(kv => kv.Key.ToString(System.Globalization.CultureInfo.InvariantCulture), kv => kv.Value),
    };

    // ---- Retour : ce que le téléphone a gagné (atelier : pêche, cuisine, jeux, caresses)

    // Deuxième sujet, tiré du même code : le téléphone y publie, le PC y lit.
    public static string SujetRetour(string code) => "pilou-" + Convert.ToHexString(Hmac(code, "pilou-retour-v1")).ToLowerInvariant()[..24];

    public sealed record Gain(string Id, int Xp, IReadOnlyDictionary<string, int> Prises, IReadOnlyList<string> Plats, int Caresses,
        int Jeux = 0, int Chasse = 0, IReadOnlyList<string>? Achats = null, IReadOnlyDictionary<string, string>? Equipe = null, double T = 0,
        IReadOnlyList<ActionSoin>? Soins = null);

    public static Gain? LireGain(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            if (!r.TryGetProperty("id", out var id) || id.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(id.GetString())) return null;
            int Entier(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out var n) ? n : 0;
            var prises = new Dictionary<string, int>();
            if (r.TryGetProperty("prises", out var pr) && pr.ValueKind == JsonValueKind.Object)
                foreach (var x in pr.EnumerateObject())
                    if (x.Value.ValueKind == JsonValueKind.Number && x.Value.TryGetInt32(out var n) && n > 0 && Butin.Trouver(x.Name) is not null)
                        prises[x.Name] = Math.Min(n, 50);
            var plats = new List<string>();
            if (r.TryGetProperty("plats", out var pl) && pl.ValueKind == JsonValueKind.Array)
                foreach (var x in pl.EnumerateArray())
                    if (x.ValueKind == JsonValueKind.String && x.GetString() is { Length: > 0 and < 120 } nom) plats.Add(nom);
            var achats = new List<string>();
            if (r.TryGetProperty("achats", out var ac) && ac.ValueKind == JsonValueKind.Array)
                foreach (var x in ac.EnumerateArray())
                    if (x.ValueKind == JsonValueKind.String && Boutique.Trouver(x.GetString() ?? "") is not null) achats.Add(x.GetString()!);
            var equipe = new Dictionary<string, string>();
            if (r.TryGetProperty("equipe", out var eq) && eq.ValueKind == JsonValueKind.Object)
                foreach (var x in eq.EnumerateObject())
                    if (Boutique.Slots.Contains(x.Name) && x.Value.ValueKind == JsonValueKind.String) equipe[x.Name] = x.Value.GetString() ?? "";
            double t = r.TryGetProperty("t", out var tv) && tv.ValueKind == JsonValueKind.Number ? tv.GetDouble() : 0;
            var soins = r.TryGetProperty("soins", out var so) ? PilouBureau.Soins.LireActions(so, 50) : new List<ActionSoin>();
            // Bornes : un message vient du téléphone appairé (chiffré), mais on reste prudent.
            return new Gain(id.GetString()!, Math.Clamp(Entier("xp"), 0, 2000), prises, plats.Take(20).ToList(), Math.Clamp(Entier("caresses"), 0, 200),
                Math.Clamp(Entier("jeux"), 0, 100), Math.Clamp(Entier("chasse"), 0, 10_000_000), achats.Distinct().Take(10).ToList(), equipe, t, soins);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    // Réponse de ntfy (une ligne JSON par événement) → gains déchiffrés, et identifiant du dernier message vu.
    public static (List<Gain> Gains, string Dernier) LireRetours(string code, string texte)
    {
        var gains = new List<Gain>();
        string dernier = "";
        foreach (var ligne in texte.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            try
            {
                using var doc = JsonDocument.Parse(ligne);
                var r = doc.RootElement;
                if (r.TryGetProperty("event", out var ev) && ev.GetString() != "message") continue;
                if (r.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.String) dernier = id.GetString() ?? dernier;
                if (!r.TryGetProperty("message", out var m) || m.ValueKind != JsonValueKind.String) continue;
                if (LireGain(Dechiffrer(code, m.GetString() ?? "")) is { } g) gains.Add(g);
            }
            catch (Exception e) when (e is JsonException or FormatException or CryptographicException or ArgumentException)
            {
                // message illisible ou chiffré avec un autre code : ignoré
            }
        }
        return (gains, dernier);
    }

    // Crédite un gain une seule fois (par son identifiant) ; renvoie l'XP ajoutée (0 : déjà reçu).
    public static int Crediter(Profil p, Gain g) => Recevoir(p, g, new Contexte(DateTime.Now, "", 1, 0)).Xp;

    // Ce que le PC sait au moment de créditer : l'heure locale et la graine (quêtes), le niveau et le solde
    // du groupe (achats faits sur le téléphone).
    public sealed record Contexte(DateTime Local, string Graine, int Niveau, int Solde);

    public sealed record Resultat(int Xp, List<RecompenseQuete> Recompenses, List<string> Achetes, List<string> Refus);

    public static Resultat Recevoir(Profil p, Gain g, Contexte ctx)
    {
        var r = new Resultat(0, new List<RecompenseQuete>(), new List<string>(), new List<string>());
        if (p.Recus.Contains(g.Id)) return r;
        p.Recus.Add(g.Id);
        if (p.Recus.Count > 100) p.Recus.RemoveRange(0, p.Recus.Count - 100);
        p.XpTelephone += g.Xp; // à part : chaque PC du groupe crédite les mêmes gains (compté au maximum)
        p.Caresses += g.Caresses;
        int rares = 0, nouveaux = 0;
        foreach (var (id, n) in g.Prises)
        {
            p.Carnet[id] = p.Carnet.GetValueOrDefault(id) + n;
            if (Butin.Trouver(id) is { } x && x.Rarete >= Rarete.Rare) rares += n;
        }
        foreach (var plat in g.Plats)
        {
            p.PlatsCuisines++;
            if (p.Plats.Contains(plat)) continue;
            p.Plats.Add(plat);
            nouveaux++;
        }

        // Quêtes : ce que le téléphone a fait compte comme si c'était ici.
        void S(string cle, int n) => r.Recompenses.AddRange(Quetes.Signaler(p.Quetes, cle, n, ctx.Local, ctx.Graine));
        S("peche", g.Prises.Values.Sum());
        S("peche:rare", rares);
        S("cuisine", g.Plats.Count);
        S("cuisine:nouveau", nouveaux);
        S("caresse", g.Caresses);
        S("jeu", g.Jeux);
        S("chasse", g.Chasse);
        // Soins faits sur le téléphone : ajoutés au journal commun (union, par identifiant).
        int soins = 0;
        foreach (var a in g.Soins ?? Array.Empty<ActionSoin>())
            if (PilouBureau.Soins.Ajouter(p.Soins, a) && a.Type is "soin" or "nourrir" or "laver" or "calin") soins++;
        S("soin", soins);
        var (po, xpQuetes) = Quetes.Appliquer(p, r.Recompenses);

        // Boutique : achats et équipement faits sur le téléphone (le PC reste l'arbitre du solde).
        int solde = ctx.Solde + po;
        var jour = DateOnly.FromDateTime(ctx.Local);
        foreach (var id in g.Achats ?? Array.Empty<string>())
        {
            var avant = p.Bourse.PoDepTelephone;
            var refus = Boutique.Acheter(p.Bourse, id, ctx.Niveau, solde, jour, parTelephone: true);
            if (refus is null)
            {
                solde -= p.Bourse.PoDepTelephone - avant;
                r.Achetes.Add(id);
            }
            else if (!p.Bourse.Inventaire.Contains(id)) r.Refus.Add($"{Boutique.Trouver(id)?.Nom ?? id} : {refus}");
        }
        double t = g.T > 0 ? g.T : DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        foreach (var (slot, id) in g.Equipe ?? new Dictionary<string, string>())
            Boutique.Equiper(p.Bourse, slot, id, t);
        return r with { Xp = g.Xp + xpQuetes };
    }

    // Boutique et quêtes, pour le téléphone (champs facultatifs, compacts : le message reste sous 4 096 octets).
    public static Dictionary<string, object> EtatBoutique(int solde, IEnumerable<string> inventaire, IReadOnlyDictionary<string, Port> equipe,
        EtatQuetes q, DateTime local) => new()
    {
        ["po"] = Math.Max(0, solde),
        ["objets"] = inventaire.ToList(),
        ["porte"] = PilouBureau.Boutique.Porte(equipe),
        ["offres"] = PilouBureau.Boutique.OffresDuJour(DateOnly.FromDateTime(local)).Select(a => a.Id).ToList(),
        ["promo"] = PilouBureau.Boutique.OffresDuJour(DateOnly.FromDateTime(local)).FirstOrDefault()?.Id ?? "",
        ["serie"] = Quetes.Serie(q, local),
        ["quetes"] = q.Liste.Select(x => new object[] { (int)x.Periode, x.Texte, x.Fait, x.Objectif, x.Po, x.Reussie ? 1 : 0 }).ToList(),
    };
}
