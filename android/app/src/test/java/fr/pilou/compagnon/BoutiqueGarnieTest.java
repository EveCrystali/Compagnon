package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Boutique garnie : même catalogue, même vitrine et mêmes règles que Boutique.cs (BoutiqueGarnieTests.cs). */
public class BoutiqueGarnieTest {
    private static List<Boutique.Article> garnis() {
        List<Boutique.Article> l = new ArrayList<>();
        for (Boutique.Article a : Boutique.CATALOGUE) if (a.numero > 0) l.add(a);
        return l;
    }

    @Test
    public void catalogueGarniLuEtCoherent() {
        List<Boutique.Article> g = garnis();
        assertTrue(g.size() + " articles garnis", g.size() >= 110);
        Set<String> ids = new HashSet<>();
        Set<Integer> nums = new HashSet<>();
        for (Boutique.Article a : Boutique.CATALOGUE) assertTrue(a.id, ids.add(a.id));
        for (Boutique.Article a : g) {
            assertTrue(a.id, nums.add(a.numero));
            assertTrue(a.id, a.prix >= 30 && a.prix <= 2200);
            assertTrue(a.id, a.saison.isEmpty() || Arrays.asList(Boutique.SAISONS).contains(a.saison));
        }
        for (String slot : Boutique.SLOTS) {
            boolean vu = false;
            for (Boutique.Article a : g) vu |= a.slot.equals(slot);
            assertTrue(slot, vu);
        }
        assertTrue(Boutique.ENSEMBLES.size() >= 8);
        for (Boutique.Ensemble e : Boutique.ENSEMBLES) {
            assertTrue(e.id, e.pieces.size() >= 5 && e.pieces.size() <= 6);
            Set<String> slots = new HashSet<>();
            for (String p : e.pieces) assertTrue(e.id + " " + p, slots.add(Boutique.trouver(p).slot));
        }
        assertEquals("Ensembles", Boutique.nomSlot(Boutique.RAYON_ENSEMBLES));
        assertEquals(6, new HashSet<>(Arrays.asList(Boutique.signeRarete(0), Boutique.signeRarete(1), Boutique.signeRarete(2),
                Boutique.signeRarete(3), Boutique.signeRarete(4), Boutique.signeRarete(5))).size());
    }

    /** Catalogue identique au PC : les articles écrits dans Boutique.cs (identifiants, emplacements, prix, rangées), dans le
     *  même ordre pour ceux qui passent en vitrine (l'ordre compte pour le tirage), puis la boutique garnie du même fichier. */
    @Test
    public void memeCatalogueEtMemeOrdreQueLePc() throws Exception {
        File f = new File("../../apps/PilouBureau/Boutique.cs");
        org.junit.Assume.assumeTrue(f.exists());
        String cs = new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
        Matcher m = Pattern.compile("new\\(\"([a-z0-9-]+)\", \"[^\"]+\", (\\w+), (\\d+), (\\d+), Rarete\\.\\w+(, true)?\\)").matcher(cs);
        List<String> ordrePc = new ArrayList<>();
        while (m.find()) {
            Boutique.Article a = Boutique.trouver(m.group(1));
            assertNotNull(m.group(1), a);
            assertEquals(m.group(1), m.group(2).toLowerCase(java.util.Locale.ROOT), a.slot);
            assertEquals(m.group(1), Integer.parseInt(m.group(3)), a.prix);
            assertEquals(m.group(1), Integer.parseInt(m.group(4)), a.niveauMin);
            assertEquals(m.group(1), m.group(5) != null, a.permanent);
            if (m.group(5) == null) ordrePc.add(m.group(1));
        }
        for (Boutique.Article a : garnis()) ordrePc.add(a.id);
        List<String> ordreTel = new ArrayList<>();
        for (Boutique.Article a : Boutique.CATALOGUE) if (!a.permanent) ordreTel.add(a.id);
        assertEquals(ordrePc, ordreTel);
        // Le PC lit le même fichier : rien à recopier pour la boutique garnie.
        assertTrue(cs.contains("TexteRessource(\"catalogue.txt\")"));
    }

    /** Même vitrine que le PC pour une date (BoutiqueGarnieTests.Vitrine_deterministe). */
    @Test
    public void vitrineDeterministeCommeLePc() {
        String[][] attendu = {
                {"2026-11-26", "perroquet-caramel,chapeau-paille,ballon-helium,patins", "nebuleuse,fond-aurore"},
                {"2026-12-24", "fond-montagne,mini-goutte,panier-dos,fond-foret", "ailes-libellule"},
                {"2027-07-14", "titre-matinal,cuivre,haut-de-forme,bulle-ambre", ""},
                {"2027-10-31", "herisson,baguette,impermeable,lunettes-3d", ""},
        };
        for (String[] l : attendu) {
            LocalDate j = LocalDate.parse(l[0]);
            assertEquals(l[0], l[1], ids(Boutique.offresDuJour(j)));
            assertEquals(l[0], l[2], ids(Boutique.passages(j)));
        }
    }

