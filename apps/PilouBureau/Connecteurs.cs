using System.Globalization;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace PilouBureau;

// ======================================================================================================
// Connecteurs : Pilou est l'application, chaque service (Claude, Codex, météo, Discord, GitHub…) est un
// connecteur qu'on branche. Un connecteur s'ajoute en UN fichier : une classe qui hérite de `Connecteur`,
// déclare ses réglages typés et implémente `Sonder` (relevé périodique) ou `Ecouter` (écoute permanente),
// puis une ligne dans `Registre.Standard`. Tout ce qu'il apprend, il l'émet en `EvenementPilou` : la bulle,
// l'humeur, les quêtes et les sorties (téléphone, Discord, webhook) n'en connaissent que ce format.
// ======================================================================================================

// Un événement, quelle que soit sa source. Type : session | attente | fin | erreur | message | notification
// | meteo | activite… ; Gravite : 0 info, 1 à voir, 2 urgent (on t'attend).
public sealed record EvenementPilou(string Source, string Type, string Titre, string Texte = "", int Gravite = 0,
    double T = 0, IReadOnlyDictionary<string, string>? Donnees = null)
{
    public static readonly string[] Types = { "session", "attente", "fin", "erreur", "message", "notification", "meteo", "activite" };

    public string Donnee(string cle) => Donnees is not null && Donnees.TryGetValue(cle, out var v) ? v : "";

    public string Json()
    {
        var o = new JsonObject
        {
            ["source"] = Source, ["type"] = Type, ["titre"] = Titre, ["texte"] = Texte, ["gravite"] = Gravite, ["t"] = T,
        };
        if (Donnees is { Count: > 0 })
        {
            var d = new JsonObject();
            foreach (var (k, v) in Donnees) d[k] = v;
            o["donnees"] = d;
        }
        return o.ToJsonString();
    }

    // Lecture tolérante (API locale) ; null si ce n'est pas un événement valable. La source est bornée à
    // 24 lettres/chiffres, les textes à 300 caractères : rien d'énorme n'entre dans la bulle.
    public static EvenementPilou? Lire(string json, double maintenant, out string erreur)
    {
        erreur = "";
        try
        {
            if (JsonNode.Parse(json) is not JsonObject o)
            {
                erreur = "objet JSON attendu";
                return null;
            }
            string S(string k, int max) => o[k] is JsonValue v && v.TryGetValue<string>(out var s) ? s.Trim()[..Math.Min(max, s.Trim().Length)] : "";
            var source = Signal.Propre(S("source", 64), "");
            var type = S("type", 24).ToLowerInvariant();
            var titre = S("titre", 300);
            if (source == "") erreur = "« source » manquante (lettres et chiffres)";
            else if (!Types.Contains(type)) erreur = $"« type » inconnu (attendu : {string.Join(", ", Types)})";
            else if (titre == "") erreur = "« titre » manquant";
            if (erreur != "") return null;
            int gravite = o["gravite"] is JsonValue g && g.TryGetValue<int>(out var n) ? Math.Clamp(n, 0, 2) : 0;
            Dictionary<string, string>? d = null;
            if (o["donnees"] is JsonObject dd)
            {
                d = new();
                foreach (var (k, v) in dd.Take(20))
                    if (v is JsonValue jv) d[Signal.Propre(k, "x", 32)] = jv.ToString()[..Math.Min(300, jv.ToString().Length)];
            }
            return new EvenementPilou(source, type, titre, S("texte", 300), gravite, maintenant, d);
        }
        catch (JsonException)
        {
            erreur = "JSON illisible";
            return null;
        }
    }
}

public enum EtatConnecteur { Desactive, Actif, Erreur, AConfigurer }

public enum TypeReglage { Texte, Secret, Liste, Case }

// Un réglage déclaré par un connecteur ; la fenêtre Connecteurs le dessine selon son type.
// Secret : stocké chiffré (DPAPI, compte Windows courant), jamais dans reglages.json, affiché masqué.
// Visible = false : valeur interne du connecteur (jeton OAuth, curseur de lecture…), gardée mais pas montrée.
public sealed record ReglageConnecteur(string Cle, string Nom, TypeReglage Type, string Aide = "", string Defaut = "",
    IReadOnlyList<string>? Choix = null, bool Visible = true);

