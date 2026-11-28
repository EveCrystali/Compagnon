package fr.pilou.compagnon;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.MotionEvent;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.shadows.ShadowSystemClock;

import java.time.Duration;
import java.util.Map;

/** La vue du théâtre dans la lecture : échelle entière, niveaux d'animation, touchers, travelling (Theatre.java fait le calcul). */
@RunWith(RobolectricTestRunner.class)
public class TheatreVueTest {
    private static void avancer(long ms) {
        ShadowSystemClock.advanceBy(Duration.ofMillis(ms));
    }

    private static TheatreVue vue(Context c, String niveau) {
        ScenesAnimees.regler(c, niveau);
        TheatreVue v = new TheatreVue(c);
        int k = TheatreVue.echelle(960);
        v.measure(View.MeasureSpec.makeMeasureSpec(960, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(Theatre.H * k, View.MeasureSpec.EXACTLY));
        v.layout(0, 0, 960, Theatre.H * k);
        return v;
    }

    private static void dessiner(TheatreVue v) {
        Bitmap b = Bitmap.createBitmap(v.getWidth(), v.getHeight(), Bitmap.Config.ARGB_8888);
        v.draw(new Canvas(b));
    }

    @Test
    public void echelleEntiereAuMoinsDeux() {
        assertEquals(5, TheatreVue.echelle(1080));
        assertEquals(1, TheatreVue.echelle(300));
        assertEquals(1, TheatreVue.echelle(0));
        assertEquals(3, TheatreVue.echelle(192 * 3 + 191));
    }

    @Test
    public void unLieuSansDessinEstRefuse() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.COMPLETES);
        assertFalse(v.lieu("prologue", "", false));
        assertFalse(v.lieu("prologue", "lieu-qui-n-existe-pas", false));
        assertFalse(v.pret());
    }

    @Test
    public void piloumarcheEtLImageChange() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.COMPLETES);
        assertTrue(v.lieu("prologue", "jardin", false));
        assertTrue(v.pret());
        long t0 = TheatreVue.maintenant();
        assertTrue(v.avancer(t0));
        long a = Theatre.fnv(v.image().clone());
        assertTrue(v.avancer(t0 + 1000));
        assertNotEquals(a, Theatre.fnv(v.image().clone()));
        // Le même pas de douze images : rien à réécrire.
        assertFalse(v.avancer(t0 + 1000 + 10));
        dessiner(v);
    }

    @Test
    public void toucherSurLaSceneEstUnClicAuxCoordonneesDuDecor() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.COMPLETES);
        v.ancienneSeule = true;                         // le repère de l'ancienne définition (192 × 80 à k)
        assertTrue(v.lieu("evolution", "fond-du-jardin-matin", false));
        avancer(6000);
        long now = TheatreVue.maintenant();
        v.avancer(now);
        dessiner(v);                                    // la vue connaît alors sa place à l'écran
        Theatre.Scene sc = Theatre.lireScenes(Sprites.ressource("/scenes/evolution.txt")).get("fond-du-jardin-matin");
        int x = sc.place, y = Theatre.sol(sc, x) - 8;
        long avant = Theatre.fnv(v.image().clone());
        int k = TheatreVue.echelle(960);
        float ex = (960 - Theatre.W * k) / 2f + (x + 0.5f) * k, ey = (y + 0.5f) * k;
        MotionEvent bas = MotionEvent.obtain(0, 0, MotionEvent.ACTION_DOWN, ex, ey, 0);
        MotionEvent haut = MotionEvent.obtain(0, 50, MotionEvent.ACTION_UP, ex, ey, 0);
        assertTrue(v.dispatchTouchEvent(bas));
        assertTrue(v.dispatchTouchEvent(haut));
        bas.recycle();
        haut.recycle();
        avancer(300);
        assertTrue(v.avancer(TheatreVue.maintenant()));
        assertNotEquals(avant, Theatre.fnv(v.image().clone()));
    }

    @Test
    public void sansAnimationLaSceneResteFixeEtIgnoreLesClics() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.AUCUNE);
        assertTrue(v.lieu("prologue", "jardin", false));
        long t0 = TheatreVue.maintenant();
        v.avancer(t0);
        int[] a = v.image().clone();
        v.cliquer(100, 100);
        v.avancer(t0 + 5000);
        assertArrayEquals(a, v.image());
        // Un second lieu : pas de travelling.
        assertTrue(v.lieu("prologue", "mare", true));
        assertTrue(v.avancer(TheatreVue.maintenant()));
    }

    @Test
    public void leTravellingGlisseDouzeCentsMillisecondesPuisSeFige() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.COMPLETES);
        assertTrue(v.lieu("prologue", "jardin", false));
        long t0 = TheatreVue.maintenant();
        v.avancer(t0 + 3000);
        assertTrue(v.lieu("prologue", "mare", true));
        long g = TheatreVue.maintenant();
        assertTrue(v.avancer(g + 300));
        int[] milieu = v.image().clone();
        assertTrue(v.avancer(g + 600));
        assertFalse(java.util.Arrays.equals(milieu, v.image()));
        // Après le travelling : Pilou est entré, l'image ne glisse plus.
        v.avancer(g + TheatreVue.GLISSE + 3000);
        int[] fin = v.image().clone();
        v.avancer(g + TheatreVue.GLISSE + 3010);
        assertArrayEquals(fin, v.image());
    }

    // ---- Théâtre HD : la mare du prologue est en HD, un lieu de Petit Nuage reste en ancien

    private static TheatreVue vueDe(Context c, int largeur, int hauteur) {
        ScenesAnimees.regler(c, Animations.COMPLETES);
        TheatreVue v = new TheatreVue(c);
        v.measure(View.MeasureSpec.makeMeasureSpec(largeur, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(hauteur, View.MeasureSpec.EXACTLY));
        v.layout(0, 0, largeur, hauteur);
        return v;
    }

    @Test
    public void echelleHdEntiereAuMoinsDeux() {
        assertEquals(2, TheatreVue.echelleHd(1078));
        assertEquals(2, TheatreVue.echelleHd(960));
        assertEquals(2, TheatreVue.echelleHd(720));
        assertEquals(2, TheatreVue.echelleHd(300));        // jamais 1
        assertEquals(3, TheatreVue.echelleHd(1440));
        assertEquals(480, TheatreVue.visiblesHd(1078));     // 959 px : rien n'est coupé
        assertEquals(360, TheatreVue.visiblesHd(720));      // écran étroit : floor(720 / 2) unités
        assertEquals(960, TheatreVue.largeurZoneHd(1078));
        assertEquals(720, TheatreVue.largeurZoneHd(720));
    }

    @Test
    public void laMareEstEnHdEtUnLieuSansDecorHdResteAncien() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vueDe(c, 1078, 480);
        assertTrue(v.lieu("prologue", "mare", false));
        assertTrue(v.hd());
        assertEquals(480, v.largeurBitmap());
        assertEquals(240, v.hauteurBitmap());
        assertTrue(v.avancer(TheatreVue.maintenant()));
        assertEquals(480 * 240, v.image().length);
        dessiner(v);
        assertEquals(2, v.echelleDessinee());
        // Un lieu sans décor HD : l'ancien, 192 × 80, sans travelling entre deux définitions (changement net).
        v.ancienneSeule = true;
        assertTrue(v.lieu("evolution", "fond-du-jardin-matin", true));
        assertFalse(v.hd());
        assertEquals(192, v.largeurBitmap());
        assertEquals(80, v.hauteurBitmap());
        assertTrue(v.avancer(TheatreVue.maintenant()));
        assertEquals(192 * 80, v.image().length);
        // Et retour en HD.
        v.ancienneSeule = false;
        assertTrue(v.lieu("prologue", "jardin", true));
        assertTrue(v.hd());
        assertTrue(v.avancer(TheatreVue.maintenant()));
        assertEquals(480 * 240, v.image().length);
    }

    @Test
    public void pilouFinEntreDansLaMare() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vueDe(c, 1078, 480);
        v.couleur("orange");
        v.pilou(2, "");
        assertTrue(v.lieu("prologue", "mare", false));
        long t0 = TheatreVue.maintenant();
        v.avancer(t0);
        int[] sans = v.image().clone();
        v.avancer(t0 + 6000);
        assertFalse("Pilou est entré dans la scène", java.util.Arrays.equals(sans, v.image()));
        // Changer la couleur ou le stade refait le rendu de Pilou, pas autre chose.
        int[] orange = v.image().clone();
        v.couleur("violet");
        v.avancer(t0 + 6500);
        assertFalse(java.util.Arrays.equals(orange, v.image()));
    }

    @Test
    public void leTravellingHdGlisseSansPilouPuisIlEntre() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vueDe(c, 1078, 480);
        assertTrue(v.lieu("prologue", "jardin", false));
        long t0 = TheatreVue.maintenant();
        v.avancer(t0 + 3000);
        assertTrue(v.lieu("prologue", "mare", true));
        assertTrue(v.hd());
        long g = TheatreVue.maintenant();
        assertTrue(v.avancer(g + 300));
        int[] milieu = v.image().clone();
        assertEquals(480 * 240, milieu.length);
        assertTrue(v.avancer(g + 700));
        assertFalse(java.util.Arrays.equals(milieu, v.image()));
        v.avancer(g + TheatreVue.GLISSE + 3000);
        int[] fin = v.image().clone();
        v.avancer(g + TheatreVue.GLISSE + 3010);
        assertArrayEquals(fin, v.image());
    }

    @Test
    public void laMetamorphoseFondLAncienneFormeDansLaNouvelle() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.COMPLETES), w = vue(c, Animations.COMPLETES);
        assertTrue(v.lieu("evolution", "fond-du-jardin-nuit", false, 150));
        assertTrue(w.lieu("evolution", "fond-du-jardin-nuit", false, 150));
        assertTrue(v.hd());
        long t0 = TheatreVue.maintenant();
        v.metamorphose(3, "", 4, "", t0 + 2200);
        w.pilou(4, "");
        // Avant : l'ancienne forme (pas celle du stade 4).
        v.avancer(t0 + 1500);
        w.avancer(t0 + 1500);
        assertFalse(java.util.Arrays.equals(v.image(), w.image()));
        // Pendant le fondu : ni l'une ni l'autre.
        v.avancer(t0 + 2200 + 2000);
        w.avancer(t0 + 2200 + 2000);
        assertFalse(java.util.Arrays.equals(v.image(), w.image()));
        // Après : exactement le Pilou du stade 4.
        long apres = t0 + 2200 + TheatreVue.DUREE_METAMORPHOSE + 500;
        v.avancer(apres);
        w.avancer(apres);
        assertArrayEquals(w.image(), v.image());
    }

    @Test
    public void leTravellingAncienResteEntreDeuxLieuxAnciens() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vue(c, Animations.COMPLETES);
        v.ancienneSeule = true;
        assertTrue(v.lieu("evolution", "fond-du-jardin-matin", false));
        long t0 = TheatreVue.maintenant();
        v.avancer(t0 + 3000);
        assertTrue(v.lieu("evolution", "fond-du-jardin-soir", true));
        assertFalse(v.hd());
        long g = TheatreVue.maintenant();
        assertTrue(v.avancer(g + 300));
        int[] milieu = v.image().clone();
        assertTrue(v.avancer(g + 600));
        assertFalse(java.util.Arrays.equals(milieu, v.image()));
    }

    @Test
    public void ecranEtroitCadreLaSceneEtLaCameraSuitPilou() {
        Context c = RuntimeEnvironment.getApplication();
        TheatreVue v = vueDe(c, 720, 480);
        assertTrue(v.lieu("prologue", "mare", false));
        long t0 = TheatreVue.maintenant();
        v.avancer(t0 + 5000);
        dessiner(v);
        assertEquals(2, v.echelleDessinee());              // jamais 1
        assertTrue("caméra bornée à [0, 120] : " + v.camera(), v.camera() >= 0 && v.camera() <= 480 - 360);
        assertEquals("Pilou est à gauche : la caméra aussi", 0, v.camera());
        // Il part par la droite : la caméra le suit doucement, sans jamais dépasser le bord de la scène.
        v.depart();
        int max = 0;
        for (long dt = 5000; dt <= 40000; dt += 250) {
            v.avancer(TheatreVue.maintenant() + dt);
            assertTrue(v.camera() >= 0 && v.camera() <= 120);
            max = Math.max(max, v.camera());
        }
        assertTrue("la caméra a suivi Pilou : " + max, max > 0);
        assertEquals(480, v.largeurBitmap());
    }
}
