package fr.pilou.compagnon;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.TypedValue;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Télécharge l'APK de la release dans une session PackageInstaller, puis Android demande « Mettre à jour ». */
public final class Installation extends Activity {
    private final Handler h = new Handler(Looper.getMainLooper());
    private TextView texte;
    private String version, url;
    private boolean enCours;

    @Override
    protected void onCreate(Bundle sauve) {
        super.onCreate(sauve);
        float d = getResources().getDisplayMetrics().density;
        LinearLayout pile = new LinearLayout(this);
        pile.setOrientation(LinearLayout.VERTICAL);
        pile.setGravity(Gravity.CENTER);
        int m = (int) (24 * d);
        pile.setPadding(m, m, m, m);
        // Même identité que le reste de l'app : fond, texte et bouton de la palette (clair / sombre).
        Ui.Palette p = Ui.p(this);
        pile.setBackgroundColor(p.fond);
        PilouVue pilou = new PilouVue(this, 4 * d);
        pilou.montrer("concentre", "bleu");
        pilou.setContentDescription("Pilou prépare sa mise à jour");
        pile.addView(pilou);
        texte = Ui.texte(this, "", 16, p.texte, false);
        texte.setGravity(Gravity.CENTER);
        texte.setPadding(0, m, 0, m);
        pile.addView(texte);
        Button annuler = Ui.bouton(this, "Plus tard", false, v -> finish());
        pile.addView(annuler, Ui.large());
        setContentView(pile);
        version = getIntent().getStringExtra("version");
        url = getIntent().getStringExtra("url");
        if (url == null) chercher();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (url != null) demarrer();
    }

    // Ouvert sans version précise (bouton « Chercher une mise à jour ») : on demande à la release.
    private void chercher() {
        texte.setText("Je regarde s'il y a du neuf…");
        new Thread(() -> {
            MiseAJour.Publication p = MiseAJour.chercher(this);
            h.post(() -> {
                if (p == null) {
                    texte.setText("Pilou est à jour.");
                    return;
                }
                version = p.version;
                url = p.urlApk();
                demarrer();
            });
        }).start();
    }

    private void demarrer() {
        if (enCours) return;
        // Première fois : Android demande d'autoriser Pilou à installer des applis.
        if (!getPackageManager().canRequestPackageInstalls()) {
            texte.setText("Autorise Pilou à installer sa mise à jour, puis reviens ici.");
            startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName())));
            return;
        }
        enCours = true;
        texte.setText("Téléchargement de Pilou " + version + "…");
        new Thread(this::installer).start();
    }

    private void installer() {
        try {
            PackageInstaller pi = getPackageManager().getPackageInstaller();
            PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
            params.setAppPackageName(getPackageName());
            int id = pi.createSession(params);
            try (PackageInstaller.Session session = pi.openSession(id)) {
                HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
                c.setConnectTimeout(15_000);
                c.setReadTimeout(60_000);
                c.setRequestProperty("User-Agent", "pilou-android");
                long total = c.getContentLengthLong();
                try (InputStream in = c.getInputStream(); OutputStream out = session.openWrite("Pilou.apk", 0, total > 0 ? total : -1)) {
                    byte[] tampon = new byte[65536];
                    int n;
                    long lu = 0;
                    while ((n = in.read(tampon)) > 0) {
                        out.write(tampon, 0, n);
                        lu += n;
                        if (total > 0) {
                            long pc = lu * 100 / total;
                            h.post(() -> texte.setText("Téléchargement de Pilou " + version + "… " + pc + " %"));
                        }
                    }
                    session.fsync(out);
                } finally {
                    c.disconnect();
                }
                Intent retour = new Intent(this, Installe.class);
                PendingIntent pe = PendingIntent.getBroadcast(this, id, retour, PendingIntent.FLAG_MUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
                session.commit(pe.getIntentSender());
            }
            h.post(() -> texte.setText("Android va te demander de confirmer la mise à jour."));
        } catch (Exception e) {
            h.post(() -> {
                enCours = false;
                texte.setText("Mise à jour impossible pour l'instant (réseau ?). Réessaie plus tard.");
            });
        }
    }
}
