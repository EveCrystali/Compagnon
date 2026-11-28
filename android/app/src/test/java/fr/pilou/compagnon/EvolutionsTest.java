package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.junit.Test;

/**
 * Les scènes d'évolution : Evolutions.java recalcule exactement ce que calcule la référence (outils/sprites/evolutions.py,
 * relue aussi par EvolutionsTests.cs) : scènes, options, répliques par stade, variante et choix, temps d'écriture.
 */
public class EvolutionsTest {
    private static String lire(File f) throws Exception {
        return new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
    }

    private static Map<Integer, Evolutions.Scene> scenes() throws Exception {
        return Evolutions.lire(lire(new File(RenduPilouTest.racine(), "assets/evolutions.txt")));
    }

    /** Les lignes que la référence écrit (même format que ecrire_reference), sans l'en-tête. */
    private static List<String> recalculer(Map<Integer, Evolutions.Scene> scenes) {
        List<String> l = new ArrayList<>();
        for (Evolutions.Scene sc : scenes.values()) {
            l.add("scene " + sc.stade + " " + sc.decor + " | " + sc.titre + " | " + sc.question);
            for (Evolutions.Option o : sc.options) l.add("option " + o.id + " " + o.libelle);
            List<String> variantes = new ArrayList<>(java.util.Arrays.asList(Evolutions.VARIANTES));
            variantes.add("autre");
            for (String var : variantes) {
                List<String> choix = new ArrayList<>();
                choix.add(null);
                for (Evolutions.Option o : sc.options) choix.add(o.id);
                for (String c : choix) {
                    List<Evolutions.Replique> d = Evolutions.deroule(sc, var, c);
                    l.add("deroule " + sc.stade + " " + var + " " + (c == null ? "-" : c) + " " + d.size());
                    for (Evolutions.Replique r : d)
                        l.add("  " + (r.humeur.isEmpty() ? "-" : r.humeur) + " " + Evolutions.msEcriture(r.texte) + " " + r.texte);
                }
            }
        }
        return l;
    }

    @Test
    public void memesScenesQueLaReference() throws Exception {
        List<String> attendu = new ArrayList<>();
        for (String l : Files.readAllLines(new File(RenduPilouTest.racine(), "outils/sprites/evolutions-reference.txt").toPath(), StandardCharsets.UTF_8))
            if (!l.isEmpty() && !l.startsWith("#")) attendu.add(l);
        List<String> vu = recalculer(scenes());
        assertEquals(attendu.size(), vu.size());
        for (int i = 0; i < attendu.size(); i++) assertEquals("ligne " + (i + 1), attendu.get(i), vu.get(i));
        assertTrue(attendu.size() > 100);
    }

    @Test
    public void troisScenesTroisOptionsEtUneFinJoyeuse() throws Exception {
        Map<Integer, Evolutions.Scene> s = scenes();
        assertEquals(3, s.size());
        for (int stade = 2; stade <= 4; stade++) {
            Evolutions.Scene sc = s.get(stade);
            assertEquals(3, sc.options.size());
            assertFalse(sc.titre.isEmpty());
            assertFalse(sc.decor.isEmpty());
            for (String var : new String[]{"calin", "espiegle", "inconnue"}) {
                List<Evolutions.Replique> avant = Evolutions.deroule(sc, var, null);
                assertEquals("", avant.get(avant.size() - 1).humeur);
                assertEquals(sc.question, avant.get(avant.size() - 1).texte);
                for (Evolutions.Option o : sc.options) {
                    List<Evolutions.Replique> d = Evolutions.deroule(sc, var, o.id);
                    assertEquals("joie", d.get(d.size() - 1).humeur);
                    assertTrue(d.size() > avant.size());
                }
            }
        }
    }

    @Test
    public void lesRessourcesEmbarqueesSontCellesDuFichier() throws Exception {
        assertEquals(scenes().keySet(), Evolutions.scenes().keySet());
        assertNull(Evolutions.scenes().get(2).libelle("inconnu"));
        assertEquals("calin", Evolutions.variante(null));
        assertEquals("espiegle", Evolutions.variante("espiegle"));
        assertEquals(900, Evolutions.msEcriture("a"));
        assertEquals(7000, Evolutions.msEcriture(new String(new char[1000]).replace('\0', 'x')));
    }
}
