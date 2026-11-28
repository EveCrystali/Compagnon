package fr.pilou.compagnon;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;

/**
 * La police pixel de Pilou, sa voix écrite (docs/POLICE.md) : glyphes lus dans assets/police/*.txt (écrits par
 * outils/sprites/police.py), mise en page (largeur, coupure des lignes, espaces fines du français) identique au
 * Python et au PC (PolicePixel.cs), vérifiée par outils/sprites/police-reference.txt. Sans Android : testable.
 * Tout se compte en points de code (un emoji hors du plan de base est un seul caractère, comme en Python).
 */
public final class PolicePixel {
    /** Un glyphe : largeur en pixels 1×, rangée du haut et rangées à l'échelle de la police. */
    public static final class Glyphe {
        public final int largeur, haut;
        public final String[] rangs;

        Glyphe(int largeur, int haut, String[] rangs) {
            this.largeur = largeur;
            this.haut = haut;
            this.rangs = rangs;
        }
    }

    private final Map<Integer, Glyphe> glyphes = new HashMap<>();
    private final Map<Long, Integer> crenage = new HashMap<>();
    public int echelle = 1, hauteur = 12, ligne = 12, chasse = 1, inconnu = 6;

    private static final String AVANT_FINE = "!?;:»›", APRES_FINE = "«‹";
    private static final String INSECABLE_AVANT = AVANT_FINE + "  …,.", INSECABLE_APRES = APRES_FINE + "  ";

    private static boolean dans(String s, int c) {
        return c < 0x10000 && s.indexOf((char) c) >= 0;
    }

    public static PolicePixel lire(String contenu) {
        PolicePixel p = new PolicePixel();
        String[] lignes = contenu.replace("\r\n", "\n").split("\n", -1);
        for (int i = 0; i < lignes.length; i++) {
            String l = lignes[i];
            if (l.isEmpty() || l.startsWith("#")) continue;
            String[] t = l.trim().split(" +");
            if (t[0].equals("@")) {
                int code = Integer.parseInt(t[1], 16), larg = Integer.parseInt(t[2]), haut = Integer.parseInt(t[3]);
                List<String> rangs = new ArrayList<>();
                while (i + 1 < lignes.length && !lignes[i + 1].isEmpty()) rangs.add(lignes[++i]);
                p.glyphes.put(code, new Glyphe(larg, haut, rangs.toArray(new String[0])));
            } else if (t[0].equals("~")) {
                p.crenage.put(cle(Integer.parseInt(t[1], 16), Integer.parseInt(t[2], 16)), Integer.parseInt(t[3]));
            } else {
                int v = Integer.parseInt(t[1]);
                switch (t[0]) {
                    case "echelle": p.echelle = v; break;
                    case "hauteur": p.hauteur = v; break;
                    case "ligne": p.ligne = v; break;
                    case "chasse": p.chasse = v; break;
                    case "inconnu": p.inconnu = v; break;
                    default: break;
                }
            }
        }
        return p;
    }

    private static final Map<String, PolicePixel> CACHE = new HashMap<>();

