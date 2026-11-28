using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Threading;

namespace PilouBureau;

// Lecture des musiques de l'Aventure sur le PC (docs/SONS.md) : waveOut de Windows, quatre tampons de 100 ms remplis
// par la table de mixage (Melangeur, Musique.cs).
public static partial class Musique
{
    private static readonly Melangeur Table = new(Boucle, EstMotif);
    private static Thread? _fil;

    // Une ligne dans la fenêtre Aventure : la musique suit la campagne ouverte et l'ambiance suit le décor, seulement
    // tant que la fenêtre est au premier plan, hors visio, réunion et présentation (docs/SONS.md).
    // `demande` : le champ facultatif « musique » de la scène ou du nœud en cours (voir Pour).
    public static void Suivre(Window w, Func<string?> campagne, Func<string?> ton, Func<string?> decor, Func<string?>? demande = null)
    {
        var minuteur = new DispatcherTimer(DispatcherPriority.Background, w.Dispatcher) { Interval = TimeSpan.FromMilliseconds(250) };
        minuteur.Tick += (_, _) =>
        {
            try
            {
                int gain = Gain(Sons.NiveauMusique());
                bool actif = gain > 0 && w.IsActive && w.WindowState != WindowState.Minimized && !Sons.Appel();
                Viser(actif ? Pour(campagne(), ton(), demande?.Invoke()) : null, actif ? Ambiance(decor()) : null, gain);
            }
            catch (Exception e) when (e is InvalidOperationException or IOException)
            {
                Viser(null, null, 0);
            }
        };
        w.Closed += (_, _) => { minuteur.Stop(); Viser(null, null, 0); };
        minuteur.Start();
    }

    private static void Viser(string? musique, string? ambiance, int gain)
    {
        Table.Viser(musique, ambiance, gain);
        lock (Table)
        {
            if (Table.Silencieux || _fil is not null) return;
            _fil = new Thread(Jouer) { IsBackground = true, Name = "Musique de Pilou", Priority = ThreadPriority.AboveNormal };
            _fil.Start();
        }
    }

    // Fil de lecture : quatre tampons de 100 ms qui tournent ; il s'arrête (et rend la sortie audio) une fois tout éteint.
    private static void Jouer()
    {
        const int Tampons = 4, Taille = Taux / 10;
        IntPtr h = IntPtr.Zero;
        var entetes = new IntPtr[Tampons];
        var donnees = new IntPtr[Tampons];
        var enCours = new bool[Tampons];
        int tailleEntete = Marshal.SizeOf<EnteteOnde>();
        int drapeaux = (int)Marshal.OffsetOf<EnteteOnde>(nameof(EnteteOnde.Drapeaux));
        var bloc = new short[Taille];
        try
        {
            var format = new FormatOnde { Format = 1, Canaux = 1, Taux = Taux, OctetsParSeconde = Taux * 2, Bloc = 2, Bits = 16 };
            if (waveOutOpen(out h, uint.MaxValue, ref format, IntPtr.Zero, IntPtr.Zero, 0) != 0) { h = IntPtr.Zero; return; }
            for (int i = 0; i < Tampons; i++)
            {
                entetes[i] = Marshal.AllocHGlobal(tailleEntete);
                donnees[i] = Marshal.AllocHGlobal(Taille * 2);
            }
            while (true)
            {
                bool tousLibres = true;
                for (int i = 0; i < Tampons; i++)
                {
                    if (enCours[i] && (Marshal.ReadInt32(entetes[i], drapeaux) & 1) == 0) { tousLibres = false; continue; }
                    if (enCours[i]) { waveOutUnprepareHeader(h, entetes[i], (uint)tailleEntete); enCours[i] = false; }
                    if (Table.Silencieux) continue;
                    Table.Remplir(bloc);
                    Marshal.Copy(bloc, 0, donnees[i], Taille);
                    Marshal.StructureToPtr(new EnteteOnde { Donnees = donnees[i], Longueur = Taille * 2 }, entetes[i], false);
                    waveOutPrepareHeader(h, entetes[i], (uint)tailleEntete);
                    waveOutWrite(h, entetes[i], (uint)tailleEntete);
                    enCours[i] = true;
                    tousLibres = false;
                }
                if (tousLibres)
                {
                    lock (Table)
                    {
                        if (Table.Silencieux) { _fil = null; return; }
                    }
                }
                Thread.Sleep(20);
            }
        }
        catch (Exception e) when (e is DllNotFoundException or EntryPointNotFoundException or OutOfMemoryException)
        {
            // pas de sortie audio : silence
        }
        finally
        {
            if (h != IntPtr.Zero)
            {
                waveOutReset(h);
                for (int i = 0; i < Tampons; i++)
                    if (enCours[i]) waveOutUnprepareHeader(h, entetes[i], (uint)tailleEntete);
                waveOutClose(h);
            }
            for (int i = 0; i < Tampons; i++)
            {
                if (entetes[i] != IntPtr.Zero) Marshal.FreeHGlobal(entetes[i]);
                if (donnees[i] != IntPtr.Zero) Marshal.FreeHGlobal(donnees[i]);
            }
            lock (Table)
            {
                if (_fil == Thread.CurrentThread) _fil = null;
            }
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct FormatOnde
    {
        public ushort Format, Canaux;
        public int Taux, OctetsParSeconde;
        public ushort Bloc, Bits, Extra;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct EnteteOnde
    {
        public IntPtr Donnees;
        public int Longueur, Enregistres;
        public IntPtr Utilisateur;
        public int Drapeaux, Boucles;
        public IntPtr Suivant, Reserve;
    }

    [DllImport("winmm.dll")] private static extern int waveOutOpen(out IntPtr h, uint peripherique, ref FormatOnde format, IntPtr rappel, IntPtr instance, uint options);
    [DllImport("winmm.dll")] private static extern int waveOutPrepareHeader(IntPtr h, IntPtr entete, uint taille);
    [DllImport("winmm.dll")] private static extern int waveOutUnprepareHeader(IntPtr h, IntPtr entete, uint taille);
    [DllImport("winmm.dll")] private static extern int waveOutWrite(IntPtr h, IntPtr entete, uint taille);
    [DllImport("winmm.dll")] private static extern int waveOutReset(IntPtr h);
    [DllImport("winmm.dll")] private static extern int waveOutClose(IntPtr h);
}
