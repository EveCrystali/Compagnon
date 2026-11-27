package fr.pilou.compagnon;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.time.format.ResolverStyle;
import java.time.temporal.IsoFields;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.regex.Pattern;

/**
 * La présence de Pilou au quotidien (docs/PRESENCE.md) : copie exacte de apps/PilouBureau/Presence.cs et EtatPresence.cs
 * (mêmes tirages, mêmes textes, même format). Aucune dépendance Android : testable partout. Les vecteurs
 * src/test/resources/presence-vecteurs.txt, écrits par le PC, sont rejoués par PresenceTest.
 */
public final class Presence {
    public static final int VERSION = 1, LONGUEUR_MAX = 90, PRENOM_MAX = 16, TAILLE_MESSAGE = 2750;
    public static final int JOURS_DANS_MESSAGE = 7, JOURS_OUVERTS = 14, JOURS_GARDES = 400, DITS_GARDES = 900;

    private Presence() {
    }

    // ---- Hachage (FNV-1a 64 sur les caractères UTF-16, comme Presence.cs)

    public static long hash(String s) {
        long h = 0xcbf29ce484222325L;
        for (int i = 0; i < s.length(); i++) {
            h ^= s.charAt(i);
            h *= 0x100000001b3L;
        }
        return h;
    }

    public static int tirer(String graine, int n) {
        return n <= 0 ? 0 : (int) Long.remainderUnsigned(hash(graine), n);
    }

    public static String id(String famille, String texte) {
        return String.format(Locale.ROOT, "%08x", hash(famille + "|" + texte) & 0xffffffffL);
    }

    static String[] couper(String s, String sep) {
        return s.split(Pattern.quote(sep), -1);
    }

    static String[] couper(String s, String sep, int max) {
        return s.split(Pattern.quote(sep), max);
    }

    // ---- Banque de textes

    public static final class Ligne {
        public final String famille, stades, variante, texte, id;
        public final int palier;
        public final List<String> trous;

        Ligne(String famille, int palier, String stades, String variante, String texte) {
            this.famille = famille;
            this.palier = palier;
            this.stades = stades;
            this.variante = variante;
            this.texte = texte;
            this.id = Presence.id(famille, texte);
            this.trous = Presence.trous(texte);
        }
    }

    public static List<Ligne> lire(String texte) {
        List<Ligne> l = new ArrayList<>();
        for (String brut : couper(texte.replace("\r\n", "\n"), "\n")) {
            String ligne = rogner(brut);
            if (ligne.isEmpty() || ligne.charAt(0) == '#') continue;
            String[] p = couper(ligne, "|");
            if (p.length != 3) continue;
            String famille = rogner(p[0]), t = rogner(p[2]);
            if (famille.isEmpty() || t.isEmpty()) continue;
            int palier = 0;
            String stades = "", variante = "";
            for (String f0 : couper(p[1], ",")) {
                String f = rogner(f0);
                if (f.isEmpty()) continue;
                if (f.equals("calin") || f.equals("espiegle")) variante = f;
                else if (f.charAt(0) == 'c' && f.length() == 2 && f.charAt(1) >= '0' && f.charAt(1) <= '9') palier = f.charAt(1) - '0';
                else if (f.charAt(0) == 's' && f.length() > 1) stades = f.substring(1);
            }
            l.add(new Ligne(famille, palier, stades, variante, t));
        }
        return l;
    }

    public static List<String> trous(String t) {
        List<String> l = new ArrayList<>();
        int i = 0;
        while ((i = t.indexOf('{', i)) >= 0) {
            int j = t.indexOf('}', i);
            if (j < 0) break;
            String nom = t.substring(i + 1, j);
            if (!l.contains(nom)) l.add(nom);
            i = j + 1;
        }
        return l;
    }

    private static volatile List<Ligne> mots, gabarits;

    public static List<Ligne> mots() {
        if (mots == null) mots = lire(ressource("/presence/mots.txt"));
        return mots;
    }

    public static List<Ligne> gabarits() {
        if (gabarits == null) gabarits = lire(ressource("/presence/journal.txt"));
        return gabarits;
    }

