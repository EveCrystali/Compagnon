package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.robolectric.Shadows.shadowOf;

import android.content.Context;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;

import java.util.ArrayList;
import java.util.List;

/** La page Métiers et succès (Collection → Métiers) et la carte de l'accueil qui y mène : ce qui s'y lit. */
@RunWith(RobolectricTestRunner.class)
public class MetiersPageTest {
    private static void etat(String plus) {
        Context ctx = RuntimeEnvironment.getApplication();
        long t = System.currentTimeMillis();
        String etat = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":12,\"titre\":\"x\",\"couleur\":\"bleu\",\"humeur\":\"repos\","
                + "\"calmes\":0,\"sessions\":[],\"xp\":3600," + plus + "\"po\":10}";
        Prefs.de(ctx).edit().clear().putString("code", "ABCDEFGHJKMNPQRS").putString("etat", etat).putLong("recu", t).commit();
    }

    private static void textes(View v, List<String> dans) {
        if (v.getVisibility() != View.VISIBLE) return;
        if (v instanceof TextView) dans.add(((TextView) v).getText().toString());
        if (v instanceof ViewGroup)
            for (int i = 0; i < ((ViewGroup) v).getChildCount(); i++) textes(((ViewGroup) v).getChildAt(i), dans);
    }

    private static List<String> textes(View v) {
        List<String> l = new ArrayList<>();
        textes(v, l);
        return l;
    }

    @Test
    public void pageEtCarte() {
        etat("\"metiers\":{\"musicien\":3},\"succes\":[\"melomane\",\"marathon\"],"
                + "\"heures\":{\"codeur\":57,\"musicien\":187},\"avance\":{\"dactylo\":70,\"visio-man\":30},");
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.aller(Principale.ACCUEIL, false);
        shadowOf(Looper.getMainLooper()).idle();
        List<String> accueil = textes(a.page(Principale.ACCUEIL));
        assertTrue(accueil.toString(), accueil.contains("♪ Mélomane · Confirmé  ·  Succès 2/22"));

        a.allerMetiers();
        shadowOf(Looper.getMainLooper()).idle();
        List<String> l = textes(a.page(Principale.COLLECTION));
        assertTrue(l.toString(), l.contains("2 / 10 métiers commencés"));
        assertTrue(l.contains("Mélomane · Confirmé"));
        assertTrue(l.contains("18,7 h / 40 h"));
        assertTrue(l.contains("Codeur · Novice"));
        assertTrue(l.contains("5,7 h / 6 h"));
        assertTrue(l.contains("⚒"));
        assertTrue(l.contains("♪"));
        assertTrue(l.contains("Succès 2/22"));
        assertTrue(l.contains("10 réunions en 7 jours · 3 / 10  ·  +25 xp"));
        assertTrue(l.contains("taper avec Pilou au clavier 25 fois · 7 / 25  ·  +25 xp"));
        // Trié par heures : Mélomane avant Codeur ; obtenus (✓) avant les autres.
        assertTrue(l.indexOf("Mélomane · Confirmé") < l.indexOf("Codeur · Novice"));
        assertTrue(l.indexOf("Marathon") < l.indexOf("Visio-man"));
        assertTrue(l.indexOf("Mélomane") < l.indexOf("Noctambule"));
        assertEquals(2, java.util.Collections.frequency(l, "✓"));
        c.pause().stop().destroy();
    }

    @Test
    public void ancienPcSansHeures() {
        etat("\"metiers\":{\"codeur\":2},\"succes\":[\"marathon\"],");
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.allerMetiers();
        shadowOf(Looper.getMainLooper()).idle();
        List<String> l = textes(a.page(Principale.COLLECTION));
        assertTrue(l.toString(), l.contains("Codeur · Compagnon"));
        assertTrue(l.contains("au moins 30 h"));
        assertTrue(l.contains("Succès 1/22"));
        c.pause().stop().destroy();
    }

    @Test
    public void pcMuetSurLesMetiers() {
        etat("");
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.aller(Principale.ACCUEIL, false);
        shadowOf(Looper.getMainLooper()).idle();
        for (String s : textes(a.page(Principale.ACCUEIL))) assertFalse(s, s.contains("Succès"));
        a.allerMetiers();
        shadowOf(Looper.getMainLooper()).idle();
        assertTrue(textes(a.page(Principale.COLLECTION)).contains("Succès 0/22"));
        c.pause().stop().destroy();
    }
}
