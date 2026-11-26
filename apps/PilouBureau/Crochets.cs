using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace PilouBureau;

// Crochet clavier bas niveau (WH_KEYBOARD_LL), installé seulement si « Pilou tape avec moi » ou
// « Appareil photo » est coché.
//
// CONFIDENTIALITÉ : ce crochet ne fait que COMPTER. À chaque touche relâchée, il signale « une frappe »,
// sans dire laquelle : aucun caractère, aucun code de touche n'est lu, gardé, écrit ni journalisé. La seule
// exception est la touche Impr. écran : son code (VK_SNAPSHOT) est comparé, sur place, pour savoir si une
// capture d'écran vient d'être faite ; il n'est pas gardé non plus. Les frappes simulées par un logiciel
// (drapeau « injected ») sont ignorées. On compte les relâchements (une touche maintenue ne compte qu'une fois).
internal sealed class CrochetClavier : IDisposable
{
    private const int WhKeyboardLl = 13;
    private const int WmKeyUp = 0x0101, WmSysKeyUp = 0x0105;
    private const int VkSnapshot = 0x2C;
    private const int LlkhfInjected = 0x10;

    private delegate IntPtr Rappel(int code, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)] private static extern IntPtr SetWindowsHookExW(int idHook, Rappel fn, IntPtr hMod, uint threadId);
    [DllImport("user32.dll")] private static extern bool UnhookWindowsHookEx(IntPtr hook);
    [DllImport("user32.dll")] private static extern IntPtr CallNextHookEx(IntPtr hook, int code, IntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr GetModuleHandleW(string? nom);

    private readonly Rappel _rappel; // gardé en vie tant que le crochet existe
    private IntPtr _crochet;

    // Une touche a été relâchée (laquelle : on ne le sait pas).
    public event Action? Frappe;
    // La touche Impr. écran a été relâchée.
    public event Action? ImprEcran;

    public bool Actif => _crochet != IntPtr.Zero;

    public CrochetClavier()
    {
        _rappel = Recevoir;
    }

    public bool Installer()
    {
        if (Actif) return true;
        try
        {
            _crochet = SetWindowsHookExW(WhKeyboardLl, _rappel, GetModuleHandleW(null), 0);
        }
        catch (Exception e) when (e is EntryPointNotFoundException or DllNotFoundException)
        {
            _crochet = IntPtr.Zero;
        }
        return Actif;
    }

    // Appelé par Windows sur le fil de l'interface (celui qui a posé le crochet) : il doit rendre la main vite.
    private IntPtr Recevoir(int code, IntPtr wParam, IntPtr lParam)
    {
        if (code >= 0 && (wParam == WmKeyUp || wParam == WmSysKeyUp))
        {
            // KBDLLHOOKSTRUCT : vkCode (0), scanCode (4), flags (8). Seuls flags et la comparaison à VK_SNAPSHOT servent.
            int drapeaux = Marshal.ReadInt32(lParam, 8);
            if ((drapeaux & LlkhfInjected) == 0)
            {
                if (Marshal.ReadInt32(lParam, 0) == VkSnapshot) ImprEcran?.Invoke();
                else Frappe?.Invoke();
            }
        }
        return CallNextHookEx(_crochet, code, wParam, lParam);
    }

    public void Dispose()
    {
        if (_crochet != IntPtr.Zero) UnhookWindowsHookEx(_crochet);
        _crochet = IntPtr.Zero;
    }
}

// Capture d'écran : une image arrive dans le presse-papiers (Win+Maj+S, Impr. écran), ou un fichier apparaît
// dans le dossier Captures d'écran (Win+Impr. écran). On ne lit jamais l'image : on demande seulement à
// Windows « y a-t-il une image ? », et pour le dossier on regarde l'extension du nom du fichier créé.
internal sealed class GuetteurCaptures : IDisposable
{
    private const int WmClipboardUpdate = 0x031D;
    private const uint CfBitmap = 2, CfDib = 8, CfDibV5 = 17;

