using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace PilouBureau;

// Mise à jour de Pilou lui-même : une minute après le démarrage, puis toutes les 2 h.
public sealed partial class FenetrePilou
{
    private DispatcherTimer? _mise;
    private bool _miseEnCours;

    // Seule une copie installée (…\.claude\compagnon\bureau) se met à jour seule ; une copie de développement, non.
    private static bool Installee =>
        Environment.ProcessPath is { } p
        && p.Replace('/', '\\').Contains(@"\.claude\compagnon\bureau\", StringComparison.OrdinalIgnoreCase);

    private void DemarrerMises()
    {
        _mise = new DispatcherTimer { Interval = TimeSpan.FromMinutes(1) };
        _mise.Tick += (_, _) =>
        {
            _mise.Interval = TimeSpan.FromHours(2);
            if (_reglages.MiseAJourAuto && Installee) _ = MettreAJour(false);
        };
        _mise.Start();
    }

    private MenuItem MenuVersion()
    {
        var m = new MenuItem { Header = $"Version {Mise.Actuelle}" };
        m.Items.Add(Entree("Chercher une mise à jour maintenant", () => _ = MettreAJour(true)));
        m.Items.Add(Case("Se mettre à jour tout seul", _reglages.MiseAJourAuto, v => _reglages.MiseAJourAuto = v));
        return m;
    }

    private async Task MettreAJour(bool demande)
    {
        if (_miseEnCours) return;
        _miseEnCours = true;
        try
        {
            var p = await Mise.Chercher();
            if (p is null)
            {
                if (demande) Dire($"déjà à jour ({Mise.Actuelle})", 3500);
                return;
            }
            Dire($"nouvelle version {p.Version}, j'arrive…", 6000);
            var exe = await Mise.Installer(p);
            if (exe is null)
            {
                if (demande) Dire("mise à jour impossible pour l'instant", 4000);
                return;
            }
            await Task.Run(Mise.MettreAJourMod);
            if (!Relancer(exe) && demande) Dire("mise à jour posée : redémarre-moi (menu Démarrer → Pilou)", 5000);
        }
        catch (Exception e) when (e is IOException or System.ComponentModel.Win32Exception or InvalidOperationException)
        {
            if (demande) Dire("mise à jour impossible pour l'instant", 4000);
        }
        finally
        {
            _miseEnCours = false;
        }
    }
}
