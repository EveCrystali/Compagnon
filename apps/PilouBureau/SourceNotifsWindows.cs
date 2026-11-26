using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Threading;
#if LECTEUR_NOTIFS
using global::Windows.UI.Notifications;
using global::Windows.UI.Notifications.Management;
#endif

namespace PilouBureau;

// Lecture des notifications des autres applis par l'API documentée de Windows, UserNotificationListener
// (Windows.UI.Notifications.Management). Voir docs/NOTIFICATIONS.md.
//
// Ce que dit la documentation Microsoft : l'appli doit déclarer la capacité « userNotificationListener »
// dans un manifeste de package, donc avoir une IDENTITÉ DE PACKAGE (MSIX, ou package « avec emplacement
// externe » signé), puis l'utilisateur doit accepter (RequestAccessAsync). Pilou est livré non empaqueté :
// sans identité, cette source se déclare indisponible et n'appelle pas l'API (aucun contournement, aucune
// API non documentée). Si une identité est enregistrée (docs/NOTIFICATIONS.md, « Donner une identité à
// Pilou »), elle demande l'accès puis relève les nouvelles notifications toutes les 2 s.
//
// CONFIDENTIALITÉ : le texte lu est passé tel quel à FiltreNotifs puis à la bulle ; rien n'est écrit,
// journalisé ni envoyé. RemoveNotification n'est jamais appelé : Pilou ne touche pas au centre de notifications.
internal sealed class SourceNotifsWindows : ISourceNotifications
{
    private const int ErreurTamponTropPetit = 122;     // ERROR_INSUFFICIENT_BUFFER : le processus a une identité
    private const int ErreurSansPackage = 15700;       // APPMODEL_ERROR_NO_PACKAGE

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetCurrentPackageFullName(ref int longueur, StringBuilder? nom);

    private readonly Dispatcher _d;
    private DispatcherTimer? _releve;
#if LECTEUR_NOTIFS
    private UserNotificationListener? _ecoute;
    private bool _amorce, _enCours;
#endif
    private readonly HashSet<uint> _vues = new();

#if LECTEUR_NOTIFS
    public event Action<NotifRecue>? Recue;
#else
    // Sans lecteur, rien n'est jamais reçu.
    public event Action<NotifRecue>? Recue { add { } remove { } }
#endif
    public string Etat { get; private set; } = "pas encore démarrée";
    public bool Disponible { get; private set; }

    public SourceNotifsWindows(Dispatcher d) => _d = d;

    // Le processus a-t-il une identité de package ? (méthode documentée : GetCurrentPackageFullName)
    public static bool AIdentite()
    {
        try
        {
            int n = 0;
            int r = GetCurrentPackageFullName(ref n, null);
            return r == ErreurTamponTropPetit;
        }
        catch (Exception e) when (e is EntryPointNotFoundException or DllNotFoundException)
        {
            return false;
        }
    }

#if LECTEUR_NOTIFS
    public async Task DemarrerAsync()
    {
        if (!OperatingSystem.IsWindowsVersionAtLeast(10, 0, 14393))
        {
            Etat = "indisponible : Windows 10 (1607) ou plus récent requis";
            return;
        }
        if (!AIdentite())
        {
            Etat = "indisponible : Windows réserve cette lecture aux applis empaquetées (identité de package)";
            return;
        }
        try
        {
            _ecoute = UserNotificationListener.Current;
            var acces = _ecoute.GetAccessStatus();
            if (acces == UserNotificationListenerAccessStatus.Unspecified) acces = await _ecoute.RequestAccessAsync();
            if (acces != UserNotificationListenerAccessStatus.Allowed)
            {
                Etat = "accès refusé : Paramètres Windows › Confidentialité › Notifications";
                return;
            }
        }
        catch (Exception e) when (e is COMException or UnauthorizedAccessException or InvalidOperationException or TypeLoadException)
        {
            Etat = "indisponible : Windows a refusé l'écoute des notifications";
            return;
        }
        Disponible = true;
        Etat = "active";
        _releve = new DispatcherTimer(TimeSpan.FromSeconds(2), DispatcherPriority.Background, async (_, _) => await Relever(), _d);
        _releve.Start();
        await Relever();
    }

    // Relève par comparaison d'identifiants (méthode de la doc « Determining which notifications were added »).
    // Le premier relevé ne fait que noter ce qui est déjà là : Pilou ne ressort pas les vieilles notifications.
    private async Task Relever()
    {
        if (_ecoute is null || _enCours) return;
        _enCours = true;
        try
        {
            if (_ecoute.GetAccessStatus() != UserNotificationListenerAccessStatus.Allowed)
            {
                Etat = "accès retiré dans les paramètres Windows";
                return;
            }
            var liste = await _ecoute.GetNotificationsAsync(NotificationKinds.Toast);
            var presentes = new HashSet<uint>();
            foreach (var n in liste)
            {
                presentes.Add(n.Id);
                if (!_vues.Add(n.Id) || !_amorce) continue;
                if (Lire(n) is { } recue) Recue?.Invoke(recue);
            }
            _vues.IntersectWith(presentes);
            _amorce = true;
        }
        catch (Exception e) when (e is COMException or UnauthorizedAccessException or InvalidOperationException)
        {
            // relevé manqué : on retentera dans 2 s
        }
        finally
        {
            _enCours = false;
        }
    }

    // Une notification lue sans planter les autres (conseil de la doc) : appli, premier texte, second texte.
    private static NotifRecue? Lire(UserNotification n)
    {
        try
        {
            string app = "";
            try
            {
                app = n.AppInfo?.DisplayInfo?.DisplayName ?? "";
            }
            catch (Exception e) when (e is COMException or InvalidOperationException)
            {
            }
            var liaison = n.Notification?.Visual?.GetBinding(KnownNotificationBindings.ToastGeneric);
            if (liaison is null) return null;
            var textes = liaison.GetTextElements();
            string titre = textes.Count > 0 ? textes[0].Text : "";
            string corps = textes.Count > 1 ? textes[1].Text : "";
            return new NotifRecue(app, titre, corps, n.Id);
        }
        catch (Exception e) when (e is COMException or InvalidOperationException or ArgumentException)
        {
            return null;
        }
    }

#else
    public Task DemarrerAsync()
    {
        Etat = AIdentite()
            ? "indisponible : cette version de Pilou n'embarque pas le lecteur (voir docs/NOTIFICATIONS.md)"
            : "indisponible : Windows réserve cette lecture aux applis empaquetées (identité de package)";
        return Task.CompletedTask;
    }

#endif

    public void Dispose()
    {
        _releve?.Stop();
        _releve = null;
#if LECTEUR_NOTIFS
        _ecoute = null;
#endif
        _vues.Clear();
        Disponible = false;
        Etat = "coupée";
    }
}
