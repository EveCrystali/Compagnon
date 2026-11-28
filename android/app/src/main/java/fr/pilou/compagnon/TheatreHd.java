package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/**
 * Le Théâtre en haute définition (docs/SCENES-HD.md) : ce que calcule outils/sprites/theatre_hd.py (référence) pour une
 * scène de 480 × 240 : le décor compact à plans (assets/decors/decor-<campagne>-<décor>.txt), le compositeur (plans
 * « fond », acteurs, personnage et Pilou triés par leurs pieds, plans « devant », effets) et le Pilou fin du bureau
 * (RenduPilou, échelle 2, grille 96 × 112) posé par Theatre.poseHd. Sans Android, comme Theatre.
 * Les images sont des int[] à plat (ARGB, 0 : transparent), ligne par ligne.
 */
public final class TheatreHd {
    /** Ancre du Pilou fin : colonne du milieu, ligne de ses pieds (grille 96 × 112). */
    public static final int PILOU_X = 48, PILOU_Y = 107, PILOU_W = 96, PILOU_H = 112;

    /** Un plan du décor : « fond » (sous les personnages) ou « devant » (par-dessus), animé sur `duree` ms par image. */
    public static final class Plan {
        public final String nom;
        public final int profondeur, duree;
        public final boolean devant;
        public final int[][] images;

        Plan(String nom, int profondeur, boolean devant, int duree, int[][] images) {
            this.nom = nom;
            this.profondeur = profondeur;
            this.devant = devant;
            this.duree = duree;
            this.images = images;
        }
    }

    /** Le décor décodé une fois. Les plans « fond » sont aplatis une fois par combinaison d'images (cache). */
    public static final class Decor {
        public final String id;
        public final int w, h;
        public final List<Plan> plans;
        private final List<Plan> fonds = new ArrayList<>(), devants = new ArrayList<>();
        private final Map<Long, int[]> aplatis = new HashMap<>();

        /** Ancre « ancre: x y » (sprites HD), ou null. */
        public final int[] ancre;

        Decor(String id, int w, int h, List<Plan> plans, int[] ancre) {
            this.ancre = ancre;
            this.id = id;
            this.w = w;
            this.h = h;
            this.plans = plans;
            for (Plan p : plans) (p.devant ? devants : fonds).add(p);
        }

        /** Le fond (plans non « devant » mélangés sur du noir) à l'instant t. Ne pas modifier le tableau rendu. */
        int[] fond(long t, String niveau) {
            long cle = 0;
            boolean cachable = fonds.size() <= 10;
            int[] idx = new int[fonds.size()];
            for (int i = 0; i < idx.length; i++) {
                Plan p = fonds.get(i);
                idx[i] = (int) Animations.imageDecor(p.images.length, p.duree, t, niveau);
                cle = cle * 64 + idx[i];
            }
            int[] f = cachable ? aplatis.get(cle) : null;
            if (f != null) return f;
            f = new int[w * h];
            Arrays.fill(f, 0xFF000000);
            for (int i = 0; i < idx.length; i++) calque(f, fonds.get(i).images[idx[i]]);
            if (cachable) aplatis.put(cle, f);
            return f;
        }
    }

    // ---- Le décor à plans

    private static int couleur(String c) {
        int rgb = Integer.parseInt(c.substring(1, 7), 16);
        int a = c.length() >= 9 ? Integer.parseInt(c.substring(7, 9), 16) : 255;
        return (a << 24) | rgb;
    }

