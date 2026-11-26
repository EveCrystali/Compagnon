using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PilouBureau;

// Amis : un code court par PC (« PILOU-7F3K-9QXA-M2HT »), distinct du code de groupe, et des visites
// de Pilou chez un ami (docs/AMIS.md). Logique sans WPF : codes, dérivations, messages, anecdotes,
// machine à états d'une visite et plafonds du jour. Le transport (ntfy) et l'animation vivent dans
// FenetreAmis.cs et FenetreVisite.cs.
//
// Sécurité. Chaque PC tire une paire de clés ECDH P-256 (X25519 n'existe pas dans .NET sans dépendance) ;
// son code ami est l'empreinte de sa clé publique (12 signes, ≈ 59 bits). Une demande d'ami porte la clé
// publique : on vérifie qu'elle redonne bien le code annoncé, sans quoi on l'ignore. Les deux amis tirent
// ensuite le même secret ECDH, d'où le sujet ntfy de la paire et sa clé AES-GCM : quelqu'un qui connaîtrait
// les deux codes ne lit pas leurs échanges. Seule la demande d'ami passe par la « boîte » publique d'un code
// (sujet et clé tirés du code), parce qu'à ce moment-là on ne connaît encore que lui.

public sealed class Identite
{
    public string Code { get; set; } = "";
    // PKCS#8, base64. Jamais écrite dans amis.json : le PC la garde dans un coffre DPAPI (amis/secrets.bin).
    [JsonIgnore]
    public string Privee { get; set; } = "";
    public string Publique { get; set; } = "";  // SubjectPublicKeyInfo, base64
}

public enum EtatAmi { Attente, Recue, Actif }

// Faits qu'un Pilou peut raconter (rien d'autre : ni titre de fenêtre, ni session, ni connecteur, ni ville).
public sealed class Faits
{
    public string Prise { get; set; } = "";     // sa plus belle prise (nom)
    public string Plat { get; set; } = "";      // dernier plat découvert (nom)
    public string Quete { get; set; } = "";     // dernière quête réussie (texte du modèle)
    public string Succes { get; set; } = "";    // dernier succès (nom)
    public string Meteo { get; set; } = "";     // état du ciel chez lui (Meteo.Etats), jamais la ville
    public int Evolution { get; set; }          // stade atteint s'il a déjà évolué en Nimbus ou Astral, 0 sinon
}

// Ce qu'un Pilou montre de lui à ses amis : son allure et quelques faits.
public sealed class Vitrine
{
    public string Nom { get; set; } = "Pilou";
    public int Niveau { get; set; } = 1;
    public int Stade { get; set; } = 2;
    public string Variante { get; set; } = "";
    public string Accessoire { get; set; } = "";
    public Dictionary<string, string> Equipe { get; set; } = new();
    public Faits? Faits { get; set; }
    public bool Accepte { get; set; } = true;   // accepte les visites en ce moment (réglage, heures calmes)
    public bool Libre { get; set; } = true;     // chez lui, sans invité, pas en mode discret
}

public sealed class Ami
{
    public string Code { get; set; } = "";
    public string Cle { get; set; } = "";       // sa clé publique (connue dès sa demande ou son accord)
    public EtatAmi Etat { get; set; }
    public Vitrine Pilou { get; set; } = new();
    public double Vu { get; set; }              // dernier message reçu (ms Unix), 0 : jamais
    public int Amitie { get; set; }             // visites et caresses partagées (des cœurs dans la liste)
    public double Ajoute { get; set; }
    public string Surnom { get; set; } = "";    // nom local, choisi ici (deux amis peuvent s'appeler « Pilou »)

    [JsonIgnore]
    public string Nom => Surnom != "" ? Surnom : Pilou.Nom;
}

// Un message brut lu sur le relais (une ligne JSON de ntfy).
public sealed record Brut(string Id, string Sujet, string Message, long Temps);

public sealed class Journee
{
    public string Jour { get; set; } = "";
    public int Spontanees { get; set; }
    public int Cadeaux { get; set; }
    public int Caresses { get; set; }
}

public sealed class CarnetAmis
{
    public Identite Moi { get; set; } = new();
    public List<Ami> Amis { get; set; } = new();
    public Journee Jour { get; set; } = new();
    public List<string> Vus { get; set; } = new();  // identifiants ntfy déjà traités (les 300 derniers)
    public long Depuis { get; set; }                // dernière lecture du relais (secondes Unix)

    public static string Chemin(string dossier) => Path.Combine(dossier, "amis.json");

