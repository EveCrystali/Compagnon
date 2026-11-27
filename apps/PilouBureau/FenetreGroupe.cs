using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Controls;

namespace PilouBureau;

// Groupe d'appareils : publier son compteur d'XP sur le relais, lire ceux des autres PC (Groupe.cs).
public sealed partial class FenetrePilou
{
    private Groupe.Memoire? _groupeMem;
    private string _grSignature = "", _grEnvoyee = "";
    private double _grChange = -1e12, _grEnvoi = -1e12, _grLu = -1e12, _grPause = -1e12;
    private bool _grEnvoiEnCours, _grLectureEnCours;
    private int _relaisEchecs;
    private bool _relaisSignale;

    private Groupe.Memoire GroupeMem => _groupeMem ??= Groupe.Memoire.Lire(_dossier);

    private int TotalXp() => _profil.Total(DossierPartage, GroupeMem.Compteurs);

    // Métiers et succès de tout le groupe (Groupe.Cumuler). Les profils du dossier partagé sont relus au plus
    // une fois par minute : le cumul sert à chaque image d'activité.
    private List<Profil>? _autresDossier;
    private double _autresDossierLu = -1e12;

    private Groupe.Cumul CumulGroupe()
    {
        if (_autresDossier is null || Epoque - _autresDossierLu > 60_000)
        {
            _autresDossier = _profil.EnMemoire ? new List<Profil>() : _profil.AutresDuDossier(DossierPartage);
            _autresDossierLu = Epoque;
        }
        return Groupe.Cumuler(_profil, _autresDossier, GroupeMem.Compteurs);
    }

    private bool DansUnGroupe => Telephone.Valide(_reglages.Telephone);

    private string IdAppareil
    {
        get
        {
            if (_reglages.Appareil == "")
            {
                var suffixe = Convert.ToHexString(RandomNumberGenerator.GetBytes(2)).ToLowerInvariant();
                _reglages.Appareil = $"{Environment.MachineName}-{suffixe}";
                _reglages.Ecrire(_dossier);
            }
            return _reglages.Appareil;
        }
    }

    // Le relais répond mal plusieurs fois de suite (proxy d'entreprise, hors ligne) : on le dit une fois.
    private void RelaisRepond(bool ok)
    {
        if (ok)
        {
            _relaisEchecs = 0;
            _relaisSignale = false;
            return;
        }
        if (++_relaisEchecs >= 3 && !_relaisSignale)
        {
            _relaisSignale = true;
            Dispatcher.InvokeAsync(() => Dire("relais injoignable : l'XP du groupe attendra", 5000));
        }
    }