    /** « [n]c » une plage, « . » le pixel de l'image précédente du même plan, « , » transparent (0). Un fichier sans
     *  ligne « plan: » a un seul plan. Même algorithme que lire_decor_hd. */
    public static Decor lireDecorHd(String texte) {
        String[] lignes = texte.split("\n", -1);
        for (int i = 0; i < lignes.length; i++)
            if (lignes[i].endsWith("\r")) lignes[i] = lignes[i].substring(0, lignes[i].length() - 1);
        String id = "";
        int[] ancre = null;
        int w = 0, h = 0;
        List<Plan> plans = new ArrayList<>();
        // Le plan en cours de lecture.
        boolean enPlan = false, devant = false;
        String nom = "";
        int prof = 0, duree = 0;
        Map<Character, Integer> palette = new HashMap<>();
        List<int[]> images = new ArrayList<>();
        int i = 0;
        while (i < lignes.length) {
            String l = lignes[i++];
            if (l.isEmpty() || l.startsWith("#")) continue;
            int deux = l.indexOf(':');
            String cle = deux < 0 ? l : l.substring(0, deux);
            String val = deux < 0 ? "" : l.substring(deux + 1).trim();
            if (cle.equals("id")) {
                id = val;
            } else if (cle.equals("ancre")) {
                String[] v = val.split("\s+");
                ancre = new int[]{Integer.parseInt(v[0]), Integer.parseInt(v[1])};
            } else if (cle.equals("taille")) {
                String[] v = val.split("\\s+");
                w = Integer.parseInt(v[0]);
                h = Integer.parseInt(v[1]);
            } else if (cle.equals("plan")) {
                String[] v = val.split("\\s+");
                nom = v[0];
                prof = Integer.parseInt(v[1]);
                devant = v[2].equals("devant");
                duree = 0;
                palette = new HashMap<>();
                images = new ArrayList<>();
                enPlan = true;
            } else if ((cle.equals("duree") || cle.equals("palette")) && !enPlan) {
                nom = "decor";
                prof = 0;
                devant = false;
                duree = 0;
                palette = new HashMap<>();
                images = new ArrayList<>();
                enPlan = true;
                i--;
            } else if (cle.equals("duree")) {
                duree = Integer.parseInt(val);
            } else if (cle.equals("palette")) {
                if (!val.isEmpty())
                    for (String paire : val.split("\\s+")) {
                        int eg = paire.indexOf('=');
                        palette.put(paire.charAt(0), couleur(paire.substring(eg + 1)));
                    }
            } else if (cle.equals("images")) {
                int n = Integer.parseInt(val);
                int[] prec = null;
                for (int k = 0; k < n; k++) {
                    int[] im = new int[w * h];
                    for (int y = 0; y < h; y++) {
                        int x = 0, nb = 0, o = y * w;
                        String ligne = lignes[i];
                        for (int c = 0; c < ligne.length(); c++) {
                            char ch = ligne.charAt(c);
                            if (ch >= '0' && ch <= '9') {
                                nb = nb * 10 + ch - '0';
                                continue;
                            }
                            if (nb == 0) nb = 1;
                            if (ch == '.') {
                                System.arraycopy(prec, o + x, im, o + x, nb);
                            } else if (ch != ',') {
                                Integer pc = palette.get(ch);
                                if (pc == null) throw new IllegalArgumentException(id + " : couleur « " + ch + " » inconnue");
                                Arrays.fill(im, o + x, o + x + nb, pc);
                            }
                            x += nb;
                            nb = 0;
                        }
                        if (x != w) throw new IllegalArgumentException(id + " : rangée de " + x + " pixels au lieu de " + w);
                        i++;
                    }
                    images.add(im);
                    prec = im;
                }
                plans.add(new Plan(nom, prof, devant, duree, images.toArray(new int[0][])));
                enPlan = false;
            }
        }
        return new Decor(id, w, h, plans, ancre);
    }

    private static final Map<String, Decor> DECORS = new HashMap<>();

    /** Le décor assets/decors/decor-<campagne>-<décor>.txt, décodé une seule fois ; null s'il n'existe pas. */
    public static synchronized Decor decor(String campagne, String decor) {
        String cle = campagne + "/" + decor;
        if (DECORS.containsKey(cle)) return DECORS.get(cle);
        String t = Sprites.ressource("/decors/decor-" + campagne + "-" + decor + ".txt");
        Decor d = t.isEmpty() ? null : lireDecorHd(t);
        DECORS.put(cle, d);
        return d;
    }

    /** Les scènes HD de assets/scenes-hd/<campagne>.txt (définition HD) ; vide si le fichier manque. */
    public static Map<String, Theatre.Scene> scenes(String campagne) {
        return Theatre.lireScenes(Sprites.ressource("/scenes-hd/" + campagne + ".txt"), Theatre.HD);
    }

    // ---- Les sprites HD : acteurs et personnages en pied (assets/sprites-hd, docs/SCENES-HD.md § 6 et 7)

    /** Un sprite HD : images ARGB à plat (0 : transparent), ancre (ax, ay) des pieds, durée d'une image. */
    public static final class SpriteHd {
        public final String id;
        public final int w, h, ax, ay, duree;
        public final int[][] images;

        SpriteHd(Decor d) {
            id = d.id;
            w = d.w;
            h = d.h;
            ax = d.ancre != null ? d.ancre[0] : d.w / 2;
            ay = d.ancre != null ? d.ancre[1] : d.h - 1;
            duree = d.plans.get(0).duree;
            images = d.plans.get(0).images;
        }
    }