    public static CarnetAmis Lire(string dossier)
    {
        try
        {
            var c = JsonSerializer.Deserialize<CarnetAmis>(File.ReadAllText(Chemin(dossier)), PilouBureau.Amis.Json);
            if (c is not null) return c;
        }
        catch (Exception e) when (e is IOException or JsonException or UnauthorizedAccessException)
        {
            // pas encore d'amis
        }
        return new CarnetAmis();
    }

    public void Ecrire(string dossier)
    {
        try
        {
            Directory.CreateDirectory(dossier);
            var tmp = Chemin(dossier) + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(this, PilouBureau.Amis.Json));
            File.Move(tmp, Chemin(dossier), true);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // on réessaiera à la prochaine écriture
        }
    }

    public Ami? Trouver(string code) => Amis.FirstOrDefault(a => a.Code == PilouBureau.Amis.Normaliser(code));

    public void Marquer(string id)
    {
        Vus.Add(id);
        if (Vus.Count > 300) Vus.RemoveRange(0, Vus.Count - 300);
    }
}

// Message échangé entre deux amis (chiffré). T : demande, accepte, retire (boîte) ; presence, visite,
// accueil, refus, ici, rappel, fin, caresse (sujet de la paire).
public sealed class MessageAmi
{
    public string T { get; set; } = "";
    public string Id { get; set; } = "";
    public string De { get; set; } = "";
    public double Ts { get; set; }
    public string? Cle { get; set; }
    public Vitrine? Pilou { get; set; }
    public string? Visite { get; set; }
    public double Duree { get; set; }
    public string? Raison { get; set; }
}

public static class Amis
{
    private const string Alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
    public const int Longueur = 12;
    public const double EnLigneMs = 25 * 60_000;      // présence plus vieille : hors ligne
    public const double PresenceMs = 10 * 60_000;     // battement de présence

