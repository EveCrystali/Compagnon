package fr.pilou.compagnon;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.widget.Toast;

/** Réponse de l'installeur d'Android : il faut la confirmation de la personne, ou c'est fait, ou c'est raté. */
public final class Installe extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        int statut = i.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (statut == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirmer = android.os.Build.VERSION.SDK_INT >= 33
                    ? i.getParcelableExtra(Intent.EXTRA_INTENT, Intent.class)
                    : ancienExtra(i);
            if (confirmer != null) c.startActivity(confirmer.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        } else if (statut != PackageInstaller.STATUS_SUCCESS) {
            String m = i.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
            Toast.makeText(c, "Mise à jour de Pilou refusée" + (m == null ? "" : " : " + m), Toast.LENGTH_LONG).show();
        }
    }

    @SuppressWarnings("deprecation")
    private static Intent ancienExtra(Intent i) {
        return i.getParcelableExtra(Intent.EXTRA_INTENT);
    }
}
