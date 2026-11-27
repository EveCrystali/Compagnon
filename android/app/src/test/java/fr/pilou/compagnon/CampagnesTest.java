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
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Campagnes : le moteur du téléphone rejoue les vecteurs écrits par celui du PC (apps/PilouBureau/tests/CampagnesVecteurs.cs)
 * et doit trouver, ligne à ligne, les mêmes états, les mêmes tirages et les mêmes messages.
 */
public class CampagnesTest {
    private static final long T0 = 1_790_000_000_000L;
    private static Campagnes.Campagne essai;

    private static String ressource(String chemin) {
        try (InputStream in = CampagnesTest.class.getClassLoader().getResourceAsStream(chemin)) {
            return in == null ? null : new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        }
    }

    /** La campagne d'essai (src/test/resources/campagnes-essai/essai) : toutes les règles du moteur en 19 nœuds. */
    static Campagnes.Campagne essai() {
        if (essai == null) essai = Campagnes.lire(ressource("campagnes-essai/essai/campagne.json"), f -> ressource("campagnes-essai/essai/" + f));
        return essai;
    }

    static Campagnes.Campagne biblio(String id) {
        return id.equals("essai") ? essai() : Campagnes.charger(id);
    }

    private static String empreinte(String s) {
        long h = 0xcbf29ce484222325L;
        for (int i = 0; i < s.length(); i++) {
            h ^= s.charAt(i);
            h *= 0x100000001b3L;
        }
        return String.format(Locale.ROOT, "%016x", h);
    }

    private static String ok(String refus) {
        return refus == null ? "ok" : refus;
    }

    /** Rejoue une ligne du fichier et renvoie ce que le moteur d'ici en dit (la ligne refaite). */
    private static final class Lecteur {
        Campagnes.Campagne c;
        Campagnes.Partie p;
        final Map<String, Campagnes.Carnet> carnets = new HashMap<>();
        Campagnes.Carnet k;
        int restants;
        List<String> attendus = new ArrayList<>();

