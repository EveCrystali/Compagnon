using System.ComponentModel;
using System.Diagnostics;
using System.Windows;
using System.Windows.Controls.Primitives;
using System.Windows.Threading;

namespace PilouBureau;

// Portes de secours : l'icône près de l'horloge (ZoneNotification.cs), les relances de l'exe (Instance.cs),
// « Redémarrer Pilou ». Elles ne passent jamais par le menu clic droit de l'overlay.
public sealed partial class FenetrePilou
{
    private ZoneNotification? _zoneNotif;
    // Ramené à la main (icône) : visible un moment même si la discrétion (plein écran, visio…) le cachait.
    private double _ramenePlusQueDiscretJusque = -1e9;

    public void BrancherRelais()
    {
        try
        {
            _zoneNotif = new ZoneNotification(Dispatcher);
        }
        catch (Win32Exception)
        {
            return; // pas de fenêtre relais : l'overlay marche sans
        }
        _zoneNotif.Relance += () => Ramener(false);
        _zoneNotif.QuitterDemande += () => Application.Current.Shutdown();
        _zoneNotif.Choix += Choisir;
        _zoneNotif.IconeVisible = _reglages.IconeNotification;
        Application.Current.Exit += (_, _) => _zoneNotif?.Dispose();
    }

    private void Choisir(ChoixNotification choix)
    {
        switch (choix)
        {
            case ChoixNotification.Afficher:
                Ramener(true);
                break;
            case ChoixNotification.OuvrirMenu:
                OuvrirMenuDepuisIcone();
                break;
            case ChoixNotification.Expedition:
                OuvrirExpeditions(false);
                break;
            case ChoixNotification.MiseAJour:
                Ramener(true);
                _ = MettreAJour(true);
                break;
            case ChoixNotification.Redemarrer:
                Redemarrer();
                break;
            case ChoixNotification.Quitter:
                Application.Current.Shutdown();
                break;
            case ChoixNotification.Defense:
                LancerDefense();
                break;
        }
    }

    // Pilou revient : fin du « se cacher 10 min », et retour sur un écran s'il était parti hors champ.
    // explicite (clic sur l'icône) : il passe aussi outre la discrétion une minute, et le dit.
    private void Ramener(bool explicite)
    {
        _cacheJusque = -1e9;
        if (explicite) _ramenePlusQueDiscretJusque = Maintenant + 60_000;
        if (_zoneConnue && !_attrape)
        {
            var z = ZoneSous(_x, _yPieds - 10);
            if (_x < z.Left || _x > z.Right || _yPieds < z.Top || _yPieds > z.Bottom + 1)
            {
                _zoneConnue = false; // replacé au prochain pas d'animation, près de Claude
                _auSol = true;
                _vy = 0;
            }
        }
        if (!explicite) return;
        if (!IsVisible) Show();
        // Toujours au-dessus : une autre fenêtre « topmost » a pu passer devant.
        Topmost = false;
        Topmost = true;
        _tSaut = Maintenant;
        Dire("me voilà !", 2500);
    }

    // Le menu clic droit de l'overlay, ouvert depuis l'icône : Pilou revient d'abord, puis le menu s'ouvre au curseur.
    private void OuvrirMenuDepuisIcone()
    {
        Ramener(true);
        var menu = _scene.ContextMenu;
        if (menu is null) return;
        var attente = new DispatcherTimer(DispatcherPriority.Input, Dispatcher) { Interval = TimeSpan.FromMilliseconds(150) };
        attente.Tick += (_, _) =>
        {
            attente.Stop();
            menu.PlacementTarget = _scene;
            menu.Placement = PlacementMode.MousePoint;
            menu.IsOpen = true;
        };
        attente.Start();
    }

    // Relance l'exe (le neuf attend que l'ancien ait quitté : --apres-maj), puis quitte. Mise à jour et redémarrage.
    private bool Relancer(string exe)
    {
        try
        {
            var info = new ProcessStartInfo(exe) { UseShellExecute = true };
            info.ArgumentList.Add("--apres-maj");
            if (_dossier != Signal.Defaut()) info.ArgumentList.Add(_dossier);
            Process.Start(info);
        }
        catch (Exception e) when (e is Win32Exception or InvalidOperationException)
        {
            return false;
        }
        Application.Current.Shutdown();
        return true;
    }

    private void Redemarrer()
    {
        if (Environment.ProcessPath is not { } exe || !Relancer(exe)) Dire("redémarrage impossible : relance-moi depuis le menu Démarrer", 5000);
    }
}
