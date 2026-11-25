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

    private Journal() {
    }

    public static synchronized void installer(Context c) {
        if (pose) return;
        pose = true;
        Context app = c.getApplicationContext();
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

    public static String dernier(Context c) {
        return Prefs.de(c).getString("plantage", "");
    }

    public static void effacer(Context c) {
        Prefs.de(c).edit().remove("plantage").apply();
    }
}
