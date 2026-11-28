package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import org.junit.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;

/**
 * Les traits de personnalité : le moteur du téléphone (Traits.java) rejoue les vecteurs écrits par celui du PC
 * (apps/PilouBureau/tests/TraitsTests.cs, classe TraitsVecteurs), ligne à ligne. Puis quelques vérifications directes.
 */
public class TraitsTest {
    private static String ressource(String chemin) {
        try (InputStream in = TraitsTest.class.getClassLoader().getResourceAsStream(chemin)) {
            return in == null ? null : new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        }
    }

    private static String condition(Traits.Trait t) {
        List<String> l = new ArrayList<>();
        for (Traits.Terme c : t.condition) l.add(c.fait + c.op + c.valeur);
        return String.join("&", l);
    }

    private static String ids(List<Traits.Trait> l) {
        List<String> r = new ArrayList<>();
        for (Traits.Trait t : l) r.add(t.id);
        return String.join(",", r);
    }

    private static TreeMap<Integer, Presence.FaitsDuJour> journal(String s) {
        TreeMap<Integer, Presence.FaitsDuJour> j = new TreeMap<>();
        if (s.isEmpty()) return j;
        for (String page : s.split("\\|", -1)) {
            int i = page.indexOf(' ');
            j.put(Presence.jourDe(page.substring(0, i)), Presence.FaitsDuJour.lire(page.substring(i + 1)));
        }
        return j;
    }

    /** Refait une ligne des vecteurs et renvoie la ligne recalculée (égale à l'entrée si tout concorde). */
    static String refaire(String ligne) {
        if (ligne.startsWith("#")) return ligne;
        String[] c = ligne.split("\t", -1);
        StringBuilder debut = new StringBuilder();
        for (int i = 0; i < c.length - 1; i++) debut.append(c[i]).append('\t');
        String r = debut.toString();
        switch (c[0]) {
            case "trait": {
                Traits.Trait t = null;
                int n = Integer.parseInt(c[1]);
                for (Traits.Trait x : Traits.tous()) if (x.numero == n) t = x;
                if (t == null) return "(trait " + n + " absent)";
                return String.join("\t", "trait", String.valueOf(t.numero), t.id, t.nom, String.valueOf(t.seuil), condition(t));
            }
            case "cas": {
                int auj = Integer.parseInt(c[1]);
                long avant = Traits.deHex(c[2]);
                TreeMap<Integer, Presence.FaitsDuJour> j = journal(c[3]);
                List<String> mesures = new ArrayList<>();
                for (Traits.Trait t : Traits.tous()) mesures.add(String.valueOf(Traits.mesure(t, j)));
                long apres = avant | Traits.acquis(Traits.tous(), j);
                Traits.Trait a = Traits.aAnnoncer(Traits.tous(), apres, avant);
                return String.join("\t", "cas", c[1], c[2], c[3], String.join(",", mesures), Traits.hex(apres),
                        ids(Traits.dominants(Traits.tous(), apres, j, auj)), a == null ? "-" : a.id);
            }
            case "etat": {
                Presence.Etat e = Presence.Etat.lire(PresenceTest.desechapper(c[1]));
                int auj = Integer.parseInt(c[2]);
                Traits.decouvrir(e);
                Presence.Totaux t = e.totaux();
                return String.join("\t", "etat", c[1], c[2], Traits.hex(t.traits), Traits.hex(t.traitsDits),
                        ids(Traits.dominants(e, auj)), PresenceTest.echapper(e.texte()));
            }
            case "mot": {
                Presence.Contexte x = new Presence.Contexte(LocalDateTime.parse(c[2] + ":00"), Presence.Moment.valueOf(c[1]));
                x.absenceMin = Double.parseDouble(c[3]);
                x.presenceJourMin = Double.parseDouble(c[4]);
                x.seanceMin = Double.parseDouble(c[5]);
                x.palier = Integer.parseInt(c[6]);
                x.traitNouveau = c[7];
                x.traits = c[8];
                Presence.Choix ch = Presence.mot(x, Presence.banque(), new java.util.HashMap<>(), c[9]);
                return r + (ch == null ? "-" : ch.famille + "|" + ch.ligne.id + "|" + ch.texte);
            }
            case "bits":
                return r + Traits.hex(Traits.deHex(c[1]));
            default:
                fail("opération inconnue : " + c[0]);
                return "";
        }
    }

    @Test
    public void vecteurs() {
        String texte = ressource("traits-vecteurs.txt");
        assertNotNull("traits-vecteurs.txt (src/test/resources) : PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests", texte);
        String[] lignes = texte.replace("\r\n", "\n").split("\n");
        int faites = 0;
        for (int i = 0; i < lignes.length; i++) {
            if (lignes[i].isEmpty()) continue;
            String refait = refaire(lignes[i]);
            if (!lignes[i].equals(refait))
                fail("ligne " + (i + 1) + " différente\nfichier : " + lignes[i] + "\ntéléphone : " + refait);
            faites++;
        }
        assertTrue("vecteurs trop courts : " + faites, faites > 250);
    }

    @Test
    public void vingtTraitsNumerotesDeUnAVingt() {
        List<Traits.Trait> l = Traits.tous();
        assertEquals(20, l.size());
        for (int i = 0; i < l.size(); i++) assertEquals(i + 1, l.get(i).numero);
    }

    @Test
    public void chaqueTraitADesMots() {
        for (Traits.Trait t : Traits.tous()) {
            int annonces = 0, repliques = 0;
            for (Presence.Ligne l : Presence.repliques()) {
                if (l.famille.equals("annonce-" + t.id)) annonces++;
                if (l.famille.equals("trait-" + t.id)) repliques++;
            }
            assertEquals("annonce de " + t.id, 1, annonces);
            assertTrue("répliques de " + t.id + " : " + repliques, repliques >= 3);
        }
    }

    @Test
    public void unHexAbimeVautZero() {
        for (String s : new String[]{"", "zz", "-1", "+1", " 1", "1 ", "1234567890abcdef", "ffffffffffffffff", "0x1"})
            assertEquals("« " + s + " »", 0L, Traits.deHex(s));
        assertEquals(0xfffffffffffffffL & ((1L << 60) - 1), Traits.deHex("fffffffffffffff"));
        assertEquals(31L, Traits.deHex("1F"));
        assertEquals("1f", Traits.hex(31));
    }

    @Test
    public void unTraitAcquisNeSePerdPas() {
        Presence.Etat e = PresenceTest.neuf("tel-1");
        int auj = Presence.jourDe("2026-06-10");
        for (int d = 0; d < 20; d++) {
            Presence.FaitsDuJour f = e.aujourdhui(Presence.jourTexte(auj - d));
            f.mn = 60;
            f.ca = 6;
        }
        assertTrue(Traits.decouvrir(e));
        long bit = Traits.trouver("calin").bit();
        assertTrue((e.moi.traits & bit) != 0);
        e.journal.clear();
        assertFalse(Traits.decouvrir(e));
        assertTrue((e.moi.traits & bit) != 0);
        assertNull(Traits.aAnnoncer(new ArrayList<>(), e.moi.traits, 0));
    }
}
