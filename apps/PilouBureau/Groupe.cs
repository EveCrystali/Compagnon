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
// Métiers et succès suivent la même règle : chaque appareil publie SES secondes par activité et SES compteurs
// (frappes avec Pilou, captures, présentations, boss de Défense) ; le total du groupe est la somme (Cumuler).
// Records de Défense : le maximum. Succès et grades déjà récompensés : l'union (un seul crédit d'XP).
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
        string ExpJour = "", int ExpNombre = 0, double ExpLibre = 0,
        IReadOnlyDictionary<string, long>? Secondes = null, IReadOnlyList<string>? SuccesObtenus = null,
        IReadOnlyDictionary<string, int>? MetiersPayes = null,
        int Clavier = 0, int Captures = 0, int Presentations = 0, int DefRecord = 0, int DefVague = 0, int DefBoss = 0,
        IReadOnlyDictionary<int, string>? GardesEvolution = null)
    {
        public IReadOnlyDictionary<string, long> Temps => Secondes ?? new Dictionary<string, long>();
        public IReadOnlyList<string> Succes => SuccesObtenus ?? Array.Empty<string>();
        public IReadOnlyDictionary<string, int> Payes => MetiersPayes ?? new Dictionary<string, int>();

        // Métiers et succès de deux messages du même appareil : maximum par activité et par compteur, union des succès.
        public Compteur AvecMetiers(Compteur c) => this with
        {
            Secondes = MaxParCle(Temps, c.Temps),
            SuccesObtenus = Succes.Union(c.Succes).OrderBy(x => x, StringComparer.Ordinal).ToList(),
            MetiersPayes = MaxParCle(Payes, c.Payes),
            Clavier = Math.Max(Clavier, c.Clavier),
            Captures = Math.Max(Captures, c.Captures),
            Presentations = Math.Max(Presentations, c.Presentations),
            DefRecord = Math.Max(DefRecord, c.DefRecord),
            DefVague = Math.Max(DefVague, c.DefVague),
            DefBoss = Math.Max(DefBoss, c.DefBoss),
        };
        public IReadOnlyList<ActionSoin> Actions => SoinsActions ?? Array.Empty<ActionSoin>();
        public IReadOnlyDictionary<int, string> Formes => Variantes ?? new Dictionary<int, string>();
        // Ce que Pilou a gardé à chaque évolution (scènes d'évolution) : le premier choix l'emporte, partout pareil.
        public IReadOnlyDictionary<int, string> Gardes => GardesEvolution ?? new Dictionary<int, string>();
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
            var fusion = (avant with
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
                GardesEvolution = FusionGardes(new[] { avant.Gardes, c.Gardes }),
                // Expéditions : départs du jour le plus récent (au maximum), fin de repos la plus tardive.
                ExpJour = string.CompareOrdinal(c.ExpJour, avant.ExpJour) > 0 ? c.ExpJour : avant.ExpJour,
                ExpNombre = c.ExpJour == avant.ExpJour ? Math.Max(c.ExpNombre, avant.ExpNombre)
                    : string.CompareOrdinal(c.ExpJour, avant.ExpJour) > 0 ? c.ExpNombre : avant.ExpNombre,
                ExpLibre = Math.Max(avant.ExpLibre, c.ExpLibre),
            }).AvecMetiers(c);
            bool change = fusion.Xp != avant.Xp || fusion.XpTelephone != avant.XpTelephone || fusion.T != avant.T
                          || fusion.PoGagnes != avant.PoGagnes || fusion.PoDepenses != avant.PoDepenses || fusion.PoDepTel != avant.PoDepTel
                          || fusion.Objets.Count != avant.Objets.Count || fusion.NiveauAcquis != avant.NiveauAcquis
                          || fusion.Prises.Count != avant.Prises.Count || fusion.Plats.Count != avant.Plats.Count || fusion.Nom != avant.Nom
                          || fusion.Actions.Count != avant.Actions.Count || fusion.Formes.Count != avant.Formes.Count || fusion.Gardes.Count != avant.Gardes.Count
                          || (fusion.SoinsBase?.T ?? 0) != (avant.SoinsBase?.T ?? 0)
                          || fusion.ExpJour != avant.ExpJour || fusion.ExpNombre != avant.ExpNombre || fusion.ExpLibre != avant.ExpLibre
                          || !MemesValeurs(fusion.Temps, avant.Temps) || fusion.Succes.Count != avant.Succes.Count
                          || !MemesValeurs(fusion.Payes, avant.Payes)
                          || fusion.Clavier != avant.Clavier || fusion.Captures != avant.Captures || fusion.Presentations != avant.Presentations
                          || fusion.DefRecord != avant.DefRecord || fusion.DefVague != avant.DefVague || fusion.DefBoss != avant.DefBoss;
            Autres[c.Appareil] = fusion;
            return change;
        }

        public void Oublier()
        {
            Autres.Clear();
            Depuis = "";
        }
    }

    private static Dictionary<string, T> MaxParCle<T>(IReadOnlyDictionary<string, T> a, IReadOnlyDictionary<string, T> b) where T : IComparable<T>
    {
        var r = new Dictionary<string, T>(a);
        foreach (var (k, v) in b)
            if (!r.TryGetValue(k, out var x) || v.CompareTo(x) > 0) r[k] = v;
        return r;
    }

    private static bool MemesValeurs<T>(IReadOnlyDictionary<string, T> a, IReadOnlyDictionary<string, T> b) =>
        a.Count == b.Count && a.All(kv => b.TryGetValue(kv.Key, out var v) && EqualityComparer<T>.Default.Equals(v, kv.Value));

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

    // Choix gardés des scènes d'évolution : le premier enregistré ne change plus. Deux choix différents au même stade
    // (deux appareils hors ligne en même temps) se départagent par l'ordre alphabétique, partout pareil. Ids bornés.
    public static Dictionary<int, string> FusionGardes(IEnumerable<IReadOnlyDictionary<int, string>> toutes)
    {
        var r = new Dictionary<int, string>();
        foreach (var v in toutes)
            foreach (var (stade, id) in v)
                if (GardeValide(stade, id) && (!r.TryGetValue(stade, out var avant) || string.CompareOrdinal(id, avant) < 0))
                    r[stade] = id;
        return r;
    }

    public static bool GardeValide(int stade, string? id) =>
        stade is >= 2 and <= 4 && id is { Length: > 0 and <= 24 } && id.All(ch => ch is >= 'a' and <= 'z' or '-');

    // Lecture d'un objet JSON { "2": "tache", … } (compteur du groupe, gain du téléphone).
    public static Dictionary<int, string> LireGardes(JsonElement r)
    {
        var g = new Dictionary<int, string>();
        if (!r.TryGetProperty("gardes", out var ga) || ga.ValueKind != JsonValueKind.Object) return g;
        foreach (var x in ga.EnumerateObject())
            if (int.TryParse(x.Name, System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out var st)
                && x.Value.ValueKind == JsonValueKind.String && GardeValide(st, x.Value.GetString()))
                g[st] = x.Value.GetString()!;
        return g;
    }

    public static Dictionary<string, string> JsonGardes(IReadOnlyDictionary<int, string> g) =>
        g.ToDictionary(kv => kv.Key.ToString(System.Globalization.CultureInfo.InvariantCulture), kv => kv.Value);

    public static Compteur Moi(Profil p, string appareil, string nom) => new(
        appareil, nom, p.Machine, p.Xp, p.XpTelephone, DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
        p.Carnet.Where(kv => kv.Value > 0).Select(kv => kv.Key).OrderBy(x => x).ToList(),
        p.Plats.Where(x => !x.StartsWith("inv:")).OrderBy(x => x).ToList(),
        p.Bourse.PoGagnes, p.Bourse.PoDepenses, p.Bourse.PoDepTelephone,
        p.Bourse.Inventaire.OrderBy(x => x).ToList(), new Dictionary<string, Port>(p.Bourse.Equipe), p.Evolution.NiveauPaye,
        p.Evolution.NiveauAcquis, p.Soins.Base, p.Soins.Origine, Soins.Recentes(p.Soins, 12), new Dictionary<int, string>(p.Evolution.Variantes),
        p.Expedition.Jour, p.Expedition.Nombre, p.Expedition.Libre,
        new Dictionary<string, long>(p.Activites.Where(kv => kv.Value > 0)), p.Succes.Distinct().OrderBy(x => x, StringComparer.Ordinal).ToList(),
        new Dictionary<string, int>(p.MetiersPayes.Where(kv => kv.Value > 0)),
        p.SeancesClavier, p.Captures, p.Presentations, p.Defense.Meilleur, p.Defense.MeilleureVague, p.Defense.Boss,
        new Dictionary<int, string>(p.Evolution.Gardes));

    // JSON du compteur, au plus : chiffré (nonce et étiquette, puis base64), il reste sous Telephone.TailleMax
    // (4 × (2 750 + 28) / 3 ≈ 3 704 octets). Le JSON n'a que des caractères ASCII (accents échappés).
    public const int TailleJson = 2750;

    // Un message ntfy reste sous 4 096 octets une fois chiffré : on retire des actions de soin récentes au besoin.
    public static string Json(Compteur c)
    {
        var actions = c.Actions.ToList();
        while (true)
        {
            var json = JsonBrut(c with { SoinsActions = actions });
            if (json.Length <= TailleJson || actions.Count == 0) return json;
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
        ["gardes"] = JsonGardes(c.Gardes),
        ["v"] = 1, ["appareil"] = c.Appareil, ["nom"] = c.Nom, ["machine"] = c.Machine, ["xp"] = c.Xp,
        ["xpTel"] = c.XpTelephone, ["t"] = c.T, ["prises"] = c.Prises, ["plats"] = c.Plats,
        ["po"] = c.PoGagnes, ["poDep"] = c.PoDepenses, ["poDepTel"] = c.PoDepTel, ["objets"] = Boutique.HorsGarde(c.Objets), ["garde"] = Boutique.Garde(c.Objets), ["nivPaye"] = c.NiveauPaye, ["nivAcquis"] = c.NiveauAcquis,
        ["equipe"] = c.Porte.ToDictionary(kv => kv.Key, kv => new Dictionary<string, object> { ["id"] = kv.Value.Id, ["t"] = kv.Value.T }),
        // Métiers et succès (ignorés par un ancien PC) : minutes par activité (non nulles), succès obtenus, grades
        // récompensés, compteurs [frappes avec Pilou, captures, présentations, record, vague, boss de Défense].
        ["act"] = c.Temps.Where(kv => kv.Value >= 60).ToDictionary(kv => kv.Key, kv => kv.Value / 60),
        ["suc"] = c.Succes,
        ["mp"] = c.Payes.Where(kv => kv.Value > 0).ToDictionary(kv => kv.Key, kv => kv.Value),
        ["cpt"] = new[] { c.Clavier, c.Captures, c.Presentations, c.DefRecord, c.DefVague, c.DefBoss },
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
                    if (id == "" || Boutique.TrouverTout(id)?.Slot == x.Name) equipe[x.Name] = new Port(id, te);
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
            // Métiers et succès (absents chez un ancien PC : rien). Bornes : un an de minutes par activité, ids connus.
            var secondes = new Dictionary<string, long>();
            if (r.TryGetProperty("act", out var act) && act.ValueKind == JsonValueKind.Object)
                foreach (var x in act.EnumerateObject())
                    if (Activites.Toutes.Contains(x.Name) && x.Value.ValueKind == JsonValueKind.Number && x.Value.TryGetInt64(out var mn) && mn > 0)
                        secondes[x.Name] = Math.Min(mn, 366L * 24 * 60) * 60;
            var payes = new Dictionary<string, int>();
            if (r.TryGetProperty("mp", out var mp) && mp.ValueKind == JsonValueKind.Object)
                foreach (var x in mp.EnumerateObject())
                    if (Metiers.Tous.Any(m => m.Id == x.Name) && x.Value.ValueKind == JsonValueKind.Number && x.Value.TryGetInt32(out var nv) && nv > 0)
                        payes[x.Name] = Math.Min(nv, Metiers.Grades.Length - 1);
            var succes = L("suc", 100).Where(id => PilouBureau.Succes.Tous.Any(d => d.Id == id)).ToList();
            var cpt = new int[6];
            if (r.TryGetProperty("cpt", out var cp) && cp.ValueKind == JsonValueKind.Array)
            {
                int i = 0;
                foreach (var x in cp.EnumerateArray())
                {
                    if (i >= cpt.Length) break;
                    cpt[i++] = x.ValueKind == JsonValueKind.Number && x.TryGetInt32(out var nb) ? Math.Max(0, nb) : 0;
                }
            }
            return new Compteur(appareil, nom.Length > 40 ? nom[..40] : nom, S("machine"), N("xp"), N("xpTel"), t, L("prises", 100), L("plats", 200),
                N("po"), N("poDep"), N("poDepTel"), L("objets", 300).Concat(Boutique.Deplier(S("garde"))).Distinct()
                    .Where(x => Boutique.Trouver(x) is not null).ToList(), equipe, N("nivPaye"), Math.Min(200, N("nivAcquis")),
                soinsBase, origine, actions, formes, expJour, expNombre, expLibre,
                secondes, succes, payes, cpt[0], cpt[1], cpt[2], cpt[3], cpt[4], cpt[5], LireGardes(r));
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
    // les achats faits sur le téléphone (comptés au maximum : chaque PC du groupe les applique), plus les po
    // des campagnes (comptées au maximum elles aussi : Campagnes.Crediter).
    public static int SoldePo(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe)
    {
        var gains = new Dictionary<string, (int G, int D)>(StringComparer.OrdinalIgnoreCase);
        int tel = moi.Bourse.PoDepTelephone, campagnes = moi.Bourse.PoCampagnes;
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
            campagnes = Math.Max(campagnes, p.Bourse.PoCampagnes);
        }
        foreach (var c in groupe)
        {
            Voir(c.Machine == "" ? "appareil:" + c.Appareil : c.Machine, c.PoGagnes, c.PoDepenses);
            tel = Math.Max(tel, c.PoDepTel);
        }
        // Po des campagnes : chaque PC les déduit du même historique partagé (sujet des campagnes) ; au maximum.
        return moi.Bourse.PoGagnes - moi.Bourse.PoDepenses + gains.Values.Sum(x => x.G - x.D) - tel + campagnes;
    }

    // Objets possédés par le groupe (union) et ce que Pilou porte (dernière écriture gagne par emplacement).
    public static List<string> Inventaire(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe) =>
        moi.Bourse.Inventaire.Concat(dossier.SelectMany(p => p.Bourse.Inventaire)).Concat(groupe.SelectMany(c => c.Objets))
            .Distinct().OrderBy(x => x).ToList();

    public static Dictionary<string, Port> Equipe(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe) =>
        Bourse.FusionEquipe(new[] { (IReadOnlyDictionary<string, Port>)moi.Bourse.Equipe }
            .Concat(dossier.Select(p => (IReadOnlyDictionary<string, Port>)p.Bourse.Equipe))
            .Concat(groupe.Select(c => c.Porte)));

    // Métiers et succès de tout le groupe : ce PC, les PC du dossier partagé et ceux du relais. Chaque autre
    // appareil compte une fois (le même PC vu des deux côtés : sa plus grande valeur, activité par activité).
    public sealed record Cumul(Dictionary<string, long> Secondes, int Clavier, int Captures, int Presentations, EtatDefense Defense,
        List<string> Succes, List<IReadOnlyDictionary<string, int>> PayesAutres);

    public static Cumul Cumuler(Profil moi, IEnumerable<Profil> dossier, IEnumerable<Compteur> groupe)
    {
        var parMachine = new Dictionary<string, Compteur>(StringComparer.OrdinalIgnoreCase);
        void Voir(string cle, Compteur c)
        {
            if (string.Equals(cle, moi.Machine, StringComparison.OrdinalIgnoreCase)) return;
            parMachine[cle] = parMachine.TryGetValue(cle, out var avant) ? avant.AvecMetiers(c) : c;
        }
        foreach (var p in dossier) Voir(p.Machine, Moi(p, "dossier:" + p.Machine, ""));
        foreach (var c in groupe) Voir(c.Machine == "" ? "appareil:" + c.Appareil : c.Machine, c);

        var autres = parMachine.Values.ToList();
        var secondes = new Dictionary<string, long>(moi.Activites.Where(kv => kv.Value > 0));
        foreach (var c in autres)
            foreach (var (k, v) in c.Temps)
                secondes[k] = secondes.GetValueOrDefault(k) + v;
        var defense = new EtatDefense
        {
            Meilleur = autres.Select(c => c.DefRecord).Append(moi.Defense.Meilleur).Max(),
            MeilleureVague = autres.Select(c => c.DefVague).Append(moi.Defense.MeilleureVague).Max(),
            Boss = moi.Defense.Boss + autres.Sum(c => c.DefBoss),
        };
        var succes = moi.Succes.Concat(autres.SelectMany(c => c.Succes)).Distinct().ToList();
        return new Cumul(secondes, moi.SeancesClavier + autres.Sum(c => c.Clavier), moi.Captures + autres.Sum(c => c.Captures),
            moi.Presentations + autres.Sum(c => c.Presentations), defense, succes, autres.Select(c => c.Payes).ToList());
    }

    // Succès obtenus ailleurs dans le groupe : ajoutés ici sans XP ni annonce (crédités là-bas). Renvoie les nouveaux.
    public static List<string> UnirSucces(Profil moi, Cumul c)
    {
        var nouveaux = c.Succes.Where(id => !moi.Succes.Contains(id)).ToList();
        moi.Succes.AddRange(nouveaux);
        return nouveaux;
    }

    // Ce que le PC sait pour juger les succès, avec les totaux du groupe (série de code et réunions : celles d'ici).
    public static Stats StatsGroupe(Cumul c, double serieCodeSec, int reunions, DateTime heure, string activite) =>
        new(c.Secondes, serieCodeSec, reunions, c.Presentations, heure, activite, c.Clavier, c.Captures, c.Defense);

    // « vu il y a 3 min » pour les menus.
    public static string VuIlYa(double t, double maintenant) => t <= 0 ? "jamais vu" : $"vu il y a {Statut.Duree(maintenant - t)}";
}
