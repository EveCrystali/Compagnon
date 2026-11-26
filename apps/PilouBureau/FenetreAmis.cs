using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using QRCoder;

namespace PilouBureau;

// Amis et visites sur le PC (docs/AMIS.md) : carnet d'amis, relais ntfy (boîte du code, sujet de chaque
// paire), présence toutes les 10 min, départ et retour de Pilou, pancarte pendant l'absence, invité
// dessiné dans sa propre fenêtre (FenetreInvite) qui raconte sa vie et joue avec Pilou.
public sealed partial class FenetrePilou
{
    private CarnetAmis? _carnet;
    private readonly Visites _visites = new();
    private readonly Dictionary<string, (string Cle, string Sujet, byte[] Secret)> _paires = new();
    private bool _amisLecture, _essaiAmis;
    private double _amisLu = -1e15, _presenceEnvoi = -1e15, _envieVue, _amisActivite = -1e15;
    private string _presenceSignature = "";
    private FenetreListeAmis? _fenetreAmis;

    // Animation : départ, absence, retour (mon Pilou) ; invité (le Pilou d'un ami chez moi).
    private double _visiteX0, _retourX;
    private int _visiteSens = 1;
    private bool _appuiPancarte;
    private FenetreInvite? _invite;
    private double _inviteDepart, _inviteCible, _inviteX;
    private int _inviteSens = 1;
    private readonly List<string> _scenario = new();
    private int _scene0 = -1, _sceneNumero, _sceneRepondue = -1;
    private double _sceneDebut;
    private double _caresseInvite = -1e15, _coeursJusque = -1e15;

    private CarnetAmis MesAmis => _carnet ??= ChargerAmis();

    private CarnetAmis ChargerAmis()
    {
        // Tournage : amis fictifs et code fictif, en mémoire ; rien ne part sur le relais.
        if (_demo)
        {
            _essaiAmis = true;
            return Tournage.CarnetDemo(Epoque);
        }
        var c = CarnetAmis.Lire(_dossier);
        var coffre = new CoffreDpapi(Path.Combine(_dossier, "amis"));
        c.Moi.Privee = coffre.Lire("cle-privee") ?? "";
        bool valide = c.Moi.Privee != "" && c.Moi.Code != "" && Amis.Authentique(c.Moi.Code, c.Moi.Publique);
        if (!valide)
        {
            // Première fois, ou clé perdue (autre compte Windows) : nouvelle identité ; les amis devront
            // se réajouter (leur clé ne correspond plus à rien).
            if (c.Moi.Code != "") c.Amis.Clear();
            c.Moi = Amis.NouvelleIdentite();
            coffre.Ecrire("cle-privee", c.Moi.Privee);
            c.Ecrire(_dossier);
        }
        return c;
    }

    private void EcrireAmis()
    {
        if (!_essaiAmis) MesAmis.Ecrire(_dossier);
    }

    private bool HeureCalme => Amis.Calme(DateTime.Now.Hour, _reglages.CalmeDebut, _reglages.CalmeFin);

    // En expédition, Pilou n'est pas là pour recevoir (l'ami lit « ne reçoit pas en ce moment »).
    private PorteAmi PorteOuverte => new(_reglages.AccepterVisites && !EnExpedition, _discret, HeureCalme);

    // Ce que mes amis voient de Pilou : allure, niveau, et (si coché) quelques faits ; rien d'autre.
    private Vitrine MaVitrine()
    {
        int stade = StadeAffiche();
        var accessoire = _reglages.Porte(DateTime.Now, a => Possede(Recompenses.IdAccessoire(a)));
        return new Vitrine
        {
            Nom = NomPilou,
            Niveau = Niveau,
            Stade = stade,
            Variante = stade >= 2 && _profil.Evolution.Variantes.TryGetValue(stade, out var v) ? v : "",
            Accessoire = accessoire is Accessoire.Aucun or Accessoire.Saison ? "" : accessoire.ToString().ToLowerInvariant(),
            Equipe = EquipeCourant().Where(kv => kv.Value != "").ToDictionary(kv => kv.Key, kv => kv.Value),
            Faits = _reglages.PartagerAnecdotes ? Amis.FaitsDe(_profil, Meteo.Courante?.Etat ?? "") : null,
            Accepte = _reglages.AccepterVisites && !HeureCalme,
            Libre = !_discret && !_visites.Occupe && !EnExpedition,
        };
    }

    // ---- Relais

    private (string Sujet, byte[] Cle)? Paire(Ami a)
    {
        if (a.Cle == "") return null;
        if (_paires.TryGetValue(a.Code, out var p) && p.Cle == a.Cle) return (p.Sujet, p.Secret);
        try
        {
            var (sujet, cle) = Amis.Paire(Amis.Secret(MesAmis.Moi, a.Cle), MesAmis.Moi.Code, a.Code);
            _paires[a.Code] = (a.Cle, sujet, cle);
            return (sujet, cle);
        }
        catch (Exception e) when (e is CryptographicException or FormatException)
        {
            return null;
        }
    }

    private void Poster(string sujet, byte[] cle, MessageAmi m)
    {
        if (_essaiAmis) return;
        var url = $"{_reglages.Relais.TrimEnd('/')}/{sujet}";
        var corps = Amis.Chiffrer(cle, Amis.Ecrire(m));
        _ = Task.Run(async () =>
        {
            try
            {
                using var r = await Relais.PostAsync(url, new StringContent(corps, Encoding.UTF8, "text/plain"));
                RelaisRepond(r.IsSuccessStatusCode || (int)r.StatusCode == 429);
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                RelaisRepond(false);
            }
        });
    }

