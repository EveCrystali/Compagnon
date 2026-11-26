package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

/** Nouvelles des connecteurs du PC : champ « annonces » (5 au plus, plus récente en tête, contenu parfois masqué). */
public class NouvellesTest {
    @Test
    public void lectureDesAnnonces() throws Exception {
        long t = 1_790_000_000_000L;
        StringBuilder an = new StringBuilder();
        for (int i = 0; i < 7; i++)
            an.append(i == 0 ? "" : ",").append("{\"source\":\"mail\",\"titre\":\"✉ Léa\",\"texte\":\"").append(i == 1 ? "" : "sujet " + i)
                .append("\",\"t\":").append(t - i * 60_000L).append('}');
        Etat e = Etat.lire("{\"t\":" + t + ",\"nom\":\"Pilou\",\"annonces\":[" + an + ",{\"titre\":\"\"}]}", t);
        assertEquals(5, e.annonces.size());
        assertEquals("✉ Léa", e.annonces.get(0).titre);
        assertEquals("sujet 0", e.annonces.get(0).texte);
        assertEquals("", e.annonces.get(1).texte);          // « titre seulement » côté PC
        assertEquals("mail", e.annonces.get(0).source);
        assertTrue(e.annonces.get(0).t > e.annonces.get(1).t);
        // Ancien PC ou envoi coupé : aucune nouvelle, la carte reste cachée.
        assertTrue(Etat.lire("{\"t\":" + t + "}", t).annonces.isEmpty());
    }
}
