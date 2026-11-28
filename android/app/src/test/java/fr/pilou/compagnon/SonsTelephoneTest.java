package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import android.app.NotificationManager;
import android.content.Context;
import android.media.AudioManager;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;

/**
 * Quand un son peut sortir sur un vrai téléphone (docs/SONS.md) : un geste du joueur passe par le volume multimédia quel
 * que soit le mode de sonnerie ; un son spontané respecte silencieux et vibreur ; jamais pendant un appel.
 */
@RunWith(RobolectricTestRunner.class)
public class SonsTelephoneTest {
    private static final int[] SONNERIES = {AudioManager.RINGER_MODE_NORMAL, AudioManager.RINGER_MODE_VIBRATE, AudioManager.RINGER_MODE_SILENT};
    private Context ctx;
    private AudioManager am;

    @Before
    public void preparer() {
        ctx = RuntimeEnvironment.getApplication();
        Journal.installer(ctx);
        am = ctx.getSystemService(AudioManager.class);
        am.setMode(AudioManager.MODE_NORMAL);
        am.setStreamVolume(AudioManager.STREAM_MUSIC, 7, 0);
        Prefs.de(ctx).edit().remove("sonsNonJoues").putString("sons", "normaux").commit();
    }

    @Test
    public void unGesteSonneQuelQueSoitLeModeDeSonnerie() {
        for (int s : SONNERIES) {
            assertEquals("geste, sonnerie " + s, "", Sons.empechement(AudioManager.MODE_NORMAL, s, 7, false, false));
            am.setRingerMode(s);
            assertEquals("geste sur l'appareil, sonnerie " + s, "", Sons.empechement(ctx, false));
        }
    }

    @Test
    public void unSonSpontaneRespecteSilencieuxEtVibreur() {
        String[] attendu = {"", "téléphone en vibreur", "téléphone en silencieux"};
        for (int i = 0; i < SONNERIES.length; i++) {
            assertEquals(attendu[i], Sons.empechement(AudioManager.MODE_NORMAL, SONNERIES[i], 7, false, true));
            am.setRingerMode(SONNERIES[i]);
            assertEquals(attendu[i], Sons.empechement(ctx, true));
        }
        assertTrue(Sons.Garde.spontane(Sons.MOT) && Sons.Garde.spontane(Sons.SUCCES) && !Sons.Garde.spontane(Sons.CHOIX));
    }

    @Test
    public void jamaisPendantUnAppelNiAVolumeNul() {
        for (int s : SONNERIES)
            for (boolean sp : new boolean[]{false, true}) {
                assertEquals("téléphone en appel ou en visio", Sons.empechement(AudioManager.MODE_IN_CALL, s, 7, false, sp));
                assertEquals("téléphone en appel ou en visio", Sons.empechement(AudioManager.MODE_IN_COMMUNICATION, s, 7, false, sp));
            }
        assertEquals("volume multimédia à zéro", Sons.empechement(AudioManager.MODE_NORMAL, AudioManager.RINGER_MODE_VIBRATE, 0, false, false));
        assertEquals("« Ne pas déranger » en silence total", Sons.empechement(AudioManager.MODE_NORMAL, AudioManager.RINGER_MODE_NORMAL, 7, true, false));
        am.setMode(AudioManager.MODE_IN_COMMUNICATION);
        assertEquals("téléphone en appel ou en visio", Sons.empechement(ctx, false));
        am.setMode(AudioManager.MODE_NORMAL);
        am.setStreamVolume(AudioManager.STREAM_MUSIC, 0, 0);
        assertEquals("volume multimédia à zéro", Sons.empechement(ctx, false));
        ctx.getSystemService(NotificationManager.class).setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_NONE);
        am.setStreamVolume(AudioManager.STREAM_MUSIC, 7, 0);
        assertEquals("« Ne pas déranger » en silence total", Sons.empechement(ctx, false));
        ctx.getSystemService(NotificationManager.class).setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_ALL);
    }

    @Test
    public void unSilenceEstNoteAvecSaRaison() {
        am.setRingerMode(AudioManager.RINGER_MODE_VIBRATE);
        am.setMode(AudioManager.MODE_IN_CALL);
        assertEquals("téléphone en appel ou en visio", Sons.jouer(ctx, Sons.CARESSE, true));
        Sons.jouer(ctx, Sons.CARESSE, true);
        String trace = Journal.sons(ctx);
        assertTrue(trace, trace.endsWith("son caresse non joué : téléphone en appel ou en visio"));
        assertEquals("deux fois la même ligne n'en font qu'une", 1, trace.split("\n").length);
        am.setMode(AudioManager.MODE_NORMAL);
        Prefs.de(ctx).edit().putString("sons", "aucun").commit();
        assertEquals("réglage « Aucun »", Sons.jouer(ctx, Sons.CHOIX, false));
        assertEquals("le réglage Aucun n'est pas une panne", 1, Journal.sons(ctx).split("\n").length);
    }

    @Test
    public void lesTouchesDeVolumeReglentLeMultimedia() {
        assertEquals(AudioManager.STREAM_MUSIC, Robolectric.buildActivity(Principale.class).setup().get().getVolumeControlStream());
    }
}
