package fr.pilou.compagnon;

import fr.pilou.compagnon.Sprites.Sprite;

import java.util.AbstractList;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;

/**
 * Le théâtre des campagnes (docs/SCENES.md) : la scène vivante de la page Aventure. Un décor fin (192 × 80) où vivent
 * le mini-Pilou, des acteurs d'ambiance et les effets de réaction aux clics. Tout est calculé comme dans
 * outils/sprites/theatre.py (référence) et Theatre.cs : arithmétique entière, tables, même ordre des opérations ;
 * TheatreTest.java relit outils/sprites/theatre-reference.txt. Sans Android : la vue ne fait que peindre l'image.
 * Java tronque les divisions vers zéro, comme C# et comme la fonction div de la référence.
 */
public final class Theatre {
    public static final int W = 192, H = 80;
    public static final int PAS = 83;                  // douze images par seconde
    public static final int VITESSE = 24;              // marche de Pilou, pixels fins par seconde
    public static final int ENTREE = -14, SORTIE_D = 206, SORTIE_G = -14;
    public static final String ID_PILOU = "scene-pilou";
    public static final int PILOU_X = 17, PILOU_Y = 33;  // ancre du sprite : centre, ligne des pieds
    private static final int REGARD_CYCLE = 7000, REGARD_DEBUT = 3000, REGARD_DUREE = 1200;
    private static final int VOL_CYCLE = 1700, VOL_POSE = 1190, FUITE_VOL = 1500, FUITE_ABSENT = 6000;
    public static final int CLICS_MAX = 24;
    // Le personnage en pied : il entre par la droite, se tient sur `interlocuteur`, sautille quand on le touche.
    private static final int VITESSE_PERSO = 48, PERSO_CYCLE = 8000, PERSO_SAUT = 5000;
    private static final int ENTREE_PERSO = W + 18;
    private static final int[] SAUT_PERSO = {0, -2, -4, -5, -4, -2, 0};

    private static final int[] SINUS = {
        0, 195, 383, 556, 707, 831, 924, 981, 1000, 981, 924, 831, 707, 556, 383, 195,
        0, -195, -383, -556, -707, -831, -924, -981, -1000, -981, -924, -831, -707, -556, -383, -195,
    };
    private static final int[] LISSE_T = {0, 11, 42, 89, 156, 229, 316, 410, 500, 590, 684, 771, 844, 911, 958, 989, 1000};

    public static final String[] HUMEURS = {"joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre"};

    private static long div(long a, long b) {
        return a / b;
    }

    private static int lisse(long num, long den) {
        if (den <= 0 || num >= den) return 1000;
        if (num <= 0) return 0;
        return LISSE_T[(int) (num * 16 / den)];
    }

    private static int sin(long i) {
        return SINUS[(int) (i % 32)];
    }

    private static boolean dans(String s, String... l) {
        for (String x : l) if (x.equals(s)) return true;
        return false;
    }

    // ---- Scènes : assets/scenes/<campagne>.txt

    public static final class Acteur {
        public final String sprite, comportement;
        public final int[] p;

        Acteur(String sprite, String comportement, int[] p) {
            this.sprite = sprite;
            this.comportement = comportement;
            this.p = p;
        }
    }

    public static final class Sensible {
        public final String nom, reaction;
        public final int x0, y0, x1, y1;
        public final int[] p;

        Sensible(String nom, int x0, int y0, int x1, int y1, String reaction, int[] p) {
            this.nom = nom;
            this.x0 = x0;
            this.y0 = y0;
            this.x1 = x1;
            this.y1 = y1;
            this.reaction = reaction;
            this.p = p;
        }
    }

    public static final class Scene {
        public String nom = "";
        /** x0, y0, x1, y1 : la ligne du sol, de gauche à droite. */
        public int[] sol = {0, 78, W, 78};
        public int place = 24;
        public int interlocuteur = 150;
        /** L'accessoire dont parle le texte (x0, y0, x1, y1), ou null : le panneau des choix du PC l'évite. */
        public int[] cle;
        public final List<Acteur> acteurs = new ArrayList<>();
        public final List<Sensible> sensibles = new ArrayList<>();
    }

    private static List<String[]> mots(String texte) {
        List<String[]> r = new ArrayList<>();
        for (String brut : texte.replace("\r", "").split("\n")) {
            int d = brut.indexOf('#');
            String l = (d >= 0 ? brut.substring(0, d) : brut).trim();
            if (!l.isEmpty()) r.add(l.split(" +"));
        }
        return r;
    }

    private static int ent(String s) {
        return Integer.parseInt(s);
    }

    private static int[] ents(String[] m, int depuis) {
        int[] r = new int[Math.max(0, m.length - depuis)];
        for (int i = 0; i < r.length; i++) r[i] = ent(m[depuis + i]);
        return r;
    }

