package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;

/** Musiques et ambiances : mêmes échantillons que le PC (MusiqueTests.cs) et que outils/sons/sons.py. */
public class MusiqueTest {
    private static Musique.Catalogue catalogue() throws Exception {
        return Musique.lire(new String(Files.readAllBytes(new File(SonsTest.racine(), "assets/musiques.txt").toPath()),
                StandardCharsets.UTF_8));
    }

    @Test
    public void memesEchantillonsQueLaReference() throws Exception {
        Musique.Catalogue c = catalogue();
        int vus = 0;
        for (String l : Files.readAllLines(new File(SonsTest.racine(), "outils/sons/musiques-reference.txt").toPath(), StandardCharsets.UTF_8)) {
            if (l.startsWith("#") || l.trim().isEmpty()) continue;
            String[] p = l.split("\\|");
            String id = p[0].trim();
            short[] s = Musique.synthetiser(c.morceaux.get(id));
            assertEquals(id + " : longueur", Integer.parseInt(p[1].trim()), s.length);
            assertEquals(id + " : empreinte", p[3].trim(), Sons.empreinte(s));
            vus++;
        }
        assertEquals(c.morceaux.size(), vus);
    }

    @Test
    public void laRessourceEmbarqueeEstLeCatalogue() {
        Musique.Catalogue c = Musique.lire(Sons.ressource("/musiques.txt"));
        for (String t : Musique.TONS) assertTrue(t, c.morceaux.containsKey(t));
        assertEquals("mer", c.decors.get("port-trebrume"));
    }

    @Test
    public void choixCommeLePc() {
        assertEquals("discrete", Musique.DEFAUT);
        assertEquals("prologue", Musique.pour("prologue", "humour"));
        assertEquals("emotion", Musique.pour("petit-nuage", "emotion"));
        assertNull(Musique.pour("autre", "epique"));
        assertEquals(0, Musique.gain("aucune"));
        assertEquals(65536 * 3 / 8, Musique.gain("discrete"));
    }

    @Test
    public void leChampMusiqueChoisitLeMorceau() {
        for (String t : new String[]{"humour", "mystere", "emotion"}) {
            assertEquals(t + "-tension", Musique.pour("x", t, "tension"));
            assertEquals(t + "-calme", Musique.pour("x", t, "calme"));
        }
        assertEquals("pilou-25", Musique.pour("evolution", "emotion", "pilou-25"));
        assertEquals("fin-secrete", Musique.pour("phare-eteint", "mystere", "fin-secrete"));
        assertEquals("prologue", Musique.pour("prologue", "humour", "calme"));
        assertEquals("mystere", Musique.pour("phare-eteint", "mystere", "inconnu"));
        assertTrue(Musique.estMotif("fin-bonne") && Musique.estMotif("pilou-court") && !Musique.estMotif("pilou-10"));
    }

    @Test
    public void unMotifJoueUneFoisPuisLeSilence() {
        short[] motif = new short[Musique.TAUX / 5];
        Arrays.fill(motif, (short) 5000);
        short[] boucle = new short[1000];
        Arrays.fill(boucle, (short) 2000);
        Musique.Melangeur t = new Musique.Melangeur(id -> id.equals("fin") ? motif : boucle, id -> id.equals("fin"));
        short[] bloc = new short[Musique.TAUX / 10];
        t.viser("emotion", null, 65536);
        for (int i = 0; i < 20; i++) t.remplir(bloc);
        assertEquals(2000, bloc[bloc.length - 1]);
        t.viser("fin", null, 65536);
        t.remplir(bloc);
        assertTrue(bloc[0] > 5000);
        for (int i = 0; i < 15; i++) {
            t.viser("fin", null, 65536);
            t.remplir(bloc);
        }
        assertEquals(0, bloc[bloc.length - 1]);
        assertTrue(t.silencieux());
        t.viser("emotion", null, 65536);
        t.viser("fin", null, 65536);
        t.remplir(bloc);
        assertTrue(bloc[0] > 4000);
    }

    @Test
    public void fonduEntreeEtSortie() {
        short[] boucle = new short[1000];
        Arrays.fill(boucle, (short) 8000);
        Musique.Melangeur t = new Musique.Melangeur(id -> boucle);
        short[] bloc = new short[Musique.TAUX / 10];
        t.viser("humour", null, 65536);
        t.remplir(bloc);
        assertTrue(bloc[0] < 100);
        for (int i = 0; i < 15; i++) t.remplir(bloc);
        assertEquals(8000, bloc[bloc.length - 1]);
        t.viser(null, null, 65536);
        for (int i = 0; i < 10; i++) t.remplir(bloc);
        assertEquals(0, bloc[bloc.length - 1]);
        assertTrue(t.silencieux());
    }
}
