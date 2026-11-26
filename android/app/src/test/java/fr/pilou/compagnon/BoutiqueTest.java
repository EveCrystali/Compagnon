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
            assertTrue(a.id, a.prix >= 30 && a.prix <= 2200); // titres à 30 po … mythiques
            assertTrue(a.id, Arrays.asList(Boutique.RAYONS).contains(Boutique.rayonDe(a.slot)));
            boolean palier = false;
            for (int p : Boutique.PALIERS) palier |= p == a.niveauMin;
            assertTrue(a.id + " : rangée d'un palier", palier);
        }
        assertEquals(30, Boutique.trouver("canne-doree").niveauMin);
        assertEquals(270, Boutique.trouver("chapeaupeche").prix); // 60 + 15 × niveau 14
    }

    @Test
    public void refusEtPromo() {
        Boutique.Article cape = Boutique.trouver("cape"), aura = Boutique.trouver("aura"), echarpe = Boutique.trouver("echarpe");
        assertEquals(210, Boutique.prix(cape, "cape"));
        assertNull(Boutique.refus(cape, 5, 500, "cape", false));
        assertEquals("niveau 5", Boutique.refus(cape, 4, 500, "cape", false));
        assertEquals("il manque 10 po", Boutique.refus(cape, 7, 200, "cape", false));
        // Plus de « pas aujourd'hui » : hors des offres, tout ce qui est dans une rangée ouverte s'achète.
        assertNull(Boutique.refus(aura, 50, 5000, "", false));
        assertEquals("à toi", Boutique.refus(echarpe, 1, 500, "", true));
        assertNull(Boutique.refus(Boutique.trouver("pierre-calme"), 10, 500, "", true)); // consommable : toujours achetable
    }

    @Test
    public void lesNiveauxOuvrentDesRangees() {
        assertEquals(1, Boutique.palier(0));
        assertEquals(1, Boutique.palier(4));
        assertEquals(5, Boutique.palier(5));
        assertEquals(15, Boutique.palier(19));
        assertEquals(50, Boutique.palier(99));
        assertEquals(5, Boutique.prochainPalier(1));
        assertEquals(30, Boutique.prochainPalier(20));
        assertEquals(0, Boutique.prochainPalier(50));
        for (int p : Boutique.PALIERS) assertFalse("palier " + p, Boutique.rayonsDuPalier(p).isEmpty());
        for (String r : Boutique.RAYONS) {
            int k = 0;
            for (int p : Boutique.PALIERS) k += Boutique.rangee(r, p).size();
            assertTrue(r, k > 0);
        }
        assertTrue(Boutique.rangee(Boutique.DOS, 15).contains(Boutique.trouver("carapace")));
        for (Boutique.Article a : Boutique.debloques(14, 15)) assertEquals(15, a.niveauMin);
        assertTrue(Boutique.debloques(15, 19).isEmpty());
        assertEquals(Boutique.SPECIAUX, Boutique.rayonDe(Boutique.BONUS));
        assertFalse(Boutique.surPilou(Boutique.FOND));
        assertFalse(Boutique.surPilou(Boutique.BULLE));
        assertTrue(Boutique.surPilou(Boutique.DOS));
        assertNotNull(Boutique.style("bulle-nuit"));
        assertTrue(Boutique.style("bulle-nuit").sombre);
        assertNull(Boutique.style("rien"));
        String s = Vitrine.prochaineRangee(14, Butin.xpPourNiveau(14));
        assertTrue(s, s.contains("niveau 15") && s.contains("encore " + (Butin.xpPourNiveau(15) - Butin.xpPourNiveau(14)) + " xp"));
        assertEquals("", Vitrine.prochaineRangee(50, 0));
    }

    /** Les nouveaux objets de la boutique rétro : au catalogue, et dessinés (ou teinte, ou cadre de bulle). */
    @Test
    public void nouveauxObjetsDessines() {
        String[] nouveaux = {"beret", "bonnet-pompon", "casque-chantier", "sombrero", "chapeau-cowboy", "oreilles-chat", "couronne-laurier",
                "antenne-neon", "lunettes-3d", "visiere-pilote", "lunettes-coeur", "bandana", "noeud-pois", "cravate", "collier-perles",
                "sac-a-dos", "carapace", "ailes-papillon", "jetpack", "sucette", "epee-mousse", "lanterne", "guitare", "canne-or", "baskets",
                "palmes", "patins", "oiseau", "petit-robot", "fantome", "mini-dragon", "bulles-savon", "confettis", "trainee-prisme", "aura-feu",
                "pervenche", "mandarine", "miel", "prune", "acier", "peche", "fond-nuit", "fond-foret", "fond-plage", "fond-arcade",
                "fond-espace", "bulle-doree", "bulle-nuit", "bulle-pixel", "bulle-nuages"};
        assertTrue(nouveaux.length >= 40);
        for (String id : nouveaux) {
            Boutique.Article a = Boutique.trouver(id);
            assertNotNull(id, a);
            if (a.slot.equals(Boutique.COULEUR)) assertNotNull(id, Sprites.banque().teintes.get(id));
            else if (a.slot.equals(Boutique.BULLE)) assertNotNull(id, Boutique.style(id));
            else {
                assertNotNull(id, Sprites.banque().get(id));
                if (!a.slot.equals(Boutique.FOND)) assertEquals(id, a.slot, Sprites.banque().get(id).slot);
            }
        }
        // Tous les articles portables : un dessin, une teinte ou un cadre.
        for (Boutique.Article a : Boutique.CATALOGUE) {
            if (!Arrays.asList(Boutique.SLOTS).contains(a.slot) || a.slot.equals(Boutique.TITRE)) continue;
            String t = Vitrine.teinte(a.id);
            assertTrue(a.id, Sprites.banque().get(a.id) != null || Sprites.banque().teintes.get(t) != null || Boutique.style(a.id) != null
                    || a.id.equals(Boutique.TRAINEE_ETOILES));
        }
        for (String id : new String[]{"cadenas", "badge-boutique", "po-tourne", "pierre-calme", "canne-doree", "marmite-cuivre"})
            assertNotNull(id, Sprites.banque().get(id));
    }

    /** Même catalogue que Boutique.cs : identifiants, emplacements, prix et rangées (lu dans le source du PC). */
    @Test
    public void memesPrixEtRangeesQueLePc() throws Exception {
        java.io.File f = new java.io.File("../../apps/PilouBureau/Boutique.cs");
        org.junit.Assume.assumeTrue(f.exists());
        String cs = new String(java.nio.file.Files.readAllBytes(f.toPath()), java.nio.charset.StandardCharsets.UTF_8);
        java.util.regex.Matcher m = java.util.regex.Pattern
                .compile("new\\(\"([a-z0-9-]+)\", \"[^\"]+\", (\\w+), (\\d+), (\\d+), Rarete").matcher(cs);
        int vus = 0;
        while (m.find()) {
            Boutique.Article a = Boutique.trouver(m.group(1));
            assertNotNull(m.group(1), a);
            assertEquals(m.group(1), m.group(2).toLowerCase(java.util.Locale.ROOT), a.slot);
            assertEquals(m.group(1), Integer.parseInt(m.group(3)), a.prix);
            assertEquals(m.group(1), Integer.parseInt(m.group(4)), a.niveauMin);
            vus++;
        }
        assertTrue("articles lus dans Boutique.cs : " + vus, vus >= 80);
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