    [DllImport("user32.dll", SetLastError = true)] private static extern bool AddClipboardFormatListener(IntPtr hwnd);
    [DllImport("user32.dll", SetLastError = true)] private static extern bool RemoveClipboardFormatListener(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool IsClipboardFormatAvailable(uint format);

    private readonly List<FileSystemWatcher> _dossiers = new();
    private IntPtr _fenetre;
    private System.Windows.Interop.HwndSource? _source;

    public event Action<SourceCapture>? Capture;

    public void Demarrer(IntPtr fenetre, System.Windows.Threading.Dispatcher d)
    {
        Arreter();
        _fenetre = fenetre;
        _source = System.Windows.Interop.HwndSource.FromHwnd(fenetre);
        _source?.AddHook(Message);
        try
        {
            if (!AddClipboardFormatListener(fenetre)) _fenetre = IntPtr.Zero;
        }
        catch (Exception e) when (e is EntryPointNotFoundException or DllNotFoundException)
        {
            _fenetre = IntPtr.Zero;
        }
        foreach (var chemin in DossiersCaptures())
        {
            try
            {
                var w = new FileSystemWatcher(chemin) { IncludeSubdirectories = false, NotifyFilter = NotifyFilters.FileName };
                w.Created += (_, e) =>
                {
                    if (EstImage(e.Name)) d.BeginInvoke(() => Capture?.Invoke(SourceCapture.Dossier));
                };
                w.EnableRaisingEvents = true;
                _dossiers.Add(w);
            }
            catch (Exception e) when (e is IOException or ArgumentException or UnauthorizedAccessException or Win32Exception)
            {
                // dossier inaccessible : le presse-papiers et la touche suffisent
            }
        }
    }

    public static bool EstImage(string? nom) =>
        nom is not null && Path.GetExtension(nom).ToLowerInvariant() is ".png" or ".jpg" or ".jpeg" or ".bmp" or ".gif";

    // Pictures\Screenshots (et sa redirection OneDrive), et les variantes OneDrive courantes s'il y en a.
    public static IEnumerable<string> DossiersCaptures()
    {
        var candidats = new List<string>();
        var images = Environment.GetFolderPath(Environment.SpecialFolder.MyPictures);
        var profil = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        if (images != "") candidats.Add(Path.Combine(images, "Screenshots"));
        if (profil != "") candidats.Add(Path.Combine(profil, "Pictures", "Screenshots"));
        foreach (var od in new[] { Environment.GetEnvironmentVariable("OneDrive"), Environment.GetEnvironmentVariable("OneDriveConsumer") })
        {
            if (string.IsNullOrWhiteSpace(od)) continue;
            foreach (var sous in new[] { "Pictures", "Images" })
            foreach (var nom in new[] { "Screenshots", "Captures d’écran", "Captures d'écran" })
                candidats.Add(Path.Combine(od, sous, nom));
        }
        return candidats.Distinct(StringComparer.OrdinalIgnoreCase).Where(Directory.Exists);
    }

    private IntPtr Message(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool traite)
    {
        if (msg == WmClipboardUpdate && _fenetre != IntPtr.Zero)
        {
            // Seulement « une image est là ? » : le contenu n'est ni ouvert ni copié.
            bool image = IsClipboardFormatAvailable(CfBitmap) || IsClipboardFormatAvailable(CfDib) || IsClipboardFormatAvailable(CfDibV5);
            if (image) Capture?.Invoke(SourceCapture.PressePapiers);
        }
        return IntPtr.Zero;
    }

    public void Arreter()
    {
        if (_fenetre != IntPtr.Zero) RemoveClipboardFormatListener(_fenetre);
        _fenetre = IntPtr.Zero;
        _source?.RemoveHook(Message);
        _source = null;
        foreach (var w in _dossiers) w.Dispose();
        _dossiers.Clear();
    }

    public void Dispose() => Arreter();
}
