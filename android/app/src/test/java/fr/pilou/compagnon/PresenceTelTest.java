package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

import android.content.Context;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;

/** Le téléphone : un mot par jour au plus, le soir, jamais la nuit, réglable ; complicité et prénom gardés localement. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
public class PresenceTelTest {
    private Context c;

    @Before
    public void neuf() {
        c = RuntimeEnvironment.getApplication();
        Prefs.de(c).edit().clear().commit();
        Retour.auPremierPlan = false;
    }

    @Test
    public void auPlusUnMotDuSoirParJour() {
        LocalDateTime soir = LocalDate.now().atTime(19, 45);
        assertTrue(MotDuSoir.envoyer(c, soir));
        assertFalse("déjà envoyé aujourd'hui", MotDuSoir.envoyer(c, soir.plusMinutes(40)));
        LocalDate demain = LocalDate.now().plusDays(1);
        assertFalse("jamais la nuit", MotDuSoir.envoyer(c, demain.atTime(23, 30)));
        assertFalse("jamais la nuit", MotDuSoir.envoyer(c, demain.atTime(3, 0)));
        assertFalse("jamais en pleine journée", MotDuSoir.envoyer(c, demain.atTime(11, 0)));
    }

    @Test
    public void leMotDuJourEstLeMemePartoutEtSeTaitSurDemande() {
        String m = PresenceTel.motDuJour(c);
        assertFalse(m.isEmpty());
        assertEquals(m, PresenceTel.motDuJour(c));
        Presence.Etat e = PresenceTel.etat(c);
        e.parle = "jamais";
        PresenceTel.garder(c, e);
        assertEquals("", PresenceTel.motDuJour(c));
        assertFalse(MotDuSoir.envoyer(c, LocalDate.now().atTime(19, 50)));
        assertEquals(-1, MotDuSoir.prochain(c, LocalDateTime.now()));
    }

    @Test
    public void leProchainMotTombeLeSoir() {
        Presence.Etat e = PresenceTel.etat(c);
        e.frequence = "parfois";
        PresenceTel.garder(c, e);
        long t = MotDuSoir.prochain(c, LocalDate.now().atTime(8, 0));
        assertNotEquals(-1, t);
        LocalDateTime quand = java.time.Instant.ofEpochMilli(t).atZone(ZoneId.systemDefault()).toLocalDateTime();
        int minute = quand.getHour() * 60 + quand.getMinute();
        assertTrue(quand.toString(), minute >= 19 * 60 && minute <= 20 * 60 + 30);
        assertTrue(Presence.jourDeMot(quand, "parfois", "normal"));
    }

    @Test
    public void lesGestesDuTelephoneNourrissentLaComplicite() {
        int avant = PresenceTel.etat(c).totaux().points;
        for (int i = 0; i < 30; i++) Gains.caresse(c);
        Presence.Totaux t = PresenceTel.etat(c).totaux();
        assertTrue(t.points > avant);
        assertEquals(Presence.MAX_CARESSES, PresenceTel.etat(c).moi.caresses); // plafond du jour, sans punition
        assertEquals(1, t.jours);
        assertTrue(PresenceTel.etat(c).faitsDu(Presence.jourTexte(LocalDateTime.now())).ca >= 30);
    }

    @Test
    public void lePrenomSeDitSeChangeEtSEfface() {
        PresenceTel.prenom(c, "  Lou  ", false);
        assertEquals("Lou", PresenceTel.prenom(c));
        PresenceTel.prenom(c, "", false);
        assertEquals("", PresenceTel.prenom(c));
        assertFalse(PresenceTel.demanderPrenom(c)); // déjà demandé : jamais redemandé
    }
}