    // Appelé toutes les 300 ms (Integrer) : visites qui avancent, présence, lecture du relais, envie de partir.
    private void SuivreAmis(double epoque)
    {
        if (_carnet is null && !File.Exists(CarnetAmis.Chemin(_dossier)) && !_essaiAmis) return; // pas encore d'amis
        var c = MesAmis;
        var avant = _visites.Sortie;
        Appliquer(_visites.Avancer(c.Moi.Code, epoque), avant);
        if (_discret && _visites.Venue is { Etape: Etape.Arrivee or Etape.Present })
            Appliquer(_visites.Congedier(c.Moi.Code, epoque, "discret"));
        if (_essaiAmis) return;
        PublierPresence(epoque);
        LireAmis(epoque);
        EnvieDeVisite(epoque);
    }

    private void PublierPresence(double epoque)
    {
        var actifs = MesAmis.Amis.Where(a => a.Etat == EtatAmi.Actif && a.Cle != "").ToList();
        if (actifs.Count == 0) return;
        var v = MaVitrine();
        var signature = JsonSerializer.Serialize(v, Amis.Json);
        bool change = signature != _presenceSignature && epoque - _presenceEnvoi > 30_000;
        if (!change && epoque - _presenceEnvoi < Amis.PresenceMs) return;
        _presenceSignature = signature;
        _presenceEnvoi = epoque;
        foreach (var a in actifs)
        {
            var m = Amis.Message("presence", MesAmis.Moi.Code, epoque);
            m.Pilou = v;
            Envoyer(a, m);
        }
    }

    private void Envoyer(Ami a, MessageAmi m)
    {
        if (Paire(a) is { } p) Poster(p.Sujet, p.Cle, m);
    }

    // Boîte de mon code et sujets de mes paires, d'une seule lecture : toutes les minutes, toutes les
    // 15 s pendant une visite ou juste après une demande.
    private void LireAmis(double epoque)
    {
        var c = MesAmis;
        bool presse = _visites.Occupe || epoque - _amisActivite < 5 * 60_000;
        if (_amisLecture || epoque - _amisLu < (presse ? 15_000 : 60_000)) return;
        _amisLu = epoque;
        var sujets = new Dictionary<string, string> { [Amis.SujetBoite(c.Moi.Code)] = "" };
        foreach (var a in c.Amis.Where(a => a.Etat == EtatAmi.Actif))
            if (Paire(a) is { } p) sujets[p.Sujet] = a.Code;
        var depuis = c.Depuis > 0 ? (c.Depuis - 60).ToString(System.Globalization.CultureInfo.InvariantCulture) : "12h";
        var url = $"{_reglages.Relais.TrimEnd('/')}/{string.Join(",", sujets.Keys)}/json?poll=1&since={depuis}";
        _amisLecture = true;
        _ = Task.Run(async () =>
        {
            try
            {
                var texte = await Relais.GetStringAsync(url);
                RelaisRepond(true);
                var bruts = Amis.LireRelais(texte);
                await Dispatcher.InvokeAsync(() => Traiter(bruts, sujets));
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                RelaisRepond(false);
            }
            finally
            {
                _amisLecture = false;
            }
        });
    }

    private void Traiter(List<Brut> bruts, Dictionary<string, string> sujets)
    {
        var c = MesAmis;
        double maintenant = Epoque;
        bool change = false;
        foreach (var b in bruts.OrderBy(b => b.Temps))
        {
            if (c.Vus.Contains(b.Id) || !sujets.TryGetValue(b.Sujet, out var code)) continue;
            c.Marquer(b.Id);
            c.Depuis = Math.Max(c.Depuis, b.Temps);
            change = true;
            double quand = Math.Min(maintenant, b.Temps * 1000.0);
            if (code == "")
            {
                if (Amis.Lire(Amis.Dechiffrer(Amis.CleBoite(c.Moi.Code), b.Message)) is { } m)
                    Appliquer(Annuaire.Boite(c, m, MaVitrine(), quand));
                continue;
            }
            if (c.Trouver(code) is not { } ami || Paire(ami) is not { } p) continue;
            if (Amis.Lire(Amis.Dechiffrer(p.Cle, b.Message)) is not { } msg || msg.De != ami.Code) continue;
            Appliquer(Annuaire.Paire(c, ami, msg, quand));
            // Un vieux message (relu au démarrage) ne relance pas une visite finie depuis longtemps.
            if (maintenant - quand < 10 * 60_000) Appliquer(_visites.Recevoir(msg, ami, c.Moi.Code, PorteOuverte, maintenant));
        }
        if (change) EcrireAmis();
        _fenetreAmis?.Remplir();
    }

    // Pilou s'ennuie (rien en cours, personne au clavier depuis deux minutes) : une chance sur vingt par
    // minute de partir chez un ami en ligne, deux fois par jour au plus.
    private void EnvieDeVisite(double epoque)
    {
        if (epoque - _envieVue < 60_000) return;
        _envieVue = epoque;
        Visites.Actualiser(MesAmis.Jour, DateTime.Now);
        if (_hasard.NextDouble() > 1 / 20.0 || EnExpedition) return;
        bool calme = !_vivantes.Any(e => e.EnTour || e.Attente != "") && _jeuEnCours == Jeu.Aucun && !_dortBureau && !_attrape
                     && _inactif > 120_000;
        if (_visites.Envie(MesAmis.Amis, MesAmis.Jour, _reglages.PartirEnVisite, calme, _discret, HeureCalme, epoque, _hasard) is { } ami)
            Partir(ami, true);
    }

    internal void Partir(Ami ami, bool spontanee)
    {
        // Pas de visite pendant une expédition (ni l'inverse : Expeditions.Refus).
        if (EnExpedition)
        {
            if (!spontanee) Dire("Pilou est en expédition : la visite attendra son retour", 3500);
            return;
        }
        if (_jeuEnCours != Jeu.Aucun) Arreter("");
        Visites.Actualiser(MesAmis.Jour, DateTime.Now);
        Appliquer(_visites.Partir(ami, MesAmis.Moi.Code, MaVitrine(), Epoque, Visites.Duree(_hasard), spontanee, MesAmis.Jour));
        EcrireAmis();
    }

    internal void Rappeler() => Appliquer(_visites.Rappeler(MesAmis.Moi.Code, Epoque));

