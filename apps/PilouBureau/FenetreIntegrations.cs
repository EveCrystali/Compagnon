using System.Diagnostics;
using System.Windows;
using System.Windows.Controls;

namespace PilouBureau;

// Ce que Pilou fait avec les autres logiciels : Codex, Discord, alertes à distance, XP des autres sources.
public sealed partial class FenetrePilou
{
    private const string AideBrancher = "https://github.com/EveCrystali/Compagnon/blob/main/docs/BRANCHER.md";

    private readonly PresenceDiscord _discord = new();
    private readonly Dictionary<string, string> _prevenu = new();
    private readonly Dictionary<string, int> _xpSources = new();

    private MenuItem MenuIntegrations()
    {
        var m = new MenuItem { Header = "Intégrations" };

        if (Codex.Branche())
            m.Items.Add(Entree("Codex : branché ✓ (débrancher)", () => Dire(Codex.Debrancher(), 4000)));
        else
            m.Items.Add(Entree(Codex.Installe ? "Codex : brancher (suivre ses sessions)" : "Codex : brancher (pas encore installé ici)",
                () => Dire(Codex.Brancher(Environment.ProcessPath ?? "PilouBureau.exe"), 6000)));

        m.Items.Add(new Separator());
        if (string.IsNullOrWhiteSpace(_reglages.DiscordApp))
            m.Items.Add(Entree("Discord : statut « Joue à Pilou »… (identifiant d'application)", ChoisirDiscord));
        else
        {
            m.Items.Add(Case("Discord : statut « Joue à Pilou »", _reglages.DiscordStatut, v => _reglages.DiscordStatut = v));
            m.Items.Add(Case("Discord : montrer le nom des sessions", _reglages.DiscordTitres, v => _reglages.DiscordTitres = v));
            m.Items.Add(Entree("Discord : changer d'application…", ChoisirDiscord));
        }

        m.Items.Add(new Separator());
        m.Items.Add(Entree(Webhook.Valide(_reglages.Webhook) ? "Me prévenir sur mon téléphone : actif (changer…)" : "Me prévenir sur mon téléphone… (webhook)",
            ChoisirWebhook));
        if (Webhook.Valide(_reglages.Webhook))
        {
            m.Items.Add(Case("… seulement quand je suis loin du PC", _reglages.WebhookSeulementAbsent, v => _reglages.WebhookSeulementAbsent = v));
            m.Items.Add(Entree("… envoyer un essai", () => _ = Essayer()));
        }

        m.Items.Add(new Separator());
        m.Items.Add(Entree("Brancher un autre logiciel… (aide)", () => Ouvrir(AideBrancher)));
        return m;
    }

    private void ChoisirDiscord()
    {
        var v = Saisie.Demander("Statut Discord",
            "Identifiant de l'application Discord « Pilou » (discord.com/developers → New Application → Application ID). " +
            "Discord affichera « Joue à Pilou » avec le niveau et ce que font tes IA. Laisser vide pour couper.",
            _reglages.DiscordApp);
        if (v is null) return;
        _reglages.DiscordApp = new string(v.Where(char.IsAsciiDigit).ToArray());
        _reglages.DiscordStatut = _reglages.DiscordApp != "";
        _reglages.Ecrire(_dossier);
        Dire(_reglages.DiscordStatut ? "statut Discord activé (Discord doit être ouvert)" : "statut Discord coupé", 4000);
    }

    private void ChoisirWebhook()
    {
        var v = Saisie.Demander("Me prévenir sur mon téléphone",
            "Adresse d'un webhook : Discord (salon → Modifier → Intégrations → Webhooks → Copier l'URL), Slack, ou https://ntfy.sh/<sujet>. " +
            "Pilou y écrit quand une IA t'attend depuis 30 s ou a fini un travail de plus de 2 min. Laisser vide pour couper.",
            _reglages.Webhook);
        if (v is null) return;
        if (v != "" && !Webhook.Valide(v))
        {
            Dire("adresse refusée : il faut une adresse https://", 4000);
            return;
        }
        _reglages.Webhook = v;
        _reglages.Ecrire(_dossier);
        if (v != "") _ = Essayer();
        else Dire("alertes à distance coupées", 3000);
    }

