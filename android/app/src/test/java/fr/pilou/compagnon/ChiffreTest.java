package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.List;

public class ChiffreTest {
    // Vecteur produit par Telephone.cs (apps/PilouBureau/tests/VecteurTests.cs) : PC et téléphone doivent s'accorder.
    private static final String CODE = "ABCD-EFGH-JKMN-PQRS";
    private static final String CHIFFRE = "AAECAwQFBgcICQoLdnHe7OQSjDSwefD1Hz/Ct/0mAe65wBrMww7s7uYGSO1MSOZXww==";

    @Test
    public void memeSujetEtMemeClairQueLePc() throws Exception {
        assertEquals("pilou-a3616b163eefd2150b2b4fa2", Chiffre.sujet(CODE));
        assertEquals("{\"v\":1,\"nom\":\"Pilou\"}", Chiffre.dechiffrer("abcd efgh jkmn pqrs", CHIFFRE));
    }

    @Test(expected = java.security.GeneralSecurityException.class)
    public void mauvaisCodeRefuse() throws Exception {
        Chiffre.dechiffrer("ABCD-EFGH-JKMN-PQRT", CHIFFRE);
    }

    @Test
    public void codes() {
        assertTrue(Chiffre.valide("abcd-efgh-jkmn-pqrs"));
        assertFalse(Chiffre.valide("abcd"));
        assertEquals("ABCD-EFGH-JKMN-PQRS", Chiffre.formater("abcdefghjkmnpqrs"));
    }

    @Test
    public void lignesEtResume() throws Exception {
        long t = 1_800_000_000_000L;
        String json = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":4,\"titre\":\"x\",\"couleur\":\"bleu\",\"humeur\":\"repos\",\"calmes\":2,"
                + "\"sessions\":[{\"id\":\"b\",\"source\":\"codex\",\"libelle\":\"site\",\"etat\":\"permission\",\"depuis\":" + (t - 1000) + ",\"outil\":\"\"},"
                + "{\"id\":\"a\",\"source\":\"claude\",\"libelle\":\"api\",\"etat\":\"travail\",\"depuis\":" + (t - 65_000) + ",\"outil\":\"\"},"
                + "{\"id\":\"c\",\"source\":\"claude\",\"libelle\":\"docs\",\"etat\":\"fini\",\"depuis\":" + (t - 180_000) + ",\"outil\":\"\"}]}";
        Etat e = Etat.lire(json, t + 500);
        assertEquals(500, e.decalage);
        List<Etat.Ligne> l = e.lignes(t + 500, 0);
        assertEquals(3, l.size());
        assertEquals("❗ Codex · site · attend ton autorisation", l.get(0).toString());
        assertEquals("◐ api · réfléchit · 1 min", l.get(1).toString());
        assertEquals("✓ docs · fini · il y a 3 min", l.get(2).toString());
        assertEquals("❗ 1 t'attend  ·  ◐ 1 en cours  ·  ✓ 1 finie", e.resume(t + 500));
        assertEquals("inquiet", e.expression(t + 500));
        assertEquals("dort", e.expression(t + 26 * 60_000L));
    }
}