    /** Police embarquée (« texte », « titre », et leur dessin fin « texte2x », « titre2x »), lue une fois ; null si absente. */
    public static synchronized PolicePixel ressource(String nom) {
        if (CACHE.containsKey(nom)) return CACHE.get(nom);
        PolicePixel p = null;
        try (InputStream in = PolicePixel.class.getResourceAsStream("/police/" + nom + ".txt")) {
            if (in != null) {
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] tampon = new byte[8192];
                int n;
                while ((n = in.read(tampon)) > 0) out.write(tampon, 0, n);
                p = lire(out.toString(StandardCharsets.UTF_8.name()));
            }
        } catch (IOException e) {
            p = null;
        }
        CACHE.put(nom, p);
        return p;
    }

    public static PolicePixel texte() {
        return ressource("texte");
    }

    private static long cle(int a, int b) {
        return ((long) a << 32) | (b & 0xffffffffL);
    }

    public boolean connu(int code) {
        return glyphes.containsKey(code);
    }

    public Glyphe glyphe(int code) {
        return glyphes.get(code);
    }

    public int crenage(int a, int b) {
        Integer d = crenage.get(cle(a, b));
        return d == null ? 0 : d;
    }

    public int largeurGlyphe(int code) {
        Glyphe g = glyphes.get(code);
        return g == null ? inconnu : g.largeur;
    }

    static int[] codes(String s) {
        return s.codePoints().toArray();
    }

    /** Largeur en pixels 1× d'un texte préparé, sur une seule ligne. */
    public int largeur(String s) {
        int[] c = codes(s);
        return largeur(c, c.length);
    }

    private int largeur(int[] c, int n) {
        int w = 0;
        for (int i = 0; i < n; i++) {
            if (i > 0) w += chasse + crenage(c[i - 1], c[i]);
            w += largeurGlyphe(c[i]);
        }
        return w;
    }

    private int largeur(List<Integer> c, int n) {
        int w = 0;
        for (int i = 0; i < n; i++) {
            if (i > 0) w += chasse + crenage(c.get(i - 1), c.get(i));
            w += largeurGlyphe(c.get(i));
        }
        return w;
    }

    /** Apostrophe courbe, espace fine insécable avant ! ? ; : » et après «, sans sélecteurs de variante. */
    public static String preparer(String texte) {
        int[] brut = codes(texte.replace("\r\n", "\n").replace('\r', '\n'));
        int[] t = Arrays.stream(brut).filter(c -> c != 0xFE0F && c != 0xFE0E && c != 0x200D).toArray();
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < t.length; i++) {
            int c = t[i];
            if (c == '\'') c = '’';
            if (c == ' ') {
                boolean avant = i + 1 < t.length && dans(AVANT_FINE, t[i + 1]);
                boolean apres = i > 0 && dans(APRES_FINE, t[i - 1]);
                if (avant || apres) c = 0x202F;
            }
            b.appendCodePoint(c);
        }
        return b.toString();
    }

    private static boolean espace(int c) {
        return c == ' ' || c == 0x2009;
    }

    private static String chaine(List<Integer> l) {
        StringBuilder b = new StringBuilder();
        for (int c : l) b.appendCodePoint(c);
        return b.toString();
    }

    public List<String> couper(String texte, int maxLargeur) {
        return couper(texte, maxLargeur, 0);
    }

    /**
     * Lignes d'un texte coupé à maxLargeur pixels 1× (0 : sans limite), au plus maxLignes (0 : toutes ; la dernière
     * finit alors par « … »). Même règle que mettre_en_page (outils/sprites/police.py).
     */
    public List<String> couper(String texte, int maxLargeur, int maxLignes) {
        int[] t = codes(preparer(texte));
        List<int[]> morceaux = new ArrayList<>();
        List<Integer> seps = new ArrayList<>(); // espace mangée, -1 après trait d'union, '\n', -2 fin
        List<Integer> cour = new ArrayList<>();
        for (int c : t) {
            if (espace(c) || c == '\n') {
                morceaux.add(versTableau(cour));
                seps.add(c);
                cour.clear();
            } else if (c == '-' || c == 0x2010) {
                cour.add(c);
                morceaux.add(versTableau(cour));
                seps.add(-1);
                cour.clear();
            } else cour.add(c);
        }
        morceaux.add(versTableau(cour));
        seps.add(-2);

        List<List<Integer>> lignes = new ArrayList<>();
        List<Integer> ligne = new ArrayList<>();
        int attente = 0;
        for (int k = 0; k < morceaux.size(); k++) {
            int[] m = morceaux.get(k);
            int sep = seps.get(k);
            if (m.length == 0 && espace(sep)) {
                if (!ligne.isEmpty() && attente == 0) attente = sep;
                continue;
            }
            if (m.length > 0) {
                if (ligne.isEmpty()) ligne = versListe(m);
                else {
                    List<Integer> cand = new ArrayList<>(ligne);
                    if (attente != 0) cand.add(attente);
                    cand.addAll(versListe(m));
                    if (tient(cand, cand.size(), maxLargeur)) ligne = cand;
                    else {
                        lignes.add(ligne);
                        ligne = versListe(m);
                    }
                }
                while (!tient(ligne, ligne.size(), maxLargeur) && ligne.size() > 1) {
                    int n = 1;
                    while (n < ligne.size() && tient(ligne, n + 1, maxLargeur)) n++;
                    // Jamais de « ! », « ? », « » » ni d'espace insécable en tête de ligne, ni de « « » en fin.
                    while (n > 1 && (dans(INSECABLE_AVANT, ligne.get(n)) || dans(INSECABLE_APRES, ligne.get(n - 1)))) n--;
                    lignes.add(new ArrayList<>(ligne.subList(0, n)));
                    ligne = new ArrayList<>(ligne.subList(n, ligne.size()));
                }
            }
            attente = espace(sep) ? sep : 0;
            if (sep == '\n') {
                lignes.add(ligne);
                ligne = new ArrayList<>();
            }
        }
        lignes.add(ligne);
        if (maxLignes > 0 && lignes.size() > maxLignes) {
            List<Integer> der = new ArrayList<>(lignes.get(maxLignes - 1));
            while (!der.isEmpty()) {
                List<Integer> essai = new ArrayList<>(der);
                essai.add((int) '…');
                if (tient(essai, essai.size(), maxLargeur)) break;
                der.remove(der.size() - 1);
            }
            while (!der.isEmpty()) {
                int c = der.get(der.size() - 1);
                if (!(espace(c) || c == 0x202F || c == 0xA0)) break;
                der.remove(der.size() - 1);
            }
            der.add((int) '…');
            lignes = new ArrayList<>(lignes.subList(0, maxLignes - 1));
            lignes.add(der);
        }
        List<String> out = new ArrayList<>();
        for (List<Integer> l : lignes) out.add(chaine(l));
        return out;
    }

    private boolean tient(List<Integer> s, int n, int maxLargeur) {
        return maxLargeur <= 0 || largeur(s, n) <= maxLargeur;
    }

    private static int[] versTableau(List<Integer> l) {
        int[] r = new int[l.size()];
        for (int i = 0; i < r.length; i++) r[i] = l.get(i);
        return r;
    }

    private static List<Integer> versListe(int[] t) {
        List<Integer> r = new ArrayList<>(t.length);
        for (int c : t) r.add(c);
        return r;
    }

    /** Un glyphe posé : case en pixels 1×, code, dessin (null : la police système le dessine). */
    public static final class Pose {
        public final int x, y, code;
        public final Glyphe dessin;

        Pose(int x, int y, int code, Glyphe dessin) {
            this.x = x;
            this.y = y;
            this.code = code;
            this.dessin = dessin;
        }
    }

    public List<Pose> poser(List<String> lignes) {
        List<Pose> r = new ArrayList<>();
        for (int i = 0; i < lignes.size(); i++) {
            int[] c = codes(lignes.get(i));
            int x = 0;
            for (int k = 0; k < c.length; k++) {
                if (k > 0) x += chasse + crenage(c[k - 1], c[k]);
                Glyphe g = glyphes.get(c[k]);
                r.add(new Pose(x, i * ligne, c[k], g));
                x += g == null ? inconnu : g.largeur;
            }
        }
        return r;
    }

    /** Pixels allumés {x, y}, à l'échelle de la police (dessin fin : deux fois plus de pixels). */
    public List<int[]> pixels(List<String> lignes) {
        List<int[]> r = new ArrayList<>();
        for (Pose p : poser(lignes)) {
            if (p.dessin == null) continue;
            for (int y = 0; y < p.dessin.rangs.length; y++)
                for (int k = 0; k < p.dessin.rangs[y].length(); k++)
                    if (p.dessin.rangs[y].charAt(k) == '#') r.add(new int[]{p.x * echelle + k, p.y * echelle + p.dessin.haut + y});
        }
        return r;
    }

    /** FNV-1a 32 bits des pixels allumés, en ordre de lecture (comme police.py). */
    public long empreinte(List<String> lignes) {
        TreeSet<Long> tri = new TreeSet<>();
        for (int[] p : pixels(lignes)) tri.add(((long) p[1] << 32) | p[0]);
        int h = 0x811C9DC5;
        for (long v : tri) {
            int x = (int) (v & 0xffffffffL), y = (int) (v >>> 32);
            h = (h ^ (x * 65536 + y)) * 16777619;
        }
        return h & 0xffffffffL;
    }

    /** Boîte d'un texte coupé, en pixels 1× : {la plus longue ligne, toutes les lignes}. */
    public int[] boite(List<String> lignes) {
        int w = 0;
        for (String l : lignes) w = Math.max(w, largeur(l));
        return new int[]{w, lignes.isEmpty() ? 0 : (lignes.size() - 1) * ligne + hauteur / echelle};
    }
}