// Une action proposée par un connecteur (bouton dans la fenêtre Connecteurs) ; renvoie un message court.
public sealed record ActionConnecteur(string Nom, Func<ContexteConnecteur, CancellationToken, Task<string>> Faire);

public enum ModeConnecteur
{
    Passif,    // déjà branché ailleurs dans Pilou : seulement montré, activé ou coupé ici
    Sondage,   // Sonder() toutes les `Intervalle`
    Ecoute,    // Ecouter() tourne en permanence (connexion ouverte), relancé s'il s'arrête
}

public abstract class Connecteur
{
    public abstract string Id { get; }
    public abstract string Nom { get; }
    public abstract string Description { get; }
    public virtual string Signe => "◆";
    public virtual ModeConnecteur Mode => ModeConnecteur.Sondage;
    public virtual TimeSpan Intervalle => TimeSpan.FromMinutes(15);
    public virtual IReadOnlyList<ReglageConnecteur> Reglages => Array.Empty<ReglageConnecteur>();
    public virtual IReadOnlyList<ActionConnecteur> Actions => Array.Empty<ActionConnecteur>();
    public virtual bool ActifParDefaut => false;

    // Pas à pas pour l'activer (créer une application développeur, un jeton…), montré dans la fenêtre Connecteurs.
    public virtual string Aide => "";

    // Sortie : le connecteur reçoit aussi les événements de Pilou (une IA attend, quête réussie, évolution).
    public virtual bool Sortie => false;

    public virtual Task Sortir(ContexteConnecteur ctx, EvenementPilou e, CancellationToken ct) => Task.CompletedTask;

    // Prêt à démarrer ? Sinon, pourquoi (« choisis une ville »…) : l'interrupteur reste grisé.
    public virtual string? Manque(ContexteConnecteur ctx) => null;

    public virtual Task Sonder(ContexteConnecteur ctx, CancellationToken ct) => Task.CompletedTask;

    public virtual Task Ecouter(ContexteConnecteur ctx, CancellationToken ct) => Task.CompletedTask;

    // Pour les connecteurs passifs : état réel (branché ailleurs) et bascule.
    public virtual bool? ActifExterne => null;
    public virtual void Basculer(bool actif)
    {
    }
}

// Ce qu'un connecteur voit de Pilou : ses réglages, ses secrets, un client HTTP, l'horloge, et de quoi
// émettre des événements et écrire dans son journal.
public sealed class ContexteConnecteur
{
    private readonly Registre _r;
    public Connecteur Connecteur { get; }

    internal ContexteConnecteur(Registre r, Connecteur c)
    {
        _r = r;
        Connecteur = c;
    }

    public HttpClient Http => _r.Http;
    public DateTime Maintenant => _r.Horloge();

    public string Lire(string cle)
    {
        var def = Connecteur.Reglages.FirstOrDefault(x => x.Cle == cle);
        if (def?.Type == TypeReglage.Secret) return _r.Secrets.Lire($"{Connecteur.Id}.{cle}") ?? "";
        return _r.Valeurs(Connecteur.Id).TryGetValue(cle, out var v) ? v : def?.Defaut ?? "";
    }

    public void Ecrire(string cle, string valeur) => _r.Regler(Connecteur.Id, cle, valeur);

    public void Emettre(EvenementPilou e) => _r.Recevoir(e with { T = e.T > 0 ? e.T : _r.Epoque() });

    public void Journal(string ligne) => _r.Noter(Connecteur.Id, ligne);
}

// Secrets des connecteurs (jetons, mots de passe) : chiffrés, hors de reglages.json.
public interface ICoffre
{
    string? Lire(string cle);
    void Ecrire(string cle, string? valeur);
}

// Windows : DPAPI (ProtectedData, portée « utilisateur courant ») ; un seul fichier secrets.bin, illisible
// sur un autre compte ou un autre PC. Ailleurs (tests), un coffre en mémoire.
public sealed class CoffreDpapi : ICoffre
{
    private readonly string _chemin;
    private Dictionary<string, string> _valeurs;
    private static readonly byte[] Sel = Encoding.UTF8.GetBytes("pilou-secrets-v1");

    public CoffreDpapi(string dossier)
    {
        _chemin = Path.Combine(dossier, "secrets.bin");
        _valeurs = Charger();
    }