    public static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters = { new JsonStringEnumConverter() },
    };

    // ---- Codes

    public static string Normaliser(string code)
    {
        var s = (code ?? "").ToUpperInvariant().Trim();
        if (s.StartsWith("PILOU")) s = s[5..];
        return new string(s.Where(ch => Alphabet.Contains(ch)).ToArray());
    }

    public static bool Valide(string code) => Normaliser(code).Length == Longueur;

    public static string Formater(string code)
    {
        var n = Normaliser(code);
        return n.Length != Longueur ? n : $"PILOU-{n[..4]}-{n[4..8]}-{n[8..]}";
    }

    // Empreinte d'une clé publique : le code ami. Un octet → un signe (biais négligeable : ≈ 59 bits).
    public static string Empreinte(string publique)
    {
        var h = SHA256.HashData(Convert.FromBase64String(publique));
        var c = new char[Longueur];
        for (int i = 0; i < Longueur; i++) c[i] = Alphabet[h[i] % Alphabet.Length];
        return new string(c);
    }

    public static bool Authentique(string code, string? publique)
    {
        if (string.IsNullOrEmpty(publique)) return false;
        try
        {
            return Empreinte(publique) == Normaliser(code);
        }
        catch (FormatException)
        {
            return false;
        }
    }

    public static Identite NouvelleIdentite()
    {
        using var ec = ECDiffieHellman.Create(ECCurve.NamedCurves.nistP256);
        var pub = Convert.ToBase64String(ec.ExportSubjectPublicKeyInfo());
        return new Identite { Code = Empreinte(pub), Privee = Convert.ToBase64String(ec.ExportPkcs8PrivateKey()), Publique = pub };
    }

    // ---- Dérivations (même vecteur côté Android : Chiffre.sujetBoite, Chiffre.paire)

    private static byte[] Hmac(byte[] cle, string usage) => HMACSHA256.HashData(cle, Encoding.UTF8.GetBytes(usage));

    private static string Sujet(byte[] h) => "pilou-" + Convert.ToHexString(h).ToLowerInvariant()[..24];

    public static string SujetBoite(string code) => Sujet(Hmac(Encoding.UTF8.GetBytes(Normaliser(code)), "pilou-ami-boite-v1"));

    public static byte[] CleBoite(string code) => Hmac(Encoding.UTF8.GetBytes(Normaliser(code)), "pilou-ami-cle-v1");

    // Secret ECDH (coordonnée x brute, 32 octets) entre ma clé privée et la clé publique de l'ami.
    public static byte[] Secret(Identite moi, string publiqueAmi)
    {
        using var a = ECDiffieHellman.Create();
        a.ImportPkcs8PrivateKey(Convert.FromBase64String(moi.Privee), out _);
        using var b = ECDiffieHellman.Create();
        b.ImportSubjectPublicKeyInfo(Convert.FromBase64String(publiqueAmi), out _);
        if (b.KeySize != 256) throw new CryptographicException("clé d'ami inattendue");
        return a.DeriveRawSecretAgreement(b.PublicKey);
    }

    // Sujet et clé de la paire : mêmes des deux côtés (codes rangés dans l'ordre).
    public static (string Sujet, byte[] Cle) Paire(byte[] secret, string codeA, string codeB)
    {
        string a = Normaliser(codeA), b = Normaliser(codeB);
        var lien = string.CompareOrdinal(a, b) <= 0 ? $"{a}|{b}" : $"{b}|{a}";
        return (Sujet(Hmac(secret, "pilou-paire-sujet-v1|" + lien)), Hmac(secret, "pilou-paire-cle-v1|" + lien));
    }

    // base64(nonce 12 ‖ chiffré ‖ étiquette 16), comme Telephone.Chiffrer.
    public static string Chiffrer(byte[] cle, string texte, byte[]? nonce = null)
    {
        nonce ??= RandomNumberGenerator.GetBytes(12);
        var clair = Encoding.UTF8.GetBytes(texte);
        var chiffre = new byte[clair.Length];
        var etiquette = new byte[16];
        using (var aes = new AesGcm(cle, 16)) aes.Encrypt(nonce, clair, chiffre, etiquette);
        return Convert.ToBase64String([.. nonce, .. chiffre, .. etiquette]);
    }

    public static string? Dechiffrer(byte[] cle, string message)
    {
        try
        {
            var tout = Convert.FromBase64String(message);
            if (tout.Length < 28) return null;
            var clair = new byte[tout.Length - 28];
            using (var aes = new AesGcm(cle, 16)) aes.Decrypt(tout[..12], tout[12..^16], tout[^16..], clair);
            return Encoding.UTF8.GetString(clair);
        }
        catch (Exception e) when (e is FormatException or CryptographicException)
        {
            return null;
        }
    }

    // ---- Relais

    // Réponse de « …/sujet1,sujet2/json?poll=1 » : une ligne JSON par événement ; seuls les messages comptent.
    public static List<Brut> LireRelais(string texte)
    {
        var l = new List<Brut>();
        foreach (var ligne in (texte ?? "").Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            try
            {
                using var d = JsonDocument.Parse(ligne);
                var r = d.RootElement;
                if (r.ValueKind != JsonValueKind.Object || !r.TryGetProperty("event", out var ev) || ev.GetString() != "message") continue;
                string Texte(string nom) => r.TryGetProperty(nom, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : "";
                long temps = r.TryGetProperty("time", out var tm) && tm.TryGetInt64(out var x) ? x : 0;
                if (Texte("id") == "" || Texte("message") == "") continue;
                l.Add(new Brut(Texte("id"), Texte("topic"), Texte("message"), temps));
            }
            catch (JsonException)
            {
                // ligne tronquée : ignorée
            }
        }
        return l;
    }

    // ---- Messages

    public static MessageAmi Message(string type, string de, double t) =>
        new() { T = type, Id = Guid.NewGuid().ToString("N")[..16], De = Normaliser(de), Ts = t };

    public static string Ecrire(MessageAmi m) => JsonSerializer.Serialize(m, Json);

    // Lecture défensive : tout ce qui vient d'un autre PC est borné et nettoyé.
    public static MessageAmi? Lire(string? json)
    {
        if (string.IsNullOrEmpty(json) || json.Length > 6000) return null;
        MessageAmi? m;
        try
        {
            m = JsonSerializer.Deserialize<MessageAmi>(json, Json);
        }
        catch (JsonException)
        {
            return null;
        }
        if (m is null || !Valide(m.De) || m.T is not ("demande" or "accepte" or "retire" or "presence" or "visite" or "accueil"
                or "refus" or "ici" or "rappel" or "fin" or "caresse"))
            return null;
        m.De = Normaliser(m.De);
        m.Id = Nettoyer(m.Id, 40);
        m.Visite = m.Visite is null ? null : Nettoyer(m.Visite, 40);
        m.Raison = m.Raison is null ? null : Nettoyer(m.Raison, 20);
        m.Cle = m.Cle is { Length: < 400 } ? m.Cle : null;
        m.Duree = Math.Clamp(m.Duree, 0, Visites.DureeMax);
        if (m.Pilou is { } v) m.Pilou = Borner(v);
        return m;
    }

    public static string Nettoyer(string? s, int max)
    {
        if (string.IsNullOrEmpty(s)) return "";
        var t = new string(s.Where(ch => !char.IsControl(ch) && ch is not ('​' or '‎' or '‏' or '‮')).ToArray()).Trim();
        return t.Length > max ? t[..max] : t;
    }

    private static bool Identifiant(string s) => s.Length is > 0 and <= 40 && s.All(ch => ch is (>= 'a' and <= 'z') or (>= '0' and <= '9') or '-' or ':');

    public static readonly string[] Emplacements = { "tete", "yeux", "cou", "dos", "main", "compagnon", "effet", "couleur" };

    public static Vitrine Borner(Vitrine v)
    {
        var f = v.Faits;
        return new Vitrine
        {
            Nom = Nettoyer(v.Nom, 24) is { Length: > 0 } n ? n : "Pilou",
            Niveau = Math.Clamp(v.Niveau, 1, 999),
            Stade = Math.Clamp(v.Stade, 1, 4),
            Variante = v.Variante is "calin" or "espiegle" ? v.Variante : "",
            Accessoire = Identifiant(v.Accessoire) ? v.Accessoire : "",
            Equipe = (v.Equipe ?? new()).Where(kv => Emplacements.Contains(kv.Key) && Identifiant(kv.Value)).Take(10)
                .ToDictionary(kv => kv.Key, kv => kv.Value),
            Faits = f is null ? null : new Faits
            {
                Prise = Nettoyer(f.Prise, 40), Plat = Nettoyer(f.Plat, 40), Quete = Nettoyer(f.Quete, 60), Succes = Nettoyer(f.Succes, 40),
                Meteo = Meteo.Etats.Contains(f.Meteo) ? f.Meteo : "", Evolution = Math.Clamp(f.Evolution, 0, 4),
            },
            Accepte = v.Accepte,
            Libre = v.Libre,
        };
    }

    // ---- Ce que je montre de moi

    // Seuls ces faits sortent du PC (et seulement si « Partager mes anecdotes » est coché).
    public static Faits FaitsDe(Profil p, string meteo)
    {
        var prise = p.Carnet.Where(kv => kv.Value > 0).Select(kv => Butin.Trouver(kv.Key)).Where(x => x is not null)
            .OrderByDescending(x => x!.Rarete).ThenByDescending(x => x!.Xp).FirstOrDefault();
        var plat = p.Plats.LastOrDefault(x => !x.StartsWith("inv:")) is { } id ? Butin.Recettes.FirstOrDefault(r => r.Id == id)?.Nom ?? "" : "";
        var quete = p.Quetes.Liste.LastOrDefault(q => q.Reussie)?.Texte ?? "";
        var succes = p.Succes.Count > 0 ? PilouBureau.Succes.Tous.FirstOrDefault(d => d.Id == p.Succes[^1])?.Nom ?? "" : "";
        int evolution = p.Evolution.StadeAtteint >= 3 ? p.Evolution.StadeAtteint : 0;
        return new Faits
        {
            Prise = prise?.Nom ?? "", Plat = plat, Quete = quete, Succes = succes,
            Meteo = Meteo.Etats.Contains(meteo) ? meteo : "", Evolution = evolution,
        };
    }

    // ---- Anecdotes (côté hôte, à partir de la vitrine reçue)

    public static List<string> Anecdotes(Vitrine v)
    {
        var l = new List<string> { $"je suis niveau {v.Niveau} maintenant !" };
        if (v.Faits is { } f)
        {
            if (f.Prise != "") l.Add($"ma plus belle prise ? {Article(f.Prise)} !");
            if (f.Plat != "") l.Add($"hier j'ai cuisiné : {f.Plat}. miam !");
            if (f.Quete != "") l.Add($"quête réussie : « {Minuscule(f.Quete)} »");
            if (f.Succes != "") l.Add($"j'ai eu le succès « {f.Succes} » !");
            if (f.Evolution >= 3) l.Add($"tu as vu ? j'ai évolué en Pilou {Amis.NomStade(f.Evolution)} !");
            var ciel = f.Meteo switch
            {
                Meteo.Pluie or Meteo.Averse => "chez moi il pleut, je suis venu au sec",
                Meteo.Orage => "chez moi ça gronde, brr…",
                Meteo.Neige => "chez moi il neige !",
                Meteo.Degage => "chez moi il fait grand beau",
                Meteo.Chaleur => "chez moi il fait une chaleur…",
                Meteo.Froid => "chez moi il fait un froid de canard",
                Meteo.Brouillard => "chez moi on n'y voit rien, du brouillard partout",
                Meteo.Vent => "chez moi ça souffle fort",
                _ => "",
            };
            if (ciel != "") l.Add(ciel);
        }
        return l;
    }

    private static string Minuscule(string s) => s.Length == 0 ? s : char.ToLowerInvariant(s[0]) + s[1..];

    private static string Article(string nom) => nom.Length > 0 && "AEIOUÉÈHaeiouéèh".Contains(nom[0]) ? $"un {nom}" : $"un {Minuscule(nom)}";

    // Réponses de l'hôte (son Pilou à lui).
    public static readonly string[] Reponses = { "oh, trop bien !", "bravo !", "la classe !", "moi aussi je veux !", "raconte encore !", "waouh !" };

    // ---- Liste d'amis

    public static bool EnLigne(Ami a, double maintenant) => a.Vu > 0 && maintenant - a.Vu < EnLigneMs;

    public static string VuIlYa(Ami a, double maintenant)
    {
        if (a.Etat == EtatAmi.Attente) return "en attente de son accord";
        if (a.Etat == EtatAmi.Recue) return "te demande en ami";
        if (a.Vu <= 0) return "jamais vu en ligne";
        if (EnLigne(a, maintenant)) return "en ligne";
        double min = (maintenant - a.Vu) / 60_000;
        return min < 60 ? $"vu il y a {Math.Max(1, (int)min)} min"
            : min < 48 * 60 ? $"vu il y a {(int)(min / 60)} h"
            : $"vu il y a {(int)(min / 1440)} j";
    }

    public static string NomStade(int s) => s switch { 1 => "Gouttelette", 3 => "Nimbus", 4 => "Astral", _ => "Pilou" };

    // Heures calmes : [debut, fin[ en heures locales, à cheval sur minuit si debut > fin.
    public static bool Calme(int heure, int debut, int fin) =>
        debut != fin && (debut < fin ? heure >= debut && heure < fin : heure >= debut || heure < fin);

    public static string Heure(DateTime t) => t.ToString("H' h 'mm", CultureInfo.InvariantCulture);
}

