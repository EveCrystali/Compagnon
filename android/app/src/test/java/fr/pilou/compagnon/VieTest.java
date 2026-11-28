package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;

import org.junit.Test;

/** Vie du personnage : mêmes valeurs que outils/sprites/vie.py (vie-reference.txt) et que le PC (VieTests.cs). */
public class VieTest {
    private static String trio(int[] v) {
        return v[0] + " " + v[1] + " " + v[2];
    }

    private static String suite(int n, java.util.function.IntUnaryOperator f) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) sb.append(i == 0 ? "" : " ").append(f.applyAsInt(i));
        return sb.toString();
    }

    @Test
    public void memesValeursQueLaReference() throws Exception {
        File f = new File(RenduPilouTest.racine(), "outils/sprites/vie-reference.txt");
        List<String> ecarts = new ArrayList<>();
        int n = 0;
        for (String l : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
            if (l.isEmpty() || l.startsWith("#")) continue;
            n++;
            String[] c = l.split(" ");
            String obtenu;
            int saute;
            switch (c[0]) {
                case "duree":
                    obtenu = "" + Vie.dureeBond(Integer.parseInt(c[2]), c[1]);
                    saute = 3;
                    break;
                case "bond":
                    obtenu = trio(Vie.bond(Long.parseLong(c[4]), Integer.parseInt(c[2]), Integer.parseInt(c[3]), c[1]));
                    saute = 5;
                    break;
                case "sautille":
                    obtenu = trio(Vie.sautille(Long.parseLong(c[4]), Integer.parseInt(c[2]), Integer.parseInt(c[3]), c[1]));
                    saute = 5;
                    break;
                case "reception": {
                    int[] r = Vie.reception(Long.parseLong(c[2]), c[1]);
                    obtenu = r[0] + " " + r[1];
                    saute = 3;
                    break;
                }
                case "lumiere": {
                    String m = Vie.lumiere(Integer.parseInt(c[1]), c[2].equals("-") ? "" : c[2], c[3]);
                    obtenu = m.isEmpty() ? "-" : m;
                    saute = 4;
                    break;
                }
                case "eclaire":
                    obtenu = String.format("#%06x", Vie.eclairer(0xff000000 | Integer.parseInt(c[2].substring(1), 16), c[1]) & 0xffffff);
                    saute = 3;
                    break;
                case "bouffee": {
                    int cad = Integer.parseInt(c[1]), sens = Integer.parseInt(c[2]);
                    obtenu = suite(70, i -> Vie.bouffee(i * 10L, cad, sens));
                    saute = 3;
                    break;
                }
                case "atterrissage":
                    obtenu = suite(32, i -> Vie.bouffeeAtterrissage(i * 10L - 20));
                    saute = 1;
                    break;
                default:
                    throw new IllegalArgumentException(c[0]);
            }
            StringBuilder attendu = new StringBuilder();
            for (int i = saute; i < c.length; i++) attendu.append(i == saute ? "" : " ").append(c[i]);
            if (!obtenu.equals(attendu.toString())) ecarts.add(l + " → " + obtenu);
        }
        assertTrue(n > 400);
        assertEquals(new ArrayList<String>(), ecarts);
    }

    @Test
    public void laLumiereGardeLAlpha() {
        assertEquals(0x80123456, Vie.eclairer(0x80123456, "jour"));
        assertEquals(0x80000000, Vie.eclairer(0x80000000, "nuit") & 0xff000000);
        assertEquals("", Vie.lumiere(22, "", Animations.AUCUNE));
    }
}
