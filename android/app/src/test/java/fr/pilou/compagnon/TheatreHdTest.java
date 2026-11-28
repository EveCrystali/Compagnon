package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
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
import java.util.TreeMap;
import java.util.function.Function;

import org.junit.Test;

/**
 * Le Théâtre HD (docs/SCENES-HD.md) : TheatreHd.java et Theatre.java calculent ce que calcule la référence
 * (outils/sprites/theatre_hd.py, relue aussi par TheatreTests.cs) : décors décodés (empreinte de chaque image de chaque
 * plan), état et pose du Pilou, acteurs, personnage, et l'empreinte de l'image composée pixel à pixel.
 */
public class TheatreHdTest {
    private static String lire(File f) throws Exception {
        return new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
    }

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

    private static String texte(Theatre.Pose q) {
        return q.sprite + " " + q.image + " " + q.x + " " + q.y + " " + (q.miroir ? 1 : 0);
    }

    @Test
    public void memesDecorsQueLaReference() throws Exception {
        File f = new File(RenduPilouTest.racine(), "outils/sprites/theatre-hd-reference.txt");
        int n = 0;
        for (String l : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
            if (!l.startsWith("decor ")) continue;
            String[] p = l.split(" ");
            TheatreHd.Decor d = TheatreHd.lireDecorHd(Sprites.ressource("/decors/" + p[1] + ".txt"));
            assertEquals(p[1], d.id);
            TheatreHd.Plan plan = null;
            for (TheatreHd.Plan q : d.plans) if (q.nom.equals(p[2])) plan = q;
            assertNotNull(l, plan);
            assertEquals(l, Integer.parseInt(p[3]), d.w);
            assertEquals(l, Integer.parseInt(p[4]), d.h);
            assertEquals(l, Integer.parseInt(p[5]), plan.images.length);
            assertEquals(l, Integer.parseInt(p[6]), plan.duree);
            for (int i = 0; i < plan.images.length; i++)
                assertEquals(p[1] + " image " + i, Long.parseLong(p[7 + i]), Theatre.fnv(plan.images[i]));
            n++;
        }
        assertTrue(n + " décors", n >= 6);
    }

    @Test
    public void memesScenesQueLaReference() throws Exception {
        Sprites.Banque b = Sprites.banque();
        Map<String, Map<String, Theatre.Anim>> anims = Theatre.lireAnimations(Sprites.ressource("/scenes/animations.txt"));
        Function<Map<String, Object>, int[]> rendre = TheatreHd.rendeurPilou(null, b);
        File f = new File(RenduPilouTest.racine(), "outils/sprites/theatre-hd-reference.txt");
        Theatre.Contexte cx = null;
        TheatreHd.Decor decor = null;
        String niveau = "", nom = "";
        int regard = 0;
        List<Theatre.Evenement> evts = new ArrayList<>();
        List<String> acteursAttendus = new ArrayList<>();
        String persoAttendu = "-";
        int n = 0, images = 0, poses = 0;
        for (String l : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
            if (l.isEmpty() || l.startsWith("#") || l.startsWith("decor ")) continue;
            String[] p = l.split(" ", -1);
            switch (p[0]) {
                case "scenario": {
                    nom = p[1];
                    Theatre.Scene sc = TheatreHd.scenes(p[2]).get(p[3]);
                    assertNotNull(l, sc);
                    cx = new Theatre.Contexte(sc, anims, id -> fin(b, id), TheatreHd::spriteHd);
                    decor = TheatreHd.decor(p[2], p[3]);        // null : pas encore de décor, fond noir
                    niveau = p[4];
                    regard = Integer.parseInt(p[5]);
                    evts = new ArrayList<>();
                    break;
                }
                case "evenement":
                    evts.add(evenement(p));
                    break;
                case "pilou": {
                    long t = Long.parseLong(p[1]);
                    Theatre.Etat e = Theatre.pilouEtat(cx, evts, t, regard, niveau);
                    String vu = e.x + " " + e.y + " " + e.anim + " " + e.dt + " " + (e.miroir ? 1 : 0) + " " + (e.visible ? 1 : 0) + " " + e.humeur;
                    assertEquals(nom + " : " + l, String.join(" ", Arrays.copyOfRange(p, 2, p.length)), vu);
                    acteursAttendus = new ArrayList<>();
                    persoAttendu = "-";
                    break;
                }
                case "pose": {
                    long t = Long.parseLong(p[1]);
                    Map<String, Object> vue = Theatre.poseHd(Theatre.pilouEtat(cx, evts, t, regard, niveau), t);
                    Map<String, String> attendue = new TreeMap<>();
                    for (int i = 2; i < p.length; i++) {
                        String[] kv = p[i].split("=", 2);
                        attendue.put(kv[0], kv[1]);
                    }
                    assertEquals(nom + " : champs de " + l, attendue.keySet(), new TreeMap<>(vue).keySet());
                    for (Map.Entry<String, String> e : attendue.entrySet()) {
                        Object v = vue.get(e.getKey());
                        String ou = nom + " : " + l + " (" + e.getKey() + ")";
                        if (v instanceof Double) assertEquals(ou, Double.parseDouble(e.getValue()), (Double) v, 0.0);
                        else if (v instanceof Boolean) assertEquals(ou, e.getValue(), (Boolean) v ? "1" : "0");
                        else assertEquals(ou, e.getValue(), String.valueOf(v));
                    }
                    poses++;
                    break;
                }
                case "acteur":
                    acteursAttendus.add(String.join(" ", Arrays.copyOfRange(p, 2, p.length)));
                    break;
                case "perso":
                    persoAttendu = String.join(" ", Arrays.copyOfRange(p, 2, p.length));
                    break;
                case "image": {
                    long t = Long.parseLong(p[1]);
                    List<String> vus = new ArrayList<>();
                    for (Theatre.Pose q : Theatre.acteurs(cx, evts, t, niveau)) vus.add(texte(q));
                    for (Theatre.Pose q : Theatre.effets(cx, evts, t, niveau)) vus.add(texte(q));
                    assertEquals(nom + " : acteurs à " + t, acteursAttendus, vus);
                    Theatre.Pose pp = Theatre.perso(cx, evts, t, niveau);
                    assertEquals(nom + " : personnage à " + t, persoAttendu, pp == null ? "-" : texte(pp));
                    int[] px = TheatreHd.composerHd(decor, cx, evts, t, rendre, regard, niveau, null);
                    assertEquals(nom + " : image à " + t + " ms", Long.parseLong(p[2]), Theatre.fnv(px));
                    images++;
                    break;
                }
                default:
                    fail("ligne inconnue : " + l);
            }
            n++;
        }
        assertTrue(n + " lignes, " + images + " images, " + poses + " poses", images >= 25 && poses == images);
    }

    @Test
    public void laDefinitionHdEstPorteeParLaScene() {
        Theatre.Scene sc = TheatreHd.scenes("prologue").get("mare");
        assertNotNull(sc);
        assertEquals(480, sc.d.w);
        assertEquals(240, sc.d.h);
        assertEquals(35 + 480, 480 + Theatre.e(sc, Theatre.SORTIE_D - Theatre.W));
        assertEquals(-35, Theatre.e(sc, -14));
        assertEquals(Theatre.ANCIENNE, new Theatre.Scene().d);
        assertEquals(78, new Theatre.Scene().sol[1]);
        assertEquals(238, new Theatre.Scene(Theatre.HD).sol[1]);
    }
}
