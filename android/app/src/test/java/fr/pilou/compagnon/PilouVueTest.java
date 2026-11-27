package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;

/** Rendu fin de PilouVue : tenu quand un pixel fin fait au moins 2 pixels de l'écran, sinon rendu 1× comme avant. */
@RunWith(RobolectricTestRunner.class)
public class PilouVueTest {
    private static int largeur(PilouVue v) {
        v.measure(0, 0);
        return v.getMeasuredWidth();
    }

    @Test
    public void finSeulementSiLePixelFinEstAssezGrand() {
        Context c = RuntimeEnvironment.getApplication();
        // Le constructeur reçoit des pixels d'écran par pixel de l'ancienne grille ; × Dessin.ECHELLE : par pixel de grille.
        PilouVue accueil = new PilouVue(c, 5.2f * 2.75f, true);     // 8,008 px par pixel de grille : 4 px par pixel fin
        assertTrue(accueil.fin());
        assertEquals((Dessin.W + 2) * 8, largeur(accueil));
        PilouVue bulle = new PilouVue(c, 2.2f * 2.75f, true);       // 3,39 px : un pixel fin ferait 1,7 px → rendu 1×
        assertFalse(bulle.fin());
        assertEquals((int) ((Dessin.W + 2) * (2.2f * 2.75f * Dessin.ECHELLE)), largeur(bulle));
        PilouVue dense = new PilouVue(c, 2.2f * 3.5f, true);        // 4,31 px : 2 px par pixel fin
        assertTrue(dense.fin());
        assertEquals((Dessin.W + 2) * 4, largeur(dense));
        // Sans le demander, rien ne change : rendu 1×, taille libre.
        PilouVue avant = new PilouVue(c, 5.2f * 2.75f);
        assertFalse(avant.fin());
        assertEquals((int) ((Dessin.W + 2) * (5.2f * 2.75f * Dessin.ECHELLE)), largeur(avant));
        // La taille change (réglage de la bulle) : le mode suit.
        bulle.pixel(2.2f * 3.5f);
        assertTrue(bulle.fin());
        bulle.pixel(2.2f * 2f);
        assertFalse(bulle.fin());
    }

    @Test
    public void pixelFinEntier() {
        assertEquals(4, Dessin.pixelFin(8.008f));
        assertEquals(3, Dessin.pixelFin(5.824f));
        assertEquals(2, Dessin.pixelFin(3.39f));
        assertEquals(1, Dessin.pixelFin(2.9f));
    }

    @Test
    public void seDessineAuxDeuxEchellesSansPlanter() {
        Context c = RuntimeEnvironment.getApplication();
        for (boolean fin : new boolean[]{false, true}) {
            PilouVue v = new PilouVue(c, 5.2f * 2.75f, fin);
            v.animer(false);
            v.montrer("joie", "bleu");
            v.tenue("voyage-marche");
            v.measure(0, 0);
            v.layout(0, 0, v.getMeasuredWidth(), v.getMeasuredHeight());
            Bitmap b = Bitmap.createBitmap(v.getMeasuredWidth(), v.getMeasuredHeight(), Bitmap.Config.ARGB_8888);
            v.draw(new Canvas(b));
            v.draw(new Canvas(b));   // deuxième image : le bitmap gardé sert encore
        }
        Dessin.ImageFine image = new Dessin.ImageFine();
        image.rendre(new RenduPilou.Allure());
        image.rendre(new RenduPilou.Allure());
        assertEquals(96, Dessin.ImageFine.LARGEUR);
        assertEquals(112, Dessin.ImageFine.HAUTEUR);
    }
}
