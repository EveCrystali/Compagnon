package fr.pilou.compagnon;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

import org.junit.Test;

/** Mesure (pas une exigence) : chargement du décor HD de la mare et coût d'une image, comparés à l'ancien théâtre. */
public class TheatreHdMesureTest {
    private static Sprites.Sprite fin(Sprites.Banque b, String id) {
        if (b.fins.containsKey(id)) return b.fins.get(id);
        return b.aLire.contains(id) ? b.fin(id) : null;
    }

    @Test
    public void mesures() {
        Sprites.Banque b = Sprites.banque();
        Map<String, Map<String, Theatre.Anim>> anims = Theatre.lireAnimations(Sprites.ressource("/scenes/animations.txt"));
        List<Theatre.Evenement> evts = new ArrayList<>();
        evts.add(new Theatre.Evenement(0, "entree"));
        evts.add(Theatre.Evenement.humeur(2600, "joie"));
        evts.add(new Theatre.Evenement(3000, "parle", 4200, 0));
        evts.add(Theatre.Evenement.humeur(6000, "surpris"));
        final int N = 120;

        // Chargement du décor HD (lecture de la ressource + décodage), sans le cache.
        long t0 = System.nanoTime();
        TheatreHd.Decor d = TheatreHd.lireDecorHd(Sprites.ressource("/decors/decor-prologue-mare.txt"));
        double chargement = (System.nanoTime() - t0) / 1e6;
        assertNotNull(d);

        Theatre.Scene sc = TheatreHd.scenes("prologue").get("mare");
        Theatre.Contexte cx = new Theatre.Contexte(sc, anims, id -> fin(b, id), TheatreHd::spriteHd);
        Function<Map<String, Object>, int[]> rendre = TheatreHd.rendeurPilou(null, b);
        int[] sortie = new int[480 * 240];
        for (int i = 0; i < 20; i++) TheatreHd.composerHd(d, cx, evts, i * 100L, rendre, 0, Animations.COMPLETES, sortie);   // chauffe
        t0 = System.nanoTime();
        for (int i = 0; i < N; i++) TheatreHd.composerHd(d, cx, evts, i * 100L, rendre, 0, Animations.COMPLETES, sortie);
        double hd = (System.nanoTime() - t0) / 1e6 / N;

        Theatre.Scene sa = Theatre.lireScenes(Sprites.ressource("/scenes/prologue.txt")).get("mare");
        Theatre.Contexte ca = new Theatre.Contexte(sa, anims, id -> fin(b, id));
        Sprites.Sprite decor = fin(b, "decor-prologue-mare");
        int[] teinte = b.teintes.get("bleu");
        int[] so = new int[Theatre.W * Theatre.H];
        for (int i = 0; i < 20; i++) Theatre.composer(ca, decor, teinte, evts, i * 100L, 0, Animations.COMPLETES, so);
        t0 = System.nanoTime();
        for (int i = 0; i < N; i++) Theatre.composer(ca, decor, teinte, evts, i * 100L, 0, Animations.COMPLETES, so);
        double ancien = (System.nanoTime() - t0) / 1e6 / N;

        System.out.println("MESURE chargement decor-prologue-mare : " + String.format("%.1f", chargement) + " ms");
        System.out.println("MESURE composerHd 480x240 : " + String.format("%.2f", hd) + " ms par image (" + N + " images)");
        System.out.println("MESURE composer ancien 192x80 : " + String.format("%.2f", ancien) + " ms par image (" + N + " images)");
        assertTrue(hd > 0 && ancien > 0);
    }
}
