package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.PixelFormat;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.List;

/**
 * Niveau 3 : Pilou flottant par-dessus les autres applis. Glisser : le déplacer (il se range au bord) ;
 * toucher : la bulle des sessions ; appui long : il se cache 10 min.
 */
final class Bulle {
    private static final int BLEU = 0xff2f7ed8, ORANGE = 0xffc86a1c, TEXTE = 0xff1c2128, PALE = 0xff57606a;

    private final Context ctx;
    private final float d;
    private final WindowManager wm;
    private final Handler h = new Handler(Looper.getMainLooper());
    private final LinearLayout racine, panneau;
    private final PilouVue pilou;
    private final WindowManager.LayoutParams lp;
    private boolean pose, ouvert;
    private long ouvertJusque;
    private Etat etat = Etat.vide();

    Bulle(Context c) {
        ctx = c;
        wm = c.getSystemService(WindowManager.class);
        d = c.getResources().getDisplayMetrics().density;
        pilou = new PilouVue(c, 2.2f * d * Prefs.taille(c));
        panneau = new LinearLayout(c);
        panneau.setOrientation(LinearLayout.VERTICAL);
        int m = (int) (10 * d);
        panneau.setPadding(m, m / 2, m, m / 2);
        GradientDrawable fond = new GradientDrawable();
        fond.setColor(0xf2f6f8fa);
        fond.setStroke((int) (2 * d), 0xff6cb6ff);
        fond.setCornerRadius(4 * d);
        panneau.setBackground(fond);
        panneau.setVisibility(View.GONE);
        racine = new LinearLayout(c);
        racine.setOrientation(LinearLayout.VERTICAL);
        racine.setGravity(Gravity.START | Gravity.TOP);
        racine.addView(panneau);
        racine.addView(pilou);

        lp = new WindowManager.LayoutParams(WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP | Gravity.START;
        lp.x = Prefs.de(c).getInt("bulleX", 0);
        lp.y = Prefs.de(c).getInt("bulleY", (int) (c.getResources().getDisplayMetrics().heightPixels * 0.6));
        pilou.setOnTouchListener(new Glisser());
        panneau.setOnClickListener(v -> fermer());
    }

    /** Taille choisie dans l'app : appliquée tout de suite, Pilou reste à sa place. */
    void reglerTaille() {
        int[] ici = positionPilou();
        pilou.pixel(2.2f * d * Prefs.taille(ctx));
        pilou.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED);
        ancrer(ici);
    }

    void montrer() {
        if (pose) return;
        try {
            wm.addView(racine, lp);
            pose = true;
        } catch (RuntimeException refuse) {
            // permission retirée entre-temps
        }
    }

    void cacher() {
        if (!pose) return;
        h.removeCallbacksAndMessages(null);
        pilou.animer(false);
        wm.removeView(racine);
        pose = false;
    }

    void maj(Etat e, long maintenant) {
        etat = e;
        pilou.montrer(e.expression(maintenant), e.couleur);
        if (ouvert && SystemClock.uptimeMillis() > ouvertJusque && ouvertJusque > 0) fermer();
        else if (ouvert) {
            int[] ici = positionPilou();
            remplir(maintenant);
            ancrer(ici);
        }
    }

    /** Une IA attend : il saute et montre la bulle quelques secondes. */
    void alerter() {
        pilou.sauter();
        ouvrir(6000);
    }

    private void ouvrir(long ms) {
        int[] ici = positionPilou();
        ouvert = true;
        ouvertJusque = ms > 0 ? SystemClock.uptimeMillis() + ms : 0;
        remplir(System.currentTimeMillis());
        panneau.setVisibility(View.VISIBLE);
        ancrer(ici);
        if (ms > 0) h.postDelayed(() -> {
            if (ouvertJusque > 0 && SystemClock.uptimeMillis() >= ouvertJusque) fermer();
        }, ms + 50);
    }

    private void fermer() {
        int[] ici = positionPilou();
        ouvert = false;
        ouvertJusque = 0;
        panneau.setVisibility(View.GONE);
        ancrer(ici);
    }

    // Où est Pilou à l'écran (coin haut-gauche de son dessin), quelle que soit la bulle.
    private int[] positionPilou() {
        return new int[]{lp.x + pilou.getLeft(), lp.y + pilou.getTop()};
    }

