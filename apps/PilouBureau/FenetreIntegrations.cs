using System.Diagnostics;
using System.Net.Http;
using System.Text;
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
    private static readonly HttpClient Relais = new() { Timeout = TimeSpan.FromSeconds(15) };
    private Expr _exprCourante = Expr.Repos;
    private string _telSignature = "", _telEnvoyee = "";
    private double _telChange = -1e12, _telEnvoi = -1e12, _telPause = -1e12;
    private bool _telEnCours;
    private string _telEtat = "";

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

        // Un seul code pour le groupe : les autres PC (XP partagée) et le téléphone Android.
        m.Items.Add(new Separator());
        RemplirGroupe(m);
        if (Telephone.Valide(_reglages.Telephone))
            m.Items.Add(new MenuItem
            {
                Header = _telEnvoi < 0 ? $"   dernier envoi au téléphone : aucun{(_telEtat == "" ? "" : $" · {_telEtat}")}"
                    : $"   dernier envoi au téléphone : il y a {Statut.Duree(Epoque - _telEnvoi)} · {(_telEtat == "" ? "ok" : _telEtat)}",
                IsEnabled = false,
            });

        m.Items.Add(new Separator());
        m.Items.Add(Entree("Brancher un autre logiciel… (aide)", () => Ouvrir(AideBrancher)));
        return m;
    }

    private void Appairer(bool nouveau)
    {
        if (nouveau || !Telephone.Valide(_reglages.Telephone)) _reglages.Telephone = Telephone.NouveauCode();
        _reglages.Ecrire(_dossier);
        _telEnvoyee = ""; // le téléphone reçoit l'état dès qu'il écoute
        Appairage.Montrer(_reglages.Telephone, _reglages.Relais);
    }

    private void ChoisirRelais()
    {
        var v = Saisie.Demander("Relais du téléphone",
            "Serveur ntfy qui porte les messages (chiffrés) vers le téléphone. ntfy.sh est gratuit mais limite le nombre " +
            "de messages par jour ; ton propre serveur ntfy n'a pas de limite. Le téléphone doit utiliser le même.",
            _reglages.Relais);
        if (v is null) return;
        v = v.TrimEnd('/');
        if (v == "") v = Telephone.RelaisParDefaut;
        if (!Webhook.Valide(v))
        {
            Dire("adresse refusée : il faut une adresse https://", 4000);
            return;
        }
        _reglages.Relais = v;
        _reglages.Ecrire(_dossier);
        _telEnvoyee = "";
        if (Telephone.Valide(_reglages.Telephone)) Appairage.Montrer(_reglages.Telephone, v);
    }

    // État des sessions vers le téléphone : sur changement (regroupé sur 3 s), sinon toutes les 15 min.
    private void PublierTelephone(IReadOnlyList<EtatSession> vivantes, double epoque)
    {
        var code = _reglages.Telephone;
        if (!Telephone.Valide(code) || _telEnCours || epoque < _telPause) return;
        var sessions = Telephone.Sessions(vivantes, epoque);
        var humeur = _exprCourante.ToString().ToLowerInvariant();
        var accessoire = _reglages.Porte(DateTime.Now, x => Possede(Recompenses.IdAccessoire(x))).ToString().ToLowerInvariant();
        // Les gains crédités et l'accessoire changent aussi ce que le téléphone doit savoir.
        var signature = Telephone.Signature(sessions, Niveau, humeur,
            $"{accessoire}|{_reglages.Couleur}|{_profil.Recus.LastOrDefault()}|{_profil.Carnet.Count}|{_profil.Plats.Count}|{GroupeMem.Autres.Count}"
            + $"|{Bourse().Solde}|{string.Join(",", Bourse().Inventaire)}|{string.Join(",", EquipeCourant().Values)}"
            + $"|{string.Join(",", _profil.Quetes.Liste.Select(q => q.Fait))}|{Quetes.CleJour(DateTime.Now)}"
            + $"|{_profil.Soins.Actions.Count}|{_profil.Soins.Base?.T}|{_profil.Evolution.Variantes.Count}"
            + $"|{Meteo.Courante?.Etat}|{Math.Round(Meteo.Courante?.Releve.Temperature ?? 0)}"
            + $"|{(_reglages.Connecteurs.AnnoncesTelephone ? _registre?.Annonces().FirstOrDefault()?.T : 0)}");
        if (signature != _telSignature)
        {
            _telSignature = signature;
            _telChange = epoque;
        }
        bool change = signature != _telEnvoyee && epoque - _telChange >= 3000;
        bool battement = epoque - _telEnvoi >= 15 * 60_000;
        if (!change && !battement) return;

        var progression = Telephone.Progression(_profil, _xpTotal, accessoire);
        var (solde, inventaire, equipe) = Bourse();
        Quetes.Actualiser(_profil.Quetes, DateTime.Now, IdAppareil);
        foreach (var (k, v) in Telephone.EtatBoutique(solde, inventaire, equipe, _profil.Quetes, DateTime.Now)) progression[k] = v;
        progression["stade"] = StadeAffiche();
        if (_reglages.Connecteurs.AnnoncesTelephone && _registre is not null)
            progression["annonces"] = Telephone.Annonces(_registre.Annonces(), _reglages.Connecteurs.AnnoncesSansContenu);
        if (Meteo.Courante is { } meteo && _registre?.Trouver("meteo") is { } cm && _registre.Actif(cm))
            progression["meteo"] = Meteo.PourTelephone(meteo);
        // Appareils du groupe, pour la liste de l'app (nom, xp, vu il y a) ; ce PC en tête.
        progression["appareils"] = new[] { new Dictionary<string, object> { ["nom"] = Environment.MachineName, ["xp"] = _profil.Xp, ["t"] = epoque } }
            .Concat(GroupeMem.Compteurs.OrderByDescending(c => c.T)
                .Select(c => new Dictionary<string, object> { ["nom"] = c.Nom, ["xp"] = c.Xp, ["t"] = c.T }))
            .Take(10).ToList();
        var charge = Telephone.Charge(sessions, epoque, NomPilou, Niveau, Recompenses.Titre(Niveau),
            _reglages.Couleur.ToString().ToLowerInvariant(), humeur, vivantes.Count - sessions.Count, progression);
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Telephone.Sujet(code)}";
        var corps = Telephone.Chiffrer(code, charge);
        // Au-delà de 4 096 octets, ntfy transforme le message en pièce jointe : on retire alors les listes
        // (carnet, recettes), que le téléphone garde de l'envoi précédent.
        if (corps.Length > Telephone.TailleMax)
        {
            var leger = Telephone.Progression(_profil, _xpTotal, accessoire);
            leger.Remove("carnet");
            leger.Remove("plats");
            foreach (var (k, v) in Telephone.EtatBoutique(solde, inventaire, equipe, _profil.Quetes, DateTime.Now)) leger[k] = v;
            leger["stade"] = StadeAffiche();
            charge = Telephone.Charge(sessions, epoque, NomPilou, Niveau, Recompenses.Titre(Niveau),
                _reglages.Couleur.ToString().ToLowerInvariant(), humeur, vivantes.Count - sessions.Count, leger);
            corps = Telephone.Chiffrer(code, charge);
        }
        _telEnCours = true;
        _ = Task.Run(async () =>
        {
            try
            {
                using var r = await Relais.PostAsync(url, new StringContent(corps, Encoding.UTF8, "text/plain"));
                if ((int)r.StatusCode == 429)
                {
                    _telPause = Epoque + 5 * 60_000; // limite du relais : on se tait 5 min
                    _telEtat = "limite du relais atteinte (pause 5 min)";
                }
                else if (r.IsSuccessStatusCode)
                {
                    _telEnvoyee = signature;
                    _telEnvoi = Epoque;
                    _telEtat = "ok";
                }
                else
                {
                    _telPause = Epoque + 60_000; // refus du relais : pas de nouvel essai avant une minute
                    _telEtat = $"refusé par le relais (HTTP {(int)r.StatusCode})";
                }
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                _telPause = Epoque + 60_000; // hors ligne : on réessaie dans une minute
                _telEtat = "relais injoignable";
            }
            finally
            {
                _telEnCours = false;
            }
        });
    }

    // Gains du téléphone (atelier) : le sujet retour, relu toutes les 90 s, crédité une fois par gain.
    private double _retourLu = -1e12;
    private bool _retourEnCours;

    private void RecevoirTelephone(double epoque)
    {
        var code = _reglages.Telephone;
        if (!Telephone.Valide(code) || _retourEnCours || epoque - _retourLu < 90_000) return;
        _retourLu = epoque;
        _retourEnCours = true;
        var depuis = _reglages.RetourDepuis == "" ? "12h" : _reglages.RetourDepuis;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Telephone.SujetRetour(code)}/json?poll=1&since={Uri.EscapeDataString(depuis)}";
        _ = Task.Run(async () =>
        {
            try
            {
                var texte = await Relais.GetStringAsync(url);
                var (gains, dernier) = Telephone.LireRetours(code, texte);
                await Dispatcher.InvokeAsync(() =>
                {
                    var ctx = new Telephone.Contexte(DateTime.Now, IdAppareil, Niveau, Bourse().Solde);
                    var resultats = gains.Select(g => Telephone.Recevoir(_profil, g, ctx with { Solde = Bourse().Solde })).ToList();
                    _bourseCache = null;
                    int total = resultats.Sum(r => r.Xp);
                    var refus = resultats.SelectMany(r => r.Refus).ToList();
                    if (dernier != "") _reglages.RetourDepuis = dernier;
                    if (gains.Count > 0 || dernier != "") _reglages.Ecrire(_dossier);
                    if (gains.Count == 0) return;
                    _profil.Ecrire(DossierPartage);
                    _xpTotal = TotalXp();
                    var recompenses = resultats.SelectMany(r => r.Recompenses).ToList();
                    if (recompenses.Count > 0)
                    {
                        FlotterPo($"+{recompenses.Sum(r => r.Po)} po");
                        Dire($"✦ quête réussie depuis le téléphone : {recompenses[0].Texte}", 4200);
                    }
                    else if (refus.Count > 0) Dire($"achat refusé : {refus[0]}", 4000);
                    else if (total > 0)
                    {
                        Flotter($"+{total} xp");
                        Dire($"le téléphone a joué : +{total} xp", 3500);
                    }
                    VerifierNiveau();
                });
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                // hors ligne : on relira au prochain passage
            }
            finally
            {
                _retourEnCours = false;
            }
        });
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
        PublierTelephone(vivantes, epoque);
        RecevoirTelephone(epoque);
        PublierGroupe(epoque);
        LireGroupe(epoque);
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