    // ---- Effets de la machine (Amis.cs) → messages et animations

    private void Appliquer(List<Effet> effets, Sortie? avant = null)
    {
        var c = MesAmis;
        foreach (var e in effets)
        {
            var ami = c.Trouver(e.Ami);
            var nom = ami?.Nom ?? "mon ami";
            switch (e.Quoi)
            {
                case "boite" when e.Message is not null:
                    Poster(Amis.SujetBoite(e.Ami), Amis.CleBoite(e.Ami), e.Message);
                    _amisActivite = Epoque;
                    break;
                case "envoi" when e.Message is not null:
                    if (ami is not null) Envoyer(ami, e.Message);
                    break;
                case "ami":
                    Dire($"{nom} et moi, on est amis !", 4500);
                    _presenceSignature = "";
                    _presenceEnvoi = -1e15;
                    EcrireAmis();
                    break;
                case "demande":
                    Dire($"{nom} veut être mon ami ! (clic droit › Amis…)", 6000);
                    EcrireAmis();
                    break;
                case "retire":
                    EcrireAmis();
                    break;
                case "depart":
                    _visiteX0 = _x;
                    _retourX = _x;
                    _visiteSens = _x - _zone.Left < _zone.Right - _x ? -1 : 1;
                    _geste = Geste.Rien;
                    Dire($"je vais voir {nom} ! à tout'", 4500);
                    break;
                case "retour":
                    // Rappelé en chemin : il fait demi-tour là où il est.
                    if (_x != _visiteX0) _retourX = _x;
                    if (_visites.Sortie?.Etape == Etape.Retour && e.Raison is "refus:ferme" or "refus:occupe" or "refus:calme"
                            or "refus:absent" or "refus:invite" or "silence")
                        Dire(e.Raison switch
                        {
                            "refus:ferme" => $"{nom} ne reçoit pas en ce moment",
                            "refus:occupe" => $"{nom} est occupé (plein écran, visio…), je reviendrai",
                            "refus:calme" => $"chez {nom}, c'est l'heure calme",
                            "refus:absent" => $"{nom} est lui-même parti en visite !",
                            "refus:invite" => $"{nom} a déjà de la visite",
                            _ => $"personne n'a ouvert chez {nom}…",
                        }, 5000);
                    break;
                case "rentre":
                    Rentre(ami, e.Raison, avant?.Accueilli ?? false);
                    break;
                case "caresse":
                    _ = Caresse(ami);
                    break;
                case "arrivee":
                    Accueillir(ami);
                    break;
                case "invite-part":
                    InvitePart(e.Raison);
                    break;
                case "invite-parti":
                    _invite?.Close();
                    _invite = null;
                    _scenario.Clear();
                    break;
            }
        }
    }

    private void Rentre(Ami? ami, string raison, bool accueilli)
    {
        var nom = ami?.Nom ?? "mon ami";
        _x = _visiteX0;
        _tSaut = Maintenant;
        _salueJusque = Maintenant + 1500;
        var (po, xp) = _essaiAmis ? (12, 5) : Visites.Cadeau(MesAmis.Jour, raison, accueilli, _hasard);
        Dire(raison switch
        {
            "rappel" => "tu m'as appelé ? me revoilà !",
            "fini" or "fin" => $"je suis rentré ! {nom} te passe le bonjour",
            _ => "je suis rentré !",
        }, 4500);
        if (po > 0)
        {
            if (!_essaiAmis)
            {
                _profil.Bourse.PoGagnes += po;
                _profil.Xp += xp;
                _profil.Ecrire(DossierPartage);
                _bourseCache = null;
                _xpTotal = TotalXp();
            }
            FlotterPo($"+{po} po");
            Flotter($"+{xp} xp", 1, new Point(TeteX - 18, TeteY - 30));
            VerifierNiveau();
        }
        if (accueilli && ami is not null && !_essaiAmis)
        {
            ami.Amitie++;
            Signaler("visite", 1);
        }
        EcrireAmis();
    }

    // Caresse entre amis (donnée ou reçue) : +2 xp, cinq fois par jour au plus.
    private int Caresse(Ami? ami)
    {
        _coeursJusque = Maintenant + 2200;
        int xp = _essaiAmis ? 2 : Visites.Caresse(MesAmis.Jour);
        if (ami is not null && !_essaiAmis) ami.Amitie++;
        if (xp > 0 && !_essaiAmis)
        {
            _profil.Xp += xp;
            _profil.Ecrire(DossierPartage);
            _xpTotal += xp;
            VerifierNiveau();
        }
        if (xp > 0) Flotter($"+{xp} xp");
        if (_visites.Sortie is { Etape: Etape.Absent }) Dire($"{ami?.Nom ?? "mon ami"} a caressé Pilou ♥", 3500);
        EcrireAmis();
        return xp;
    }

    // ---- Mon Pilou : départ, pancarte, retour

    // Pendant une visite, Pilou ne se promène pas : il part, attend (pancarte) ou revient. Renvoie s'il marche.
    private bool VisiteBouge(double dt, out bool marche)
    {
        marche = false;
        double e = Epoque;
        if (_visites.Sortie is { } s)
        {
            double sortie = _visiteSens < 0 ? _zone.Left - 90 * K : _zone.Right + 90 * K;
            switch (s.Etape)
            {
                case Etape.Depart:
                {
                    double k = Math.Clamp((e - s.Depuis - 1200) / (Visites.DepartMs - 1200), 0, 1);
                    _x = _visiteX0 + (sortie - _visiteX0) * k;
                    marche = k > 0;
                    break;
                }
                case Etape.Absent:
                    _x = _visiteX0;
                    _retourX = sortie;
                    break;
                case Etape.Retour:
                {
                    // Il revient par le bord de l'écran, ou rebrousse chemin s'il n'était pas encore sorti.
                    double k = Math.Clamp((e - s.Depuis) / (Visites.RetourMs - 900), 0, 1);
                    _x = _retourX + (_visiteX0 - _retourX) * k;
                    marche = k < 1;
                    break;
                }
            }
            return true;
        }
        if (_visites.Venue is not null)
        {
            // L'hôte reste là pour son invité (il le regarde, il joue avec lui).
            _x = Math.Clamp(_x, _zone.Left + Scene.Largeur / 2 * K, _zone.Right - Scene.Largeur / 2 * K);
            return true;
        }
        return false;
    }