    public static Map<String, Scene> lireScenes(String texte) {
        Map<String, Scene> scenes = new HashMap<>();
        Scene sc = null;
        for (String[] m : mots(texte)) {
            if (m[0].equals("scene")) {
                sc = new Scene();
                sc.nom = m[1];
                scenes.put(m[1], sc);
            } else if (sc == null) {
                continue;
            } else if (m[0].equals("sol")) {
                sc.sol = new int[]{ent(m[1]), ent(m[2]), ent(m[3]), ent(m[4])};
            } else if (m[0].equals("place")) {
                sc.place = ent(m[1]);
            } else if (m[0].equals("interlocuteur")) {
                sc.interlocuteur = ent(m[1]);
            } else if (m[0].equals("cle")) {
                sc.cle = new int[]{ent(m[1]), ent(m[2]), ent(m[3]), ent(m[4])};
            } else if (m[0].equals("acteur")) {
                sc.acteurs.add(new Acteur("acteur-" + m[1], m[2], ents(m, 3)));
            } else if (m[0].equals("sensible")) {
                sc.sensibles.add(new Sensible(m[1], ent(m[2]), ent(m[3]), ent(m[4]), ent(m[5]), m[6], ents(m, 7)));
            }
        }
        return scenes;
    }

    public static int sol(Scene sc, int x) {
        int x0 = sc.sol[0], y0 = sc.sol[1], x1 = sc.sol[2], y1 = sc.sol[3];
        if (x <= x0 || x1 == x0) return y0;
        if (x >= x1) return y1;
        return y0 + (int) div((long) (y1 - y0) * (x - x0), x1 - x0);
    }

    // ---- Animations nommées : assets/scenes/animations.txt

    public static final class Anim {
        public final int premiere, nombre, pas;
        public final boolean boucle;

        Anim(int premiere, int nombre, int pas, boolean boucle) {
            this.premiere = premiere;
            this.nombre = nombre;
            this.pas = pas;
            this.boucle = boucle;
        }

        public int duree() {
            return nombre * pas;
        }

        public int image(long dt) {
            if (dt < 0) dt = 0;
            long k = dt / pas;
            return premiere + (int) (boucle ? k % nombre : Math.min(k, nombre - 1));
        }
    }

    public static Map<String, Map<String, Anim>> lireAnimations(String texte) {
        Map<String, Map<String, Anim>> a = new HashMap<>();
        for (String[] m : mots(texte)) {
            if (m.length < 6) continue;
            Map<String, Anim> d = a.get(m[0]);
            if (d == null) a.put(m[0], d = new HashMap<>());
            d.put(m[1], new Anim(ent(m[2]), ent(m[3]), ent(m[4]), m[5].equals("boucle")));
        }
        return a;
    }

    // ---- Événements : entree, depart (a : +1 droite, -1 gauche), humeur (humeur), parle (a : fin de la réplique),
    // perso (humeur : le sprite du personnage en pied, "" : plus personne), parle-perso (a : fin de sa réplique),
    // clic (a, b : point touché en pixels du décor). Toujours ajoutés dans l'ordre du temps.

    public static final class Evenement {
        public final long t, a, b;
        public final String sorte, humeur;

        public Evenement(long t, String sorte) {
            this(t, sorte, 0, 0, "");
        }

        public Evenement(long t, String sorte, long a, long b) {
            this(t, sorte, a, b, "");
        }

        public Evenement(long t, String sorte, long a, long b, String humeur) {
            this.t = t;
            this.sorte = sorte;
            this.a = a;
            this.b = b;
            this.humeur = humeur;
        }

        public static Evenement humeur(long t, String humeur) {
            return new Evenement(t, "humeur", 0, 0, humeur);
        }
    }

    /** Ce que la scène sait calculer : la scène, les animations, le sprite fin de chaque id (acteurs, Pilou).
     *  Les clics déjà résolus sont gardés (la liste d'événements ne fait que s'allonger). */
    public static final class Contexte {
        public final Scene scene;
        public final Map<String, Anim> p;
        public final Map<String, Map<String, Anim>> anims;
        public final Function<String, Sprite> sprites;
        private final Map<Integer, Cible> cibles = new HashMap<>();
        private int evtsVus = -1;
        private List<Evenement> liste;

        public Contexte(Scene scene, Map<String, Map<String, Anim>> anims, Function<String, Sprite> sprites) {
            this.scene = scene;
            Map<String, Anim> pi = anims.get(ID_PILOU);
            this.p = pi != null ? pi : new HashMap<String, Anim>();
            this.anims = anims;
            this.sprites = sprites;
        }

        public int duree(String sid) {
            Sprite s = sprites.apply(sid);
            return s != null ? s.duree : 100;
        }

        /** Le clic evts[k] ne dépend que de ce qui le précède : on le garde tant que la liste de base ne change pas en
         *  amont (une nouvelle liste, ou une liste raccourcie, vide le cache). */
        Cible cibleDe(List<Evenement> evts, int k) {
            List<Evenement> base = evts instanceof Prefixe ? ((Prefixe) evts).base : evts;
            if (base != liste || base.size() < evtsVus) {
                cibles.clear();
                liste = base;
            }
            evtsVus = base.size();
            Cible c = cibles.get(k);
            if (c != null) return c;
            Evenement e = evts.get(k);
            c = cibleA(this, new Prefixe(evts, k), e.t, (int) e.a, (int) e.b);
            cibles.put(k, c);
            return c;
        }
    }

