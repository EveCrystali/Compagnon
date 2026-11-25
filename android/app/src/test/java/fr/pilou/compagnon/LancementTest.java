package fr.pilou.compagnon;

import static org.junit.Assert.assertNotNull;

import android.content.Context;
import android.content.Intent;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;

/** L'app se lance et chaque onglet s'affiche : neuve, puis avec les réglages d'une version précédente. */
@RunWith(RobolectricTestRunner.class)
public class LancementTest {
    private static void parcourir() {
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup();
        Principale a = c.get();
        assertNotNull(a);
        for (int i = 0; i < 4; i++) {
            a.page(i);
            if (i == Principale.COLLECTION) for (int k = 0; k <= PageCollection.BOUTIQUE; k++) ((PageCollection) a.page(i)).choisir(k);
            Intent onglet = new Intent(RuntimeEnvironment.getApplication(), Principale.class).putExtra(Principale.EXTRA_ONGLET, i);
            Robolectric.buildActivity(Principale.class, onglet).setup().pause().stop().destroy();
        }
        c.pause().stop().destroy();
    }

    @Test
    public void autresEcrans() {
        Robolectric.buildActivity(ActiviteChasse.class).setup().pause().stop().destroy();
        Robolectric.buildActivity(Atelier.class).setup().pause().stop().destroy();
        Robolectric.buildActivity(Installation.class).setup().pause().stop().destroy();
    }

    @Test
    public void appNeuve() {
        parcourir();
    }

    @Test
    public void apresUneVersionPrecedente() {
        Context ctx = RuntimeEnvironment.getApplication();
        long t = System.currentTimeMillis();
        String etat = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":7,\"titre\":\"x\",\"couleur\":\"bleu\",\"humeur\":\"repos\",\"calmes\":1,"
                + "\"sessions\":[{\"id\":\"a\",\"source\":\"claude\",\"libelle\":\"api\",\"etat\":\"travail\",\"depuis\":" + (t - 5000) + ",\"outil\":\"Bash\"}],"
                + "\"xp\":300,\"accessoire\":\"feuille\",\"carnet\":[\"truite\"],\"plats\":[],\"recus\":[],"
                + "\"po\":240,\"objets\":[\"echarpe\"],\"porte\":{\"cou\":\"echarpe\"},\"offres\":[\"cape\",\"monocle\",\"aura\",\"parapluie\"],"
                + "\"soins\":{\"f\":8,\"p\":5,\"m\":40,\"s\":30,\"t\":" + (t - 3_600_000) + ",\"r\":\"doux\",\"v\":0},\"formes\":{\"2\":\"espiegle\",\"x\":\"y\"},"
                + "\"promo\":\"cape\",\"serie\":2,\"quetes\":[[0,\"Pêche 3 prises\",1,3,30,0],[1,\"Cuisine 5 plats\",5,5,120,1]]}";
        Prefs.de(ctx).edit()
                .putString("code", "ABCDEFGHJKMNPQRS")
                .putString("relais", "https://ntfy.sh")
                .putString("etat", etat)
                .putLong("recu", t)
                .putFloat("taille", 1.4f)
                .putBoolean("bulle", true)
                .putInt("bulleX", 0)
                .putInt("bulleY", 900)
                .putString("plantage", "Pilou 0.9.7 · essai\njava.lang.RuntimeException: essai")
                .commit();
        parcourir();
    }
}
