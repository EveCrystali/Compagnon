package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/** Expéditions vues du téléphone (lecture seule) : ce que publie Expeditions.PourTelephone sur le PC. */
public class ExpeditionTest {
    @Test
    public void enRouteEtDernierJournal() throws Exception {
        long t = 1_790_000_000_000L;
        String json = "{\"v\":1,\"t\":" + t + ",\"sessions\":[],\"expedition\":{\"energie\":42,\"reste\":2,\"libre\":0,"
                + "\"etat\":\"en\",\"lieu\":\"Caverne des câbles\",\"retour\":" + (t + 20 * 60_000) + ",\"issue\":\"defaite\","
                + "\"dernier\":\"Tour du tampon\",\"t\":" + (t - 3600_000) + ",\"journal\":[\"✦ Départ\",\"✕ Bon. On dira que c'était un repérage.\"]}}";
        Etat e = Etat.lire(json, t);
        assertTrue(e.expedition.enRoute());
        assertEquals(42, e.expedition.energie);
        assertEquals("Caverne des câbles", e.expedition.lieu);
        assertEquals(t + 20 * 60_000, e.expedition.retour);
        assertTrue(e.expedition.ligne(t).startsWith("en expédition · Caverne des câbles · retour vers "));
        assertEquals("✕", e.expedition.signe());
        assertEquals("défaite", e.expedition.nomIssue());
        assertEquals(2, e.expedition.journal.size());
    }

    @Test
    public void reposEtAncienPc() throws Exception {
        long t = 1_790_000_000_000L;
        Etat e = Etat.lire("{\"v\":1,\"t\":" + t + ",\"sessions\":[],\"expedition\":{\"energie\":150,\"reste\":1,\"etat\":\"repos\",\"libre\":"
                + (t + 12 * 60_000) + "}}", t);
        assertFalse(e.expedition.enRoute());
        assertEquals(100, e.expedition.energie);
        assertEquals("se repose encore 12 min", e.expedition.ligne(t));
        assertTrue(e.expedition.journal.isEmpty());
        Etat sansRien = Etat.lire("{\"v\":1,\"t\":" + t + ",\"sessions\":[],\"expedition\":{\"reste\":0,\"etat\":\"pret\"}}", t);
        assertEquals("trois expéditions aujourd'hui : il repart demain", sansRien.expedition.ligne(t));
        assertNull(Etat.lire("{\"v\":1,\"t\":" + t + ",\"sessions\":[]}", t).expedition);
    }
}
