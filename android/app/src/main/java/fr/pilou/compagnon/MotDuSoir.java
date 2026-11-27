package fr.pilou.compagnon;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

import java.time.LocalDateTime;
import java.time.ZoneId;

/**
 * Le mot du soir (docs/PRESENCE.md) : au plus UNE notification par jour, silencieuse et discrète (aucun son, aucune
 * vibration, aucun badge), entre 19 h et 20 h 30 selon le jour et l'appareil, jamais la nuit. Réglable (Réglages →
 * Pilou et moi) : chaque jour (par défaut), parfois (2 à 3 par semaine), jamais ; « Pilou me parle : jamais » coupe tout.
 * Jamais de relance : une notification ignorée s'efface d'elle-même avant la nuit, et rien ne la remplace. Même modèle
 * que Retour (alarme sans permission d'alarme exacte, reprogrammée à l'ouverture et au redémarrage).
 */
public final class MotDuSoir extends BroadcastReceiver {
    static final String CANAL = "mot", ACTION = "fr.pilou.compagnon.MOT";
    static final int NOTIF = 0x50111;

    private static PendingIntent alarme(Context c) {
        Intent i = new Intent(c, MotDuSoir.class).setAction(ACTION);
        return PendingIntent.getBroadcast(c, 43, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    /** Le prochain instant où un mot peut partir (ms Unix), ou -1 s'il n'y en a plus (réglé sur « jamais »). */
    static long prochain(Context c, LocalDateTime maintenant) {
        Presence.Etat e = PresenceTel.etat(c);
        String appareil = e.moi.id;
        for (int d = 0; d < 8; d++) {
            LocalDateTime jour = maintenant.toLocalDate().plusDays(d).atStartOfDay();
            if (!Presence.jourDeMot(jour, e.frequence, e.parle)) continue;
            String j = Presence.jourTexte(jour);
            if (d == 0 && j.equals(e.motNotifie)) continue;
            LocalDateTime quand = jour.plusMinutes(Presence.minuteDuSoir(j, appareil));
            if (quand.isBefore(maintenant)) {
                // Trop tard aujourd'hui (passé 21 h 30) : on n'envoie plus rien ce soir.
                if (d == 0 && maintenant.getHour() * 60 + maintenant.getMinute() < 21 * 60 + 30) return System.currentTimeMillis() + 60_000;
                continue;
            }
            return quand.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli();
        }
        return -1;
    }

    /** Programme (ou annule) l'alarme du prochain mot. */
    public static void programmer(Context c) {
        try {
            AlarmManager am = c.getSystemService(AlarmManager.class);
            if (am == null) return;
            long quand = prochain(c, LocalDateTime.now());
            if (quand < 0) {
                am.cancel(alarme(c));
                return;
            }
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, quand, alarme(c));
        } catch (RuntimeException ex) {
            Journal.noter("mot du soir : programmer", ex);
        }
    }

    @Override
    public void onReceive(Context c, Intent i) {
        PendingResult fin = goAsync();
        Context app = c.getApplicationContext();
        new Thread(() -> {
            try {
                envoyer(app, LocalDateTime.now());
                programmer(app);
            } catch (RuntimeException ex) {
                Journal.noter("mot du soir : alarme", ex);
            } finally {
                fin.finish();
            }
        }, "pilou-mot").start();
    }

    /** L'alarme a sonné : le mot part s'il le doit (une fois par jour, entre 19 h et 21 h 30, app fermée). */
    static boolean envoyer(Context c, LocalDateTime maintenant) {
        Presence.Etat e = PresenceTel.etat(c);
        String jour = Presence.jourTexte(maintenant);
        int minute = maintenant.getHour() * 60 + maintenant.getMinute();
        if (!Presence.jourDeMot(maintenant, e.frequence, e.parle) || jour.equals(e.motNotifie)) return false;
        if (minute < 19 * 60 || minute > 21 * 60 + 30) return false; // jamais la nuit, jamais en pleine journée
        String mot = PresenceTel.motDuJour(c);
        e = PresenceTel.etat(c);
        e.motNotifie = jour;
        PresenceTel.garder(c, e);
        // L'app est ouverte : le mot est déjà en tête de l'Accueil, pas besoin de notification.
        if (mot.isEmpty() || Retour.auPremierPlan) return false;
        notifier(c, mot);
        return true;
    }

    static void notifier(Context c, String mot) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        if (nm == null) return;
        NotificationChannel canal = new NotificationChannel(CANAL, "Le mot de Pilou (le soir)", NotificationManager.IMPORTANCE_LOW);
        canal.setDescription("Un petit mot de Pilou, le soir, au plus une fois par jour. Silencieux, sans badge, jamais de relance.");
        canal.setShowBadge(false);
        canal.enableVibration(false);
        canal.setSound(null, null);
        nm.createNotificationChannel(canal);
        Intent ouvrir = new Intent(c, Principale.class).putExtra(Principale.EXTRA_ONGLET, Principale.ACCUEIL)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        Notification.Builder b = new Notification.Builder(c, CANAL)
                .setSmallIcon(R.drawable.ic_stat_pilou)
                .setContentTitle("Pilou")
                .setContentText(mot)
                .setStyle(new Notification.BigTextStyle().bigText(mot))
                .setAutoCancel(true)
                .setOnlyAlertOnce(true)
                .setNumber(0)
                .setBadgeIconType(Notification.BADGE_ICON_NONE)
                // Ignoré, il s'efface de lui-même avant la nuit (pas de relance, pas de pile de mots).
                .setTimeoutAfter(3 * 3600_000L)
                .setContentIntent(PendingIntent.getActivity(c, 44, ouvrir, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
        try {
            Etat pc = Prefs.etat(c);
            b.setLargeIcon(Dessin.image("joie", pc.couleur, pc.accessoire, 4));
        } catch (RuntimeException sansImage) {
            // l'icône est un plus
        }
        nm.notify(NOTIF, b.build());
    }
}