    private Dictionary<string, string> Charger()
    {
        try
        {
            if (!File.Exists(_chemin) || !OperatingSystem.IsWindows()) return new();
            var clair = ProtectedData.Unprotect(File.ReadAllBytes(_chemin), Sel, DataProtectionScope.CurrentUser);
            return JsonSerializer.Deserialize<Dictionary<string, string>>(clair) ?? new();
        }
        catch (Exception e) when (e is IOException or CryptographicException or JsonException or UnauthorizedAccessException)
        {
            return new(); // coffre d'un autre compte ou abîmé : on repart vide (les jetons sont à ressaisir)
        }
    }

    public string? Lire(string cle) => _valeurs.TryGetValue(cle, out var v) ? v : null;

    public void Ecrire(string cle, string? valeur)
    {
        if (string.IsNullOrEmpty(valeur)) _valeurs.Remove(cle);
        else _valeurs[cle] = valeur;
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            var chiffre = ProtectedData.Protect(JsonSerializer.SerializeToUtf8Bytes(_valeurs), Sel, DataProtectionScope.CurrentUser);
            Directory.CreateDirectory(Path.GetDirectoryName(_chemin)!);
            File.WriteAllBytes(_chemin, chiffre);
        }
        catch (Exception e) when (e is IOException or CryptographicException or UnauthorizedAccessException)
        {
            // gardé en mémoire pour cette exécution
        }
    }
}

public sealed class CoffreMemoire : ICoffre
{
    public readonly Dictionary<string, string> Valeurs = new();
    public string? Lire(string cle) => Valeurs.TryGetValue(cle, out var v) ? v : null;

    public void Ecrire(string cle, string? valeur)
    {
        if (string.IsNullOrEmpty(valeur)) Valeurs.Remove(cle);
        else Valeurs[cle] = valeur;
    }
}

// Réglages persistants des connecteurs (dans reglages.json, sauf les secrets).
public sealed class ReglagesConnecteurs
{
    public Dictionary<string, bool> Actifs { get; set; } = new();
    public Dictionary<string, Dictionary<string, string>> Valeurs { get; set; } = new();
    // API locale : port (127.0.0.1 seulement) et jeton (pas un secret de service : il ne protège que la
    // machine elle-même contre les autres comptes et les pages web).
    public bool Api { get; set; } = true;
    public int PortApi { get; set; } = ApiLocale.PortParDefaut;
    public string JetonApi { get; set; } = "";
    // Téléphone : carte « Nouvelles » (5 derniers événements), avec ou sans leur contenu.
    public bool AnnoncesTelephone { get; set; } = true;
    public bool AnnoncesSansContenu { get; set; }
}

public sealed record LigneJournal(DateTime T, string Connecteur, string Texte);

// Les connecteurs branchés, leur état, leur journal ; planifie les relevés et les écoutes.
public sealed class Registre
{
    public const int TailleJournal = 50;

    private readonly ReglagesConnecteurs _reglages;
    private readonly Action _sauver;
    private readonly List<Connecteur> _liste = new();
    private readonly Dictionary<string, DateTime> _prochain = new();
    private readonly Dictionary<string, (Task Tache, CancellationTokenSource Arret)> _enCours = new();
    private readonly Dictionary<string, string> _erreurs = new();
    private readonly Dictionary<string, EvenementPilou> _derniers = new();
    private readonly LinkedList<LigneJournal> _journal = new();
    private readonly LinkedList<EvenementPilou> _annonces = new();
    public const int TailleAnnonces = 5;
    private readonly object _verrou = new();

    public ICoffre Secrets { get; }
    public HttpClient Http { get; }
    public Func<DateTime> Horloge { get; set; } = () => DateTime.Now;
    public Func<double> Epoque { get; set; } = () => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

    // Appelé (sur n'importe quel fil) pour chaque événement émis : la fenêtre le ramène sur son fil d'interface.
    public event Action<EvenementPilou>? Evenement;

    public Registre(ReglagesConnecteurs reglages, ICoffre secrets, Action sauver, HttpClient? http = null)
    {
        _reglages = reglages;
        Secrets = secrets;
        _sauver = sauver;
        Http = http ?? Client();
    }