// Ajouter, accepter, retirer un ami. Les demandes passent par la boîte du code de l'ami (« boite ») ;
// le reste par le sujet de la paire (« envoi »). Une clé qui ne redonne pas le code annoncé est ignorée.
public static class Annuaire
{
    public const int AmisMax = 30;

    public static string? Refus(CarnetAmis c, string code)
    {
        if (!Amis.Valide(code)) return "Ce code ne ressemble pas à un code ami (PILOU- puis 12 signes).";
        if (Amis.Normaliser(code) == c.Moi.Code) return "C'est ton propre code : donne-le à ton ami, et demande-lui le sien.";
        if (c.Amis.Count >= AmisMax && c.Trouver(code) is null) return $"Tu as déjà {AmisMax} amis.";
        return null;
    }

    private static MessageAmi Carte(string type, CarnetAmis c, Vitrine moi, double t)
    {
        var m = Amis.Message(type, c.Moi.Code, t);
        m.Cle = c.Moi.Publique;
        m.Pilou = moi;
        return m;
    }

    // J'ajoute un code : une demande part dans sa boîte ; s'il m'avait déjà demandé, c'est un accord.
    public static List<Effet> Ajouter(CarnetAmis c, string code, Vitrine moi, double t)
    {
        var e = new List<Effet>();
        if (Refus(c, code) is not null) return e;
        var n = Amis.Normaliser(code);
        var a = c.Trouver(n);
        if (a is { Etat: EtatAmi.Recue }) return Accepter(c, n, moi, t);
        if (a is null)
        {
            a = new Ami { Code = n, Etat = EtatAmi.Attente, Ajoute = t };
            c.Amis.Add(a);
        }
        if (a.Etat == EtatAmi.Attente) e.Add(new Effet("boite", n, Carte("demande", c, moi, t)));
        return e;
    }

