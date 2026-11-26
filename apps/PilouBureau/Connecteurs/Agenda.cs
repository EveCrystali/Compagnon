using System.Globalization;
using System.Xml;
using static PilouBureau.OutilsConnecteur;

namespace PilouBureau;

// Un événement d'agenda (VEVENT), avec sa règle de récurrence simple s'il en a une.
public sealed record EvenementIcs(string Uid, string Titre, DateTimeOffset Debut, DateTimeOffset Fin, bool JourEntier,
    RegleIcs? Regle, IReadOnlyList<DateTimeOffset> Exclus, DateTimeOffset? RemplaceOccurrence, TimeZoneInfo? Fuseau);

// FREQ=DAILY|WEEKLY, INTERVAL, COUNT, UNTIL, BYDAY (hebdomadaire) : de quoi couvrir les réunions courantes.
public sealed record RegleIcs(string Frequence, int Intervalle, int? Compte, DateTimeOffset? Jusque, IReadOnlyList<DayOfWeek> Jours);

public sealed record Occurrence(string Titre, DateTimeOffset Debut, DateTimeOffset Fin)
{
    public string Cle => $"{Titre}@{Debut.UtcDateTime:yyyyMMddTHHmm}";
}

// Lecture d'un calendrier iCalendar (RFC 5545), minimale mais attentive aux fuseaux et aux récurrences simples.
public static class Ics
{
    public static List<EvenementIcs> Lire(string texte)
    {
        var evts = new List<EvenementIcs>();
        // Dépliage : une ligne qui commence par un espace ou une tabulation continue la précédente.
        var lignes = new List<string>();
        foreach (var brute in texte.Replace("\r\n", "\n").Split('\n'))
        {
            if ((brute.StartsWith(' ') || brute.StartsWith('\t')) && lignes.Count > 0) lignes[^1] += brute[1..];
            else lignes.Add(brute);
        }
        Dictionary<string, (string Valeur, Dictionary<string, string> Params)>? courant = null;
        var exclus = new List<(string, Dictionary<string, string>)>();
        foreach (var l in lignes)
        {
            if (l == "BEGIN:VEVENT")
            {
                courant = new(StringComparer.OrdinalIgnoreCase);
                exclus.Clear();
                continue;
            }
            if (l == "END:VEVENT" && courant is not null)
            {
                if (Construire(courant, exclus) is { } e) evts.Add(e);
                courant = null;
                continue;
            }
            if (courant is null) continue;
            int deux = IndexDeuxPoints(l);
            if (deux <= 0) continue;
            var tete = l[..deux].Split(';');
            var p = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (var x in tete.Skip(1))
            {
                var kv = x.Split('=', 2);
                if (kv.Length == 2) p[kv[0]] = kv[1].Trim('"');
            }
            var nom = tete[0].ToUpperInvariant();
            var valeur = l[(deux + 1)..];
            if (nom == "EXDATE") exclus.Add((valeur, p));
            else courant[nom] = (valeur, p);
        }
        return evts;
    }

    // Le « : » qui sépare la tête de la valeur, hors des paramètres entre guillemets.
    private static int IndexDeuxPoints(string l)
    {
        bool guillemets = false;
        for (int i = 0; i < l.Length; i++)
        {
            if (l[i] == '"') guillemets = !guillemets;
            else if (l[i] == ':' && !guillemets) return i;
        }
        return -1;
    }

    private static string Texte(string v) =>
        v.Replace("\\n", " ").Replace("\\N", " ").Replace("\\,", ",").Replace("\\;", ";").Replace("\\\\", "\\").Trim();

    public static TimeZoneInfo? Fuseau(string? id)
    {
        if (string.IsNullOrEmpty(id)) return null;
        try
        {
            return TimeZoneInfo.FindSystemTimeZoneById(id);
        }
        catch (Exception e) when (e is TimeZoneNotFoundException or InvalidTimeZoneException)
        {
            // Outlook écrit parfois des noms Windows, Google des noms IANA : on tente la conversion.
            if (TimeZoneInfo.TryConvertWindowsIdToIanaId(id, out var iana) && Essayer(iana) is { } a) return a;
            if (TimeZoneInfo.TryConvertIanaIdToWindowsId(id, out var win) && Essayer(win) is { } b) return b;
            return null;
        }

        static TimeZoneInfo? Essayer(string i)
        {
            try
            {
                return TimeZoneInfo.FindSystemTimeZoneById(i);
            }
            catch (Exception e) when (e is TimeZoneNotFoundException or InvalidTimeZoneException)
            {
                return null;
            }
        }
    }