    private static HttpClient Client()
    {
        var h = new HttpClient { Timeout = TimeSpan.FromSeconds(20) };
        h.DefaultRequestHeaders.UserAgent.ParseAdd("pilou-bureau");
        return h;
    }

    public IReadOnlyList<Connecteur> Liste => _liste;
    public ReglagesConnecteurs Reglages => _reglages;

    public void Ajouter(Connecteur c)
    {
        if (_liste.Any(x => x.Id == c.Id)) return;
        _liste.Add(c);
    }

    public Connecteur? Trouver(string id) => _liste.FirstOrDefault(c => c.Id == id);

    public ContexteConnecteur Contexte(Connecteur c) => new(this, c);

    public IReadOnlyDictionary<string, string> Valeurs(string id) =>
        _reglages.Valeurs.TryGetValue(id, out var v) ? v : new Dictionary<string, string>();

    public void Regler(string id, string cle, string valeur)
    {
        var c = Trouver(id);
        var def = c?.Reglages.FirstOrDefault(x => x.Cle == cle);
        if (def?.Type == TypeReglage.Secret)
        {
            Secrets.Ecrire($"{id}.{cle}", valeur);
            return;
        }
        if (!_reglages.Valeurs.TryGetValue(id, out var v)) _reglages.Valeurs[id] = v = new();
        v[cle] = valeur;
        _sauver();
    }

    public bool Actif(Connecteur c) =>
        c.Mode == ModeConnecteur.Passif && c.ActifExterne is { } ext ? ext
        : _reglages.Actifs.TryGetValue(c.Id, out var a) ? a : c.ActifParDefaut;

    public void Activer(Connecteur c, bool actif)
    {
        if (c.Mode == ModeConnecteur.Passif) c.Basculer(actif);
        _reglages.Actifs[c.Id] = actif;
        _sauver();
        if (!actif) Arreter(c.Id);
        else _prochain.Remove(c.Id); // relevé tout de suite
        Noter(c.Id, actif ? "activé" : "coupé");
    }

    public EtatConnecteur Etat(Connecteur c)
    {
        if (!Actif(c)) return EtatConnecteur.Desactive;
        if (c.Manque(Contexte(c)) is not null) return EtatConnecteur.AConfigurer;
        lock (_verrou) return _erreurs.ContainsKey(c.Id) ? EtatConnecteur.Erreur : EtatConnecteur.Actif;
    }

    public string? Erreur(string id)
    {
        lock (_verrou) return _erreurs.TryGetValue(id, out var e) ? e : null;
    }

    public EvenementPilou? Dernier(string source)
    {
        lock (_verrou) return _derniers.TryGetValue(source, out var e) ? e : null;
    }

    public IReadOnlyList<LigneJournal> Journal()
    {
        lock (_verrou) return _journal.ToList();
    }

    public void Noter(string id, string texte)
    {
        lock (_verrou)
        {
            _journal.AddFirst(new LigneJournal(Horloge(), id, texte));
            while (_journal.Count > TailleJournal) _journal.RemoveLast();
        }
    }

    // Tout événement passe ici : journal, dernier par source, puis l'abonné (la fenêtre).
    public void Recevoir(EvenementPilou e)
    {
        if (e.T == 0) e = e with { T = new DateTimeOffset(Horloge()).ToUnixTimeMilliseconds() };
        lock (_verrou)
        {
            _derniers[e.Source] = e;
            // Nouvelles pour le téléphone : messages et notifications des connecteurs (pas la météo, déjà à part).
            if (e.Type is "message" or "notification" && e.Source != "meteo")
            {
                _annonces.AddFirst(e);
                while (_annonces.Count > TailleAnnonces) _annonces.RemoveLast();
            }
        }
        Noter(e.Source, $"{e.Type} · {e.Titre}{(e.Texte == "" ? "" : " — " + e.Texte)}");
        Evenement?.Invoke(e);
    }

    public IReadOnlyList<EvenementPilou> Annonces()
    {
        lock (_verrou) return _annonces.ToList();
    }