        String refaire(String ligne) throws Exception {
            if (ligne.startsWith("#")) return ligne;
            if (restants > 0) {
                restants--;
                return "m " + attendus.remove(0);
            }
            String[] m = ligne.split(" ");
            String debut;
            switch (m[0]) {
                case "code":
                    return "code " + m[1] + " " + Campagnes.code(m[1]);
                case "tirage":
                    return "tirage " + m[1] + " " + m[2] + " " + m[3] + " "
                            + Campagnes.tirage(m[1].equals("-") ? "" : m[1], Integer.parseInt(m[2])).suivant(Integer.parseInt(m[3]));
                case "chance":
                    return "chance " + m[1] + " " + m[2] + " " + Campagnes.chanceDe(Integer.parseInt(m[1]), Integer.parseInt(m[2]));
                case "sujet":
                    return "sujet " + m[1] + " " + Campagnes.sujet(m[1]);
                case "cas":
                    return ligne;
                case "campagne":
                    c = biblio(m[1]);
                    assertNotNull("campagne " + m[1], c);
                    return ligne;
                case "partie":
                    p = Campagnes.lirePartie(ligne.substring("partie ".length()));
                    assertNotNull(ligne, p);
                    return ligne;
                case "rejouer":
                    return "rejouer " + m[1] + " " + Campagnes.rejouer(c, p, Long.parseLong(m[1])).texte();
                case "decider": {
                    Campagnes.Partie q = Campagnes.decider(c, p, Long.parseLong(m[1]), m[2], Integer.parseInt(m[3]));
                    if (q != null) p = q;
                    return "decider " + m[1] + " " + m[2] + " " + m[3] + " " + (q == null ? "refus" : empreinte(Campagnes.jsonPartie(q)));
                }
                case "de":
                    return "de " + m[1] + " " + (Campagnes.deDe(p, Campagnes.rejouer(c, p, Long.parseLong(m[1]))) ? 1 : 0);
                case "compacter":
                    p = Campagnes.compacter(c, p, Long.parseLong(m[1]));
                    return "compacter " + m[1] + " " + Campagnes.jsonPartie(p);
                case "carnet":
                    k = carnets.get(m[1]);
                    if (k == null) carnets.put(m[1], k = new Campagnes.Carnet());
                    return ligne;
                case "demarrer":
                    debut = "demarrer " + m[1] + " " + m[2] + " " + m[3] + " " + m[4] + " " + m[5] + " " + m[6] + " ";
                    return debut + ok(Campagnes.demarrer(k, biblio(m[1]), Integer.parseInt(m[2]), Long.parseLong(m[3]), m[4],
                            CampagnesTest::biblio, m[5], m[6].equals("1")));
                case "choisir":
                    return "choisir " + m[1] + " " + m[2] + " " + m[3] + " " + m[4] + " "
                            + ok(Campagnes.choisir(k, biblio(m[1]), Long.parseLong(m[2]), m[3], m[4]));
                case "continuer":
                    return "continuer " + m[1] + " " + m[2] + " " + m[3] + " " + ok(Campagnes.continuer(k, biblio(m[1]), Long.parseLong(m[2]), m[3]));
                case "epreuve":
                    return "epreuve " + m[1] + " " + m[2] + " " + m[3] + " " + m[4] + " "
                            + ok(Campagnes.epreuve(k, biblio(m[1]), Long.parseLong(m[2]), m[3], m[4].equals("1")));
                case "aude":
                    return "aude " + m[1] + " " + m[2] + " " + m[3] + " " + ok(Campagnes.epreuveAuDe(k, biblio(m[1]), Long.parseLong(m[2]), m[3]));
                case "abandonner":
                    return "abandonner " + m[1] + " " + m[2] + " " + m[3] + " " + ok(Campagnes.abandonner(k, biblio(m[1]), Long.parseLong(m[2]), m[3]));
                case "actualiser": {
                    Campagnes.Etat e = Campagnes.actualiser(k, CampagnesTest::biblio, Long.parseLong(m[1]));
                    return "actualiser " + m[1] + " " + (e == null ? "rien" : e.texte());
                }
                case "messages": {
                    attendus = new ArrayList<>(Campagnes.messages(k, m[1], m[2]));
                    restants = attendus.size();
                    return "messages " + m[1] + " " + m[2] + " " + attendus.size();
                }
                case "recevoir": {
                    String json = ligne.substring(("recevoir " + m[1] + " " + m[2] + " " + m[3] + " ").length());
                    return "recevoir " + m[1] + " " + m[2] + " " + (Campagnes.recevoir(k, json, m[1], CampagnesTest::biblio, Long.parseLong(m[2])) ? 1 : 0) + " " + json;
                }
                case "signature":
                    return "signature " + Campagnes.signature(k);
                case "fil": {
                    StringBuilder b = new StringBuilder();
                    for (Campagnes.Message x : k.fil)
                        b.append(x.p).append('.').append(x.e).append('.').append(x.i).append('.').append(x.qui).append('.').append(x.noeud).append('.').append(x.texte).append('\n');
                    return "fil " + k.fil.size() + " " + k.nonLus() + " " + empreinte(b.toString());
                }
                case "lu":
                    Campagnes.marquerLu(k);
                    return ligne;
                case "acquis": {
                    Campagnes.Campagne x = biblio(m[1]);
                    int[] a = Campagnes.acquis(k, x);
                    List<String> fins = new ArrayList<>();
                    for (Campagnes.FinObtenue f : Campagnes.fins(k, x)) fins.add(f.noeud);
                    return "acquis " + m[1] + " " + a[0] + " " + a[1] + " " + String.join(",", fins);
                }
                case "attente": {
                    int[] a = Campagnes.enAttente(k, CampagnesTest::biblio);
                    return "attente " + a[0] + " " + a[1];
                }
                default:
                    fail("opération inconnue : " + ligne);
                    return "";
            }
        }
    }

    @Test
    public void memesVecteursQueLePc() throws Exception {
        String texte = ressource("campagnes-vecteurs.txt");
        assertNotNull("campagnes-vecteurs.txt (src/test/resources) : PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests", texte);
        Lecteur l = new Lecteur();
        String[] lignes = texte.replace("\r\n", "\n").split("\n");
        int faites = 0;
        for (int i = 0; i < lignes.length; i++) {
            if (lignes[i].isEmpty()) continue;
            assertEquals("ligne " + (i + 1), lignes[i], l.refaire(lignes[i]));
            faites++;
        }
        assertTrue("vecteurs trop courts : " + faites, faites > 500);
    }

