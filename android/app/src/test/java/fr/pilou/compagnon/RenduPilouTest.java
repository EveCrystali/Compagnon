package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Le rendu Java tombe sur les mêmes pixels que le rendu de référence (outils/sprites/rendu.py) et que le PC. */
public class RenduPilouTest {
    static File racine() {
        File f = new File("").getAbsoluteFile();
        while (f != null && !new File(f, "assets/index.txt").exists()) f = f.getParentFile();
        assertNotNull("racine du dépôt introuvable", f);
        return f;
    }

    static RenduPilou.Allure allure(String ligne) {
        RenduPilou.Allure a = new RenduPilou.Allure();
        for (String paire : ligne.trim().split("\\s+")) {
            String[] kv = paire.split("=", 2);
            String k = kv[0], v = kv[1];
            switch (k) {
                case "expr": a.expr = v; break;
                case "couleur": a.couleur = v; break;
                case "accessoire": a.accessoire = v; break;
                case "tenue": a.tenue = v; break;
                case "reaction": a.reaction = v; break;
                case "objets": a.objets = Arrays.asList(v.split(",")); break;
                case "cligne": a.cligne = v.equals("1"); break;
                case "clin": a.clin = v.equals("1"); break;
                case "marche": a.marche = v.equals("1"); break;
                case "course": a.course = v.equals("1"); break;
                case "baille": a.baille = v.equals("1"); break;
                case "etourdi": a.etourdi = v.equals("1"); break;
                case "fatigue": a.fatigue = v.equals("1"); break;
                case "regard": a.regard = Integer.parseInt(v); break;
                case "regard_y": a.regardY = Integer.parseInt(v); break;
                case "stade": a.stade = Integer.parseInt(v); break;
                case "t": a.t = Double.parseDouble(v); break;
                case "saut": a.saut = Double.parseDouble(v); break;
                case "chute": a.chute = Double.parseDouble(v); break;
                case "assis": a.assis = Double.parseDouble(v); break;
                case "suspendu": a.suspendu = Double.parseDouble(v); break;
                case "tremble": a.tremble = Double.parseDouble(v); break;
                case "evolution": a.evolution = Double.parseDouble(v); break;
                default: throw new IllegalArgumentException(k);
            }
        }
        return a;
    }

    static String empreinte(int[] g) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        for (int c : g) md.update(new byte[]{(byte) (c >>> 24), (byte) (c >>> 16), (byte) (c >>> 8), (byte) c});
        StringBuilder s = new StringBuilder();
        for (byte b : md.digest()) s.append(String.format("%02x", b));
        return s.toString();
    }

    @Test
    public void memesPixelsQueLaReference() throws Exception {
        Sprites.Banque b = Sprites.banque();
        List<String> lignes = Files.readAllLines(new File(racine(), "outils/sprites/rendus-reference.txt").toPath(), StandardCharsets.UTF_8);
        List<String> ecarts = new ArrayList<>();
        int n = 0;
        for (String l : lignes) {
            if (l.startsWith("#") || l.trim().isEmpty()) continue;
            String[] p = l.split("\\|");
            String obtenu = empreinte(RenduPilou.rendre(allure(p[0]), b, null));
            if (!obtenu.equals(p[1].trim())) ecarts.add(p[0].trim());
            n++;
        }
        assertTrue("trop peu de poses", n >= 40);
        assertEquals("poses qui diffèrent de la référence : " + ecarts, 0, ecarts.size());
    }

    @Test
    public void banqueComplete() {
        Sprites.Banque b = Sprites.banque();
        for (String id : new String[]{"oeil-ouvert", "bouche-repos", "etincelle-roue", "acc-bonnet", "tenue-code-lunettes", "chapeau-pirate",
                "petit-chat", "po", "po-tourne", "coffre-quete", "parchemin-quete", "prise-goujon", "prise-baleineau", "marmite",
                "plat-invente", "bug-prod", "astral-cape", "oeil-serein", "oeil-ouvert-g"})
            assertNotNull(id, b.get(id));
        for (String[] ids : b.tenues.values())
            for (String id : ids) assertNotNull(id, b.get(id));
        for (String id : b.plats.values()) assertNotNull(id, b.get(id));
        for (Butin.Prise x : Butin.PRISES) assertNotNull("prise-" + x.id, b.get("prise-" + x.id));
        for (String c : new String[]{"bleu", "orange", "lavande", "corail-orange", "ardoise", "sable", "glacier"})
            assertNotNull(c, b.teintes.get(c));
        for (Sprites.Sprite s : b.sprites.values()) {
            assertTrue(s.id + " sans image", s.h() > 0);
            for (String[] im : s.images) assertEquals(s.id + " : images de hauteurs différentes", s.h(), im.length);
        }
    }

    @Test
    public void objetInconnuIgnoreSansPlanter() {
        RenduPilou.Allure a = allure("expr=repos t=0 objets=n-existe-pas tenue=inconnue accessoire=rien stade=9");
        assertEquals(RenduPilou.W * RenduPilou.H, RenduPilou.rendre(a, Sprites.banque(), null).length);
    }
}
