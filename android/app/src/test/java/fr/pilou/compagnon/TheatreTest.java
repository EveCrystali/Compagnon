package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.junit.Test;

/**
 * Le théâtre des campagnes (docs/SCENES.md) : Theatre.java calcule exactement ce que calcule la référence
 * (outils/sprites/theatre.py, relue aussi par TheatreTests.cs) : position et image de Pilou, acteurs, effets, et
 * l'empreinte de l'image composée pixel à pixel.
 */
public class TheatreTest {
    private static File assets(String... p) {
        File f = new File(RenduPilouTest.racine(), "assets");
        for (String s : p) f = new File(f, s);
        return f;
    }

    private static String lire(File f) throws Exception {
        return new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
    }

    private static Map<String, Map<String, Theatre.Anim>> anims() throws Exception {
        return Theatre.lireAnimations(lire(assets("scenes", "animations.txt")));
    }

    /** Sprite fin dessiné à la main (les décors sont lus à la demande) ; null s'il n'existe pas en natif. */
    private static Sprites.Sprite fin(Sprites.Banque b, String id) {
        if (b.fins.containsKey(id)) return b.fins.get(id);
        return b.aLire.contains(id) ? b.fin(id) : null;
    }

    private static Theatre.Evenement evenement(String[] p) {
        long t = Long.parseLong(p[1]);
        if (p[2].equals("perso")) return new Theatre.Evenement(t, "perso", 0, 0, p[3]);
        return p[2].equals("humeur") ? Theatre.Evenement.humeur(t, p[3])
                : new Theatre.Evenement(t, p[2], Long.parseLong(p[3]), Long.parseLong(p[4]));
    }

    @Test
    public void memesScenesQueLaReference() throws Exception {
        Sprites.Banque b = Sprites.banque();
        Map<String, Map<String, Theatre.Anim>> anims = anims();
        File f = new File(RenduPilouTest.racine(), "outils/sprites/theatre-reference.txt");
        Theatre.Contexte cx = null;
        Sprites.Sprite decor = null;
        int[] teinte = new int[0];
        String niveau = "", nom = "";
        int regard = 0;
        List<Theatre.Evenement> evts = new ArrayList<>();
        int n = 0, images = 0;
        for (String l : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
            if (l.isEmpty() || l.startsWith("#")) continue;
            String[] p = l.split(" ", -1);
            switch (p[0]) {
                case "scenario": {
                    nom = p[1];
                    Map<String, Theatre.Scene> scenes = Theatre.lireScenes(lire(assets("scenes", p[2] + ".txt")));
                    cx = new Theatre.Contexte(scenes.get(p[3]), anims, id -> fin(b, id));
                    decor = fin(b, "decor-" + p[2] + "-" + p[3]);
                    teinte = b.teintes.get(p[4]);
                    niveau = p[5];
                    regard = Integer.parseInt(p[6]);
                    evts = new ArrayList<>();
                    break;
                }
                case "evenement":
                    evts.add(evenement(p));
                    break;
                case "pilou": {
                    Theatre.EtatPilou e = Theatre.pilou(cx, evts, Long.parseLong(p[1]), regard, niveau);
                    Theatre.EtatPilou attendu = new Theatre.EtatPilou(Integer.parseInt(p[2]), Integer.parseInt(p[3]),
                            Integer.parseInt(p[4]), p[5].equals("1"), p[6].equals("1"));
                    assertEquals(nom + " : " + l, attendu, e);
                    break;
                }
                case "perso": {
                    Theatre.Pose q = Theatre.perso(cx, evts, Long.parseLong(p[1]), niveau);
                    String attendu = p[2].equals("-") ? "-" : String.join(" ", Arrays.copyOfRange(p, 2, p.length));
                    String vu = q == null ? "-" : q.sprite + " " + q.image + " " + q.x + " " + q.y + " " + (q.miroir ? 1 : 0);
                    assertEquals(nom + " : " + l, attendu, vu);
                    break;
                }
                case "acteurs": {
                    long t = Long.parseLong(p[1]);
                    List<Theatre.Pose> poses = new ArrayList<>(Theatre.acteurs(cx, evts, t, niveau));
                    poses.addAll(Theatre.effets(cx, evts, t, niveau));
                    List<String> s = new ArrayList<>();
                    for (Theatre.Pose q : poses) s.add(q.sprite + ":" + q.image + ":" + q.x + ":" + q.y + ":" + (q.miroir ? 1 : 0));
                    String lu = s.isEmpty() ? "-" : String.join(" ", s);
                    assertEquals(nom + " : " + l, String.join(" ", Arrays.copyOfRange(p, 2, p.length)), lu);
                    break;
                }
                case "image": {
                    int[] px = Theatre.composer(cx, decor, teinte, evts, Long.parseLong(p[1]), regard, niveau, null);
                    assertEquals(nom + " : image à " + p[1] + " ms", Long.parseLong(p[2]), Theatre.fnv(px));
                    images++;
                    break;
                }
                default:
                    fail("ligne inconnue : " + l);
            }
            n++;
        }
        assertTrue(n + " lignes, " + images + " images", n > 500 && images > 50);
    }