    // La fenêtre se recale pour que Pilou reste exactement là où il était : la bulle s'ouvre au-dessus
    // de lui (en dessous s'il est trop haut), alignée du côté de l'écran où il se trouve.
    private void ancrer(int[] ici) {
        int largeurEcran = ctx.getResources().getDisplayMetrics().widthPixels;
        int lp0 = pilou.getMeasuredWidth();
        if (!ouvert) {
            racine.removeAllViews();
            racine.addView(panneau);
            racine.addView(pilou);
            lp.x = ici[0];
            lp.y = ici[1];
        } else {
            panneau.measure(View.MeasureSpec.makeMeasureSpec(largeurEcran, View.MeasureSpec.AT_MOST),
                    View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
            int w = Math.max(panneau.getMeasuredWidth(), lp0), hp = panneau.getMeasuredHeight();
            boolean droite = ici[0] + lp0 / 2 > largeurEcran / 2;
            boolean dessus = ici[1] - hp >= 0;
            racine.setGravity((droite ? Gravity.END : Gravity.START) | Gravity.TOP);
            racine.removeAllViews();
            if (dessus) {
                racine.addView(panneau);
                racine.addView(pilou);
            } else {
                racine.addView(pilou);
                racine.addView(panneau);
            }
            lp.x = droite ? ici[0] + lp0 - w : ici[0];
            lp.y = dessus ? ici[1] - hp : ici[1];
        }
        if (pose) wm.updateViewLayout(racine, lp);
    }

    private void remplir(long maintenant) {
        panneau.removeAllViews();
        panneau.addView(texte(etat.nom + " · niv " + etat.niveau + "   " + etat.resume(maintenant), PALE, true));
        List<Etat.Ligne> lignes = etat.lignes(maintenant, (int) (maintenant / 300));
        for (int i = 0; i < Math.min(6, lignes.size()); i++) {
            Etat.Ligne l = lignes.get(i);
            int couleur = l.ton == Etat.Ton.ATTENTE ? ORANGE : l.ton == Etat.Ton.TRAVAIL || l.nouveau ? BLEU : TEXTE;
            panneau.addView(texte(l.signe + "  " + l.libelle + "  ·  " + l.texte, couleur, false));
        }
    }

    private TextView texte(String s, int couleur, boolean discret) {
        TextView t = new TextView(ctx);
        t.setText(s);
        t.setTextColor(couleur);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, discret ? 11 : 12);
        if (discret) t.setTypeface(Typeface.DEFAULT, Typeface.ITALIC);
        t.setSingleLine(true);
        t.setMaxWidth((int) (280 * d));
        t.setEllipsize(android.text.TextUtils.TruncateAt.END);
        return t;
    }

    private final class Glisser implements View.OnTouchListener {
        private float dx, dy, x0, y0;
        private boolean bouge;
        private final Runnable longAppui = () -> {
            cacher();
            h.postDelayed(Bulle.this::montrer, 10 * 60_000L);
            pilou.animer(true);
        };

        @Override
        public boolean onTouch(View v, MotionEvent e) {
            switch (e.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    x0 = e.getRawX();
                    y0 = e.getRawY();
                    dx = lp.x - x0;
                    dy = lp.y - y0;
                    bouge = false;
                    h.postDelayed(longAppui, 700);
                    return true;
                case MotionEvent.ACTION_MOVE:
                    if (!bouge && Math.hypot(e.getRawX() - x0, e.getRawY() - y0) > 12) {
                        bouge = true;
                        h.removeCallbacks(longAppui);
                        if (ouvert) {
                            fermer();
                            dx = lp.x - e.getRawX();
                            dy = lp.y - e.getRawY();
                        }
                    }
                    if (bouge) {
                        lp.x = (int) (e.getRawX() + dx);
                        lp.y = (int) (e.getRawY() + dy);
                        wm.updateViewLayout(racine, lp);
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    h.removeCallbacks(longAppui);
                    if (bouge) ranger();
                    else if (ouvert) fermer();
                    else ouvrir(0);
                    return true;
                default:
                    return false;
            }
        }
    }

    // Il se range contre le bord le plus proche.
    private void ranger() {
        int largeur = ctx.getResources().getDisplayMetrics().widthPixels;
        lp.x = lp.x + racine.getWidth() / 2 < largeur / 2 ? 0 : largeur - racine.getWidth();
        lp.y = Math.max(0, lp.y);
        wm.updateViewLayout(racine, lp);
        Prefs.de(ctx).edit().putInt("bulleX", lp.x).putInt("bulleY", lp.y).apply();
    }
}
