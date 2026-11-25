using System.IO;
using System.Security.Cryptography;
using System.Text.Json;

namespace PilouBureau;

// Groupe d'appareils : l'XP partagée entre des PC qui n'ont pas de dossier commun (PC perso, PC de
// travail…), par le relais ntfy chiffré. Le code du groupe est le code d'appairage (Reglages.Telephone) :
// un seul code pour les PC et le téléphone.
//
// Compteur G : chaque appareil publie SON compteur (qui ne fait que monter) ; chacun garde, pour chaque
// autre appareil, la plus grande valeur reçue ; le total est la somme. Ordre d'arrivée, doublons et
// retards n'y changent rien. Les gains du téléphone (canal retour) sont crédités par chaque PC du groupe
// dans un compteur à part (XpTelephone) : on en prend le maximum, jamais la somme.
public static class Groupe
{
    public static string Sujet(string code) =>
        "pilou-" + Convert.ToHexString(HMACSHA256.HashData(
            System.Text.Encoding.UTF8.GetBytes(Telephone.Normaliser(code)),
            System.Text.Encoding.UTF8.GetBytes("pilou-groupe-v1"))).ToLowerInvariant()[..24];

    public sealed record Compteur(
        string Appareil, string Nom, string Machine, int Xp, int XpTelephone, double T,
        IReadOnlyList<string> Prises, IReadOnlyList<string> Plats);

    // Mémoire locale du groupe (groupe.json, dans le dossier de Pilou, jamais dans le dossier partagé).
    public sealed class Memoire
    {
        public Dictionary<string, Compteur> Autres { get; set; } = new();
        public string Depuis { get; set; } = "";

        public IEnumerable<Compteur> Compteurs => Autres.Values;

        private static readonly JsonSerializerOptions Options = new() { WriteIndented = true };

        public static string Chemin(string dossier) => Path.Combine(dossier, "groupe.json");

        public static Memoire Lire(string dossier)
        {
            try
            {
                var c = Chemin(dossier);
                if (File.Exists(c)) return JsonSerializer.Deserialize<Memoire>(File.ReadAllText(c), Options) ?? new();
            }
            catch (Exception e) when (e is IOException or JsonException or UnauthorizedAccessException)
            {
                // illisible : on repart de zéro, les autres republient toutes les heures
            }
            return new();
        }

        public void Ecrire(string dossier)
        {
            try
            {
                Directory.CreateDirectory(dossier);
                var tmp = Chemin(dossier) + ".tmp";
                File.WriteAllText(tmp, JsonSerializer.Serialize(this, Options));
                File.Move(tmp, Chemin(dossier), true);
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException)
            {
                // gardé en mémoire
            }
        }

        // Fusion d'un compteur reçu : maximum par appareil, union des découvertes. Le sien est ignoré.
        // Renvoie true si quelque chose a changé.
        public bool Fusionner(Compteur c, string moi)
        {
            if (c.Appareil == "" || c.Appareil == moi) return false;
            if (!Autres.TryGetValue(c.Appareil, out var avant))
            {
                Autres[c.Appareil] = c;
                return true;
            }
            var fusion = avant with
            {
                Nom = c.T >= avant.T ? c.Nom : avant.Nom,
                Machine = c.T >= avant.T ? c.Machine : avant.Machine,
                Xp = Math.Max(avant.Xp, c.Xp),
                XpTelephone = Math.Max(avant.XpTelephone, c.XpTelephone),
                T = Math.Max(avant.T, c.T),
                Prises = avant.Prises.Union(c.Prises).OrderBy(x => x).ToList(),
                Plats = avant.Plats.Union(c.Plats).OrderBy(x => x).ToList(),
            };
            bool change = fusion.Xp != avant.Xp || fusion.XpTelephone != avant.XpTelephone || fusion.T != avant.T
                          || fusion.Prises.Count != avant.Prises.Count || fusion.Plats.Count != avant.Plats.Count || fusion.Nom != avant.Nom;
            Autres[c.Appareil] = fusion;
            return change;
        }

