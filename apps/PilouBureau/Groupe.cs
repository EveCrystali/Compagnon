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
        IReadOnlyList<string> Prises, IReadOnlyList<string> Plats,
        int PoGagnes = 0, int PoDepenses = 0, int PoDepTel = 0,
        IReadOnlyList<string>? Inventaire = null, IReadOnlyDictionary<string, Port>? Equipe = null, int NiveauPaye = 0, int NiveauAcquis = 0,
        EtatSoins? SoinsBase = null, string SoinsOrigine = "", IReadOnlyList<ActionSoin>? SoinsActions = null,
        IReadOnlyDictionary<int, string>? Variantes = null,
        string ExpJour = "", int ExpNombre = 0, double ExpLibre = 0)
    {
        public IReadOnlyList<ActionSoin> Actions => SoinsActions ?? Array.Empty<ActionSoin>();
        public IReadOnlyDictionary<int, string> Formes => Variantes ?? new Dictionary<int, string>();
        public IReadOnlyList<string> Objets => Inventaire ?? Array.Empty<string>();
        public IReadOnlyDictionary<string, Port> Porte => Equipe ?? new Dictionary<string, Port>();
    }

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
                PoGagnes = Math.Max(avant.PoGagnes, c.PoGagnes),
                PoDepenses = Math.Max(avant.PoDepenses, c.PoDepenses),
                PoDepTel = Math.Max(avant.PoDepTel, c.PoDepTel),
                Inventaire = avant.Objets.Union(c.Objets).OrderBy(x => x).ToList(),
                Equipe = Bourse.FusionEquipe(new[] { avant.Porte, c.Porte }),
                NiveauPaye = Math.Max(avant.NiveauPaye, c.NiveauPaye),
                NiveauAcquis = Math.Max(avant.NiveauAcquis, c.NiveauAcquis),
                SoinsBase = c.SoinsBase ?? avant.SoinsBase,
                SoinsOrigine = c.SoinsBase is not null ? c.SoinsOrigine : avant.SoinsOrigine,
                SoinsActions = avant.Actions.Concat(c.Actions).GroupBy(a => a.Id).Select(g => g.First())
                    .OrderByDescending(a => a.T).Take(40).ToList(),
                Variantes = FusionVariantes(new[] { avant.Formes, c.Formes }),
                // Expéditions : départs du jour le plus récent (au maximum), fin de repos la plus tardive.
                ExpJour = string.CompareOrdinal(c.ExpJour, avant.ExpJour) > 0 ? c.ExpJour : avant.ExpJour,
                ExpNombre = c.ExpJour == avant.ExpJour ? Math.Max(c.ExpNombre, avant.ExpNombre)
                    : string.CompareOrdinal(c.ExpJour, avant.ExpJour) > 0 ? c.ExpNombre : avant.ExpNombre,
                ExpLibre = Math.Max(avant.ExpLibre, c.ExpLibre),
            };
            bool change = fusion.Xp != avant.Xp || fusion.XpTelephone != avant.XpTelephone || fusion.T != avant.T
                          || fusion.PoGagnes != avant.PoGagnes || fusion.PoDepenses != avant.PoDepenses || fusion.PoDepTel != avant.PoDepTel
                          || fusion.Objets.Count != avant.Objets.Count || fusion.NiveauAcquis != avant.NiveauAcquis
                          || fusion.Prises.Count != avant.Prises.Count || fusion.Plats.Count != avant.Plats.Count || fusion.Nom != avant.Nom
                          || fusion.Actions.Count != avant.Actions.Count || fusion.Formes.Count != avant.Formes.Count
                          || (fusion.SoinsBase?.T ?? 0) != (avant.SoinsBase?.T ?? 0)
                          || fusion.ExpJour != avant.ExpJour || fusion.ExpNombre != avant.ExpNombre || fusion.ExpLibre != avant.ExpLibre;
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

    // Variantes d'évolution : la première décision l'emporte ; deux décisions différentes au même stade
    // (deux PC en même temps) se départagent par l'ordre alphabétique, partout pareil.
    public static Dictionary<int, string> FusionVariantes(IEnumerable<IReadOnlyDictionary<int, string>> toutes)
    {
        var r = new Dictionary<int, string>();
        foreach (var v in toutes)
            foreach (var (stade, forme) in v)
                if (forme is "calin" or "espiegle" && (!r.TryGetValue(stade, out var avant) || string.CompareOrdinal(forme, avant) < 0))
                    r[stade] = forme;
        return r;
    }

    public static Compteur Moi(Profil p, string appareil, string nom) => new(
        appareil, nom, p.Machine, p.Xp, p.XpTelephone, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
        p.Carnet.Where(kv => kv.Value > 0).Select(kv => kv.Key).OrderBy(x => x).ToList(),
        p.Plats.Where(x => !x.StartsWith("inv:")).OrderBy(x => x).ToList(),
        p.Bourse.PoGagnes, p.Bourse.PoDepenses, p.Bourse.PoDepTelephone,
        p.Bourse.Inventaire.OrderBy(x => x).ToList(), new Dictionary<string, Port>(p.Bourse.Equipe), p.Evolution.NiveauPaye,
        p.Evolution.NiveauAcquis, p.Soins.Base, p.Soins.Origine, Soins.Recentes(p.Soins, 12), new Dictionary<int, string>(p.Evolution.Variantes),
        p.Expedition.Jour, p.Expedition.Nombre, p.Expedition.Libre);

    // Un message ntfy reste sous 4 096 octets une fois chiffré : on retire des actions de soin récentes au besoin.
    public static string Json(Compteur c)
    {
        var actions = c.Actions.ToList();
        while (true)
        {
            var json = JsonBrut(c with { SoinsActions = actions });
            if (json.Length <= 2600 || actions.Count == 0) return json;
            actions.RemoveAt(actions.Count - 1);
        }
    }

    private static string JsonBrut(Compteur c) => JsonSerializer.Serialize(new Dictionary<string, object>
    {
        ["soins"] = c.SoinsBase is null ? new Dictionary<string, object>() : new Dictionary<string, object>
        {
            ["base"] = Soins.JsonEtat(c.SoinsBase), ["o"] = c.SoinsOrigine, ["a"] = c.Actions.Select(Soins.JsonAction).ToList(),
        },
        ["exp"] = new Dictionary<string, object> { ["j"] = c.ExpJour, ["n"] = c.ExpNombre, ["l"] = c.ExpLibre },
        ["formes"] = c.Formes.ToDictionary(kv => kv.Key.ToString(System.Globalization.CultureInfo.InvariantCulture), kv => kv.Value),
        ["v"] = 1, ["appareil"] = c.Appareil, ["nom"] = c.Nom, ["machine"] = c.Machine, ["xp"] = c.Xp,
        ["xpTel"] = c.XpTelephone, ["t"] = c.T, ["prises"] = c.Prises, ["plats"] = c.Plats,
        ["po"] = c.PoGagnes, ["poDep"] = c.PoDepenses, ["poDepTel"] = c.PoDepTel, ["objets"] = c.Objets, ["nivPaye"] = c.NiveauPaye, ["nivAcquis"] = c.NiveauAcquis,
        ["equipe"] = c.Porte.ToDictionary(kv => kv.Key, kv => new Dictionary<string, object> { ["id"] = kv.Value.Id, ["t"] = kv.Value.T }),
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
            var equipe = new Dictionary<string, Port>();
            if (r.TryGetProperty("equipe", out var eq) && eq.ValueKind == JsonValueKind.Object)
                foreach (var x in eq.EnumerateObject())
                {
                    if (!Boutique.Slots.Contains(x.Name) || x.Value.ValueKind != JsonValueKind.Object) continue;
                    var id = x.Value.TryGetProperty("id", out var iv) && iv.ValueKind == JsonValueKind.String ? iv.GetString() ?? "" : "";
                    double te = x.Value.TryGetProperty("t", out var tv2) && tv2.ValueKind == JsonValueKind.Number ? tv2.GetDouble() : 0;
                    if (id == "" || Boutique.Trouver(id)?.Slot == x.Name) equipe[x.Name] = new Port(id, te);
                }
            EtatSoins? soinsBase = null;
            string origine = "";
            var actions = new List<ActionSoin>();
            if (r.TryGetProperty("soins", out var so) && so.ValueKind == JsonValueKind.Object)
            {
                if (so.TryGetProperty("base", out var sb)) soinsBase = Soins.LireEtat(sb);
                if (so.TryGetProperty("o", out var sorig) && sorig.ValueKind == JsonValueKind.String) origine = sorig.GetString() ?? "";
                if (so.TryGetProperty("a", out var sa)) actions = Soins.LireActions(sa, 40);
                if (origine.Length > 64) origine = "";
            }
            var formes = new Dictionary<int, string>();
            if (r.TryGetProperty("formes", out var fo) && fo.ValueKind == JsonValueKind.Object)
                foreach (var x in fo.EnumerateObject())
                    if (int.TryParse(x.Name, out var st) && st is >= 2 and <= 4 && x.Value.ValueKind == JsonValueKind.String
                        && x.Value.GetString() is "calin" or "espiegle")
                        formes[st] = x.Value.GetString()!;
            string expJour = "";
            int expNombre = 0;
            double expLibre = 0;
            if (r.TryGetProperty("exp", out var ex) && ex.ValueKind == JsonValueKind.Object)
            {
                if (ex.TryGetProperty("j", out var ej) && ej.ValueKind == JsonValueKind.String && ej.GetString() is { Length: <= 10 } jour) expJour = jour;
                if (ex.TryGetProperty("n", out var en) && en.ValueKind == JsonValueKind.Number && en.TryGetInt32(out var nb)) expNombre = Math.Clamp(nb, 0, 10);
                if (ex.TryGetProperty("l", out var el) && el.ValueKind == JsonValueKind.Number) expLibre = Math.Max(0, el.GetDouble());
            }
            return new Compteur(appareil, nom.Length > 40 ? nom[..40] : nom, S("machine"), N("xp"), N("xpTel"), t, L("prises", 100), L("plats", 200),
                N("po"), N("poDep"), N("poDepTel"), L("objets", 100).Where(x => Boutique.Trouver(x) is not null).ToList(), equipe, N("nivPaye"), Math.Min(200, N("nivAcquis")),
                soinsBase, origine, actions, formes, expJour, expNombre, expLibre);
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

    // Pièces d'or du groupe : Σ (gains − dépenses) par appareil (chacun à sa plus grande valeur vue), moins
    // les achats faits sur le téléphone (comptés au maximum : chaque PC du groupe les applique).
    public static int SoldePo(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe)
    {
        var gains = new Dictionary<string, (int G, int D)>(StringComparer.OrdinalIgnoreCase);
        int tel = moi.Bourse.PoDepTelephone;
        void Voir(string cle, int g, int d)
        {
            if (string.Equals(cle, moi.Machine, StringComparison.OrdinalIgnoreCase)) return;
            var avant = gains.GetValueOrDefault(cle);
            gains[cle] = (Math.Max(avant.G, g), Math.Max(avant.D, d));
        }
        foreach (var p in dossier)
        {
            Voir(p.Machine, p.Bourse.PoGagnes, p.Bourse.PoDepenses);
            tel = Math.Max(tel, p.Bourse.PoDepTelephone);
        }
        foreach (var c in groupe)
        {
            Voir(c.Machine == "" ? "appareil:" + c.Appareil : c.Machine, c.PoGagnes, c.PoDepenses);
            tel = Math.Max(tel, c.PoDepTel);
        }
        return moi.Bourse.PoGagnes - moi.Bourse.PoDepenses + gains.Values.Sum(x => x.G - x.D) - tel;
    }

    // Objets possédés par le groupe (union) et ce que Pilou porte (dernière écriture gagne par emplacement).
    public static List<string> Inventaire(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe) =>
        moi.Bourse.Inventaire.Concat(dossier.SelectMany(p => p.Bourse.Inventaire)).Concat(groupe.SelectMany(c => c.Objets))
            .Distinct().OrderBy(x => x).ToList();

    public static Dictionary<string, Port> Equipe(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe) =>
        Bourse.FusionEquipe(new[] { (IReadOnlyDictionary<string, Port>)moi.Bourse.Equipe }
            .Concat(dossier.Select(p => (IReadOnlyDictionary<string, Port>)p.Bourse.Equipe))
            .Concat(groupe.Select(c => c.Porte)));

    // « vu il y a 3 min » pour les menus.
    public static string VuIlYa(double t, double maintenant) => t <= 0 ? "jamais vu" : $"vu il y a {Statut.Duree(maintenant - t)}";
}