    /** Les n premiers événements d'une liste, sans copie. */
    private static final class Prefixe extends AbstractList<Evenement> {
        final List<Evenement> base;
        private final int n;

        Prefixe(List<Evenement> l, int n) {
            this.base = l instanceof Prefixe ? ((Prefixe) l).base : l;
            this.n = n;
        }

        @Override
        public int size() {
            return n;
        }

        @Override
        public Evenement get(int i) {
            return base.get(i);
        }
    }

    static final class Cible {
        final String sorte, reaction;
        final int i, x;

        Cible(String sorte, int i, String reaction, int x) {
            this.sorte = sorte;
            this.i = i;
            this.reaction = reaction;
            this.x = x;
        }
    }

    private static List<Integer> clics(List<Evenement> evts) {
        List<Integer> c = new ArrayList<>();
        for (int i = 0; i < evts.size(); i++) if (evts.get(i).sorte.equals("clic")) c.add(i);
        return c.size() > CLICS_MAX ? new ArrayList<>(c.subList(c.size() - CLICS_MAX, c.size())) : c;
    }

    private static String face(String humeur) {
        return humeur.isEmpty() || humeur.equals("neutre") || !dans(humeur, HUMEURS) ? "repos" : "repos-" + humeur;
    }

    // ---- Le mini-Pilou : (x au centre, y la ligne des pieds, image, miroir, visible)

    public static final class EtatPilou {
        public final int x, y, image;
        public final boolean miroir, visible;

        EtatPilou(int x, int y, int image, boolean miroir, boolean visible) {
            this.x = x;
            this.y = y;
            this.image = image;
            this.miroir = miroir;
            this.visible = visible;
        }

        @Override
        public boolean equals(Object o) {
            if (!(o instanceof EtatPilou)) return false;
            EtatPilou e = (EtatPilou) o;
            return x == e.x && y == e.y && image == e.image && miroir == e.miroir && visible == e.visible;
        }

        @Override
        public int hashCode() {
            return Arrays.hashCode(new int[]{x, y, image, miroir ? 1 : 0, visible ? 1 : 0});
        }

        @Override
        public String toString() {
            return "EtatPilou(" + x + ", " + y + ", " + image + ", " + miroir + ", " + visible + ")";
        }
    }

    /** L'action en cours de Pilou et ce qui s'y rattache (x, parti) : l'état que la boucle des événements fait avancer. */
    private static final class Marche {
        String sorte = "";   // "" : aucune ; "marche" ; "anim"
        long t0;
        int x0, x1;
        String nom;
        long duree;
        int x;
        boolean parti;

        void action(String sorte, long t0, int x0, int x1, String nom, long duree) {
            this.sorte = sorte;
            this.t0 = t0;
            this.x0 = x0;
            this.x1 = x1;
            this.nom = nom;
            this.duree = duree;
        }

        void finir(long jusque) {
            if (sorte.equals("marche")) {
                long fait = (jusque - t0) * VITESSE / 1000;
                if (fait >= Math.abs(x1 - x0)) {
                    x = x1;
                    parti = x1 >= SORTIE_D || x1 <= SORTIE_G;
                    sorte = "";
                }
            } else if (sorte.equals("anim") && jusque - t0 >= duree) {
                sorte = "";
            }
        }

        int position(long jusque) {
            if (!sorte.equals("marche")) return x;
            long fait = (jusque - t0) * VITESSE / 1000;
            return (int) (x1 >= x0 ? x0 + fait : x0 - fait);
        }
    }

    public static EtatPilou pilou(Contexte cx, List<Evenement> evts, long t) {
        return pilou(cx, evts, t, 0, Animations.COMPLETES);
    }