    private bool PilouAbsent => _visites.Sortie is { Etape: Etape.Absent };

    // Ce que la visite change à la pose de Pilou (baluchon, pancarte, regard vers l'invité, jeux, cœurs).
    private void HabillerVisite(Pose p, double t)
    {
        double e = Epoque;
        var plus = new List<string>();
        if (_visites.Sortie is { } s)
        {
            var nom = MesAmis.Trouver(s.Ami)?.Nom ?? "un ami";
            switch (s.Etape)
            {
                case Etape.Depart:
                    plus.Add("baluchon");
                    p.Regard = _visiteSens;
                    p.Salue = e - s.Depuis < 1200;
                    p.Course = e - s.Depuis > 1200;
                    p.Expr = Expr.Fete;
                    break;
                case Etape.Absent:
                    p.Pancarte = $"chez {Raccourcir(nom, 11)}\n↩ {Amis.Heure(DateTime.Now.AddMilliseconds(s.Fin - e))}";
                    break;
                case Etape.Retour:
                    plus.Add(e - s.Depuis < Visites.RetourMs - 900 ? "baluchon" : "valise");
                    p.Regard = -_visiteSens;
                    p.Expr = Expr.Fete;
                    break;
            }
        }
        if (_visites.Venue is { } v && _invite is not null)
        {
            p.Regard = Math.Sign(_inviteX - _x);
            if (v.Etape == Etape.Present) JeuHote(p, t);
            if (v.Etape == Etape.Sortie) p.Salue = true;
        }
        if (Maintenant < _coeursJusque) plus.Add("coeurs-amitie");
        if (plus.Count > 0) p.Soins = p.Soins.Concat(plus).ToList();
    }

    private static string Raccourcir(string s, int n) => s.Length <= n ? s : s[..(n - 1)] + "…";

    // Ligne de la bulle pendant l'absence (les statuts des sessions restent affichés dessous).
    private string LigneVisite()
    {
        if (_visites.Sortie is not { } s) return "";
        var nom = MesAmis.Trouver(s.Ami)?.Nom ?? "un ami";
        return s.Etape switch
        {
            Etape.Absent => $"➜ parti chez {nom} · retour vers {Amis.Heure(DateTime.Now.AddMilliseconds(s.Fin - Epoque))} (clic sur la pancarte : le rappeler)",
            Etape.Depart => $"➜ en route pour chez {nom}",
            _ => "",
        };
    }

    // Pour le téléphone : la même phrase, sans l'aide au clic.
    private string VisitePourTelephone() =>
        _visites.Sortie is { Etape: Etape.Absent or Etape.Depart } s
            ? $"parti chez {MesAmis.Trouver(s.Ami)?.Nom ?? "un ami"} · retour vers {Amis.Heure(DateTime.Now.AddMilliseconds(s.Fin - Epoque))}"
            : "";

    private List<Dictionary<string, object>> AmisPourTelephone() =>
        _carnet is null ? new()
            : _carnet.Amis.Where(a => a.Etat != EtatAmi.Recue).Take(30).Select(a => new Dictionary<string, object>
            {
                ["nom"] = a.Nom, ["niveau"] = a.Pilou.Niveau, ["stade"] = a.Pilou.Stade, ["t"] = a.Vu, ["actif"] = a.Etat == EtatAmi.Actif,
            }).ToList();

    private string SignatureAmis() =>
        _carnet is null ? "" : string.Join(",", _carnet.Amis.Select(a => $"{a.Nom}{a.Etat}{a.Pilou.Niveau}{(Amis.EnLigne(a, Epoque) ? 1 : 0)}")) + VisitePourTelephone();

    // ---- L'invité chez moi

    private void Accueillir(Ami? ami)
    {
        if (_visites.Venue is not { } v) return;
        var nom = ami?.Nom ?? v.Invite.Nom;
        if (_jeuEnCours != Jeu.Aucun) Arreter("");
        _geste = Geste.Rien;
        // Il arrive par le côté où il y a le plus de place, et s'arrête à côté de Pilou.
        _inviteSens = _x - _zone.Left > _zone.Right - _x ? 1 : -1;
        _inviteDepart = _inviteSens > 0 ? _zone.Left - 90 * K : _zone.Right + 90 * K;
        _inviteCible = _x - _inviteSens * 118 * K;
        _inviteX = _inviteDepart;
        _invite?.Close();
        _invite = new FenetreInvite(nom, K, _sombre);
        _invite.Caresse += CaresserInvite;
        _invite.Show();
        Dire($"oh ! {nom} vient me rendre visite !", 4500);
        // Le programme de la visite : ses anecdotes, entrecoupées de jeux.
        _scenario.Clear();
        var anecdotes = Amis.Anecdotes(v.Invite).OrderBy(_ => _hasard.Next()).ToList();
        var jeux = new[] { "tape", "ballon", "danse", "course" }.OrderBy(_ => _hasard.Next()).ToList();
        for (int i = 0; i < 12; i++)
        {
            _scenario.Add(anecdotes.Count > 0 ? "parle:" + anecdotes[i % anecdotes.Count] : "parle:je suis content d'être là !");
            if (i % 2 == 1) _scenario.Add(jeux[i / 2 % jeux.Count]);
        }
        _scene0 = -1;
    }

    private void InvitePart(string raison)
    {
        if (_invite is null) return;
        _invite.Dire(raison switch
        {
            "rappel" => "oh, on m'appelle à la maison ! au revoir !",
            "silence" => "je file, à bientôt !",
            "discret" => "tu as l'air occupé, je repasserai !",
            _ => "c'était super ! au revoir !",
        }, Maintenant, 3500);
        Dire("au revoir ! reviens quand tu veux", 3500);
    }