    public static SpriteHd lireSpriteHd(String texte) {
        return new SpriteHd(lireDecorHd(texte));
    }

    private static final Map<String, SpriteHd> SPRITES = new HashMap<>();

    /** Le sprite HD assets/sprites-hd/<id>.txt, lu une seule fois ; null s'il n'existe pas. */
    public static synchronized SpriteHd spriteHd(String id) {
        if (SPRITES.containsKey(id)) return SPRITES.get(id);
        String t = Sprites.ressource("/sprites-hd/" + id + ".txt");
        SpriteHd s = t.isEmpty() ? null : lireSpriteHd(t);
        SPRITES.put(id, s);
        return s;
    }

    /** Pose l'image im du sprite à son ancre (x, y) ; le miroir se fait autour de l'ancre. */
    private static void poserHd(int[] px, int w, int h, SpriteHd s, int im, int x, int y, boolean miroir) {
        int[] g = s.images[((im % s.images.length) + s.images.length) % s.images.length];
        int ox = x - (miroir ? s.w - 1 - s.ax : s.ax), oy = y - s.ay;
        for (int j = 0; j < s.h; j++) {
            int yy = oy + j;
            if (yy < 0 || yy >= h) continue;
            int o = j * s.w;
            for (int i = 0; i < s.w; i++) {
                int c = g[o + i];
                if (c == 0) continue;
                int xx = ox + (miroir ? s.w - 1 - i : i);
                if (xx >= 0 && xx < w) melanger(px, yy * w + xx, c);
            }
        }
    }

    // ---- Le Pilou fin du bureau, rendu pour la scène

