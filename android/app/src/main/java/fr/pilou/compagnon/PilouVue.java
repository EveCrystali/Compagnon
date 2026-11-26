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
    private int stade = 2;
    private String tenue = "";
    private java.util.List<String> objets = java.util.Collections.emptyList();
    private long debutEvolution = -1;
    private java.util.List<String> objetsSoins = java.util.Collections.emptyList();
    private int humeurSoins = CONTENT;
    /** Humeur des soins : content, il boude, il se laisse amadouer. */
    static final int CONTENT = 0, BOUDE = 1, AMADOUE = 2;
    private String meteo = "";
    /** Durée de l'animation d'évolution (silhouette qui alterne, puis éclat). */
    public static final long DUREE_EVOLUTION = 2600;

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

    /** Stade (1 Gouttelette … 4 Astral), tenue d'activité, objets de boutique équipés. */
    public void stade(int s) {
        stade = s;
        invalidate();
    }

    public void tenue(String t) {
        tenue = t == null ? "" : t;
        invalidate();
    }

    public void objets(java.util.List<String> o) {
        objets = o == null ? java.util.Collections.<String>emptyList() : o;
        invalidate();
    }

    /** Soins : sprites en plus (variante, rayonnement, mousse) et humeur (CONTENT, BOUDE, AMADOUE). */
    public void soins(java.util.List<String> o, int humeur) {
        java.util.List<String> l = o == null ? java.util.Collections.<String>emptyList() : o;
        if (l.equals(objetsSoins) && humeur == humeurSoins) return;
        objetsSoins = l;
        humeurSoins = humeur;
        invalidate();
    }

    /** Météo du PC (Meteo.PLUIE…, "" : rien) : gouttes, Pilou mouillé s'il n'a pas de parapluie, etc. */
    public void meteo(String etat) {
        etat = etat == null ? "" : etat;
        if (etat.equals(meteo)) return;
        meteo = etat;
        invalidate();
    }

    public String meteo() {
        return meteo;
    }

    /** Joue l'évolution vers le stade donné. */
    public void evoluer(int versStade) {
        stade = versStade;
        debutEvolution = SystemClock.uptimeMillis();
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
        RenduPilou.Allure a = Dessin.allure(e, t, couleur, accessoire, t < finClin, saut);
        a.stade = stade;
        a.tenue = tenue;
        // Objets de la boutique portés (un par emplacement) ; la couleur achetée remplace celle du niveau.
        java.util.List<String> portes = new java.util.ArrayList<>(objets);
        for (java.util.Map.Entry<String, String> en : equipe.entrySet()) {
            if (en.getValue() == null || en.getValue().isEmpty()) continue;
            if (en.getKey().equals(Boutique.COULEUR)) a.couleur = Vitrine.teinte(en.getValue());
            else if (Boutique.surPilou(en.getKey())) portes.add(en.getValue());
        }
        // Ensembles portés en entier : leur effet bonus.
        portes.addAll(Boutique.bonusPortes(equipe));
        portes.addAll(objetsSoins);
        bouder(a, portes, e, t);
        a.objets = portes;
        Meteo.appliquer(a, meteo, t);
        if (debutEvolution >= 0) {
            double k = (t - debutEvolution) / (double) DUREE_EVOLUTION;
            if (k >= 1) debutEvolution = -1;
            else a.evolution = Math.max(0.001, k);
        }
        Dessin.dessiner(cv, 0, 0, p, a);
        if (anime) postInvalidateDelayed(expr.equals("dort") ? 200 : 80);
    }

    /** Il boude (comme sur le PC) : moue et sourcils au repos, nuage gris, bras croisés du Nimbus, dos tourné
     *  6 s sur 47 ; amadoué, une éclaircie, et la moue qui va et vient. */
    private void bouder(RenduPilou.Allure a, java.util.List<String> portes, String e, long t) {
        boolean repos = e.equals("repos");
        if (humeurSoins == AMADOUE) {
            portes.add("boude-eclaircie");
            a.boude = repos && t % 9000 < 6000;
        } else if (humeurSoins == BOUDE) {
            boolean dos = repos && t % 47_000 > 41_000;
            portes.add("boude-nuage");
            if (stade == 3 && !dos) portes.add("boude-bras");
            a.boude = repos;
            a.dos = dos;
        }
    }
}
