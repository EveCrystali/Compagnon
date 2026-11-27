package fr.pilou.compagnon;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

/**
 * Le retour de Pilou (campagnes) : à la fin d'une attente ou d'un repos, UNE notification locale (« Pilou est arrivé… il
 * a besoin de toi »), programmée à l'heure de fin, même app fermée et hors ligne. Pas d'alarme exacte (aucune permission
 * à demander) : AlarmManager.setAndAllowWhileIdle, que le système peut retarder de quelques minutes en veille profonde.
 * Jamais de relance : une fin d'attente donne une notification au plus. Reprogrammée après une décision, une
 * synchronisation, à l'ouverture de l'app et au redémarrage du téléphone (Demarrage).
 */
public final class Retour extends BroadcastReceiver {
    static final String CANAL = "aventure", ACTION = "fr.pilou.compagnon.RETOUR";
    static final int NOTIF = 0x50110;
    /** L'app est au premier plan : pas de notification, l'écran le montre déjà. */
    static volatile boolean auPremierPlan;

    private static PendingIntent alarme(Context c) {
        Intent i = new Intent(c, Retour.class).setAction(ACTION);
        return PendingIntent.getBroadcast(c, 41, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    /** Programme (ou annule) l'alarme de retour d'après l'état de la campagne. À appeler hors du fil d'interface si possible. */
    public static void programmer(Context c) {
        try {
            Campagnes.Etat e = CampagnesTel.etat(c);
            SharedPreferences p = Prefs.de(c);
            AlarmManager am = c.getSystemService(AlarmManager.class);
            if (am == null) return;
            if (e == null || !e.enAttente() || e.fin <= CampagnesTel.maintenant()) {
                am.cancel(alarme(c));
                return;
            }
            p.edit().putLong("retourFin", e.fin).putString("retourSorte", e.phase == Campagnes.Phase.Repos ? "repos" : "attente").apply();
            if (!Prefs.alerteAventure(c)) {
                am.cancel(alarme(c));
                return;
            }
            // L'horloge des campagnes peut être décalée en test : l'alarme suit toujours l'heure du téléphone.
            long dans = e.fin - CampagnesTel.maintenant();
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + dans, alarme(c));
        } catch (RuntimeException ex) {
            Journal.noter("retour : programmer", ex);
        }
    }

    @Override
    public void onReceive(Context c, Intent i) {
        PendingResult fin = goAsync();
        Context app = c.getApplicationContext();
        new Thread(() -> {
            try {
                verifier(app);
            } catch (RuntimeException ex) {
                Journal.noter("retour : alarme", ex);
            } finally {
                fin.finish();
            }
        }, "pilou-retour").start();
    }

    /** L'alarme a sonné : Pilou est-il bien revenu ? Une notification, une seule, s'il a besoin du joueur. */
    static void verifier(Context c) {
        SharedPreferences p = Prefs.de(c);
        long fin = p.getLong("retourFin", 0);
        if (fin == 0 || p.getLong("retourNotifie", 0) == fin) return;
        Campagnes.Etat e = CampagnesTel.etat(c);
        if (e != null && e.enAttente() && e.fin > CampagnesTel.maintenant()) {
            programmer(c); // trop tôt (horloge, autre appareil) : on reprogramme
            return;
        }
        p.edit().putLong("retourNotifie", fin).apply();
        if (e == null || !e.enCours() && e.phase != Campagnes.Phase.Fin) return; // abandonnée entre-temps
        if (!Prefs.alerteAventure(c) || auPremierPlan) return;
        notifier(c, e, "repos".equals(p.getString("retourSorte", "")));
    }

    static void notifier(Context c, Campagnes.Etat e, boolean repos) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        if (nm == null) return;
        NotificationChannel canal = new NotificationChannel(CANAL, "Retours de Pilou (aventures)", NotificationManager.IMPORTANCE_DEFAULT);
        canal.setDescription("Une notification quand Pilou revient d'une étape de son aventure. Jamais de relance.");
        nm.createNotificationChannel(canal);
        String titre, texte;
        if (repos) {
            titre = "Pilou est remis sur pied";
            texte = "Il est prêt à repartir" + (e.lieu.isEmpty() ? "" : " de " + e.lieu) + " : il a besoin de toi.";
        } else {
            titre = "Pilou est arrivé" + (e.lieu.isEmpty() ? "…" : " : " + e.lieu);
            texte = "Il a besoin de toi.";
        }
        Intent ouvrir = new Intent(c, Principale.class).putExtra(Principale.EXTRA_ONGLET, Principale.AVENTURE)
                .putExtra(Principale.EXTRA_LECTURE, true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        Notification.Builder b = new Notification.Builder(c, CANAL)
                .setSmallIcon(R.drawable.ic_stat_pilou)
                .setContentTitle(titre)
                .setContentText(texte)
                .setAutoCancel(true)
                .setOnlyAlertOnce(true)
                .setCategory(Notification.CATEGORY_REMINDER)
                .setContentIntent(PendingIntent.getActivity(c, 42, ouvrir, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
        try {
            Etat pc = Prefs.etat(c);
            b.setLargeIcon(Dessin.image(repos ? "fatigue" : "joie", pc.couleur, pc.accessoire, 4));
        } catch (RuntimeException sansImage) {
            // l'icône est un plus
        }
        nm.notify(NOTIF, b.build());
    }

    /** Le joueur a ouvert l'aventure : la notification de retour n'a plus lieu d'être. */
    static void effacer(Context c) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        if (nm != null) nm.cancel(NOTIF);
    }
}
