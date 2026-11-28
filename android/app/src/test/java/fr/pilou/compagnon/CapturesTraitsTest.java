package fr.pilou.compagnon;

import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

import java.io.File;
import java.io.FileOutputStream;
import java.time.LocalDateTime;

/**
 * Captures des traits de personnalité (docs/TRAITS.md) dans la carte « Pilou et moi » de l'Accueil, au format d'un vrai
 * téléphone en portrait (1078 × 2400, densité 2,75), en thème clair et sombre : la carte repliée (les trois dominants),
 * dépliée (tous les traits, découverts et « ? »), et un Pilou qui n'a encore aucun trait. Données de démonstration,
 * rien de personnel. Images dans app/build/captures/ (artefact CI « captures-ui »), préfixe « traits- ».
 * Ne fait jamais échouer le build : sans rendu graphique natif, les captures sont simplement sautées.
 */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class CapturesTraitsTest {
    private static final String[][] FORMATS = {
            {"clair", "w392dp-h873dp-notnight-440dpi"},
            {"sombre", "w392dp-h873dp-night-440dpi"},
    };

    private File dossier;

    @Test
    public void carteDesTraits() {
        try {
            dossier = new File("build/captures");
            dossier.mkdirs();
            for (String[] f : FORMATS) {
                RuntimeEnvironment.setQualifiers(f[1]);
                Context ctx = RuntimeEnvironment.getApplication();
                Prefs.de(ctx).edit().clear().commit();
                essayer(f[0] + "-aucun", () -> prendre(ctx, f[0] + "-aucun", false, false));
                essayer(f[0] + "-replie", () -> prendre(ctx, f[0] + "-replie", true, false));
                essayer(f[0] + "-deplie", () -> prendre(ctx, f[0] + "-deplie", true, true));
            }
        } catch (Throwable t) {
            System.out.println("CAPTURES-SAUTEES traits " + t);
        }
    }

    private void essayer(String nom, Runnable r) {
        try {
            r.run();
        } catch (Throwable t) {
            System.out.println("CAPTURE-ERREUR traits-" + nom + " " + t);
        }
    }

    /** Deux mois de vie commune : des soirées tardives, des caresses, de la cuisine, de la pêche le week-end, des lectures. */
    static Presence.Etat demo(Context ctx, boolean vecu) {
        Presence.Etat e = new Presence.Etat();
        e.moi.id = CampagnesTel.appareil(ctx);
        e.moi.sorte = "tel";
        LocalDateTime now = LocalDateTime.now();
        int auj = Presence.jour(now);
        for (int d = 60; d >= 0; d--) e.marquer(auj - d);
        e.moi.caresses = 260;
        e.moi.minutes = 4200;
        e.moi.soins = 90;
        e.moi.jeux = 110;
        if (!vecu) return e;
        for (int d = 60; d >= 1; d--) {
            int j = auj - d;
            Presence.FaitsDuJour f = e.aujourdhui(Presence.jourTexte(j));
            f.mn = 90;
            if (d % 2 == 0) f.ta = 23 * 60 + 20;
            if (d % 3 == 0) f.ca = 6;
            if (d % 4 == 0) f.cu = 1;
            if (Traits.jourDeSemaine(j) >= 6) f.pc = 1;
            if (d % 5 == 0) {
                f.ac = "lecture";
                f.am = 45;
            }
            if (d % 7 == 0) f.ex = "Forêt des onglets";
            if (d == 11 || d == 23 || d == 37) {
                f.px = "une perle de lune";
                f.pq = 3;
                f.pc = 1;
            }
        }
        Traits.decouvrir(e);
        e.moi.traitsDits = e.moi.traits;
        return e;
    }

    private void prendre(Context ctx, String nom, boolean vecu, boolean deplie) {
        Prefs.de(ctx).edit().putString("presence", demo(ctx, vecu).texte()).putBoolean("traitsOuverts", deplie).commit();
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.aller(Principale.ACCUEIL, false);
        shadowOf(Looper.getMainLooper()).idle();
        Page page = a.page(Principale.ACCUEIL);
        int[] t = mesurer(a);
        View carte = trouver(page, PresenceVue.class);
        Bitmap b = Bitmap.createBitmap(t[0], t[1], Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        // La carte en haut de l'image : le contenu de la page, remonté jusqu'à elle, à la largeur exacte du téléphone
        // (sans l'en-tête ni la barre du bas, qui ne sont pas le sujet ; le défilement réel ne prend pas hors écran).
        int haut = 0;
        for (View v = carte; v != null && v != page.corps && v.getParent() instanceof View; v = (View) v.getParent()) haut += v.getTop();
        haut = Math.max(0, haut - Ui.dp(a, 12));
        cv.drawColor(Ui.p(a).fond);
        cv.translate(0, -haut);
        page.corps.draw(cv);
        System.out.println("CAPTURE-TRAITS " + nom + " carte=" + (carte != null) + " haut=" + haut + " contenu=" + page.corps.getHeight());
        ecrire(b, nom);
        c.pause().stop().destroy();
    }

    private static View trouver(View v, Class<?> sorte) {
        if (sorte.isInstance(v)) return v;
        if (!(v instanceof ViewGroup)) return null;
        ViewGroup g = (ViewGroup) v;
        for (int k = 0; k < g.getChildCount(); k++) {
            View x = trouver(g.getChildAt(k), sorte);
            if (x != null) return x;
        }
        return null;
    }

    private static int[] mesurer(Activity a) {
        View racine = a.getWindow().getDecorView();
        android.util.DisplayMetrics m = a.getResources().getDisplayMetrics();
        int w = m.widthPixels, h = m.heightPixels;
        racine.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(h, View.MeasureSpec.EXACTLY));
        racine.layout(0, 0, w, h);
        return new int[]{w, h};
    }

    private void ecrire(Bitmap b, String nom) {
        int[] t = {b.getWidth(), b.getHeight()};
        File f = new File(dossier, "traits-" + nom + ".png");
        try (FileOutputStream o = new FileOutputStream(f)) {
            b.compress(Bitmap.CompressFormat.PNG, 100, o);
            System.out.println("CAPTURE-TRAITS " + f.getName() + " " + t[0] + "x" + t[1]);
        } catch (Exception e) {
            System.out.println("CAPTURE-ERREUR traits-" + nom + " " + e);
        }
    }
}
