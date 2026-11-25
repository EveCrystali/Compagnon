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
 */
public final class Sprites {
    public static final class Sprite {
        public String id = "", slot = "objet", ancre = "aucun";
        public int dx, dy, duree;
        public boolean derriere, coiffe;
        /** Couleur par lettre : #rrggbb(aa) ou @contour / @ombre / @base / @clair. */
        public final Map<Character, String> palette = new HashMap<>();
        public final List<String[]> images = new ArrayList<>();

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

        public Sprite get(String id) {
            return id == null ? null : sprites.get(id);
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

    private Sprites() {
    }
}
