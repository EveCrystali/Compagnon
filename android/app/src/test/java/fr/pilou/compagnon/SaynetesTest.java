package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.Test;

/** Saynètes de repos : mêmes tirages et mêmes poses que outils/sprites/saynetes.py (saynetes-reference.txt) et que
 *  le PC (SaynetesTests.cs), à partir de la même banque (assets/saynetes.txt). */
public class SaynetesTest {
    private static List<Saynetes.Saynete> banque() throws Exception {
        File f = new File(RenduPilouTest.racine(), "assets/saynetes.txt");
        return Saynetes.lire(new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8));
    }

    static String texte(Saynetes.Jeu j) {
        if (j == null) return "fini";
        return "assis=" + j.assis + " saut=" + j.saut + " etire=" + j.etire + " penche=" + j.penche + " expr=" + j.expr
                + " regard=" + j.regard + " regard_y=" + j.regardY + " cligne=" + (j.cligne ? 1 : 0) + " baille="
                + (j.baille ? 1 : 0) + " salue=" + (j.salue ? 1 : 0) + " objets="
                + (j.objets.isEmpty() ? "-" : String.join(",", j.objets));
    }

    @Test
    public void memesValeursQueLaReference() throws Exception {
        List<Saynetes.Saynete> b = banque();
        assertTrue(b.size() >= 15);
        File f = new File(RenduPilouTest.racine(), "outils/sprites/saynetes-reference.txt");
        List<String> ecarts = new ArrayList<>();
        int n = 0;
        for (String l : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
            if (l.trim().isEmpty() || l.startsWith("#")) continue;
            n++;
            int i = l.indexOf(" -> ");
            String gauche = l.substring(0, i), attendu = l.substring(i + 4);
            String[] m = gauche.split(" ");
            String obtenu;
            if (m[0].equals("tirer")) {
                Map<String, String> c = new HashMap<>();
                for (int k = 1; k < m.length; k++) {
                    String[] kv = m[k].split("=", 2);
                    c.put(kv[0], kv[1]);
                }
                Saynetes.Contexte ctx = new Saynetes.Contexte(Integer.parseInt(c.get("heure")), Integer.parseInt(c.get("mois")),
                        Integer.parseInt(c.get("stade")), c.get("objets").equals("-") ? Collections.<String>emptyList()
                        : Arrays.asList(c.get("objets").split(",")), c.get("compagnon").equals("1"),
                        c.get("mainlibre").equals("1"), c.get("travail").equals("1"), c.get("traits").equals("-")
                        ? Collections.<String>emptyList() : Arrays.asList(c.get("traits").split(",")));
                String id = Saynetes.tirer(b, Integer.parseInt(c.get("u")), ctx, c.get("evite").equals("-") ? "" : c.get("evite"));
                obtenu = id.isEmpty() ? "-" : id;
            } else if (m[0].equals("eveil")) {
                int h = Integer.parseInt(m[1].substring("heure=".length()));
                long inactif = Long.parseLong(m[2].substring("inactif=".length()));
                obtenu = (Saynetes.endormi(h, inactif) ? "dort" : "eveille") + " nuit=" + (Saynetes.nuit(h) ? 1 : 0);
            } else {
                obtenu = texte(Saynetes.jouer(Saynetes.trouver(b, m[1]), Long.parseLong(m[2]), m[3], Integer.parseInt(m[4])));
            }
            if (!obtenu.equals(attendu)) ecarts.add(gauche + " : " + obtenu + " au lieu de " + attendu);
        }
        assertTrue(n > 1000);
        assertEquals(String.join("\n", ecarts.subList(0, Math.min(10, ecarts.size()))), 0, ecarts.size());
    }

    @Test
    public void aucuneCoupeTout() throws Exception {
        for (Saynetes.Saynete s : banque()) assertNull(Saynetes.jouer(s, s.duree / 2, Animations.AUCUNE, 1));
    }
}