    private void CaresserInvite()
    {
        if (_visites.Venue is not { Etape: Etape.Arrivee or Etape.Present } v || _invite is null) return;
        _caresseInvite = Maintenant;
        var m = Amis.Message("caresse", MesAmis.Moi.Code, Epoque);
        m.Visite = v.Id;
        if (MesAmis.Trouver(v.Ami) is { } ami) Envoyer(ami, m);
        _invite.Dire("hihi ♥", Maintenant, 2000);
        Caresse(MesAmis.Trouver(v.Ami));
    }

    // Image par image : où est l'invité, ce qu'il fait, ce qu'il dit.
    private void AnimerInvite(double t)
    {
        if (_invite is null || _visites.Venue is not { } v) return;
        if (!_invite.IsVisible) _invite.Show();
        double e = Epoque;
        var iv = v.Invite;
        var p = new Pose
        {
            Expr = Expr.Repos, T = t, Stade = iv.Stade, Couleur = Couleur.Bleu, Equipe = iv.Equipe,
            Accessoire = Enum.TryParse<Accessoire>(iv.Accessoire, true, out var acc) ? acc : Accessoire.Aucun,
            Regard = Math.Sign(_x - _inviteX), Cligne = (int)(t / 3100) % 7 == 0 && t % 3100 < 150,
        };
        var plus = new List<string>();
        if (iv.Stade >= 2 && iv.Variante != "")
        {
            plus.Add($"variante-{iv.Variante}-{iv.Stade}");
            plus.Add($"variante-{iv.Variante}-{iv.Stade}-tete");
        }
        switch (v.Etape)
        {
            case Etape.Arrivee:
            {
                double k = (e - v.Depuis) / Visites.ArriveeMs;
                double marche = Math.Clamp(k / 0.72, 0, 1);
                _inviteX = _inviteDepart + (_inviteCible - _inviteDepart) * marche;
                p.Marche = marche < 1;
                p.Regard = _inviteSens;
                if (marche < 1) plus.Add("baluchon");
                if (k >= 0.72)
                {
                    // Toc toc : il frappe (petits coups dans le vide) puis salue.
                    p.Toque = Math.Clamp((k - 0.72) / 0.28, 0, 1);
                    p.Salue = true;
                    p.Expr = Expr.Fete;
                    if (_scene0 == -1)
                    {
                        _invite.Dire($"toc toc ! coucou {NomPilou} !", t, 3200);
                        _scene0 = -2;
                    }
                }
                break;
            }
            case Etape.Present:
                _inviteX = _inviteCible;
                JeuInvite(p, t, plus);
                break;
            case Etape.Sortie:
            {
                double k = Math.Clamp((e - v.Depuis - 900) / (Visites.SortieMs - 900), 0, 1);
                _inviteX = _inviteCible + (_inviteDepart - _inviteCible) * k;
                p.Marche = k > 0;
                p.Salue = k == 0;
                p.Regard = k > 0 ? -_inviteSens : _inviteSens;
                plus.Add("baluchon");
                break;
            }
        }
        if (t - _caresseInvite < 1500)
        {
            p.Expr = Expr.Caresse;
            p.Depuis = t - _caresseInvite;
        }
        if (Maintenant < _coeursJusque) plus.Add("coeurs-amitie");
        p.Soins = plus;
        _invite.Poser(p, _inviteX, _zone.Bottom, t);
    }

    private const double DureeScene = 8000;

    private string SceneCourante(double t)
    {
        if (_scenario.Count == 0) return "";
        if (_scene0 < 0)
        {
            _scene0 = 0;
            _sceneDebut = t;
            _sceneNumero++;
            AnnoncerScene(_scenario[0], t);
        }
        while (t - _sceneDebut > DureeScene)
        {
            _sceneDebut += DureeScene;
            _scene0 = (_scene0 + 1) % _scenario.Count;
            _sceneNumero++;
            AnnoncerScene(_scenario[_scene0], _sceneDebut);
        }
        return _scenario[_scene0];
    }

    private void AnnoncerScene(string scene, double t)
    {
        if (_invite is null) return;
        if (scene.StartsWith("parle:"))
        {
            _invite.Dire(scene[6..], t, 4500);
            return;
        }
        _invite.Dire(scene switch
        {
            "tape" => "tape m'en cinq !",
            "ballon" => "on joue au ballon ?",
            "danse" => "allez, on danse !",
            _ => "course jusqu'au bord, partez !",
        }, t, 3000);
    }

    private void JeuInvite(Pose p, double t, List<string> plus)
    {
        var scene = SceneCourante(t);
        double d = t - _sceneDebut;
        p.Regard = Math.Sign(_x - _inviteX);
        switch (scene)
        {
            case "tape":
                // Il s'approche, et clac : les deux mains (antennes) se touchent, des cœurs montent.
                _inviteX = _inviteCible + _inviteSens * Math.Min(1, d / 900) * 34 * K;
                if (d is > 1100 and < 2600)
                {
                    p.Salue = true;
                    p.Saut = Math.Abs(Math.Sin(Math.PI * (d - 1100) / 750)) * 2;
                    p.Expr = Expr.Fete;
                    if (d < 1140) _coeursJusque = Maintenant + 2000;
                }
                break;
            case "ballon":
                p.Balle = true;
                p.BalleX = Math.Sin(d / 500) * 7 * _inviteSens;
                p.BalleRot = d / 140;
                p.Expr = d % 2400 < 1200 ? Expr.Fete : Expr.Repos;
                break;
            case "danse":
                p.Saut = Math.Abs(Math.Sin(d / 260)) * 2.5;
                p.Reaction = "danse";
                p.Expr = Expr.Fete;
                p.Regard = (int)(d / 520) % 2 == 0 ? 1 : -1;
                break;
            case "course":
            {
                double k = Math.Sin(Math.PI * Math.Min(1, d / 5200));
                _inviteX = _inviteCible - _inviteSens * k * 220 * K;
                p.Marche = d < 5200;
                p.Course = d < 5200;
                p.Regard = d < 2600 ? -_inviteSens : _inviteSens;
                break;
            }
            default:
                // Il raconte : il s'anime au début de sa phrase.
                p.Expr = d < 1600 ? Expr.Fete : Expr.Repos;
                p.Salue = d < 900;
                if (d > 3600 && _sceneRepondue != _sceneNumero)
                {
                    // Pilou lui répond, une fois par anecdote.
                    _sceneRepondue = _sceneNumero;
                    Dire(Amis.Reponses[_hasard.Next(Amis.Reponses.Length)], 2600);
                }
                break;
        }
    }