    public static List<Effet> Accepter(CarnetAmis c, string code, Vitrine moi, double t)
    {
        var e = new List<Effet>();
        if (c.Trouver(code) is not { Etat: EtatAmi.Recue } a) return e;
        a.Etat = EtatAmi.Actif;
        e.Add(new Effet("boite", a.Code, Carte("accepte", c, moi, t)));
        e.Add(new Effet("ami", a.Code));
        return e;
    }

    // Retirer : l'ami l'apprend par la paire (s'il était actif), puis on l'oublie.
    public static List<Effet> Retirer(CarnetAmis c, string code, double t)
    {
        var e = new List<Effet>();
        if (c.Trouver(code) is not { } a) return e;
        if (a.Etat == EtatAmi.Actif && a.Cle != "") e.Add(new Effet("envoi", a.Code, Amis.Message("retire", c.Moi.Code, t)));
        c.Amis.Remove(a);
        return e;
    }

    // Message lu dans ma boîte.
    public static List<Effet> Boite(CarnetAmis c, MessageAmi m, Vitrine moi, double t)
    {
        var e = new List<Effet>();
        if (m.De == c.Moi.Code || !Amis.Authentique(m.De, m.Cle)) return e;
        var a = c.Trouver(m.De);
        switch (m.T)
        {
            case "demande":
                if (a is null)
                {
                    if (c.Amis.Count >= AmisMax) break;
                    a = new Ami { Code = m.De, Etat = EtatAmi.Recue, Ajoute = t };
                    c.Amis.Add(a);
                    e.Add(new Effet("demande", a.Code));
                }
                a.Cle = m.Cle!;
                if (m.Pilou is not null) a.Pilou = m.Pilou;
                // Je l'avais déjà ajouté (ou nous l'étions déjà et il a perdu sa liste) : l'amitié est active.
                if (a.Etat is EtatAmi.Attente or EtatAmi.Actif)
                {
                    bool nouveau = a.Etat == EtatAmi.Attente;
                    a.Etat = EtatAmi.Actif;
                    a.Vu = t;
                    e.Add(new Effet("boite", a.Code, Carte("accepte", c, moi, t)));
                    if (nouveau) e.Add(new Effet("ami", a.Code));
                }
                break;
            case "accepte" when a is { Etat: EtatAmi.Attente or EtatAmi.Actif }:
                bool neuf = a.Etat == EtatAmi.Attente;
                a.Cle = m.Cle!;
                a.Etat = EtatAmi.Actif;
                if (m.Pilou is not null) a.Pilou = m.Pilou;
                a.Vu = t;
                if (neuf) e.Add(new Effet("ami", a.Code));
                break;
        }
        return e;
    }