    public static EtatPilou pilou(Contexte cx, List<Evenement> evts, long t, int regard, String niveau) {
        Scene sc = cx.scene;
        Map<String, Anim> P = cx.p;
        int x0 = sc.place;
        String humeur = "neutre";
        if (!niveau.equals(Animations.COMPLETES)) {
            for (Evenement e : evts) if (e.t <= t && e.sorte.equals("humeur")) humeur = e.humeur;
            int im = P.get(face(humeur)).premiere;
            if (niveau.equals(Animations.REDUITES) && Animations.cligne(t)) im = P.get("cligne").premiere;
            return new EtatPilou(x0, sol(sc, x0), im, x0 > W / 2, true);
        }
        Marche m = new Marche();
        m.x = x0;
        List<long[]> paroles = new ArrayList<>();
        Set<Integer> vus = new HashSet<>(clics(evts));
        int nPilou = 0;
        for (int ie = 0; ie < evts.size(); ie++) {
            Evenement e = evts.get(ie);
            if (e.t > t) break;
            m.finir(e.t);
            switch (e.sorte) {
                case "entree": {
                    int xe = e.a != 0 ? (int) e.a : ENTREE;     // a : d'où il entre (0 : du bord gauche)
                    m.x = xe;
                    m.parti = false;
                    m.action("marche", e.t, xe, sc.place, null, 0);
                    break;
                }
                case "depart": {
                    m.x = m.position(e.t);
                    m.action("marche", e.t, m.x, e.a >= 0 ? SORTIE_D : SORTIE_G, null, 0);
                    break;
                }
                case "humeur":
                    humeur = dans(e.humeur, HUMEURS) ? e.humeur : "neutre";
                    if ((m.sorte.isEmpty() || m.sorte.equals("anim")) && (humeur.equals("joie") || humeur.equals("surpris")))
                        m.action("anim", e.t, 0, 0, humeur, P.get(humeur).duree());
                    break;
                case "parle":
                    paroles.clear();                            // une nouvelle réplique remplace la précédente
                    paroles.add(new long[]{e.t, e.a});
                    break;
                case "clic": {
                    if (!vus.contains(ie)) break;
                    if (m.parti || m.sorte.equals("marche")) break;
                    Cible c = cx.cibleDe(evts, ie);
                    if (c.sorte.equals("pilou")) {
                        String nom = nPilou % 2 == 0 ? "joie" : "coucou";
                        nPilou++;
                        m.action("anim", e.t, 0, 0, nom, P.get(nom).duree());
                    } else if (c.sorte.equals("sensible") && c.reaction.equals("bulle")) {
                        m.action("anim", e.t, 0, 0, "surpris", P.get("surpris").duree() + 1200);
                    } else if (c.sorte.equals("sensible") || c.sorte.equals("acteur") || c.sorte.equals("perso")) {
                        m.action("anim", e.t, 0, 0, c.x >= m.x ? "regard-d" : "regard-g", 900);
                    }
                    break;
                }
                default:
                    break;
            }
        }
        m.finir(t);
        int x = m.x;
        if (m.parti) return new EtatPilou(x, sol(sc, x), P.get(face(humeur)).premiere, false, false);
        if (m.sorte.equals("marche")) {
            int px = m.position(t);
            return new EtatPilou(px, sol(sc, px), P.get("marche").image(t - m.t0), m.x1 < m.x0, true);
        }
        boolean miroir = x > W / 2;
        int y = sol(sc, x);
        if (m.sorte.equals("anim")) {
            String nom = m.nom != null ? m.nom : "repos";
            if (nom.equals("surpris") && t - m.t0 >= P.get("surpris").duree())
                return new EtatPilou(x, y, P.get("repos-peur").image(t - m.t0), miroir, true);
            if (nom.equals("regard-d") || nom.equals("regard-g")) return new EtatPilou(x, y, P.get(nom).premiere, false, true);
            return new EtatPilou(x, y, P.get(nom).image(t - m.t0), miroir, true);
        }
        for (long[] pa : paroles)
            if (pa[0] <= t && t < pa[1]) return new EtatPilou(x, y, P.get("parle").image(t - pa[0]), miroir, true);
        if (Animations.cligne(t)) return new EtatPilou(x, y, P.get("cligne").premiere, miroir, true);
        if (regard != 0) return new EtatPilou(x, y, P.get(regard > 0 ? "regard-d" : "regard-g").premiere, false, true);
        long cy = t / REGARD_CYCLE, u = t % REGARD_CYCLE;
        if (Animations.hasard(cy, 11, 3) < 4000 && u >= REGARD_DEBUT && u < REGARD_DEBUT + REGARD_DUREE) {
            String nom = Animations.hasard(cy, 12, 3) < 5000 ? "regard-g" : "regard-d";
            return new EtatPilou(x, y, P.get(nom).premiere, false, true);
        }
        return new EtatPilou(x, y, P.get(face(humeur)).image(t), miroir, true);
    }

    // ---- Le personnage en pied

    private static int xEntree(Scene sc, long tIn, long t) {
        return (int) Math.max(sc.interlocuteur, ENTREE_PERSO - (t - tIn) * VITESSE_PERSO / 1000);
    }

    /** Ce que les événements « perso » et « parle-perso » ont fait jusqu'à t. */
    private static final class EtatPerso {
        String cur = "";
        long tIn;
        String sortieSid;      // celui qui s'en va (null : personne)
        long sortieT;
        int sortieX;
        final List<long[]> paroles = new ArrayList<>();
    }

    private static EtatPerso etatPerso(Scene sc, List<Evenement> evts, long t) {
        EtatPerso r = new EtatPerso();
        for (Evenement e : evts) {
            if (e.t > t) break;
            if (e.sorte.equals("perso")) {
                String sid = e.humeur == null ? "" : e.humeur;
                if (sid.equals(r.cur)) continue;
                // Remplacé par un autre : il s'efface ; plus personne : il ressort en marchant.
                if (!r.cur.isEmpty() && sid.isEmpty()) {
                    r.sortieSid = r.cur;
                    r.sortieT = e.t;
                    r.sortieX = xEntree(sc, r.tIn, e.t);
                } else {
                    r.sortieSid = null;
                }
                r.cur = sid;
                r.tIn = e.t;
                r.paroles.clear();
            } else if (e.sorte.equals("parle-perso")) {
                r.paroles.clear();
                r.paroles.add(new long[]{e.t, e.a});
            }
        }
        return r;
    }