    /** Une pose (Theatre.poseHd) → grille 96 × 112 ARGB (0 : vide), par RenduPilou à l'échelle 2. base : les champs
     *  propres au joueur (stade, couleur, accessoire…) ; null : le Pilou de démonstration (stade 2, bleu). Les derniers
     *  rendus sont gardés (une pose demandée deux fois de suite ne se rend qu'une fois). */
    public static Function<Map<String, Object>, int[]> rendeurPilou(RenduPilou.Allure base, Sprites.Banque banque) {
        final Map<Map<String, Object>, int[]> cache = new LinkedHashMap<Map<String, Object>, int[]>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<Map<String, Object>, int[]> e) {
                return size() > 32;
            }
        };
        return pose -> {
            int[] g = cache.get(pose);
            if (g == null) {
                g = RenduPilou.rendre(allure(base, pose), banque, null, 2);
                cache.put(new HashMap<>(pose), g);
            }
            return g;
        };
    }

    /** Les champs d'une pose de référence posés sur l'allure de base. */
    public static RenduPilou.Allure allure(RenduPilou.Allure base, Map<String, Object> pose) {
        RenduPilou.Allure a = base != null ? base.copie() : new RenduPilou.Allure();
        for (Map.Entry<String, Object> e : pose.entrySet()) {
            Object v = e.getValue();
            switch (e.getKey()) {
                case "expr": a.expr = (String) v; break;
                case "t": a.t = ((Number) v).doubleValue(); break;
                case "marche": a.marche = (Boolean) v; break;
                case "parle": a.parle = (Boolean) v; break;
                case "cligne": a.cligne = (Boolean) v; break;
                case "regard": a.regard = ((Number) v).intValue(); break;
                case "saut": a.saut = ((Number) v).doubleValue(); break;
                case "salue": a.salue = (Boolean) v; break;
                default: throw new IllegalArgumentException(e.getKey());
            }
        }
        return a;
    }

    // ---- Le compositeur HD

    /** Mélange alpha entier (arrondi au plus proche) de c sur px[k], comme _melanger. */
    private static void melanger(int[] px, int k, int c) {
        int a = c >>> 24;
        if (a == 0) return;
        if (a == 255) {
            px[k] = c;
            return;
        }
        int d = px[k];
        int r = (((c >>> 16) & 255) * a + ((d >>> 16) & 255) * (255 - a) + 127) / 255;
        int v = (((c >>> 8) & 255) * a + ((d >>> 8) & 255) * (255 - a) + 127) / 255;
        int b = ((c & 255) * a + (d & 255) * (255 - a) + 127) / 255;
        px[k] = 0xFF000000 | r << 16 | v << 8 | b;
    }

    private static void calque(int[] px, int[] im) {
        for (int k = 0; k < im.length; k++) {
            int c = im[k];
            if (c == 0) continue;
            if ((c >>> 24) == 255) px[k] = c;
            else melanger(px, k, c);
        }
    }

    private static void poserGrille(int[] px, int w, int h, int[] g, int gw, int gh, int x, int y, int ax, int ay) {
        int ox = x - ax, oy = y - ay;
        for (int j = 0; j < gh; j++) {
            int yy = oy + j;
            if (yy < 0 || yy >= h) continue;
            for (int i = 0; i < gw; i++) {
                int c = g[j * gw + i];
                int xx = ox + i;
                if (c != 0 && xx >= 0 && xx < w) melanger(px, yy * w + xx, c);
            }
        }
    }

    /** L'image HD de la scène à l'instant t (largeur × hauteur de la définition de la scène). Les acteurs et
     *  personnages sans sprite HD (cx.hd rend null) ne sont pas dessinés : jamais d'ancien sprite agrandi.
     *  rendrePilou : pose (Theatre.poseHd) → grille 96 × 112 ARGB (0 : vide). */
    public static int[] composerHd(Decor decor, Theatre.Contexte cx, List<Theatre.Evenement> evts, long t,
                                   Function<Map<String, Object>, int[]> rendrePilou, int regard, String niveau,
                                   int[] sortie) {
        return composerHd(decor, cx, evts, t, rendrePilou, regard, niveau, sortie, true);
    }

    /** avecPilou : faux pendant un travelling (Pilou entre ensuite, la vue ne le pose pas sur les décors qui glissent). */
    public static int[] composerHd(Decor decor, Theatre.Contexte cx, List<Theatre.Evenement> evts, long t,
                                   Function<Map<String, Object>, int[]> rendrePilou, int regard, String niveau,
                                   int[] sortie, boolean avecPilou) {
        Theatre.Scene sc = cx.scene;
        int w = sc.d.w, h = sc.d.h;
        int[] px = sortie != null && sortie.length == w * h ? sortie : new int[w * h];
        if (decor != null && decor.w == w && decor.h == h) {
            System.arraycopy(decor.fond(t, niveau), 0, px, 0, px.length);
        } else {
            Arrays.fill(px, 0xFF000000);
        }
        // Tri stable par (pieds, Pilou après les autres à égalité, ordre d'insertion), comme la référence.
        List<Object[]> poses = new ArrayList<>();
        for (Theatre.Pose a : Theatre.acteurs(cx, evts, t, niveau)) poses.add(new Object[]{a.y, 0, poses.size(), a});
        Theatre.Pose pp = Theatre.perso(cx, evts, t, niveau);
        if (pp != null && cx.existe(pp.sprite))   // le dessin HD regarde à droite : retourné pour regarder Pilou
            poses.add(new Object[]{pp.y, 0, poses.size(), new Theatre.Pose(pp.sprite, pp.image, pp.x, pp.y, !pp.miroir)});
        Theatre.Etat etat = Theatre.pilouEtat(cx, evts, t, regard, niveau);
        if (etat.visible && avecPilou) poses.add(new Object[]{etat.y, 1, poses.size(), etat});
        Collections.sort(poses, (u, v) -> {
            int c = Integer.compare((Integer) u[0], (Integer) v[0]);
            if (c == 0) c = Integer.compare((Integer) u[1], (Integer) v[1]);
            if (c == 0) c = Integer.compare((Integer) u[2], (Integer) v[2]);
            return c;
        });
        for (Object[] o : poses) {
            if (o[3] instanceof Theatre.Etat) {
                Theatre.Etat e = (Theatre.Etat) o[3];
                int[] g = rendrePilou.apply(Theatre.poseHd(e, t));
                poserGrille(px, w, h, g, PILOU_W, PILOU_H, e.x, e.y, PILOU_X, PILOU_Y);
            } else {
                Theatre.Pose q = (Theatre.Pose) o[3];
                poserHd(px, w, h, cx.hd.apply(q.sprite), q.image, q.x, q.y, q.miroir);
            }
        }
        if (decor != null)
            for (Plan p : decor.devants) calque(px, p.images[(int) Animations.imageDecor(p.images.length, p.duree, t, niveau)]);
        for (Theatre.Pose q : Theatre.effets(cx, evts, t, niveau))
            poserHd(px, w, h, cx.hd.apply(q.sprite), q.image, q.x, q.y, q.miroir);
        return px;
    }

    private TheatreHd() {
    }
}
