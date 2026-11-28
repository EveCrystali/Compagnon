package fr.pilou.compagnon;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Les traits de personnalité de Pilou (docs/TRAITS.md) : copie exacte de apps/PilouBureau/Traits.cs. Aucune dépendance
 * Android. Lit assets/traits.txt et rejoue src/test/resources/traits-vecteurs.txt, écrit par le PC (TraitsTest).
 */
public final class Traits {
    public static final int MAX = 60, NOMBRE_DOMINANTS = 3, FENETRE = 28;

    private Traits() {
    }

    static final List<String> NOMBRES = Arrays.asList("mn", "tv", "am", "ta", "jx", "ca", "so", "pc", "pq", "cu", "qu", "ce", "vi", "nv", "mg", "ma", "we", "sem", "abs");
    static final List<String> TEXTES = Arrays.asList("ac", "px", "cx", "me", "cf", "mo", "ex", "ob");

    /** Un terme de condition : fait, comparaison (>= <= = !=), valeur (nombre ou texte). */
    public static final class Terme {
        public final String fait, op, valeur;
        public final int nombre;
        public final boolean texte;

        Terme(String fait, String op, String valeur, int nombre, boolean texte) {
            this.fait = fait;
            this.op = op;
            this.valeur = valeur;
            this.nombre = nombre;
            this.texte = texte;
        }
    }

    public static final class Trait {
        public final int numero, seuil;
        public final String id, nom;
        public final List<Terme> condition;

        Trait(int numero, String id, String nom, int seuil, List<Terme> condition) {
            this.numero = numero;
            this.id = id;
            this.nom = nom;
            this.seuil = seuil;
            this.condition = condition;
        }

        public long bit() {
            return 1L << (numero - 1);
        }

        public String sprite() {
            return "trait-" + id;
        }
    }

    // ---- Définition (assets/traits.txt) : « numéro|identifiant|nom|seuil|condition » ; une ligne fausse est ignorée.

    /** Entier sans signe ni espace (NumberStyles.None en C#) ; -1 si ce n'est pas le cas. */
    private static int sansSigne(String s) {
        if (s.isEmpty() || s.length() > 9) return -1;
        for (int i = 0; i < s.length(); i++) if (s.charAt(i) < '0' || s.charAt(i) > '9') return -1;
        return Integer.parseInt(s);
    }

    public static List<Trait> lire(String texte) {
        List<Trait> l = new ArrayList<>();
        for (String brut : Presence.couper(texte.replace("\r\n", "\n"), "\n")) {
            String ligne = Presence.rogner(brut);
            if (ligne.isEmpty() || ligne.charAt(0) == '#') continue;
            String[] p = Presence.couper(ligne, "|");
            if (p.length != 5) continue;
            int n = sansSigne(p[0]);
            if (n < 1 || n > MAX) continue;
            int seuil = sansSigne(p[3]);
            if (seuil < 1) continue;
            String id = Presence.rogner(p[1]), nom = Presence.rogner(p[2]);
            List<Terme> condition = condition(Presence.rogner(p[4]));
            if (id.isEmpty() || nom.isEmpty() || condition == null) continue;
            boolean doublon = false;
            for (Trait t : l) if (t.numero == n || t.id.equals(id)) doublon = true;
            if (doublon) continue;
            l.add(new Trait(n, id, nom, seuil, condition));
        }
        l.sort((a, b) -> Integer.compare(a.numero, b.numero));
        return l;
    }

    private static final String[] OPS = {">=", "<=", "!=", "="};

