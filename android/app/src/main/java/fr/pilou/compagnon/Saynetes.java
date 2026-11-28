package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Saynètes de repos (docs/SPRITES.md, « Saynètes de repos ») : la banque assets/saynetes.txt, le tirage pondéré et
 *  ce qu'une saynète impose à Pilou à chaque instant. Mêmes règles que outils/sprites/saynetes.py et Saynetes.cs, en
 *  arithmétique entière (divisions vers le bas) : saynetes-reference.txt, relu par SaynetesTest.java et
 *  SaynetesTests.cs. Aucun gain (xp, pièces) n'est lié aux saynètes. */
public final class Saynetes {
    private Saynetes() {}

    static final String[] CONTINUS = {"assis", "saut", "etire", "penche"};
    /** Un trait dominant (Traits.java) triple le poids des saynètes qui lui ressemblent : le poids seulement, aucun gain. */
    public static final int TRAIT = 3;
    private static final String[] ENTIERS = {"regard", "regard_y", "cligne", "baille", "salue"};

    /** Contexte du tirage : heure, mois (1…12), stade, objets portés, compagnon porté, main libre, tu travailles. */
    public static final class Contexte {
        final int heure, mois, stade;
        final Collection<String> objets, traits;
        final boolean compagnon, mainLibre, travail;

        public Contexte(int heure, int mois, int stade, Collection<String> objets, boolean compagnon, boolean mainLibre,
                        boolean travail) {
            this(heure, mois, stade, objets, compagnon, mainLibre, travail, Collections.<String>emptyList());
        }

        /** traits : identifiants des traits dominants (Traits.java), vide s'il n'y en a pas. */
        public Contexte(int heure, int mois, int stade, Collection<String> objets, boolean compagnon, boolean mainLibre,
                        boolean travail, Collection<String> traits) {
            this.traits = traits;
            this.heure = heure;
            this.mois = mois;
            this.stade = stade;
            this.objets = objets;
            this.compagnon = compagnon;
            this.mainLibre = mainLibre;
            this.travail = travail;
        }
    }

    /** Ce que la saynète impose : continus en millièmes (assis 0…1000, saut, étirement, penché), le reste tel quel. */
    public static final class Jeu {
        public int assis, saut, etire, penche, regard, regardY;
        public String expr = "repos";
        public boolean cligne, baille, salue;
        public List<String> objets = Collections.emptyList();
    }

    public static final class Saynete {
        public String id = "";
        public int poids, duree;
        final List<int[]> heures = new ArrayList<>();
        final List<Integer> mois = new ArrayList<>();
        int[] stades;
        String[] objetsRequis = new String[0];
        String[] traits = new String[0];
        boolean compagnon, mainLibre, repos, tourne;
        final Map<String, List<int[]>> cles = new HashMap<>();
        final Map<String, List<int[]>> entiers = new HashMap<>();
        final List<Object[]> expr = new ArrayList<>();
        final List<Object[]> objets = new ArrayList<>();

        Saynete() {
            for (String k : CONTINUS) cles.put(k, new ArrayList<int[]>());
            for (String k : ENTIERS) entiers.put(k, new ArrayList<int[]>());
        }
    }

    public static List<Saynete> lire(String texte) {
        List<Saynete> banque = new ArrayList<>();
        for (String brut : texte.replace("\r", "").split("\n")) {
            String l = brut.trim();
            if (l.isEmpty() || l.startsWith("#")) continue;
            String[] m = l.split(" +");
            if (m[0].equals("saynete")) {
                Saynete s = new Saynete();
                s.id = m[1];
                s.poids = Integer.parseInt(m[2]);
                s.duree = Integer.parseInt(m[3]);
                for (int j = 4; j < m.length; j++) {
                    String q = m[j];
                    int i = q.indexOf('=');
                    String k = i < 0 ? q : q.substring(0, i), v = i < 0 ? "" : q.substring(i + 1);
                    switch (k) {
                        case "heure":
                            for (String p : v.split(",")) {
                                String[] ab = p.split("-");
                                s.heures.add(new int[]{Integer.parseInt(ab[0]), Integer.parseInt(ab[1])});
                            }
                            break;
                        case "mois":
                            for (String x : v.split(",")) s.mois.add(Integer.parseInt(x));
                            break;
                        case "stade":
                            String[] st = v.split("-");
                            s.stades = new int[]{Integer.parseInt(st[0]), Integer.parseInt(st[1])};
                            break;
                        case "objet":
                            s.objetsRequis = v.split("\\|");
                            break;
                        case "trait":
                            s.traits = v.split("\\|");
                            break;
                        case "compagnon":
                            s.compagnon = true;
                            break;
                        case "mainlibre":
                            s.mainLibre = true;
                            break;
                        case "repos":
                            s.repos = true;
                            break;
                        case "tourne":
                            s.tourne = true;
                            break;
                        default:
                            break;
                    }
                }
                banque.add(s);
                continue;
            }
            Saynete c = banque.get(banque.size() - 1);
            int t = Integer.parseInt(m[0]);
            for (int j = 1; j < m.length; j++) {
                int i = m[j].indexOf('=');
                String k = m[j].substring(0, i), v = m[j].substring(i + 1);
                if (c.cles.containsKey(k)) c.cles.get(k).add(new int[]{t, Integer.parseInt(v)});
                else if (k.equals("objets"))
                    c.objets.add(new Object[]{t, v.equals("-") ? Collections.<String>emptyList() : Arrays.asList(v.split(","))});
                else if (k.equals("expr")) c.expr.add(new Object[]{t, v});
                else if (c.entiers.containsKey(k)) c.entiers.get(k).add(new int[]{t, Integer.parseInt(v)});
            }
        }
        return banque;
    }