    /** (sprite, image, x, y, miroir) du personnage en pied, ou null. Il regarde vers la place de Pilou. */
    public static Pose perso(Contexte cx, List<Evenement> evts, long t, String niveau) {
        Scene sc = cx.scene;
        EtatPerso st = etatPerso(sc, evts, t);
        boolean miroir = sc.place > sc.interlocuteur;
        if (!niveau.equals(Animations.COMPLETES)) {
            Map<String, Anim> ar = st.cur.isEmpty() ? null : cx.anims.get(st.cur);
            if (ar == null) return null;
            int im = niveau.equals(Animations.REDUITES) && Animations.cligne(t + 1700) && ar.containsKey("cligne") ? ar.get("cligne").premiere : ar.get("repos").premiere;
            return new Pose(st.cur, im, sc.interlocuteur, sol(sc, sc.interlocuteur), miroir);
        }
        if (st.cur.isEmpty()) {
            Map<String, Anim> a0 = st.sortieSid == null ? null : cx.anims.get(st.sortieSid);
            if (a0 == null) return null;
            long xs = st.sortieX + (t - st.sortieT) * VITESSE_PERSO / 1000;
            if (xs > W + 30) return null;
            int k0 = (int) (t / 166 % 2);
            return new Pose(st.sortieSid, a0.get("repos").image(t), (int) xs, sol(sc, (int) Math.min(xs, W)) - k0, false);
        }
        Map<String, Anim> a = cx.anims.get(st.cur);
        if (a == null) return null;
        int x = xEntree(sc, st.tIn, t), y = sol(sc, x);
        if (x > sc.interlocuteur) {
            int k = (int) (t / 166 % 2);     // il trottine : un pixel de haut une image sur deux
            return new Pose(st.cur, a.get("repos").image(t), x, y - k, miroir);
        }
        // Un saut quand on le touche, ou de temps en temps.
        long saut = -1;
        for (int k : clics(evts)) {
            long tc = evts.get(k).t;
            if (st.tIn <= tc && tc <= t && t - tc < SAUT_PERSO.length * PAS && cx.cibleDe(evts, k).sorte.equals("perso")) saut = (t - tc) / PAS;
        }
        long cy = t / PERSO_CYCLE, u = t % PERSO_CYCLE;
        if (saut < 0 && t - st.tIn > PERSO_CYCLE && Animations.hasard(cy, 21, 7) < 3000 && u >= PERSO_SAUT && u < PERSO_SAUT + SAUT_PERSO.length * PAS)
            saut = (u - PERSO_SAUT) / PAS;
        if (saut >= 0) return new Pose(st.cur, a.get("repos").premiere, x, y + SAUT_PERSO[(int) saut], miroir);
        Anim pa = a.get("parle");
        for (long[] pr : st.paroles)
            if (pr[0] <= t && t < pr[1] && pa != null) return new Pose(st.cur, pa.image(t - pr[0]), x, y, miroir);
        Anim c2 = a.get("cligne");
        if (c2 != null && Animations.cligne(t + 1700)) return new Pose(st.cur, c2.premiere, x, y, miroir);
        return new Pose(st.cur, a.get("repos").image(t), x, y, miroir);
    }

    // ---- Les acteurs : (x au centre, y la ligne du bas, image ou -1 s'il est absent, miroir)

    public static final class Pose {
        public final String sprite;
        public final int image, x, y;
        public final boolean miroir;

        public Pose(String sprite, int image, int x, int y, boolean miroir) {
            this.sprite = sprite;
            this.image = image;
            this.x = x;
            this.y = y;
            this.miroir = miroir;
        }
    }

    private static List<Long> fuites(Contexte cx, List<Evenement> evts, int i, long t) {
        List<Long> f = new ArrayList<>();
        for (int k : clics(evts)) {
            if (evts.get(k).t > t) continue;
            Cible c = cx.cibleDe(evts, k);
            if (c.sorte.equals("acteur") && c.i == i) f.add(evts.get(k).t);
        }
        return f;
    }

    /** {x, y, miroir (0 ou 1)} du vol d'un acteur à l'instant t. */
    private static int[] vol(int[] p, long t) {
        int x0 = p[0], y0 = p[1], x1 = p[2], y1 = p[3], g = p[4];
        long c = t / VOL_CYCLE, u = t % VOL_CYCLE;
        int ax = x0 + Animations.hasard(c, 1, g) * (x1 - x0) / 10000;
        int ay = y0 + Animations.hasard(c, 2, g) * (y1 - y0) / 10000;
        int bx = x0 + Animations.hasard(c + 1, 1, g) * (x1 - x0) / 10000;
        int by = y0 + Animations.hasard(c + 1, 2, g) * (y1 - y0) / 10000;
        int f = u < VOL_POSE ? 0 : lisse(u - VOL_POSE, VOL_CYCLE - VOL_POSE);
        int x = ax + (int) div((long) (bx - ax) * f, 1000);
        int y = ay + (int) div((long) (by - ay) * f, 1000) + (int) div(sin(t / 140), 700);
        return new int[]{x, y, bx < ax ? 1 : 0};
    }

