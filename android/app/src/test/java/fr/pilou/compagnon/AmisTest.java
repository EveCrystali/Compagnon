package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class AmisTest {
    private static String hex(byte[] b) {
        return Amis.hex(b, b.length);
    }

    // Même vecteur que apps/PilouBureau/tests/AmisTests.cs (VecteurCommunAvecLeTelephone).
    @Test
    public void memesDerivationsQueLePc() throws Exception {
        assertEquals("pilou-85913c41bb6794a5b77c6709", Amis.sujetBoite("PILOU-ABCD-EFGH-JKMN"));
        assertEquals(Amis.sujetBoite("PILOU-ABCD-EFGH-JKMN"), Amis.sujetBoite("abcd efgh jkmn"));
        assertEquals("d3b777c4a2b5cd51c1c107381b283c7be4ef1b066da675e1430ee805d5b538a4", hex(Amis.cleBoite("ABCDEFGHJKMN")));
        byte[] secret = new byte[32];
        for (int i = 0; i < 32; i++) secret[i] = (byte) i;
        assertEquals("pilou-abbaa91136238890812f2bd3", Amis.sujetPaire(secret, "PILOU-ABCD-EFGH-JKMN", "PILOU-PQRS-TUVW-XYZ2"));
        assertEquals(Amis.sujetPaire(secret, "PQRSTUVWXYZ2", "ABCDEFGHJKMN"), Amis.sujetPaire(secret, "ABCDEFGHJKMN", "PQRSTUVWXYZ2"));
        assertEquals("84365017af9cc44dd3433b1b13c2eb20dd7b83b04f12bed742b82a3873b1ff64",
                hex(Amis.clePaire(secret, "PILOU-ABCD-EFGH-JKMN", "PILOU-PQRS-TUVW-XYZ2")));
        assertEquals("GQWMKMXKYVZM", Amis.empreinte(secret));
        assertTrue(Amis.valide("PILOU-7F3K-9QXA-M2HT"));
        assertFalse(Amis.valide("ABCD-EFGH-JKMN-PQRS"));
    }

    @Test
    public void amisEtVisiteLusDansLEtat() throws Exception {
        long t = 1_800_000_000_000L;
        String json = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":9,\"sessions\":[],"
                + "\"visite\":\"parti chez Léo · retour vers 14 h 20\","
                + "\"amis\":[{\"nom\":\"Léo\",\"niveau\":12,\"stade\":3,\"t\":" + (t - 60_000) + "},"
                + "{\"nom\":\"Zoé\",\"niveau\":4,\"stade\":9,\"t\":" + (t - 3_600_000) + "},{\"nom\":\"Max\",\"actif\":false},{\"niveau\":3}]}";
        Etat e = Etat.lire(json, t);
        assertEquals(3, e.amis.size());
        assertEquals("parti chez Léo · retour vers 14 h 20", e.visite);
        assertTrue(e.amis.get(0).enLigne(t));
        assertEquals("niveau 12 · Nimbus · en ligne", e.amis.get(0).texte(t));
        assertEquals("niveau 4 · Astral · vu il y a 1 h 00", e.amis.get(1).texte(t));
        assertEquals("niveau 1 · Pilou · en attente", e.amis.get(2).texte(t));
        assertEquals("", Etat.lire("{\"v\":1,\"t\":" + t + ",\"sessions\":[]}", t).visite);
    }
}