    /** « pc>=1&we=1 » ; null si un terme ne se lit pas (fait inconnu, nombre attendu…). */
    public static List<Terme> condition(String texte) {
        List<Terme> l = new ArrayList<>();
        for (String brut : Presence.couper(texte, "&")) {
            String t = Presence.rogner(brut);
            String op = "";
            int i = -1;
            for (String o : OPS) {
                i = t.indexOf(o);
                if (i > 0) {
                    op = o;
                    break;
                }
            }
            if (op.isEmpty()) return null;
            String fait = t.substring(0, i), valeur = t.substring(i + op.length());
            if (NOMBRES.contains(fait)) {
                int n = sansSigne(valeur);
                if (n < 0) return null;
                l.add(new Terme(fait, op, valeur, n, false));
            } else if (TEXTES.contains(fait) && (op.equals("=") || op.equals("!="))) l.add(new Terme(fait, op, valeur, 0, true));
            else return null;
        }
        return l.isEmpty() ? null : l;
    }

    private static volatile List<Trait> tous;

    public static List<Trait> tous() {
        if (tous == null) tous = lire(ressource("/traits.txt"));
        return tous;
    }

    public static Trait trouver(String id) {
        for (Trait t : tous()) if (t.id.equals(id)) return t;
        return null;
    }

