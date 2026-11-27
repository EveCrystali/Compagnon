using System.Globalization;
using System.Text;

namespace PilouBureau;

// Le rythme des petits mots sur le PC : au plus trois par jour, à des moments calmes et signifiants (premier retour au
// clavier du jour, retour après une vraie pause, fin de journée), espacés d'au moins 90 minutes. Le moment attend que
// tout soit calme (ni saisie, ni plein écran, ni visio, ni IA qui attend) ; trop tard, il passe son tour, sans relance.
public sealed class Cadence
{
    public string Jour = "";
    public int Dits;
    public long DernierMot, DerniereVue, DebutSeance;
    public double PresenceJourMin;
    public bool Soir;
    public string Attente = "";
    public long AttenteDepuis;
    public int AttenteAbsence;
}

public static class Cadences
{
    public const double Pause = 45, Ecart = 90, Expire = 25, SoirApres = 90;

    public static int Plafond(string parle) => parle switch { "jamais" => 0, "peu" => 1, _ => 3 };

    // present : clavier ou souris touchés dans la dernière minute.
    public static void Observer(Cadence r, long maintenant, DateTime local, bool present)
    {
        if (!present) return;
        var jour = Presence.JourTexte(local);
        double absence = r.DerniereVue <= 0 ? 0 : Math.Max(0, (maintenant - r.DerniereVue) / 60_000.0);
        if (jour != r.Jour)
        {
            bool premiereFois = r.Jour == "";
            r.Jour = jour;
            r.Dits = 0;
            r.Soir = false;
            r.PresenceJourMin = 0;
            r.DebutSeance = maintenant;
            r.Attente = premiereFois ? "" : "premier";
            r.AttenteDepuis = maintenant;
            r.AttenteAbsence = (int)Math.Min(absence, int.MaxValue);
        }
        else if (absence >= Pause)
        {
            r.DebutSeance = maintenant;
            if (r.Attente is "" or "soir")
            {
                r.Attente = "retour";
                r.AttenteDepuis = maintenant;
                r.AttenteAbsence = (int)absence;
            }
        }
        else r.PresenceJourMin += Math.Min(absence, 2);
        if (r.Attente == "" && !r.Soir && (local.Hour >= 18 || local.Hour < 4) && r.PresenceJourMin >= SoirApres)
        {
            r.Attente = "soir";
            r.AttenteDepuis = maintenant;
            r.AttenteAbsence = 0;
        }
        r.DerniereVue = maintenant;
    }

    // Le moment qui peut partir maintenant, ou null. calme : personne ne tape, rien de caché, aucune IA n'attend,
    // pas de campagne ni de jeu en cours. Un moment trop vieux est abandonné (pas de relance).
    public static Presence.Moment? Pret(Cadence r, long maintenant, string parle, bool calme)
    {
        if (r.Attente == "") return null;
        // La dernière place du jour est gardée pour le soir : un seul retour, entre le bonjour et la fin de journée.
        int reserve = r.Attente == "retour" && !r.Soir ? 1 : 0;
        if (r.Dits >= Plafond(parle) - reserve)
        {
            r.Attente = "";
            return null;
        }
        if (r.Attente != "soir" && maintenant - r.AttenteDepuis > Expire * 60_000)
        {
            r.Attente = "";
            return null;
        }
        if (r.Attente != "premier" && r.DernierMot > 0 && maintenant - r.DernierMot < Ecart * 60_000)
        {
            if (r.Attente == "retour") r.Attente = "";
            return null;
        }
        if (!calme) return null;
        return r.Attente switch { "premier" => Presence.Moment.Premier, "retour" => Presence.Moment.Retour, _ => Presence.Moment.Soir };
    }

    public static void Noter(Cadence r, long maintenant, Presence.Moment m)
    {
        r.Dits++;
        r.DernierMot = maintenant;
        if (m == Presence.Moment.Soir) r.Soir = true;
        r.Attente = "";
    }

    public static double SeanceMin(Cadence r, long maintenant) => r.DebutSeance <= 0 ? 0 : Math.Max(0, (maintenant - r.DebutSeance) / 60_000.0);
}