    // Un événement de Pilou lui-même vers les connecteurs qui ont une sortie (salon Discord…). En tâche de
    // fond ; une sortie en panne est notée au journal sans rien bloquer.
    public void Publier(EvenementPilou e)
    {
        e = e with { T = e.T > 0 ? e.T : Epoque() };
        foreach (var c in _liste)
        {
            if (!c.Sortie || !Actif(c) || c.Manque(Contexte(c)) is not null) continue;
            var ctx = Contexte(c);
            _ = Task.Run(async () =>
            {
                try
                {
                    await c.Sortir(ctx, e, CancellationToken.None);
                }
                catch (Exception x)
                {
                    Noter(c.Id, "sortie : " + (x is HttpRequestException ? "service injoignable" : x.Message));
                }
            });
        }
    }

    // Appelé régulièrement (toutes les secondes ou plus) : lance les relevés dus, garde les écoutes en vie.
    public void Battre()
    {
        var maintenant = Horloge();
        foreach (var c in _liste)
        {
            if (c.Mode == ModeConnecteur.Passif || !Actif(c) || c.Manque(Contexte(c)) is not null) continue;
            lock (_verrou)
                if (_enCours.TryGetValue(c.Id, out var t) && !t.Tache.IsCompleted) continue;
            if (c.Mode == ModeConnecteur.Sondage)
            {
                if (_prochain.TryGetValue(c.Id, out var quand) && maintenant < quand) continue;
                _prochain[c.Id] = maintenant + c.Intervalle;
                Lancer(c, (ctx, ct) => c.Sonder(ctx, ct));
            }
            else
            {
                // Une écoute qui s'arrête (erreur, coupure réseau) repart au plus tôt 30 s après.
                if (_prochain.TryGetValue(c.Id, out var quand) && maintenant < quand) continue;
                _prochain[c.Id] = maintenant + TimeSpan.FromSeconds(30);
                Lancer(c, (ctx, ct) => c.Ecouter(ctx, ct));
            }
        }
    }

    // Relevé immédiat (bouton « Actualiser », ville qui change).
    public void Maintenant(string id) => _prochain.Remove(id);

    private void Lancer(Connecteur c, Func<ContexteConnecteur, CancellationToken, Task> travail)
    {
        var arret = new CancellationTokenSource();
        var ctx = Contexte(c);
        var tache = Task.Run(async () =>
        {
            try
            {
                await travail(ctx, arret.Token);
                lock (_verrou) _erreurs.Remove(c.Id);
            }
            catch (OperationCanceledException)
            {
                // coupé
            }
            catch (Exception e)
            {
                // Un connecteur en panne ne fait jamais tomber Pilou : il passe en erreur et réessaie plus tard.
                lock (_verrou) _erreurs[c.Id] = e is HttpRequestException ? "service injoignable" : e.Message;
                Noter(c.Id, "erreur : " + (e is HttpRequestException ? "service injoignable" : e.Message));
            }
        });
        lock (_verrou) _enCours[c.Id] = (tache, arret);
    }

    public void Arreter(string id)
    {
        lock (_verrou)
            if (_enCours.TryGetValue(id, out var t))
            {
                t.Arret.Cancel();
                _enCours.Remove(id);
            }
    }

    public void ArreterTout()
    {
        foreach (var c in _liste) Arreter(c.Id);
    }

    // Jeton de l'API locale : tiré au premier usage, gardé dans les réglages.
    public string JetonApi()
    {
        if (string.IsNullOrEmpty(_reglages.JetonApi))
        {
            _reglages.JetonApi = Convert.ToHexString(RandomNumberGenerator.GetBytes(16)).ToLowerInvariant();
            _sauver();
        }
        return _reglages.JetonApi;
    }

    public void NouveauJeton()
    {
        _reglages.JetonApi = "";
        JetonApi();
    }
}

// Ce qui existe déjà dans Pilou (Claude, Codex, activités, Discord, webhook, téléphone, groupe), montré comme
// connecteur sans changer son fonctionnement : état lu et bascule écrite dans les réglages d'origine.
public sealed class ConnecteurIntegre : Connecteur
{
    private readonly Func<bool> _actif;
    private readonly Action<bool>? _basculer;

    public ConnecteurIntegre(string id, string nom, string description, string signe, Func<bool> actif, Action<bool>? basculer = null)
    {
        Id = id;
        Nom = nom;
        Description = description;
        Signe = signe;
        _actif = actif;
        _basculer = basculer;
    }