    // Son compteur : à chaque changement (regroupé sur 5 s), au démarrage, puis toutes les heures (ntfy garde 12 h).
    private void PublierGroupe(double epoque)
    {
        var code = _reglages.Telephone;
        if (!DansUnGroupe || _grEnvoiEnCours || epoque < _grPause) return;
        var b = _profil.Bourse;
        var signature = $"{_profil.Xp}|{_profil.XpTelephone}|{_profil.Carnet.Count}|{_profil.Plats.Count}|{NomPilou}"
                        + $"|{b.PoGagnes}|{b.PoDepenses}|{b.PoDepTelephone}|{b.Inventaire.Count}|{string.Join(",", b.Equipe.Select(kv => kv.Key + kv.Value.Id))}"
                        + $"|{_profil.Evolution.NiveauAcquis}|{_profil.Evolution.NiveauPaye}"
                        + $"|{_profil.Expedition.Jour}|{_profil.Expedition.Nombre}|{_profil.Expedition.Libre}"
                        // Métiers : une publication par demi-heure d'activité au plus (le relais limite les messages),
                        // tout de suite pour un succès, un grade payé ou un compteur de succès.
                        + $"|{_profil.Activites.Values.Sum() / 1800}|{_profil.Succes.Count}|{string.Join(",", _profil.MetiersPayes.Values)}"
                        + $"|{_profil.SeancesClavier}|{_profil.Captures}|{_profil.Presentations}|{_profil.Defense.Meilleur}|{_profil.Defense.MeilleureVague}|{_profil.Defense.Boss}";
        if (signature != _grSignature)
        {
            _grSignature = signature;
            _grChange = epoque;
        }
        bool change = signature != _grEnvoyee && epoque - _grChange >= 5000;
        bool battement = epoque - _grEnvoi >= 3600_000;
        if (!change && !battement) return;

        var moi = Groupe.Moi(_profil, IdAppareil, Environment.MachineName);
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Groupe.Sujet(code)}";
        var corps = Telephone.Chiffrer(code, Groupe.Json(moi));
        _grEnvoiEnCours = true;
        _ = Task.Run(async () =>
        {
            try
            {
                using var r = await Relais.PostAsync(url, new StringContent(corps, Encoding.UTF8, "text/plain"));
                if ((int)r.StatusCode == 429) _grPause = Epoque + 5 * 60_000;
                else if (r.IsSuccessStatusCode)
                {
                    _grEnvoyee = signature;
                    _grEnvoi = Epoque;
                }
                RelaisRepond(r.IsSuccessStatusCode || (int)r.StatusCode == 429);
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                _grPause = Epoque + 60_000;
                RelaisRepond(false);
            }
            finally
            {
                _grEnvoiEnCours = false;
            }
        });
    }

    // Les compteurs des autres : relus toutes les 90 s, fusionnés (maximum par appareil).
    private void LireGroupe(double epoque)
    {
        var code = _reglages.Telephone;
        if (!DansUnGroupe || _grLectureEnCours || epoque - _grLu < 90_000) return;
        _grLu = epoque;
        _grLectureEnCours = true;
        var memoire = GroupeMem;
        var depuis = memoire.Depuis == "" ? "12h" : memoire.Depuis;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{Groupe.Sujet(code)}/json?poll=1&since={Uri.EscapeDataString(depuis)}";
        var moi = IdAppareil;
        _ = Task.Run(async () =>
        {
            try
            {
                var texte = await Relais.GetStringAsync(url);
                RelaisRepond(true);
                var (compteurs, dernier) = Groupe.LireMessages(code, texte);
                await Dispatcher.InvokeAsync(() =>
                {
                    bool change = false;
                    foreach (var c in compteurs) change |= memoire.Fusionner(c, moi);
                    RecevoirSoinsGroupe(compteurs.Where(c => c.Appareil != moi));
                    if (dernier != "") memoire.Depuis = dernier;
                    if (change || dernier != "") memoire.Ecrire(_dossier);
                    if (!change) return;
                    int avant = _xpTotal;
                    _xpTotal = TotalXp();
                    if (_xpTotal > avant) Flotter($"+{_xpTotal - avant} xp");
                    VerifierNiveau();
                    // Heures et succès des autres PC : grades montés ailleurs (annonce discrète), succès du groupe.
                    MetiersEtSuccesDuGroupe();
                });
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                RelaisRepond(false);
            }
            finally
            {
                _grLectureEnCours = false;
            }
        });
    }

    // ---- Menu

    private void RemplirGroupe(MenuItem m)
    {
        if (DansUnGroupe)
        {
            m.Items.Add(Entree("Groupe d'appareils : revoir le code (PC, téléphone)", () => Appairage.Montrer(_reglages.Telephone, _reglages.Relais)));
            var appareils = new MenuItem { Header = $"Appareils du groupe ({GroupeMem.Autres.Count + 1})" };
            var maintenant = Epoque;
            appareils.Items.Add(new MenuItem { Header = $"✦ {Environment.MachineName} (ce PC) · {_profil.Xp} xp", IsEnabled = false });
            foreach (var c in GroupeMem.Compteurs.OrderByDescending(c => c.T))
                appareils.Items.Add(new MenuItem { Header = $"{c.Nom} · {c.Xp} xp · {Groupe.VuIlYa(c.T, maintenant)}", IsEnabled = false });
            int tel = Math.Max(_profil.XpTelephone, GroupeMem.Compteurs.Select(c => c.XpTelephone).DefaultIfEmpty(0).Max());
            if (tel > 0) appareils.Items.Add(new MenuItem { Header = $"Téléphone et campagnes · {tel} xp", IsEnabled = false });
            appareils.Items.Add(new MenuItem { Header = $"Total : {_xpTotal} xp · niveau {Niveau}", IsEnabled = false });
            m.Items.Add(appareils);
            m.Items.Add(Entree("Rejoindre un autre groupe… (code de mon autre PC ou du téléphone)", Rejoindre));
            m.Items.Add(Entree("Groupe : nouveau code (les autres appareils décrochent)", () => Appairer(true)));
            m.Items.Add(Entree("Quitter le groupe", () =>
            {
                _reglages.Telephone = "";
                _reglages.Ecrire(_dossier);
                GroupeMem.Oublier();
                GroupeMem.Ecrire(_dossier);
                _xpTotal = TotalXp();
                Dire("hors du groupe : l'XP des autres appareils n'est plus comptée ici", 4000);
            }));
        }
        else
        {
            m.Items.Add(Entree("Partager l'XP entre mes appareils… (nouveau code)", () => Appairer(false)));
            m.Items.Add(Entree("Rejoindre un groupe… (code d'un autre appareil)", Rejoindre));
        }
        m.Items.Add(Entree($"Relais du groupe : {_reglages.Relais}…", ChoisirRelais));
    }

    private void Rejoindre()
    {
        var v = Saisie.Demander("Rejoindre un groupe d'appareils",
            "Code à 16 caractères affiché par l'autre PC (clic droit → Intégrations → Groupe d'appareils : revoir le code). " +
            "L'XP de tous les appareils du groupe s'additionne ; le téléphone appairé avec ce code en fait aussi partie.",
            "");
        if (v is null) return;
        if (!Telephone.Valide(v))
        {
            Dire("code incomplet : 16 caractères", 3500);
            return;
        }
        _reglages.Telephone = Telephone.Formater(v);
        _reglages.Ecrire(_dossier);
        GroupeMem.Oublier();
        _grEnvoyee = "";
        _grLu = -1e12;
        _telEnvoyee = "";
        Dire("dans le groupe : je cherche les autres appareils…", 4000);
    }
}