    private static String ressource(String chemin) {
        try (InputStream in = Traits.class.getResourceAsStream(chemin)) {
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

    // ---- Mesure

    /** 1 lundi … 7 dimanche (le jour 0, le 1er janvier 1970, est un jeudi). */
    public static int jourDeSemaine(int jour) {
        return (((jour + 3) % 7) + 7) % 7 + 1;
    }

    public static int lundi(int jour) {
        return jour - (jourDeSemaine(jour) - 1);
    }

    private static int nombre(Presence.FaitsDuJour f, String fait, int jour, int ecart) {
        switch (fait) {
            case "mn": return f.mn;
            case "tv": return f.tv;
            case "am": return f.am;
            case "ta": return f.ta;
            case "jx": return f.jx;
            case "ca": return f.ca;
            case "so": return f.so;
            case "pc": return f.pc;
            case "pq": return f.pq;
            case "cu": return f.cu;
            case "qu": return f.qu;
            case "ce": return f.ce;
            case "vi": return f.vi;
            case "nv": return f.nv;
            case "mg": return f.mg;
            case "ma": return f.ma;
            case "we": return jourDeSemaine(jour) >= 6 ? 1 : 0;
            case "sem": return jourDeSemaine(jour);
            case "abs": return ecart;
            default: return 0;
        }
    }

    private static String texte(Presence.FaitsDuJour f, String fait) {
        switch (fait) {
            case "ac": return f.ac;
            case "px": return f.px;
            case "cx": return f.cx;
            case "me": return f.me;
            case "cf": return f.cf;
            case "mo": return f.mo;
            case "ex": return f.ex;
            case "ob": return f.ob;
            default: return "";
        }
    }

    /** Ce jour-là remplit-il la condition ? ecart : jours écoulés depuis la page précédente du journal (0 : première page). */
    public static boolean vrai(Trait t, Presence.FaitsDuJour f, int jour, int ecart) {
        for (Terme c : t.condition) {
            boolean ok;
            if (c.texte) ok = texte(f, c.fait).equals(c.valeur) == c.op.equals("=");
            else {
                int v = nombre(f, c.fait, jour, ecart);
                switch (c.op) {
                    case ">=": ok = v >= c.nombre; break;
                    case "<=": ok = v <= c.nombre; break;
                    case "=": ok = v == c.nombre; break;
                    default: ok = v != c.nombre; break;
                }
            }
            if (!ok) return false;
        }
        return true;
    }

    /** Nombre de jours du journal, de « de » à « a » compris, qui remplissent la condition. */
    public static int mesure(Trait t, TreeMap<Integer, Presence.FaitsDuJour> journal, int de, int a) {
        int n = 0, avant = Integer.MIN_VALUE;
        for (Map.Entry<Integer, Presence.FaitsDuJour> e : journal.entrySet()) {
            int jour = e.getKey();
            int ecart = avant == Integer.MIN_VALUE ? 0 : jour - avant;
            avant = jour;
            if (jour >= de && jour <= a && vrai(t, e.getValue(), jour, ecart)) n++;
        }
        return n;
    }

    public static int mesure(Trait t, TreeMap<Integer, Presence.FaitsDuJour> journal) {
        return mesure(t, journal, Integer.MIN_VALUE, Integer.MAX_VALUE);
    }

    /** Le journal tel que les traits le lisent : un jour → ses faits fusionnés (tous appareils), sans les jours vides. */
    public static TreeMap<Integer, Presence.FaitsDuJour> journal(Presence.Etat e) {
        TreeMap<Integer, Presence.FaitsDuJour> r = new TreeMap<>();
        for (String jour : e.journal.keySet()) {
            int j = Presence.jourDe(jour);
            if (j == Integer.MIN_VALUE) continue;
            Presence.FaitsDuJour f = e.faitsDu(jour);
            if (!f.vide()) r.put(j, f);
        }
        return r;
    }

    // ---- Acquis : un bit par trait. Ce que le journal donne aujourd'hui ; l'appareil le garde par « ou » (jamais perdu).

    public static long acquis(List<Trait> traits, TreeMap<Integer, Presence.FaitsDuJour> journal) {
        long bits = 0;
        for (Trait t : traits) if (mesure(t, journal) >= t.seuil) bits |= t.bit();
        return bits;
    }

    public static List<Trait> parmi(List<Trait> traits, long bits) {
        List<Trait> l = new ArrayList<>();
        for (Trait t : traits) if ((bits & t.bit()) != 0) l.add(t);
        return l;
    }

    /** Le prochain trait à annoncer (le plus petit numéro acquis et pas encore annoncé), ou null. */
    public static Trait aAnnoncer(List<Trait> traits, long acquis, long annonces) {
        List<Trait> l = parmi(traits, acquis & ~annonces);
        return l.isEmpty() ? null : l.get(0);
    }

    // ---- Dominants : trois au plus, les plus vécus récemment ; à égalité, le plus petit numéro.

    /** Vivacité d'un trait : jours remplis pendant la fenêtre, rapportés au seuil (en millièmes). */
    public static int vivacite(Trait t, TreeMap<Integer, Presence.FaitsDuJour> journal, int aujourdhui) {
        int lundi = lundi(aujourdhui);
        return mesure(t, journal, lundi - FENETRE, lundi - 1) * 1000 / t.seuil;
    }

    public static List<Trait> dominants(List<Trait> traits, long acquis, TreeMap<Integer, Presence.FaitsDuJour> journal, int aujourdhui) {
        List<Trait> l = parmi(traits, acquis);
        final Map<Trait, Integer> v = new java.util.IdentityHashMap<>();
        for (Trait t : l) v.put(t, vivacite(t, journal, aujourdhui));
        l.sort((a, b) -> {
            int x = Integer.compare(v.get(b), v.get(a));
            return x != 0 ? x : Integer.compare(a.numero, b.numero);
        });
        return new ArrayList<>(l.subList(0, Math.min(NOMBRE_DOMINANTS, l.size())));
    }

    /** Les traits dominants de Pilou sur cet appareil, aujourd'hui. Réunit ce que tous les appareils du groupe ont découvert. */
    public static List<Trait> dominants(Presence.Etat e, int aujourdhui) {
        return dominants(tous(), e.totaux().traits, journal(e), aujourdhui);
    }

    /** Découvre ce que le journal donne de nouveau ; vrai si un trait vient d'être acquis sur cet appareil. */
    public static boolean decouvrir(Presence.Etat e) {
        long avant = e.moi.traits;
        e.moi.traits |= acquis(tous(), journal(e));
        return e.moi.traits != avant;
    }

    // ---- Texte des bits (message entre appareils, fichier d'état) : hexadécimal, « 0 » si rien.

    public static String hex(long bits) {
        return Long.toHexString(bits);
    }

    public static long deHex(String s) {
        if (s.isEmpty() || s.length() > 15) return 0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) return 0;
        }
        return Long.parseLong(s, 16) & ((1L << MAX) - 1);
    }
}
