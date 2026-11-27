package fr.pilou.compagnon;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Banque de sprites partagée avec le PC : assets/ du dépôt, embarqué comme ressources Java (voir app/build.gradle) :
 * /index.txt, /sprites/&lt;id&gt;.txt, /teintes.txt, /tenues.txt, /plats.txt. Format : docs/SPRITES.md.
 * Rendu fin (grille 96 × 112) : /index2x.txt et /sprites2x/&lt;id&gt;.txt pour les sprites redessinés ; les autres sont
 * agrandis à la demande (agrandir, même règle que le PC et que outils/sprites/rendu.py).
 */
public final class Sprites {
    public static final class Sprite {
        public String id = "", slot = "objet", ancre = "aucun";
        public int dx, dy, duree;
        public boolean derriere, coiffe;
        /** Couleur par lettre : #rrggbb(aa) ou @contour / @ombre / @base / @clair. */
        public final Map<Character, String> palette = new HashMap<>();
        public final List<String[]> images = new ArrayList<>();
        /** Rendu fin : faux si ce sprite 2× vient de l'agrandissement automatique d'un sprite 1×. */
        public boolean natif = true;
        private int[] compilee;

        /** Palette prête à peindre, par lettre : ARGB ; 0 : rien ; 1 à 4 : contour, ombre, base, clair de la teinte de
         *  Pilou. Calculée une fois (le rendu ne relit pas les codes à chaque pixel). */
        public int[] compilee() {
            int[] c = compilee;
            if (c != null) return c;
            c = new int[128];
            for (Map.Entry<Character, String> e : palette.entrySet()) {
                char ch = e.getKey();
                if (ch >= 128) continue;
                switch (e.getValue()) {
                    case "@contour": c[ch] = 1; break;
                    case "@ombre": c[ch] = 2; break;
                    case "@base": c[ch] = 3; break;
                    case "@clair": c[ch] = 4; break;
                    default: c[ch] = couleur(e.getValue());
                }
            }
            compilee = c;
            return c;
        }

        public int w() {
            if (images.isEmpty()) return 0;
            int w = 0;
            for (String l : images.get(0)) w = Math.max(w, l.length());
            return w;
        }

        public int h() {
            return images.isEmpty() ? 0 : images.get(0).length;
        }

        public String[] image(double t) {
            if (images.isEmpty()) return new String[0];
            if (duree <= 0 || images.size() == 1) return images.get(0);
            return images.get((int) (Math.floor(Math.max(0, t) / duree) % images.size()));
        }
    }

    public static Sprite lire(String texte, String id) {
        Sprite s = new Sprite();
        s.id = id;
        List<String> image = new ArrayList<>();
        boolean dans = false;
        for (String brut : texte.replace("\r", "").split("\n")) {
            String ligne = brut.replaceAll("\\s+$", "");
            if (!dans) {
                if (ligne.isEmpty() || ligne.startsWith("#")) continue;
                int i = ligne.indexOf(':');
                if (i < 0) continue;
                String cle = ligne.substring(0, i).trim(), val = ligne.substring(i + 1).trim();
                switch (cle) {
                    case "images": dans = true; break;
                    case "id": s.id = val; break;
                    case "slot": s.slot = val; break;
                    case "ancre": s.ancre = val; break;
                    case "decalage": {
                        String[] p = val.split("\\s+");
                        s.dx = Integer.parseInt(p[0]);
                        s.dy = Integer.parseInt(p[1]);
                        break;
                    }
                    case "couche": s.derriere = val.equals("derriere"); break;
                    case "coiffe": s.coiffe = val.equals("oui"); break;
                    case "duree": s.duree = Integer.parseInt(val); break;
                    case "palette":
                        for (String paire : val.split("\\s+"))
                            if (paire.length() > 2 && paire.charAt(1) == '=') s.palette.put(paire.charAt(0), paire.substring(2));
                        break;
                    default: break;
                }
            } else if (ligne.equals("---")) {
                s.images.add(image.toArray(new String[0]));
                image.clear();
            } else if (!ligne.isEmpty()) {
                image.add(ligne);
            }
        }
        if (!image.isEmpty()) s.images.add(image.toArray(new String[0]));
        return s;
    }

    // ---- Agrandissement automatique (rendu fin) : même règle que rendu.agrandir (Python) et Sprite.Agrandi (C#).

