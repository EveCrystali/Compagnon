using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Threading;
using EnvDTE;
using EnvDTE80;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;
using Microsoft.VisualStudio.Shell.TableControl;
using Microsoft.VisualStudio.Shell.TableManager;
using Task = System.Threading.Tasks.Task;

namespace PilouVisualStudio
{
    // Pilou pour Visual Studio : lit la Liste d'erreurs (IErrorList), garde les lignes du document actif
    // (DTE.ActiveDocument), compte erreurs et avertissements et les envoie à l'API locale de Pilou
    // (POST http://127.0.0.1:47821/diagnostics). Pilou regroupe et décide seul s'il dit quelque chose.
    // Envoi 750 ms après le dernier changement, seulement si le compte ou le fichier change, et une fois par
    // minute tant que Visual Studio est la fenêtre active. Doc : docs/EDITEURS.md.
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [Guid(PackageGuidString)]
    [ProvideAutoLoad(UIContextGuids80.SolutionExists, PackageAutoLoadFlags.BackgroundLoad)]
    [ProvideAutoLoad(UIContextGuids80.NoSolution, PackageAutoLoadFlags.BackgroundLoad)]
    [ProvideOptionPage(typeof(OptionsPilou), "Pilou", "Général", 0, 0, true)]
    public sealed class PilouPackage : AsyncPackage
    {
        public const string PackageGuidString = "5b0f3a52-8c1e-4d2a-9f37-6a1c2e7d4b90";

        private static readonly HttpClient Http = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };

        private DTE2 _dte;
        private IErrorList _liste;
        private WindowEvents _fenetres;
        private DispatcherTimer _attente, _battement;
        private Rapport _dernier;
        private string _jeton;
        private int _port;

        protected override async Task InitializeAsync(CancellationToken ct, IProgress<ServiceProgressData> progres)
        {
            await JoinableTaskFactory.SwitchToMainThreadAsync(ct);
            _dte = await GetServiceAsync(typeof(DTE)) as DTE2;
            _liste = await GetServiceAsync(typeof(SVsErrorList)) as IErrorList;
            if (_dte == null || _liste == null) return; // rien à lire : Pilou n'en saura rien, Visual Studio non plus

            _attente = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(750) };
            _attente.Tick += (s, e) =>
            {
                _attente.Stop();
                Envoyer(false);
            };
            _battement = new DispatcherTimer { Interval = TimeSpan.FromMinutes(1) };
            _battement.Tick += (s, e) => Envoyer(true);
            _battement.Start();

