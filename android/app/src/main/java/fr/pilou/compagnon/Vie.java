package fr.pilou.compagnon;

/**
 * Vie du personnage (docs/SPRITES.md, « Vie du personnage ») : ressorts du saut, arc du saut, antenne qui suit en
 * retard, lumière du moment, bouffées de poussière. Mêmes règles que outils/sprites/vie.py et Vie.cs, en arithmétique
 * entière (divisions vers le bas) : vie-reference.txt, relu par VieTest.java et VieTests.cs.
 * Valeurs en millièmes (hauteur : millièmes d'« ancien pixel » ; étirement et antenne : −1000 … 1000).
 * Niveau « aucune » : rien ; l'appelant garde les mouvements d'avant. Sans Android : testable sur la JVM.
 */
final class Vie {
    static final int PREP = 70, RECEPTION = 280, RETARD_ANTENNE = 60, ETIRE_VOL = 350;
    static final int APPUI = 60, ETIRE_SAUTILLE = 220, BOUFFEE_IMAGE = 80;
    private static final int[][] PREP_CLES = {{0, 0}, {40, -450}, {70, -200}};
    private static final int[][] RECEPTION_CLES = {{0, -600}, {50, -700}, {120, 260}, {190, -100}, {250, 30}, {280, 0}};
    private static final int[][] APPUI_CLES = {{0, -500}, {60, 200}};
    private static final String[] COUVERT = {"nuageux", "pluie", "averse", "orage", "neige", "brouillard"};

    /** Bouffées, en pixels de la grille 1× : {recul, hauteur, opaque (1) ou légère (0)} depuis le talon. */
    static final int POUSSIERE = 0xc0b5a690, POUSSIERE_LEGERE = 0x78b5a690;
    static final int[][][] BOUFFEES = {{{0, 0, 1}, {1, 0, 0}}, {{1, -1, 1}, {2, 0, 0}}, {{2, -1, 0}}};
    static final int[][][] BOUFFEES_ATTERRISSAGE = {{{0, 0, 1}}, {{1, 0, 1}, {1, -1, 0}}, {{2, -1, 0}}};

    private Vie() {
    }

    static int cles(int[][] table, long d) {
        if (d <= table[0][0]) return table[0][1];
        for (int i = 0; i + 1 < table.length; i++) {
            int t0 = table[i][0], v0 = table[i][1], t1 = table[i + 1][0], v1 = table[i + 1][1];
            if (d < t1) return (int) (v0 + Math.floorDiv((long) (v1 - v0) * (d - t0), (long) (t1 - t0)));
        }
        return table[table.length - 1][1];
    }

    private static int etireBond(long d, int vol) {
        if (d < 0) return 0;
        if (d < PREP) return cles(PREP_CLES, d);
        long k = d - PREP;
        if (k < vol) return (int) Math.floorDiv(ETIRE_VOL * Math.abs(vol - 2 * k), (long) vol);
        long r = k - vol;
        return r < RECEPTION ? cles(RECEPTION_CLES, r) : 0;
    }

    private static int antenne(int etireAvant) {
        return (int) Math.floorDiv(-etireAvant * 8L, 10L);
    }

    /** {hauteur, étirement, antenne} d ms après le début d'un bond de vol ms. */
    static int[] bond(long d, int vol, int haut, String niveau) {
        if (Animations.AUCUNE.equals(niveau) || d < 0 || vol <= 0) return new int[]{0, 0, 0};
        if (!Animations.COMPLETES.equals(niveau))
            return d >= vol ? new int[]{0, 0, 0} : new int[]{(int) Math.floorDiv(haut * 4L * d * (vol - d), (long) vol * vol), 0, 0};
        long k = d - PREP;
        int saut = k >= 0 && k < vol ? (int) Math.floorDiv(haut * 4L * k * (vol - k), (long) vol * vol) : 0;
        return new int[]{saut, etireBond(d, vol), antenne(etireBond(d - RETARD_ANTENNE, vol))};
    }

