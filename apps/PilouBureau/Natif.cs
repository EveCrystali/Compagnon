using System.Diagnostics;
using System.Runtime.InteropServices;

namespace PilouBureau;

// Accès Win32 : trouver la fenêtre de Claude, lire son cadre, s'y rattacher.
internal static class Natif
{
    [StructLayout(LayoutKind.Sequential)]
    public struct Rect
    {
        public int Left, Top, Right, Bottom;
    }

    private const int GwlExStyle = -20;
    private const int GwlpHwndParent = -8;
    private const long WsExToolWindow = 0x80;
    private const long WsExNoActivate = 0x08000000;
    private const int DwmwaExtendedFrameBounds = 9;

    [DllImport("user32.dll")] private static extern bool IsWindow(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool IsIconic(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
    [DllImport("dwmapi.dll")] private static extern int DwmGetWindowAttribute(IntPtr hwnd, int attribute, out Rect rect, int size);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")] private static extern IntPtr GetWindowLongPtr(IntPtr hwnd, int index);
    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW")] private static extern IntPtr SetWindowLongPtr(IntPtr hwnd, int index, IntPtr value);

    // La plus grande fenêtre visible d'un processus « claude » (l'app de bureau).
    public static IntPtr TrouverClaude()
    {
        var meilleure = IntPtr.Zero;
        long aire = 0;
        foreach (var p in Process.GetProcessesByName("claude"))
        {
            try
            {
                var h = p.MainWindowHandle;
                if (h == IntPtr.Zero || !IsWindowVisible(h)) continue;
                if (!GetWindowRect(h, out var r)) continue;
                long a = (long)(r.Right - r.Left) * (r.Bottom - r.Top);
                if (a > aire)
                {
                    aire = a;
                    meilleure = h;
                }
            }
            catch (InvalidOperationException)
            {
                // processus terminé entre-temps
            }
            finally
            {
                p.Dispose();
            }
        }
        return meilleure;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct Point32
    {
        public int X, Y;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct InfoEcran
    {
        public int Taille;
        public Rect Ecran;
        public Rect Travail;
        public uint Drapeaux;
    }

    [DllImport("user32.dll")] private static extern IntPtr MonitorFromPoint(Point32 pt, uint flags);
    [DllImport("user32.dll")] private static extern bool GetMonitorInfo(IntPtr monitor, ref InfoEcran info);

    // Zone de travail (écran moins la barre des tâches) de l'écran le plus proche d'un point, en pixels physiques.
    public static Rect ZoneTravail(int x, int y)
    {
        var m = MonitorFromPoint(new Point32 { X = x, Y = y }, 2);
        var info = new InfoEcran { Taille = Marshal.SizeOf<InfoEcran>() };
        return GetMonitorInfo(m, ref info) ? info.Travail : new Rect { Left = 0, Top = 0, Right = 1920, Bottom = 1080 };
    }

    [DllImport("user32.dll")] private static extern bool GetCursorPos(out Point32 pt);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hwnd, int cmd);

    [StructLayout(LayoutKind.Sequential)]
    private struct DerniereSaisie
    {
        public uint Taille;
        public uint Instant;
    }

    [DllImport("user32.dll")] private static extern bool GetLastInputInfo(ref DerniereSaisie info);

    // Temps depuis la dernière frappe ou le dernier mouvement de souris, en ms.
    public static double InactifMs()
    {
        var info = new DerniereSaisie { Taille = (uint)Marshal.SizeOf<DerniereSaisie>() };
        return GetLastInputInfo(ref info) ? unchecked((uint)Environment.TickCount - info.Instant) : 0;
    }

    public static (int X, int Y) Souris() => GetCursorPos(out var p) ? (p.X, p.Y) : (int.MinValue, int.MinValue);

    // Met la fenêtre de Claude au premier plan (permis : c'est un clic de la personne sur Pilou).
    public static void Activer(IntPtr hwnd)
    {
        if (hwnd == IntPtr.Zero) return;
        if (IsIconic(hwnd)) ShowWindow(hwnd, 9);
        SetForegroundWindow(hwnd);
    }

    public static bool Valide(IntPtr hwnd) => hwnd != IntPtr.Zero && IsWindow(hwnd) && IsWindowVisible(hwnd);

    public static bool Reduite(IntPtr hwnd) => IsIconic(hwnd);

    // Cadre visible (sans l'ombre DWM), en pixels physiques.
    public static Rect? Cadre(IntPtr hwnd)
    {
        if (DwmGetWindowAttribute(hwnd, DwmwaExtendedFrameBounds, out var r, Marshal.SizeOf<Rect>()) == 0) return r;
        return GetWindowRect(hwnd, out r) ? r : null;
    }

    // Fenêtre possédée par Claude : toujours juste au-dessus d'elle, jamais au-dessus des autres
    // applis, cachée quand Claude est réduite. Pas d'Alt+Tab, ne vole pas le focus.
    public static void Rattacher(IntPtr nous, IntPtr proprietaire)
    {
        SetWindowLongPtr(nous, GwlpHwndParent, proprietaire);
    }

    public static void StyleDiscret(IntPtr nous)
    {
        var ex = GetWindowLongPtr(nous, GwlExStyle).ToInt64();
        SetWindowLongPtr(nous, GwlExStyle, new IntPtr(ex | WsExToolWindow | WsExNoActivate));
    }
}
