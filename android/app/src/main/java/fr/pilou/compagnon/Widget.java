package fr.pilou.compagnon;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;

import java.util.List;

/** Niveau 2 : widget d'écran d'accueil, Pilou et les sessions qui comptent. */
public final class Widget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {
        maj(c, Prefs.etat(c), System.currentTimeMillis());
    }

    static void maj(Context c, Etat etat, long maintenant) {
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        int[] ids = m.getAppWidgetIds(new ComponentName(c, Widget.class));
        if (ids.length == 0) return;
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget);
        RenduPilou.Allure a = Dessin.allure(etat.expression(maintenant), 0, etat.couleur, etat.accessoire, false, 0);
        java.util.List<String> portes = new java.util.ArrayList<>();
        for (java.util.Map.Entry<String, String> en : etat.porte.entrySet())
            if (Boutique.surPilou(en.getKey())) portes.add(en.getValue());
        a.objets = portes;
        Meteo.appliquer(a, etat.etatMeteo(maintenant), 0);
        v.setImageViewBitmap(R.id.pilou, Dessin.image(a, 3));
        Meteo mt = etat.meteo(maintenant);
        v.setTextViewText(R.id.titre, etat.nom + " · niveau " + etat.niveau + (mt == null ? "" : "  " + mt.signe + " " + mt.temperature + " °C"));
        v.setTextViewText(R.id.resume, etat.resume(maintenant));
        StringBuilder b = new StringBuilder();
        List<Etat.Ligne> lignes = etat.lignes(maintenant, 0);
        for (int i = 0; i < Math.min(4, lignes.size()); i++) {
            if (i > 0) b.append('\n');
            b.append(lignes.get(i).toString());
        }
        v.setTextViewText(R.id.lignes, b.toString());
        v.setOnClickPendingIntent(R.id.racine, PendingIntent.getActivity(c, 1,
                new Intent(c, Principale.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK), PendingIntent.FLAG_IMMUTABLE));
        m.updateAppWidget(ids, v);
    }
}
