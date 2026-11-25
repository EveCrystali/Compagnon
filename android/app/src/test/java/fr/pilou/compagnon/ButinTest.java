package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Random;
import java.util.Set;

public class ButinTest {
    @Test
    public void memeCatalogueQueLePc() {
        assertEquals(23, Butin.PRISES.size());
        assertEquals(30, Butin.RECETTES.size());
        Set<String> ids = new HashSet<>();
        for (Butin.Prise p : Butin.PRISES) assertTrue(ids.add(p.id));
        assertEquals("★", Butin.signe(Butin.LEGENDAIRE));
        assertEquals("Pilou éternel", Butin.titre(50));
        assertEquals("Apprenti", Butin.titre(4));
        assertEquals(1, Butin.niveau(0));
        assertEquals(2, Butin.niveau(5));
        assertEquals(5, Butin.xpPourNiveau(2));
    }

    @Test
    public void seulPiloutRateSouventEtJamaisMieuxQueRare() {
        Random r = new Random(42);
        int prises = 0, n = 20_000;
        for (int i = 0; i < n; i++) {
            Butin.Prise p = Butin.tirer(r, 50, true);
            if (p == null) continue;
            prises++;
            assertTrue(p.rarete <= Butin.RARE);
        }
        assertEquals(Butin.CHANCE_SEUL, prises / (double) n, 0.02);
    }

    @Test
    public void aLaMainToujoursUnePriseDeSonNiveau() {
        Random r = new Random(7);
        for (int i = 0; i < 2000; i++) {
            Butin.Prise p = Butin.tirer(r, 3, false);
            assertNotNull(p);
            assertTrue(p.niveauMin <= 3);
        }
        assertEquals(2 * 14 + 5, Butin.xpPrise(Butin.trouver("crabe"), true));
    }

    @Test
    public void cuisineDecouverteEtPlatsInventes() {
        Map<String, Integer> stock = new HashMap<>();
        assertNull(Butin.cuisiner(new Random(1), 5, stock, new HashSet<>(), false));
        stock.put("botte", 2);
        assertFalse(Butin.peutCuisiner(stock));
        stock.put("goujon", 3);
        stock.put("algue", 2);
        Set<String> connues = new HashSet<>();
        int recettes = 0, inventes = 0;
        Random r = new Random(3);
        for (int i = 0; i < 200; i++) {
            Butin.Plat p = Butin.cuisiner(r, 5, stock, connues, true);
            assertNotNull(p);
            assertFalse(p.rate); // remuer annule le risque
            if (p.inventee) inventes++;
            else recettes++;
            if (p.decouverte) assertTrue(connues.add(p.id));
        }
        assertTrue(recettes > 0 && inventes > 0);
        assertTrue(connues.contains("grille") || connues.contains("soupe") || connues.contains("maki"));
        assertTrue(Butin.inventer(new Random(1), Butin.trouver("algue")).contains("d'algue frisée"));
    }

    @Test
    public void chanceDeBruler() {
        assertEquals(0, Butin.chanceRate(10, true), 1e-9);
        assertTrue(Butin.chanceRate(1, false) > Butin.chanceRate(40, false));
    }

    @Test
    public void canalRetourCommunAvecLePc() throws Exception {
        assertEquals("pilou-7f73fb3174ad7b3e4ba8e683", Chiffre.sujetRetour("ABCD-EFGH-JKMN-PQRS"));
        byte[] nonce = new byte[12];
        for (int i = 0; i < 12; i++) nonce[i] = (byte) (11 - i);
        String clair = "{\"v\":1,\"id\":\"abc123def456\",\"xp\":7,\"prises\":{\"goujon\":1},\"plats\":[\"grille\"],\"caresses\":2}";
        // Même chaîne que RetourTests.cs (le PC la relit).
        assertEquals("CwoJCAcGBQQDAgEAvHMcyNTTLMvvDj8R7ZMt3bH28CF4obx9dta8COWrOYM1NQ7ri8HsUENAELS04KyjJeltNiwaqSNgKQcAhKlOcorrxqvHN4+qrUPC/C01dhzJpg7S1QnAh0o84kghFMQt9EoIfFhpxjk=",
                Chiffre.chiffrer("ABCD-EFGH-JKMN-PQRS", clair, nonce));
        assertEquals(clair, Chiffre.dechiffrer("ABCD-EFGH-JKMN-PQRS", Chiffre.chiffrer("ABCD-EFGH-JKMN-PQRS", clair)));
    }

    @Test
    public void etatAvecProgression() throws Exception {
        String json = "{\"v\":1,\"t\":1000,\"nom\":\"Pilou\",\"niveau\":4,\"couleur\":\"lagon\",\"humeur\":\"repos\",\"sessions\":[],"
                + "\"xp\":80,\"accessoire\":\"lunettes\",\"carnet\":[\"goujon\"],\"plats\":[\"grille\"],\"inventes\":2,\"recus\":[\"g1\"]}";
        Etat e = Etat.lire(json, 1000);
        assertEquals(80, e.xp);
        assertEquals("lunettes", e.accessoire);
        assertTrue(e.carnet.contains("goujon"));
        assertTrue(e.plats.contains("grille"));
        assertEquals(2, e.inventes);
        assertEquals("g1", e.recus.get(0));
        // Un PC plus ancien n'envoie rien de tout ça : valeurs par défaut.
        Etat vieux = Etat.lire("{\"v\":1,\"t\":1000,\"sessions\":[]}", 1000);
        assertEquals(-1, vieux.xp);
        assertEquals("aucun", vieux.accessoire);
    }
}