    private static final int[] ABSENT = {0, 0, -1, 0};

    /** {x, y, image (-1 : absent), miroir (0 ou 1)}. */
    static int[] positionActeur(Contexte cx, List<Evenement> evts, int i, long t) {
        Acteur a = cx.scene.acteurs.get(i);
        int[] p = a.p;
        long duree = Math.max(1, cx.duree(a.sprite));
        List<Long> fuites = a.comportement.equals("vol") || a.comportement.equals("traverse")
                ? fuites(cx, evts, i, t) : new ArrayList<Long>();
        switch (a.comportement) {
            case "vol": {
                for (int k = fuites.size() - 1; k >= 0; k--) {
                    long tf = fuites.get(k);
                    if (t < tf + FUITE_ABSENT) {
                        if (t >= tf + FUITE_VOL) return ABSENT;
                        int[] v = vol(p, tf);
                        int d = v[0] < W / 2 ? 1 : -1;
                        return new int[]{(int) (v[0] - d * ((t - tf) * 90 / 1000)), (int) (v[1] - (t - tf) * 30 / 1000), (int) (t / duree), d > 0 ? 1 : 0};
                    }
                }
                int[] v = vol(p, t);
                return new int[]{v[0], v[1], (int) (t / duree), v[2]};
            }
            case "traverse": {
                int y0 = p[0], y1 = p[1], periode = p[2], decalage = p[3], vitesse = p[4];
                long tt = t + decalage, c = tt / periode, u = tt % periode;
                long x = -12 + u * vitesse / 1000;
                long y = y0 + Animations.hasard(c, 3, 5) * (y1 - y0) / 10000 + div(sin(t / 160), 800);
                for (long tf : fuites)
                    if ((tf + decalage) / periode == c) {
                        x += (t - tf) * 60 / 1000;
                        y -= (t - tf) * 25 / 1000;
                    }
                if (x > W + 12 || y < -8) return ABSENT;
                return new int[]{(int) x, (int) y, (int) (t / duree), 0};
            }
            case "rond": {
                long u = (t + p[3]) % p[2];
                if (u >= 5 * 280) return ABSENT;
                return new int[]{p[0], p[1], (int) (u / 280), 0};
            }
            case "saut": {
                long u = (t + p[3]) % p[2];
                if (u >= 700) return ABSENT;
                long f = u * 1000 / 700;
                long arc = 12 * 4 * f * (1000 - f) / 1000000;
                return new int[]{(int) (p[0] + 20 * f / 1000), (int) (p[1] - arc), f < 400 ? 0 : f < 600 ? 1 : 2, 0};
            }
            case "pose":
                return new int[]{p[0], p[1], (int) (t / duree), 0};
            case "flotte": {
                long u = (t + p[3]) % p[2];
                long px = p[0] + div(u * p[4], 1000) + div(sin(u / 200) * 2L, 1000);
                long py = p[1] + div(u * p[5], 1000);
                if (px < -8 || px > W + 8 || py < -8 || py > H + 8) return ABSENT;
                return new int[]{(int) px, (int) py, (int) (t / duree), 0};
            }
            case "chute": {
                long u = (t + p[3]) % p[2];
                long py = p[1] + u * 14 / 1000;
                long px = p[0] + div(sin(u / 150) * 4L, 1000);
                if (py > H + 4) return ABSENT;
                return new int[]{(int) px, (int) py, (int) (u / duree), 0};
            }
            default:
                return ABSENT;
        }
    }

    private static Cible cibleA(Contexte cx, List<Evenement> avant, long tc, int x, int y) {
        Scene sc = cx.scene;
        EtatPilou p = pilou(cx, avant, tc);
        if (p.visible && Math.abs(x - p.x) <= 10 && y >= p.y - 22 && y <= p.y + 1) return new Cible("pilou", 0, "", p.x);
        Pose pp = perso(cx, avant, tc, Animations.COMPLETES);
        if (pp != null) {
            Sprite sp = cx.sprites.apply(pp.sprite);
            int w = sp != null ? sp.w() : 24, h = sp != null ? sp.h() : 32;
            if (Math.abs(x - pp.x) <= w / 2 && y > pp.y - h && y <= pp.y) return new Cible("perso", 0, "", pp.x);
        }
        for (int i = 0; i < sc.acteurs.size(); i++) {
            String comp = sc.acteurs.get(i).comportement;
            if (!comp.equals("vol") && !comp.equals("traverse")) continue;
            int[] r = positionActeur(cx, avant, i, tc);
            if (r[2] >= 0 && Math.abs(x - r[0]) <= 6 && y >= r[1] - 7 && y <= r[1] + 2) return new Cible("acteur", i, "", 0);
        }
        for (int j = 0; j < sc.sensibles.size(); j++) {
            Sensible s = sc.sensibles.get(j);
            if (x >= s.x0 && x <= s.x1 && y >= s.y0 && y <= s.y1) return new Cible("sensible", j, s.reaction, x);
        }
        return new Cible("rien", 0, "", 0);
    }

