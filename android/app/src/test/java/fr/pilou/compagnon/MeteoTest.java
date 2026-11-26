package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.json.JSONObject;
import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;

/** Météo reçue du PC : lecture du champ « meteo », mêmes effets que Meteo.cs selon ce que Pilou porte. */
public class MeteoTest {
    @Test
    public void lectureDuMessage() throws Exception {
        long t = 1_790_000_000_000L;
        String json = "{\"t\":" + t + ",\"nom\":\"Pilou\",\"meteo\":{\"etat\":\"pluie\",\"temperature\":8.4,\"ville\":\"Paris\",\"signe\":\"☂\"}}";
        Etat e = Etat.lire(json, t);
        assertNotNull(e.meteo);
        assertEquals(Meteo.PLUIE, e.meteo.etat);
        assertEquals(8, e.meteo.temperature);
        assertEquals("☂ pluie · 8 °C · Paris", e.meteo.ligne());
        assertEquals(Meteo.PLUIE, e.etatMeteo(t + 60_000));
        assertEquals("", e.etatMeteo(t + Etat.METEO_VALIDE + 1));   // trop vieille : on ne la montre plus
        // Champ absent (connecteur coupé, ancien PC) ou état inconnu : pas de météo.
        assertNull(Etat.lire("{\"t\":" + t + "}", t).meteo);
        assertNull(Meteo.lire(new JSONObject("{\"etat\":\"tempete-de-grenouilles\"}")));
        assertEquals("❄", Meteo.lire(new JSONObject("{\"etat\":\"neige\"}")).signe);
    }

    @Test
    public void mouilleSansParapluieAuSecAvec() {
        Meteo.Effet sans = Meteo.effet(Meteo.PLUIE, Collections.singletonList("echarpe"), 0);
        assertFalse(sans.protege);
        assertEquals("mouille", sans.inconfort);
        assertTrue(sans.sprites.contains("meteo-mouille"));
        for (String abri : new String[]{"parapluie", "parapluie-etoile", "impermeable"}) {
            Meteo.Effet avec = Meteo.effet(Meteo.AVERSE, Collections.singletonList(abri), 0);
            assertTrue(abri, avec.protege);
            assertFalse(abri, avec.sprites.contains("meteo-mouille"));
        }
        assertTrue(Meteo.effet(Meteo.ORAGE, Collections.<String>emptyList(), 0).sprites.contains("meteo-eclair"));
        assertTrue(Meteo.effet(Meteo.NEIGE, Collections.singletonList("acc-bonnet"), 0).protege);
        assertEquals("froid", Meteo.effet(Meteo.FROID, Collections.<String>emptyList(), 0).inconfort);
        assertEquals("sueur", Meteo.effet(Meteo.CHALEUR, Collections.<String>emptyList(), 0).reaction);
        assertTrue(Meteo.effet(Meteo.CHALEUR, Collections.singletonList("eventail"), 0).protege);
        assertTrue(Meteo.effet(Meteo.DEGAGE, Collections.<String>emptyList(), 0) == Meteo.Effet.AUCUN);
        assertTrue(Meteo.effet("", Collections.<String>emptyList(), 0) == Meteo.Effet.AUCUN);
    }

    @Test
    public void appliqueeALAllure() {
        RenduPilou.Allure a = new RenduPilou.Allure();
        a.objets = Arrays.asList("casquette");
        Meteo.appliquer(a, Meteo.PLUIE, 0);
        assertTrue(a.objets.contains("casquette"));
        assertTrue(a.objets.contains("meteo-pluie"));
        assertTrue(a.objets.contains("meteo-mouille"));
        assertEquals("grimace", a.expr);                         // t = 0 : moment grognon
        RenduPilou.Allure b = new RenduPilou.Allure();
        b.accessoire = "lunettes";                               // l'accessoire compte (« acc-lunettes »)
        Meteo.appliquer(b, Meteo.CHALEUR, 0);
        assertEquals("", b.reaction);
        assertEquals("repos", b.expr);
        // Les sprites existent dans la banque partagée (mêmes fichiers que le PC).
        for (String id : new String[]{"meteo-pluie", "meteo-averse", "meteo-mouille", "meteo-eclair", "meteo-neige", "meteo-givre",
                "meteo-soleil", "meteo-vent", "meteo-brouillard", "impermeable", "bottes-pluie", "moufles", "eventail", "parapluie-etoile"})
            assertNotNull(id, Sprites.banque().get(id));
    }

    @Test
    public void objetsMeteoEnBoutique() {
        assertEquals(Boutique.PIEDS, Boutique.trouver("bottes-pluie").slot);
        assertEquals(Boutique.DOS, Boutique.trouver("impermeable").slot);
        assertEquals(10, Boutique.trouver("parapluie-etoile").niveauMin); // rangée du palier 10
        assertTrue(Arrays.asList(Boutique.SLOTS).contains(Boutique.PIEDS));
        assertEquals("Pieds", Boutique.nomSlot(Boutique.PIEDS));
    }
}