    // Pilou (l'hôte) joue aussi.
    private void JeuHote(Pose p, double t)
    {
        if (_scenario.Count == 0 || _scene0 < 0) return;
        double d = t - _sceneDebut;
        switch (_scenario[_scene0])
        {
            case "tape" when d is > 1100 and < 2600:
                p.Salue = true;
                p.Saut = Math.Abs(Math.Sin(Math.PI * (d - 1100) / 750)) * 2;
                p.Expr = Expr.Fete;
                break;
            case "danse":
                p.Saut = Math.Abs(Math.Cos(d / 260)) * 2.5;
                p.Reaction = "danse";
                p.Expr = Expr.Fete;
                break;
            case "ballon" when d % 2400 > 1200:
                p.Expr = Expr.Fete;
                break;
            case "course":
                p.Regard = Math.Sign(_inviteX - _x);
                p.Expr = d > 4800 ? Expr.Fete : Expr.Repos;
                break;
        }
    }

    // ---- Essais sans réseau : --essai=visite:depart|arrivee|jeu|retour

    private Ami AmiEssai()
    {
        _essaiAmis = true;
        var leo = new Ami
        {
            Code = "ESSAYEZ23ESS", Etat = EtatAmi.Actif, Surnom = "Léo", Vu = Epoque, Cle = "",
            Pilou = new Vitrine
            {
                Nom = "Léo", Niveau = 12, Stade = 3, Variante = "espiegle",
                Equipe = new() { ["tete"] = "chapeau-pirate", ["couleur"] = "ambre" },
                Faits = new Faits { Prise = "Brochet doré", Plat = "Soupe du pêcheur", Meteo = Meteo.Pluie, Quete = "Pêche 3 prises", Evolution = 3 },
            },
        };
        MesAmis.Amis.RemoveAll(a => a.Code == leo.Code);
        MesAmis.Amis.Add(leo);
        return leo;
    }

    private void EssaiVisite(string quoi)
    {
        var leo = AmiEssai();
        double e = Epoque;
        switch (quoi)
        {
            case "depart":
                Partir(leo, false);
                if (_visites.Sortie is { } s) s.Accueilli = true;
                break;
            case "arrivee":
            case "jeu":
            {
                var m = Amis.Message("visite", leo.Code, e);
                m.Visite = m.Id;
                m.Duree = 6 * 60_000;
                m.Pilou = leo.Pilou;
                Appliquer(_visites.Recevoir(m, leo, MesAmis.Moi.Code, new PorteAmi(true, false, false), e));
                if (quoi == "jeu" && _visites.Venue is { } v)
                {
                    v.Etape = Etape.Present;
                    v.Depuis = e;
                    _scenario.Clear();
                    _scenario.AddRange(new[] { "tape", "ballon", "danse", "course", "parle:ma plus belle prise ? un brochet doré !" });
                    _scene0 = -1;
                }
                break;
            }
            case "retour":
                _visiteX0 = _x;
                _visiteSens = _x - _zone.Left < _zone.Right - _x ? -1 : 1;
                _retourX = _visiteSens < 0 ? _zone.Left - 90 * K : _zone.Right + 90 * K;
                _visites.Sortie = new Sortie
                {
                    Ami = leo.Code, Id = "essai", Etape = Etape.Retour, Depuis = e, Debut = e - 6 * 60_000, Fin = e, Accueilli = true, Raison = "fini",
                };
                break;
        }
    }

    // ---- Menu et fenêtre « Amis »

    private IEnumerable<MenuItem> MenusAmis()
    {
        yield return Entree("Amis…", OuvrirAmis);
        if (_visites.Sortie is { Etape: Etape.Depart or Etape.Absent } s)
            yield return Entree($"Rappeler Pilou (parti chez {MesAmis.Trouver(s.Ami)?.Nom ?? "un ami"})", Rappeler);
    }

    private void OuvrirAmis()
    {
        if (_fenetreAmis is { IsVisible: true })
        {
            _fenetreAmis.Activate();
            return;
        }
        _fenetreAmis = new FenetreListeAmis(this);
        _fenetreAmis.Closed += (_, _) => _fenetreAmis = null;
        _fenetreAmis.Show();
    }

    // Pour la fenêtre.
    internal CarnetAmis CarnetDesAmis => MesAmis;
    internal Reglages ReglagesAmis => _reglages;
    internal bool Occupe => _visites.Occupe;
    internal bool EnVisiteChez(string code) => _visites.Sortie?.Ami == code;
    internal double EpoqueAmis => Epoque;

    internal string? Ajouter(string code)
    {
        var refus = Annuaire.Refus(MesAmis, code);
        if (refus is not null) return refus;
        Appliquer(Annuaire.Ajouter(MesAmis, code, MaVitrine(), Epoque));
        EcrireAmis();
        _amisActivite = Epoque;
        _amisLu = -1e15;
        return null;
    }

    internal void Accepter(string code)
    {
        Appliquer(Annuaire.Accepter(MesAmis, code, MaVitrine(), Epoque));
        EcrireAmis();
        _amisActivite = Epoque;
    }