    private static String ressource(String chemin) {
        try (InputStream in = Presence.class.getResourceAsStream(chemin)) {
            if (in == null) return "";
            ByteArrayOutputStream b = new ByteArrayOutputStream();
            byte[] tampon = new byte[8192];
            int n;
            while ((n = in.read(tampon)) > 0) b.write(tampon, 0, n);
            return new String(b.toByteArray(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "";
        }
    }

    public static String remplir(String texte, Map<String, String> valeurs) {
        String r = texte;
        for (String t : trous(texte)) {
            String v = valeurs.get(t);
            if (v != null) r = r.replace("{" + t + "}", v);
        }
        return r;
    }

    // ---- Choix

    public static final class Qui {
        public final int palier, stade;
        public final String variante;

        public Qui(int palier, int stade, String variante) {
            this.palier = palier;
            this.stade = stade;
            this.variante = variante;
        }
    }

    public static Ligne choisir(List<Ligne> banque, String famille, Qui qui, Map<String, String> valeurs, Map<String, Integer> dits, String graine) {
        List<Ligne> c = new ArrayList<>();
        for (Ligne l : banque) {
            if (!l.famille.equals(famille) || l.palier > qui.palier) continue;
            if (!l.stades.isEmpty() && l.stades.indexOf((char) ('0' + qui.stade)) < 0) continue;
            if (!l.variante.isEmpty() && !l.variante.equals(qui.variante)) continue;
            boolean ok = true;
            for (String t : l.trous) {
                String v = valeurs.get(t);
                if (v == null || v.isEmpty()) {
                    ok = false;
                    break;
                }
            }
            if (ok) c.add(l);
        }
        if (c.isEmpty()) return null;
        c.sort((a, b) -> a.id.compareTo(b.id));
        List<Ligne> neufs = new ArrayList<>();
        for (Ligne l : c) if (!dits.containsKey(l.id)) neufs.add(l);
        List<Ligne> pool;
        if (!neufs.isEmpty()) pool = neufs;
        else {
            List<Ligne> t = new ArrayList<>(c);
            t.sort((a, b) -> {
                int x = Integer.compare(dits.get(a.id), dits.get(b.id));
                return x != 0 ? x : a.id.compareTo(b.id);
            });
            pool = new ArrayList<>(t.subList(0, (c.size() + 2) / 3));
            pool.sort((a, b) -> a.id.compareTo(b.id));
        }
        return pool.get(tirer(graine, pool.size()));
    }

    public static void retenir(Map<String, Integer> dits, String id, int jour) {
        dits.put(id, jour);
        while (dits.size() > DITS_GARDES) {
            String vieux = null;
            int v = Integer.MAX_VALUE;
            for (Map.Entry<String, Integer> e : dits.entrySet())
                if (vieux == null || e.getValue() < v || (e.getValue() == v && e.getKey().compareTo(vieux) < 0)) {
                    v = e.getValue();
                    vieux = e.getKey();
                }
            dits.remove(vieux);
        }
    }

    // ---- Calendrier

    private static final DateTimeFormatter JOUR = DateTimeFormatter.ofPattern("uuuu-MM-dd", Locale.ROOT).withResolverStyle(ResolverStyle.STRICT);

    public static int jour(LocalDateTime local) {
        return (int) local.toLocalDate().toEpochDay();
    }

    public static String jourTexte(LocalDateTime local) {
        return local.toLocalDate().format(JOUR);
    }

    public static String jourTexte(int jour) {
        return LocalDate.ofEpochDay(jour).format(JOUR);
    }

    public static int jourDe(String texte) {
        if (texte == null || texte.length() != 10) return Integer.MIN_VALUE;
        try {
            return (int) LocalDate.parse(texte, JOUR).toEpochDay();
        } catch (DateTimeParseException e) {
            return Integer.MIN_VALUE;
        }
    }

    static int dow(LocalDateTime d) {
        return d.getDayOfWeek().getValue() % 7; // 0 dimanche … 6 samedi, comme DayOfWeek en C#
    }

    public static String saison(int mois) {
        return mois == 12 || mois <= 2 ? "hiver" : mois <= 5 ? "printemps" : mois <= 8 ? "ete" : "automne";
    }

    public static String fete(int mois, int jour) {
        if (mois == 1 && jour == 1) return "nouvel-an";
        if (mois == 2 && jour == 2) return "chandeleur";
        if (mois == 3 && jour == 20) return "printemps";
        if (mois == 4 && jour == 1) return "poisson";
        if (mois == 6 && jour == 21) return "musique";
        if (mois == 9 && jour == 1) return "rentree";
        if (mois == 9 && jour == 22) return "automne";
        if (mois == 10 && jour == 31) return "citrouille";
        if (mois == 12 && jour == 21) return "hiver";
        if (mois == 12 && (jour == 24 || jour == 25)) return "noel";
        if (mois == 12 && jour == 31) return "reveillon";
        return "";
    }

    public static final String[] METEOS_NOTABLES = {"pluie", "orage", "neige", "brouillard", "vent", "chaleur", "froid", "degage"};
    public static final String[] CURIOSITES = {"code", "tableur", "texte", "mail", "musique", "video", "lecture", "dessin", "jeu"};

    static int indice(String[] t, String v) {
        for (int i = 0; i < t.length; i++) if (t[i].equals(v)) return i;
        return -1;
    }

    public static String meteoFamille(String etat) {
        return "averse".equals(etat) ? "pluie" : indice(METEOS_NOTABLES, etat) >= 0 ? etat : "";
    }

    public static String curiositeDe(String activite) {
        return "jeu-mmo".equals(activite) ? "jeu" : indice(CURIOSITES, activite) >= 0 ? activite : "";
    }

    // ---- Moments et familles

    public enum Moment {Premier, Retour, Soir, Telephone}

    public static final class Contexte {
        public LocalDateTime local;
        public Moment moment;
        public double absenceMin, presenceJourMin, seanceMin;
        public String activite = "", meteo = "", variante = "", prenom = "", metier = "", objet = "", prise = "", plat = "", souvenir = "",
                dateAFeter = "";
        public int palier, stade = 2, niveau, palierNouveau = -1, joursEnsemble, annees;
        public boolean demanderPrenom;

        public Contexte(LocalDateTime local, Moment moment) {
            this.local = local;
            this.moment = moment;
        }
    }

    public static final class Choix {
        public final String famille, texte;
        public final Ligne ligne;

        Choix(String famille, Ligne ligne, String texte) {
            this.famille = famille;
            this.ligne = ligne;
            this.texte = texte;
        }
    }

    public static List<String> plan(Contexte c, String graine) {
        List<String> l = new ArrayList<>();
        LocalDateTime d = c.local;
        int dow = dow(d), heure = d.getHour();
        String saison = "saison-" + saison(d.getMonthValue()), fete = fete(d.getMonthValue(), d.getDayOfMonth()), meteo = meteoFamille(c.meteo);
        List<String> rf = new ArrayList<>();
        List<Integer> rp = new ArrayList<>();
        Runnable annonces = () -> {
            if (!c.dateAFeter.isEmpty()) l.add("date-" + (c.dateAFeter.charAt(0) == 'a' ? "a" : c.dateAFeter));
            if (c.palierNouveau > 0) l.add("palier-" + c.palierNouveau);
        };
        java.util.function.BiConsumer<String, Integer> rot = (f, p) -> {
            rf.add(f);
            rp.add(p);
        };
        java.util.function.IntConsumer souvenirs = p -> {
            if (!c.souvenir.isEmpty()) rot.accept("souvenir-" + c.souvenir, p);
            if (!c.prise.isEmpty()) rot.accept("souvenir-prise", p);
            if (!c.plat.isEmpty()) rot.accept("souvenir-plat", p);
        };
        switch (c.moment) {
            case Premier:
                annonces.run();
                if (c.absenceMin >= 21 * 1440) l.add("retour-long");
                if (c.absenceMin >= 5 * 1440) l.add("retour-semaine");
                else if (c.absenceMin >= 40 * 60) l.add(dow == 1 ? "retour-weekend" : "retour-jours");
                if (!fete.isEmpty()) l.add("fete-" + fete);
                if (dow == 1 && heure < 14) l.add("lundi");
                if (dow == 0 || dow == 6) l.add("weekend");
                rot.accept("bonjour", 4);
                if (c.absenceMin >= 360) rot.accept("retour-nuit", 2);
                rot.accept(saison, 1);
                if (!meteo.isEmpty()) rot.accept("meteo-" + meteo, 1);
                souvenirs.accept(1);
                rot.accept("pensee", 1);
                break;
            case Retour:
                if (c.demanderPrenom) l.add("prenom-demande");
                rot.accept("retour-1h", 4);
                String cu = curiositeDe(c.activite);
                if (!cu.isEmpty()) rot.accept("curiosite-" + cu, 2);
                rot.accept("pensee", 3);
                if (!c.metier.isEmpty()) rot.accept("metier", 2);
                if (c.niveau > 0) rot.accept("niveau", 2);
                if (!c.objet.isEmpty()) rot.accept("objet", 1);
                souvenirs.accept(1);
                if (!meteo.isEmpty()) rot.accept("meteo-" + meteo, 1);
                break;
            case Soir:
                if (dow == 5) l.add("vendredi");
                if (heure >= 22 || heure < 5) l.add("tard");
                if (c.seanceMin >= 150 || c.presenceJourMin >= 360) l.add("fin-seance");
                rot.accept("soir", 4);
                rot.accept("pensee", 2);
                souvenirs.accept(1);
                rot.accept(saison, 1);
                break;
            default:
                annonces.run();
                if (!fete.isEmpty()) l.add("fete-" + fete);
                rot.accept("tel-soir", 4);
                rot.accept("pensee", 3);
                souvenirs.accept(1);
                rot.accept(saison, 1);
                if (!meteo.isEmpty()) rot.accept("meteo-" + meteo, 1);
                if (!c.objet.isEmpty()) rot.accept("objet", 1);
                if (!c.metier.isEmpty()) rot.accept("metier", 1);
                break;
        }
        int total = 0;
        for (int p : rp) total += p;
        int v = tirer(graine + "|famille", total), premier = 0;
        for (int i = 0, acc = 0; i < rf.size(); i++) {
            acc += rp.get(i);
            if (v < acc) {
                premier = i;
                break;
            }
        }
        if (!rf.isEmpty()) l.add(rf.get(premier));
        for (int i = 0; i < rf.size(); i++) if (i != premier) l.add(rf.get(i));
        l.add(c.moment == Moment.Premier ? "bonjour" : c.moment == Moment.Retour ? "retour-1h" : c.moment == Moment.Soir ? "soir" : "tel-soir");
        l.add("pensee");
        return new ArrayList<>(new LinkedHashSet<>(l));
    }

    static String minuscule(String s) {
        return s.isEmpty() ? s : Character.toLowerCase(s.charAt(0)) + s.substring(1);
    }

    static String majuscule(String s) {
        return s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1);
    }

    public static final String[] PALIERS = {"Connaissance", "Copain", "Ami", "Meilleur ami", "Inséparables"};
    public static final int[] SEUILS = {0, 150, 700, 2500, 7000};

    public static String nomPalier(int p) {
        return PALIERS[Math.max(0, Math.min(PALIERS.length - 1, p))];
    }

    public static Choix mot(Contexte c, List<Ligne> banque, Map<String, Integer> dits, String graine) {
        Qui qui = new Qui(c.palier, Math.max(1, Math.min(4, c.stade)), c.variante);
        Map<String, String> valeurs = new HashMap<>();
        mettre(valeurs, "metier", minuscule(c.metier));
        if (c.niveau > 0) valeurs.put("niveau", String.valueOf(c.niveau));
        mettre(valeurs, "objet", minuscule(c.objet));
        mettre(valeurs, "prise", minuscule(c.prise));
        mettre(valeurs, "plat", minuscule(c.plat));
        mettre(valeurs, "palier", minuscule(nomPalier(c.palier)));
        if (c.joursEnsemble > 0) valeurs.put("jours", String.valueOf(c.joursEnsemble));
        if (c.annees > 0) valeurs.put("annees", c.annees == 1 ? "un an" : c.annees + " ans");
        boolean prenom = !c.prenom.isEmpty() && tirer(graine + "|prenom", c.palier >= 4 ? 3 : 5) == 0;
        for (String f : plan(c, graine)) {
            Map<String, String> v = new HashMap<>(valeurs);
            if (!c.prenom.isEmpty() && (prenom || f.startsWith("prenom-"))) v.put("prenom", c.prenom);
            Ligne ligne = choisir(banque, f, qui, v, dits, graine + "|" + f);
            if (ligne != null) return new Choix(f, ligne, remplir(ligne.texte, v));
        }
        return null;
    }

    private static void mettre(Map<String, String> m, String k, String v) {
        if (!v.isEmpty()) m.put(k, v);
    }

    // ---- Téléphone : le mot du soir

    public static int minuteDuSoir(String jour, String appareil) {
        return 19 * 60 + tirer(jour + "|" + appareil + "|soir", 91);
    }

    public static boolean jourDeMot(LocalDateTime local, String frequence, String parle) {
        if ("jamais".equals(parle) || "jamais".equals(frequence)) return false;
        String f = "peu".equals(parle) ? "parfois" : frequence;
        if (!"parfois".equals(f)) return true;
        DayOfWeek d = local.getDayOfWeek();
        return d == DayOfWeek.TUESDAY || d == DayOfWeek.SATURDAY
                || (d == DayOfWeek.THURSDAY && local.toLocalDate().get(IsoFields.WEEK_OF_WEEK_BASED_YEAR) % 2 == 1);
    }

    // ---- Complicité

    public static final int MAX_MINUTES = 180, MAX_CARESSES = 10, MAX_SOINS = 6, MAX_JEUX = 6;

    public static final class Totaux {
        public final int points, palier, jours, adoption, palierAnnonce, finies;
        public final Set<String> fetes;
        public final String prenom;
        public final long prenomT;
        public final boolean prenomDemande;

        Totaux(int points, int palier, int jours, int adoption, Set<String> fetes, int palierAnnonce, String prenom, long prenomT,
               boolean prenomDemande, int finies) {
            this.points = points;
            this.palier = palier;
            this.jours = jours;
            this.adoption = adoption;
            this.fetes = fetes;
            this.palierAnnonce = palierAnnonce;
            this.prenom = prenom;
            this.prenomT = prenomT;
            this.prenomDemande = prenomDemande;
            this.finies = finies;
        }
    }

    public static int palierDe(int points) {
        int p = 0;
        for (int i = 0; i < SEUILS.length; i++) if (points >= SEUILS[i]) p = i;
        return p;
    }

    public static Totaux calculer(Appareil moi, Collection<Appareil> autres) {
        List<Appareil> tous = new ArrayList<>();
        tous.add(moi);
        for (Appareil a : autres) if (!a.id.equals(moi.id)) tous.add(a);
        TreeSet<Integer> jours = new TreeSet<>();
        TreeSet<String> finies = new TreeSet<>(), fetes = new TreeSet<>();
        long points = 0;
        int annonce = 0, adoption = Integer.MAX_VALUE;
        String prenom = "";
        long prenomT = -1;
        boolean demande = false;
        for (Appareil a : tous) {
            points += a.minutes / 10 + a.caresses + 2L * a.soins + 2L * a.jeux;
            jours.addAll(a.jours);
            finies.addAll(a.finies);
            fetes.addAll(a.fetes);
            annonce = Math.max(annonce, a.palierAnnonce);
            if (!a.jours.isEmpty()) adoption = Math.min(adoption, a.jours.first());
            if (a.prenomT > prenomT || (a.prenomT == prenomT && a.prenom.compareTo(prenom) < 0)) {
                prenomT = a.prenomT;
                prenom = a.prenom;
            }
            demande |= a.prenomDemande;
        }
        int suites = 0;
        for (int j : jours) if (jours.contains(j - 1)) suites++;
        points += 10L * jours.size() + 5L * suites + 60L * finies.size();
        int pts = (int) Math.min(Integer.MAX_VALUE, points);
        return new Totaux(pts, palierDe(pts), jours.size(), adoption == Integer.MAX_VALUE ? -1 : adoption, fetes, annonce,
                prenomT < 0 ? "" : prenom, Math.max(0, prenomT), demande, finies.size());
    }

    public static final int[] PALIERS_JOURS = {7, 100, 200, 500, 1000};

    public static String dateAFeter(Totaux t, int aujourdhui) {
        if (t.adoption < 0 || aujourdhui < t.adoption) return "";
        LocalDate debut = LocalDate.ofEpochDay(t.adoption), auj = LocalDate.ofEpochDay(aujourdhui);
        for (int n = 1; n <= 50; n++) {
            LocalDate anniv = debut.plusYears(n);
            if (anniv.isAfter(auj)) break;
            long ecart = auj.toEpochDay() - anniv.toEpochDay();
            if (ecart < 7 && !t.fetes.contains("a" + n)) return "a" + n;
        }
        for (int m : new int[]{1, 6}) {
            long ecart = auj.toEpochDay() - debut.plusMonths(m).toEpochDay();
            if (ecart >= 0 && ecart < 7 && !t.fetes.contains("m" + m)) return "m" + m;
        }
        for (int n : PALIERS_JOURS) if (t.jours >= n && t.jours < n + 7 && !t.fetes.contains("j" + n)) return "j" + n;
        return "";
    }

    public static String nettoyerPrenom(String s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c0 = s.charAt(i);
            char ch = Character.isISOControl(c0) ? ' ' : c0;
            if (ch == '|' || ch == '{' || ch == '}' || ch == ';' || ch == '=' || ch == ',' || Character.isSurrogate(ch)) continue;
            if (ch == ' ' && (b.length() == 0 || b.charAt(b.length() - 1) == ' ')) continue;
            b.append(ch);
        }
        String r = rogner(b.toString());
        return r.length() > PRENOM_MAX ? rogner(r.substring(0, PRENOM_MAX)) : r;
    }

