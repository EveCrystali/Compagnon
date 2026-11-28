package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;

import fr.pilou.compagnon.Sprites.Sprite;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * La scène du théâtre dans la lecture d'une campagne (docs/SCENES.md) : le décor entier, le mini-Pilou qui vit dans le
 * lieu, les acteurs d'ambiance, les réactions aux touchers. Tout le calcul est dans Theatre.java (commun avec le PC,
 * dont VueTheatre.cs est le modèle) ; ici, seulement l'affichage : un Bitmap de 192 × 80 réécrit au plus douze fois par
 * seconde (et seulement si l'image change), agrandi d'un facteur entier sans lissage. Pas de regard à la souris sur
 * téléphone. Changer de lieu fait un travelling : l'ancien décor part à gauche, le nouveau arrive, Pilou marche au
 * milieu. La minuterie ne tourne que si la vue est à l'écran. Une erreur de calcul laisse l'image telle quelle.
 */
final class TheatreVue extends View {
    static final int GLISSE = 1200;        // durée du travelling (ms)
    private static final int ENTREE_X = 40;  // là où Pilou se trouve à la fin du travelling

    /** La scène HD (docs/SCENES-HD.md) : 480 × 240 unités, au moins 2 pixels d'écran par unité (jamais 1). */
    static final int HD_W = Theatre.HD.w, HD_H = Theatre.HD.h;

    // La définition du lieu courant : ancienne (192 × 80) ou HD (480 × 240). Tampons et bitmap suivent.
    private Theatre.Definition def = Theatre.ANCIENNE;
    private Bitmap bitmap = Bitmap.createBitmap(def.w, def.h, Bitmap.Config.ARGB_8888);
    private int[] px = new int[def.w * def.h];
    private int[] avant = new int[def.w * def.h];
    private int[] apres = new int[def.w * def.h];
    private final Paint pt = new Paint();
    private final Rect dst = new Rect();
    private final Rect src = new Rect();
    private final Sprites.Banque banque = Sprites.banque();

    private Theatre.Contexte cx;
    private Sprite decor;
    private TheatreHd.Decor decorHd;
    // Le Pilou du joueur pour les scènes HD : la base de l'allure, le rendeur (recréé seulement si la base change).
    private String couleurJoueur = "bleu", varianteJoueur = "";
    private int stadeJoueur = 2;
    private java.util.function.Function<Map<String, Object>, int[]> rendeur;
    // La caméra des écrans étroits (HD) : x entier du bord gauche visible, qui suit Pilou doucement.
    private int camera;
    private double cameraF;
    private int cameraCible;
    private long cameraT = -1;
    private List<Theatre.Evenement> evts = new ArrayList<>();
    private long debut;
    private long glisse = -1;
    private String cle = "";
    private long dernierPas = -1;
    private long derniere;
    private int[] teinte;
    private String niveau = Animations.COMPLETES;
    private long niveauLu = Long.MIN_VALUE;
    private String humeurVue = "";
    private String persoVu = "";        // le sprite fin du personnage en pied qui est dans la scène ("" : personne)
    private boolean persoParle;
    private boolean casse;
    private boolean actif;
    private int echelle = 1;

    private final Runnable tic = new Runnable() {
        @Override
        public void run() {
            actif = false;
            if (!isShown()) return;
            if (avancer(maintenant())) invalidate();
            actif = true;
            postDelayed(this, Theatre.PAS);
        }
    };

    TheatreVue(Context c) {
        super(c);
        pt.setFilterBitmap(false);
        pt.setAntiAlias(false);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        teinte = RenduPilou.teinte(Dessin.allure("repos", 0, "bleu", "", false, 0), banque);
        niveau = ScenesAnimees.niveau(c);
    }

    static long maintenant() {
        return SystemClock.uptimeMillis();
    }

    /** La plus grande échelle entière qui tient dans la largeur (au moins 1) : l unité de pixel de l écran Aventure. */
    static int echelle(int largeurPx) {
        return Aventure.unite(largeurPx);
    }

    /** L'échelle HD : pixels d'écran par unité, entier, au moins 2 (480 px de large est refusé : trop petit). */
    static int echelleHd(int largeurPx) {
        return Math.max(2, largeurPx / HD_W);
    }

    /** Unités HD visibles sur cette largeur d'écran : toute la scène (480), ou floor(largeur / échelle) sur un écran étroit. */
    static int visiblesHd(int largeurPx) {
        return Math.max(1, Math.min(HD_W, largeurPx / echelleHd(largeurPx)));
    }

    /** Largeur en pixels d'écran de la partie visible d'une scène HD : 960 sur 1078 px, 720 sur 720 px. */
    static int largeurZoneHd(int largeurPx) {
        return visiblesHd(largeurPx) * echelleHd(largeurPx);
    }

    /** La couleur de Pilou (nom de teinte : « bleu », « orange »…), comme PilouVue la reçoit. */
    void couleur(String couleur) {
        String c = couleur == null || couleur.isEmpty() ? "bleu" : couleur;
        if (c.equals(couleurJoueur) && teinte != null) return;
        couleurJoueur = c;
        teinte = RenduPilou.teinte(Dessin.allure("repos", 0, c, "", false, 0), banque);
        rendeur = null;
        dernierPas = -1;
    }

    /** Le stade et la variante d'évolution (« calin », « espiegle », ou "") du Pilou du joueur, pour les scènes HD. */
    void pilou(int stade, String variante) {
        int s = stade >= 1 && stade <= 4 ? stade : 2;
        String v = variante == null ? "" : variante;
        if (s == stadeJoueur && v.equals(varianteJoueur)) return;
        stadeJoueur = s;
        varianteJoueur = v;
        rendeur = null;
        dernierPas = -1;
    }

    /** L'allure de base du Pilou fin du joueur : sa couleur, son stade, sa variante. */
    private RenduPilou.Allure baseJoueur() {
        RenduPilou.Allure base = new RenduPilou.Allure();
        base.couleur = couleurJoueur;
        base.stade = stadeJoueur;
        if (stadeJoueur >= 2 && !varianteJoueur.isEmpty())
            base.objets = java.util.Arrays.asList("variante-" + varianteJoueur + "-" + stadeJoueur, "variante-" + varianteJoueur + "-" + stadeJoueur + "-tete");
        return base;
    }

    /** Le rendeur du Pilou fin du joueur (couleur, stade, variante) ; gardé tant que cette base ne change pas. */
    private java.util.function.Function<Map<String, Object>, int[]> rendeur() {
        if (rendeur == null) rendeur = TheatreHd.rendeurPilou(baseJoueur(), banque);
        return rendeur;
    }

    // La métamorphose des scènes d'évolution (docs/SCENES.md), comme VueTheatre.Metamorphose sur PC : Pilou garde son
    // ancien stade jusqu'à metaDebut, puis le bureau fond l'ancienne forme dans la nouvelle (Allure.evolution de 0 à 1),
    // puis il reste au nouveau stade.
    static final long DUREE_METAMORPHOSE = 4200;               // la même que l'évolution du bureau
    private int metaApres;
    private String metaVariante = "";
    private long metaDebut = -1;

    void metamorphose(int avant, String varianteAvant, int apres, String varianteApres, long debut) {
        pilou(avant, varianteAvant);
        metaApres = apres;
        metaVariante = varianteApres == null ? "" : varianteApres;
        metaDebut = debut;
        dernierPas = -1;
    }

    /** Le rendeur à l'instant now : pendant le fondu de la métamorphose, sans cache (l'évolution change à chaque pas). */
    private java.util.function.Function<Map<String, Object>, int[]> rendeur(long now) {
        if (metaDebut < 0 || now < metaDebut) return rendeur();
        double f = (now - metaDebut) / (double) DUREE_METAMORPHOSE;
        pilou(metaApres, metaVariante);
        if (f >= 1) return rendeur();
        final RenduPilou.Allure base = baseJoueur();
        base.evolution = Math.max(0.001, f);
        return pose -> RenduPilou.rendre(TheatreHd.allure(base, pose), banque, null, 2);
    }

    /** Aux animations réduites ou sans animation, le Pilou fin ne respire pas : le temps de son rendu reste à 0 (il cligne par sa pose). */
    private java.util.function.Function<Map<String, Object>, int[]> rendeurNiveau(long now) {
        final java.util.function.Function<Map<String, Object>, int[]> r = rendeur(now);
        if (vif()) return r;
        return pose -> {
            Map<String, Object> p = new HashMap<>(pose);
            p.put("t", 0L);
            return r.apply(p);
        };
    }

    /** Pour les tests : le lieu courant est-il en haute définition (480 × 240) ? */
    boolean hd() {
        return def == Theatre.HD;
    }

    /** Pour les tests : largeur et hauteur du Bitmap. */
    int largeurBitmap() {
        return bitmap.getWidth();
    }

    int hauteurBitmap() {
        return bitmap.getHeight();
    }

    /** Pour les tests : le x (unités) du bord gauche visible. */
    int camera() {
        return camera;
    }

    private boolean aDecor() {
        return decor != null || decorHd != null;
    }

    // ---- Les scènes embarquées : assets/scenes/<campagne>.txt et animations.txt

    private static final Map<String, Map<String, Theatre.Scene>> SCENES = new HashMap<>();
    private static final Map<String, Map<String, Theatre.Scene>> SCENES_HD = new HashMap<>();
    private static Map<String, Map<String, Theatre.Anim>> anims;

    private static synchronized Theatre.Scene sceneHd(String campagne, String decor) {
        Map<String, Theatre.Scene> s = SCENES_HD.get(campagne);
        if (s == null) SCENES_HD.put(campagne, s = TheatreHd.scenes(campagne));
        return s.get(decor);
    }

    private static synchronized Theatre.Scene sceneDe(String campagne, String decor) {
        Map<String, Theatre.Scene> s = SCENES.get(campagne);
        if (s == null) SCENES.put(campagne, s = Theatre.lireScenes(Sprites.ressource("/scenes/" + campagne + ".txt")));
        Theatre.Scene sc = s.get(decor);
        if (sc != null) return sc;
        // Un décor sans fiche de scène : Pilou marche en bas, sans acteurs (comme au PC).
        sc = new Theatre.Scene();
        sc.nom = decor;
        sc.sol = new int[]{0, 77, Theatre.W, 77};
        sc.place = 30;
        return sc;
    }

    private static synchronized Map<String, Map<String, Theatre.Anim>> anims() {
        if (anims == null) anims = Theatre.lireAnimations(Sprites.ressource("/scenes/animations.txt"));
        return anims;
    }

    /** Sprite fin d'un acteur, de Pilou ou d'un décor (les décors sont lus à la demande) ; null s'il n'existe pas. */
    static Sprite fin(Sprites.Banque b, String id) {
        Sprite s = b.fins.get(id);
        if (s != null) return s;
        return b.aLire.contains(id) ? b.fin(id) : null;
    }

    boolean pret() {
        return cx != null && !cx.p.isEmpty();
    }

    // ---- Ce que la lecture raconte

    private boolean vif() {
        return Animations.COMPLETES.equals(niveau);
    }

    private long t(long now) {
        return Math.max(0, now - debut);
    }

    /**
     * Montre ce lieu (décor de la campagne) ; rend faux s'il n'a pas de dessin. glisser : un travelling depuis le lieu
     * précédent (faux quand la lecture rattrape d'un coup des messages déjà lus).
     */
    /** Pour les tests : jouer l'ancienne définition même quand le décor HD existe (tous les lieux réels en ont un). */
    boolean ancienneSeule;

    boolean lieu(String campagne, String decorId, boolean glisser) {
        return lieu(campagne, decorId, glisser, 0);
    }

    /** entree : en HD sans travelling, d'où Pilou entre (0 : le bord gauche), en unités de la scène. */
    boolean lieu(String campagne, String decorId, boolean glisser, int entree) {
        long now = maintenant();
        String k = campagne + "|" + decorId;
        lireNiveau(now, true);
        if (k.equals(cle) && cx != null) return aDecor();
        // HD : la scène HD de la campagne ET le décor HD existent. Sinon l'ancien, jamais les deux dans la même image.
        TheatreHd.Decor neufHd = null;
        Theatre.Scene sceneHdNeuve = null;
        try {
            sceneHdNeuve = ancienneSeule ? null : sceneHd(campagne, decorId);
            if (sceneHdNeuve != null) {
                neufHd = TheatreHd.decor(campagne, decorId);
                if (neufHd == null || neufHd.w != HD_W || neufHd.h != HD_H) neufHd = null;
            }
        } catch (RuntimeException x) {
            Journal.noter("théâtre : décor HD", x);
            neufHd = null;
        }
        boolean hdNeuf = neufHd != null;
        Sprite neuf = null;
        if (!hdNeuf) {
            try {
                neuf = Sprites.decor(banque, campagne, decorId, 2);
            } catch (RuntimeException x) {
                Journal.noter("théâtre : décor", x);
            }
            if (neuf == null) return false;
        }
        boolean avait = cx != null && aDecor();
        // Pas de travelling entre deux définitions : changement net.
        glisser = glisser && avait && vif() && !casse && hdNeuf == hd();
        try {
            Theatre.Contexte nouveau = hdNeuf
                    ? new Theatre.Contexte(sceneHdNeuve, anims(), id -> fin(banque, id), this::spriteHd)
                    : new Theatre.Contexte(sceneDe(campagne, decorId), anims(), id -> fin(banque, id));
            if (glisser) {
                // Travelling : l'ancien lieu (sans Pilou) est gardé tel quel pour glisser.
                if (hd()) TheatreHd.composerHd(decorHd, cx, evts, t(now), rendeur(), 0, niveau, avant, false);
                else Theatre.composer(cx, decor, teinte, evts, t(now), 0, niveau, avant, false);
                glisse = now;
            }
            cx = nouveau;
        } catch (RuntimeException x) {
            Journal.noter("théâtre : lieu", x);
            casse = true;
            return false;
        }
        casse = false;
        cle = k;
        decor = neuf;
        decorHd = neufHd;
        definir(hdNeuf ? Theatre.HD : Theatre.ANCIENNE);
        camera = 0;
        cameraF = 0;
        cameraT = -1;
        evts = new ArrayList<>();
        humeurVue = "";
        persoVu = "";
        persoParle = false;
        debut = glisser ? now + GLISSE : now;
        if (!glisser) glisse = -1;
        // En HD, Pilou n'est pas dessiné pendant le glissement : il entre ensuite par la gauche.
        if (vif()) evts.add(new Theatre.Evenement(0, "entree", glisser ? (hdNeuf ? 0 : ENTREE_X) : hdNeuf ? entree : 0, 0));
        dernierPas = -1;
        invalidate();
        return true;
    }

    /** Passe à une définition : tampons et bitmap à la taille du lieu (rien ne bouge si elle ne change pas). */
    private void definir(Theatre.Definition d) {
        if (d == def) return;
        def = d;
        bitmap = Bitmap.createBitmap(d.w, d.h, Bitmap.Config.ARGB_8888);
        px = new int[d.w * d.h];
        avant = new int[d.w * d.h];
        apres = new int[d.w * d.h];
        derniere = 0;
    }

    private boolean ajouter(Theatre.Evenement e) {
        if (cx == null || !vif()) return false;          // pendant un travelling, l'événement tombe au début de la nouvelle scène
        return pousser(e);
    }

    private boolean pousser(Theatre.Evenement e) {
        if (!evts.isEmpty() && e.t < evts.get(evts.size() - 1).t) {
            long dernier = evts.get(evts.size() - 1).t;
            e = new Theatre.Evenement(dernier, e.sorte, e.a, e.b, e.humeur);
        }
        evts.add(e);
        dernierPas = -1;
        return true;
    }

    /** L'humeur de Pilou. Un message qui s'écrit la redit à chaque fois (une joie fait sauter Pilou de nouveau) ;
     *  la lecture finie la répète à chaque rafraîchissement : redite sans effet (redit faux). */
    void humeur(String humeur, boolean redit) {
        String h = humeur == null ? "neutre" : humeur;
        if (!redit && h.equals(humeurVue)) return;
        if (ajouter(Theatre.Evenement.humeur(t(maintenant()), h))) humeurVue = h;
    }

    /** Pilou parle pendant ms millisecondes. */
    void parle(long ms) {
        long now = maintenant();
        ajouter(new Theatre.Evenement(t(now), "parle", t(now) + ms, 0));
    }

    /** Le silence : Pilou et, s'il parlait, le personnage en pied se taisent (fin de l'écriture, ou texte accéléré). */
    void tait() {
        long n = t(maintenant());
        ajouter(new Theatre.Evenement(n, "parle", n, 0));
        if (persoParle) {
            persoParle = false;
            if (cx != null) pousser(new Theatre.Evenement(n, "parle-perso", n, 0));
        }
    }

    /**
     * Le personnage en pied du message : son sprite fin « pied-campagne-personnage » s'il est dessiné, sinon plus
     * personne. Un message sans personnage ne l'enlève pas (il reste tant qu'on est dans le même lieu ; un autre lieu
     * repart sans lui). Il se pose aussi pendant un travelling ou à animations réduites : il entre quand la scène
     * commence.
     */
    /** L'humeur du message du personnage : en HD, il prend la variante dessinée pour elle (pied-<campagne>-<id>-<humeur>,
     *  même toile et même ancre), sinon sa version neutre. Comme VueTheatre.SpriteHd (PC). */
    private String persoHumeur = "";

    private TheatreHd.SpriteHd spriteHd(String id) {
        if (id.equals(persoVu) && !persoHumeur.isEmpty()) {
            TheatreHd.SpriteHd v = TheatreHd.spriteHd(id + "-" + persoHumeur);
            if (v != null) return v;
        }
        return TheatreHd.spriteHd(id);
    }

    void personnage(String campagne, String personnage, String humeur) {
        persoHumeur = humeur == null ? "" : humeur;
        personnage(campagne, personnage);
    }

    void personnage(String campagne, String personnage) {
        if (cx == null || personnage == null || personnage.isEmpty()) return;
        String sid = "pied-" + campagne + "-" + personnage;
        if (!cx.existe(sid) || !cx.anims.containsKey(sid)) sid = "";
        if (sid.equals(persoVu)) return;
        if (pousser(new Theatre.Evenement(t(maintenant()), "perso", 0, 0, sid))) persoVu = sid;
        if (sid.isEmpty()) persoParle = false;
    }

    /** Y a-t-il un personnage en pied dans la scène ? */
    boolean aPerso() {
        return !persoVu.isEmpty();
    }

    /** Le personnage en pied dit sa réplique pendant ms millisecondes ; faux s'il n'y en a pas (Pilou parlera alors). */
    boolean parlePerso(long ms) {
        if (cx == null || persoVu.isEmpty()) return false;
        long now = maintenant(), t0 = t(now), fin = (now - debut) + ms;   // pendant un travelling, la scène n'a pas commencé
        if (fin > t0 && pousser(new Theatre.Evenement(t0, "parle-perso", fin, 0))) persoParle = true;
        return true;
    }

    /** Il s'en va (un choix l'envoie en route). */
    void depart() {
        ajouter(new Theatre.Evenement(t(maintenant()), "depart", 1, 0));
    }

    /** Il revient s'il était parti et que l'histoire continue ici. */
    void revient() {
        if (cx == null || !pret()) return;
        try {
            if (!Theatre.pilouEtat(cx, evts, t(maintenant()), 0, Animations.COMPLETES).visible) ajouter(new Theatre.Evenement(t(maintenant()), "entree"));
        } catch (RuntimeException x) {
            Journal.noter("théâtre : retour", x);
        }
    }

    /** Il est en route (attente, repos) : la scène montre le lieu sans lui ; il reviendra par la gauche. */
    void absent() {
        if (cx == null || !vif()) return;
        evts = new ArrayList<>();
        evts.add(new Theatre.Evenement(0, "entree", def.w + Theatre.e(cx.scene, Theatre.SORTIE_D - Theatre.W) + 4, 0));
        evts.add(new Theatre.Evenement(0, "depart", 1, 0));
        humeurVue = "";
        persoVu = "";
        persoParle = false;
        glisse = -1;
        debut = maintenant();
        dernierPas = -1;
    }

    // ---- Toucher : un clic aux coordonnées du décor (un toucher sur la scène n'accélère jamais le texte)

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        int a = e.getActionMasked();
        if (a == MotionEvent.ACTION_DOWN) return true;
        if (a == MotionEvent.ACTION_UP) {
            performClick();
            cliquer(e.getX(), e.getY());
            return true;
        }
        return a == MotionEvent.ACTION_MOVE;
    }

    @Override
    public boolean performClick() {
        return super.performClick();
    }

    void cliquer(float ex, float ey) {
        if (cx == null || !vif() || glisse >= 0 || dst.width() <= 0) return;
        int x = camera + (int) Math.floor((ex - dst.left) / (float) echelle), y = (int) Math.floor((ey - dst.top) / (float) echelle);
        if (x < 0 || y < 0 || x >= def.w || y >= def.h) return;
        ajouter(new Theatre.Evenement(t(maintenant()), "clic", x, y));
    }

    // ---- Chaque image (la minuterie de la vue)

    private void lireNiveau(long now, boolean force) {
        if (!force && now - niveauLu < 1000) return;
        niveauLu = now;
        String n = ScenesAnimees.niveau(getContext());
        if (!n.equals(niveau)) {
            niveau = n;
            dernierPas = -1;
        }
    }

    /** Recalcule l'image si besoin ; vrai si le Bitmap a été réécrit. */
    boolean avancer(long now) {
        if (cx == null || casse) return false;
        lireNiveau(now, false);
        try {
            if (glisse >= 0) {
                double f = (now - glisse) / (double) GLISSE;
                if (f >= 1) glisse = -1;
                else {
                    glisser(f);
                    return true;
                }
            }
            long t = t(now);
            boolean cam = hd() && majCamera(now, t);
            long pas = t / Theatre.PAS;
            boolean vif = vif();
            if (pas == dernierPas && vif) return cam;
            if (!vif && dernierPas >= 0 && pas / 2 == dernierPas / 2) return cam;
            dernierPas = pas;
            if (hd()) TheatreHd.composerHd(decorHd, cx, evts, t, rendeurNiveau(now), 0, niveau, px);
            else Theatre.composer(cx, decor, teinte, evts, t, 0, niveau, px);
            long h = Theatre.fnv(px);
            if (h == derniere) return cam;
            derniere = h;
            ecrire(px);
            return true;
        } catch (RuntimeException x) {
            Journal.noter("théâtre : image", x);
            casse = true;
            return false;
        }
    }

    /** L échelle HD de la vue : la plus grande entière qui tient (largeur et hauteur), au moins 2. */
    private int kHd() {
        return Math.max(2, Math.min(getWidth() / HD_W, getHeight() / HD_H));
    }

    /**
     * La caméra d un écran étroit (HD) : vise Pilou au centre du champ, bornée à [0, 480 − visibles], et l y rejoint
     * doucement (demi-vie de 300 ms : environ une seconde). Vrai si le x entier a changé. Sur un écran assez large : 0, immobile.
     */
    private boolean majCamera(long now, long t) {
        int vis = getWidth() > 0 ? Math.min(def.w, Math.max(1, getWidth() / kHd())) : def.w;
        int max = def.w - vis;
        if (max <= 0) {
            boolean change = camera != 0;
            camera = 0;
            cameraF = 0;
            return change;
        }
        Theatre.Etat e = Theatre.pilouEtat(cx, evts, t, 0, niveau);
        if (e.visible) cameraCible = Math.max(0, Math.min(max, e.x - vis / 2));
        if (cameraT < 0) cameraF = cameraCible;
        else {
            long dt = Math.max(0, Math.min(250, now - cameraT));
            cameraF += (cameraCible - cameraF) * (1 - Math.pow(0.5, dt / 300.0));
        }
        cameraT = now;
        int c = Math.max(0, Math.min(max, (int) Math.rint(cameraF)));
        boolean change = c != camera;
        camera = c;
        return change;
    }

    // Le travelling : décors côte à côte qui glissent (lissés), Pilou qui marche au milieu.
    private void glisser(double f) {
        double l = f * f * (3 - 2 * f);
        final int w = def.w, h = def.h;
        int dx = (int) Math.rint(-l * w);
        if (hd()) TheatreHd.composerHd(decorHd, cx, Collections.<Theatre.Evenement>emptyList(), 0, rendeur(), 0, niveau, apres, false);
        else Theatre.composer(cx, decor, teinte, Collections.<Theatre.Evenement>emptyList(), 0, 0, niveau, apres, false);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                int sx = x - dx;
                px[y * w + x] = sx < w ? avant[y * w + sx] : apres[y * w + sx - w];
            }
        Theatre.Anim m = hd() ? null : cx.p.get("marche");   // en HD, Pilou entre ensuite
        if (m != null) {
            Theatre.poser(px, cx.sprites.apply(Theatre.ID_PILOU), m.image((long) (f * GLISSE)), ENTREE_X, Theatre.sol(cx.scene, ENTREE_X), false, teinte,
                    Theatre.PILOU_X, Theatre.PILOU_Y);
        }
        derniere = 0;
        ecrire(px);
    }

    private void ecrire(int[] p) {
        bitmap.setPixels(p, 0, def.w, 0, 0, def.w, def.h);
    }

    /** Pour les tests : l échelle (pixels d écran par pixel fin) de la dernière image dessinée. */
    int echelleDessinee() {
        return echelle;
    }

    /** Pour les tests : l'image courante (192 × 80, ARGB). */
    int[] image() {
        return px;
    }

    @Override
    protected void onMeasure(int largeur, int hauteur) {
        int w = MeasureSpec.getSize(largeur);
        int h = MeasureSpec.getMode(hauteur) == MeasureSpec.UNSPECIFIED ? (hd() ? HD_H * echelleHd(w) : Theatre.H * echelle(w)) : MeasureSpec.getSize(hauteur);
        setMeasuredDimension(w, h);
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        demarrer();
    }

    @Override
    protected void onDetachedFromWindow() {
        removeCallbacks(tic);
        actif = false;
        super.onDetachedFromWindow();
    }

    @Override
    protected void onVisibilityChanged(View vue, int visibilite) {
        super.onVisibilityChanged(vue, visibilite);
        majMinuterie();
    }

    @Override
    protected void onWindowVisibilityChanged(int visibilite) {
        super.onWindowVisibilityChanged(visibilite);
        majMinuterie();
    }

    private void majMinuterie() {
        if (isShown()) demarrer();
        else {
            removeCallbacks(tic);
            actif = false;
        }
    }

    private void demarrer() {
        if (actif || !isShown()) return;
        actif = true;
        removeCallbacks(tic);
        postDelayed(tic, 0);
    }

    @Override
    protected void onDraw(Canvas cv) {
        if (cx == null) return;
        avancer(maintenant());
        // HD : au moins 2 pixels d écran par unité (jamais 1) ; si l écran est plus étroit que la scène, seule la partie
        // de la caméra est montrée (visiblesHd unités, centrées). Ancien : le plus grand entier qui tient.
        int k, vis;
        if (hd()) {
            k = kHd();
            vis = Math.min(def.w, Math.max(1, getWidth() / k));
        } else {
            k = Math.max(1, Math.min(getWidth() / def.w, Math.max(1, getHeight() / def.h)));
            vis = def.w;
        }
        echelle = k;
        int cam = Math.max(0, Math.min(def.w - vis, camera));
        src.set(cam, 0, cam + vis, def.h);
        int w = vis * k, h = def.h * k;
        int x = (getWidth() - w) / 2, y = 0;
        dst.set(x, y, x + w, y + h);
        cv.save();
        cv.clipRect(0, 0, getWidth(), getHeight());
        cv.drawBitmap(bitmap, src, dst, pt);
        cv.restore();
    }
}
