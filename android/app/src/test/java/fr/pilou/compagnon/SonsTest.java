package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;

/** Sons de Pilou : mêmes échantillons que le PC (SonsTests.cs) et que outils/sons/sons.py. */
public class SonsTest {
    static File racine() {
        File f = new File("").getAbsoluteFile();
        while (f != null && !new File(f, "assets/index.txt").exists()) f = f.getParentFile();
        assertNotNull("racine du dépôt introuvable", f);
        return f;
    }

    @Test
    public void memesEchantillonsQueLaReference() throws Exception {
        Map<String, List<Sons.Note>> c = Sons.lire(new String(Files.readAllBytes(new File(racine(), "assets/sons.txt").toPath()),
                StandardCharsets.UTF_8));
        int vus = 0;
        for (String l : Files.readAllLines(new File(racine(), "outils/sons/sons-reference.txt").toPath(), StandardCharsets.UTF_8)) {
            if (l.startsWith("#") || l.trim().isEmpty()) continue;
            String[] p = l.split("\\|");
            String id = p[0].trim();
            short[] s = Sons.synthetiser(c.get(id));
            assertEquals(id + " : longueur", Integer.parseInt(p[1].trim()), s.length);
            assertEquals(id + " : empreinte", p[3].trim(), Sons.empreinte(s));
            vus++;
        }
        assertEquals(c.size(), vus);
    }

    @Test
    public void laRessourceEmbarqueeEstLeCatalogue() {
        Map<String, List<Sons.Note>> c = Sons.lire(Sons.ressource("/sons.txt"));
        for (String id : new String[]{Sons.CARESSE, Sons.MOT, Sons.AVENTURE, Sons.CHOIX, Sons.ACHAT, Sons.PECHE,
                Sons.EXPEDITION, Sons.CAMPAGNE, Sons.PALIER, Sons.SUCCES}) {
            assertTrue(id, c.containsKey(id));
        }
        assertEquals(10, c.size());
    }

    @Test
    public void gardeCommeLePc() {
        Sons.Garde g = new Sons.Garde();
        assertFalse(g.peut(Sons.CARESSE, 0, "aucun", false, false));
        assertFalse(g.peut(Sons.CARESSE, 0, "normaux", true, false));
        assertFalse(g.peut(Sons.MOT, 0, "normaux", false, true));
        assertTrue(g.peut(Sons.CARESSE, 0, "discrets", false, true));
        assertFalse(g.peut(Sons.CHOIX, 500, "normaux", false, false));
        assertTrue(g.peut(Sons.CHOIX, 1300, "normaux", false, false));
        assertFalse(g.peut(Sons.CARESSE, 2600, "normaux", false, false));
        assertTrue(g.peut(Sons.CARESSE, 4100, "normaux", false, false));
    }

    @Test
    public void discretEstVraimentBas() {
        short[] d = Sons.adoucir(new short[]{16000, -16000, 1});
        assertEquals(3000, d[0]);
        assertEquals(-3000, d[1]);
        assertEquals(0, d[2]);
    }
}
