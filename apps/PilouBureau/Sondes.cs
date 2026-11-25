using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32;

namespace PilouBureau;

// Ce que Windows dit de l'instant : fenêtre au premier plan, plein écran, sons en cours, caméra et micro,
// charge du processeur. Chaque sonde qui échoue rend une valeur neutre : Pilou ne plante jamais pour ça.
public static class Sondes
{
    [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowTextW(IntPtr hwnd, StringBuilder texte, int max);
    [DllImport("kernel32.dll")] private static extern IntPtr OpenProcess(uint acces, bool heriter, uint pid);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] private static extern bool QueryFullProcessImageNameW(IntPtr h, int flags, StringBuilder nom, ref int taille);
    [DllImport("shell32.dll")] private static extern int SHQueryUserNotificationState(out int etat);
    [DllImport("kernel32.dll")] private static extern bool GetSystemTimes(out long inactif, out long noyau, out long utilisateur);

    private const uint LectureLimitee = 0x1000; // PROCESS_QUERY_LIMITED_INFORMATION

    // Fenêtre au premier plan : nom du programme, titre, chemin. La fenêtre de Pilou lui-même est ignorée.
    public static (string Processus, string Titre, string Chemin)? PremierPlan()
    {
        try
        {
            var h = GetForegroundWindow();
            if (h == IntPtr.Zero) return null;
            GetWindowThreadProcessId(h, out var pid);
            if (pid == 0 || pid == (uint)Environment.ProcessId) return null;
            var titre = new StringBuilder(512);
            GetWindowTextW(h, titre, titre.Capacity);
            var chemin = CheminDe(pid);
            var nom = chemin != "" ? Path.GetFileNameWithoutExtension(chemin) : "";
            return (nom, titre.ToString(), chemin);
        }
        catch (Exception e) when (e is ExternalException or InvalidOperationException or ArgumentException)
        {
            return null;
        }
    }

    private static string CheminDe(uint pid)
    {
        var h = OpenProcess(LectureLimitee, false, pid);
        if (h == IntPtr.Zero) return "";
        try
        {
            var nom = new StringBuilder(1024);
            int taille = nom.Capacity;
            return QueryFullProcessImageNameW(h, 0, nom, ref taille) ? nom.ToString(0, taille) : "";
        }
        finally
        {
            CloseHandle(h);
        }
    }

    // QUERY_USER_NOTIFICATION_STATE : 1 verrouillé/écran de veille, 2 appli plein écran, 3 jeu Direct3D plein écran,
    // 4 mode présentation, 5 normal, 6 heures calmes, 7 appli du Store en plein écran.
    public static Activites.Ecran Ecran()
    {
        try
        {
            if (SHQueryUserNotificationState(out var e) != 0) return Activites.Ecran.Normal;
            return e switch
            {
                1 => Activites.Ecran.Verrouille,
                2 or 7 => Activites.Ecran.PleinEcran,
                3 => Activites.Ecran.Jeu3D,
                4 => Activites.Ecran.Presentation,
                _ => Activites.Ecran.Normal,
            };
        }
        catch (Exception e) when (e is ExternalException or EntryPointNotFoundException or DllNotFoundException)
        {
            return Activites.Ecran.Normal;
        }
    }

    // Caméra ou micro en cours d'utilisation : Windows note LastUsedTimeStop = 0 tant qu'une app s'en sert.
    public static bool EnCours(string capacite)
    {
        try
        {
            using var racine = Registry.CurrentUser.OpenSubKey(
                $@"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\{capacite}");
            return racine is not null && Parcourir(racine, 0);
        }
        catch (Exception e) when (e is System.Security.SecurityException or UnauthorizedAccessException or IOException)
        {
            return false;
        }

        static bool Parcourir(RegistryKey cle, int profondeur)
        {
            if (cle.GetValue("LastUsedTimeStop") is long fin && fin == 0 && cle.GetValue("LastUsedTimeStart") is long debut && debut != 0)
                return true;
            if (profondeur >= 2) return false;
            foreach (var nom in cle.GetSubKeyNames())
            {
                using var sous = cle.OpenSubKey(nom);
                if (sous is not null && Parcourir(sous, profondeur + 1)) return true;
            }
            return false;
        }
    }

    // Charge du processeur (0..1) depuis le dernier appel.
    private static long _inactif, _total;

    public static double Cpu()
    {
        try
        {
            if (!GetSystemTimes(out var inactif, out var noyau, out var utilisateur)) return 0;
            long total = noyau + utilisateur; // le temps noyau inclut l'inactif
            long dI = inactif - _inactif, dT = total - _total;
            _inactif = inactif;
            _total = total;
            return dT <= 0 ? 0 : Math.Clamp(1.0 - (double)dI / dT, 0, 1);
        }
        catch (Exception e) when (e is ExternalException or EntryPointNotFoundException)
        {
            return 0;
        }
    }