    // Message lu sur le sujet d'une paire : présence et retrait ici ; le reste va à la machine des visites.
    public static List<Effet> Paire(CarnetAmis c, Ami a, MessageAmi m, double t)
    {
        var e = new List<Effet>();
        a.Vu = t;
        if (m.T == "presence" && m.Pilou is not null) a.Pilou = m.Pilou;
        if (m.T == "retire")
        {
            c.Amis.Remove(a);
            e.Add(new Effet("retire", a.Code));
        }
        return e;
    }
}

// ---- Visites

public enum Etape { Depart, Absent, Retour, Arrivee, Present, Sortie }

// Mon Pilou chez un ami.
public sealed class Sortie
{
    public string Ami { get; set; } = "";
    public string Id { get; set; } = "";
    public Etape Etape { get; set; }
    public double Depuis { get; set; }      // début de l'étape
    public double Debut { get; set; }
    public double Fin { get; set; }
    public bool Accueilli { get; set; }
    public double Contact { get; set; }
    public bool Spontanee { get; set; }
    public string Raison { get; set; } = "";
}

// Un invité chez moi.
public sealed class Venue
{
    public string Ami { get; set; } = "";
    public string Id { get; set; } = "";
    public Etape Etape { get; set; }
    public double Depuis { get; set; }
    public double Fin { get; set; }
    public double Contact { get; set; }
    public Vitrine Invite { get; set; } = new();
    public string Raison { get; set; } = "";
}

// Ce que la machine demande à la fenêtre : un message à envoyer à un ami, ou un moment à animer.
public sealed record Effet(string Quoi, string Ami, MessageAmi? Message = null, string Raison = "");

// Ce que l'hôte vérifie avant d'ouvrir sa porte.
public sealed record PorteAmi(bool Accepte, bool Discret, bool Calme);

public sealed class Visites
{
    public const double DepartMs = 4500, RetourMs = 4000, ArriveeMs = 5000, SortieMs = 4000;
    public const double DureeMin = 5 * 60_000, DureeMax = 10 * 60_000;
    public const double AttenteMax = 150_000;   // sans « accueil » après le départ : il rentre
    public const double SilenceMax = 300_000;   // plus de nouvelles de l'autre PC : chacun rentre
    public const double BattementMs = 90_000;   // « ici » pendant une visite
    public const int SpontaneesMax = 2, CadeauxMax = 2, CaressesMax = 5;

    public Sortie? Sortie { get; set; }
    public Venue? Venue { get; set; }
    public double Battement { get; set; } = -1e15;

    public bool Occupe => Sortie is not null || Venue is not null;

    public static double Duree(Random r) => DureeMin + r.NextDouble() * (DureeMax - DureeMin);

    public static void Actualiser(Journee j, DateTime local)
    {
        var jour = Quetes.CleJour(local);
        if (j.Jour == jour) return;
        j.Jour = jour;
        j.Spontanees = j.Cadeaux = j.Caresses = 0;
    }

