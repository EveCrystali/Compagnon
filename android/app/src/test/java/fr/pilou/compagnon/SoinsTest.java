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
            a("a2", "rythme", 12, "exigeant"),
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
        assertEquals(100 - (2 + 12 * 1.6 + 6 * 1.6) * 100 / 36, e.faim, 1e-6);
        assertEquals(100 - (4 * 1.6 + 6 * 1.6) * 100 / 48, e.proprete, 1e-6);
        assertEquals(0, e.moral, 1e-6);
        assertEquals("exigeant", e.rythme);
        assertFalse(e.vacances);
        assertEquals(73.792665, Math.round(e.score * 1e6) / 1e6, 1e-9);
    }

    @Test
    public void decroissanceLenteEtRythmes() {
        Soins.EtatSoins e = Soins.calculer(Soins.neuf(T0), Collections.<Soins.Action>emptyList(), T0 + 18 * H);
        assertEquals(50, e.faim, 1e-6);
        assertEquals(62.5, e.proprete, 1e-6);
        assertEquals(40, e.moral, 1e-6);
        Soins.EtatSoins doux = Soins.calculer(Soins.neuf(T0), Collections.singletonList(a("r", "rythme", 0, "doux")), T0 + 18 * H);
        assertEquals(70, doux.faim, 1e-6);
        assertTrue(Soins.manques(Soins.calculer(Soins.neuf(T0), Collections.<Soins.Action>emptyList(), T0 + 6 * H)).isEmpty());
    }

    @Test
    public void vacancesFigentTout() {
        Soins.EtatSoins e = Soins.calculer(Soins.neuf(T0), Collections.singletonList(a("v", "vacances", 1, "1")), T0 + 500 * H);
        assertTrue(e.vacances);
        assertEquals(100 - 100 / 36.0, e.faim, 1e-6);
        assertFalse(Soins.terne(e));
        assertFalse(Soins.rayonnant(e));
    }

    @Test
    public void unToucherComble() {
        Soins.EtatSoins b = Soins.neuf(T0);
        b.faim = 8;
        b.proprete = 20;
        b.moral = 5;
        assertEquals(Arrays.asList(Soins.MORAL, Soins.FAIM, Soins.PROPRETE), Soins.manques(b));
        assertTrue(Soins.terne(b));
        Soins.EtatSoins nourri = Soins.calculer(b, Collections.singletonList(a("n", "nourrir", 0, "gateau")), T0);
        assertEquals(100, nourri.faim, 0);
        assertEquals(20, nourri.moral, 0);
        Soins.EtatSoins tout = Soins.calculer(b, Collections.singletonList(a("s", "soin", 0, "")), T0);
        assertTrue(Soins.rayonnant(tout));
        assertEquals(15, Soins.bonusEnCas("plat-soupe"));
        assertEquals("◒", Soins.signe(Soins.FAIM));
    }

    @Test
    public void etatDuPcEtActionsEnJson() throws Exception {
        assertNull(Soins.lireEtat(new JSONObject("{\"f\":3}")));
        Soins.EtatSoins e = Soins.lireEtat(new JSONObject("{\"f\":120,\"p\":-4,\"m\":55.5,\"s\":70,\"t\":5,\"r\":\"bizarre\",\"v\":1}"));
        assertNotNull(e);
        assertEquals(100, e.faim, 0);
        assertEquals(0, e.proprete, 0);
        assertEquals("normal", e.rythme);
        assertTrue(e.vacances);
        Soins.Action x = Soins.lireAction(Soins.json(a("id1", "nourrir", 2, "pomme")));
        assertEquals("pomme", x.objet);
        assertEquals(T0 + 2 * H, x.t, 0);
        assertEquals(3, Soins.json(a("id2", "laver", 0, "")).length());
    }
}
