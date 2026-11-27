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
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

/**
 * La présence au quotidien : le moteur du téléphone (Presence.java) rejoue les vecteurs écrits par celui du PC
 * (apps/PilouBureau/tests/PresenceTests.cs) et trouve, ligne à ligne, les mêmes mots, les mêmes entrées du journal, les
 * mêmes totaux et les mêmes messages. Puis les règles du téléphone : un mot par jour au plus, le soir, réglable.
 */
public class PresenceTest {
    private static String ressource(String chemin) {
        try (InputStream in = PresenceTest.class.getClassLoader().getResourceAsStream(chemin)) {
            return in == null ? null : new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        }
    }

    static String desechapper(String s) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\\' && i + 1 < s.length()) {
                char n = s.charAt(++i);
                b.append(n == 'n' ? '\n' : n == 't' ? '\t' : n);
            } else b.append(c);
        }
        return b.toString();
    }

    static String echapper(String s) {
        return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t");
    }

    private static LocalDateTime date(String s) {
        return LocalDateTime.parse(s.length() == 16 ? s + ":00" : s);
    }

    private static Map<String, Integer> dits(String s) {
        Map<String, Integer> d = new HashMap<>();
        if (s.isEmpty()) return d;
        for (String x : s.split(",")) {
            int i = x.indexOf(':');
            d.put(x.substring(0, i), Integer.parseInt(x.substring(i + 1)));
        }
        return d;
    }

    /** Refait une ligne des vecteurs et renvoie la ligne recalculée (égale à l'entrée si tout concorde). */
    static String refaire(String ligne) {
        if (ligne.startsWith("#")) return ligne;
        String[] c = ligne.split("\t", -1);
        StringBuilder debut = new StringBuilder();
        for (int i = 0; i < c.length - 1; i++) debut.append(c[i]).append('\t');
        String r = debut.toString();
        switch (c[0]) {
            case "hash":
                return r + String.format("%016x", Presence.hash(c[1]));
            case "mot": {
                Presence.Contexte x = new Presence.Contexte(date(c[2]), Presence.Moment.valueOf(c[1]));
                x.absenceMin = Double.parseDouble(c[3]);
                x.presenceJourMin = Double.parseDouble(c[4]);
                x.seanceMin = Double.parseDouble(c[5]);
                x.activite = c[6];
                x.meteo = c[7];
                x.palier = Integer.parseInt(c[8]);
                x.stade = Integer.parseInt(c[9]);
                x.variante = c[10];
                x.prenom = c[11];
                x.metier = c[12];
                x.niveau = Integer.parseInt(c[13]);
                x.objet = c[14];
                x.prise = c[15];
                x.plat = c[16];
                x.souvenir = c[17];
                x.dateAFeter = c[18];
                x.palierNouveau = Integer.parseInt(c[19]);
                x.demanderPrenom = c[20].equals("1");
                x.joursEnsemble = Integer.parseInt(c[21]);
                x.annees = Integer.parseInt(c[22]);
                Presence.Choix ch = Presence.mot(x, Presence.mots(), dits(c[23]), c[24]);
                return r + (ch == null ? "-" : ch.famille + "|" + ch.ligne.id + "|" + ch.texte);
            }
            case "journal": {
                Presence.Entree e = Presence.ecrire(c[1], Presence.FaitsDuJour.lire(c[2]), Presence.gabarits());
                return r + (e == null ? "-" : e.texte + "|" + e.humeur);
            }
            case "fusion":
                return r + Presence.FaitsDuJour.fusion(Presence.FaitsDuJour.lire(c[1]), Presence.FaitsDuJour.lire(c[2])).texte();
            case "soir":
                return r + Presence.minuteDuSoir(c[1], c[2]);
            case "jourdemot":
                return r + (Presence.jourDeMot(LocalDate.parse(c[1]).atStartOfDay(), c[2], c[3]) ? "1" : "0");
            case "message": {
                Presence.Etat e = Presence.Etat.lire(desechapper(c[1]));
                return r + echapper(e.message(Integer.parseInt(c[2])));
            }
            case "recevoir": {
                Presence.Etat e = Presence.Etat.lire(desechapper(c[1]));
                boolean change = e.recevoir(Presence.Appareil.lireMessage(desechapper(c[2])), Integer.parseInt(c[3]));
                if (c[4].equals("1")) e.compacter(Integer.parseInt(c[3]));
                StringBuilder s = new StringBuilder();
                for (int i = 0; i < 5; i++) s.append(c[i]).append('\t');
                return s + (change ? "1" : "0") + "\t" + echapper(e.texte());
            }
            case "totaux": {
                Presence.Etat e = Presence.Etat.lire(desechapper(c[1]));
                Presence.Totaux t = e.totaux();
                String d = Presence.dateAFeter(t, Integer.parseInt(c[2]));
                return r + t.points + " " + t.palier + " " + t.jours + " " + t.adoption + " " + (d.isEmpty() ? "-" : d);
            }
            case "cadence": {
                Presence.Etat e = Presence.Etat.lire(desechapper(c[1]));
                long t = Long.parseLong(c[2]);
                Presence.observer(e.cadence, t, date(c[3]), c[4].equals("1"));
                Presence.Moment m = Presence.pret(e.cadence, t, c[5], c[6].equals("1"));
                if (m != null) Presence.noter(e.cadence, t, m);
                StringBuilder s = new StringBuilder();
                for (int i = 0; i < 7; i++) s.append(c[i]).append('\t');
                return s + (m == null ? "-" : m.name()) + "\t" + echapper(e.texte());
            }
            default:
                fail("opération inconnue : " + c[0]);
                return "";
        }
    }

    @Test
    public void memesVecteursQueLePc() {
        String texte = ressource("presence-vecteurs.txt");
        assertNotNull("presence-vecteurs.txt (src/test/resources) : PILOU_REGENERER=1 dotnet test apps/PilouBureau/tests", texte);
        String[] lignes = texte.replace("\r\n", "\n").split("\n");
        int faites = 0;
        for (int i = 0; i < lignes.length; i++) {
            if (lignes[i].isEmpty()) continue;
            assertEquals("ligne " + (i + 1), lignes[i], refaire(lignes[i]));
            faites++;
        }
        assertTrue("vecteurs trop courts : " + faites, faites > 2000);
    }

    @Test
    public void laBanqueEstLaMemeQueCelleDuPc() {
        List<Presence.Ligne> mots = Presence.mots();
        assertTrue(mots.size() + " mots", mots.size() >= 400);
        Set<String> ids = new HashSet<>();
        for (Presence.Ligne l : mots) {
            assertTrue(l.texte, l.texte.length() <= Presence.LONGUEUR_MAX);
            assertTrue("doublon : " + l.texte, ids.add(l.id));
        }
        assertFalse(Presence.gabarits().isEmpty());
    }

    @Test
    public void auPlusUnMotParJourEtJamaisLaNuit() {
        Random h = new Random(5);
        for (int i = 0; i < 500; i++) {
            String jour = LocalDate.of(2026, 1, 1).plusDays(i).toString();
            int m = Presence.minuteDuSoir(jour, "tel-" + h.nextInt(1000));
            assertTrue(m >= 19 * 60 && m <= 20 * 60 + 30);
        }
        int parfois = 0, chaque = 0, jamais = 0;
        for (int i = 0; i < 70; i++) {
            LocalDateTime d = LocalDate.of(2026, 3, 2).plusDays(i).atTime(19, 30);
            if (Presence.jourDeMot(d, "parfois", "normal")) parfois++;
            if (Presence.jourDeMot(d, "chaque", "normal")) chaque++;
            if (Presence.jourDeMot(d, "chaque", "jamais") || Presence.jourDeMot(d, "jamais", "normal")) jamais++;
        }
        assertEquals(70, chaque);
        assertEquals(0, jamais);
        assertTrue("parfois : " + parfois, parfois >= 20 && parfois <= 30); // 2 à 3 par semaine
    }

    @Test
    public void laComplicitéNeBaisseJamais() {
        Presence.Etat tel = neuf("tel-1"), pc = neuf("pc-1");
        Random h = new Random(9);
        List<String> messages = new ArrayList<>();
        int avant = 0;
        LocalDateTime d = LocalDateTime.of(2026, 4, 1, 19, 0);
        for (int i = 0; i < 200; i++) {
            if (i % 6 == 0) d = d.plusDays(1 + h.nextInt(4));
            Presence.Etat qui = h.nextBoolean() ? tel : pc;
            qui.ajouter(new String[]{"minutes", "caresses", "soins", "jeux"}[h.nextInt(4)], 1 + h.nextInt(20), d);
            messages.add(qui.message(Presence.jour(d)));
            String m = messages.get(h.nextInt(messages.size()));
            tel.recevoir(Presence.Appareil.lireMessage(m), Presence.jour(d));
            int p = tel.totaux().points;
            assertTrue(avant + " → " + p, p >= avant);
            avant = p;
        }
        for (String m : messages) tel.recevoir(Presence.Appareil.lireMessage(m), Presence.jour(d));
        int fige = tel.totaux().points;
        for (String m : messages) assertFalse(tel.recevoir(Presence.Appareil.lireMessage(m), Presence.jour(d)) && tel.totaux().points != fige);
        assertEquals(fige, tel.totaux().points);
    }

    @Test
    public void lePrenomRefuseNeRevientPas() {
        Presence.Etat e = neuf("tel-1");
        assertEquals("", e.prenom());
        e.moi.prenomDemande = true;
        assertTrue(e.totaux().prenomDemande);
        e.choisirPrenom(" Lou ", 10);
        assertEquals("Lou", e.prenom());
        e.choisirPrenom("", 11);
        assertEquals("", e.prenom());
        assertNull(Presence.Appareil.lireMessage("autre chose"));
    }

    static Presence.Etat neuf(String id) {
        Presence.Etat e = new Presence.Etat();
        e.moi.id = id;
        e.moi.sorte = id.startsWith("tel") ? "tel" : "pc";
        return e;
    }
}
