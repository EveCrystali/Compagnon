package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
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
                case "boude": a.boude = v.equals("1"); break;
                case "dos": a.dos = v.equals("1"); break;
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

    static List<String[]> reference(String fichier) throws Exception {
        List<String[]> l = new ArrayList<>();
        for (String ligne : Files.readAllLines(new File(racine(), "outils/sprites/" + fichier).toPath(), StandardCharsets.UTF_8)) {
            if (ligne.startsWith("#") || ligne.trim().isEmpty()) continue;
            String[] p = ligne.split("\\|");
            l.add(new String[]{p[0].trim(), p[1].trim()});
        }
        return l;
    }

    private static void memesPixels(String fichier, int echelle) throws Exception {
        Sprites.Banque b = Sprites.banque();
        List<String> ecarts = new ArrayList<>();
        List<String[]> poses = reference(fichier);
        RenduPilou.Tampon tampon = new RenduPilou.Tampon();
        for (String[] p : poses) {
            if (!empreinte(RenduPilou.rendre(allure(p[0]), b, null, echelle)).equals(p[1])) ecarts.add(p[0]);
            // Avec un tampon réutilisé d'une image à l'autre : mêmes pixels.
            else if (!empreinte(RenduPilou.rendre(allure(p[0]), b, null, echelle, tampon)).equals(p[1])) ecarts.add("tampon : " + p[0]);
        }
        assertTrue("trop peu de poses", poses.size() >= 80);
        assertEquals("poses qui diffèrent de la référence : " + ecarts, 0, ecarts.size());
    }

    @Test
    public void memesPixelsQueLaReference() throws Exception {
        memesPixels("rendus-reference.txt", 1);
    }

    /** Rendu fin (grille 96 × 112) : mêmes pixels que rendu.py à l'échelle 2 et que le PC. */
    @Test
    public void renduFinMemesPixelsQueLaReference() throws Exception {
        memesPixels("rendus-reference-2x.txt", 2);
    }

    /** L'agrandissement automatique d'un sprite 1× donne les mêmes lettres que rendu.agrandir, sprite par sprite. */
    @Test
    public void agrandissementIdentiqueALaReference() throws Exception {
        Sprites.Banque b = Sprites.banque();
        List<String[]> lignes = reference("agrandis-reference.txt");
        assertEquals(b.sprites.size(), lignes.size());
        List<String> ecarts = new ArrayList<>();
        for (String[] p : lignes) {
            Sprites.Sprite s = b.get(p[0]);
            assertNotNull(p[0], s);
            Sprites.Sprite g = Sprites.agrandir(s);
            StringBuilder t = new StringBuilder();
            for (int k = 0; k < g.images.size(); k++) {
                if (k > 0) t.append("\n---\n");
                t.append(String.join("\n", g.images.get(k)));
            }
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            StringBuilder h = new StringBuilder();
            for (byte o : md.digest(t.toString().getBytes(StandardCharsets.UTF_8))) h.append(String.format("%02x", o));
            if (!h.toString().equals(p[1])) ecarts.add(p[0]);
            assertEquals(p[0], s.w() * 2, g.w());
            assertEquals(p[0], s.dx * 2, g.dx);
            assertTrue(p[0], !g.natif && g.palette.equals(s.palette));
        }
        assertEquals("sprites agrandis qui diffèrent de la référence : " + ecarts, 0, ecarts.size());
    }

    /** Les sprites redessinés en fin gardent l'emplacement, l'ancre et l'animation du sprite 1×. */
    @Test
    public void spritesFinsCoherents() {
        Sprites.Banque b = Sprites.banque();
        assertTrue(b.fins.size() + " sprites fins", b.fins.size() >= 100);
        for (Sprites.Sprite f : b.fins.values()) {
            Sprites.Sprite s = b.get(f.id);
            assertNotNull(f.id + " : pas de sprite 1×", s);
            assertEquals(f.id, s.slot + s.ancre + s.derriere + s.coiffe + s.duree + s.images.size(),
                    f.slot + f.ancre + f.derriere + f.coiffe + f.duree + f.images.size());
            assertTrue(f.id + " : ancrage", Math.abs(f.dx - s.dx * 2) <= 2 && Math.abs(f.dy - s.dy * 2) <= 2);
            assertSame(f, b.fin(f.id));
            assertSame(f, b.get(f.id, 2));
        }
        assertSame(b.fin("po"), b.fin("po"));
        assertSame(b.get("po"), b.get("po", 1));
        assertNull(b.fin("n-existe-pas"));
    }

    /** Humeurs et tenues de voyage des campagnes : tout est dans la banque, aux deux échelles. */
    @Test
    public void humeursEtVoyagesDesCampagnes() throws Exception {
        Sprites.Banque b = Sprites.banque();
        String repos = empreinte(RenduPilou.rendre(new RenduPilou.Allure(), b, null));
        for (String h : RenduPilou.HUMEURS) {
            assertNotNull("bouche-" + h, b.get("bouche-" + h));
            assertNotNull("bouche-" + h + " (fin)", b.fins.get("bouche-" + h));
            RenduPilou.Allure a = new RenduPilou.Allure();
            a.expr = h;
            assertTrue(h, !repos.equals(empreinte(RenduPilou.rendre(a, b, null))));
        }
        for (String mode : RenduPilou.VOYAGES) {
            assertNotNull(mode, b.tenues.get("voyage-" + mode));
            RenduPilou.Allure a = new RenduPilou.Allure();
            a.tenue = "voyage-" + mode;
            a.t = 400;
            RenduPilou.Allure nu = new RenduPilou.Allure();
            nu.t = 400;
            assertTrue(mode, !empreinte(RenduPilou.rendre(nu, b, null)).equals(empreinte(RenduPilou.rendre(a, b, null))));
            assertEquals(96 * 112, RenduPilou.rendre(a, b, null, 2).length);
            assertEquals("l'allure donnée n'est pas modifiée", "repos", a.expr);
        }
        RenduPilou.Allure m = new RenduPilou.Allure();
        m.tenue = "voyage-marche";
        assertTrue(RenduPilou.voyager(m).marche && !m.marche);
    }

    /** La géométrie rendue reste en pixels de la grille 48 × 56, quelle que soit l'échelle. */
    @Test
    public void geometrieIndependanteDeLEchelle() {
        Sprites.Banque b = Sprites.banque();
        RenduPilou.Geometrie g1 = new RenduPilou.Geometrie(), g2 = new RenduPilou.Geometrie();
        for (int stade = 1; stade <= 4; stade++) {
            RenduPilou.Allure a = new RenduPilou.Allure();
            a.stade = stade;
            a.t = 700;
            RenduPilou.rendre(a, b, g1, 1);
            RenduPilou.rendre(a, b, g2, 2);
            assertEquals(g1.cx, g2.cx, 1e-9);
            assertEquals(g1.ry, g2.ry, 1e-9);
            assertTrue(Math.abs(g1.sommet - g2.sommet) <= 1 && Math.abs(g1.pied - g2.pied) <= 1);
        }
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
        assertEquals(RenduPilou.W * RenduPilou.H * 4, RenduPilou.rendre(a, Sprites.banque(), null, 2).length);
        a.tenue = "voyage-inconnu";
        assertEquals(RenduPilou.W * RenduPilou.H * 4, RenduPilou.rendre(a, new Sprites.Banque(), null, 2).length);
    }
}
