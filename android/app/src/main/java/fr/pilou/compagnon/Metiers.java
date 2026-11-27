package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * Métiers et succès du PC (copie de apps/PilouBureau/Metiers.cs, vérifiée par MetiersTest contre
 * src/test/resources/metiers-succes.txt, que le test C# tire du même fichier). Le PC envoie les heures de chaque
 * métier en dixièmes d'heure (« heures ») et l'avancement des succès en dixièmes (« avance ») ; un ancien PC
 * n'envoie que les niveaux (« metiers ») et les succès obtenus (« succes »).
 */
final class Metiers {
    static final int[] PALIERS = {1, 5, 15, 40, 100, 250};
    /** Métiers de travail (code, tableur, visio, écriture, mail) : six fois plus d'heures. */
    static final int[] PALIERS_TRAVAIL = {6, 30, 90, 240, 600, 1500};
    static final String[] GRADES = {"Novice", "Apprenti", "Compagnon", "Confirmé", "Expert", "Maître", "Légende"};
    /** Signes de forme (pas seulement de couleur) : ⚒ travail, ♪ loisir. */
    static final String TRAVAIL = "⚒", LOISIR = "♪";

    static final class Metier {
        final String id, nom;
        final String[] activites;
        final boolean travail;

        Metier(String id, String nom, boolean travail, String... activites) {
            this.id = id;
            this.nom = nom;
            this.travail = travail;
            this.activites = activites;
        }

        int[] paliers() {
            return travail ? PALIERS_TRAVAIL : PALIERS;
        }

        String signe() {
            return travail ? TRAVAIL : LOISIR;
        }
    }

    static final class Succes {
        final String id, nom, description, unite;
        final double but;
        final int xp;

        Succes(String id, String nom, String description, double but, int xp, String unite) {
            this.id = id;
            this.nom = nom;
            this.description = description;
            this.but = but;
            this.xp = xp;
            this.unite = unite;
        }
    }

    static final List<Metier> TOUS = Collections.unmodifiableList(Arrays.asList(
            new Metier("codeur", "Codeur", true, "code"),
            new Metier("tableur", "As du tableur", true, "tableur"),
            new Metier("joueur", "Joueur", false, "jeu", "jeu-mmo"),
            new Metier("musicien", "Mélomane", false, "musique"),
            new Metier("cinephile", "Cinéphile", false, "video"),
            new Metier("lecteur", "Lecteur", false, "lecture"),
            new Metier("artiste", "Artiste", false, "dessin"),
            new Metier("orateur", "Orateur", true, "visio", "diaporama"),
            new Metier("ecrivain", "Écrivain", true, "texte"),
            new Metier("facteur", "Facteur", true, "mail")));

    static final List<Succes> SUCCES = Collections.unmodifiableList(Arrays.asList(
            new Succes("marathon", "Marathon", "4 h de code d'affilée", 4, 25, "h"),
            new Succes("noctambule", "Noctambule", "actif entre 1 h et 4 h du matin", 1, 25, ""),
            new Succes("leve-tot", "Lève-tôt", "actif avant 6 h du matin", 1, 25, ""),
            new Succes("visio-man", "Visio-man", "10 réunions en 7 jours", 10, 25, "n"),
            new Succes("orateur", "Orateur", "5 présentations en plein écran", 5, 25, "n"),
            new Succes("melomane", "Mélomane", "10 h de musique", 10, 25, "h"),
            new Succes("tableur-fou", "Tableur fou", "10 h de tableur", 10, 25, "h"),
            new Succes("codeur-confirme", "Codeur confirmé", "50 h de code", 50, 50, "h"),
            new Succes("gamer", "Gamer", "20 h de jeu", 20, 25, "h"),
            new Succes("aventurier", "Aventurier", "10 h de jeu de rôle en ligne", 10, 25, "h"),
            new Succes("cinephile", "Cinéphile", "10 h de vidéo", 10, 25, "h"),
            new Succes("rat-de-bibliotheque", "Rat de bibliothèque", "10 h de lecture", 10, 25, "h"),
            new Succes("artiste", "Artiste", "10 h de dessin ou de création", 10, 25, "h"),
            new Succes("plume", "Plume", "10 h d'écriture", 10, 25, "h"),
            new Succes("facteur", "Facteur", "5 h de mail", 5, 25, "h"),
            new Succes("explorateur", "Explorateur", "8 activités différentes", 8, 25, "n"),
            new Succes("dactylo", "Dactylo", "taper avec Pilou au clavier 25 fois", 25, 25, "n"),
            new Succes("photographe", "Photographe", "10 captures d'écran photographiées par Pilou", 10, 25, "n"),
            new Succes("couteau-suisse", "Couteau suisse", "4 métiers au rang Compagnon", 4, 50, "n"),
            new Succes("pare-feu", "Pare-feu", "vaincre un Bug de prod à Défense du bureau", 1, 25, ""),
            new Succes("rempart", "Rempart", "atteindre la vague 10 à Défense du bureau", 10, 40, "vague"),
            new Succes("gardien", "Gardien du bureau", "10 000 points à Défense du bureau", 10000, 40, "points")));

    private Metiers() {
    }

    static Metier metier(String id) {
        for (Metier m : TOUS) if (m.id.equals(id)) return m;
        return null;
    }

    static Succes succes(String id) {
        for (Succes s : SUCCES) if (s.id.equals(id)) return s;
        return null;
    }

    /** Niveau (0 Novice … 6 Légende) d'après les dixièmes d'heure : même calcul que le PC (paliers en heures entières). */
    static int niveau(Metier m, int dixiemes) {
        int n = 0;
        for (int p : m.paliers()) if (dixiemes >= p * 10) n++;
        return n;
    }

    /** « 5,7 h » (dixièmes) ; « 6 h » quand c'est rond. */
    static String heures(int dixiemes) {
        int d = Math.max(0, dixiemes);
        return (d % 10 == 0 ? String.valueOf(d / 10) : (d / 10) + "," + (d % 10)) + " h";
    }

    /** « 5,7 h / 6 h » vers le palier suivant ; au dernier palier, le total arrondi (« 1523 h »), comme le PC. */
    static String progres(Metier m, int dixiemes) {
        int n = niveau(m, dixiemes);
        int[] p = m.paliers();
        return n >= p.length ? Math.round(dixiemes / 10.0) + " h" : heures(dixiemes) + " / " + p[n] + " h";
    }

    /** Part de la barre : les heures sur le palier suivant (pleine au dernier). */
    static float part(Metier m, int dixiemes) {
        int n = niveau(m, dixiemes);
        int[] p = m.paliers();
        return n >= p.length ? 1f : Math.min(1f, dixiemes / (p[n] * 10f));
    }

    /** Avancement d'un succès (dixièmes) : « 2,5 h / 4 h », « 3 / 10 », « vague 7 / 10 », « 8765 / 10000 points ». */
    static String progres(Succes s, int dixiemes) {
        int a = (int) Math.min(Math.max(0, dixiemes), Math.round(s.but * 10));
        String but = entier(s.but);
        switch (s.unite) {
            case "": return "";
            case "n": return Math.round(a / 10.0) + " / " + but;
            case "vague": return "vague " + Math.round(a / 10.0) + " / " + but;
            case "points": return Math.round(a / 10.0) + " / " + but + " points";
            default: return heures(a) + " / " + but + " h";
        }
    }

    private static String entier(double v) {
        return v == Math.rint(v) ? String.valueOf((long) v) : String.format(Locale.ROOT, "%.2f", v).replaceAll("0+$", "");
    }

    /** Le catalogue en texte, ligne à ligne, comme MetiersTelephoneTests.Catalogue (C#). */
    static String catalogue() {
        StringBuilder b = new StringBuilder();
        b.append("paliers ").append(joindre(PALIERS)).append('\n');
        b.append("paliersTravail ").append(joindre(PALIERS_TRAVAIL)).append('\n');
        b.append("grades ").append(String.join(",", GRADES)).append('\n');
        for (Metier m : TOUS)
            b.append("metier ").append(m.id).append('|').append(m.nom).append('|').append(String.join(",", m.activites)).append('|')
                    .append(m.travail ? "travail" : "loisir").append('\n');
        for (Succes s : SUCCES)
            b.append("succes ").append(s.id).append('|').append(s.nom).append('|').append(s.description).append('|').append(entier(s.but))
                    .append('|').append(s.xp).append('|').append(s.unite).append('\n');
        return b.toString();
    }

    private static String joindre(int[] v) {
        StringBuilder b = new StringBuilder();
        for (int x : v) b.append(b.length() > 0 ? "," : "").append(x);
        return b.toString();
    }

    // ---- Ce qu'affiche le téléphone

    /** Un métier tel qu'on le montre : niveau, dixièmes d'heure (-1 : un ancien PC ne les envoie pas). */
    static final class Ligne {
        final Metier metier;
        final int niveau, dixiemes;

        Ligne(Metier metier, int niveau, int dixiemes) {
            this.metier = metier;
            this.niveau = niveau;
            this.dixiemes = dixiemes;
        }

        boolean commence() {
            return dixiemes > 0 || niveau > 0;
        }

        String grade() {
            return GRADES[Math.max(0, Math.min(GRADES.length - 1, niveau))];
        }

        /** « 5,7 h / 6 h », « au moins 15 h » (ancien PC), « pas encore commencé ». */
        String texte() {
            if (dixiemes > 0) return progres(metier, dixiemes);
            if (dixiemes < 0 && niveau > 0) return "au moins " + metier.paliers()[Math.min(niveau, 6) - 1] + " h";
            return "pas encore commencé · " + metier.paliers()[0] + " h pour Apprenti";
        }

        float part() {
            return dixiemes > 0 ? Metiers.part(metier, dixiemes) : 0f;
        }
    }

    /** Les métiers, les plus pratiqués en tête (par heures, ou par niveau avec un ancien PC), ceux à 0 h en dernier. */
    static List<Ligne> lignes(Etat e) {
        List<Ligne> l = new ArrayList<>();
        for (Metier m : TOUS) {
            Integer h = e.heures.get(m.id), n = e.metiers.get(m.id);
            int dixiemes = e.heuresConnues ? (h == null ? 0 : Math.max(0, h)) : -1;
            int niveau = dixiemes >= 0 ? niveau(m, dixiemes) : n == null ? 0 : Math.max(0, Math.min(6, n));
            l.add(new Ligne(m, niveau, dixiemes));
        }
        // Tri stable : à égalité, l'ordre du catalogue.
        l.sort((a, b) -> a.dixiemes != b.dixiemes ? Integer.compare(b.dixiemes, a.dixiemes) : Integer.compare(b.niveau, a.niveau));
        return l;
    }

    /** Les succès : obtenus d'abord (ordre du catalogue), puis les autres. */
    static List<Succes> succesTries(Etat e) {
        List<Succes> l = new ArrayList<>(), autres = new ArrayList<>();
        for (Succes s : SUCCES) (e.succes.contains(s.id) ? l : autres).add(s);
        l.addAll(autres);
        return l;
    }

    static int obtenus(Etat e) {
        int n = 0;
        for (Succes s : SUCCES) if (e.succes.contains(s.id)) n++;
        return n;
    }

    /** Il y a quelque chose à montrer (le PC a envoyé des métiers ou des succès). */
    static boolean connus(Etat e) {
        return e.heuresConnues || !e.metiers.isEmpty() || !e.succes.isEmpty();
    }

    /** « Codeur · Compagnon  ·  Succès 3/22 » : la petite carte de l'accueil. */
    static String resume(Etat e) {
        List<Ligne> l = lignes(e);
        Ligne t = l.isEmpty() || !l.get(0).commence() ? null : l.get(0);
        return (t == null ? "Aucun métier commencé" : t.metier.signe() + " " + t.metier.nom + " · " + t.grade())
                + "  ·  Succès " + obtenus(e) + "/" + SUCCES.size();
    }
}
