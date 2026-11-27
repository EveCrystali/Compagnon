package fr.pilou.compagnon;

/**
 * Animations des campagnes (docs/SPRITES.md, « Animations des campagnes ») : les règles communes au PC et au téléphone,
 * en arithmétique entière (même résultat partout). Référence : outils/sprites/animations.py et son fichier
 * outils/sprites/animations-reference.txt, relu par AnimationsTest.java et AnimationsCampagneTests.cs.
 * Sans Android : les vues (ScenesAnimees.java) s'en servent pour choisir les images, écrire lettre à lettre, enchaîner
 * les décors et animer le fond.
 */
final class Animations {
    static final String COMPLETES = "completes", REDUITES = "reduites", AUCUNE = "aucune";
    static final String[] NIVEAUX = {COMPLETES, REDUITES, AUCUNE};

    static final int RESPIRATION = 900, CLIGNE_PERIODE = 4300, CLIGNE_DUREE = 150, PAS_PAROLE = 140;
    private static final int[] PAROLE = {3, 4, 3, 0};
    static final int PAR_LETTRE = 22, PAUSE_POINT = 230, PAUSE_VIRGULE = 90, DUREE_MAX = 5200;
    static final int TRANSITION = 360, VOLET_BLOC = 8;

    /** Le niveau effectif : celui du réglage, ou « aucune » si le système demande moins d'animations. */
    static String niveau(String reglage, boolean systeme) {
        String r = COMPLETES;
        for (String n : NIVEAUX) if (n.equals(reglage)) r = n;
        return systeme ? r : AUCUNE;
    }

    static long imageDecor(int n, int duree, long t, String niveau) {
        if (!COMPLETES.equals(niveau) || n <= 1 || duree <= 0 || t < 0) return 0;
        return t / duree % n;
    }

    static boolean cligne(long t) {
        return t >= 0 && t % CLIGNE_PERIODE >= CLIGNE_PERIODE - CLIGNE_DUREE;
    }

    /** Image d'un portrait : 0 et 1 repos (respiration), 2 yeux fermés, 3 et 4 parole (portraits_campagnes.py). */
    static int imagePortrait(int n, long t, boolean parle, String niveau) {
        if (n <= 1 || AUCUNE.equals(niveau) || t < 0) return 0;
        if (n > 2 && cligne(t)) return 2;
        if (!COMPLETES.equals(niveau)) return 0;
        if (parle && n >= 5) return PAROLE[(int) (t / PAS_PAROLE % PAROLE.length)];
        return (int) (t / RESPIRATION % 2);
    }

    private static int cout(char c) {
        switch (c) {
            case '.': case '!': case '?': case '…': return PAR_LETTRE + PAUSE_POINT;
            case ',': case ';': case ':': return PAR_LETTRE + PAUSE_VIRGULE;
            default: return PAR_LETTRE;
        }
    }

    private static long brut(String texte) {
        long s = 0;
        for (int i = 0; i < texte.length(); i++) s += cout(texte.charAt(i));
        return s;
    }

    static long dureeEcriture(String texte) {
        return Math.min(brut(texte), DUREE_MAX);
    }

    /** Lettres écrites après ms : une lettre, une petite pause aux virgules, une plus longue aux points. */
    static int lettres(String texte, long ms) {
        if (ms <= 0) return 0;
        long b = brut(texte);
        if (b <= 0) return texte.length();
        long total = Math.min(b, DUREE_MAX), lim = ms * b, acc = 0;
        for (int i = 0; i < texte.length(); i++) {
            acc += cout(texte.charAt(i)) * total;
            if (acc > lim) return i;
        }
        return texte.length();
    }

    /** Les « … » de Pilou qui écrit, avant un message nouveau (ms). */
    static int attente(String texte) {
        return Math.max(600, Math.min(1500, 450 + 3 * texte.length()));
    }

    private static final int[][] BAYER = {{0, 8, 2, 10}, {12, 4, 14, 6}, {3, 11, 1, 9}, {15, 7, 13, 5}};

    /** Volet pixelisé : ordre d'apparition d'un bloc (dix-millièmes) ; montré quand ordre &lt; progression × 10000. */
    static int ordreVolet(int bx, int by, int nbx) {
        int trame = (BAYER[by % 4][bx % 4] * 2 + 1) * 10000 / 32;
        int balaye = bx * 10000 / Math.max(1, nbx - 1);
        return (trame * 6 + balaye * 4) / 10;
    }

    // ---- Fond animé : ton et heure

    static String moment(int heure) {
        if (heure >= 6 && heure < 11) return "matin";
        if (heure >= 11 && heure < 17) return "jour";
        if (heure >= 17 && heure < 21) return "soir";
        return "nuit";
    }

