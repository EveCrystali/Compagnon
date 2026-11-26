using System.Diagnostics;
using System.Runtime.InteropServices;

namespace PilouBureau;

// L'autre Pilou sous Windows : mutex nommé de la session, et fenêtre relais (ZoneNotification) jointe par
// SendMessageTimeout. SMTO_ABORTIFHUNG : un Pilou figé ne nous bloque pas, il répond « non » et on le remplace.
internal sealed class AutreInstanceWindows : IAutreInstance, IDisposable
{
    private readonly Mutex? _verrou;
    private readonly bool _libre;
    private bool _tenu;

    public AutreInstanceWindows(string nom)
    {
        try
        {
            _verrou = new Mutex(true, nom, out _libre);
        }
        catch (UnauthorizedAccessException)
        {
            // verrou tenu par un Pilou lancé en administrateur : on ne peut ni le prendre ni l'attendre
            _verrou = null;
            _libre = false;
        }
    }

    public bool Prendre() => _tenu = _libre;

    public bool Attendre(TimeSpan delai)
    {
        if (_verrou is null) return false;
        try
        {
            return _tenu = _verrou.WaitOne(delai);
        }
        catch (AbandonedMutexException)
        {
            return _tenu = true; // l'autre a été arrêté sans rendre le verrou : il est à nous
        }
    }

    public bool DemanderAfficher() => Envoyer(ZoneNotification.MessageAfficher);

    public bool DemanderQuitter() => Envoyer(ZoneNotification.MessageQuitter);

    private static bool Envoyer(int message)
    {
        // Un Pilou qui démarre n'a pas encore sa fenêtre relais : on lui laisse quelques secondes.
        var chrono = Stopwatch.StartNew();
        while (chrono.Elapsed < TimeSpan.FromSeconds(8))
        {
            var h = FindWindowW(null, ZoneNotification.TitreRelais);
            if (h != IntPtr.Zero)
                return SendMessageTimeoutW(h, message, IntPtr.Zero, IntPtr.Zero, SmtoAbortIfHung | SmtoBlock, 5000, out var r) != IntPtr.Zero
                       && r == ZoneNotification.Reponse;
            Thread.Sleep(250);
        }
        return false;
    }

    public void Forcer()
    {
        int nous = Environment.ProcessId, session = Process.GetCurrentProcess().SessionId;
        foreach (var p in Process.GetProcessesByName("PilouBureau"))
        {
            try
            {
                if (p.Id == nous || p.SessionId != session) continue;
                p.Kill();
                p.WaitForExit(3000);
            }
            catch (Exception e) when (e is InvalidOperationException or System.ComponentModel.Win32Exception or NotSupportedException)
            {
                // déjà parti, ou pas à nous (administrateur)
            }
            finally
            {
                p.Dispose();
            }
        }
    }

    // En quittant, on rend le verrou : le Pilou suivant (mise à jour, redémarrage) le prend aussitôt.
    public void Dispose()
    {
        if (_tenu)
        {
            try
            {
                _verrou?.ReleaseMutex();
            }
            catch (ApplicationException)
            {
                // pas tenu par ce fil
            }
        }
        _verrou?.Dispose();
    }

    private const int SmtoBlock = 0x1, SmtoAbortIfHung = 0x2;

    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr FindWindowW(string? classe, string titre);

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessageTimeoutW(IntPtr hwnd, int msg, IntPtr w, IntPtr l, int drapeaux, int delaiMs, out IntPtr resultat);
}
