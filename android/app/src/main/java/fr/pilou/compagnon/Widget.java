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
        portes.addAll(Boutique.bonusPortes(etat.porte));
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
        // Le mot du jour de Pilou (docs/PRESENCE.md), quand il y en a un.
        String mot = "";
        try {
            mot = PresenceTel.motDuJour(c);
        } catch (RuntimeException ignore) {
            // le mot est un plus
        }
        // Écrit dans la police pixel de Pilou, à la largeur du plus étroit des widgets posés (Pilou et marges ôtés).
        android.graphics.Bitmap image = mot.isEmpty() ? null
                : TextePixelVue.image(c, "« " + mot + " »", 1.2f, 0xFFCDD9E5, largeurTexte(c, m, ids), 2);
        if (image != null) {
            v.setImageViewBitmap(R.id.mot, image);
            v.setContentDescription(R.id.mot, "Pilou dit : " + mot);
        }
        v.setViewVisibility(R.id.mot, image == null ? android.view.View.GONE : android.view.View.VISIBLE);
        v.setOnClickPendingIntent(R.id.racine, PendingIntent.getActivity(c, 1,
                new Intent(c, Principale.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK), PendingIntent.FLAG_IMMUTABLE));
        m.updateAppWidget(ids, v);
    }

    /** Largeur (pixels de l'écran) laissée au texte dans le plus étroit des widgets ; 200 dp si Android ne la dit pas. */
    static int largeurTexte(Context c, AppWidgetManager m, int[] ids) {
        float d = c.getResources().getDisplayMetrics().density;
        int min = 0;
        for (int id : ids) {
            int w = m.getAppWidgetOptions(id).getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, 0);
            if (w > 0 && (min == 0 || w < min)) min = w;
        }
        // Pilou (56 dp), sa marge (8 dp) et le bord du widget (2 × 8 dp).
        int dp = min > 0 ? Math.max(80, min - 56 - 8 - 16) : 200;
        return (int) (dp * d);
    }
}
