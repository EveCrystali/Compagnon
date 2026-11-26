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
import java.util.List;

/** Même modèle que le PC (apps/PilouBureau/tests/SoinsTests.cs) : mêmes vecteurs, mêmes résultats. */
public class SoinsTest {
    private static final double H = 3600_000, T0 = 1_789_999_200_000d;

    private static Soins.Action a(String id, String type, double heures, String objet) {
        return new Soins.Action(id, type, T0 + heures * H, objet);
    }

    private static final List<Soins.Action> VECTEUR = Arrays.asList(
            a("a1", "nourrir", 10, "gateau"),
            a("a2", "rythme", 12, "exigeant"), // ancien réglage de difficulté : ignoré
            a("a3", "laver", 20, ""),
            a("a4", "vacances", 24, "1"),
            a("a5", "vacances", 48, "0"),
            a("a6", "caresse", 50, ""));

    @Test
    public void vecteurCommunAvecLePc() {
        // Dans le désordre : l'ordre vient des heures, pas de l'arrivée.
        List<Soins.Action> melange = new java.util.ArrayList<>(VECTEUR);
        Collections.reverse(melange);
        Soins.EtatSoins e = Soins.calculer(Soins.neuf(T0), melange, T0 + 54 * H);
        assertEquals(100 - 20 * 100 / 36.0, e.faim, 1e-6);
        assertEquals(100 - 10 * 100 / 48.0, e.proprete, 1e-6);
        assertEquals(25, e.moral, 1e-6);
        assertFalse(e.vacances);
        assertFalse(e.boude);
        assertEquals(76.861989, Math.round(e.score * 1e6) / 1e6, 1e-9);
    }

    @Test
    public void decroissanceLenteEtMemeRythmePourTous() {
        Soins.EtatSoins e = Soins.calculer(Soins.neuf(T0), Collections.<Soins.Action>emptyList(), T0 + 18 * H);
        assertEquals(50, e.faim, 1e-6);
        assertEquals(62.5, e.proprete, 1e-6);
        assertEquals(40, e.moral, 1e-6);
        // Un ancien journal avec « rythme doux » ou « exigeant » : même état, sans erreur.
        for (String r : new String[]{"doux", "exigeant", "n'importe quoi"})
            assertEquals(50, Soins.calculer(Soins.neuf(T0), Collections.singletonList(a("r", "rythme", 0, r)), T0 + 18 * H).faim, 1e-6);
        assertTrue(Soins.manques(Soins.calculer(Soins.neuf(T0), Collections.<Soins.Action>emptyList(), T0 + 6 * H)).isEmpty());
    }

    @Test
    public void vacancesFigentTout() {
        Soins.EtatSoins e = Soins.calculer(Soins.neuf(T0), Collections.singletonList(a("v", "vacances", 1, "1")), T0 + 500 * H);
        assertTrue(e.vacances);
        assertEquals(100 - 100 / 36.0, e.faim, 1e-6);
        assertFalse(Soins.boudeur(e));
        assertFalse(Soins.rayonnant(e));
        assertEquals(1, Soins.multiplicateur(e), 0);
    }

    @Test
    public void unToucherComble() {
        Soins.EtatSoins b = Soins.neuf(T0);
        b.faim = 8;
        b.proprete = 20;
        b.moral = 5;
        assertEquals(Arrays.asList(Soins.MORAL, Soins.FAIM, Soins.PROPRETE), Soins.manques(b));
        Soins.EtatSoins nourri = Soins.calculer(b, Collections.singletonList(a("n", "nourrir", 0, "gateau")), T0);
        assertEquals(100, nourri.faim, 0);
        assertEquals(20, nourri.moral, 0);
        Soins.EtatSoins tout = Soins.calculer(b, Collections.singletonList(a("s", "soin", 0, "")), T0);
        assertTrue(Soins.rayonnant(tout));
        assertEquals(12, Soins.bonus(10, tout));
        assertEquals(10, Soins.bonus(10, b)); // besoins bas, mais il ne boude pas encore
        assertEquals(15, Soins.bonusEnCas("plat-soupe"));
        assertEquals("◒", Soins.signe(Soins.FAIM));
    }

