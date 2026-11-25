package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class GroupeTest {
    // Même vecteur que apps/PilouBureau/tests/GroupeTests.cs : PC et téléphone dérivent le même sujet de groupe.
    @Test
    public void memeSujetDeGroupeQueLePc() throws Exception {
        assertEquals("pilou-4404248bb27fbeba24ba6972", Chiffre.sujetGroupe("ABCD-EFGH-JKMN-PQRS"));
        assertEquals(Chiffre.sujetGroupe("ABCD-EFGH-JKMN-PQRS"), Chiffre.sujetGroupe("abcd efgh jkmn pqrs"));
    }

    @Test
    public void appareilsDuGroupeLusDansLEtat() throws Exception {
        long t = 1_800_000_000_000L;
        String json = "{\"v\":1,\"t\":" + t + ",\"niveau\":9,\"xp\":420,\"sessions\":[],"
                + "\"appareils\":[{\"nom\":\"PERSO\",\"xp\":300,\"t\":" + t + "},{\"nom\":\"TAGG\",\"xp\":120,\"t\":" + (t - 180_000) + "},{\"xp\":5}]}";
        Etat e = Etat.lire(json, t);
        assertEquals(2, e.appareils.size());
        assertEquals("TAGG · 120 xp · vu il y a 3 min", e.appareils.get(1).texte(t));
        assertEquals(420, e.xp);
    }
}