// Tout ce qu'un appareil garde de la présence (fichier presence.txt sur le PC, préférence « presence » sur le
// téléphone) : son appareil, ce qu'il sait des autres, le journal, la mémoire des mots, le rythme et les réglages.
public sealed class EtatPresence
{
    public Appareil Moi = new();
    public SortedDictionary<string, Appareil> Autres = new(StringComparer.Ordinal);
    // jour → source (appareil, « * » pour les jours figés) → faits.
    public SortedDictionary<string, SortedDictionary<string, FaitsDuJour>> Journal = new(StringComparer.Ordinal);
    public Dictionary<string, int> Dits = new();
    public Cadence Cadence = new();
    public string CapJour = "";
    public int CapMin, CapCar, CapSoi, CapJeu;
    public double SecondesEnsemble;
    // Réglages « Pilou et moi » : parle (normal, peu, jamais), mot du soir (chaque, parfois, jamais), journal, gestes.
    public string Parle = "normal", Frequence = "chaque";
    public bool JournalActif = true, Gestes = true;
    // Le mot du jour (téléphone : accueil, widget, bulle, notification du soir).
    public string MotJour = "", MotTexte = "", MotNotifie = "";
    // Activités du jour (PC) : secondes par activité, pour les faits du journal.
    public string ActJour = "";
    public SortedDictionary<string, double> ActSec = new(StringComparer.Ordinal);

    public const string Fige = "*";

    // ---- Jours et compteurs (plafonnés par jour : passé le plafond, rien ne compte, rien ne se perd)

    public void Marquer(int jour)
    {
        if (jour > 0) Moi.Jours.Add(jour);
    }

    private void Caps(string jour)
    {
        if (CapJour == jour) return;
        CapJour = jour;
        CapMin = CapCar = CapSoi = CapJeu = 0;
    }

    // quoi : minutes, caresses, soins, jeux. Renvoie ce qui a été compté.
    public int Ajouter(string quoi, int n, DateTime local)
    {
        if (n <= 0) return 0;
        Caps(Presence.JourTexte(local));
        Marquer(Presence.Jour(local));
        int pris;
        switch (quoi)
        {
            case "minutes":
                pris = Math.Min(n, Presence.MaxMinutes - CapMin);
                CapMin += Math.Max(0, pris);
                Moi.Minutes += Math.Max(0, pris);
                break;
            case "caresses":
                pris = Math.Min(n, Presence.MaxCaresses - CapCar);
                CapCar += Math.Max(0, pris);
                Moi.Caresses += Math.Max(0, pris);
                break;
            case "soins":
                pris = Math.Min(n, Presence.MaxSoins - CapSoi);
                CapSoi += Math.Max(0, pris);
                Moi.Soins += Math.Max(0, pris);
                break;
            case "jeux":
                pris = Math.Min(n, Presence.MaxJeux - CapJeu);
                CapJeu += Math.Max(0, pris);
                Moi.Jeux += Math.Max(0, pris);
                break;
            default:
                return 0;
        }
        return Math.Max(0, pris);
    }

    // ---- Journal

    public FaitsDuJour Aujourdhui(string jour)
    {
        if (!Journal.TryGetValue(jour, out var s)) Journal[jour] = s = new SortedDictionary<string, FaitsDuJour>(StringComparer.Ordinal);
        if (!s.TryGetValue(Moi.Id, out var f)) s[Moi.Id] = f = new FaitsDuJour();
        return f;
    }

    public FaitsDuJour FaitsDu(string jour)
    {
        var r = new FaitsDuJour();
        if (Journal.TryGetValue(jour, out var s))
            foreach (var f in s.Values) r = FaitsDuJour.Fusion(r, f);
        return r;
    }

    // Jours fermés (plus de JoursOuverts) : figés en une seule source ; au plus JoursGardes jours.
    public void Compacter(int aujourdhui)
    {
        foreach (var jour in Journal.Keys.ToList())
        {
            int j = Presence.JourDe(jour);
            if (j == int.MinValue)
            {
                Journal.Remove(jour);
                continue;
            }
            var s = Journal[jour];
            if (aujourdhui - j > Presence.JoursOuverts && (s.Count > 1 || !s.ContainsKey(Fige)))
            {
                var f = FaitsDu(jour);
                Journal[jour] = new SortedDictionary<string, FaitsDuJour>(StringComparer.Ordinal) { [Fige] = f };
            }
        }
        while (Journal.Count > Presence.JoursGardes) Journal.Remove(Journal.Keys.First());
    }

    // Un message d'un autre appareil du groupe : ses compteurs et ses faits récents (jamais les nôtres).
    public bool Recevoir(Appareil a, int aujourdhui)
    {
        if (a.Id == "" || a.Id == Moi.Id || a.Id == Fige) return false;
        bool change = false;
        var sans = Appareil.Lire(a.Texte(false))!;
        if (Autres.TryGetValue(a.Id, out var avant)) change |= avant.Absorber(sans);
        else if (Autres.Count < 32)
        {
            Autres[a.Id] = sans;
            change = true;
        }
        foreach (var (jour, f) in a.Recents)
        {
            int j = Presence.JourDe(jour);
            if (j == int.MinValue || aujourdhui - j > Presence.JoursOuverts || j > aujourdhui + 1) continue;
            if (!Journal.TryGetValue(jour, out var s)) Journal[jour] = s = new SortedDictionary<string, FaitsDuJour>(StringComparer.Ordinal);
            var n = s.TryGetValue(a.Id, out var x) ? FaitsDuJour.Fusion(x, f) : f.Copie();
            if (x is null || x.Texte() != n.Texte())
            {
                s[a.Id] = n;
                change = true;
            }
        }
        return change;
    }