    /** Le point touché répond-il au clic (pour la main au survol) ? */
    public static boolean repond(Contexte cx, List<Evenement> evts, long t, int x, int y) {
        return !cibleA(cx, evts, t, x, y).sorte.equals("rien");
    }

    public static List<Pose> acteurs(Contexte cx, List<Evenement> evts, long t, String niveau) {
        List<Pose> o = new ArrayList<>();
        if (!niveau.equals(Animations.COMPLETES)) return o;
        Scene sc = cx.scene;
        for (int i = 0; i < sc.acteurs.size(); i++) {
            int[] r = positionActeur(cx, evts, i, t);
            Sprite s = cx.sprites.apply(sc.acteurs.get(i).sprite);
            if (r[2] < 0 || s == null || s.images.isEmpty()) continue;
            o.add(new Pose(sc.acteurs.get(i).sprite, r[2] % s.images.size(), r[0], r[1], r[3] == 1));
        }
        return o;
    }

    private static final int[] BULLE = {0, 1, 2, 1, 2, 3, 0};

    public static List<Pose> effets(Contexte cx, List<Evenement> evts, long t, String niveau) {
        List<Pose> o = new ArrayList<>();
        if (!niveau.equals(Animations.COMPLETES)) return o;
        Scene sc = cx.scene;
        Map<Integer, Integer> ronds = new HashMap<>();
        for (int k : clics(evts)) {
            Evenement e = evts.get(k);
            long tc = e.t;
            if (tc > t) break;
            long dt = t - tc;
            Cible c = cx.cibleDe(evts, k);
            int ex = (int) e.a, ey = (int) e.b;
            if (c.sorte.equals("pilou") && dt < 350) {
                EtatPilou p = pilou(cx, new Prefixe(evts, k), tc);
                o.add(new Pose("acteur-eclats", (int) (dt / 70), p.x, p.y - 24, false));
            } else if (c.sorte.equals("sensible")) {
                int[] pr = sc.sensibles.get(c.i).p;
                boolean bulle = c.reaction.equals("bulle");
                if (bulle && dt < 1050) o.add(new Pose("acteur-bulle", BULLE[(int) (dt / 150)], pr[0], pr[1], false));
                if (bulle && dt < 1100)
                    o.add(new Pose("acteur-note", (int) (t / 180 % 2), pr[0] + 5, (int) (pr[1] - 5 - dt * 10 / 1000), false));
                if (c.reaction.equals("rond")) {
                    Integer n0 = ronds.get(c.i);
                    int n = (n0 == null ? 0 : n0) + 1;
                    ronds.put(c.i, n);
                    if (dt < 1400) o.add(new Pose("acteur-rond", (int) (dt / 280), ex, ey + 2, false));
                    if (n % 3 == 0 && dt < 700) {
                        long f = dt * 1000 / 700;
                        long arc = 12 * 4 * f * (1000 - f) / 1000000;
                        o.add(new Pose("acteur-poisson", f < 400 ? 0 : f < 600 ? 1 : 2, (int) (ex + 20 * f / 1000), (int) (ey - arc), false));
                        if (dt < 360) o.add(new Pose("acteur-plouf", (int) (dt / 90), ex, ey, false));
                    }
                    if (n % 3 == 0 && dt >= 700 && dt < 1060) o.add(new Pose("acteur-plouf", (int) ((dt - 700) / 90), ex + 20, ey, false));
                }
                if (c.reaction.equals("graines") && dt < 4000)
                    for (int g = 0; g < 5; g++) {
                        int vx = -8 - g * 3, vy = -6 + g * 2;
                        long gx = pr[0] + div(dt * vx, 1000) + div(sin(dt / 200 + g * 5) * 2L, 1000);
                        long gy = pr[1] + div(dt * vy, 1000);
                        o.add(new Pose("acteur-graine", (int) ((t / 300 + g) % 2), (int) gx, (int) gy, false));
                    }
            }
        }
        List<Pose> garde = new ArrayList<>();
        for (Pose q : o) if (cx.sprites.apply(q.sprite) != null) garde.add(q);
        return garde;
    }

    // ---- Le compositeur : décor, puis acteurs et Pilou triés par leurs pieds, puis les effets.