        public void Oublier()
        {
            Autres.Clear();
            Depuis = "";
        }
    }

    // ---- Messages

    public static Compteur Moi(Profil p, string appareil, string nom) => new(
        appareil, nom, p.Machine, p.Xp, p.XpTelephone, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
        p.Carnet.Where(kv => kv.Value > 0).Select(kv => kv.Key).OrderBy(x => x).ToList(),
        p.Plats.Where(x => !x.StartsWith("inv:")).OrderBy(x => x).ToList());

    public static string Json(Compteur c) => JsonSerializer.Serialize(new Dictionary<string, object>
    {
        ["v"] = 1, ["appareil"] = c.Appareil, ["nom"] = c.Nom, ["machine"] = c.Machine, ["xp"] = c.Xp,
        ["xpTel"] = c.XpTelephone, ["t"] = c.T, ["prises"] = c.Prises, ["plats"] = c.Plats,
    });

    public static Compteur? Lire(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            var r = doc.RootElement;
            string S(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";
            int N(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out var n) ? Math.Max(0, n) : 0;
            List<string> L(string k, int max) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Array
                ? v.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.String).Select(x => x.GetString()!)
                    .Where(x => x.Length is > 0 and < 120).Distinct().Take(max).ToList()
                : new List<string>();
            var appareil = S("appareil");
            if (appareil == "" || appareil.Length > 64) return null;
            double t = r.TryGetProperty("t", out var tv) && tv.ValueKind == JsonValueKind.Number ? tv.GetDouble() : 0;
            var nom = S("nom");
            return new Compteur(appareil, nom.Length > 40 ? nom[..40] : nom, S("machine"), N("xp"), N("xpTel"), t, L("prises", 100), L("plats", 200));
        }
        catch (JsonException)
        {
            return null;
        }
    }

    // Réponse de ntfy (une ligne JSON par événement) → compteurs déchiffrés, et dernier identifiant vu.
    public static (List<Compteur> Compteurs, string Dernier) LireMessages(string code, string texte)
    {
        var liste = new List<Compteur>();
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
                if (Lire(Telephone.Dechiffrer(code, m.GetString() ?? "")) is { } c) liste.Add(c);
            }
            catch (Exception e) when (e is JsonException or FormatException or CryptographicException or ArgumentException)
            {
                // illisible ou d'un autre groupe : ignoré
            }
        }
        return (liste, dernier);
    }

    // ---- Le total

    // XP de tout le groupe : ce PC, les PC du dossier partagé et ceux du relais. Un même PC vu des deux
    // côtés (dossier et relais) compte une fois, à sa plus grande valeur. Le téléphone : le maximum des
    // XpTelephone, parce que chaque PC du groupe crédite les mêmes gains du téléphone.
    public static int Total(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe)
    {
        var parMachine = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        int tel = Math.Max(0, moi.XpTelephone);
        foreach (var p in dossier)
        {
            if (string.Equals(p.Machine, moi.Machine, StringComparison.OrdinalIgnoreCase)) continue;
            parMachine[p.Machine] = Math.Max(parMachine.GetValueOrDefault(p.Machine), Math.Max(0, p.Xp));
            tel = Math.Max(tel, p.XpTelephone);
        }
        foreach (var c in groupe)
        {
            var cle = c.Machine == "" ? "appareil:" + c.Appareil : c.Machine;
            if (string.Equals(cle, moi.Machine, StringComparison.OrdinalIgnoreCase)) continue;
            parMachine[cle] = Math.Max(parMachine.GetValueOrDefault(cle), c.Xp);
            tel = Math.Max(tel, c.XpTelephone);
        }
        return Math.Max(0, moi.Xp) + parMachine.Values.Sum() + tel;
    }

    // « vu il y a 3 min » pour les menus.
    public static string VuIlYa(double t, double maintenant) => t <= 0 ? "jamais vu" : $"vu il y a {Statut.Duree(maintenant - t)}";
}