    // Ce que l'appareil publie : ses compteurs, et ses faits des derniers jours.
    public string Message(int aujourdhui)
    {
        var m = Appareil.Lire(Moi.Texte(false)) ?? new Appareil { Id = Moi.Id };
        foreach (var (jour, s) in Journal)
        {
            int j = Presence.JourDe(jour);
            if (aujourdhui - j >= Presence.JoursDansMessage || j > aujourdhui) continue;
            if (s.TryGetValue(Moi.Id, out var f) && !f.Vide) m.Recents[jour] = f;
        }
        return m.Message();
    }

    public Presence.Totaux Totaux() => Presence.Calculer(Moi, Autres.Values);

    public List<Presence.Entree> Entrees(IReadOnlyList<Presence.Ligne> gabarits)
    {
        var l = new List<Presence.Entree>();
        foreach (var jour in Journal.Keys.Reverse())
            if (Presence.Ecrire(jour, FaitsDu(jour), gabarits) is { } e) l.Add(e);
        return l;
    }

    // Le prénom est-il connu ici (dernier choix du groupe) ?
    public string Prenom => Totaux().Prenom;

    public void ChoisirPrenom(string? prenom, long maintenant)
    {
        Moi.Prenom = Presence.NettoyerPrenom(prenom);
        Moi.PrenomT = Math.Max(maintenant, Math.Max(Moi.PrenomT, Autres.Values.Select(a => a.PrenomT).DefaultIfEmpty(-1).Max()) + 1);
        Moi.PrenomDemande = true;
    }

    // ---- Fichier (même format que le message, par sections)

    private static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

    public string Texte()
    {
        var b = new StringBuilder("pilou-presence-etat 1\n[moi]\n");
        b.Append(Moi.Texte(false));
        foreach (var a in Autres.Values)
        {
            b.Append("[autre]\n");
            b.Append(a.Texte(false));
        }
        b.Append("[journal]\n");
        foreach (var (jour, s) in Journal)
            foreach (var (src, f) in s)
                if (f.Texte() is { Length: > 0 } t) b.Append(jour).Append(' ').Append(src).Append(' ').Append(t).Append('\n');
        b.Append("[dits]\n");
        foreach (var (id, j) in Dits.OrderBy(kv => kv.Key, StringComparer.Ordinal)) b.Append(id).Append(' ').Append(j.ToString(Ci)).Append('\n');
        b.Append("[divers]\n");
        b.Append("parle ").Append(Parle).Append('\n');
        b.Append("frequence ").Append(Frequence).Append('\n');
        b.Append("journal ").Append(JournalActif ? "1" : "0").Append('\n');
        b.Append("gestes ").Append(Gestes ? "1" : "0").Append('\n');
        b.Append("cap ").Append(CapJour == "" ? "-" : CapJour).Append(' ').Append(CapMin.ToString(Ci)).Append(' ').Append(CapCar.ToString(Ci))
            .Append(' ').Append(CapSoi.ToString(Ci)).Append(' ').Append(CapJeu.ToString(Ci)).Append('\n');
        b.Append("ensemble ").Append(((long)SecondesEnsemble).ToString(Ci)).Append('\n');
        var r = Cadence;
        b.Append("rythme ").Append(r.Jour == "" ? "-" : r.Jour).Append(' ').Append(r.Dits.ToString(Ci)).Append(' ').Append(r.DernierMot.ToString(Ci))
            .Append(' ').Append(r.DerniereVue.ToString(Ci)).Append(' ').Append(r.DebutSeance.ToString(Ci)).Append(' ')
            .Append(((long)(r.PresenceJourMin * 60)).ToString(Ci)).Append(' ').Append(r.Soir ? "1" : "0").Append(' ')
            .Append(r.Attente == "" ? "-" : r.Attente).Append(' ').Append(r.AttenteDepuis.ToString(Ci)).Append(' ').Append(r.AttenteAbsence.ToString(Ci)).Append('\n');
        if (ActJour != "")
            b.Append("act ").Append(ActJour).Append(' ')
                .Append(string.Join(",", ActSec.Select(kv => kv.Key + ":" + ((long)kv.Value).ToString(Ci)))).Append('\n');
        if (MotJour != "") b.Append("mot ").Append(MotJour).Append(' ').Append(MotNotifie == "" ? "-" : MotNotifie).Append(' ').Append(MotTexte).Append('\n');
        return b.ToString();
    }

