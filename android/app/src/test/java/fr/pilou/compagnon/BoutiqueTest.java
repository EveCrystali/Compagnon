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

public class BoutiqueTest {
    @Test
    public void memeCatalogueQueLePc() {
        // Mêmes identifiants que Boutique.cs (objets neufs et anciennes récompenses).
        for (String id : new String[]{"chapeau-pirate", "haut-de-forme", "casquette", "bandeau-ninja", "cornes-viking", "aureole",
                "chapeau-sorcier", "couronne-fleurs", "lunettes-rondes", "monocle", "masque-plongee", "echarpe", "cape", "medaille",
                "baguette", "ballon-helium", "parapluie", "tasse-cafe", "petit-chat", "petit-poisson-bocal", "trainee-coeurs",
                "trainee-notes", "aura", "lavande", "corail-orange", "ardoise", "sable", "glacier", "feuille", "chapeaupeche",
                "etoilemer", "couleur-comete", "trainee-etoiles", "canne-doree", "marmite-cuivre", "pierre-calme"})
            assertNotNull(id, Boutique.trouver(id));
        Set<String> ids = new HashSet<>();
        for (Boutique.Article a : Boutique.CATALOGUE) {
            assertTrue(a.id, ids.add(a.id));
            assertTrue(a.id, a.prix >= 60 && a.prix <= 600);
            assertTrue(a.id, Arrays.asList(Boutique.RAYONS).contains(a.slot));
        }
        assertEquals(30, Boutique.trouver("canne-doree").niveauMin);
        assertEquals(270, Boutique.trouver("chapeaupeche").prix); // 60 + 15 × niveau 14
    }

    @Test
    public void refusEtPromo() {
        List<String> offres = Arrays.asList("cape", "monocle");
        Boutique.Article cape = Boutique.trouver("cape"), aura = Boutique.trouver("aura"), echarpe = Boutique.trouver("echarpe");
        assertEquals(210, Boutique.prix(cape, "cape"));
        assertNull(Boutique.refus(cape, 7, 500, offres, "cape", false));
        assertEquals("niveau 7", Boutique.refus(cape, 6, 500, offres, "cape", false));
        assertEquals("il manque 10 po", Boutique.refus(cape, 7, 200, offres, "cape", false));
        assertEquals("pas aujourd'hui", Boutique.refus(aura, 50, 5000, offres, "", false));
        assertEquals("à toi", Boutique.refus(echarpe, 1, 500, offres, "", true));
        assertNull(Boutique.refus(Boutique.trouver("pierre-calme"), 10, 500, offres, "", true)); // consommable : toujours achetable
    }

    @Test
    public void accesParNiveau() {
        assertFalse(Acces.jeuOuvert("peche", 1));
        assertTrue(Acces.jeuOuvert("peche", 2));
        assertTrue(Acces.jeuOuvert("chasse", 5));
        assertEquals(1, Acces.stade(9));
        assertEquals(2, Acces.stade(10));
        assertEquals(4, Acces.stade(41));
        assertEquals("Pilou Nimbus", Acces.nomStade(3));
    }

    @Test
    public void etatBoutiqueEtQuetes() throws Exception {
        String json = "{\"v\":1,\"t\":1,\"niveau\":7,\"po\":240,\"stade\":1,\"objets\":[\"echarpe\",\"feuille\"],\"porte\":{\"cou\":\"echarpe\"},"
                + "\"offres\":[\"cape\",\"monocle\"],\"promo\":\"cape\",\"serie\":3,"
                + "\"quetes\":[[0,\"Pêche 3 prises\",1,3,30,0],[1,\"Cuisine 5 plats\",5,5,120,1],[9]]}";
        Etat e = Etat.lire(json, 1);
        assertEquals(240, e.po);
        assertEquals(1, e.stade);
        assertTrue(e.objets.contains("feuille"));
        assertEquals("echarpe", e.porte.get("cou"));
        assertEquals(Arrays.asList("cape", "monocle"), e.offres);
        assertEquals(3, e.serie);
        assertEquals(2, e.quetes.size());
        assertTrue(e.quetes.get(1).reussie);
        assertEquals(30, e.quetes.get(0).po);
        assertEquals(-1, Etat.lire("{\"v\":1,\"t\":1}", 1).po);
    }

    @Test
    public void canneEtMarmiteSeulementPossedees() {
        assertTrue(Butin.poids(Butin.LEGENDAIRE, 30, true) > Butin.poids(Butin.LEGENDAIRE, 30));
        assertTrue(Butin.chanceRate(35, false, true) < Butin.chanceRate(35, false));
    }
}