    internal void Retirer(string code)
    {
        // Retirer un ami chez qui Pilou est : il rentre d'abord.
        if (_visites.Sortie?.Ami == code) Rappeler();
        if (_visites.Venue?.Ami == code) Appliquer(_visites.Congedier(MesAmis.Moi.Code, Epoque, "retire"));
        Appliquer(Annuaire.Retirer(MesAmis, code, Epoque));
        _paires.Remove(code);
        EcrireAmis();
    }

    internal void Renommer(Ami a, string surnom)
    {
        a.Surnom = Amis.Nettoyer(surnom, 24);
        EcrireAmis();
    }

    internal void ReglerAmis(Action<Reglages> changer)
    {
        changer(_reglages);
        _reglages.Ecrire(_dossier);
        _presenceSignature = "";
    }
}

// Fenêtre « Amis de Pilou » : mon code (et son QR), ajouter un code, demandes reçues, liste d'amis
// (niveau, stade, en ligne, cœurs d'amitié ; aller le voir, renommer, retirer), réglages des visites.
internal sealed class FenetreListeAmis : Window
{
    private readonly FenetrePilou _pilou;
    private readonly StackPanel _corps = new() { Margin = new Thickness(16) };
    private readonly TextBlock _message = new() { FontSize = 12, Margin = new Thickness(0, 4, 0, 4), TextWrapping = TextWrapping.Wrap };
    private readonly TextBox _saisie = new() { FontFamily = new FontFamily("Consolas"), FontSize = 15, MinWidth = 220, Padding = new Thickness(4, 2, 4, 2) };
    private readonly DispatcherTimer _minuteur;

    private static readonly Brush Bleu = Geler("#2f7ed8"), Orange = Geler("#c86a1c"), Argent = Geler("#768390");

    private static Brush Geler(string hex)
    {
        var b = new SolidColorBrush((Color)ColorConverter.ConvertFromString(hex));
        b.Freeze();
        return b;
    }

    public FenetreListeAmis(FenetrePilou pilou)
    {
        _pilou = pilou;
        Title = "Amis de Pilou";
        Width = 560;
        Height = 680;
        WindowStartupLocation = WindowStartupLocation.CenterScreen;
        Topmost = true;
        Content = new ScrollViewer { Content = _corps, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
        _minuteur = new DispatcherTimer(TimeSpan.FromSeconds(5), DispatcherPriority.Background, (_, _) => Remplir(), Dispatcher);
        _minuteur.Start();
        Closed += (_, _) => _minuteur.Stop();
        Remplir();
    }

    private void Section(string titre) =>
        _corps.Children.Add(new TextBlock { Text = titre, FontSize = 14, FontWeight = FontWeights.Bold, Margin = new Thickness(0, 14, 0, 4) });

    private void Note(string texte) =>
        _corps.Children.Add(new TextBlock { Text = texte, FontSize = 11.5, Foreground = Argent, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 0, 0, 4) });

    private static Button Bouton(string texte, Action action, bool actif = true)
    {
        var b = new Button { Content = texte, Padding = new Thickness(8, 2, 8, 2), Margin = new Thickness(6, 0, 0, 0), IsEnabled = actif };
        b.Click += (_, _) => action();
        return b;
    }

