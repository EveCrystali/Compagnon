using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Interop;
using System.Windows.Threading;

namespace PilouBureau;

// Icône de Pilou près de l'horloge (Shell_NotifyIcon, sans WinForms) et fenêtre relais, cachée, qui la porte.
// Porte de secours indépendante de l'overlay : clic gauche, Pilou revient ; clic droit, un menu natif
// (TrackPopupMenu) pour le ramener, ouvrir son menu, chercher une mise à jour, le redémarrer ou le quitter.
// La fenêtre relais reçoit aussi les demandes des autres lancements de l'exe (InstanceWindows.cs).
// Fenêtre de premier niveau cachée, pas « message-only » : seules les premières reçoivent TaskbarCreated
// (l'explorateur a redémarré : l'icône est à reposer).
internal sealed class ZoneNotification : IDisposable
{
    public const string TitreRelais = "PilouBureau-relais";
    private const int WmApp = 0x8000;
    public const int MessageAfficher = WmApp + 0x50, MessageQuitter = WmApp + 0x51;
    private const int MessageIcone = WmApp + 0x52;
    public static readonly IntPtr Reponse = new(0x9110);

    // Un autre lancement de l'exe : « montre-toi » (sans forcer la discrétion) ; « quitte » (--redemarrer).
    public event Action? Relance;
    public event Action? QuitterDemande;
    // Clic gauche sur l'icône, ou un choix de son menu.
    public event Action<ChoixNotification>? Choix;
    // L'état de l'aventure pour l'entrée « Aventure… » du menu (lu à chaque ouverture) ; null : le texte fixe.
    public Func<string>? TexteAventure;

    private readonly Dispatcher _dispatcher;
    private readonly HwndSource _source;
    private readonly int _taskbarCreated;
    private IntPtr _hicon;
    private bool _posee, _voulue;
    private DispatcherTimer? _reessai;

    public ZoneNotification(Dispatcher dispatcher)
    {
        _dispatcher = dispatcher;
        _taskbarCreated = RegisterWindowMessageW("TaskbarCreated");
        _source = new HwndSource(new HwndSourceParameters(TitreRelais)
        {
            WindowStyle = unchecked((int)0x80000000), // WS_POPUP, jamais visible
            ExtendedWindowStyle = 0x80,               // WS_EX_TOOLWINDOW : ni barre des tâches ni Alt+Tab
            Width = 0,
            Height = 0,
        });
        _source.AddHook(Crochet);
        // Un Pilou lancé en administrateur doit encore entendre les lancements ordinaires (filtre UIPI).
        foreach (var m in new[] { MessageAfficher, MessageQuitter, _taskbarCreated })
            ChangeWindowMessageFilterEx(_source.Handle, m, 1, IntPtr.Zero);
    }

    public bool IconeVisible
    {
        get => _voulue;
        set
        {
            _voulue = value;
            if (value) Poser();
            else Retirer();
        }
    }

    private NotifyIconData Donnees(int drapeaux) => new()
    {
        Taille = Marshal.SizeOf<NotifyIconData>(),
        Fenetre = _source.Handle,
        Id = 1,
        Drapeaux = drapeaux,
        MessageRappel = MessageIcone,
        Icone = _hicon,
        Infobulle = MenuNotification.Infobulle,
        Info = "",
        TitreInfo = "",
    };

    private void Poser()
    {
        if (_posee || !_voulue) return;
        if (_hicon == IntPtr.Zero) _hicon = ChargerIcone();
        var d = Donnees(NifMessage | NifIcon | NifTip | NifShowTip);
        if (Shell_NotifyIconW(NimAdd, ref d))
        {
            d.Version = NotifyIconVersion4;
            Shell_NotifyIconW(NimSetVersion, ref d);
            _posee = true;
            _reessai?.Stop();
            return;
        }
        // Au démarrage de Windows, la barre des tâches n'est pas toujours prête : on réessaie un moment.
        if (_reessai is null)
        {
            int essais = 0;
            _reessai = new DispatcherTimer(TimeSpan.FromSeconds(2), DispatcherPriority.Background, (_, _) =>
            {
                if (_posee || !_voulue || ++essais > 30) _reessai!.Stop();
                else Poser();
            }, _dispatcher);
        }
        _reessai.Start();
    }

