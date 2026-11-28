using System.IO;

namespace PilouBureau;

// Un Pilou d'essai (--essai=, --instantane=, --film=, --captures=) ne touche jamais aux vraies données de Pilou
// (CLAUDE.md, « Tester en vrai ») : quand on ne lui donne pas d'autre dossier, il travaille dans un dossier de données
// jetable et vide, effacé à la sortie. Profil, réglages, dossier de partage, coffre des secrets, amis, groupe et
// téléphone partent tous de ce dossier : rien ne s'écrit dans ~/.claude/compagnon ni dans le dossier de partage réel.
// Le reste (réseau, mise à jour, connecteurs) est coupé par FenetrePilou en mode essai.
public static class EssaiIsole
{
    public const string Prefixe = "pilou-essai-";

    /// Le dossier de données d'un essai : celui donné s'il n'est pas le vrai dossier de Pilou, sinon un dossier neuf
    /// sous temp (créé vide). Jetable : vrai quand le dossier rendu est à effacer à la sortie.
    public static (string Dossier, bool Jetable) Dossier(string? donne, string reel, string temp)
    {
        if (donne is { Length: > 0 } && !Meme(donne, reel)) return (donne, false);
        var d = Path.Combine(temp, $"{Prefixe}{Environment.ProcessId}-{Environment.TickCount64}");
        Directory.CreateDirectory(d);
        return (d, true);
    }

    /// Deux chemins désignent-ils le même dossier (casse, séparateur final, chemin relatif) ?
    public static bool Meme(string a, string b)
    {
        try
        {
            return string.Equals(Path.GetFullPath(a).TrimEnd('\\', '/'), Path.GetFullPath(b).TrimEnd('\\', '/'), StringComparison.OrdinalIgnoreCase);
        }
        catch (Exception e) when (e is ArgumentException or NotSupportedException or PathTooLongException)
        {
            return false;
        }
    }

    /// Les dossiers jetables laissés par des essais arrêtés de force (les scripts de capture tuent le processus) : ceux
    /// dont le processus n'existe plus sont effacés au lancement d'essai suivant. Rend leur nombre.
    public static int Nettoyer(string temp, Func<int, bool> vivant)
    {
        int n = 0;
        try
        {
            foreach (var d in Directory.EnumerateDirectories(temp, Prefixe + "*"))
            {
                var reste = Path.GetFileName(d)[Prefixe.Length..];
                var tiret = reste.IndexOf('-');
                if (tiret <= 0 || !int.TryParse(reste[..tiret], out var pid) || vivant(pid)) continue;
                Effacer(d);
                if (!Directory.Exists(d)) n++;
            }
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
        }
        return n;
    }

    /// Un processus de Pilou porte-t-il ce numéro ?
    public static bool PilouVivant(int pid)
    {
        try
        {
            using var p = System.Diagnostics.Process.GetProcessById(pid);
            return p.ProcessName.StartsWith("PilouBureau", StringComparison.OrdinalIgnoreCase);
        }
        catch (Exception e) when (e is ArgumentException or InvalidOperationException)
        {
            return false;
        }
    }

    /// Efface un dossier jetable d'essai (et lui seul : son nom porte le préfixe des essais).
    public static void Effacer(string dossier)
    {
        if (!Path.GetFileName(dossier.TrimEnd('\\', '/')).StartsWith(Prefixe, StringComparison.Ordinal)) return;
        try
        {
            Directory.Delete(dossier, true);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            // un fichier encore ouvert : le dossier reste dans temp, sans rien de réel dedans
        }
    }
}
