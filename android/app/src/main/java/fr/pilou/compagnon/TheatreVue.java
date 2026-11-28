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

    private final Bitmap bitmap = Bitmap.createBitmap(Theatre.W, Theatre.H, Bitmap.Config.ARGB_8888);
    private final int[] px = new int[Theatre.W * Theatre.H];
    private final int[] avant = new int[Theatre.W * Theatre.H];
    private final int[] apres = new int[Theatre.W * Theatre.H];
    private final Paint pt = new Paint();
    private final Rect dst = new Rect();
    private final Sprites.Banque banque = Sprites.banque();

    private Theatre.Contexte cx;
    private Sprite decor;
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

    /** La couleur de Pilou (nom de teinte : « bleu », « orange »…), comme PilouVue la reçoit. */
    void couleur(String couleur) {
        teinte = RenduPilou.teinte(Dessin.allure("repos", 0, couleur, "", false, 0), banque);
        dernierPas = -1;
    }

    // ---- Les scènes embarquées : assets/scenes/<campagne>.txt et animations.txt

    private static final Map<String, Map<String, Theatre.Scene>> SCENES = new HashMap<>();
    private static Map<String, Map<String, Theatre.Anim>> anims;

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
    boolean lieu(String campagne, String decorId, boolean glisser) {
        long now = maintenant();
        String k = campagne + "|" + decorId;
        lireNiveau(now, true);
        if (k.equals(cle) && cx != null) return decor != null;
        Sprite neuf = null;
        try {
            neuf = Sprites.decor(banque, campagne, decorId, 2);
        } catch (RuntimeException x) {
            Journal.noter("théâtre : décor", x);
        }
        boolean avait = cx != null && decor != null;
        if (neuf == null) return false;
        glisser = glisser && avait && vif() && !casse;
        try {
            Theatre.Contexte nouveau = new Theatre.Contexte(sceneDe(campagne, decorId), anims(), id -> fin(banque, id));
            if (glisser) {
                // Travelling : l'ancien lieu (sans Pilou) est gardé tel quel pour glisser.
                Theatre.composer(cx, decor, teinte, evts, t(now), 0, niveau, avant, false);
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
        evts = new ArrayList<>();
        humeurVue = "";
        debut = glisser ? now + GLISSE : now;
        if (!glisser) glisse = -1;
        if (vif()) evts.add(new Theatre.Evenement(0, "entree", glisser ? ENTREE_X : 0, 0));
        dernierPas = -1;
        invalidate();
        return true;
    }

    private boolean ajouter(Theatre.Evenement e) {
        if (cx == null || !vif() || glisse >= 0) return false;
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

    void tait() {
        long n = t(maintenant());
        ajouter(new Theatre.Evenement(n, "parle", n, 0));
    }

    /** Il s'en va (un choix l'envoie en route). */
    void depart() {
        ajouter(new Theatre.Evenement(t(maintenant()), "depart", 1, 0));
    }

    /** Il revient s'il était parti et que l'histoire continue ici. */
    void revient() {
        if (cx == null || !pret()) return;
        try {
            if (!Theatre.pilou(cx, evts, t(maintenant())).visible) ajouter(new Theatre.Evenement(t(maintenant()), "entree"));
        } catch (RuntimeException x) {
            Journal.noter("théâtre : retour", x);
        }
    }

    /** Il est en route (attente, repos) : la scène montre le lieu sans lui ; il reviendra par la gauche. */
    void absent() {
        if (cx == null || !vif()) return;
        evts = new ArrayList<>();
        evts.add(new Theatre.Evenement(0, "entree", Theatre.SORTIE_D + 4, 0));
        evts.add(new Theatre.Evenement(0, "depart", 1, 0));
        humeurVue = "";
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
        int x = (int) Math.floor((ex - dst.left) / (float) echelle), y = (int) Math.floor((ey - dst.top) / (float) echelle);
        if (x < 0 || y < 0 || x >= Theatre.W || y >= Theatre.H) return;
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
            long pas = t / Theatre.PAS;
            boolean vif = vif();
            if (pas == dernierPas && vif) return false;
            if (!vif && dernierPas >= 0 && pas / 2 == dernierPas / 2) return false;
            dernierPas = pas;
            Theatre.composer(cx, decor, teinte, evts, t, 0, niveau, px);
            long h = Theatre.fnv(px);
            if (h == derniere) return false;
            derniere = h;
            ecrire(px);
            return true;
        } catch (RuntimeException x) {
            Journal.noter("théâtre : image", x);
            casse = true;
            return false;
        }
    }

    // Le travelling : décors côte à côte qui glissent (lissés), Pilou qui marche au milieu.
    private void glisser(double f) {
        double l = f * f * (3 - 2 * f);
        int dx = (int) Math.rint(-l * Theatre.W);
        Theatre.composer(cx, decor, teinte, Collections.<Theatre.Evenement>emptyList(), 0, 0, niveau, apres, false);
        for (int y = 0; y < Theatre.H; y++)
            for (int x = 0; x < Theatre.W; x++) {
                int sx = x - dx;
                px[y * Theatre.W + x] = sx < Theatre.W ? avant[y * Theatre.W + sx] : apres[y * Theatre.W + sx - Theatre.W];
            }
        Theatre.Anim m = cx.p.get("marche");
        if (m != null) {
            Theatre.poser(px, cx.sprites.apply(Theatre.ID_PILOU), m.image((long) (f * GLISSE)), ENTREE_X, Theatre.sol(cx.scene, ENTREE_X), false, teinte,
                    Theatre.PILOU_X, Theatre.PILOU_Y);
        }
        derniere = 0;
        ecrire(px);
    }

    private void ecrire(int[] p) {
        bitmap.setPixels(p, 0, Theatre.W, 0, 0, Theatre.W, Theatre.H);
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
        int h = MeasureSpec.getMode(hauteur) == MeasureSpec.UNSPECIFIED ? Theatre.H * echelle(w) : MeasureSpec.getSize(hauteur);
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
        int k = Math.max(1, Math.min(getWidth() / Theatre.W, Math.max(1, getHeight() / Theatre.H)));
        echelle = k;
        int w = Theatre.W * k, h = Theatre.H * k;
        int x = (getWidth() - w) / 2, y = 0;
        dst.set(x, y, x + w, y + h);
        cv.save();
        cv.clipRect(0, 0, getWidth(), getHeight());
        cv.drawBitmap(bitmap, null, dst, pt);
        cv.restore();
    }
}