    public static String rogner(String s) {
        int a = 0, b = s.length();
        while (a < b && s.charAt(a) == ' ') a++;
        while (b > a && s.charAt(b - 1) == ' ') b--;
        return s.substring(a, b);
    }

    private static final Set<String> FEMININS = new HashSet<>(Arrays.asList(
            "ablette", "algue", "botte", "perche", "ecrevisse", "bouteille", "truite", "anguille", "cle", "pieuvre", "raie", "perle", "carpe",
            "tartine", "soupe", "brochette", "papillote", "tempura", "chaudree", "bisque", "tourte", "bouillabaisse", "etoile"));
    private static final Set<String> PLURIELS = new HashSet<>(Arrays.asList("croquettes", "maki", "beignets"));

    /** « une truite argentée », « des croquettes croustillantes » : prises et plats pour le journal. */
    public static String avecArticle(String id, String nom) {
        if (nom == null || nom.isEmpty()) return "";
        return (PLURIELS.contains(id) ? "des " : FEMININS.contains(id) ? "une " : "un ") + minuscule(nom);
    }

    // ---- Journal

    public static final class Entree {
        public final String jour, texte, humeur;

        Entree(String jour, String texte, String humeur) {
            this.jour = jour;
            this.texte = texte;
            this.humeur = humeur;
        }