    /** teinte : contour, ombre, base, clair (ARGB) pour les couleurs @ du mini-Pilou. ancreX / ancreY : -1 pour le
     *  centre du bas du sprite. px : W × H pixels ARGB. */
    public static void poser(int[] px, Sprite s, int im, int x, int y, boolean miroir, int[] teinte, int ancreX, int ancreY) {
        if (s == null || s.images.isEmpty()) return;
        int n = s.images.size();
        String[] g = s.images.get(((im % n) + n) % n);
        int[] pal = s.compilee();
        int w = s.w(), h = s.h();
        int ax = ancreX >= 0 ? ancreX : w / 2, ay = ancreY >= 0 ? ancreY : h - 1;
        int ox = x - (miroir ? w - 1 - ax : ax), oy = y - ay;
        for (int j = 0; j < g.length; j++) {
            int yy = oy + j;
            if (yy < 0 || yy >= H) continue;
            String ligne = g[j];
            for (int i = 0; i < ligne.length(); i++) {
                char ch = ligne.charAt(i);
                if (ch == '.' || ch >= 128) continue;
                int xx = ox + (miroir ? w - 1 - i : i);
                if (xx < 0 || xx >= W) continue;
                int c = pal[ch];
                if (c >= 1 && c <= 4) c = teinte[c - 1] | 0xFF000000;
                int a = c >>> 24;
                if (a == 0) continue;
                int k = yy * W + xx;
                if (a == 255) {
                    px[k] = c;
                } else {
                    int d = px[k];
                    int r = (((c >>> 16) & 255) * a + ((d >>> 16) & 255) * (255 - a) + 127) / 255;
                    int v = (((c >>> 8) & 255) * a + ((d >>> 8) & 255) * (255 - a) + 127) / 255;
                    int b = ((c & 255) * a + (d & 255) * (255 - a) + 127) / 255;
                    px[k] = 0xFF000000 | r << 16 | v << 8 | b;
                }
            }
        }
    }

    public static void poser(int[] px, Sprite s, int im, int x, int y, boolean miroir, int[] teinte) {
        poser(px, s, im, x, y, miroir, teinte, -1, -1);
    }

    public static int[] composer(Contexte cx, Sprite decor, int[] teinte, List<Evenement> evts, long t, int regard, String niveau, int[] sortie) {
        return composer(cx, decor, teinte, evts, t, regard, niveau, sortie, true);
    }

    /** avecPilou : faux pendant un travelling (la vue pose Pilou elle-même par-dessus les deux décors qui glissent). */
    public static int[] composer(Contexte cx, Sprite decor, int[] teinte, List<Evenement> evts, long t, int regard, String niveau, int[] sortie,
                                 boolean avecPilou) {
        int[] px = sortie != null && sortie.length == W * H ? sortie : new int[W * H];
        Arrays.fill(px, 0xFF000000);
        if (decor != null && !decor.images.isEmpty()) {
            int k = (int) Animations.imageDecor(decor.images.size(), decor.duree, t, niveau);
            poser(px, decor, k, 0, 0, false, teinte, 0, 0);
        }
        // Tri stable par (pieds, Pilou après les acteurs à égalité, ordre d'insertion), comme la référence.
        List<Object[]> poses = new ArrayList<>();
        for (Pose a : acteurs(cx, evts, t, niveau)) poses.add(new Object[]{a.y, 0, poses.size(), a});
        Pose pp = perso(cx, evts, t, niveau);
        if (pp != null && cx.sprites.apply(pp.sprite) != null) poses.add(new Object[]{pp.y, 0, poses.size(), pp});
        EtatPilou p = pilou(cx, evts, t, regard, niveau);
        if (p.visible && avecPilou) poses.add(new Object[]{p.y, 1, poses.size(), new Pose(ID_PILOU, p.image, p.x, p.y, p.miroir)});
        Collections.sort(poses, (u, v) -> {
            int c = Integer.compare((Integer) u[0], (Integer) v[0]);
            if (c == 0) c = Integer.compare((Integer) u[1], (Integer) v[1]);
            if (c == 0) c = Integer.compare((Integer) u[2], (Integer) v[2]);
            return c;
        });
        for (Object[] o : poses) {
            Pose q = (Pose) o[3];
            if (q.sprite.equals(ID_PILOU)) poser(px, cx.sprites.apply(ID_PILOU), q.image, q.x, q.y, q.miroir, teinte, PILOU_X, PILOU_Y);
            else poser(px, cx.sprites.apply(q.sprite), q.image, q.x, q.y, q.miroir, teinte);
        }
        for (Pose q : effets(cx, evts, t, niveau)) poser(px, cx.sprites.apply(q.sprite), q.image, q.x, q.y, q.miroir, teinte);
        return px;
    }

    public static int[] composer(Contexte cx, Sprite decor, int[] teinte, List<Evenement> evts, long t) {
        return composer(cx, decor, teinte, evts, t, 0, Animations.COMPLETES, null);
    }

    /** FNV-1a 32 bits des pixels, octet de poids faible d'abord ; rendu non signé (0 à 2^32 − 1). */
    public static long fnv(int[] px) {
        int h = 0x811C9DC5;
        for (int v : px)
            for (int s = 0; s < 32; s += 8) {
                h ^= (v >>> s) & 255;
                h *= 0x01000193;
            }
        return h & 0xFFFFFFFFL;
    }

    private Theatre() {
    }
}