    // Envie de partir : réglage coché, PC calme, pas discret, hors heures calmes, moins de 2 fois aujourd'hui,
    // un ami en ligne qui accepte et qui est libre. Renvoie l'ami choisi (au hasard), null sinon.
    public Ami? Envie(IEnumerable<Ami> amis, Journee j, bool permis, bool calmePc, bool discret, bool heureCalme, double maintenant, Random r)
    {
        if (!permis || !calmePc || discret || heureCalme || Occupe || j.Spontanees >= SpontaneesMax) return null;
        var dispo = amis.Where(a => a.Etat == EtatAmi.Actif && Amis.EnLigne(a, maintenant) && a.Pilou.Accepte && a.Pilou.Libre).ToList();
        return dispo.Count == 0 ? null : dispo[r.Next(dispo.Count)];
    }

    public List<Effet> Partir(Ami ami, string moi, Vitrine vitrine, double t, double duree, bool spontanee, Journee j)
    {
        var e = new List<Effet>();
        if (Occupe || ami.Etat != EtatAmi.Actif) return e;
        if (spontanee) j.Spontanees++;
        var m = Amis.Message("visite", moi, t);
        m.Visite = m.Id;
        m.Duree = Math.Clamp(duree, DureeMin, DureeMax);
        m.Pilou = vitrine;
        Sortie = new Sortie
        {
            Ami = ami.Code, Id = m.Id, Etape = Etape.Depart, Depuis = t, Debut = t, Fin = t + DepartMs + m.Duree, Contact = t,
            Spontanee = spontanee,
        };
        e.Add(new Effet("envoi", ami.Code, m));
        e.Add(new Effet("depart", ami.Code));
        return e;
    }

    // On rappelle son Pilou (clic sur la pancarte) : il dit au revoir là-bas et rentre tout de suite.
    public List<Effet> Rappeler(string moi, double t)
    {
        var e = new List<Effet>();
        if (Sortie is not { Etape: Etape.Depart or Etape.Absent } s) return e;
        var m = Amis.Message("rappel", moi, t);
        m.Visite = s.Id;
        e.Add(new Effet("envoi", s.Ami, m));
        Rentrer(s, t, "rappel", e);
        return e;
    }

    // L'hôte met fin à la visite (plein écran, présentation, visio, ou il raccompagne l'invité).
    public List<Effet> Congedier(string moi, double t, string raison)
    {
        var e = new List<Effet>();
        if (Venue is not { Etape: Etape.Arrivee or Etape.Present } v) return e;
        var m = Amis.Message("fin", moi, t);
        m.Visite = v.Id;
        m.Raison = raison;
        e.Add(new Effet("envoi", v.Ami, m));
        Raccompagner(v, t, raison, e);
        return e;
    }

    public List<Effet> Recevoir(MessageAmi m, Ami? ami, string moi, PorteAmi porte, double t)
    {
        var e = new List<Effet>();
        if (ami is not { Etat: EtatAmi.Actif }) return e;
        switch (m.T)
        {
            case "visite":
                string? refus = !porte.Accepte ? "ferme" : porte.Calme ? "calme" : porte.Discret ? "occupe"
                    : Sortie is not null ? "absent" : Venue is not null ? "invite" : null;
                if (refus is not null)
                {
                    var r = Amis.Message("refus", moi, t);
                    r.Visite = m.Visite;
                    r.Raison = refus;
                    e.Add(new Effet("envoi", ami.Code, r));
                    break;
                }
                Venue = new Venue
                {
                    Ami = ami.Code, Id = m.Visite ?? m.Id, Etape = Etape.Arrivee, Depuis = t, Contact = t,
                    Fin = t + Math.Clamp(m.Duree, DureeMin, DureeMax), Invite = m.Pilou ?? ami.Pilou,
                };
                var a = Amis.Message("accueil", moi, t);
                a.Visite = Venue.Id;
                e.Add(new Effet("envoi", ami.Code, a));
                e.Add(new Effet("arrivee", ami.Code));
                break;
            case "accueil" when Sortie is { } s && s.Id == m.Visite && s.Ami == ami.Code:
                s.Accueilli = true;
                s.Contact = t;
                e.Add(new Effet("accueilli", ami.Code));
                break;
            case "refus" when Sortie is { Etape: Etape.Depart or Etape.Absent } s && s.Id == m.Visite && s.Ami == ami.Code:
                Rentrer(s, t, "refus:" + (m.Raison ?? ""), e);
                break;
            case "fin" when Sortie is { Etape: Etape.Depart or Etape.Absent } s && s.Id == m.Visite && s.Ami == ami.Code:
                Rentrer(s, t, "fin", e);
                break;
            case "rappel" or "fin" when Venue is { Etape: Etape.Arrivee or Etape.Present } v && v.Id == m.Visite && v.Ami == ami.Code:
                Raccompagner(v, t, m.T, e);
                break;
            case "ici":
                if (Sortie is { } so && so.Id == m.Visite && so.Ami == ami.Code) so.Contact = t;
                if (Venue is { } ve && ve.Id == m.Visite && ve.Ami == ami.Code) ve.Contact = t;
                break;
            case "caresse" when Sortie is { Etape: Etape.Absent } s && s.Id == m.Visite && s.Ami == ami.Code:
                e.Add(new Effet("caresse", ami.Code));
                break;
        }
        return e;
    }