    // « 20261126T093000Z » (UTC), « 20261126T093000 » (fuseau TZID, sinon heure locale), « 20261126 » (jour entier).
    public static (DateTimeOffset Instant, bool JourEntier)? Date(string valeur, string? tzid, TimeZoneInfo? local = null)
    {
        valeur = valeur.Trim();
        if (valeur.Length == 8 && DateTime.TryParseExact(valeur, "yyyyMMdd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var jour))
            return (Placer(jour, Fuseau(tzid) ?? local ?? TimeZoneInfo.Local), true);
        if (valeur.EndsWith('Z') && DateTime.TryParseExact(valeur, "yyyyMMdd'T'HHmmss'Z'", CultureInfo.InvariantCulture,
                DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal, out var utc))
            return (new DateTimeOffset(utc, TimeSpan.Zero), false);
        if (DateTime.TryParseExact(valeur, "yyyyMMdd'T'HHmmss", CultureInfo.InvariantCulture, DateTimeStyles.None, out var mur))
            return (Placer(mur, Fuseau(tzid) ?? local ?? TimeZoneInfo.Local), false);
        return null;
    }

    // Heure murale d'un fuseau → instant (heure d'été comprise ; une heure qui n'existe pas glisse d'une heure).
    public static DateTimeOffset Placer(DateTime mur, TimeZoneInfo z)
    {
        mur = DateTime.SpecifyKind(mur, DateTimeKind.Unspecified);
        if (z.IsInvalidTime(mur)) mur = mur.AddHours(1);
        return new DateTimeOffset(mur, z.GetUtcOffset(mur));
    }

    private static EvenementIcs? Construire(Dictionary<string, (string Valeur, Dictionary<string, string> Params)> p,
        List<(string Valeur, Dictionary<string, string> Params)> exclus)
    {
        if (p.TryGetValue("STATUS", out var st) && st.Valeur.Equals("CANCELLED", StringComparison.OrdinalIgnoreCase)) return null;
        if (!p.TryGetValue("DTSTART", out var ds)) return null;
        ds.Params.TryGetValue("TZID", out var tz);
        if (Date(ds.Valeur, tz) is not { } debut) return null;
        DateTimeOffset fin = debut.Instant + (debut.JourEntier ? TimeSpan.FromDays(1) : TimeSpan.FromHours(1));
        if (p.TryGetValue("DTEND", out var de))
        {
            de.Params.TryGetValue("TZID", out var tz2);
            if (Date(de.Valeur, tz2) is { } f) fin = f.Instant;
        }
        else if (p.TryGetValue("DURATION", out var du))
        {
            try
            {
                fin = debut.Instant + XmlConvert.ToTimeSpan(du.Valeur.Trim());
            }
            catch (FormatException)
            {
            }
        }
        RegleIcs? regle = p.TryGetValue("RRULE", out var rr) ? Regle(rr.Valeur, tz) : null;
        var ex = new List<DateTimeOffset>();
        foreach (var (v, pa) in exclus)
        {
            pa.TryGetValue("TZID", out var tze);
            foreach (var x in v.Split(','))
                if (Date(x, tze ?? tz) is { } d) ex.Add(d.Instant);
        }
        DateTimeOffset? remplace = null;
        if (p.TryGetValue("RECURRENCE-ID", out var ri))
        {
            ri.Params.TryGetValue("TZID", out var tzr);
            remplace = Date(ri.Valeur, tzr ?? tz)?.Instant;
        }
        var titre = p.TryGetValue("SUMMARY", out var su) ? Texte(su.Valeur) : "(sans titre)";
        var uid = p.TryGetValue("UID", out var u) ? u.Valeur : titre;
        return new EvenementIcs(uid, titre, debut.Instant, fin, debut.JourEntier, regle, ex, remplace, Fuseau(tz));
    }

    private static readonly Dictionary<string, DayOfWeek> JoursIcs = new()
    {
        ["MO"] = DayOfWeek.Monday, ["TU"] = DayOfWeek.Tuesday, ["WE"] = DayOfWeek.Wednesday, ["TH"] = DayOfWeek.Thursday,
        ["FR"] = DayOfWeek.Friday, ["SA"] = DayOfWeek.Saturday, ["SU"] = DayOfWeek.Sunday,
    };

    public static RegleIcs? Regle(string valeur, string? tzid)
    {
        var d = valeur.Split(';').Select(x => x.Split('=', 2)).Where(x => x.Length == 2)
            .ToDictionary(x => x[0].ToUpperInvariant(), x => x[1], StringComparer.OrdinalIgnoreCase);
        if (!d.TryGetValue("FREQ", out var freq) || freq.ToUpperInvariant() is not ("DAILY" or "WEEKLY")) return null;
        int intervalle = d.TryGetValue("INTERVAL", out var i) && int.TryParse(i, out var n) && n > 0 ? n : 1;
        int? compte = d.TryGetValue("COUNT", out var c) && int.TryParse(c, out var k) ? k : null;
        DateTimeOffset? jusque = d.TryGetValue("UNTIL", out var un) && Date(un, tzid) is { } u ? u.Instant : null;
        var jours = d.TryGetValue("BYDAY", out var bd)
            ? bd.Split(',').Select(x => x.Trim().ToUpperInvariant()).Select(x => x.Length > 2 ? x[^2..] : x)
                .Where(JoursIcs.ContainsKey).Select(x => JoursIcs[x]).ToList()
            : new List<DayOfWeek>();
        return new RegleIcs(freq.ToUpperInvariant(), intervalle, compte, jusque, jours);
    }

    // Toutes les occurrences qui touchent [de, a[ (jours entiers exclus : ce ne sont pas des réunions).
    public static List<Occurrence> Occurrences(IEnumerable<EvenementIcs> evts, DateTimeOffset de, DateTimeOffset a)
    {
        var liste = evts.ToList();
        var remplaces = liste.Where(e => e.RemplaceOccurrence is not null).ToLookup(e => e.Uid, e => e.RemplaceOccurrence!.Value);
        var res = new List<Occurrence>();
        foreach (var e in liste)
        {
            if (e.JourEntier) continue;
            var duree = e.Fin - e.Debut;
            foreach (var debut in Debuts(e, a))
            {
                if (e.Regle is not null && (e.Exclus.Contains(debut) || remplaces[e.Uid].Contains(debut))) continue;
                var fin = debut + duree;
                if (fin > de && debut < a) res.Add(new Occurrence(e.Titre, debut, fin));
            }
        }
        return res.OrderBy(o => o.Debut).ToList();
    }

    // Débuts successifs (au plus 3 000 pas), calculés en heure murale du fuseau de l'événement : une réunion de
    // 9 h reste à 9 h après le passage à l'heure d'été.
    private static IEnumerable<DateTimeOffset> Debuts(EvenementIcs e, DateTimeOffset a)
    {
        if (e.Regle is not { } r)
        {
            yield return e.Debut;
            yield break;
        }
        var z = e.Fuseau ?? TimeZoneInfo.Local;
        var mur0 = TimeZoneInfo.ConvertTime(e.Debut, z).DateTime;
        int emis = 0;
        for (int pas = 0; pas < 3000; pas++)
        {
            IEnumerable<DateTime> candidats;
            if (r.Frequence == "DAILY") candidats = new[] { mur0.AddDays((double)pas * r.Intervalle) };
            else
            {
                var semaine = mur0.Date.AddDays(-(((int)mur0.DayOfWeek + 6) % 7)).AddDays(7.0 * pas * r.Intervalle);
                var jours = r.Jours.Count > 0 ? r.Jours : new List<DayOfWeek> { mur0.DayOfWeek };
                candidats = jours.Select(j => semaine.AddDays(((int)j + 6) % 7) + mur0.TimeOfDay).OrderBy(x => x);
            }
            foreach (var m in candidats)
            {
                if (m < mur0) continue;
                var instant = Placer(m, z);
                if (r.Jusque is { } j && instant > j) yield break;
                if (r.Compte is { } c && emis >= c) yield break;
                if (instant >= a) yield break;
                emis++;
                yield return instant;
            }
        }
    }
}

// ------------------------------------------------------------------------------------------------------
// Agenda : un lien d'abonnement ICS (Google, Outlook, iCloud…). 5 min avant une réunion, Pilou prévient ;
// pendant la réunion, il se cache comme en visio. Le lien est secret : chiffré sur ce PC.
// ------------------------------------------------------------------------------------------------------
public sealed class ConnecteurAgenda : Connecteur
{
    public override string Id => "agenda";
    public override string Nom => "Agenda";
    public override string Description =>
        "Tes réunions, par le lien d'abonnement de ton agenda : Pilou te prévient avant, puis se fait discret pendant. " +
        "Seuls les titres et les horaires sont lus.";
    public override string Signe => "▦";
    public override TimeSpan Intervalle => TimeSpan.FromMinutes(1);

    public override string Aide =>
        "• Google Agenda : paramètres de l'agenda → « Intégrer l'agenda » → « Adresse secrète au format iCal » → copie.\n" +
        "• Outlook.com / Microsoft 365 : Paramètres → Calendrier → Calendriers partagés → Publier un calendrier → lien ICS.\n" +
        "• iCloud : partage public de l'agenda → lien webcal:// (remplace webcal par https).\n" +
        "Colle le lien ci-dessous : il donne accès à ton agenda, il est donc chiffré sur ce PC.";

    public override IReadOnlyList<ReglageConnecteur> Reglages { get; } = new[]
    {
        new ReglageConnecteur("url", "Lien d'abonnement ICS", TypeReglage.Secret, "https://… .ics"),
        new ReglageConnecteur("avance", "Prévenir (minutes avant)", TypeReglage.Liste, "", "5", new[] { "2", "5", "10", "15" }),
        new ReglageConnecteur("cacher", "Se cacher pendant les réunions", TypeReglage.Case, "", "oui"),
    };

    public override string? Manque(ContexteConnecteur ctx) => ctx.Lire("url") == "" ? "colle le lien d'abonnement de ton agenda" : null;

    // Lu par la fenêtre de Pilou (discrétion) ; Inactivite est fournie par elle (ms depuis la dernière saisie).
    public static volatile bool EnReunion;
    public static Func<double> Inactivite { get; set; } = () => 0;

    private string _ics = "";
    private DateTime _charge = DateTime.MinValue;
    private readonly HashSet<string> _prevenus = new(), _commencees = new();

    public override async Task Sonder(ContexteConnecteur ctx, CancellationToken ct)
    {
        if (ctx.Maintenant - _charge > TimeSpan.FromMinutes(30) || _ics == "")
        {
            var url = ctx.Lire("url").Trim();
            if (url.StartsWith("webcal://", StringComparison.OrdinalIgnoreCase)) url = "https://" + url[9..];
            _ics = await ctx.Http.GetStringAsync(url, ct);
            _charge = ctx.Maintenant;
        }
        foreach (var e in Examiner(Ics.Lire(_ics), new DateTimeOffset(ctx.Maintenant), int.TryParse(ctx.Lire("avance"), out var av) ? av : 5,
                     Oui(ctx.Lire("cacher")), Inactivite()))
            ctx.Emettre(e);
    }

    // À cet instant : rappels dus, réunions qui commencent (quête « ponctuel » si on est là), discrétion.
    public List<EvenementPilou> Examiner(List<EvenementIcs> evts, DateTimeOffset maintenant, int avance, bool cacher, double inactifMs)
    {
        var sortie = new List<EvenementPilou>();
        var proches = Ics.Occurrences(evts, maintenant.AddHours(-12), maintenant.AddHours(12))
            .Where(o => o.Fin - o.Debut <= TimeSpan.FromHours(8)).ToList();
        foreach (var o in proches)
        {
            var avant = o.Debut - maintenant;
            if (avant > TimeSpan.Zero && avant <= TimeSpan.FromMinutes(avance) && _prevenus.Add(o.Cle))
                sortie.Add(new EvenementPilou(Id, "notification", $"▦ Dans {Math.Max(1, (int)Math.Ceiling(avant.TotalMinutes))} min",
                    Court(o.Titre, 80), 1));
            if (o.Debut <= maintenant && maintenant < o.Debut.AddMinutes(2) && _commencees.Add(o.Cle) && inactifMs < 2 * 60_000)
                sortie.Add(new EvenementPilou(Id, "notification", "▦ C'est l'heure", Court(o.Titre, 80), 0,
                    0, new Dictionary<string, string> { ["quete"] = "agenda:ponctuel" }));
        }
        EnReunion = cacher && proches.Any(o => o.Debut <= maintenant && maintenant < o.Fin);
        return sortie;
    }
}
