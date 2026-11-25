using System.IO;
using System.Windows;

namespace PilouBureau;

public static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        // --signal <source> … : un autre logiciel (Codex, script…) signale un événement, puis on rend la main.
        var iSignal = Array.IndexOf(args, "--signal");
        if (iSignal >= 0)
        {
            var dossierSignal = args.FirstOrDefault(a => a.StartsWith("--dossier="))?["--dossier=".Length..] ?? Signal.Defaut();
            return Signal.Principal(args[(iSignal + 1)..], dossierSignal);
        }
        // --brancher codex / --debrancher codex : pose ou retire les hooks de Pilou chez Codex.
        if (args.Length >= 2 && args[0] is "--brancher" or "--debrancher")
            return Integrations.Ligne(args[0] == "--brancher", args[1]);

        // Une seule instance : chaque session Claude tente de le lancer.
        bool rendu = args.Any(a => a.StartsWith("--instantane="));
        // --apres-maj : lancé par l'ancienne version, qui est en train de quitter ; on attend sa place.
        bool apresMaj = args.Contains("--apres-maj");
        args = args.Where(a => a != "--apres-maj").ToArray();
        using var unique = new Mutex(true, rendu ? @"Local\PilouBureau-essai" : @"Local\PilouBureau", out var premier);
        if (!premier && apresMaj)
        {
            try
            {
                premier = unique.WaitOne(15_000);
            }
            catch (AbandonedMutexException)
            {
                premier = true;
            }
        }
        if (!premier) return 0;
        Mise.Nettoyer();

        // --devant : premier plan, sans rattachement à Claude (essai visuel).
        bool devant = args.Contains("--devant");
        // --instantane=<png> : rend la fenêtre dans un PNG au bout de 2,5 s puis quitte (essai sans écran).
        var instantane = args.FirstOrDefault(a => a.StartsWith("--instantane="))?["--instantane=".Length..];
        var essai = args.FirstOrDefault(a => a.StartsWith("--essai="))?["--essai=".Length..];
        args = args.Where(a => a != "--devant" && !a.StartsWith("--instantane=") && !a.StartsWith("--essai=")).ToArray();
        var dossier = args.Length > 0 ? args[0] : Signal.Defaut();
        var app = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        var fenetre = new FenetrePilou(dossier, devant);
        fenetre.Show();
        if (essai is not null)
        {
            var declic = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(900) };
            declic.Tick += (_, _) =>
            {
                declic.Stop();
                fenetre.Essai(essai);
            };
            declic.Start();
        }
        if (instantane is not null)
        {
            var minuteur = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(2500) };
            minuteur.Tick += (_, _) =>
            {
                minuteur.Stop();
                fenetre.Instantane(instantane);
                app.Shutdown();
            };
            minuteur.Start();
        }
        return app.Run();
    }
}
