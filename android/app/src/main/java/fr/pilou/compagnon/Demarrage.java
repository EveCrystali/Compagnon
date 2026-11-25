package fr.pilou.compagnon;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Au démarrage du téléphone (ou après une mise à jour de l'app), Pilou se remet à écouter. */
public final class Demarrage extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        String a = i.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(a) || Intent.ACTION_MY_PACKAGE_REPLACED.equals(a)) Veille.demarrer(c);
    }
}