    // Bouderie (mêmes cas que SoinsTests.cs) : deux besoins sous 20 %, il boude aussitôt.
    @Test
    public void deuxBesoinsBasIlBoudePuisSeLaisseAmadouer() {
        List<Soins.Action> rien = Collections.emptyList();
        Soins.EtatSoins neuf = Soins.neuf(T0);
        assertFalse(Soins.boudeur(Soins.calculer(neuf, rien, T0 + 28 * H))); // le moral seul est bas depuis 4 h
        Soins.EtatSoins a29 = Soins.calculer(neuf, rien, T0 + 29 * H);
        assertTrue(Soins.boudeur(a29)); // la faim passe sous 20 % aussi
        assertFalse(Soins.amadoue(a29));
        assertEquals(0.6, Soins.multiplicateur(a29), 0);
        assertEquals(6, Soins.bonus(10, a29));
        assertEquals(3, Soins.bonus(5, a29));
        assertEquals(9, Soins.bonus(15, a29));
        assertEquals(1, Soins.bonus(1, a29)); // un gain rapporte toujours au moins 1
        assertEquals(0, Soins.bonus(0, a29));

        // Une caresse ne suffit pas (le moral reste bas) ; le soin complet, si : 30 min de rancune.
        Soins.EtatSoins caresse = Soins.calculer(neuf, Collections.singletonList(a("c", "caresse", 30, "")), T0 + 30.5 * H);
        assertTrue(Soins.boudeur(caresse));
        assertFalse(Soins.amadoue(caresse));
        List<Soins.Action> soin = Collections.singletonList(a("s", "soin", 31, ""));
        Soins.EtatSoins amadoue = Soins.calculer(neuf, soin, T0 + 31.25 * H);
        assertTrue(Soins.boudeur(amadoue));
        assertTrue(Soins.amadoue(amadoue));
        assertEquals(6, Soins.bonus(10, amadoue)); // les gains restent réduits tant qu'il boude
        assertEquals(T0 + 31.5 * H, amadoue.finBouderie, 0);
        Soins.EtatSoins reconcilie = Soins.calculer(neuf, soin, T0 + 31.5 * H);
        assertFalse(Soins.boudeur(reconcilie));
        assertTrue(Soins.rayonnant(reconcilie));
        assertEquals(12, Soins.bonus(10, reconcilie)); // rayonnant : × 1,2
        assertEquals(6, Soins.bonus(5, reconcilie));
    }

    @Test
    public void unSeulBesoinBasSixHeuresEtIlBoude() {
        List<Soins.Action> soins = Arrays.asList(a("n", "nourrir", 20, ""), a("l", "laver", 20, ""));
        Soins.EtatSoins avant = Soins.calculer(Soins.neuf(T0), soins, T0 + 29.5 * H); // moral sous 20 % depuis 24 h
        assertFalse(Soins.boudeur(avant));
        assertEquals(1, Soins.multiplicateur(avant), 0);
        assertTrue(Soins.boudeur(Soins.calculer(Soins.neuf(T0), soins, T0 + 30 * H)));
        // Un câlin à temps : le compteur de négligence repart de zéro.
        List<Soins.Action> calin = new java.util.ArrayList<>(soins);
        calin.add(a("c", "calin", 27, ""));
        Soins.EtatSoins c = Soins.calculer(Soins.neuf(T0), calin, T0 + 32 * H);
        assertFalse(Soins.boudeur(c));
        assertEquals(0, c.neglige, 0);
        // En vacances, il ne boude pas.
        assertFalse(Soins.boudeur(Soins.calculer(Soins.neuf(T0), Collections.singletonList(a("v", "vacances", 0, "1")), T0 + 100 * H)));
    }

    @Test
    public void etatDuPcEtActionsEnJson() throws Exception {
        assertNull(Soins.lireEtat(new JSONObject("{\"f\":3}")));
        // Un ancien état avec « r » (rythme) se lit sans erreur ; la bouderie voyage (n, b, fb).
        Soins.EtatSoins e = Soins.lireEtat(new JSONObject("{\"f\":120,\"p\":-4,\"m\":55.5,\"s\":70,\"t\":5,\"r\":\"bizarre\",\"v\":1}"));
        assertNotNull(e);
        assertEquals(100, e.faim, 0);
        assertEquals(0, e.proprete, 0);
        assertTrue(e.vacances);
        assertFalse(e.boude);
        Soins.EtatSoins b = Soins.lireEtat(new JSONObject("{\"f\":100,\"p\":100,\"m\":100,\"s\":70,\"t\":5,\"v\":0,\"n\":0,\"b\":1,\"fb\":1800005}"));
        assertTrue(Soins.amadoue(b));
        assertEquals(1800005, b.finBouderie, 0);
        Soins.Action x = Soins.lireAction(Soins.json(a("id1", "nourrir", 2, "pomme")));
        assertEquals("pomme", x.objet);
        assertEquals(T0 + 2 * H, x.t, 0);
        assertEquals(3, Soins.json(a("id2", "laver", 0, "")).length());
    }
}
