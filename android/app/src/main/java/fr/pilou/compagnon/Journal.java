package fr.pilou.compagnon;

import android.content.Context;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Garde la trace du dernier plantage (affichée dans l'app, à copier pour un rapport de bug). */
public final class Journal {
    private static boolean pose;
    private static Context appli;

    private Journal() {
    }

    public static synchronized void installer(Context c) {
        Context app = c.getApplicationContext();
        appli = app;
        if (pose) return;
        pose = true;
        Thread.UncaughtExceptionHandler avant = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((fil, e) -> {
            try {
                StringWriter sw = new StringWriter();
                e.printStackTrace(new PrintWriter(sw));
                String quand = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.ROOT).format(new Date());
                String version;
                try {
                    version = app.getPackageManager().getPackageInfo(app.getPackageName(), 0).versionName;
                } catch (Exception ignore) {
                    version = "?";
                }
                String texte = "Pilou " + version + " · " + quand + " · fil " + fil.getName() + "\n" + sw;
                Prefs.de(app).edit().putString("plantage", texte.length() > 6000 ? texte.substring(0, 6000) : texte).commit();
            } catch (Throwable ignore) {
                // rien : le plantage d'origine passe quand même
            }
            if (avant != null) avant.uncaughtException(fil, e);
        });
    }

    /** Une erreur rattrapée (l'app continue) : gardée pour le diagnostic, sans rien montrer au joueur. */
    public static void noter(String quoi, Throwable e) {
        Context app = appli;
        if (app == null) return;
        try {
            String quand = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.ROOT).format(new Date());
            StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            String texte = quand + " · " + quoi + " · " + sw;
            Prefs.de(app).edit().putString("erreur", texte.length() > 3000 ? texte.substring(0, 3000) : texte).apply();
        } catch (Throwable ignore) {
            // le journal ne doit jamais faire tomber l'app
        }
    }

    /**
     * Un son qui n'a pas pu partir : « son X non joué : raison », gardé (cinq lignes au plus) pour le diagnostic.
     * Rien de personnel : un nom de son et une raison technique. Deux fois la même ligne de suite n'en font qu'une.
     */
    public static synchronized void son(String id, String raison) {
        Context app = appli;
        if (app == null) return;
        try {
            String ligne = "son " + id + " non joué : " + raison;
            String avant = Prefs.de(app).getString("sonsNonJoues", "");
            String[] l = avant.isEmpty() ? new String[0] : avant.split("\n");
            if (l.length > 0 && l[0].endsWith(" · " + ligne)) return;
            StringBuilder b = new StringBuilder(new SimpleDateFormat("HH:mm:ss", Locale.ROOT).format(new Date()) + " · " + ligne);
            for (int i = 0; i < Math.min(4, l.length); i++) b.append('\n').append(l[i]);
            Prefs.de(app).edit().putString("sonsNonJoues", b.toString()).apply();
        } catch (Throwable ignore) {
            // le journal ne doit jamais faire tomber l'app
        }
    }

    /** Les derniers sons non joués, le plus récent d'abord ("" : aucun). */
    public static String sons(Context c) {
        return Prefs.de(c).getString("sonsNonJoues", "");
    }

    /** La dernière erreur rattrapée ("" : aucune). */
    public static String erreur(Context c) {
        return Prefs.de(c).getString("erreur", "");
    }

    public static String dernier(Context c) {
        return Prefs.de(c).getString("plantage", "");
    }

    public static void effacer(Context c) {
        Prefs.de(c).edit().remove("plantage").apply();
    }
}