    public void Remplir()
    {
        var c = _pilou.CarnetDesAmis;
        double maintenant = _pilou.EpoqueAmis;
        // Garder ce qu'on était en train de taper.
        var saisie = _saisie.Text;
        _corps.Children.Clear();

        Section("Ton code ami");
        var rangee = new StackPanel { Orientation = Orientation.Horizontal };
        var code = Amis.Formater(c.Moi.Code);
        rangee.Children.Add(new TextBox
        {
            Text = code, IsReadOnly = true, FontFamily = new FontFamily("Consolas"), FontSize = 20, BorderThickness = new Thickness(0),
            VerticalAlignment = VerticalAlignment.Center,
        });
        rangee.Children.Add(Bouton("Copier", () =>
        {
            Clipboard.SetText(code);
            _message.Text = "✓ code copié : envoie-le à ton ami (il le tape dans « Ajouter un ami »).";
        }));
        _corps.Children.Add(rangee);
        try
        {
            var png = new PngByteQRCode(new QRCodeGenerator().CreateQrCode(code, QRCodeGenerator.ECCLevel.M)).GetGraphic(5);
            var image = new BitmapImage();
            image.BeginInit();
            image.StreamSource = new MemoryStream(png);
            image.CacheOption = BitmapCacheOption.OnLoad;
            image.EndInit();
            _corps.Children.Add(new Image { Source = image, Width = 120, Height = 120, HorizontalAlignment = HorizontalAlignment.Left, Margin = new Thickness(0, 6, 0, 0) });
        }
        catch (Exception)
        {
            // pas de QR : le code suffit
        }
        Note("Distinct du code de groupe (tes propres appareils). L'amitié est active quand chacun a tapé le code de l'autre, "
             + "ou quand tu acceptes sa demande.");

        Section("Ajouter un ami");
        var ajout = new StackPanel { Orientation = Orientation.Horizontal };
        _saisie.Text = saisie;
        ajout.Children.Add(_saisie);
        ajout.Children.Add(Bouton("Ajouter", () =>
        {
            var refus = _pilou.Ajouter(_saisie.Text);
            _message.Text = refus is null ? "✓ demande envoyée : elle sera acceptée dès que ton ami t'ajoute aussi." : $"✕ {refus}";
            if (refus is null) _saisie.Text = "";
            Remplir();
        }));
        _corps.Children.Add(ajout);
        _corps.Children.Add(_message);

        var recues = c.Amis.Where(a => a.Etat == EtatAmi.Recue).ToList();
        if (recues.Count > 0)
        {
            Section("✉ Demandes reçues");
            foreach (var a in recues)
                Ligne(a, $"✉ {a.Nom}", $"niveau {a.Pilou.Niveau} · {Amis.Formater(a.Code)}", Orange,
                    Bouton("Accepter", () => { _pilou.Accepter(a.Code); Remplir(); }),
                    Bouton("Refuser", () => { _pilou.Retirer(a.Code); Remplir(); }));
        }

        Section($"♥ Amis ({c.Amis.Count(a => a.Etat != EtatAmi.Recue)})");
        if (c.Amis.All(a => a.Etat == EtatAmi.Recue)) Note("Pas encore d'amis : échangez vos codes.");
        foreach (var a in c.Amis.Where(a => a.Etat != EtatAmi.Recue).OrderByDescending(a => Amis.EnLigne(a, maintenant)).ThenBy(a => a.Nom))
        {
            bool enLigne = Amis.EnLigne(a, maintenant);
            string signe = a.Etat == EtatAmi.Attente ? "◌" : enLigne ? "●" : "○";
            var couleur = a.Etat == EtatAmi.Attente ? Orange : enLigne ? Bleu : Argent;
            var coeurs = a.Amitie > 0 ? $" · ♥ {a.Amitie}" : "";
            var detail = a.Etat == EtatAmi.Attente
                ? $"{Amis.Formater(a.Code)} · {Amis.VuIlYa(a, maintenant)}"
                : $"niveau {a.Pilou.Niveau} · {Amis.NomStade(a.Pilou.Stade)} · {Amis.VuIlYa(a, maintenant)}{coeurs}"
                  + (enLigne && !a.Pilou.Accepte ? " · ne reçoit pas" : enLigne && !a.Pilou.Libre ? " · occupé" : "");
            var boutons = new List<Button>();
            if (a.Etat == EtatAmi.Actif)
            {
                bool chez = _pilou.EnVisiteChez(a.Code);
                boutons.Add(chez
                    ? Bouton("Rappeler", () => { _pilou.Rappeler(); Remplir(); })
                    : Bouton("Aller voir", () => { _pilou.Partir(a, false); Remplir(); },
                        enLigne && a.Pilou.Accepte && a.Pilou.Libre && !_pilou.Occupe));
                boutons.Add(Bouton("Renommer", () =>
                {
                    var nom = Saisie.Demander("Renommer", "Le nom que tu donnes à cet ami (seulement sur ce PC).", a.Nom);
                    if (nom is not null) _pilou.Renommer(a, nom);
                    Remplir();
                }));
            }
            boutons.Add(Bouton(a.Etat == EtatAmi.Attente ? "Annuler" : "Retirer", () =>
            {
                if (a.Etat == EtatAmi.Actif && MessageBox.Show(this, $"Retirer {a.Nom} de tes amis ?", "Amis de Pilou", MessageBoxButton.YesNo) != MessageBoxResult.Yes) return;
                _pilou.Retirer(a.Code);
                Remplir();
            }));
            Ligne(a, $"{signe} {a.Nom}", detail, couleur, boutons.ToArray());
        }

        Section("Visites");
        var r = _pilou.ReglagesAmis;
        Case("Accepter les visites", r.AccepterVisites, v => _pilou.ReglerAmis(x => x.AccepterVisites = v));
        Case("Mon Pilou peut partir en visite (de lui-même, deux fois par jour au plus)", r.PartirEnVisite, v => _pilou.ReglerAmis(x => x.PartirEnVisite = v));
        Case("Partager mes anecdotes (plus belle prise, dernier plat, quête, succès, météo)", r.PartagerAnecdotes, v => _pilou.ReglerAmis(x => x.PartagerAnecdotes = v));
        var calme = new ComboBox { Margin = new Thickness(0, 4, 0, 0), HorizontalAlignment = HorizontalAlignment.Left, MinWidth = 260 };
        var choix = new[] { ("Heures calmes : 22 h – 8 h", 22, 8), ("Heures calmes : 21 h – 9 h", 21, 9), ("Heures calmes : 20 h – 8 h", 20, 8), ("Pas d'heures calmes", 0, 0) };
        foreach (var (texte, _, _) in choix) calme.Items.Add(texte);
        calme.SelectedIndex = Math.Max(0, Array.FindIndex(choix, x => x.Item2 == r.CalmeDebut && x.Item3 == r.CalmeFin));
        calme.SelectionChanged += (_, _) =>
        {
            var (_, d, f) = choix[Math.Max(0, calme.SelectedIndex)];
            _pilou.ReglerAmis(x => { x.CalmeDebut = d; x.CalmeFin = f; });
        };
        _corps.Children.Add(calme);
        Note("Ce que tes amis reçoivent : le nom, le niveau, le stade, la couleur et les objets portés de Pilou, s'il est là, "
             + "et (si la case est cochée) ces quelques anecdotes. Jamais tes fenêtres, tes sessions, tes connecteurs ni ta ville. "
             + "Tout passe chiffré par le relais ntfy. Détails : docs/AMIS.md.");
    }

    private void Case(string texte, bool valeur, Action<bool> changer)
    {
        var cb = new CheckBox { Content = texte, IsChecked = valeur, Margin = new Thickness(0, 2, 0, 2) };
        cb.Click += (_, _) => changer(cb.IsChecked == true);
        _corps.Children.Add(cb);
    }

    private void Ligne(Ami a, string titre, string detail, Brush couleur, params Button[] boutons)
    {
        var rangee = new DockPanel { Margin = new Thickness(0, 3, 0, 3) };
        var droite = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
        foreach (var b in boutons) droite.Children.Add(b);
        DockPanel.SetDock(droite, Dock.Right);
        rangee.Children.Add(droite);
        var texte = new TextBlock { VerticalAlignment = VerticalAlignment.Center, TextWrapping = TextWrapping.Wrap };
        texte.Inlines.Add(new System.Windows.Documents.Run(titre) { FontWeight = FontWeights.SemiBold, Foreground = couleur });
        texte.Inlines.Add(new System.Windows.Documents.LineBreak());
        texte.Inlines.Add(new System.Windows.Documents.Run(detail) { Foreground = Argent, FontSize = 11.5 });
        rangee.Children.Add(texte);
        _corps.Children.Add(rangee);
    }
}