    public override string Id { get; }
    public override string Nom { get; }
    public override string Description { get; }
    public override string Signe { get; }
    public override ModeConnecteur Mode => ModeConnecteur.Passif;
    public override bool? ActifExterne => _actif();
    public bool Basculable => _basculer is not null;
    public override void Basculer(bool actif) => _basculer?.Invoke(actif);
}

// ------------------------------------------------------------------------------------------------------
// Météo (Open-Meteo, sans clé) : un relevé toutes les 15 min pour la ville choisie.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurMeteo : Connecteur
{
    public override string Id => "meteo";
    public override string Nom => "Météo";
    public override string Description =>
        "Le temps qu'il fait dans ta ville (Open-Meteo, sans compte). Pluie, neige, canicule : Pilou le vit, " +
        "et râle s'il n'a pas ce qu'il faut. Seule la position de la ville choisie part chez Open-Meteo.";
    public override string Signe => "☂";
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(15);

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("ville", "Ville", TypeReglage.Texte, "Nom de la ville, puis « Chercher la ville »"),
        new ReglageConnecteur("phrases", "Pilou commente la météo", TypeReglage.Case, "", "oui"),
    };

    public override IReadOnlyList<ActionConnecteur> Actions => new[]
    {
        new ActionConnecteur("Chercher la ville", ChercherVille),
        new ActionConnecteur("Actualiser", async (ctx, ct) =>
        {
            await Sonder(ctx, ct);
            return Meteo.Courante is { } s ? $"{Meteo.Signe(s.Etat)} {Meteo.Nom(s.Etat)}, {Math.Round(s.Releve.Temperature)} °C" : "pas de relevé";
        }),
    };

    public override string? Manque(ContexteConnecteur ctx) =>
        ctx.Lire("latitude") == "" ? "choisis une ville (« Chercher la ville »)" : null;

    private static double D(string s) => double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var d) ? d : double.NaN;

    private async Task<string> ChercherVille(ContexteConnecteur ctx, CancellationToken ct)
    {
        var nom = ctx.Lire("ville");
        if (nom.Trim().Length < 2) return "écris d'abord le nom de la ville";
        var villes = Meteo.LireVilles(await ctx.Http.GetStringAsync(Meteo.UrlRecherche(nom), ct));
        if (villes.Count == 0) return $"aucune ville « {nom} » trouvée";
        var v = villes[0];
        ctx.Ecrire("ville", v.Nom);
        ctx.Ecrire("libelle", v.Libelle);
        ctx.Ecrire("latitude", v.Latitude.ToString("0.####", CultureInfo.InvariantCulture));
        ctx.Ecrire("longitude", v.Longitude.ToString("0.####", CultureInfo.InvariantCulture));
        ctx.Journal($"ville : {v.Libelle}");
        await Sonder(ctx, ct);
        return $"ville choisie : {v.Libelle}";
    }

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        double la = D(ctx.Lire("latitude")), lo = D(ctx.Lire("longitude"));
        if (double.IsNaN(la) || double.IsNaN(lo)) return;
        string json;
        try
        {
            json = await ctx.Http.GetStringAsync(Meteo.UrlPrevision(la, lo), ct);
            ctx.Ecrire("dernier", json);
        }
        catch (HttpRequestException)
        {
            // Hors ligne : la dernière météo connue reste affichée.
            json = ctx.Lire("dernier");
            if (json == "") throw;
        }
        Appliquer(ctx, json);
    }

    // Relevé → météo courante + événement (seulement quand l'état change, pour ne pas inonder le journal).
    public void Appliquer(ContexteConnecteur ctx, string json)
    {
        var r = Meteo.Lire(json);
        if (r is null) return;
        var etat = Meteo.Etat(r);
        var ville = ctx.Lire("ville");
        var avant = Meteo.Courante?.Etat;
        Meteo.Courante = new Meteo.Situation(etat, r, ville, ctx.Maintenant);
        if (avant == etat) return;
        ctx.Emettre(new EvenementPilou("meteo", "meteo", $"{Meteo.Signe(etat)} {Meteo.Nom(etat)} à {ville}",
            $"{Math.Round(r.Temperature)} °C", 0, 0, new Dictionary<string, string> { ["etat"] = etat }));
    }
}
