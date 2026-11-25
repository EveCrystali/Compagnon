package fr.pilou.compagnon;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Une fois par jour : la dernière release (version.json) est-elle plus récente que l'app ? Si oui, une
 * notification ; la toucher ouvre Installation, qui télécharge l'APK et lance l'installeur d'Android.
 */
public final class MiseAJour {
    public static final String DEPOT = "EveCrystali/Compagnon";
    static final String URL_VERSION = "https://github.com/" + DEPOT + "/releases/latest/download/version.json";
    static final String CANAL = "maj";
    private static final int NOTIF = 7;
    private static final long JOUR = 24 * 3600_000L;

    public static final class Publication {
        public final String version, apk;
        public final long code;

        Publication(String version, long code, String apk) {
            this.version = version;
            this.code = code;
            this.apk = apk;
        }

        public String urlApk() {
            return "https://github.com/" + DEPOT + "/releases/download/v" + version + "/" + apk;
        }
    }

    private MiseAJour() {
    }

    /** Lecture de version.json (pur, testé). */
    public static Publication lire(String json) throws org.json.JSONException {
        JSONObject r = new JSONObject(json);
        return new Publication(r.getString("version"), r.getLong("apkCode"), r.optString("apk", "Pilou.apk"));
    }

    public static long codeInstalle(Context c) {
        try {
            return c.getPackageManager().getPackageInfo(c.getPackageName(), 0).getLongVersionCode();
        } catch (PackageManager.NameNotFoundException e) {
            return Long.MAX_VALUE;
        }
    }

    static String telecharger(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(15_000);
        c.setReadTimeout(30_000);
        c.setRequestProperty("User-Agent", "pilou-android");
        c.setInstanceFollowRedirects(true);
        try (InputStream in = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] tampon = new byte[8192];
            int n;
            while ((n = in.read(tampon)) > 0) out.write(tampon, 0, n);
            return out.toString(StandardCharsets.UTF_8.name());
        } finally {
            c.disconnect();
        }
    }

    /** La release plus récente que l'app, ou null (à jour, hors ligne). À appeler hors du fil principal. */
    public static Publication chercher(Context c) {
        try {
            Publication p = lire(telecharger(URL_VERSION));
            return p.code > codeInstalle(c) ? p : null;
        } catch (Exception e) {
            return null;
        }
    }

    /** Appelé par la Veille : au plus une vérification par jour ; une notification par nouvelle version. */
    public static void peutEtre(Context c) {
        long maintenant = System.currentTimeMillis();
        if (maintenant - Prefs.de(c).getLong("majVue", 0) < JOUR) return;
        Prefs.de(c).edit().putLong("majVue", maintenant).apply();
        Publication p = chercher(c);
        if (p == null || Prefs.de(c).getString("majNotifiee", "").equals(p.version)) return;
        Prefs.de(c).edit().putString("majNotifiee", p.version).apply();
        notifier(c, p);
    }

    static void notifier(Context c, Publication p) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        nm.createNotificationChannel(new NotificationChannel(CANAL, "Mises à jour de Pilou", NotificationManager.IMPORTANCE_DEFAULT));
        Intent i = new Intent(c, Installation.class).putExtra("version", p.version).putExtra("url", p.urlApk())
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        nm.notify(NOTIF, new Notification.Builder(c, CANAL)
                .setSmallIcon(R.drawable.ic_stat_pilou)
                .setContentTitle("Pilou " + p.version + " est disponible")
                .setContentText("Toucher pour installer la mise à jour")
                .setAutoCancel(true)
                .setContentIntent(PendingIntent.getActivity(c, 7, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT))
                .build());
    }
}
