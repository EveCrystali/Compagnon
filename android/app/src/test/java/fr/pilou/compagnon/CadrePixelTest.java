package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;

import android.graphics.Bitmap;
import android.graphics.Canvas;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

/**
 * Le cadre pixel (CadrePixel) : tout se compte en u (ici u = 5 pixels d'écran) : bord d'1 u, coins en escalier (le pixel de
 * coin est vide), biseau d'1 u, ombre d'1 u en escalier, état « appuyé » sans ombre. Et le calage du fil sur une bulle entière.
 */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class CadrePixelTest {
    private static final int U = 5;
    private static final CadrePixel.Couleurs C = CadrePixel.SOMBRE;

    private static Bitmap dessiner(CadrePixel d, int w, int h) {
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        d.setBounds(0, 0, w, h);
        d.draw(new Canvas(b));
        return b;
    }

    @Test
    public void bordBiseauEtCoinsEnEscalier() {
        CadrePixel d = new CadrePixel(C, U, true);
        assertEquals(2 * U, d.dedans());
        assertEquals(U, d.ombre());
        Bitmap b = dessiner(d, 60, 40);   // cadre visible : 55 × 35, ombre d'1 u à droite et en bas
        // Les quatre coins du cadre : le pixel de 1 u × 1 u est vide.
        assertEquals(0, b.getPixel(0, 0));
        assertEquals(0, b.getPixel(U - 1, U - 1));
        assertEquals(0, b.getPixel(55 - 1, 0));
        assertEquals(0, b.getPixel(0, 35 - 1));
        // Le bord : 1 u, juste à côté du coin vide.
        assertEquals(C.bord, b.getPixel(U, 0));
        assertEquals(C.bord, b.getPixel(0, U));
        assertEquals(C.bord, b.getPixel(2 * U, U - 1));
        assertEquals(C.bord, b.getPixel(55 - 1, 2 * U));
        // Le biseau : 1 u, clair en haut et à gauche, sombre en bas et à droite ; puis le fond.
        assertEquals(C.biseauClair, b.getPixel(3 * U, U));
        assertEquals(C.biseauClair, b.getPixel(3 * U, 2 * U - 1));
        assertEquals(C.biseauClair, b.getPixel(U, 3 * U));
        assertEquals(C.biseauSombre, b.getPixel(3 * U, 35 - U - 1));
        assertEquals(C.biseauSombre, b.getPixel(55 - U - 1, 3 * U));
        assertEquals(C.fond, b.getPixel(3 * U, 2 * U));
        assertEquals(C.fond, b.getPixel(2 * U, 3 * U));
        // L'ombre : 1 u, en escalier elle aussi (ses coins haut-droite et bas-gauche manquent).
        assertEquals(C.ombre, b.getPixel(57, 20));
        assertEquals(C.ombre, b.getPixel(20, 37));
        assertEquals(0, b.getPixel(57, U + 2));
        assertEquals(0, b.getPixel(U + 2, 37));
        assertEquals(0, b.getPixel(59, 39));
    }

    @Test
    public void appuyeSansOmbreEtSansOmbreDuTout() {
        CadrePixel d = new CadrePixel(C, U, true);
        d.forcer(true);
        Bitmap b = dessiner(d, 60, 40);
        assertEquals(0, b.getPixel(57, 20));
        assertEquals(0, b.getPixel(20, 37));
        assertEquals(C.appuyeFond, b.getPixel(3 * U, 2 * U));
        assertEquals(C.bord, b.getPixel(U, 0));

        CadrePixel s = new CadrePixel(C, U, false);
        assertEquals(0, s.ombre());
        Bitmap c = dessiner(s, 60, 40);
        assertEquals(0, c.getPixel(0, 0));
        assertEquals(C.bord, c.getPixel(59 - U, 0 + 1));
        assertEquals(C.biseauSombre, c.getPixel(3 * U, 40 - U - 1));
        assertEquals(C.bord, c.getPixel(30, 39));
    }

    @Test
    public void lesPalettesSontCellesDuMenuDuPc() {
        assertEquals(0xff151a2e, CadrePixel.SOMBRE.fond);
        assertEquals(0xfffbf3e4, CadrePixel.CLAIRE.fond);
        assertEquals(0xff6a5acd, CadrePixel.SOMBRE.bord);
        assertEquals(0xff2f7ed8, CadrePixel.CLAIRE.bord);
        assertEquals(0xfff69d50, CadrePixel.SOMBRE.appuyeFond);
        assertEquals(0xff1f5fae, CadrePixel.CLAIRE.appuyeFond);
    }

    @Test
    public void caleSurLaPlusAncienneBulleQuiLaisseToutTenir() {
        // Hauts des bulles (pixels), fin du contenu 300, 250 visibles, marge 10 : la 2e bulle (100 - 10) laisse tout tenir.
        assertEquals(90, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 300, 250, 10));
        // Tout tient : on reste en haut (jamais négatif).
        assertEquals(0, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 300, 400, 10));
        // La dernière bulle est plus haute que l'écran : on montre son début.
        assertEquals(190, Lecture.Fil.cibleBas(new int[]{10, 100, 200}, 600, 50, 10));
        assertEquals(0, Lecture.Fil.cibleBas(new int[0], 0, 100, 10));
    }
}
