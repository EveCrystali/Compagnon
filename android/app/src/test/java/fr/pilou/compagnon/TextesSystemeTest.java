package fr.pilou.compagnon;

import static org.junit.Assert.assertTrue;
import static org.robolectric.Shadows.shadowOf;

import android.content.Context;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.TextView;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;

import java.util.ArrayList;
import java.util.List;

/**
 * Une seule écriture (docs/STYLE.md) : sur les écrans passés au guide de style, aucun texte n'est écrit dans la
 * police du système, hors les exceptions du guide (champs de saisie). Le test parcourt chaque écran et liste tout
 * TextView visible, non vide, qui n'est pas un texte en police pixel (Style.Texte, TextePixelVue n'étant pas un
 * TextView). Un nouvel écran ou une nouvelle ligne en police système le fait échouer, avec la liste.
 */
@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34, qualifiers = "w392dp-h873dp-notnight-440dpi")
public class TextesSystemeTest {

    @Test
    public void aucunTexteEnPoliceSysteme() {
        Context ctx = RuntimeEnvironment.getApplication();
        List<String> trouves = new ArrayList<>();
        // Premier lancement, pas encore appairé : le guide et la ligne de bienvenue.
        Prefs.de(ctx).edit().clear().commit();
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        attendre();
        lister("accueil (neuf)", c.get().page(Principale.ACCUEIL), trouves);
        c.get().aller(Principale.REGLAGES, false);
        attendre();
        lister("reglages (neuf)", c.get().page(Principale.REGLAGES), trouves);
        c.pause().stop().destroy();

        CapturesStyleTest.appairer(ctx);
        c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        attendre();
        lister("en-tete et barre", a.getWindow().getDecorView(), trouves);
        int[] onglets = {Principale.ACCUEIL, Principale.JOUER, Principale.BOUTIQUE, Principale.COLLECTION, Principale.REGLAGES};
        String[] noms = {"accueil", "jouer", "boutique", "collection", "reglages"};
        for (int i = 0; i < onglets.length; i++) {
            a.aller(onglets[i], false);
            attendre();
            Page p = a.page(onglets[i]);
            if (onglets[i] == Principale.COLLECTION) {
                for (int k = 0; k <= PageCollection.METIERS; k++) {
                    ((PageCollection) p).choisir(k);
                    attendre();
                    lister("collection " + k, p, trouves);
                }
            } else lister(noms[i], p, trouves);
        }
        PageBoutique b = (PageBoutique) a.page(Principale.BOUTIQUE);
        for (String rayon : new String[]{Boutique.DOS, Boutique.BULLE, Boutique.TITRE, Boutique.RAYON_ENSEMBLES}) {
            b.rayon(rayon);
            attendre();
            lister("boutique " + rayon, b, trouves);
        }
        a.montrerRangees(9, 15);
        attendre();
        lister("rangees debloquees", a.getWindow().getDecorView(), trouves);
        c.pause().stop().destroy();

        for (String t : trouves) System.out.println("POLICE-SYSTEME " + t);
        assertTrue("Textes encore en police système (docs/STYLE.md) :\n" + String.join("\n", trouves), trouves.isEmpty());
    }

    private static void attendre() {
        shadowOf(Looper.getMainLooper()).idle();
    }

    private static void lister(String ecran, View v, List<String> dans) {
        if (v.getVisibility() != View.VISIBLE) return;
        if (v instanceof TextView && !(v instanceof Style.Texte) && !(v instanceof EditText)) {
            CharSequence t = ((TextView) v).getText();
            if (t != null && t.toString().trim().length() > 0) {
                String ligne = ecran + " | " + v.getClass().getSimpleName() + " | " + t.toString().replace('\n', ' ');
                if (!dans.contains(ligne)) dans.add(ligne);
            }
        }
        if (v instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) v;
            for (int i = 0; i < g.getChildCount(); i++) lister(ecran, g.getChildAt(i), dans);
        }
    }
}
