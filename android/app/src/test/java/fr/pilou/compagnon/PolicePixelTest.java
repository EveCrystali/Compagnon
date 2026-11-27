package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;

/**
 * La police pixel (assets/police) se met en page au pixel près comme outils/sprites/police.py et comme le PC
 * (PolicePixelTests.cs) : mêmes lignes, mêmes largeurs, mêmes pixels (police-reference.txt).
 */
public class PolicePixelTest {
    @Test
    public void memesLignesLargeursEtPixelsQueLaReference() throws Exception {
        List<String> l = Files.readAllLines(new File(RenduPilouTest.racine(), "outils/sprites/police-reference.txt").toPath(), StandardCharsets.UTF_8);
        int cas = 0;
        List<String> ecarts = new ArrayList<>();
        for (int i = 0; i < l.size(); i++) {
            if (!l.get(i).startsWith("= ")) continue;
            String[] t = l.get(i).split(" ");
            String texte = l.get(++i).replace("\\n", "\n").replace("\\\\", "\\");
            List<String> attendu = new ArrayList<>();
            List<Integer> largeurs = new ArrayList<>();
            while (l.get(i + 1).startsWith("| ")) {
                String s = l.get(++i);
                int sp = s.indexOf(' ', 2);
                largeurs.add(Integer.parseInt(s.substring(2, sp)));
                attendu.add(s.substring(sp + 1));
            }
            long emp = Long.parseLong(l.get(++i).substring(2));
            PolicePixel p = PolicePixel.ressource(t[1]);
            assertNotNull(t[1], p);
            List<String> lignes = p.couper(texte, Integer.parseInt(t[2]), Integer.parseInt(t[3]));
            cas++;
            if (!lignes.equals(attendu)) {
                ecarts.add(t[1] + " " + t[2] + " « " + texte + " » : " + lignes);
                continue;
            }
            for (int k = 0; k < lignes.size(); k++)
                if (p.largeur(lignes.get(k)) != largeurs.get(k)) ecarts.add("largeur « " + texte + " »");
            if (p.empreinte(lignes) != emp) ecarts.add("pixels « " + texte + " »");
        }
        assertTrue(cas >= 100);
        assertEquals(new ArrayList<String>(), ecarts);
    }

    @Test
    public void leDessinFinALesMemesChasses() {
        String t = "Voix ambiguë d'un cœur qui, au zéphyr, préfère les jattes de kiwis ♥";
        for (String[] paire : new String[][]{{"texte", "texte2x"}, {"titre", "titre2x"}}) {
            PolicePixel a = PolicePixel.ressource(paire[0]), b = PolicePixel.ressource(paire[1]);
            assertEquals(2, b.echelle);
            assertEquals(a.ligne, b.ligne);
            assertEquals(a.couper(t, 120), b.couper(t, 120));
        }
    }

    @Test
    public void toutLeFrancaisAUnDessin() {
        PolicePixel p = PolicePixel.texte();
        String s = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                + "éèêëàâäîïôöùûüÿçœæÉÈÊËÀÂÄÎÏÔÖÙÛÜŸÇŒÆ«»’…–—!?:;.,()♥✓✧→¤  ";
        for (int i = 0; i < s.length(); i++) assertTrue("« " + s.charAt(i) + " »", p.connu(s.charAt(i)));
    }

    @Test
    public void typographieFrancaise() {
        assertEquals("bonjour ! c’est « toi »", PolicePixel.preparer("bonjour ! c'est « toi »"));
        for (String l : PolicePixel.texte().couper("tu m'as appelé ? je fais demi-tour !", 30))
            assertFalse(l.startsWith("!") || l.startsWith("?"));
    }
}
