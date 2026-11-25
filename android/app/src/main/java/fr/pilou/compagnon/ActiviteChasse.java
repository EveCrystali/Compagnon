package fr.pilou.compagnon;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;

import java.util.List;

/** « Chasse aux bugs » en plein écran : sons, vibrations, record, XP créditée à la fin de chaque partie. */
public final class ActiviteChasse extends Activity implements ChasseVue.Ecoute {
    private ChasseVue vue;
    private Sons sons;
    private Vibrator vibreur;
    private boolean vibrer;
    private int meilleur;

    @Override
    protected void onCreate(Bundle sauve) {
        super.onCreate(sauve);
        Journal.installer(this);
        meilleur = Prefs.meilleurChasse(this);
        vibrer = Prefs.vibrations(this);
        vibreur = getSystemService(Vibrator.class);
        sons = new Sons(Prefs.son(this));
        vue = new ChasseVue(this, this);
        setContentView(vue);
        pleinEcran();
    }

    @SuppressWarnings("deprecation")
    private void pleinEcran() {
        getWindow().setStatusBarColor(ChasseDessin.NUIT);
        getWindow().setNavigationBarColor(ChasseDessin.NUIT);
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            WindowInsetsController c = getWindow().getInsetsController();
            if (c != null) {
                c.hide(WindowInsets.Type.systemBars());
                c.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        vue.demarrer();
    }

    @Override
    protected void onPause() {
        super.onPause();
        vue.arreter();
        new Thread(() -> Gains.envoyer(getApplicationContext()), "pilou-gains").start();
    }

    @Override
    protected void onDestroy() {
        sons.liberer();
        super.onDestroy();
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        Chasse p = vue.partie;
        if (p.phase == Chasse.Phase.JEU || p.phase == Chasse.Phase.ENTRE_VAGUES) p.pause(true);
        else super.onBackPressed();
    }

    // ---- ChasseVue.Ecoute (fil principal : Choreographer)

    @Override
    public void evenements(List<Chasse.Evenement> e) {
        for (Chasse.Evenement x : e) {
            sons.jouer(x);
            if (x == Chasse.Evenement.BLESSE) vibrer(120);
            else if (x == Chasse.Evenement.EXPLOSION) vibrer(60);
            else if (x == Chasse.Evenement.FIN) finPartie();
        }
    }

    private void vibrer(long ms) {
        if (!vibrer || vibreur == null || !vibreur.hasVibrator()) return;
        vibreur.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE));
    }

    private void finPartie() {
        Chasse p = vue.partie;
        int xp = p.xp();
        if (xp > 0) Gains.jeu(this, xp);
        if (p.score > meilleur) {
            Prefs.de(this).edit().putInt("meilleurChasse", p.score).apply();
            // le record affiché pendant l'écran de fin reste l'ancien : « nouveau record » s'affiche
            meilleurApres = p.score;
        }
        new Thread(() -> Gains.envoyer(getApplicationContext()), "pilou-gains").start();
    }

    private int meilleurApres;

    @Override
    public void quitter() {
        finish();
    }

    @Override
    public int meilleur() {
        Chasse p = vue.partie;
        if (p.phase != Chasse.Phase.FIN && meilleurApres > meilleur) meilleur = meilleurApres;
        return meilleur;
    }
}