        @Override
        public boolean equals(Object o) {
            return o instanceof Entree && ((Entree) o).jour.equals(jour) && ((Entree) o).texte.equals(texte) && ((Entree) o).humeur.equals(humeur);
        }

        @Override
        public int hashCode() {
            return texte.hashCode();
        }
    }

    private static final String[] ACTIVITES_JOURNAL = {"code", "tableur", "texte", "mail", "visio", "diaporama", "musique", "video", "lecture", "dessin", "jeu"};

    static boolean fin(char c) {
        return c == '.' || c == '!' || c == '?' || c == '…';
    }

    public static int phrases(String t) {
        int n = 0;
        for (int i = 0; i < t.length(); i++) if (fin(t.charAt(i)) && (i + 1 == t.length() || t.charAt(i + 1) == ' ')) n++;
        return n;
    }

    public static String premierePhrase(String t) {
        for (int i = 0; i < t.length(); i++) if (fin(t.charAt(i)) && (i + 1 == t.length() || t.charAt(i + 1) == ' ')) return t.substring(0, i + 1);
        return t;
    }

    static final class Sujet {
        final String famille;
        final Map<String, String> valeurs = new HashMap<>();

        Sujet(String famille, String... kv) {
            this.famille = famille;
            for (int i = 0; i + 1 < kv.length; i += 2) valeurs.put(kv[i], kv[i + 1]);
        }
    }

    static List<Sujet> sujets(FaitsDuJour f) {
        List<Sujet> l = new ArrayList<>();
        if (!f.cf.isEmpty()) l.add(new Sujet("j-campagne", "campagne", f.cf));
        if (f.nv > 0) l.add(new Sujet("j-niveau", "niveau", String.valueOf(f.nv)));
        if (!f.mo.isEmpty()) l.add(new Sujet("j-metier", "metier", minuscule(f.mo)));
        if (!f.px.isEmpty() && f.pq >= 2) l.add(new Sujet("j-prise-rare", "prise", f.px));
        if (f.vi > 0) l.add(new Sujet("j-visite"));
        if (!f.ex.isEmpty()) l.add(new Sujet("j-expedition", "lieu", f.ex));
        if (!f.cx.isEmpty()) l.add(new Sujet("j-plat", "plat", f.cx));
        if (!f.ob.isEmpty()) l.add(new Sujet("j-objet", "objet", minuscule(f.ob)));
        if (f.jx >= 3) l.add(new Sujet("j-jeux", "n", String.valueOf(f.jx)));
        if (f.jx > 0 && f.jx < 3) l.add(new Sujet("j-jeu"));
        if (f.ca >= 5) l.add(new Sujet("j-caresses"));
        if (f.ca > 0 && f.ca < 5) l.add(new Sujet("j-caresse"));
        if (f.so > 0) l.add(new Sujet("j-soins"));
        if (f.pc > 0 && !f.px.isEmpty() && f.pq < 2) l.add(new Sujet("j-peche", "prise", f.px));
        if (f.qu > 0) l.add(new Sujet("j-quetes", "n", String.valueOf(f.qu)));
        if (f.tv >= 300) l.add(new Sujet("j-travail-long"));
        String ac = "jeu-mmo".equals(f.ac) ? "jeu" : f.ac;
        if (indice(ACTIVITES_JOURNAL, ac) >= 0 && f.am >= 20) l.add(new Sujet("j-act-" + ac));
        if (f.ta >= 22 * 60) l.add(new Sujet("j-tard"));
        if (!meteoFamille(f.me).isEmpty()) l.add(new Sujet("j-meteo-" + meteoFamille(f.me)));
        if (f.ce > 0 && f.cf.isEmpty()) l.add(new Sujet("j-aventure"));
        if (f.mn >= 5 || l.isEmpty()) l.add(new Sujet("j-calme"));
        return l;
    }

    public static String humeur(FaitsDuJour f) {
        return !f.cf.isEmpty() || f.nv > 0 ? "fete"
                : f.ca >= 5 ? "tendre"
                : f.jx >= 3 || f.pq >= 2 || f.vi > 0 ? "joie"
                : f.ta >= 23 * 60 || f.tv >= 420 ? "fatigue"
                : f.ca > 0 || f.so > 0 ? "caresse"
                : f.tv >= 120 ? "concentre"
                : "repos";
    }

    public static Entree ecrire(String jour, FaitsDuJour f, List<Ligne> gabarits) {
        if (f.vide()) return null;
        List<Sujet> sujets = sujets(f);
        Qui qui = new Qui(9, 2, "");
        Map<String, Integer> vides = new HashMap<>();
        List<String> phrases = new ArrayList<>();
        int premier = -1;
        for (int i = 0; i < sujets.size() && phrases.isEmpty(); i++) {
            String t = une(gabarits, qui, vides, jour, sujets.get(i).famille, sujets.get(i).valeurs, 1);
            if (t != null) {
                phrases.add(t);
                premier = i;
            }
        }
        if (phrases.isEmpty()) return null;
        String ac = "jeu-mmo".equals(f.ac) ? "jeu" : f.ac;
        boolean mot = false;
        if (indice(ACTIVITES_JOURNAL, ac) >= 0 && f.am >= 20 && tirer(jour + "|journal|mot", 3) == 0) {
            Ligne m = choisir(gabarits, "mot-" + ac, qui, new HashMap<>(), vides, jour + "|journal|mot-" + ac);
            if (m != null) {
                Map<String, String> v = new HashMap<>();
                v.put("mot", m.texte);
                String tm = une(gabarits, qui, vides, jour, "j-mot", v, 3);
                if (tm != null) mot = ajouter(phrases, tm) || ajouter(phrases, premierePhrase(tm));
            }
        }
        if (!mot) {
            List<Sujet> reste = new ArrayList<>();
            for (int i = 0; i < sujets.size() && reste.size() < 4; i++)
                if (i != premier && !(sujets.get(i).famille.equals("j-calme") && sujets.size() > 1)) reste.add(sujets.get(i));
            if (!reste.isEmpty()) {
                Sujet s = reste.get(tirer(jour + "|journal|second", reste.size()));
                String t = une(gabarits, qui, vides, jour, s.famille, s.valeurs, 2);
                if (t != null) ajouter(phrases, premierePhrase(t));
            }
            if (tirer(jour + "|journal|fin", 2) == 0) ajouter(phrases, une(gabarits, qui, vides, jour, "j-fin", new HashMap<>(), 4));
        }
        return new Entree(jour, String.join(" ", phrases), humeur(f));
    }

    private static String une(List<Ligne> gabarits, Qui qui, Map<String, Integer> vides, String jour, String famille, Map<String, String> v, int k) {
        Ligne g = choisir(gabarits, famille, qui, v, vides, jour + "|journal|" + famille + "|" + k);
        return g == null ? null : majuscule(remplir(g.texte, v));
    }

    private static boolean ajouter(List<String> phrases, String t) {
        if (t != null && t.startsWith("Aujourd'hui, ")) t = majuscule(t.substring("Aujourd'hui, ".length()));
        else if (t != null && t.startsWith("Aujourd'hui ")) t = majuscule(t.substring("Aujourd'hui ".length()));
        if (t == null || t.isEmpty()) return false;
        List<String> essai = new ArrayList<>(phrases);
        essai.add(t);
        if (phrases(String.join(" ", essai)) > 3) return false;
        phrases.add(t);
        return true;
    }

    // ---- Synchronisation