    // ---- Sons en cours : sessions audio du périphérique de sortie par défaut, niveau crête par programme.

    public static Dictionary<string, float> Sons()
    {
        var sons = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
        object? enumerateur = null, peripherique = null, gestionnaire = null, liste = null;
        try
        {
            enumerateur = Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"))!);
            var en = (IMMDeviceEnumerator)enumerateur!;
            if (en.GetDefaultAudioEndpoint(0 /* eRender */, 1 /* eMultimedia */, out var dev) != 0 || dev is null) return sons;
            peripherique = dev;
            var iid = typeof(IAudioSessionManager2).GUID;
            if (dev.Activate(ref iid, 0x17 /* CLSCTX_ALL */, IntPtr.Zero, out var obj) != 0 || obj is null) return sons;
            gestionnaire = obj;
            var gm = (IAudioSessionManager2)obj;
            if (gm.GetSessionEnumerator(out var sessions) != 0 || sessions is null) return sons;
            liste = sessions;
            sessions.GetCount(out var n);
            for (int i = 0; i < n; i++)
            {
                if (sessions.GetSession(i, out var ctl) != 0 || ctl is null) continue;
                try
                {
                    if (ctl is not IAudioSessionControl2 c2 || ctl is not IAudioMeterInformation compteur) continue;
                    c2.GetState(out var etat);
                    if (etat != 1 /* AudioSessionStateActive */) continue;
                    c2.GetProcessId(out var pid);
                    if (pid == 0) continue;
                    compteur.GetPeakValue(out var crete);
                    string nom;
                    try
                    {
                        using var p = Process.GetProcessById((int)pid);
                        nom = p.ProcessName;
                    }
                    catch (ArgumentException)
                    {
                        continue;
                    }
                    sons[nom] = Math.Max(sons.TryGetValue(nom, out var v) ? v : 0, crete);
                }
                finally
                {
                    Marshal.ReleaseComObject(ctl);
                }
            }
        }
        catch (Exception e) when (e is COMException or InvalidCastException or InvalidOperationException or ArgumentException)
        {
            // pas de périphérique audio, ou Windows trop ancien : pas de son
        }
        finally
        {
            foreach (var o in new[] { liste, gestionnaire, peripherique, enumerateur })
                if (o is not null && Marshal.IsComObject(o)) Marshal.ReleaseComObject(o);
        }
        return sons;
    }

    // Interfaces Core Audio, déclarées dans l'ordre exact de leurs tables de méthodes.
    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(int flux, int etat, out IntPtr appareils);
        [PreserveSig] int GetDefaultAudioEndpoint(int flux, int role, out IMMDevice? appareil);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, int contexte, IntPtr parametres, [MarshalAs(UnmanagedType.IUnknown)] out object? interfaceObtenue);
    }

    [ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioSessionManager2
    {
        [PreserveSig] int GetAudioSessionControl(IntPtr guid, int flags, out IntPtr controle);
        [PreserveSig] int GetSimpleAudioVolume(IntPtr guid, int flags, out IntPtr volume);
        [PreserveSig] int GetSessionEnumerator(out IAudioSessionEnumerator? liste);
    }

    [ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioSessionEnumerator
    {
        [PreserveSig] int GetCount(out int nombre);
        [PreserveSig] int GetSession(int index, [MarshalAs(UnmanagedType.IUnknown)] out object? session);
    }

    [ComImport, Guid("bfb7ff88-7239-4fc9-8fa2-07c950be9c6d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioSessionControl2
    {
        // IAudioSessionControl
        [PreserveSig] int GetState(out int etat);
        [PreserveSig] int GetDisplayName(out IntPtr nom);
        [PreserveSig] int SetDisplayName(IntPtr nom, IntPtr contexte);
        [PreserveSig] int GetIconPath(out IntPtr chemin);
        [PreserveSig] int SetIconPath(IntPtr chemin, IntPtr contexte);
        [PreserveSig] int GetGroupingParam(out Guid groupe);
        [PreserveSig] int SetGroupingParam(ref Guid groupe, IntPtr contexte);
        [PreserveSig] int RegisterAudioSessionNotification(IntPtr rappel);
        [PreserveSig] int UnregisterAudioSessionNotification(IntPtr rappel);
        // IAudioSessionControl2
        [PreserveSig] int GetSessionIdentifier(out IntPtr id);
        [PreserveSig] int GetSessionInstanceIdentifier(out IntPtr id);
        [PreserveSig] int GetProcessId(out uint pid);
    }

    [ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IAudioMeterInformation
    {
        [PreserveSig] int GetPeakValue(out float crete);
    }
}
