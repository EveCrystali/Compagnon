package fr.pilou.compagnon;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/**
 * Au démarrage du téléphone (ou après une mise à jour de l'app), Pilou se remet à écouter, et l'alarme du retour de
 * campagne (Retour), qu'Android oublie au redémarrage, est reprogrammée (hors du fil principal : la campagne se lit).
 */
public final class Demarrage extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        String a = i.getAction();
        if (!Intent.ACTION_BOOT_COMPLETED.equals(a) && !Intent.ACTION_MY_PACKAGE_REPLACED.equals(a)) return;
        Veille.demarrer(c);
        PendingResult fin = goAsync();
        Context app = c.getApplicationContext();
        new Thread(() -> {
            try {
                Retour.programmer(app);
                Retour.verifier(app); // revenu pendant que le téléphone était éteint : la notification part maintenant
            } finally {
                fin.finish();
            }
        }, "pilou-demarrage").start();
    }
}