    private static String ids(List<Boutique.Article> l) {
        StringBuilder b = new StringBuilder();
        for (Boutique.Article a : l) b.append(b.length() > 0 ? "," : "").append(a.id);
        return b.toString();
    }

    @Test
    public void saisonsEtPassages() {
        LocalDate j = LocalDate.of(2026, 11, 26);
        assertEquals(5, Boutique.joursRestants("automne", j));
        assertEquals(LocalDate.of(2026, 12, 1), Boutique.retour("hiver", j));
        assertEquals(LocalDate.of(2027, 10, 15), Boutique.retour("frissons", j));
        assertEquals(28, Boutique.joursRestants("fetes", LocalDate.of(2026, 12, 10)));
        Boutique.Article bonnet = Boutique.trouver("bonnet-oreillettes");
        assertEquals("hors saison", Boutique.refus(bonnet, 50, 9999, "", false, j));
        assertNull(Boutique.refus(bonnet, 50, 9999, "", false, LocalDate.of(2026, 12, 2)));
        for (Boutique.Article a : Boutique.CATALOGUE) {
            if (!a.passage) continue;
            int n = 0;
            for (int i = 0; i < 31; i++) if (Boutique.dePassage(a, LocalDate.of(2027, 3, 1).plusDays(i))) n++;
            assertEquals(a.id, Boutique.JOURS_PASSAGE, n);
        }
        assertNull(Boutique.refus(Boutique.trouver("nebuleuse"), 50, 9999, "", false, j));
        assertEquals("pas en vitrine", Boutique.refus(Boutique.trouver("phenix"), 50, 9999, "", false, j));
    }

    @Test
    public void collectionEnsemblesEtBonus() {
        List<String> inv = new ArrayList<>();
        assertEquals(10, Boutique.seuil(Boutique.prochainPalierCollection(0)));
        for (Boutique.Article a : Boutique.CATALOGUE) if (Boutique.collectionnable(a) && inv.size() < 10) inv.add(a.id);
        inv.add(Boutique.PIERRE_CALME);
        assertEquals(10, Boutique.collection(inv));
        assertTrue(Boutique.gagnees(inv).contains("titre-col-herbe"));
        Boutique.Ensemble e = Boutique.ensemble("jardinier");
        assertFalse(Boutique.peutPorter(inv, Boutique.TITRE, e.idTitre()));
        inv.addAll(e.pieces);
        assertTrue(Boutique.peutPorter(inv, Boutique.TITRE, e.idTitre()));
        assertEquals("« Jardinier émérite »", Boutique.nomTitre(e.idTitre()));
        assertEquals("à gagner", Boutique.refus(Boutique.trouverTout(e.idTitre()), 50, 9999, "", false));
        Map<String, String> porte = new HashMap<>();
        for (String p : e.pieces) porte.put(Boutique.trouver(p).slot, p);
        assertEquals(Arrays.asList("bonus-jardinier"), Boutique.bonusPortes(porte));
        porte.remove(Boutique.MAIN);
        assertTrue(Boutique.bonusPortes(porte).isEmpty());
        assertEquals(Boutique.TOTAL_COLLECTION, Boutique.seuil(Boutique.PALIERS_COLLECTION.get(Boutique.PALIERS_COLLECTION.size() - 1)));
    }

    /** Même encodage que Boutique.Garde (PC) : l'inventaire voyage en bits. */
    @Test
    public void synchroCompacte() {
        List<String> inv = new ArrayList<>();
        for (Boutique.Article a : garnis()) inv.add(a.id);
        inv.add("casquette");
        String g = Boutique.garde(inv);
        assertTrue(g, g.length() < 40);
        assertEquals(new HashSet<>(inv.subList(0, inv.size() - 1)), new HashSet<>(Boutique.deplier(g)));
        assertEquals(Arrays.asList("casquette"), Boutique.horsGarde(inv));
        assertTrue(Boutique.deplier("!!").isEmpty());
        // Les trois premiers articles garnis (n° 1, 2, 3) : un octet 0b111.
        assertEquals("Bw", Boutique.garde(Arrays.asList("chapeau-explorateur", "jumelles", "foulard-explorateur")));
    }
}