    /** Clarté d'une couleur de palette : (r + v + b + 1) × (256 − alpha) ; vide : 256. Les références à la teinte de
     *  Pilou prennent les valeurs du bleu, pour que l'agrandissement ne dépende pas de la teinte portée. */
    static int clarte(String code) {
        if (code == null) return 256;
        switch (code) {
            case "@contour": code = "#1f4f8a"; break;
            case "@ombre": code = "#4a8fdc"; break;
            case "@base": code = "#6cb6ff"; break;
            case "@clair": code = "#b4dbff"; break;
            default: break;
        }
        if (code.length() < 7 || code.charAt(0) != '#') return 256;
        int c = couleur(code);
        return ((c >> 16 & 0xff) + (c >> 8 & 0xff) + (c & 0xff) + 1) * (256 - (c >>> 24));
    }

    private static char src(String[] im, int x, int y) {
        return y >= 0 && y < im.length && x >= 0 && x < im[y].length() ? im[y].charAt(x) : '.';
    }

    /**
     * Image deux fois plus grande, mêmes lettres. Règle « MMPX » (McGuire et Gagiu, 2021) : chaque pixel devient
     * 2 × 2 pixels pris parmi lui-même et ses voisins, sans flou ni nouvelle couleur ; les cernes sombres d'un pixel
     * sont gardés, les diagonales et les pentes 2:1 lissées. Le vide (« . », hors de l'image) compte comme une couleur.
     */
    static String[] agrandirImage(String[] im, Map<Character, String> palette) {
        int h = im.length, w = 0;
        for (String l : im) w = Math.max(w, l.length());
        int[] cl = new int[128];
        java.util.Arrays.fill(cl, 256);
        for (Map.Entry<Character, String> e : palette.entrySet())
            if (e.getKey() < 128) cl[e.getKey()] = clarte(e.getValue());
        String[] sortie = new String[h * 2];
        char[] haut = new char[w * 2], bas = new char[w * 2];
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                char A = src(im, x - 1, y - 1), B = src(im, x, y - 1), C = src(im, x + 1, y - 1);
                char D = src(im, x - 1, y), E = src(im, x, y), F = src(im, x + 1, y);
                char G = src(im, x - 1, y + 1), H = src(im, x, y + 1), I = src(im, x + 1, y + 1);
                char J = E, K = E, L = E, M = E;
                if (!(A == E && B == E && C == E && D == E && F == E && G == E && H == E && I == E)) {
                    char P = src(im, x, y - 2), S = src(im, x, y + 2), Q = src(im, x - 2, y), R = src(im, x + 2, y);
                    int Bl = cl[B & 127], Dl = cl[D & 127], El = cl[E & 127], Fl = cl[F & 127], Hl = cl[H & 127];
                    // Pentes 1:1 (coins arrondis, diagonales lissées).
                    if (D == B && D != H && D != F && (El >= Dl || E == A) && (E == A || E == C || E == G) && (El < Dl || A != D || E != P || E != Q)) J = D;
                    if (B == F && B != D && B != H && (El >= Bl || E == C) && (E == A || E == C || E == I) && (El < Bl || C != B || E != P || E != R)) K = B;
                    if (H == D && H != F && H != B && (El >= Hl || E == G) && (E == A || E == G || E == I) && (El < Hl || G != H || E != S || E != Q)) L = H;
                    if (F == H && F != B && F != D && (El >= Fl || E == I) && (E == C || E == G || E == I) && (El < Fl || I != H || E != R || E != S)) M = F;
                    // Croisements.
                    if (E != F && E == C && E == I && E == D && E == Q && F == B && F == H && F != src(im, x + 3, y)) K = M = F;
                    if (E != D && E == A && E == G && E == F && E == R && D == B && D == H && D != src(im, x - 3, y)) J = L = D;
                    if (E != H && E == G && E == I && E == B && E == P && H == D && H == F && H != src(im, x, y + 3)) L = M = H;
                    if (E != B && E == A && E == C && E == H && E == S && B == D && B == F && B != src(im, x, y - 3)) J = K = B;
                    if (Bl < El && E == G && E == H && E == I && E == S && E != A && E != D && E != C && E != F) J = K = B;
                    if (Hl < El && E == A && E == B && E == C && E == P && E != D && E != G && E != I && E != F) L = M = H;
                    if (Fl < El && E == A && E == D && E == G && E == Q && E != B && E != C && E != I && E != H) K = M = F;
                    if (Dl < El && E == C && E == F && E == I && E == R && E != B && E != A && E != G && E != H) J = L = D;
                    // Pentes 2:1.
                    if (H != B) {
                        if (H != A && H != E && H != C) {
                            if (H == G && H == F && H == R && H != D && H != src(im, x + 2, y - 1)) L = M;
                            if (H == I && H == D && H == Q && H != F && H != src(im, x - 2, y - 1)) M = L;
                        }
                        if (B != I && B != G && B != E) {
                            if (B == A && B == F && B == R && B != D && B != src(im, x + 2, y + 1)) J = K;
                            if (B == C && B == D && B == Q && B != F && B != src(im, x - 2, y + 1)) K = J;
                        }
                    }
                    if (F != D) {
                        if (D != I && D != E && D != C) {
                            if (D == A && D == H && D == S && D != B && D != src(im, x + 1, y + 2)) J = L;
                            if (D == G && D == B && D == P && D != H && D != src(im, x + 1, y - 2)) L = J;
                        }
                        if (F != E && F != A && F != G) {
                            if (F == C && F == H && F == S && F != B && F != src(im, x - 1, y + 2)) K = M;
                            if (F == I && F == B && F == P && F != H && F != src(im, x - 1, y - 2)) M = K;
                        }
                    }
                }
                haut[x * 2] = J;
                haut[x * 2 + 1] = K;
                bas[x * 2] = L;
                bas[x * 2 + 1] = M;
            }
            sortie[y * 2] = new String(haut);
            sortie[y * 2 + 1] = new String(bas);
        }
        return sortie;
    }

    /** Sprite deux fois plus fin, mêmes couleurs, mêmes ancrages (× 2). */
    public static Sprite agrandir(Sprite s) {
        Sprite g = new Sprite();
        g.id = s.id;
        g.slot = s.slot;
        g.ancre = s.ancre;
        g.dx = s.dx * 2;
        g.dy = s.dy * 2;
        g.duree = s.duree;
        g.derriere = s.derriere;
        g.coiffe = s.coiffe;
        g.natif = false;
        g.palette.putAll(s.palette);
        for (String[] im : s.images) g.images.add(agrandirImage(im, s.palette));
        return g;
    }

    /** ARGB d'un code #rrggbb ou #rrggbbaa ; 0 = transparent ou inconnu. */
    public static int couleur(String code) {
        if (code == null || code.length() < 7 || code.charAt(0) != '#') return 0;
        int rgb = Integer.parseInt(code.substring(1, 7), 16);
        int a = code.length() >= 9 ? Integer.parseInt(code.substring(7, 9), 16) : 0xff;
        return a << 24 | rgb;
    }

    public static final class Banque {
        public final Map<String, Sprite> sprites = new HashMap<>();
        public final Map<String, int[]> teintes = new HashMap<>();
        public final Map<String, String[]> tenues = new HashMap<>();
        public final Map<String, String> plats = new HashMap<>();

        /** Sprites redessinés pour le rendu fin (assets/sprites2x). */
        public final Map<String, Sprite> fins = new HashMap<>();
        private final Map<String, Sprite> agrandis = new HashMap<>();
        /** Grands dessins fins (décors animés, portraits) : lus à la demande, gardés dans un cache borné. */
        final java.util.Set<String> aLire = new java.util.HashSet<>();
        private final Map<String, Sprite> lus = new java.util.LinkedHashMap<String, Sprite>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, Sprite> e) {
                return size() > 12;
            }
        };

        public Sprite get(String id) {
            return id == null ? null : sprites.get(id);
        }

        /** Sprite du rendu fin : le dessin 2× s'il existe, sinon le sprite 1× agrandi (calculé une fois). */
        public Sprite fin(String id) {
            if (id == null) return null;
            Sprite s = fins.get(id);
            if (s != null) return s;
            if (aLire.contains(id)) {
                synchronized (lus) {
                    s = lus.get(id);
                    if (s == null) {
                        String t = ressource("/sprites2x/" + id + ".txt");
                        if (!t.isEmpty()) {
                            s = lire(t, id);
                            lus.put(id, s);
                        }
                    }
                }
                if (s != null) return s;
            }
            synchronized (agrandis) {
                s = agrandis.get(id);
                if (s == null) {
                    Sprite petit = sprites.get(id);
                    if (petit == null) return null;
                    s = agrandir(petit);
                    agrandis.put(id, s);
                }
                return s;
            }
        }

        /** Sprite à l'échelle demandée (1 : grille 48 × 56 ; 2 : rendu fin). */
        public Sprite get(String id, int echelle) {
            return echelle == 2 ? fin(id) : get(id);
        }

        /** Sprite du plat d'une recette ; inventé : plat-invente ; brûlé : plat-rate. */
        public String plat(String idRecette, boolean rate) {
            if (rate) return "plat-rate";
            String s = plats.get(idRecette);
            return s != null ? s : "plat-invente";
        }
    }

    private static Banque commune;

    /** La banque de l'app, lue une fois dans les ressources ; vide si elles manquent (rien ne plante). */
    public static synchronized Banque banque() {
        if (commune == null) commune = charger();
        return commune;
    }

    static Banque charger() {
        Banque b = new Banque();
        for (String id : lignes(ressource("/index.txt"))) {
            if (id.isEmpty() || id.startsWith("#")) continue;
            String t = ressource("/sprites/" + id + ".txt");
            if (!t.isEmpty()) b.sprites.put(id, lire(t, id));
        }
        for (String id : lignes(ressource("/index2x.txt"))) {
            if (id.isEmpty() || id.startsWith("#")) continue;
            // Les décors animés et les portraits fins sont gros : lus seulement quand on les montre.
            if (id.startsWith("decor-") || id.startsWith("portrait-")) {
                b.aLire.add(id);
                continue;
            }
            String t = ressource("/sprites2x/" + id + ".txt");
            if (!t.isEmpty()) b.fins.put(id, lire(t, id));
        }
        for (String[] l : table(ressource("/teintes.txt"))) {
            if (l.length != 5) continue;
            int[] c = new int[4];
            for (int i = 0; i < 4; i++) c[i] = couleur(l[i + 1]);
            b.teintes.put(l[0], c);
        }
        for (String[] l : table(ressource("/tenues.txt"))) {
            String[] ids = new String[l.length - 1];
            System.arraycopy(l, 1, ids, 0, ids.length);
            b.tenues.put(l[0], ids);
        }
        for (String[] l : table(ressource("/plats.txt")))
            if (l.length > 1) b.plats.put(l[0], l[1]);
        return b;
    }

    private static String ressource(String chemin) {
        try (InputStream in = Sprites.class.getResourceAsStream(chemin)) {
            if (in == null) return "";
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] tampon = new byte[8192];
            int n;
            while ((n = in.read(tampon)) > 0) out.write(tampon, 0, n);
            return out.toString(StandardCharsets.UTF_8.name());
        } catch (IOException e) {
            return "";
        }
    }

    private static String[] lignes(String texte) {
        return texte.replace("\r", "").split("\n");
    }

    private static List<String[]> table(String texte) {
        List<String[]> l = new ArrayList<>();
        for (String brut : lignes(texte)) {
            String s = brut.trim();
            int i = s.indexOf(':');
            if (s.isEmpty() || s.startsWith("#") || i < 0) continue;
            String[] v = s.substring(i + 1).trim().split("\\s+");
            String[] r = new String[v.length + 1];
            r[0] = s.substring(0, i).trim();
            System.arraycopy(v, 0, r, 1, v.length);
            l.add(r);
        }
        return l;
    }

    /** Dessine l'image d'un sprite objet (sans teinte) : coin haut-gauche (x0, y0), pixels de p points. */
    public static void dessiner(Dessin.Peintre pe, Sprite s, float x0, float y0, float p, double t, boolean miroir) {
        if (s == null) return;
        String[] im = s.image(t);
        for (int j = 0; j < im.length; j++) {
            String l = im[j];
            for (int i = 0; i < l.length(); i++) {
                char ch = l.charAt(i);
                if (ch == '.') continue;
                int c = couleur(s.palette.get(ch));
                if (c == 0) continue;
                int x = miroir ? l.length() - 1 - i : i;
                pe.rect(x0 + x * p, y0 + j * p, x0 + (x + 1) * p, y0 + (j + 1) * p, c);
            }
        }
    }

    // ---- Illustrations des campagnes (docs/SPRITES.md, « Décors et illustrations des campagnes ») : décor d'une scène
    // (bandeau de 96 × 40, 192 × 80 en fin), timbre d'un souvenir, vignette d'une campagne, emblème d'un ton. null si la
    // banque ne l'a pas : l'interface garde alors son repli. echelle : 1, ou 2 (dessin fin). Dessin : Sprites.dessiner.
    public static final int DECOR_LARGEUR = 96, DECOR_HAUTEUR = 40;

    public static Sprite decor(Banque b, String campagne, String decor, int echelle) {
        return decor == null || decor.isEmpty() ? null : illustration(b, "decor-" + campagne + "-" + decor, echelle);
    }

    public static Sprite souvenir(Banque b, String campagne, String souvenir, int echelle) {
        return illustration(b, "souvenir-" + campagne + "-" + souvenir, echelle);
    }

    public static Sprite vignette(Banque b, String campagne, int echelle) {
        return illustration(b, "campagne-" + campagne, echelle);
    }

    public static Sprite ton(Banque b, String ton, int echelle) {
        return illustration(b, "ton-" + ton, echelle);
    }

    private static Sprite illustration(Banque b, String id, int echelle) {
        return b == null || b.get(id) == null ? null : b.get(id, echelle);
    }

    private Sprites() {
    }
}
