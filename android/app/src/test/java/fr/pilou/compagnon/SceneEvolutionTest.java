package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.robolectric.Shadows.shadowOf;

import android.content.Context;
import android.os.Looper;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

import java.util.ArrayList;
import java.util.List;

/** La vue d'une scène d'évolution : la question, le choix gardé la première fois seulement, la fin et le retour. */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class SceneEvolutionTest {
    private static void attendre() {
        shadowOf(Looper.getMainLooper()).idle();
    }

    private static List<View> toutes(View v) {
        List<View> l = new ArrayList<>();
        l.add(v);
        if (v instanceof android.view.ViewGroup)
            for (int i = 0; i < ((android.view.ViewGroup) v).getChildCount(); i++) l.addAll(toutes(((android.view.ViewGroup) v).getChildAt(i)));
        return l;
    }

    private static void toucherBoite(SceneEvolution ev) {
        for (View w : toutes(ev)) {
            CharSequence d = w.getContentDescription();
            if (d != null && d.toString().startsWith("Pilou raconte")) w.performClick();
        }
        attendre();
    }

    private static void jusquaLaQuestion(SceneEvolution ev) {
        for (int i = 0; i < 40 && !ev.questionPosee(); i++) toucherBoite(ev);
        assertTrue(ev.questionPosee());
    }

    private Principale ouvrir(Context ctx, int stade, ActivityController<Principale>[] ac) {
        android.provider.Settings.Global.putFloat(ctx.getContentResolver(), android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 0f);
        ac[0] = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac[0].get();
        a.ouvrirEvolution(stade);
        attendre();
        assertNotNull(a.evolution());
        return a;
    }

    @Test
    @SuppressWarnings("unchecked")
    public void leChoixNEstGardeQueLaPremiereFoisEtLaFinFermeLaScene() {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        ActivityController<Principale>[] ac = new ActivityController[1];
        Principale a = ouvrir(ctx, 2, ac);
        assertNull(SceneEvolution.garde(ctx, 2));
        SceneEvolution ev = a.evolution();
        jusquaLaQuestion(ev);
        List<View> options = ev.optionsVues();
        assertEquals(3, options.size());
        options.get(1).performClick();   // « rouler »
        attendre();
        assertEquals("rouler", SceneEvolution.garde(ctx, 2));
        for (int i = 0; i < 40 && !ev.finie(); i++) toucherBoite(ev);
        assertTrue(ev.finie());
        assertEquals(1, ev.optionsVues().size());   // « ▸ retour »
        ev.optionsVues().get(0).performClick();
        attendre();
        assertNull(a.evolution());

        // Revue depuis le carnet : on peut rechoisir, mais ce que Pilou a gardé ne change pas.
        a.ouvrirEvolution(2);
        attendre();
        ev = a.evolution();
        jusquaLaQuestion(ev);
        ev.optionsVues().get(0).performClick();   // « tache »
        attendre();
        assertEquals("rouler", SceneEvolution.garde(ctx, 2));
        // Un autre stade garde le sien.
        ac[0].pause().stop().destroy();
    }

    @Test
    @SuppressWarnings("unchecked")
    public void laVarianteVientDuPcSinonCalin() {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        assertEquals("calin", SceneEvolution.varianteDe(ctx, 2));
        long t = System.currentTimeMillis();
        String etat = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":12,\"titre\":\"x\",\"couleur\":\"bleu\",\"humeur\":\"repos\","
                + "\"calmes\":0,\"sessions\":[],\"xp\":3900,\"accessoire\":\"\",\"carnet\":[],\"plats\":[],\"recus\":[],\"po\":0,"
                + "\"objets\":[],\"porte\":{},\"stade\":2,\"formes\":{\"2\":\"espiegle\"}}";
        Prefs.de(ctx).edit().putString("etat", etat).putLong("recu", t).commit();
        assertEquals("espiegle", SceneEvolution.varianteDe(ctx, 2));
        assertEquals("calin", SceneEvolution.varianteDe(ctx, 3));
    }
}
