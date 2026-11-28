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
        assertTrue(v.lieu("prologue", "jardin", false));
        avancer(6000);
        long now = TheatreVue.maintenant();
        v.avancer(now);
        dessiner(v);                                    // la vue connaît alors sa place à l'écran
        Theatre.Scene sc = Theatre.lireScenes(Sprites.ressource("/scenes/prologue.txt")).get("jardin");
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
}