    @Test
    public void chaqueSceneASonDecorEtSesActeurs() throws Exception {
        Sprites.Banque b = Sprites.banque();
        Map<String, Map<String, Theatre.Anim>> anims = anims();
        assertTrue(anims.containsKey(Theatre.ID_PILOU));
        Sprites.Sprite pilou = fin(b, Theatre.ID_PILOU);
        assertNotNull(pilou);
        for (Theatre.Anim a : anims.get(Theatre.ID_PILOU).values()) assertTrue(a.premiere + a.nombre <= pilou.images.size());
        List<String> comportements = Arrays.asList("vol", "traverse", "rond", "saut", "pose", "flotte", "chute");
        List<String> reactions = Arrays.asList("bulle", "rond", "graines");
        int n = 0;
        File[] fichiers = assets("scenes").listFiles((d, nomFichier) -> nomFichier.endsWith(".txt") && !nomFichier.equals("animations.txt"));
        assertNotNull(fichiers);
        for (File f : fichiers) {
            String campagne = f.getName().replace(".txt", "");
            for (Map.Entry<String, Theatre.Scene> e : Theatre.lireScenes(lire(f)).entrySet()) {
                Theatre.Scene sc = e.getValue();
                assertNotNull(fin(b, "decor-" + campagne + "-" + e.getKey()));
                assertTrue(sc.place >= 8 && sc.place <= Theatre.W - 8);
                assertTrue(sc.interlocuteur >= 20 && sc.interlocuteur <= Theatre.W - 8);
                assertTrue(sc.sol[1] >= 30 && sc.sol[1] <= Theatre.H);
                assertTrue(sc.sol[3] >= 20 && sc.sol[3] <= Theatre.H);
                for (Theatre.Acteur a : sc.acteurs) {
                    assertNotNull(a.sprite, fin(b, a.sprite));
                    assertTrue(a.comportement, comportements.contains(a.comportement));
                }
                for (Theatre.Sensible s : sc.sensibles) assertTrue(s.reaction, reactions.contains(s.reaction));
                n++;
            }
        }
        assertTrue(n + " scènes", n >= 6);
    }

    @Test
    public void unClicNeChangeQueCeQuiLeSuit() throws Exception {
        // La scène se recalcule à chaque image depuis la liste d'événements : ajouter un clic ne doit pas modifier le
        // passé (ce que Pilou faisait avant le clic reste identique).
        Sprites.Banque b = Sprites.banque();
        Theatre.Scene sc = Theatre.lireScenes(lire(assets("scenes", "prologue.txt"))).get("mare");
        Theatre.Contexte cx = new Theatre.Contexte(sc, anims(), id -> fin(b, id));
        List<Theatre.Evenement> evts = new ArrayList<>();
        evts.add(new Theatre.Evenement(0, "entree"));
        List<Theatre.EtatPilou> avant = new ArrayList<>(), apres = new ArrayList<>();
        for (int i = 0; i < 40; i++) avant.add(Theatre.pilou(cx, evts, i * 100L));
        evts.add(new Theatre.Evenement(4000, "clic", 18, 70));
        for (int i = 0; i < 40; i++) apres.add(Theatre.pilou(cx, evts, i * 100L));
        assertEquals(avant, apres);
        assertNotEquals(Theatre.pilou(cx, evts.subList(0, 1), 4200), Theatre.pilou(cx, evts, 4200));
    }
}
