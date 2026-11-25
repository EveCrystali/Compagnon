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
    public static string Signature(IReadOnlyList<SessionTel> sessions, int niveau, string humeur) =>
        $"{niveau}|{humeur}|" + string.Join(";", sessions.Select(s => $"{s.Id}:{s.Etat}:{s.Depuis}"));

    public static string Charge(IReadOnlyList<SessionTel> sessions, double maintenant, string nom, int niveau, string titre,
        string couleur, string humeur, int calmes) =>
        JsonSerializer.Serialize(new Dictionary<string, object>
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
        });
}
