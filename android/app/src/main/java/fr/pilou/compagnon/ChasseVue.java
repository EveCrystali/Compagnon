package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.SystemClock;
import android.view.Choreographer;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import java.util.List;

/**
 * Surface de « Chasse aux bugs » : une image par battement d'écran (Choreographer), monde de 120 × 200
 * mis à l'échelle et centré. Glisser : Pilou suit le doigt ; il tire tout seul.
 */
final class ChasseVue extends SurfaceView implements SurfaceHolder.Callback, Choreographer.FrameCallback {
    interface Ecoute {
        void evenements(List<Chasse.Evenement> e);

        void quitter();

        int meilleur();
    }

    final Chasse partie = new Chasse(SystemClock.uptimeMillis());
    private final Ecoute ecoute;
    private final Paint pt = new Paint();
    private boolean surface, tourne;
    private long dernier;
    private float k = 1, ox, oy;

    ChasseVue(Context c, Ecoute e) {
        super(c);
        ecoute = e;
        pt.setAntiAlias(false);
        getHolder().addCallback(this);
        setFocusable(true);
    }

    void demarrer() {
        if (tourne || !surface) return;
        tourne = true;
        dernier = 0;
        Choreographer.getInstance().postFrameCallback(this);
    }

    void arreter() {
        tourne = false;
        Choreographer.getInstance().removeFrameCallback(this);
        partie.pause(true);
    }

    @Override
    public void surfaceCreated(SurfaceHolder h) {
        surface = true;
        demarrer();
    }

    @Override
    public void surfaceChanged(SurfaceHolder h, int format, int w, int ht) {
        k = Math.min(w / Chasse.W, ht / Chasse.H);
        ox = (w - Chasse.W * k) / 2;
        oy = (ht - Chasse.H * k) / 2;
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder h) {
        surface = false;
        arreter();
    }

    @Override
    public void doFrame(long nanos) {
        if (!tourne) return;
        float dt = dernier == 0 ? 1 / 60f : (nanos - dernier) / 1e9f;
        dernier = nanos;
        partie.avancer(dt);
        List<Chasse.Evenement> ev = partie.evenements();
        if (!ev.isEmpty()) ecoute.evenements(ev);
        dessiner();
        Choreographer.getInstance().postFrameCallback(this);
    }

    private void dessiner() {
        Canvas cv = getHolder().lockCanvas();
        if (cv == null) return;
        try {
            cv.drawColor(ChasseDessin.NUIT);
            ChasseDessin.dessiner((g, h, d, b, c) -> {
                pt.setColor(c);
                cv.drawRect(g, h, d, b, pt);
            }, partie, ox, oy, k, SystemClock.uptimeMillis(), ecoute.meilleur());
        } finally {
            getHolder().unlockCanvasAndPost(cv);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        float x = (e.getX() - ox) / k, y = (e.getY() - oy) / k;
        int a = e.getActionMasked();
        switch (partie.phase) {
            case ACCUEIL:
                if (a == MotionEvent.ACTION_UP) partie.commencer();
                return true;
            case PAUSE:
                if (a == MotionEvent.ACTION_UP) partie.pause(false);
                return true;
            case FIN:
                if (a == MotionEvent.ACTION_UP) {
                    if (ChasseDessin.dans(ChasseDessin.REJOUER, x, y)) partie.commencer();
                    else if (ChasseDessin.dans(ChasseDessin.QUITTER, x, y)) ecoute.quitter();
                }
                return true;
            default:
                if (a == MotionEvent.ACTION_DOWN && ChasseDessin.dans(ChasseDessin.PAUSE, x, y)) {
                    partie.pause(true);
                    return true;
                }
                if (a == MotionEvent.ACTION_DOWN || a == MotionEvent.ACTION_MOVE) partie.viser(x);
                return true;
        }
    }
}