    private static String[] fond(String ton) {
        switch (ton == null ? "" : ton) {
            case "humour": return new String[]{"#1c2448", "#3a3263", "#ffc89a"};
            case "mystere": return new String[]{"#0b1022", "#1d2448", "#a9bbd8"};
            case "emotion": return new String[]{"#1d2240", "#4a3f66", "#f2c6d6"};
            case "epique": return new String[]{"#071a33", "#173d66", "#ffd29a"};
            default: return new String[]{"#151a2e", "#2d333b", "#adbac7"};
        }
    }

    private static String melange(String a, String b, int cent) {
        StringBuilder s = new StringBuilder("#");
        for (int i = 0; i < 3; i++) {
            int x = Integer.parseInt(a.substring(1 + 2 * i, 3 + 2 * i), 16), y = Integer.parseInt(b.substring(1 + 2 * i, 3 + 2 * i), 16);
            int v = x + Math.floorDiv((y - x) * cent, 100);
            s.append(String.format(java.util.Locale.ROOT, "%02x", v));
        }
        return s.toString();
    }

    /** Trois couleurs du fond (haut, bas, particules) selon le ton de la campagne et l'heure. */
    static String[] teintesFond(String ton, int heure) {
        String[] f = fond(ton);
        String m = moment(heure);
        String vers = m.equals("matin") ? "#f6c89a" : m.equals("jour") ? "#9fb4de" : m.equals("soir") ? "#d9803a" : "#05070f";
        int cent = m.equals("matin") ? 12 : m.equals("jour") ? 8 : m.equals("soir") ? 14 : 30;
        return new String[]{melange(f[0], vers, cent), melange(f[1], vers, cent), f[2]};
    }

    /** Le même bruit entier que outils/sprites/peinture.hasard, en dix-millièmes. */
    static int hasard(long i, long j, long graine) {
        long n = (i * 374761393L + j * 668265263L + graine * 2246822519L) & 0xFFFFFFFFL;
        n = ((n ^ (n >>> 13)) * 1274126177L) & 0xFFFFFFFFL;
        return (int) (((n ^ (n >>> 16)) & 0xFFFF) * 10000 / 65536);
    }

    static final int NB_PARTICULES = 14;

    /** Une particule du fond : {x, y} en dix-millièmes, opacité 0–150 ; elle naît, traverse lentement, s'efface. */
    static int[] particuleFond(String ton, int i, long t) {
        return particuleFond(ton, i, t, new int[3]);
    }

    /** Même chose, dans un tableau gardé par l'appelant (aucune allocation par image). */
    static int[] particuleFond(String ton, int i, long t, int[] r) {
        int vie, dx, dy, bal;
        switch (ton == null ? "" : ton) {
            case "humour": vie = 16000; dx = 600; dy = -3200; bal = 250; break;
            case "emotion": vie = 19000; dx = -500; dy = 2800; bal = 300; break;
            case "epique": vie = 14000; dx = 900; dy = -2400; bal = 150; break;
            default: vie = 22000; dx = 2600; dy = -300; bal = 120;
        }
        long decal = (long) hasard(i, 1, 17) * vie / 10000;
        long u = (t + decal) % vie * 10000 / vie;
        long x = hasard(i, 2, 17) + Math.floorDiv(dx * u, 10000L);
        long y = hasard(i, 3, 17) + Math.floorDiv(dy * u, 10000L);
        long tri = u * 4 % 20000;
        if (tri >= 10000) tri = 20000 - tri;
        x += Math.floorDiv(bal * (tri - 5000), 5000L);
        x = Math.floorMod(x, 10000L);
        y = Math.floorMod(y, 10000L);
        long a = Math.min(Math.min(u, 10000 - u) * 255 * 3 / 10000, 150);
        r[0] = (int) x;
        r[1] = (int) y;
        r[2] = (int) a;
        return r;
    }

    static int delaiRecompense(int i) {
        return 420 + 260 * i;
    }

    // ---- Portraits des personnages

    static String idPortrait(String campagne, String personnage, String expression) {
        return "portrait-" + campagne + "-" + personnage + (expression == null || expression.isEmpty() || expression.equals("neutre") ? "" : "-" + expression);
    }

    /** Le portrait d'un personnage : son expression si elle est dessinée, sinon son visage neutre ; null sinon. */
    static Sprites.Sprite portrait(Sprites.Banque b, String campagne, String personnage, String expression, int echelle) {
        if (b == null || personnage == null || personnage.isEmpty()) return null;
        String id = idPortrait(campagne, personnage, expression);
        if (b.get(id) == null) id = idPortrait(campagne, personnage, "");
        return b.get(id) == null ? null : b.get(id, echelle);
    }

    /** Parle-t-il dans ce message ? (une réplique entre guillemets) */
    static boolean parle(String texte) {
        return texte != null && texte.indexOf('«') >= 0;
    }

    private Animations() {
    }
}