    private void Retirer()
    {
        _reessai?.Stop();
        if (!_posee) return;
        var d = Donnees(0);
        Shell_NotifyIconW(NimDelete, ref d);
        _posee = false;
    }

    // L'image du .ico embarqué la plus proche de la taille des petites icônes de cet écran.
    private static IntPtr ChargerIcone()
    {
        try
        {
            using var flux = typeof(ZoneNotification).Assembly.GetManifestResourceStream("pilou:icone.ico");
            if (flux is null) return IntPtr.Zero;
            using var m = new MemoryStream();
            flux.CopyTo(m);
            var ico = m.ToArray();
            var entrees = Icone.Entrees(ico);
            int voulue = Math.Max(16, GetSystemMetrics(SmCxSmIcon));
            int i = Icone.Choisir(entrees.Select(e => e.Taille).ToList(), voulue);
            if (i < 0) return IntPtr.Zero;
            var (_, debut, longueur) = entrees[i];
            return CreateIconFromResourceEx(ico[debut..(debut + longueur)], longueur, true, 0x00030000, voulue, voulue, 0);
        }
        catch (IOException)
        {
            return IntPtr.Zero;
        }
    }

    private IntPtr Crochet(IntPtr hwnd, int msg, IntPtr w, IntPtr l, ref bool traite)
    {
        if (msg == MessageAfficher)
        {
            traite = true;
            _dispatcher.BeginInvoke(() => Relance?.Invoke());
            return Reponse;
        }
        if (msg == MessageQuitter)
        {
            traite = true;
            _dispatcher.BeginInvoke(() => QuitterDemande?.Invoke());
            return Reponse;
        }
        if (msg == _taskbarCreated && _taskbarCreated != 0)
        {
            _posee = false;
            Poser();
            return IntPtr.Zero;
        }
        if (msg != MessageIcone) return IntPtr.Zero;
        traite = true;
        switch ((int)(l.ToInt64() & 0xffff))
        {
            case NinSelect or NinKeySelect:
                _dispatcher.BeginInvoke(() => Choix?.Invoke(ChoixNotification.Afficher));
                break;
            case WmContextMenu:
                // Version 4 : le point d'ancrage est dans wParam (coordonnées signées sur 16 bits).
                long p = w.ToInt64();
                Menu((short)(p & 0xffff), (short)((p >> 16) & 0xffff));
                break;
        }
        return IntPtr.Zero;
    }

    // Menu natif : le correctif officiel (SetForegroundWindow avant, WM_NULL après) le ferme bien au clic ailleurs.
    private void Menu(int x, int y)
    {
        var menu = CreatePopupMenu();
        if (menu == IntPtr.Zero) return;
        try
        {
            string? aventure = null;
            try
            {
                aventure = TexteAventure?.Invoke();
            }
            catch (Exception e) when (e is not OutOfMemoryException)
            {
                // le menu s'ouvre quand même, avec le texte fixe
            }
            foreach (var (choix, texte) in MenuNotification.Entrees)
                AppendMenuW(menu, choix is null ? MfSeparator : MfString, choix is { } c ? (IntPtr)(int)c : IntPtr.Zero,
                    choix is { } ch ? MenuNotification.Texte(ch, texte, aventure) : null);
            SetMenuDefaultItem(menu, (int)ChoixNotification.Afficher, 0);
            SetForegroundWindow(_source.Handle);
            int alignement = GetSystemMetrics(SmMenuDropAlignment) != 0 ? TpmRightAlign : TpmLeftAlign;
            int id = TrackPopupMenuEx(menu, TpmReturnCmd | TpmRightButton | TpmBottomAlign | alignement, x, y, _source.Handle, IntPtr.Zero);
            PostMessageW(_source.Handle, 0, IntPtr.Zero, IntPtr.Zero); // WM_NULL
            if (MenuNotification.Lire(id) is { } lu) _dispatcher.BeginInvoke(() => Choix?.Invoke(lu));
        }
        finally
        {
            DestroyMenu(menu);
        }
    }