    public List<Effet> Avancer(string moi, double t)
    {
        var e = new List<Effet>();
        if (Sortie is { } s)
        {
            if (s.Etape == Etape.Depart && t - s.Depuis >= DepartMs)
            {
                s.Etape = Etape.Absent;
                s.Depuis = t;
            }
            if (s.Etape is Etape.Depart or Etape.Absent)
            {
                if (!s.Accueilli && t - s.Debut > AttenteMax) Rentrer(s, t, "silence", e);
                else if (s.Accueilli && t - s.Contact > SilenceMax) Rentrer(s, t, "silence", e);
                else if (t >= s.Fin)
                {
                    // Fin de la visite : on le dit à l'hôte, pour que son invité parte en même temps.
                    e.Add(Fin(s.Ami, s.Id, moi, t));
                    Rentrer(s, t, "fini", e);
                }
                else if (s.Accueilli && t - Battement >= BattementMs) e.Add(Ici(s.Ami, s.Id, moi, t));
            }
            else if (s.Etape == Etape.Retour && t - s.Depuis >= RetourMs)
            {
                e.Add(new Effet("rentre", s.Ami, null, s.Raison));
                Sortie = null;
            }
        }
        if (Venue is { } v)
        {
            if (v.Etape == Etape.Arrivee && t - v.Depuis >= ArriveeMs)
            {
                v.Etape = Etape.Present;
                v.Depuis = t;
                e.Add(new Effet("present", v.Ami));
            }
            if (v.Etape is Etape.Arrivee or Etape.Present)
            {
                if (t - v.Contact > SilenceMax) Raccompagner(v, t, "silence", e);
                else if (t >= v.Fin)
                {
                    e.Add(Fin(v.Ami, v.Id, moi, t));
                    Raccompagner(v, t, "fini", e);
                }
                else if (t - Battement >= BattementMs) e.Add(Ici(v.Ami, v.Id, moi, t));
            }
            else if (v.Etape == Etape.Sortie && t - v.Depuis >= SortieMs)
            {
                e.Add(new Effet("invite-parti", v.Ami, null, v.Raison));
                Venue = null;
            }
        }
        return e;
    }

    private Effet Ici(string ami, string id, string moi, double t)
    {
        Battement = t;
        var m = Amis.Message("ici", moi, t);
        m.Visite = id;
        return new Effet("envoi", ami, m);
    }

    private static Effet Fin(string ami, string id, string moi, double t)
    {
        var m = Amis.Message("fin", moi, t);
        m.Visite = id;
        m.Raison = "fini";
        return new Effet("envoi", ami, m);
    }

    private static void Rentrer(Sortie s, double t, string raison, List<Effet> e)
    {
        s.Etape = Etape.Retour;
        s.Depuis = t;
        s.Raison = raison;
        e.Add(new Effet("retour", s.Ami, null, raison));
    }

    private static void Raccompagner(Venue v, double t, string raison, List<Effet> e)
    {
        v.Etape = Etape.Sortie;
        v.Depuis = t;
        v.Raison = raison;
        e.Add(new Effet("invite-part", v.Ami, null, raison));
    }

    // Petit cadeau au retour (seulement si l'ami l'a accueilli), deux fois par jour au plus.
    public static (int Po, int Xp) Cadeau(Journee j, string raison, bool accueilli, Random r)
    {
        if (!accueilli || raison.StartsWith("refus") || raison == "silence" || j.Cadeaux >= CadeauxMax) return (0, 0);
        j.Cadeaux++;
        return (8 + r.Next(8), 5);
    }

    // Caresse entre amis (donnée ou reçue) : +2 xp, cinq fois par jour au plus.
    public static int Caresse(Journee j)
    {
        if (j.Caresses >= CaressesMax) return 0;
        j.Caresses++;
        return 2;
    }
}
