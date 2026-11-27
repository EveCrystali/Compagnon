package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Métiers et succès : catalogue identique au PC, heures et avancement reçus, compatibilité avec un ancien PC. */
public class MetiersTest {
    /** Même catalogue que Metiers.cs : le test C# (MetiersTelephoneTests) écrit ce fichier depuis le PC. */
    @Test
    public void memeCatalogueQueLePc() throws Exception {
        InputStream in = MetiersTest.class.getClassLoader().getResourceAsStream("metiers-succes.txt");
        assertNotNull("metiers-succes.txt (src/test/resources)", in);
        StringBuilder attendu = new StringBuilder();
        for (String l : new String(in.readAllBytes(), StandardCharsets.UTF_8).replace("\r\n", "\n").split("\n"))
            if (!l.startsWith("#") && !l.isEmpty()) attendu.append(l).append('\n');
        assertEquals(attendu.toString(), Metiers.catalogue());
        assertEquals(10, Metiers.TOUS.size());
        assertEquals(22, Metiers.SUCCES.size());
    }

    @Test
    public void niveauxEtTextes() {
        Metiers.Metier codeur = Metiers.metier("codeur"), joueur = Metiers.metier("joueur");
        assertTrue(codeur.travail);
        assertFalse(joueur.travail);
        assertEquals("⚒", codeur.signe());
        assertEquals("♪", joueur.signe());
        assertEquals(0, Metiers.niveau(codeur, 57));          // 5,7 h : Novice (Apprenti à 6 h)
        assertEquals(1, Metiers.niveau(codeur, 60));
        assertEquals(2, Metiers.niveau(joueur, 57));          // loisir : Compagnon dès 5 h
        assertEquals("5,7 h / 6 h", Metiers.progres(codeur, 57));
        assertEquals("6 h / 30 h", Metiers.progres(codeur, 60));
        assertEquals(6, Metiers.niveau(codeur, 15_000));
        assertEquals("1523 h", Metiers.progres(codeur, 15_234));
        assertEquals(0.95f, Metiers.part(codeur, 57), 0.001f);
        assertEquals(1f, Metiers.part(codeur, 20_000), 0.001f);
        assertEquals("2,5 h / 4 h", Metiers.progres(Metiers.succes("marathon"), 25));
        assertEquals("3 / 10", Metiers.progres(Metiers.succes("visio-man"), 30));
        assertEquals("vague 7 / 10", Metiers.progres(Metiers.succes("rempart"), 70));
        assertEquals("8765 / 10000 points", Metiers.progres(Metiers.succes("gardien"), 87_650));
        assertEquals("10 h / 10 h", Metiers.progres(Metiers.succes("melomane"), 999));  // borné au but
        assertEquals("", Metiers.progres(Metiers.succes("noctambule"), 10));
    }

    @Test
    public void lectureDuPcAJour() throws Exception {
        String json = "{\"v\":1,\"t\":1,\"metiers\":{\"musicien\":2},\"succes\":[\"melomane\",\"marathon\"],"
                + "\"heures\":{\"codeur\":57,\"musicien\":153,\"joueur\":2},\"avance\":{\"dactylo\":70,\"gamer\":2}}";
        Etat e = Etat.lire(json, 1);
        assertTrue(e.heuresConnues);
        List<Metiers.Ligne> l = Metiers.lignes(e);
        assertEquals("musicien", l.get(0).metier.id);          // trié par heures
        assertEquals("codeur", l.get(1).metier.id);
        assertEquals("Confirmé", l.get(0).grade());            // 15,3 h de musique (Confirmé à 15 h)
        assertEquals("15,3 h / 40 h", l.get(0).texte());
        assertEquals("5,7 h / 6 h", l.get(1).texte());
        assertEquals("Novice", l.get(1).grade());
        assertFalse(l.get(l.size() - 1).commence());           // 0 h : en dernier, grisé
        assertEquals(2, Metiers.obtenus(e));
        List<Metiers.Succes> s = Metiers.succesTries(e);
        assertEquals("marathon", s.get(0).id);                 // obtenus d'abord (ordre du catalogue)
        assertEquals("melomane", s.get(1).id);
        assertEquals(70, (int) e.avance.get("dactylo"));
        assertEquals("♪ Mélomane · Confirmé  ·  Succès 2/22", Metiers.resume(e));
    }

    @Test
    public void ancienPcEtAncienTelephone() throws Exception {
        // Ancien PC : niveaux et succès seulement (pas d'heures) : le niveau suffit pour l'affichage.
        Etat e = Etat.lire("{\"v\":1,\"t\":1,\"metiers\":{\"codeur\":2,\"joueur\":1},\"succes\":[\"marathon\"]}", 1);
        assertFalse(e.heuresConnues);
        List<Metiers.Ligne> l = Metiers.lignes(e);
        assertEquals("codeur", l.get(0).metier.id);
        assertEquals("Compagnon", l.get(0).grade());
        assertEquals("au moins 30 h", l.get(0).texte());
        assertEquals("pas encore commencé · 6 h pour Apprenti", l.get(l.size() - 1).texte()); // Facteur (travail), dernier
        assertTrue(Metiers.connus(e));
        // PC plus ancien encore : rien, la carte de l'accueil reste cachée.
        Etat vide = Etat.lire("{\"v\":1,\"t\":1}", 1);
        assertFalse(Metiers.connus(vide));
        assertEquals("Aucun métier commencé  ·  Succès 0/22", Metiers.resume(vide));
        // Valeurs étranges : ignorées sans erreur.
        Etat bizarre = Etat.lire("{\"v\":1,\"t\":1,\"metiers\":{\"codeur\":99,\"x\":\"a\"},\"heures\":{\"codeur\":-4},\"succes\":[1,\"\"]}", 1);
        assertTrue(bizarre.heures.isEmpty());
        assertEquals(6, (int) bizarre.metiers.get("codeur"));
    }
}
