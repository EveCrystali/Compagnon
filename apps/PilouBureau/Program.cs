using System.IO;
using System.Windows;

namespace PilouBureau;

public static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        // --essais-disponibles=<fichier> : écrit ce que cet exe sait montrer (version, scènes, rayons), puis rend la main.
        // Le script de tournage le lit avant de filmer ; il ne touche ni au Pilou qui tourne ni à ses données.
        if (args.FirstOrDefault(a => a.StartsWith("--essais-disponibles=", StringComparison.Ordinal)) is { } liste)
        {
            try
            {
                File.WriteAllText(liste["--essais-disponibles=".Length..].Trim('"'), Tournage.Disponibles(Mise.Actuelle));
                return 0;
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException or ArgumentException or NotSupportedException)
            {
                return 3;
            }
        }
        var lancement = Lancement.Analyser(args);
        // --signal <source> … : un autre logiciel (Codex, script…) signale un événement, puis on rend la main.
        if (lancement.Mode == ModeLancement.Signal)
        {
            var iSignal = Array.IndexOf(args, "--signal");
            var dossierSignal = args.FirstOrDefault(a => a.StartsWith("--dossier="))?["--dossier=".Length..] ?? Signal.Defaut();
            return Signal.Principal(args[(iSignal + 1)..], dossierSignal);
        }
        // --brancher codex / --debrancher codex : pose ou retire les hooks de Pilou chez Codex.
        if (lancement.Mode == ModeLancement.Brancher)
            return Integrations.Ligne(args[0] == "--brancher", args[1]);

        // Une seule instance : chaque session Claude tente de le lancer. Relancer l'exe montre le Pilou qui tourne
        // (et remplace un Pilou figé) ; --redemarrer arrête proprement celui qui tourne et prend sa place ;
        // --apres-maj : lancé par l'ancienne version, qui est en train de quitter, on attend sa place (Instance.cs).
        // Les essais (--instantane, --film, --essai) ont leur propre verrou : ils tournent à côté, sans rien toucher.
        bool principal = lancement.Mode == ModeLancement.Principal;
        args = Lancement.Reste(args);
        // Tournage (outils/tourner-ecran-gauche.ps1, Tournage.cs) : --visite-guidee[=<chronologie.json>], --ecran=gauche,
        // --placer=x,y. La visite guidée prend la place du Pilou habituel (avec --redemarrer), en mode démo : profil,
        // amis et réglages fictifs en mémoire, dans le dossier de démo donné (jamais le vrai dossier de Pilou).
        var (tournage, sansTournage) = OptionsTournage.Analyser(args);
        args = sansTournage;
        if (tournage.Visite && (args.Length == 0 || args[0].StartsWith("--")
            || Path.GetFullPath(args[0]).TrimEnd('\\', '/').Equals(Path.GetFullPath(Signal.Defaut()).TrimEnd('\\', '/'), StringComparison.OrdinalIgnoreCase)))
            return 2; // visite guidée : un dossier de démo est obligatoire
        // Les captures (--captures=, voir CapturesEssai) quittent seules : leur verrou est à elles, pour tourner à côté d'un
        // autre essai ouvert (par exemple celui d'une autre session de travail).
        bool captures_ = args.Any(a => a.StartsWith("--captures=", StringComparison.Ordinal));
        using var autre = new AutreInstanceWindows(principal ? @"Local\PilouBureau"
            : captures_ ? $@"Local\PilouBureau-captures-{Environment.ProcessId}" : @"Local\PilouBureau-essai");
        var issue = principal ? Instance.Decider(lancement, autre) : autre.Prendre() ? Issue.Demarrer : Issue.Rendre;
        if (issue == Issue.Rendre) return 0;
        if (principal) Mise.Nettoyer();                 // un essai ne touche pas au dossier de l'exe installé

        // --devant : premier plan, sans rattachement à Claude (essai visuel).
        bool devant = args.Contains("--devant");
        // --instantane=<png> : rend la fenêtre dans un PNG au bout de 2,5 s puis quitte (essai sans écran).
        var instantane = args.FirstOrDefault(a => a.StartsWith("--instantane="))?["--instantane=".Length..];
        var essai = args.FirstOrDefault(a => a.StartsWith("--essai="))?["--essai=".Length..];
        // --film=<dossier> [--duree=6] [--ips=15] : enregistre la fenêtre de Pilou elle-même, image par image (PNG
        // transparents), puis quitte. Seuls les pixels de Pilou et de sa bulle : jamais l'écran ni les autres fenêtres.
        var film = args.FirstOrDefault(a => a.StartsWith("--film="))?["--film=".Length..];
        double Nombre(string nom, double defaut) =>
            double.TryParse(args.FirstOrDefault(a => a.StartsWith($"--{nom}="))?[(nom.Length + 3)..],
                System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : defaut;
        double duree = Math.Clamp(Nombre("duree", 6), 1, 30), ips = Math.Clamp(Nombre("ips", 15), 5, 30);
        // --captures=<dossier> [--apres=6] (avec --essai) : chaque fenêtre ouverte rendue en PNG à 100/125/150 %, puis quitte.
        var captures = essai is null ? null : args.FirstOrDefault(a => a.StartsWith("--captures="))?["--captures=".Length..];
        double apres = Math.Clamp(Nombre("apres", 6), 2, 60);
        args = args.Where(a => a != "--devant" && !a.StartsWith("--instantane=") && !a.StartsWith("--essai=")
            && !a.StartsWith("--film=") && !a.StartsWith("--duree=") && !a.StartsWith("--ips=")
            && !a.StartsWith("--captures=") && !a.StartsWith("--apres=")).ToArray();
        var dossier = args.Length > 0 ? args[0] : Signal.Defaut();
        // Un essai ne touche jamais aux vraies données (EssaiIsole.cs) : sans autre dossier donné, un dossier jetable,
        // effacé à la sortie ; et FenetrePilou coupe en essai tout envoi réseau, la mise à jour et les connecteurs.
        bool enEssai = lancement.Mode == ModeLancement.Essai;
        string? jetable = null;
        if (enEssai)
        {
            EssaiIsole.Nettoyer(Path.GetTempPath(), EssaiIsole.PilouVivant);
            var (d, j) = EssaiIsole.Dossier(args.Length > 0 ? args[0] : null, Signal.Defaut(), Path.GetTempPath());
            dossier = d;
            if (j) jetable = d;
        }
        var app = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        var fenetre = new FenetrePilou(dossier, devant, tournage.Visite, essai: enEssai);
        // Posé en bas de l'écran demandé pour cette session : les réglages durables ne changent pas.
        CadreEcran? ecranFilme = null;
        if (tournage.Placer is { } point)
        {
            fenetre.PoserSur(point.X, point.Y);
            ecranFilme = Natif.Ecrans().FirstOrDefault(e => point.X >= e.X && point.X < e.Droite && point.Y >= e.Y && point.Y < e.Bas);
        }
        else if (tournage.Ecran is { } nom && Natif.Ecrans() is { Count: > 0 } ecrans)
        {
            var e = ecrans[Math.Max(0, Tournage.Choisir(nom, ecrans))];
            fenetre.PoserSur(e.X + e.Largeur / 2, e.Y + e.Hauteur / 2);
            ecranFilme = e;
        }
        if (tournage.Visite)
        {
            // Visite guidée : journal prêt avant tout (même une erreur du démarrage y est notée) ; une erreur qui
            // échappe aux étapes est notée et la visite continue, au lieu d'arrêter Pilou (et le tournage) net.
            FenetreDecor? decor = null;
            if (ecranFilme is { } ef && !tournage.SansDecor)
            {
                var travail = Natif.ZoneTravail(ef.X + ef.Largeur / 2, ef.Y + ef.Hauteur / 2);
                decor = new FenetreDecor(ef, ef.Bas - travail.Bottom);
                decor.Show(); // d'abord : Pilou et ses fenêtres, montrés après, passent devant
            }
            fenetre.PreparerVisite(tournage.Chronologie, ecranFilme, decor);
            app.DispatcherUnhandledException += (_, ev) =>
            {
                fenetre.ErreurVisite(ev.Exception);
                ev.Handled = true;
            };
            AppDomain.CurrentDomain.UnhandledException += (_, ev) =>
            {
                if (ev.ExceptionObject is Exception x) fenetre.ErreurVisite(x);
            };
            TaskScheduler.UnobservedTaskException += (_, ev) =>
            {
                fenetre.ErreurVisite(ev.Exception);
                ev.SetObserved();
            };
        }
        fenetre.Show();
        // Icône près de l'horloge et fenêtre relais (les autres lancements nous joignent par elle) : Pilou habituel seulement.
        if (principal) fenetre.BrancherRelais();
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
        if (captures is not null) CapturesEssai.Programmer(app, captures, apres);
        if (tournage.Visite)
        {
            var depart = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(1500) };
            depart.Tick += (_, _) =>
            {
                depart.Stop();
                fenetre.VisiteGuidee(tournage.Chronologie);
            };
            depart.Start();
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
        if (film is not null)
        {
            Directory.CreateDirectory(film);
            int image = 0, total = (int)(duree * ips);
            var debut = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(1000) };
            debut.Tick += (_, _) =>
            {
                debut.Stop();
                var prise = new System.Windows.Threading.DispatcherTimer(System.Windows.Threading.DispatcherPriority.Render)
                    { Interval = TimeSpan.FromMilliseconds(1000 / ips) };
                prise.Tick += (_, _) =>
                {
                    fenetre.Instantane(Path.Combine(film, $"{image:0000}.png"));
                    if (++image >= total)
                    {
                        prise.Stop();
                        app.Shutdown();
                    }
                };
                prise.Start();
            };
            debut.Start();
        }
        int fin = app.Run();
        if (jetable is not null) EssaiIsole.Effacer(jetable);
        return fin;
    }
}