    private static long L(string s) => long.TryParse(s, NumberStyles.Integer, Ci, out var n) ? n : 0;
    private static int I(string s) => int.TryParse(s, NumberStyles.Integer, Ci, out var n) ? n : 0;
    private static string Tiret(string s) => s == "-" ? "" : s;

    public static EtatPresence Lire(string? texte)
    {
        var e = new EtatPresence();
        if (string.IsNullOrEmpty(texte)) return e;
        var lignes = texte.Replace("\r\n", "\n").Split('\n');
        if (lignes.Length == 0 || lignes[0] != "pilou-presence-etat 1") return e;
        string section = "";
        Appareil? autre = null;
        void Ranger()
        {
            if (autre is not null && autre.Id != "" && autre.Id != e.Moi.Id && e.Autres.Count < 32) e.Autres[autre.Id] = autre;
            autre = null;
        }
        foreach (var l in lignes.Skip(1))
        {
            if (l.Length == 0) continue;
            if (l[0] == '[')
            {
                Ranger();
                section = l;
                if (section == "[autre]") autre = new Appareil();
                continue;
            }
            try
            {
                switch (section)
                {
                    case "[moi]": e.Moi.LireLigne(l); break;
                    case "[autre]": autre?.LireLigne(l); break;
                    case "[journal]":
                    {
                        var p = l.Split(' ', 3);
                        if (p.Length == 3 && Presence.JourDe(p[0]) != int.MinValue)
                        {
                            if (!e.Journal.TryGetValue(p[0], out var s)) e.Journal[p[0]] = s = new SortedDictionary<string, FaitsDuJour>(StringComparer.Ordinal);
                            s[p[1]] = FaitsDuJour.Lire(p[2]);
                        }
                        break;
                    }
                    case "[dits]":
                    {
                        var p = l.Split(' ');
                        if (p.Length == 2 && p[0].Length == 8) e.Dits[p[0]] = I(p[1]);
                        break;
                    }
                    case "[divers]":
                    {
                        var p = l.Split(' ');
                        switch (p[0])
                        {
                            case "parle": e.Parle = p.Length > 1 && p[1] is "peu" or "jamais" ? p[1] : "normal"; break;
                            case "frequence": e.Frequence = p.Length > 1 && p[1] is "parfois" or "jamais" ? p[1] : "chaque"; break;
                            case "journal": e.JournalActif = p.Length < 2 || p[1] != "0"; break;
                            case "gestes": e.Gestes = p.Length < 2 || p[1] != "0"; break;
                            case "cap" when p.Length == 6:
                                e.CapJour = Tiret(p[1]);
                                (e.CapMin, e.CapCar, e.CapSoi, e.CapJeu) = (I(p[2]), I(p[3]), I(p[4]), I(p[5]));
                                break;
                            case "ensemble" when p.Length == 2: e.SecondesEnsemble = L(p[1]); break;
                            case "rythme" when p.Length == 11:
                                e.Cadence = new Cadence
                                {
                                    Jour = Tiret(p[1]), Dits = I(p[2]), DernierMot = L(p[3]), DerniereVue = L(p[4]), DebutSeance = L(p[5]),
                                    PresenceJourMin = L(p[6]) / 60.0, Soir = p[7] == "1", Attente = Tiret(p[8]), AttenteDepuis = L(p[9]),
                                    AttenteAbsence = I(p[10]),
                                };
                                break;
                            case "act" when p.Length >= 2:
                                e.ActJour = p[1];
                                if (p.Length == 3)
                                    foreach (var x in p[2].Split(','))
                                    {
                                        int k = x.IndexOf(':');
                                        if (k > 0) e.ActSec[x[..k]] = L(x[(k + 1)..]);
                                    }
                                break;
                            case "mot" when p.Length >= 3:
                            {
                                var q = l.Split(' ', 4);
                                e.MotJour = q[1];
                                e.MotNotifie = Tiret(q[2]);
                                e.MotTexte = q.Length == 4 ? q[3] : "";
                                break;
                            }
                        }
                        break;
                    }
                }
            }
            catch (Exception x) when (x is FormatException or ArgumentException or OverflowException)
            {
                // ligne abîmée : ignorée
            }
        }
        Ranger();
        return e;
    }
}
