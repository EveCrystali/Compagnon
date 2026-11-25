package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Canvas;
import android.os.SystemClock;
import android.view.View;

/** Pilou animé : respire, cligne, sautille quand il se passe quelque chose. */
public final class PilouVue extends View {
    private float p;
    private String expr = "dort", couleur = "bleu", accessoire = "aucun";
    private String passager = "";
    private long finPassager;
    private long prochainClin = 2500, finClin, debutSaut = -10_000;
    private boolean anime = true;

    public PilouVue(Context c, float pixel) {
        super(c);
        p = pixel * Dessin.ECHELLE;
    }

    public void montrer(String expression, String teinte) {
        if (!expression.equals(expr) && (expression.equals("inquiet") || expression.equals("fete") || expression.equals("soulage")))
            debutSaut = SystemClock.uptimeMillis();
        expr = expression;
        couleur = teinte;
        invalidate();
    }

    public void accessoire(String a) {
        accessoire = a == null || a.isEmpty() ? "aucun" : a;
        invalidate();
    }

    /** Objets de la boutique portés (emplacement → id). Gardés pour le dessin, qui viendra les montrer. */
    public final java.util.Map<String, String> equipe = new java.util.TreeMap<>();

    public void equipe(java.util.Map<String, String> m) {
        if (m.equals(equipe)) return;
        equipe.clear();
        equipe.putAll(m);
        invalidate();
    }

    /** Humeur passagère (caresse, fête, grimace) pendant ms millisecondes. */
    public void jouer(String humeur, long ms) {
        passager = humeur;
        finPassager = SystemClock.uptimeMillis() + ms;
        if (humeur.equals("fete") || humeur.equals("caresse")) debutSaut = SystemClock.uptimeMillis();
        invalidate();
    }

    /** Nouvelle taille de pixel (même unité qu'au constructeur) : la vue se remesure. */
    public void pixel(float nouveau) {
        nouveau *= Dessin.ECHELLE;
        if (nouveau == p) return;
        p = nouveau;
        requestLayout();
        invalidate();
    }

    public void sauter() {
        debutSaut = SystemClock.uptimeMillis();
    }

    public void animer(boolean oui) {
        anime = oui;
        invalidate();
    }

    @Override
    protected void onMeasure(int largeur, int hauteur) {
        setMeasuredDimension((int) ((Dessin.W + 2) * p), (int) ((Dessin.H + 2) * p));
    }

    @Override
    protected void onDraw(Canvas cv) {
        long t = SystemClock.uptimeMillis();
        if (t > prochainClin) {
            finClin = t + 140;
            prochainClin = t + 2500 + (long) (Math.random() * 3500);
        }
        long ds = t - debutSaut;
        float saut = ds < 600 ? (float) (Math.sin(Math.PI * ds / 600.0) * 3) : 0;
        String e = t < finPassager ? passager : expr;
        Dessin.dessiner(cv, 0, 0, p, e, t, couleur, accessoire, t < finClin, saut);
        if (anime) postInvalidateDelayed(expr.equals("dort") ? 200 : 80);
    }
}
