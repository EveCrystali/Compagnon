namespace PilouBureau;

public enum Ton { Attente, Travail, Fini, Neutre }

// Une ligne de la bulle : un signe de forme, la session, ce qu'elle fait.
public sealed record LigneStatut(string Signe, string Libelle, string Texte, Ton Ton, bool Nouveau = false);

// Résumé d'une ligne pour la bulle compacte : « ◐ 2 en cours · ✓ 3 finies ».
public sealed record Resume(int Attente, int Travail, int Fini, int Calme);

// Ce que dit la bulle, session par session : d'abord ce qui t'attend, puis ce qui
// travaille, puis ce qui vient de finir. Chaque état a son signe (❗ ? ◐ ✓ ■ ✕), pas seulement une couleur.
public static class Statut
{
    public const double FiniVisible = 2 * 3600_000;
    public const int MaxLignes = 6;
    private static readonly string[] Roue = { "◐", "◓", "◑", "◒" };

    // Nom affiché d'une source : Claude, Codex, Cursor…
    public static string Etiquette(string source) => source switch
    {
        "claude" => "Claude",
        "codex" => "Codex",
        "gemini" => "Gemini",
        "copilot" => "Copilot",
        "" => "?",
        _ => char.ToUpperInvariant(source[0]) + source[1..],
    };

    // Libellé d'une session dans la bulle : les autres sources que Claude portent leur nom devant.
    public static string Nom(EtatSession e)
    {
        var nom = e.Libelle == "" ? $"session {e.Session}" : e.Libelle;
        return e.Claude ? nom : $"{Etiquette(e.Source)} · {nom}";
    }

    public static string Duree(double ms)
    {
        var s = Math.Max(0, (int)(ms / 1000));
        if (s < 60) return $"{s} s";
        if (s < 3600) return $"{s / 60} min";
        return $"{s / 3600} h {s % 3600 / 60:00}";
    }

    public static Resume Resumer(IEnumerable<EtatSession> sessions, double maintenant)
    {
        int a = 0, w = 0, f = 0, c = 0;
        foreach (var e in sessions)
        {
            if (e.Attente != "") a++;
            else if (e.EnTour) w++;
            else if (e.FinTour > 0 && maintenant - e.FinTour < FiniVisible) f++;
            else c++;
        }
        return new Resume(a, w, f, c);
    }

    public static string TexteResume(Resume r)
    {
        var morceaux = new List<string>();
        if (r.Travail > 0) morceaux.Add($"◐ {r.Travail} en cours");
        if (r.Fini > 0) morceaux.Add($"✓ {r.Fini} fini{(r.Fini > 1 ? "es" : "e")}");
        if (morceaux.Count == 0 && r.Calme > 0) morceaux.Add($"{r.Calme} session{(r.Calme > 1 ? "s" : "")} au calme");
        if (morceaux.Count == 0 && r.Attente == 0) morceaux.Add("aucune session ouverte");
        return string.Join("  ·  ", morceaux);
    }

    public static (List<LigneStatut> Lignes, int AuRepos) Lignes(IEnumerable<EtatSession> sessions, double maintenant, int image = 0)
    {
        var attente = new List<(double, LigneStatut)>();
        var travail = new List<(double, LigneStatut)>();
        var fini = new List<(double, LigneStatut)>();
        int repos = 0;
        foreach (var e in sessions)
        {
            var nom = Nom(e);
            if (e.Attente == "permission")
                attente.Add((e.DebutOutil, new("❗", nom, "attend ton autorisation", Ton.Attente)));
            else if (e.Attente == "question")
                attente.Add((e.DebutOutil, new("?", nom, "te pose une question", Ton.Attente)));
            else if (e.EnTour)
            {
                var signe = Roue[image % Roue.Length];
                // Une durée sans heure de début connue (session rechargée en plein tour) ne veut rien dire.
                static bool Connue(double debut, double now) => debut > 0 && now - debut < 24 * 3600_000;
                var texte = e.Outil != "" && Connue(e.DebutOutil, maintenant)
                    ? $"{e.Outil} · {Duree(maintenant - e.DebutOutil)}"
                    : e.Outil != "" ? e.Outil
                    : Connue(e.DebutTour, maintenant) ? $"réfléchit · {Duree(maintenant - e.DebutTour)}" : "réfléchit";
                travail.Add((e.DebutTour, new(signe, nom, texte, Ton.Travail)));
            }
            else if (e.FinTour > 0 && maintenant - e.FinTour < FiniVisible)
            {
                var il = Duree(maintenant - e.FinTour);
                var ligne = e.FinRaison switch
                {
                    "interrompu" => new LigneStatut("■", nom, $"interrompu · il y a {il}", Ton.Neutre),
                    "erreur" => new LigneStatut("✕", nom, $"erreur · il y a {il}", Ton.Attente),
                    _ => new LigneStatut("✓", nom, maintenant - e.FinTour < 60_000 ? "vient de finir" : $"fini · il y a {il}", Ton.Fini,
                        maintenant - e.FinTour < 60_000),
                };
                fini.Add((-e.FinTour, ligne));
            }
            else repos++;
        }
        var tout = attente.OrderBy(x => x.Item1).Select(x => x.Item2)
            .Concat(travail.OrderBy(x => x.Item1).Select(x => x.Item2))
            .Concat(fini.OrderBy(x => x.Item1).Select(x => x.Item2))
            .ToList();
        if (tout.Count > MaxLignes)
        {
            repos += tout.Count - MaxLignes;
            tout = tout.Take(MaxLignes).ToList();
        }
        return (tout, repos);
    }
}
