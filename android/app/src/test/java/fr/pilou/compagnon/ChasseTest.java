package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.util.List;

public class ChasseTest {
    private static Chasse partie() {
        Chasse c = new Chasse(42);
        c.commencer();
        return c;
    }

    @Test
    public void premiereVagueTroisRangsDeSept() {
        Chasse c = partie();
        assertEquals(1, c.vague);
        assertEquals(21, c.vivants());
        assertNull(c.boss);
        assertEquals(3, c.vies);
        assertTrue(c.evenements().contains(Chasse.Evenement.VAGUE));
    }

    @Test
    public void uneEtincelleTueUnBugEtRapporteSesPoints() {
        Chasse c = partie();
        Chasse.Bug b = c.bugs.get(0); // rang du haut : scarabée, 30 points
        c.tirAmi(b.x + 4, b.y + 3);
        c.collisions();
        assertFalse(b.vivant);
        assertEquals(30, c.score);
        assertTrue(c.evenements().contains(Chasse.Evenement.TOUCHE));
    }

    @Test
    public void vagueNettoyeeOuvreLaSuivanteEtLaCinquiemeALeBoss() {
        Chasse c = partie();
        for (Chasse.Bug b : c.bugs) b.vivant = false;
        c.avancer(0.02f);
        assertEquals(Chasse.Phase.ENTRE_VAGUES, c.phase);
        assertEquals(50, c.score);
        for (int i = 0; i < 100; i++) c.avancer(0.02f);
        assertEquals(2, c.vague);
        assertEquals(Chasse.Phase.JEU, c.phase);
        c.sauterA(5);
        assertNotNull(c.boss);
        assertEquals(0, c.bugs.size());
        assertTrue(c.evenements().contains(Chasse.Evenement.BOSS));
    }

    @Test
    public void leBossTombeSousLesEtincelles() {
        Chasse c = partie();
        c.sauterA(5);
        int pv = c.boss.pv;
        for (int i = 0; i < pv; i++) {
            c.tirAmi(c.boss.x + Chasse.Boss.L / 2, c.boss.y + 5);
            c.collisions();
        }
        assertNull(c.boss);
        assertEquals(250 + 50 * 5, c.score);
        assertFalse(c.bonus.isEmpty());
    }

    @Test
    public void lesAccoladesSEffritent() {
        Chasse c = partie();
        float bx = Chasse.boucliersX(0);
        // case (ligne 4, colonne 0) : pleine, 2 points de vie
        assertEquals(2, c.boucliers[0][4][0]);
        c.tirEnnemi(bx + 1, Chasse.BOUCLIER_Y + 4 * Chasse.CASE + 1);
        c.collisions();
        assertEquals(1, c.boucliers[0][4][0]);
        c.tirEnnemi(bx + 1, Chasse.BOUCLIER_Y + 4 * Chasse.CASE + 1);
        c.collisions();
        assertEquals(0, c.boucliers[0][4][0]);
        // le milieu de l'accolade est vide : une étincelle passe
        c.tirs.clear();
        c.tirAmi(bx + 6 * Chasse.CASE + 1, Chasse.BOUCLIER_Y + 3);
        c.collisions();
        assertEquals(1, c.tirs.stream().filter(t -> t.y > 0).count());
    }

    @Test
    public void cafeAccelereLeTirEtTestsVertsProtegent() {
        Chasse c = partie();
        c.poserBonus(c.joueurX + 2, Chasse.JOUEUR_Y, true);
        c.collisions();
        assertTrue(c.cafe > 0);
        c.evenements();
        for (int i = 0; i < 50; i++) c.avancer(0.02f); // 1 s
        long rapide = c.evenements().stream().filter(e -> e == Chasse.Evenement.TIR).count();
        Chasse lent = partie();
        lent.evenements();
        for (int i = 0; i < 50; i++) lent.avancer(0.02f);
        long normal = lent.evenements().stream().filter(e -> e == Chasse.Evenement.TIR).count();
        assertTrue("tir rapide : " + rapide + " contre " + normal, rapide >= 5 && rapide >= normal + 3);

        Chasse d = partie();
        d.poserBonus(d.joueurX + 2, Chasse.JOUEUR_Y, false);
        d.collisions();
        assertTrue(d.tests > 0);
        d.blesser();
        assertEquals(3, d.vies);      // le bouclier a pris le coup
        assertEquals(0, d.tests, 0.001);
    }

    @Test
    public void troisBlessuresEtCestFini() {
        Chasse c = partie();
        for (int i = 0; i < 3; i++) {
            c.invulnerable = 0;
            c.blesser();
        }
        assertEquals(0, c.vies);
        assertEquals(Chasse.Phase.FIN, c.phase);
        List<Chasse.Evenement> e = c.evenements();
        assertTrue(e.contains(Chasse.Evenement.FIN));
    }

    @Test
    public void lesBugsQuiAtteignentLaProdTerminentLaPartie() {
        Chasse c = partie();
        for (Chasse.Bug b : c.bugs) b.y += 120;
        c.avancer(0.02f);
        assertEquals(Chasse.Phase.FIN, c.phase);
    }

    @Test
    public void xpPlafonneeEtPause() {
        Chasse c = partie();
        assertEquals(0, c.xp());
        c.score = 100_000;
        c.vague = 40;
        assertEquals(Chasse.XP_MAX, c.xp());
        c.score = 10;
        c.vague = 1;
        assertEquals(1, c.xp());
        c.pause(true);
        assertEquals(Chasse.Phase.PAUSE, c.phase);
        float x = c.bugs.get(0).x;
        c.avancer(0.02f);
        assertEquals(x, c.bugs.get(0).x, 0.0001);
        c.pause(false);
        assertEquals(Chasse.Phase.JEU, c.phase);
    }

    @Test
    public void policeCouvreLesTextesDuJeu() {
        assertEquals("PARTIE TERMINEE", Police.simple("Partie terminée"));
        assertEquals(11, Police.largeur("ABC"));
    }
}