    public static String sujet(String code) throws java.security.GeneralSecurityException {
        byte[] h = Chiffre.hmac(code, "pilou-presence-v1");
        StringBuilder b = new StringBuilder("pilou-");
        for (int i = 0; i < 12; i++) b.append(String.format(Locale.ROOT, "%02x", h[i]));
        return b.toString();
    }

    public static int octets(String s) {
        return s.getBytes(StandardCharsets.UTF_8).length;
    }

    public static String propre(String s) {
        return propre(s, 40);
    }

    public static String propre(String s, int max) {
        if (s == null || s.isEmpty()) return "";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            b.append(ch == ';' || ch == '=' || ch == '|' || ch == ',' || Character.isISOControl(ch) || Character.isSurrogate(ch) ? ' ' : ch);
        }
        String r = rogner(b.toString());
        return r.length() > max ? rogner(r.substring(0, max)) : r;
    }

    static int entier(String s, int min, int max) {
        try {
            long v = Long.parseLong(s);
            if (v < Integer.MIN_VALUE || v > Integer.MAX_VALUE) return 0;
            return (int) Math.max(min, Math.min(max, v));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    static long longue(String s) {
        try {
            return Long.parseLong(s);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    // =====================================================================================================================

    /** Les faits d'un jour, vus par un appareil. Fusion : maximum et paire de plus grand poids (FaitsDuJour en C#). */
    public static final class FaitsDuJour {
        public int mn, tv, am, ta, jx, ca, so, pc, pq, cu, qu, ce, vi, nv, mg;
        public String ac = "", px = "", cx = "", me = "", cf = "", mo = "", ex = "", ob = "";

        public boolean vide() {
            return mn < 5 && tv == 0 && jx == 0 && ca == 0 && so == 0 && pc == 0 && cu == 0 && qu == 0 && ce == 0 && vi == 0
                    && nv == 0 && cf.isEmpty() && mo.isEmpty() && ex.isEmpty() && ob.isEmpty() && cx.isEmpty() && px.isEmpty();
        }

        private static final String[] ORDRE_METEO = {"orage", "neige", "pluie", "averse", "brouillard", "vent", "chaleur", "froid", "degage", "nuageux"};

        private static int rangMeteo(String m) {
            int i = indice(ORDRE_METEO, m);
            return i < 0 ? Integer.MAX_VALUE : i;
        }

        private static String min(String a, String b) {
            return a.isEmpty() ? b : b.isEmpty() ? a : a.compareTo(b) <= 0 ? a : b;
        }

        public static FaitsDuJour fusion(FaitsDuJour a, FaitsDuJour b) {
            FaitsDuJour r = new FaitsDuJour();
            r.mn = Math.max(a.mn, b.mn);
            r.tv = Math.max(a.tv, b.tv);
            r.ta = Math.max(a.ta, b.ta);
            r.jx = Math.max(a.jx, b.jx);
            r.ca = Math.max(a.ca, b.ca);
            r.so = Math.max(a.so, b.so);
            r.pc = Math.max(a.pc, b.pc);
            r.cu = Math.max(a.cu, b.cu);
            r.qu = Math.max(a.qu, b.qu);
            r.ce = Math.max(a.ce, b.ce);
            r.vi = Math.max(a.vi, b.vi);
            r.nv = Math.max(a.nv, b.nv);
            r.cx = min(a.cx, b.cx);
            r.cf = min(a.cf, b.cf);
            r.ex = min(a.ex, b.ex);
            r.ob = min(a.ob, b.ob);
            if (a.am > b.am || (a.am == b.am && min(a.ac, b.ac).equals(a.ac))) {
                r.ac = a.ac;
                r.am = a.am;
            } else {
                r.ac = b.ac;
                r.am = b.am;
            }
            if (!a.px.isEmpty() && (b.px.isEmpty() || a.pq > b.pq || (a.pq == b.pq && a.px.compareTo(b.px) <= 0))) {
                r.px = a.px;
                r.pq = a.pq;
            } else {
                r.px = b.px;
                r.pq = b.pq;
            }
            if (!a.mo.isEmpty() && (b.mo.isEmpty() || a.mg > b.mg || (a.mg == b.mg && a.mo.compareTo(b.mo) <= 0))) {
                r.mo = a.mo;
                r.mg = a.mg;
            } else {
                r.mo = b.mo;
                r.mg = b.mg;
            }
            int ra = rangMeteo(a.me), rb = rangMeteo(b.me);
            r.me = ra <= rb ? (ra == rb ? min(a.me, b.me) : a.me) : b.me;
            return r;
        }

        public String texte() {
            StringBuilder b = new StringBuilder();
            n(b, "mn", mn);
            n(b, "tv", tv);
            s(b, "ac", ac);
            n(b, "am", am);
            n(b, "ta", ta);
            n(b, "jx", jx);
            n(b, "ca", ca);
            n(b, "so", so);
            n(b, "pc", pc);
            s(b, "px", px);
            n(b, "pq", pq);
            n(b, "cu", cu);
            s(b, "cx", cx);
            n(b, "qu", qu);
            s(b, "me", me);
            s(b, "cf", cf);
            n(b, "ce", ce);
            n(b, "vi", vi);
            n(b, "nv", nv);
            s(b, "mo", mo);
            n(b, "mg", mg);
            s(b, "ex", ex);
            s(b, "ob", ob);
            return b.toString();
        }

        private static void n(StringBuilder b, String k, int v) {
            if (v == 0) return;
            if (b.length() > 0) b.append(';');
            b.append(k).append('=').append(v);
        }

        private static void s(StringBuilder b, String k, String v) {
            if (v.isEmpty()) return;
            if (b.length() > 0) b.append(';');
            b.append(k).append('=').append(v);
        }

        public static FaitsDuJour lire(String texte) {
            FaitsDuJour f = new FaitsDuJour();
            if (texte == null || texte.isEmpty()) return f;
            for (String paire : couper(texte, ";")) {
                int i = paire.indexOf('=');
                if (i <= 0) continue;
                String k = paire.substring(0, i), v = propre(paire.substring(i + 1));
                int n = entier(v, 0, 100_000);
                switch (k) {
                    case "mn": f.mn = n; break;
                    case "tv": f.tv = n; break;
                    case "ac": f.ac = v; break;
                    case "am": f.am = n; break;
                    case "ta": f.ta = Math.min(n, 1439); break;
                    case "jx": f.jx = n; break;
                    case "ca": f.ca = n; break;
                    case "so": f.so = n; break;
                    case "pc": f.pc = n; break;
                    case "px": f.px = v; break;
                    case "pq": f.pq = Math.min(n, 9); break;
                    case "cu": f.cu = n; break;
                    case "cx": f.cx = v; break;
                    case "qu": f.qu = n; break;
                    case "me": f.me = v; break;
                    case "cf": f.cf = v; break;
                    case "ce": f.ce = n; break;
                    case "vi": f.vi = n; break;
                    case "nv": f.nv = Math.min(n, 999); break;
                    case "mo": f.mo = v; break;
                    case "mg": f.mg = Math.min(n, 9); break;
                    case "ex": f.ex = v; break;
                    case "ob": f.ob = v; break;
                    default: break;
                }
            }
            return f;
        }

        public FaitsDuJour copie() {
            return lire(texte());
        }
    }

    // =====================================================================================================================

    /** Ce qu'un appareil sait de lui pour la complicité (Appareil en C#). */
    public static final class Appareil {
        public String id = "", sorte = "pc", prenom = "";
        public long t, prenomT = -1;
        public int minutes, caresses, soins, jeux, palierAnnonce;
        public final TreeSet<Integer> jours = new TreeSet<>();
        public final TreeSet<String> finies = new TreeSet<>(), fetes = new TreeSet<>();
        public boolean prenomDemande;
        public final TreeMap<String, FaitsDuJour> recents = new TreeMap<>();

        public boolean absorber(Appareil b) {
            String avant = texte(true, Integer.MAX_VALUE);
            t = Math.max(t, b.t);
            minutes = Math.max(minutes, b.minutes);
            caresses = Math.max(caresses, b.caresses);
            soins = Math.max(soins, b.soins);
            jeux = Math.max(jeux, b.jeux);
            palierAnnonce = Math.max(palierAnnonce, b.palierAnnonce);
            jours.addAll(b.jours);
            finies.addAll(b.finies);
            fetes.addAll(b.fetes);
            if (b.prenomT > prenomT || (b.prenomT == prenomT && b.prenom.compareTo(prenom) < 0)) {
                prenomT = b.prenomT;
                prenom = b.prenom;
            }
            prenomDemande |= b.prenomDemande;
            if (b.sorte.equals("pc") || b.sorte.equals("tel")) sorte = b.sorte;
            for (Map.Entry<String, FaitsDuJour> e : b.recents.entrySet()) {
                FaitsDuJour x = recents.get(e.getKey());
                recents.put(e.getKey(), x != null ? FaitsDuJour.fusion(x, e.getValue()) : e.getValue().copie());
            }
            return !avant.equals(texte(true, Integer.MAX_VALUE));
        }

        private static final String HEX = "0123456789abcdef";

        public String texte(boolean avecRecents) {
            return texte(avecRecents, Integer.MAX_VALUE);
        }

        public String texte(boolean avecRecents, int maxRecents) {
            StringBuilder b = new StringBuilder();
            b.append("a ").append(id).append('\n');
            b.append("k ").append(sorte).append('\n');
            b.append("t ").append(t).append('\n');
            b.append("c ").append(minutes).append(' ').append(caresses).append(' ').append(soins).append(' ').append(jeux).append('\n');
            if (!jours.isEmpty()) {
                int origine = jours.first(), n = jours.last() - origine + 1;
                StringBuilder h = new StringBuilder();
                for (int i = 0; i < n; i += 4) {
                    int v = 0;
                    for (int k = 0; k < 4; k++) if (jours.contains(origine + i + k)) v |= 8 >> k;
                    h.append(HEX.charAt(v));
                }
                b.append("j ").append(origine).append(' ').append(h).append('\n');
            }
            if (!finies.isEmpty()) b.append("f ").append(String.join(",", finies)).append('\n');
            if (palierAnnonce > 0) b.append("pa ").append(palierAnnonce).append('\n');
            if (!fetes.isEmpty()) b.append("fe ").append(String.join(",", fetes)).append('\n');
            if (prenomT >= 0) b.append("n ").append(prenomT).append(' ').append(prenom).append('\n');
            if (prenomDemande) b.append("q 1\n");
            if (avecRecents) {
                List<Map.Entry<String, FaitsDuJour>> l = new ArrayList<>(recents.entrySet());
                for (int i = Math.max(0, l.size() - maxRecents); i < l.size(); i++) {
                    String ft = l.get(i).getValue().texte();
                    if (!ft.isEmpty()) b.append("d ").append(l.get(i).getKey()).append(' ').append(ft).append('\n');
                }
            }
            return b.toString();
        }

        public boolean lireLigne(String ligne) {
            int i = ligne.indexOf(' ');
            String k = i < 0 ? ligne : ligne.substring(0, i), v = i < 0 ? "" : ligne.substring(i + 1);
            switch (k) {
                case "a": id = propre(v, 64); return true;
                case "k": sorte = v.equals("tel") ? "tel" : "pc"; return true;
                case "t": t = Math.max(0, longue(v)); return true;
                case "c": {
                    String[] p = couper(v, " ");
                    if (p.length >= 4) {
                        minutes = entier(p[0], 0, 100_000_000);
                        caresses = entier(p[1], 0, 100_000_000);
                        soins = entier(p[2], 0, 100_000_000);
                        jeux = entier(p[3], 0, 100_000_000);
                    }
                    return true;
                }
                case "j": {
                    String[] p = couper(v, " ");
                    if (p.length == 2 && p[1].length() <= 2000) {
                        int o;
                        try {
                            o = Integer.parseInt(p[0]);
                        } catch (NumberFormatException e) {
                            return true;
                        }
                        if (o > 0 && o < 200_000)
                            for (int x = 0; x < p[1].length(); x++) {
                                int h = HEX.indexOf(p[1].charAt(x));
                                if (h < 0) continue;
                                for (int bit = 0; bit < 4; bit++) if ((h & (8 >> bit)) != 0) jours.add(o + x * 4 + bit);
                            }
                    }
                    return true;
                }
                case "f":
                    for (String x : couper(v, ",")) {
                        String id = propre(x);
                        if (!id.isEmpty() && finies.size() < 100) finies.add(id);
                    }
                    return true;
                case "pa": palierAnnonce = Math.min(entier(v, 0, 100_000_000), PALIERS.length - 1); return true;
                case "fe":
                    for (String x : couper(v, ",")) {
                        String id = propre(x, 8);
                        if (!id.isEmpty() && fetes.size() < 200) fetes.add(id);
                    }
                    return true;
                case "n": {
                    int s = v.indexOf(' ');
                    String tt = s < 0 ? v : v.substring(0, s);
                    try {
                        long pt = Long.parseLong(tt);
                        if (pt >= 0) {
                            prenomT = pt;
                            prenom = nettoyerPrenom(s < 0 ? "" : v.substring(s + 1));
                        }
                    } catch (NumberFormatException e) {
                        // ignoré
                    }
                    return true;
                }
                case "q": prenomDemande = v.equals("1"); return true;
                case "d": {
                    int s = v.indexOf(' ');
                    if (s > 0 && jourDe(v.substring(0, s)) != Integer.MIN_VALUE && recents.size() < 30)
                        recents.put(v.substring(0, s), FaitsDuJour.lire(v.substring(s + 1)));
                    return true;
                }
                default:
                    return false;
            }
        }

        public static Appareil lire(String texte) {
            Appareil a = new Appareil();
            for (String l : couper(texte.replace("\r\n", "\n"), "\n")) if (!l.isEmpty()) a.lireLigne(l);
            return a.id.isEmpty() ? null : a;
        }

        public String message() {
            for (int n = JOURS_DANS_MESSAGE; n >= 0; n--) {
                String m = "pilou-presence 1\n" + texte(true, n);
                if (octets(m) <= TAILLE_MESSAGE || n == 0) return m;
            }
            return "pilou-presence 1\n" + texte(false);
        }

        public static Appareil lireMessage(String texte) {
            String t = texte.replace("\r\n", "\n");
            if (!t.startsWith("pilou-presence 1\n")) return null;
            return lire(t.substring("pilou-presence 1\n".length()));
        }
    }

    // =====================================================================================================================

    /** Le rythme des petits mots sur le PC (Cadence en C#) ; le téléphone ne s'en sert pas (mot du soir). */
    public static final class Cadence {
        public String jour = "", attente = "";
        public int dits, attenteAbsence;
        public long dernierMot, derniereVue, debutSeance, attenteDepuis;
        public double presenceJourMin;
        public boolean soir;
    }

    public static final double PAUSE = 45, ECART = 90, EXPIRE = 25, SOIR_APRES = 90;

    public static int plafond(String parle) {
        return "jamais".equals(parle) ? 0 : "peu".equals(parle) ? 1 : 3;
    }

    public static void observer(Cadence r, long maintenant, LocalDateTime local, boolean present) {
        if (!present) return;
        String jour = jourTexte(local);
        double absence = r.derniereVue <= 0 ? 0 : Math.max(0, (maintenant - r.derniereVue) / 60_000.0);
        if (!jour.equals(r.jour)) {
            boolean premiereFois = r.jour.isEmpty();
            r.jour = jour;
            r.dits = 0;
            r.soir = false;
            r.presenceJourMin = 0;
            r.debutSeance = maintenant;
            r.attente = premiereFois ? "" : "premier";
            r.attenteDepuis = maintenant;
            r.attenteAbsence = (int) Math.min(absence, Integer.MAX_VALUE);
        } else if (absence >= PAUSE) {
            r.debutSeance = maintenant;
            if (r.attente.isEmpty() || r.attente.equals("soir")) {
                r.attente = "retour";
                r.attenteDepuis = maintenant;
                r.attenteAbsence = (int) absence;
            }
        } else r.presenceJourMin += Math.min(absence, 2);
        if (r.attente.isEmpty() && !r.soir && (local.getHour() >= 18 || local.getHour() < 4) && r.presenceJourMin >= SOIR_APRES) {
            r.attente = "soir";
            r.attenteDepuis = maintenant;
            r.attenteAbsence = 0;
        }
        r.derniereVue = maintenant;
    }

    public static Moment pret(Cadence r, long maintenant, String parle, boolean calme) {
        if (r.attente.isEmpty()) return null;
        int reserve = r.attente.equals("retour") && !r.soir ? 1 : 0;
        if (r.dits >= plafond(parle) - reserve) {
            r.attente = "";
            return null;
        }
        if (!r.attente.equals("soir") && maintenant - r.attenteDepuis > EXPIRE * 60_000) {
            r.attente = "";
            return null;
        }
        if (!r.attente.equals("premier") && r.dernierMot > 0 && maintenant - r.dernierMot < ECART * 60_000) {
            if (r.attente.equals("retour")) r.attente = "";
            return null;
        }
        if (!calme) return null;
        return r.attente.equals("premier") ? Moment.Premier : r.attente.equals("retour") ? Moment.Retour : Moment.Soir;
    }

    public static void noter(Cadence r, long maintenant, Moment m) {
        r.dits++;
        r.dernierMot = maintenant;
        if (m == Moment.Soir) r.soir = true;
        r.attente = "";
    }

    // =====================================================================================================================

    /** Tout ce qu'un appareil garde de la présence (EtatPresence en C#, même format texte). */
    public static final class Etat {
        public Appareil moi = new Appareil();
        public final TreeMap<String, Appareil> autres = new TreeMap<>();
        public final TreeMap<String, TreeMap<String, FaitsDuJour>> journal = new TreeMap<>();
        public final Map<String, Integer> dits = new HashMap<>();
        public Cadence cadence = new Cadence();
        public String capJour = "";
        public int capMin, capCar, capSoi, capJeu;
        public double secondesEnsemble;
        public String parle = "normal", frequence = "chaque";
        public boolean journalActif = true, gestes = true;
        public String motJour = "", motTexte = "", motNotifie = "";
        public String actJour = "";
        public final TreeMap<String, Double> actSec = new TreeMap<>();

        public static final String FIGE = "*";

        public void marquer(int jour) {
            if (jour > 0) moi.jours.add(jour);
        }

        private void caps(String jour) {
            if (capJour.equals(jour)) return;
            capJour = jour;
            capMin = capCar = capSoi = capJeu = 0;
        }

        public int ajouter(String quoi, int n, LocalDateTime local) {
            if (n <= 0) return 0;
            caps(jourTexte(local));
            marquer(jour(local));
            int pris;
            switch (quoi) {
                case "minutes":
                    pris = Math.min(n, MAX_MINUTES - capMin);
                    capMin += Math.max(0, pris);
                    moi.minutes += Math.max(0, pris);
                    break;
                case "caresses":
                    pris = Math.min(n, MAX_CARESSES - capCar);
                    capCar += Math.max(0, pris);
                    moi.caresses += Math.max(0, pris);
                    break;
                case "soins":
                    pris = Math.min(n, MAX_SOINS - capSoi);
                    capSoi += Math.max(0, pris);
                    moi.soins += Math.max(0, pris);
                    break;
                case "jeux":
                    pris = Math.min(n, MAX_JEUX - capJeu);
                    capJeu += Math.max(0, pris);
                    moi.jeux += Math.max(0, pris);
                    break;
                default:
                    return 0;
            }
            return Math.max(0, pris);
        }

        public FaitsDuJour aujourdhui(String jour) {
            TreeMap<String, FaitsDuJour> s = journal.computeIfAbsent(jour, k -> new TreeMap<>());
            return s.computeIfAbsent(moi.id, k -> new FaitsDuJour());
        }

        public FaitsDuJour faitsDu(String jour) {
            FaitsDuJour r = new FaitsDuJour();
            TreeMap<String, FaitsDuJour> s = journal.get(jour);
            if (s != null) for (FaitsDuJour f : s.values()) r = FaitsDuJour.fusion(r, f);
            return r;
        }

        public void compacter(int aujourdhui) {
            for (String jour : new ArrayList<>(journal.keySet())) {
                int j = jourDe(jour);
                if (j == Integer.MIN_VALUE) {
                    journal.remove(jour);
                    continue;
                }
                TreeMap<String, FaitsDuJour> s = journal.get(jour);
                if (aujourdhui - j > JOURS_OUVERTS && (s.size() > 1 || !s.containsKey(FIGE))) {
                    FaitsDuJour f = faitsDu(jour);
                    TreeMap<String, FaitsDuJour> n = new TreeMap<>();
                    n.put(FIGE, f);
                    journal.put(jour, n);
                }
            }
            while (journal.size() > JOURS_GARDES) journal.remove(journal.firstKey());
        }

        public boolean recevoir(Appareil a, int aujourdhui) {
            if (a.id.isEmpty() || a.id.equals(moi.id) || a.id.equals(FIGE)) return false;
            boolean change = false;
            Appareil sans = Appareil.lire(a.texte(false));
            Appareil avant = autres.get(a.id);
            if (avant != null) change |= avant.absorber(sans);
            else if (autres.size() < 32) {
                autres.put(a.id, sans);
                change = true;
            }
            for (Map.Entry<String, FaitsDuJour> e : a.recents.entrySet()) {
                int j = jourDe(e.getKey());
                if (j == Integer.MIN_VALUE || aujourdhui - j > JOURS_OUVERTS || j > aujourdhui + 1) continue;
                TreeMap<String, FaitsDuJour> s = journal.computeIfAbsent(e.getKey(), k -> new TreeMap<>());
                FaitsDuJour x = s.get(a.id);
                FaitsDuJour n = x != null ? FaitsDuJour.fusion(x, e.getValue()) : e.getValue().copie();
                if (x == null || !x.texte().equals(n.texte())) {
                    s.put(a.id, n);
                    change = true;
                }
            }
            return change;
        }

        public String message(int aujourdhui) {
            Appareil m = Appareil.lire(moi.texte(false));
            if (m == null) {
                m = new Appareil();
                m.id = moi.id;
            }
            for (Map.Entry<String, TreeMap<String, FaitsDuJour>> e : journal.entrySet()) {
                int j = jourDe(e.getKey());
                if (aujourdhui - j >= JOURS_DANS_MESSAGE || j > aujourdhui) continue;
                FaitsDuJour f = e.getValue().get(moi.id);
                if (f != null && !f.vide()) m.recents.put(e.getKey(), f);
            }
            return m.message();
        }

        public Totaux totaux() {
            return calculer(moi, autres.values());
        }

        public List<Entree> entrees(List<Ligne> gabarits) {
            List<Entree> l = new ArrayList<>();
            for (String jour : journal.descendingKeySet()) {
                Entree e = ecrire(jour, faitsDu(jour), gabarits);
                if (e != null) l.add(e);
            }
            return l;
        }

        public String prenom() {
            return totaux().prenom;
        }

        public void choisirPrenom(String prenom, long maintenant) {
            moi.prenom = nettoyerPrenom(prenom);
            long max = -1;
            for (Appareil a : autres.values()) max = Math.max(max, a.prenomT);
            moi.prenomT = Math.max(maintenant, Math.max(moi.prenomT, max) + 1);
            moi.prenomDemande = true;
        }

        public String texte() {
            StringBuilder b = new StringBuilder("pilou-presence-etat 1\n[moi]\n");
            b.append(moi.texte(false));
            for (Appareil a : autres.values()) {
                b.append("[autre]\n");
                b.append(a.texte(false));
            }
            b.append("[journal]\n");
            for (Map.Entry<String, TreeMap<String, FaitsDuJour>> e : journal.entrySet())
                for (Map.Entry<String, FaitsDuJour> s : e.getValue().entrySet()) {
                    String t = s.getValue().texte();
                    if (!t.isEmpty()) b.append(e.getKey()).append(' ').append(s.getKey()).append(' ').append(t).append('\n');
                }
            b.append("[dits]\n");
            List<String> cles = new ArrayList<>(dits.keySet());
            Collections.sort(cles);
            for (String id : cles) b.append(id).append(' ').append(dits.get(id)).append('\n');
            b.append("[divers]\n");
            b.append("parle ").append(parle).append('\n');
            b.append("frequence ").append(frequence).append('\n');
            b.append("journal ").append(journalActif ? "1" : "0").append('\n');
            b.append("gestes ").append(gestes ? "1" : "0").append('\n');
            b.append("cap ").append(capJour.isEmpty() ? "-" : capJour).append(' ').append(capMin).append(' ').append(capCar).append(' ')
                    .append(capSoi).append(' ').append(capJeu).append('\n');
            b.append("ensemble ").append((long) secondesEnsemble).append('\n');
            Cadence r = cadence;
            b.append("rythme ").append(r.jour.isEmpty() ? "-" : r.jour).append(' ').append(r.dits).append(' ').append(r.dernierMot).append(' ')
                    .append(r.derniereVue).append(' ').append(r.debutSeance).append(' ').append((long) (r.presenceJourMin * 60)).append(' ')
                    .append(r.soir ? "1" : "0").append(' ').append(r.attente.isEmpty() ? "-" : r.attente).append(' ').append(r.attenteDepuis)
                    .append(' ').append(r.attenteAbsence).append('\n');
            if (!actJour.isEmpty()) {
                List<String> l = new ArrayList<>();
                for (Map.Entry<String, Double> e : actSec.entrySet()) l.add(e.getKey() + ":" + (long) (double) e.getValue());
                b.append("act ").append(actJour).append(' ').append(String.join(",", l)).append('\n');
            }
            if (!motJour.isEmpty())
                b.append("mot ").append(motJour).append(' ').append(motNotifie.isEmpty() ? "-" : motNotifie).append(' ').append(motTexte).append('\n');
            return b.toString();
        }

        private static String tiret(String s) {
            return s.equals("-") ? "" : s;
        }

        public static Etat lire(String texte) {
            Etat e = new Etat();
            if (texte == null || texte.isEmpty()) return e;
            String[] lignes = couper(texte.replace("\r\n", "\n"), "\n");
            if (lignes.length == 0 || !lignes[0].equals("pilou-presence-etat 1")) return e;
            String section = "";
            Appareil autre = null;
            for (int i = 1; i < lignes.length; i++) {
                String l = lignes[i];
                if (l.isEmpty()) continue;
                if (l.charAt(0) == '[') {
                    ranger(e, autre);
                    autre = null;
                    section = l;
                    if (section.equals("[autre]")) autre = new Appareil();
                    continue;
                }
                try {
                    switch (section) {
                        case "[moi]":
                            e.moi.lireLigne(l);
                            break;
                        case "[autre]":
                            if (autre != null) autre.lireLigne(l);
                            break;
                        case "[journal]": {
                            String[] p = couper(l, " ", 3);
                            if (p.length == 3 && jourDe(p[0]) != Integer.MIN_VALUE)
                                e.journal.computeIfAbsent(p[0], k -> new TreeMap<>()).put(p[1], FaitsDuJour.lire(p[2]));
                            break;
                        }
                        case "[dits]": {
                            String[] p = couper(l, " ");
                            if (p.length == 2 && p[0].length() == 8) e.dits.put(p[0], entier(p[1], Integer.MIN_VALUE, Integer.MAX_VALUE));
                            break;
                        }
                        case "[divers]": {
                            String[] p = couper(l, " ");
                            switch (p[0]) {
                                case "parle":
                                    e.parle = p.length > 1 && (p[1].equals("peu") || p[1].equals("jamais")) ? p[1] : "normal";
                                    break;
                                case "frequence":
                                    e.frequence = p.length > 1 && (p[1].equals("parfois") || p[1].equals("jamais")) ? p[1] : "chaque";
                                    break;
                                case "journal":
                                    e.journalActif = p.length < 2 || !p[1].equals("0");
                                    break;
                                case "gestes":
                                    e.gestes = p.length < 2 || !p[1].equals("0");
                                    break;
                                case "cap":
                                    if (p.length == 6) {
                                        e.capJour = tiret(p[1]);
                                        e.capMin = entier(p[2], Integer.MIN_VALUE, Integer.MAX_VALUE);
                                        e.capCar = entier(p[3], Integer.MIN_VALUE, Integer.MAX_VALUE);
                                        e.capSoi = entier(p[4], Integer.MIN_VALUE, Integer.MAX_VALUE);
                                        e.capJeu = entier(p[5], Integer.MIN_VALUE, Integer.MAX_VALUE);
                                    }
                                    break;
                                case "ensemble":
                                    if (p.length == 2) e.secondesEnsemble = longue(p[1]);
                                    break;
                                case "rythme":
                                    if (p.length == 11) {
                                        Cadence r = new Cadence();
                                        r.jour = tiret(p[1]);
                                        r.dits = entier(p[2], Integer.MIN_VALUE, Integer.MAX_VALUE);
                                        r.dernierMot = longue(p[3]);
                                        r.derniereVue = longue(p[4]);
                                        r.debutSeance = longue(p[5]);
                                        r.presenceJourMin = longue(p[6]) / 60.0;
                                        r.soir = p[7].equals("1");
                                        r.attente = tiret(p[8]);
                                        r.attenteDepuis = longue(p[9]);
                                        r.attenteAbsence = entier(p[10], Integer.MIN_VALUE, Integer.MAX_VALUE);
                                        e.cadence = r;
                                    }
                                    break;
                                case "act":
                                    if (p.length >= 2) {
                                        e.actJour = p[1];
                                        if (p.length == 3)
                                            for (String x : couper(p[2], ",")) {
                                                int k = x.indexOf(':');
                                                if (k > 0) e.actSec.put(x.substring(0, k), (double) longue(x.substring(k + 1)));
                                            }
                                    }
                                    break;
                                case "mot":
                                    if (p.length >= 3) {
                                        String[] q = couper(l, " ", 4);
                                        e.motJour = q[1];
                                        e.motNotifie = tiret(q[2]);
                                        e.motTexte = q.length == 4 ? q[3] : "";
                                    }
                                    break;
                                default:
                                    break;
                            }
                            break;
                        }
                        default:
                            break;
                    }
                } catch (RuntimeException ligneAbimee) {
                    // ligne abîmée : ignorée
                }
            }
            ranger(e, autre);
            return e;
        }

        private static void ranger(Etat e, Appareil autre) {
            if (autre != null && !autre.id.isEmpty() && !autre.id.equals(e.moi.id) && e.autres.size() < 32) e.autres.put(autre.id, autre);
        }
    }
}
