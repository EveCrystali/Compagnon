using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace PilouVisualStudio
{
    // Une ligne de la Liste d'erreurs, réduite à ce qui compte ici.
    public struct LigneErreur
    {
        public LigneErreur(string document, Gravite gravite, string texte, int ligne)
        {
            Document = document ?? "";
            Gravite = gravite;
            Texte = texte ?? "";
            Ligne = ligne;
        }

        public string Document { get; }
        public Gravite Gravite { get; }
        public string Texte { get; }
        public int Ligne { get; }
    }

    public enum Gravite { Erreur, Avertissement, Message }

    // Ce qu'on envoie à Pilou (POST /diagnostics). Sans rien de Visual Studio : testé avec Pilou (tests xunit).
    public sealed class Rapport
    {
        public const int PortParDefaut = 47821;

        public string Fichier { get; private set; } = "";
        public int Erreurs { get; private set; }
        public int Avertissements { get; private set; }
        public string Message { get; private set; } = "";
        public bool Ferme { get; private set; }

        public static Rapport Fermeture() => new Rapport { Ferme = true };

        // Lignes de la Liste d'erreurs qui portent sur le document actif (chemin complet, casse ignorée).
        public static Rapport Compter(string documentActif, IEnumerable<LigneErreur> lignes, bool avecMessage)
        {
            var miennes = lignes.Where(l => l.Document != "" && string.Equals(Normaliser(l.Document), Normaliser(documentActif),
                StringComparison.OrdinalIgnoreCase)).ToList();
            var erreurs = miennes.Where(l => l.Gravite == Gravite.Erreur).OrderBy(l => l.Ligne).ToList();
            return new Rapport
            {
                Fichier = NomFichier(documentActif),
                Erreurs = erreurs.Count,
                Avertissements = miennes.Count(l => l.Gravite == Gravite.Avertissement),
                Message = avecMessage && erreurs.Count > 0 ? Nettoyer(erreurs[0].Texte, 160) : "",
            };
        }

        private static string Normaliser(string chemin)
        {
            try
            {
                return Path.GetFullPath(chemin.Trim());
            }
            catch (Exception)
            {
                return chemin.Trim();
            }
        }

        // Nom seul, jamais le chemin.
        public static string NomFichier(string chemin)
        {
            var s = (chemin ?? "").Trim();
            int i = s.LastIndexOfAny(new[] { '/', '\\' });
            if (i >= 0) s = s.Substring(i + 1);
            return s.Length <= 80 ? s : s.Substring(0, 80);
        }

        private static readonly Regex Chemins = new Regex(
            @"(file:///?)?([A-Za-z]:[\\/]|\\\\|/)([^\s""'<>|:*?]+[\\/])+(?<nom>[^\s""'<>|:*?\\/]+)", RegexOptions.Compiled);

        // Chemins absolus réduits au nom, une ligne, borné. Pilou refait le même nettoyage à la réception.
        public static string Nettoyer(string texte, int max)
        {
            var s = new string((texte ?? "").Select(c => char.IsControl(c) ? ' ' : c).ToArray());
            s = Chemins.Replace(s, m => m.Groups["nom"].Value);
            s = Regex.Replace(s, @"\s+", " ").Trim();
            return s.Length <= max ? s : s.Substring(0, max - 1).TrimEnd() + "…";
        }

        public bool Meme(Rapport autre) =>
            autre != null && autre.Fichier == Fichier && autre.Erreurs == Erreurs && autre.Avertissements == Avertissements
            && autre.Message == Message && autre.Ferme == Ferme;

        public string Json()
        {
            var b = new StringBuilder("{\"source\":\"vs\"");
            if (Ferme) return b.Append(",\"fichier\":\"\",\"ferme\":true}").ToString();
            b.Append(",\"fichier\":").Append(Chaine(Fichier))
                .Append(",\"erreurs\":").Append(Erreurs)
                .Append(",\"avertissements\":").Append(Avertissements);
            if (Message != "") b.Append(",\"message\":").Append(Chaine(Message));
            return b.Append('}').ToString();
        }

        private static string Chaine(string s)
        {
            var b = new StringBuilder("\"");
            foreach (var c in s)
            {
                if (c == '"' || c == '\\') b.Append('\\').Append(c);
                else if (c < 0x20) b.Append("\\u").Append(((int)c).ToString("x4"));
                else b.Append(c);
            }
            return b.Append('"').ToString();
        }

        // %USERPROFILE%\.claude\compagnon\reglages.json : Pilou y range le jeton (Connecteurs.JetonApi) et le port.
        public static string CheminReglages() =>
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".claude", "compagnon", "reglages.json");

        // Jeton et port : ceux des options s'ils sont donnés, sinon ceux de reglages.json. Jeton vide : Pilou absent.
        public static void LireAcces(string reglagesJson, string jetonOption, int portOption, out string jeton, out int port)
        {
            jeton = (jetonOption ?? "").Trim();
            port = portOption > 0 ? portOption : 0;
            var json = reglagesJson ?? "";
            // Le bloc « Connecteurs » (JetonApi et PortApi n'existent que là).
            if (jeton == "")
            {
                var m = Regex.Match(json, "\"JetonApi\"\\s*:\\s*\"([^\"]*)\"");
                if (m.Success) jeton = m.Groups[1].Value;
            }
            if (port == 0)
            {
                var m = Regex.Match(json, "\"PortApi\"\\s*:\\s*(\\d{1,5})");
                if (m.Success && int.TryParse(m.Groups[1].Value, out var p) && p > 0 && p < 65536) port = p;
            }
            if (port == 0) port = PortParDefaut;
        }
    }
}