    private static List<Saynete> commune;

    /** La banque embarquée (ressource /saynetes.txt) ; vide si elle manque. */
    public static synchronized List<Saynete> commune() {
        if (commune == null) commune = lire(Sprites.ressource("/saynetes.txt"));
        return commune;
    }

    static boolean permise(Saynete s, Contexte c) {
        if (!s.heures.isEmpty()) {
            boolean ok = false;
            for (int[] h : s.heures)
                ok |= h[0] <= h[1] ? h[0] <= c.heure && c.heure < h[1] : c.heure >= h[0] || c.heure < h[1];
            if (!ok) return false;
        }
        if (!s.mois.isEmpty() && !s.mois.contains(c.mois)) return false;
        if (s.stades != null && (c.stade < s.stades[0] || c.stade > s.stades[1])) return false;
        if (s.objetsRequis.length > 0) {
            boolean ok = false;
            for (String o : s.objetsRequis) ok |= c.objets.contains(o);
            if (!ok) return false;
        }
        if (s.compagnon && !c.compagnon) return false;
        if (s.mainLibre && !c.mainLibre) return false;
        return !(s.repos && c.travail);
    }

    /** Poids de la saynète dans ce contexte : triplé si elle ressemble à l'un des traits dominants. */
    static int poids(Saynete s, Contexte c) {
        for (String t : s.traits) if (c.traits.contains(t)) return s.poids * TRAIT;
        return s.poids;
    }

    /** L'identifiant tiré (u : 0…9999) parmi les saynètes permises, sauf « evite » ; "" s'il n'y en a pas. Les réactions
     *  au monde (poids 0) ne sont jamais tirées. */
    public static String tirer(List<Saynete> banque, int u, Contexte c, String evite) {
        List<Saynete> ok = new ArrayList<>();
        long total = 0;
        for (Saynete s : banque)
            if (!s.id.equals(evite) && s.poids > 0 && permise(s, c)) {
                ok.add(s);
                total += poids(s, c);
            }
        if (total == 0) return "";
        long x = Math.floorDiv(u * total, 10000);
        for (Saynete s : ok) {
            if (x < poids(s, c)) return s.id;
            x -= poids(s, c);
        }
        return ok.get(ok.size() - 1).id;
    }

    /** Éveil (saynetes.py) : sans aucune session d'IA, Pilou est éveillé ; il ne dort que si on s'absente, ou la nuit. */
    public static final int ABSENT = 10 * 60_000, ABSENT_NUIT = 2 * 60_000;

    public static boolean nuit(int heure) {
        return Math.floorMod(heure, 24) < 6;
    }

    public static boolean endormi(int heure, long inactifMs) {
        return inactifMs >= ABSENT || (nuit(heure) && inactifMs >= ABSENT_NUIT);
    }

    public static Saynete trouver(List<Saynete> banque, String id) {
        for (Saynete s : banque) if (s.id.equals(id)) return s;
        return null;
    }

    static int cles(List<int[]> table, long d) {
        if (table.isEmpty()) return 0;
        if (d <= table.get(0)[0]) return d == table.get(0)[0] ? table.get(0)[1] : 0;
        for (int i = 0; i + 1 < table.size(); i++) {
            int[] a = table.get(i), b = table.get(i + 1);
            if (d < b[0]) return (int) (a[1] + Math.floorDiv((long) (b[1] - a[1]) * (d - a[0]), (long) (b[0] - a[0])));
        }
        return table.get(table.size() - 1)[1];
    }

    private static int entier(List<int[]> table, long d) {
        int v = 0;
        for (int[] x : table) if (x[0] <= d) v = x[1];
        return v;
    }

    @SuppressWarnings("unchecked")
    private static <T> T dernier(List<Object[]> table, long d, T defaut) {
        T v = defaut;
        for (Object[] x : table) if ((Integer) x[0] <= d) v = (T) x[1];
        return v;
    }

    /** Ce que la saynète impose d ms après son début ; null si elle est finie, ou au niveau « aucune ». */
    public static Jeu jouer(Saynete s, long d, String niveau, int sens) {
        if (Animations.AUCUNE.equals(niveau) || d < 0 || d >= s.duree) return null;
        boolean completes = Animations.COMPLETES.equals(niveau);
        Jeu j = new Jeu();
        j.assis = cles(s.cles.get("assis"), d);
        j.saut = completes ? cles(s.cles.get("saut"), d) : 0;
        j.etire = completes ? cles(s.cles.get("etire"), d) : 0;
        j.penche = completes ? cles(s.cles.get("penche"), d) : 0;
        j.regard = entier(s.entiers.get("regard"), d);
        if (s.tourne && sens < 0) {
            j.regard = -j.regard;
            j.penche = -j.penche;
        }
        j.regardY = entier(s.entiers.get("regard_y"), d);
        j.cligne = entier(s.entiers.get("cligne"), d) != 0;
        j.baille = entier(s.entiers.get("baille"), d) != 0;
        j.salue = entier(s.entiers.get("salue"), d) != 0;
        j.expr = dernier(s.expr, d, "repos");
        j.objets = dernier(s.objets, d, Collections.<String>emptyList());
        return j;
    }
}
