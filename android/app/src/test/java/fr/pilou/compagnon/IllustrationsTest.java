package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Illustrations des campagnes (docs/SPRITES.md) : décors, souvenirs, vignettes, emblèmes et objets exclusifs. */
public class IllustrationsTest {
    private static boolean opaque(Sprites.Sprite s) {
        for (String[] im : s.images)
            for (String l : im)
                if (l.indexOf('.') >= 0) return false;
        return true;
    }

    @Test
    public void chaqueDecorDeclareASonBandeau() {
        Sprites.Banque b = Sprites.banque();
        int n = 0;
        for (String id : Campagnes.disponibles()) {
            Campagnes.Campagne c = Campagnes.charger(id);
            assertNotNull(id, c);
            for (Campagnes.Nomme d : c.decors) {
                Sprites.Sprite un = Sprites.decor(b, c.id, d.id, 1), fin = Sprites.decor(b, c.id, d.id, 2);
                assertNotNull(d.id, un);
                assertEquals(Sprites.DECOR_LARGEUR, un.w());
                assertEquals(Sprites.DECOR_HAUTEUR, un.h());
                assertTrue(d.id, fin.natif);
                assertEquals(un.w() * 2, fin.w());
                assertEquals(un.h() * 2, fin.h());
                assertEquals(un.images.size(), fin.images.size());
                assertEquals(un.duree, fin.duree);
                assertTrue(d.id, opaque(un) && opaque(fin));
                n++;
            }
            for (Campagnes.Nomme s : c.souvenirs) {
                Sprites.Sprite t = Sprites.souvenir(b, c.id, s.id, 1);
                assertNotNull(s.id, t);
                assertEquals(24, t.w());
            }
            assertNotNull(Sprites.vignette(b, c.id, 2));
            assertNotNull(c.ton, Sprites.ton(b, c.ton, 2));
        }
        assertTrue(n + " décors", n >= 40);
        assertNull(Sprites.decor(b, "prologue", "nulle-part", 2));
    }

    @Test
    public void objetsExclusifsPortesASonEmplacement() {
        Sprites.Banque b = Sprites.banque();
        List<String> tete = Arrays.asList("tete"), cou = Arrays.asList("cou"), dos = Arrays.asList("cou", "corps", "main-g"),
                main = Arrays.asList("main", "main-g");
        int n = 0;
        for (String id : Campagnes.disponibles()) {
            for (Campagnes.Nomme o : Campagnes.charger(id).objets) {
                if (!o.portable) continue;
                Sprites.Sprite s = b.get(o.id);
                assertNotNull(o.id, s);
                assertEquals(o.id, o.emplacement, s.slot);
                List<String> ancres = o.emplacement.equals("tete") ? tete : o.emplacement.equals("cou") ? cou
                        : o.emplacement.equals("dos") ? dos : main;
                assertTrue(o.id, ancres.contains(s.ancre));
                assertTrue(o.id, b.fin(o.id).natif);
                for (int stade = 1; stade <= 4; stade++) {
                    RenduPilou.Allure nu = new RenduPilou.Allure(), porte = new RenduPilou.Allure();
                    nu.stade = porte.stade = stade;
                    porte.objets = Arrays.asList(o.id);
                    RenduPilou.Geometrie g = new RenduPilou.Geometrie();
                    assertFalse(o.id + " stade " + stade, Arrays.equals(RenduPilou.rendre(nu, b, g, 2), RenduPilou.rendre(porte, b, g, 2)));
                }
                n++;
            }
        }
        assertTrue(n + " objets exclusifs", n >= 13);
    }

    @Test
    public void unEmblemeDeFormeDistinctePourChaqueTon() {
        Sprites.Banque b = Sprites.banque();
        Set<String> formes = new HashSet<>();
        for (String ton : new String[]{"humour", "mystere", "emotion", "epique"})
            formes.add(String.join("|", b.get("ton-" + ton).images.get(0)).replaceAll("[^.|]", "#"));
        assertEquals(4, formes.size());
    }
}
