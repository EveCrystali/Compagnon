package fr.pilou.compagnon;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;

import org.junit.Test;

/** Animations des campagnes : mêmes règles que le PC, relues dans outils/sprites/animations-reference.txt. */
public class AnimationsTest {
    @Test
    public void memesReglesQueLaReference() throws Exception {
        File f = new File(RenduPilouTest.racine(), "outils/sprites/animations-reference.txt");
        Map<Integer, String> textes = new HashMap<>();
        int n = 0;
        for (String l : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
            if (l.isEmpty() || l.startsWith("#")) continue;
            String[] p = l.split(" ", -1);
            switch (p[0]) {
                case "niveau":
                    assertEquals(l, p[3], Animations.niveau(p[1], p[2].equals("1")));
                    break;
                case "decor":
                    assertEquals(l, Long.parseLong(p[5]), Animations.imageDecor(Integer.parseInt(p[1]), Integer.parseInt(p[2]), Long.parseLong(p[3]), p[4]));
                    break;
                case "portrait":
                    assertEquals(l, Integer.parseInt(p[6]), Animations.imagePortrait(Integer.parseInt(p[1]), Long.parseLong(p[3]), p[4].equals("1"), p[5]));
                    break;
                case "texte": {
                    int k = 7 + p[1].length();
                    textes.put(Integer.parseInt(p[1]), l.length() > k ? l.substring(k) : "");
                    break;
                }
                case "ecriture": {
                    String t = textes.get(Integer.parseInt(p[1]));
                    assertEquals(l, Long.parseLong(p[2]), Animations.dureeEcriture(t));
                    assertEquals(l, Integer.parseInt(p[3]), Animations.attente(t));
                    break;
                }
                case "lettres":
                    assertEquals(l, Integer.parseInt(p[3]), Animations.lettres(textes.get(Integer.parseInt(p[1])), Long.parseLong(p[2])));
                    break;
                case "volet":
                    for (int bx = 0; bx < 12; bx++) assertEquals(l, Integer.parseInt(p[2 + bx]), Animations.ordreVolet(bx, Integer.parseInt(p[1]), 12));
                    break;
                case "fond":
                    assertArrayEquals(l, new String[]{p[3], p[4], p[5]}, Animations.teintesFond(p[1], Integer.parseInt(p[2])));
                    break;
                case "particule":
                    assertArrayEquals(l, new int[]{Integer.parseInt(p[4]), Integer.parseInt(p[5]), Integer.parseInt(p[6])},
                            Animations.particuleFond(p[1], Integer.parseInt(p[2]), Long.parseLong(p[3])));
                    break;
                case "recompense":
                    for (int i = 1; i < p.length; i++) assertEquals(l, Integer.parseInt(p[i]), Animations.delaiRecompense(i - 1));
                    break;
                default:
                    fail("ligne inconnue : " + l);
            }
            n++;
        }
        assertTrue(n + " lignes", n > 500);
    }

    @Test
    public void portraitsEtDecorsAnimes() {
        Sprites.Banque b = Sprites.banque();
        Sprites.Sprite s = Animations.portrait(b, "grande-panne", "grumeau", "colere", 2);
        assertNotNull(s);
        assertEquals(64, s.w());
        assertEquals(5, s.images.size());
        assertEquals("portrait-phare-eteint-vernier", Animations.portrait(b, "phare-eteint", "vernier", "colere", 1).id);
        assertNull(Animations.portrait(b, "phare-eteint", "personne", "", 2));
        Sprites.Sprite d = Sprites.decor(b, "phare-eteint", "jetee-nuit", 2);
        assertNotNull(d);
        assertTrue(d.images.size() >= 4 && d.images.size() <= 8);
        assertTrue(d.duree >= 125 && d.duree <= 250);
    }
}