    // Info-bulle de l'icône (« Pilou t'attend pour son aventure ! ») ; NIM_MODIFY, sans effet si l'icône n'est pas posée.
    public void Infobulle(string texte)
    {
        if (!_posee) return;
        var d = Donnees(NifTip | NifShowTip);
        d.Infobulle = texte.Length > 127 ? texte[..127] : texte;
        Shell_NotifyIconW(NimModify, ref d);
    }

    // Visite guidée (FenetreVisite.cs) : le même menu, ouvert sans clic, refermé par FermerMenu.
    public void MontrerMenu(int x, int y) => Menu(x, y);

    public static void FermerMenu() => EndMenu();

    // Où est l'icône (pixels de ce processus) ; null si elle n'est pas posée ou introuvable.
    public (int X, int Y)? PositionIcone()
    {
        if (!_posee) return null;
        var id = new IdentifiantIcone { Taille = Marshal.SizeOf<IdentifiantIcone>(), Fenetre = _source.Handle, Id = 1 };
        if (Shell_NotifyIconGetRect(ref id, out var r) != 0) return null;
        return ((r.Left + r.Right) / 2, (r.Top + r.Bottom) / 2);
    }

    public void Dispose()
    {
        Retirer();
        if (_hicon != IntPtr.Zero) DestroyIcon(_hicon);
        _hicon = IntPtr.Zero;
        _source.RemoveHook(Crochet);
        _source.Dispose();
    }

    // ---- Win32

    private const int NimAdd = 0, NimModify = 1, NimDelete = 2, NimSetVersion = 4, NotifyIconVersion4 = 4;
    private const int NifMessage = 0x1, NifIcon = 0x2, NifTip = 0x4, NifShowTip = 0x80;
    private const int NinSelect = 0x400, NinKeySelect = 0x401, WmContextMenu = 0x7b;
    private const int MfString = 0x0, MfSeparator = 0x800;
    private const int TpmLeftAlign = 0x0, TpmRightAlign = 0x8, TpmBottomAlign = 0x20, TpmRightButton = 0x2, TpmReturnCmd = 0x100;
    private const int SmCxSmIcon = 49, SmMenuDropAlignment = 40;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct NotifyIconData
    {
        public int Taille;
        public IntPtr Fenetre;
        public int Id;
        public int Drapeaux;
        public int MessageRappel;
        public IntPtr Icone;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string Infobulle;
        public int Etat;
        public int MasqueEtat;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 256)] public string Info;
        public int Version;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)] public string TitreInfo;
        public int DrapeauxInfo;
        public Guid Guid;
        public IntPtr IconeInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IdentifiantIcone
    {
        public int Taille;
        public IntPtr Fenetre;
        public int Id;
        public Guid Guid;
    }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)] private static extern bool Shell_NotifyIconW(int message, ref NotifyIconData donnees);
    [DllImport("shell32.dll")] private static extern int Shell_NotifyIconGetRect(ref IdentifiantIcone id, out Natif.Rect cadre);
    [DllImport("user32.dll")] private static extern bool EndMenu();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int RegisterWindowMessageW(string nom);
    [DllImport("user32.dll")] private static extern bool ChangeWindowMessageFilterEx(IntPtr hwnd, int message, int action, IntPtr info);
    [DllImport("user32.dll")] private static extern int GetSystemMetrics(int index);
    [DllImport("user32.dll")] private static extern IntPtr CreateIconFromResourceEx(byte[] octets, int taille, bool icone, int version, int cx, int cy, int drapeaux);
    [DllImport("user32.dll")] private static extern bool DestroyIcon(IntPtr icone);
    [DllImport("user32.dll")] private static extern IntPtr CreatePopupMenu();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern bool AppendMenuW(IntPtr menu, int drapeaux, IntPtr id, string? texte);
    [DllImport("user32.dll")] private static extern bool SetMenuDefaultItem(IntPtr menu, int id, int parPosition);
    [DllImport("user32.dll")] private static extern int TrackPopupMenuEx(IntPtr menu, int drapeaux, int x, int y, IntPtr hwnd, IntPtr parametres);
    [DllImport("user32.dll")] private static extern bool DestroyMenu(IntPtr menu);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")] private static extern bool PostMessageW(IntPtr hwnd, int msg, IntPtr w, IntPtr l);
}