    /** Vecteurs d'autres campagnes, écrits par le PC (PILOU_VECTEURS=<fichier>, voir CampagnesTests.cs) : même rejeu. */
    @Test
    public void vecteursDUnAutreFichier() throws Exception {
        String fichier = System.getenv("PILOU_VECTEURS");
        if (fichier == null || fichier.isEmpty()) return;
        String texte = new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(fichier)), StandardCharsets.UTF_8);
        Lecteur l = new Lecteur();
        String[] lignes = texte.replace("\r\n", "\n").split("\n");
        for (int i = 0; i < lignes.length; i++)
            if (!lignes[i].isEmpty()) assertEquals(fichier + ", ligne " + (i + 1), lignes[i], l.refaire(lignes[i]));
    }

    @Test
    public void leProloguEstEmbarque() {
        // L'index est écrit à la compilation (app/build.gradle) : Android ne sait pas lister ses ressources.
        assertTrue(Campagnes.disponibles().toString(), Campagnes.disponibles().contains("prologue"));
        for (String id : Campagnes.disponibles()) {
            Campagnes.Campagne c = Campagnes.charger(id);
            assertNotNull(id, c);
            assertEquals(id, c.id);
            assertNotNull(id + " : départ", c.noeud(c.depart));
            for (Campagnes.Chapitre ch : c.chapitres) {
                boolean vu = false;
                for (Campagnes.Noeud n : c.noeuds.values()) vu |= n.chapitre.equals(ch.id);
                assertTrue(id + " : chapitre " + ch.id + " vide ou illisible (" + ch.fichier + ")", vu);
            }
        }
        Campagnes.Campagne p = Campagnes.charger("prologue");
        assertEquals("La colline d'en face", p.titre);
        assertEquals(1, p.niveau);
        assertEquals(2, p.chapitres.size());
        assertEquals(25, p.noeuds.size());
        assertEquals("peur", p.noeud("p1-mare").humeur);
        assertEquals(6, p.decors.size());
        assertNull(Campagnes.charger("inconnue"));
        assertNull(Campagnes.charger("../secret"));
    }

    @Test
    public void unePartieDuPrologueSurLeTelephone() {
        Campagnes.Carnet k = new Campagnes.Carnet();
        Campagnes.Campagne c = Campagnes.charger("prologue");
        assertEquals("niveau 3 requis", Campagnes.demarrer(k, essai(), 1, T0, "tel", CampagnesTest::biblio, "g", false));
        assertNull(Campagnes.demarrer(k, c, 1, T0, "tel", CampagnesTest::biblio, "g", false));
        Campagnes.Etat e = Campagnes.actualiser(k, CampagnesTest::biblio, T0);
        assertEquals(Campagnes.Phase.Choix, e.phase);
        assertEquals(3, e.options.size());
        assertEquals(3, k.nonLus());
        assertEquals("Devant la porte", e.lieu);
        assertEquals("seuil", e.decor);
        assertNull(Campagnes.choisir(k, c, T0 + 5000, "tel", "lampe"));
        e = Campagnes.actualiser(k, CampagnesTest::biblio, T0 + 6000);
        assertEquals(Campagnes.Phase.Attente, e.phase);
        assertEquals(T0 + 65_000, e.fin);                              // de quoi programmer la notification locale
        assertEquals("Pilou traverse le jardin", e.pendant);
        assertEquals("marche", e.tenue);
        assertTrue(Campagnes.ligne(e).startsWith("Pilou traverse le jardin · retour vers "));
        assertEquals("ce n'est pas possible maintenant", Campagnes.choisir(k, c, T0 + 7000, "tel", "saute"));
        e = Campagnes.actualiser(k, CampagnesTest::biblio, e.fin);
        assertEquals(Campagnes.Phase.Choix, e.phase);
        assertEquals("p1-mare", e.noeud);
        assertEquals(2, e.options.size());                             // pas de pont sans corde

        // Le carnet se garde dans les préférences et se relit tel quel.
        Campagnes.Carnet relu = Campagnes.relire(Campagnes.sauver(k));
        assertEquals(Campagnes.signature(k), Campagnes.signature(relu));
        assertEquals(k.fil.size(), relu.fil.size());
        assertEquals(k.fil.get(k.fil.size() - 1).texte, relu.fil.get(relu.fil.size() - 1).texte);
        assertEquals(k.nonLus(), relu.nonLus());
        assertEquals(e.texte(), Campagnes.actualiser(relu, CampagnesTest::biblio, e.t).texte());
        assertNull(Campagnes.relire("pas du json").courante);
        assertTrue(Campagnes.messages(new Campagnes.Carnet(), "tel", "tel").isEmpty());

        // Le message tient sous la limite du relais, une fois chiffré.
        for (String m : Campagnes.messages(k, "tel-0123456789ab", "tel")) assertTrue(Campagnes.octets(m) <= Campagnes.TAILLE_JSON);
    }

    /** Chaque campagne embarquée (et la campagne d'essai) se joue jusqu'à une fin, au hasard, sans casse ni message trop gros. */
    @Test
    public void toutesLesCampagnesSeJouentJusquAUneFin() {
        List<Campagnes.Campagne> toutes = new ArrayList<>();
        for (String id : Campagnes.disponibles()) toutes.add(Campagnes.charger(id));
        toutes.add(essai());
        for (Campagnes.Campagne c : toutes) {
            for (int g = 0; g < 12; g++) {
                java.util.Random h = new java.util.Random(1000L * g + c.id.length());
                Campagnes.Carnet k = new Campagnes.Carnet();
                long t = T0;
                assertNull(Campagnes.demarrer(k, c, 99, t, "tel", CampagnesTest::biblio, "graine" + g, false));
                Campagnes.Etat e = Campagnes.actualiser(k, CampagnesTest::biblio, t);
                for (int i = 0; i < 4000 && e.enCours(); i++) {
                    if (e.enAttente()) t = e.fin;
                    t += 30_000 + h.nextInt(600) * 1000L;
                    e = Campagnes.actualiser(k, CampagnesTest::biblio, t);
                    String ou = c.id + ", graine " + g + ", nœud " + e.noeud;
                    String r = null;
                    if (e.phase == Campagnes.Phase.Choix) {
                        assertFalse(ou + " : aucune option", e.options.isEmpty());
                        r = Campagnes.choisir(k, c, t, "tel", e.options.get(h.nextInt(e.options.size())).id);
                    } else if (e.phase == Campagnes.Phase.Epreuve) {
                        r = h.nextBoolean() ? Campagnes.epreuveAuDe(k, c, t, "tel") : Campagnes.epreuve(k, c, t, "tel", h.nextInt(3) != 0);
                    } else if (e.phase == Campagnes.Phase.Depart) r = Campagnes.continuer(k, c, t, "tel");
                    assertNull(ou, r);
                    e = Campagnes.actualiser(k, CampagnesTest::biblio, t);
                    assertTrue(ou + " : partie cassée", e.phase != Campagnes.Phase.Cassee);
                    for (String m : Campagnes.messages(k, "tel-0123456789ab", "tel")) assertTrue(ou + " : message trop gros", Campagnes.octets(m) <= Campagnes.TAILLE_JSON);
                    // Le carnet gardé puis relu donne le même état (préférences du téléphone).
                    if (i % 7 == 0) assertEquals(ou, Campagnes.signature(k), Campagnes.signature(Campagnes.relire(Campagnes.sauver(k))));
                }
                assertEquals(c.id + ", graine " + g + " : pas de fin (nœud " + e.noeud + ")", Campagnes.Phase.Fin, e.phase);
                int[] acquis = Campagnes.acquis(k, c);
                assertTrue(c.id + " : " + acquis[0] + " po, " + acquis[1] + " xp", acquis[0] <= 600 && acquis[1] <= 300);
            }
        }
    }

    @Test
    public void repriseEtObjetsPortables() {
        Campagnes.Campagne c = essai();
        Campagnes.Nomme cape = null;
        for (Campagnes.Nomme o : c.objets) if (o.id.equals("cape-d-essai")) cape = o;
        assertNotNull(cape);
        assertTrue(cape.portable);
        assertEquals("dos", cape.emplacement);
        // Nord, vas-y, épreuve réussie, puis le trou : un piège, le repos, et le retour au check-point « b-entree ».
        Campagnes.Carnet k = new Campagnes.Carnet();
        long t = T0;
        assertNull(Campagnes.demarrer(k, c, 9, t, "tel", CampagnesTest::biblio, "g", false));
        assertNull(Campagnes.choisir(k, c, t += 1000, "tel", "nord"));
        t = Campagnes.actualiser(k, CampagnesTest::biblio, t).fin;
        assertNull(Campagnes.continuer(k, c, t, "tel"));
        t = Campagnes.actualiser(k, CampagnesTest::biblio, t).fin;
        assertNull(Campagnes.epreuve(k, c, t, "tel", true));
        assertNull(Campagnes.choisir(k, c, t += 1000, "tel", "trou"));
        Campagnes.Etat e = Campagnes.actualiser(k, CampagnesTest::biblio, t);
        assertEquals(Campagnes.Phase.Repos, e.phase);
        assertFalse(e.reprise);
        e = Campagnes.actualiser(k, CampagnesTest::biblio, e.fin);
        assertEquals("b-entree", e.noeud);
        assertTrue(e.reprise);
        Campagnes.Message dernier = k.fil.get(k.fil.size() - 1);
        assertTrue(dernier.reprise);
        assertEquals("La maison. Par où entrer ?", dernier.texte);
        assertTrue(Campagnes.relire(Campagnes.sauver(k)).fil.get(k.fil.size() - 1).reprise);
        assertNull(Campagnes.choisir(k, c, e.t + 1000, "tel", "porte"));
        e = Campagnes.actualiser(k, CampagnesTest::biblio, e.t + 2000);
        assertFalse(e.reprise);
        assertEquals("cape-d-essai", Campagnes.objetsGagnes(k, c).get(0));
        assertEquals("Testeur de portes", Campagnes.titres(k, c).get(0));
    }

    @Test
    public void recompensesEnAttenteDuPc() {
        Campagnes.Carnet tel = new Campagnes.Carnet();
        Campagnes.Campagne c = Campagnes.charger("prologue");
        long t = T0;
        assertNull(Campagnes.demarrer(tel, c, 1, t, "tel", CampagnesTest::biblio, "g", false));
        Campagnes.Etat e = Campagnes.actualiser(tel, CampagnesTest::biblio, t);
        for (int i = 0; i < 40 && e.phase != Campagnes.Phase.Fin; i++) {
            if (e.enAttente()) t = e.fin;
            t += 1000;
            e = Campagnes.actualiser(tel, CampagnesTest::biblio, t);
            if (e.phase == Campagnes.Phase.Choix) {
                String option = e.options.get(0).id;
                for (Campagnes.OptionVue o : e.options) if (o.id.equals("tour") || o.id.equals("sentier") || o.id.equals("rentre")) option = o.id;
                assertNull(Campagnes.choisir(tel, c, t, "tel", option));
            } else if (e.phase == Campagnes.Phase.Depart) assertNull(Campagnes.continuer(tel, c, t, "tel"));
            e = Campagnes.actualiser(tel, CampagnesTest::biblio, t);
        }
        assertEquals(Campagnes.Phase.Fin, e.phase);
        assertEquals("douce-amere", e.issue);
        assertEquals(15, Campagnes.acquis(tel, c)[0]);
        assertEquals(8, Campagnes.acquis(tel, c)[1]);
        assertEquals(15, Campagnes.enAttente(tel, CampagnesTest::biblio)[0]);   // le PC est éteint : rien n'est versé
        assertEquals("question-gardee", Campagnes.souvenirs(tel, c).get(0).id);
        assertFalse(Campagnes.enCours(tel, CampagnesTest::biblio, t));
        // Un PC reçoit le message du téléphone, puis publie le sien : les récompenses n'attendent plus.
        Campagnes.Carnet pc = new Campagnes.Carnet();
        for (String m : Campagnes.messages(tel, "tel", "tel")) assertTrue(Campagnes.recevoir(pc, m, "pc", CampagnesTest::biblio, t));
        for (String m : Campagnes.messages(pc, "pc", "pc")) Campagnes.recevoir(tel, m, "tel", CampagnesTest::biblio, t);
        assertEquals(0, Campagnes.enAttente(tel, CampagnesTest::biblio)[0]);
        assertEquals(Campagnes.signature(pc), Campagnes.signature(tel));
    }
}