            _liste.TableControl.EntriesChanged += (s, e) => Planifier();
            // Garder une référence aux événements DTE, sinon ils sont ramassés et se taisent.
            _fenetres = _dte.Events.WindowEvents;
            _fenetres.WindowActivated += (actif, avant) => Planifier();
            var principale = System.Windows.Application.Current?.MainWindow;
            if (principale != null)
                principale.Activated += (s, e) =>
                {
                    // Visual Studio retrouve le focus : il redevient l'éditeur le plus récent pour Pilou.
                    _dernier = null;
                    Planifier();
                };
            Planifier();
        }

        private OptionsPilou Options => (OptionsPilou)GetDialogPage(typeof(OptionsPilou));

        // EntriesChanged arrive sur n'importe quel fil : on revient sur celui de l'interface.
        private void Planifier()
        {
            _ = JoinableTaskFactory.RunAsync(async () =>
            {
                await JoinableTaskFactory.SwitchToMainThreadAsync(DisposalToken);
                _attente?.Stop();
                _attente?.Start();
            });
        }

        private static bool VisualStudioActif() => System.Windows.Application.Current?.MainWindow?.IsActive == true;

        private void Envoyer(bool battement)
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            if (!Options.Actif || !VisualStudioActif()) return;
            var r = Lire();
            // Pas de document (page de démarrage, outil) : Pilou garde le dernier fichier, rien à envoyer.
            if (r == null || (!battement && r.Meme(_dernier))) return;
            _ = JoinableTaskFactory.RunAsync(() => Poster(r));
        }

        private Rapport Lire()
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            string actif;
            try
            {
                actif = _dte.ActiveDocument?.FullName;
            }
            catch (Exception)
            {
                return null; // document en cours de fermeture
            }
            if (string.IsNullOrEmpty(actif)) return null;
            var lignes = new List<LigneErreur>();
            foreach (var entree in _liste.TableControl.Entries)
            {
                if (!entree.TryGetValue(StandardTableKeyNames.DocumentName, out object doc) || !(doc is string chemin)) continue;
                var gravite = Gravite.Message;
                if (entree.TryGetValue(StandardTableKeyNames.ErrorSeverity, out object g) && g is __VSERRORCATEGORY cat)
                    gravite = cat == __VSERRORCATEGORY.EC_ERROR ? Gravite.Erreur
                        : cat == __VSERRORCATEGORY.EC_WARNING ? Gravite.Avertissement : Gravite.Message;
                entree.TryGetValue(StandardTableKeyNames.Text, out object texte);
                int ligne = entree.TryGetValue(StandardTableKeyNames.Line, out object l) && l is int n ? n : 0;
                lignes.Add(new LigneErreur(chemin, gravite, texte as string, ligne));
            }
            return Rapport.Compter(actif, lignes, Options.EnvoyerMessage);
        }

        private void Acces(bool relire)
        {
            if (!relire && !string.IsNullOrEmpty(_jeton)) return;
            string json = "";
            try
            {
                var chemin = Rapport.CheminReglages();
                if (File.Exists(chemin)) json = File.ReadAllText(chemin);
            }
            catch (Exception e) when (e is IOException || e is UnauthorizedAccessException)
            {
                // illisible : on garde ce qu'on a
            }
            Rapport.LireAcces(json, Options.Jeton, Options.Port, out _jeton, out _port);
        }

        private async Task<int> PosterUneFois(Rapport r)
        {
            if (string.IsNullOrEmpty(_jeton)) return 0; // Pilou pas installé : silence
            try
            {
                using (var req = new HttpRequestMessage(HttpMethod.Post, $"http://127.0.0.1:{_port}/diagnostics"))
                {
                    req.Headers.TryAddWithoutValidation("Authorization", "Bearer " + _jeton);
                    req.Content = new StringContent(r.Json(), Encoding.UTF8, "application/json");
                    using (var rep = await Http.SendAsync(req).ConfigureAwait(false))
                        return (int)rep.StatusCode;
                }
            }
            catch (Exception)
            {
                return 0; // Pilou fermé : jamais d'erreur dans Visual Studio
            }
        }

        private async Task Poster(Rapport r)
        {
            Acces(false);
            int code = await PosterUneFois(r);
            if (code == 401)
            {
                Acces(true); // jeton renouvelé dans Pilou : relu une fois
                code = await PosterUneFois(r);
            }
            if (code == 202) _dernier = r;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _attente?.Stop();
                _battement?.Stop();
                // Visual Studio se ferme : Pilou oublie le fichier tout de suite (sinon au bout de 5 min).
                if (_dernier != null && !string.IsNullOrEmpty(_jeton))
                {
                    try
                    {
#pragma warning disable VSTHRD002 // une seconde au plus, à la fermeture, sans revenir sur le fil de l'interface
                        Task.Run(() => PosterUneFois(Rapport.Fermeture())).Wait(1000);
#pragma warning restore VSTHRD002
                    }
                    catch (Exception)
                    {
                        // tant pis : la durée de vie fera le reste
                    }
                }
            }
            base.Dispose(disposing);
        }
    }

    // Outils → Options → Pilou → Général.
    public sealed class OptionsPilou : DialogPage
    {
        [Category("Pilou")]
        [DisplayName("Envoyer à Pilou")]
        [Description("Compte d'erreurs et d'avertissements du fichier actif, vers l'API locale de Pilou (127.0.0.1).")]
        public bool Actif { get; set; } = true;

        [Category("Pilou")]
        [DisplayName("Premier message d'erreur")]
        [Description("Envoyer aussi le premier message d'erreur (chemins retirés, 160 caractères au plus). Pilou ne l'affiche que si sa case est cochée.")]
        public bool EnvoyerMessage { get; set; }

        [Category("API locale")]
        [DisplayName("Jeton")]
        [Description("Vide : lu dans %USERPROFILE%\\.claude\\compagnon\\reglages.json. Sinon : Pilou → Connecteurs… → Copier le jeton.")]
        [PasswordPropertyText(true)]
        public string Jeton { get; set; } = "";

        [Category("API locale")]
        [DisplayName("Port")]
        [Description("0 : celui de reglages.json, sinon 47821.")]
        public int Port { get; set; }
    }
}