    static long dureeBond(int vol, String niveau) {
        if (Animations.AUCUNE.equals(niveau)) return 0;
        return Animations.COMPLETES.equals(niveau) ? PREP + vol + RECEPTION + RETARD_ANTENNE : vol;
    }

    private static int etireSautille(long d, int periode) {
        long k = Math.floorMod(d, (long) periode);
        return k < APPUI ? cles(APPUI_CLES, k) : (int) Math.floorDiv(ETIRE_SAUTILLE * Math.abs(periode - 2 * k), (long) periode);
    }

    static int[] sautille(long d, int periode, int haut, String niveau) {
        if (Animations.AUCUNE.equals(niveau) || d < 0 || periode <= 0) return new int[]{0, 0, 0};
        long k = Math.floorMod(d, (long) periode);
        int saut = (int) Math.floorDiv(haut * 4L * k * (periode - k), (long) periode * periode);
        if (!Animations.COMPLETES.equals(niveau)) return new int[]{saut, 0, 0};
        return new int[]{saut, etireSautille(d, periode), antenne(etireSautille(d - RETARD_ANTENNE, periode))};
    }

    private static int etireReception(long d) {
        return d >= 0 && d < RECEPTION ? cles(RECEPTION_CLES, d) : 0;
    }

    /** {étirement, antenne} d ms après un atterrissage (Pilou lâché qui retombe). */
    static int[] reception(long d, String niveau) {
        if (!Animations.COMPLETES.equals(niveau) || d < 0 || d >= RECEPTION + RETARD_ANTENNE) return new int[]{0, 0};
        return new int[]{etireReception(d), antenne(etireReception(d - RETARD_ANTENNE))};
    }

    /** « matin », « soir », « nuit » ou "" (plein jour, ou aube et couchant par temps couvert). */
    static String lumiere(int heure, String etat, String niveau) {
        if (Animations.AUCUNE.equals(niveau)) return "";
        int h = Math.floorMod(heure, 24);
        String m = h >= 6 && h < 9 ? "matin" : h >= 17 && h < 21 ? "soir" : h >= 21 || h < 6 ? "nuit" : "";
        if (m.isEmpty()) return "";
        if (!m.equals("nuit")) for (String c : COUVERT) if (c.equals(etat)) return "";
        return m;
    }

    /** Une couleur ARGB mêlée à la lumière du moment ; l'alpha est gardé. */
    static int eclairer(int c, String moment) {
        int vers, cent;
        switch (moment == null ? "" : moment) {
            case "matin": vers = 0xffffd8b0; cent = 10; break;
            case "soir": vers = 0xffb98ad9; cent = 16; break;
            case "nuit": vers = 0xff1d2448; cent = 18; break;
            default: return c;
        }
        int r = c & 0xff000000;
        for (int dec = 16; dec >= 0; dec -= 8) {
            int x = (c >> dec) & 0xff, y = (vers >> dec) & 0xff;
            r |= (x + Math.floorDiv((y - x) * cent, 100)) << dec;
        }
        return r;
    }

    static int[] eclairer(int[] te, String moment) {
        int[] o = new int[te.length];
        for (int i = 0; i < te.length; i++) o[i] = eclairer(te[i], moment);
        return o;
    }

    /** Image (0 à 2 ; −1 : rien) de la bouffée du pied arrière : une tous les deux pas, quand il se pose. */
    static int bouffee(long t, int cadence, int sens) {
        if (cadence <= 0) return -1;
        int arriere = sens >= 0 ? 0 : 1;
        long age = Math.floorMod(t - (long) cadence * (1 - arriere), 2L * cadence);
        return age < 3 * BOUFFEE_IMAGE ? (int) (age / BOUFFEE_IMAGE) : -1;
    }

    static int bouffeeAtterrissage(long d) {
        return d >= 0 && d < 3 * BOUFFEE_IMAGE ? (int) (d / BOUFFEE_IMAGE) : -1;
    }
}