    private async Task Essayer()
    {
        var ok = await Webhook.Envoyer(_reglages.Webhook, $"👋 {NomPilou} est branché : il te préviendra ici quand une IA t'attend.");
        Dire(ok ? "message d'essai envoyé ✓" : "le webhook n'a pas répondu (adresse ?)", 4000);
    }

    private static void Ouvrir(string url)
    {
        try
        {
            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
        }
        catch (Exception e) when (e is System.ComponentModel.Win32Exception or InvalidOperationException)
        {
            // pas de navigateur par défaut
        }
    }

    private string NomPilou => _vivantes.FirstOrDefault(e => e.Claude)?.Nom ?? "Pilou";

    // Appelé à chaque lecture des sessions.
    private void Integrer(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        CrediterSources(vivantes);
        PublierDiscord(vivantes, epoque);
        Prevenir(vivantes, epoque);
    }

    // XP gagnée par les autres sources (tour fini, commit, tests) : écart depuis la dernière lecture.
    private void CrediterSources(IReadOnlyList<EtatSession> vivantes)
    {
        foreach (var e in vivantes.Where(e => !e.Claude))
        {
            if (_xpSources.TryGetValue(e.Session, out var vu) && e.Xp > vu)
            {
                int gain = Math.Min(50, e.Xp - vu);
                _profil.Xp += gain;
                _profil.Ecrire(DossierPartage);
                _xpTotal += gain;
                Flotter($"+{gain} xp");
            }
            _xpSources[e.Session] = e.Xp;
        }
    }

    private void PublierDiscord(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        if (!_reglages.DiscordStatut)
        {
            _discord.Fermer();
            return;
        }
        var details = $"{NomPilou} · niveau {Niveau} · {Recompenses.Titre(Niveau)}";
        var r = Statut.Resumer(vivantes, epoque);
        string etat;
        if (r.Attente > 0) etat = "❗ attend son humain";
        else if (r.Travail > 0)
        {
            var sources = vivantes.Where(e => e.EnTour).Select(e => Statut.Etiquette(e.Source)).Distinct();
            etat = $"◐ {r.Travail} session{(r.Travail > 1 ? "s" : "")} en cours ({string.Join(", ", sources)})";
            if (_reglages.DiscordTitres && vivantes.FirstOrDefault(e => e.EnTour) is { } une) etat = $"◐ {Statut.Nom(une)}";
        }
        else if (r.Fini > 0) etat = $"✓ {r.Fini} fini{(r.Fini > 1 ? "es" : "e")}, se repose";
        else etat = "se promène sur le bureau";
        if (etat.Length > 120) etat = etat[..119] + "…";
        _discord.Publier(_reglages.DiscordApp, details, etat);
    }

    // Une IA attend depuis 30 s, ou vient de finir un travail de plus de 2 min : un message, une fois.
    private void Prevenir(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        if (!Webhook.Valide(_reglages.Webhook)) return;
        double inactif = Natif.InactifMs();
        bool absent = !_reglages.WebhookSeulementAbsent || inactif > 30_000;
        foreach (var e in vivantes)
        {
            string cle, texte;
            if (e.Attente != "" && epoque - e.DebutOutil > 30_000)
            {
                cle = $"a|{e.DebutOutil}";
                texte = e.Attente == "permission"
                    ? $"❗ **{Statut.Nom(e)}** attend ton autorisation"
                    : $"? **{Statut.Nom(e)}** te pose une question";
            }
            else if (!e.EnTour && e.FinRaison == "" && e.FinTour > 0 && epoque - e.FinTour < 120_000 && e.DebutTour > 0
                     && e.FinTour - e.DebutTour >= 120_000)
            {
                cle = $"f|{e.FinTour}";
                texte = $"✓ **{Statut.Nom(e)}** a fini ({Statut.Duree(e.FinTour - e.DebutTour)} de travail)";
            }
            else continue;
            if (_prevenu.TryGetValue(e.Session, out var deja) && deja == cle) continue;
            if (!absent) continue; // tu es là : la bulle suffit (on retentera si tu t'éloignes)
            _prevenu[e.Session] = cle;
            _ = Webhook.Envoyer(_reglages.Webhook, texte);
        }
    }
}
