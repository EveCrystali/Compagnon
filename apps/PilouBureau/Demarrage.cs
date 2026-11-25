using Microsoft.Win32;

namespace PilouBureau;

// « Démarrer avec Windows » : une valeur dans la clé Run de l'utilisateur, rien d'autre.
public static class Demarrage
{
    private const string Cle = @"Software\Microsoft\Windows\CurrentVersion\Run";
    private const string Nom = "PilouBureau";

    public static bool Actif()
    {
        using var k = Registry.CurrentUser.OpenSubKey(Cle);
        return k?.GetValue(Nom) is string;
    }

    public static void Regler(bool actif)
    {
        using var k = Registry.CurrentUser.CreateSubKey(Cle);
        if (actif) k.SetValue(Nom, $"\"{Environment.ProcessPath}\"");
        else k.DeleteValue(Nom, false);
    }
}
