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

    /** Rendu fin (grille 96 × 112) : demandé par l'écran ; tenu seulement si un pixel fin fait au moins 2 pixels
     *  de l'écran (sinon la vue reste au rendu 1×, comme avant). */
    private final boolean finDemande;
    private Dessin.ImageFine fine;

    public PilouVue(Context c, float pixel) {
        this(c, pixel, false);
    }

    /** fin : Pilou en rendu fin si l'écran est assez dense pour cette taille (accueil, essayage, installation). */
    public PilouVue(Context c, float pixel, boolean fin) {
        super(c);
        finDemande = fin;
        regler(pixel * Dessin.ECHELLE);
    }

    /** Taille du pixel de grille. En rendu fin, elle est arrondie pour qu'un pixel fin tombe sur un nombre entier
     *  de pixels de l'écran (dessin net, sans pixels inégaux). */
    private void regler(float pixel) {
        int n = Dessin.pixelFin(pixel);
        // Au moins 2 pixels de l'écran par pixel fin (1,75 arrondi à 2 : la vue grandit alors de 14 % au plus).
        if (finDemande && n >= 2 && pixel / 2 >= 1.75f) {
            p = 2 * n;
            if (fine == null) fine = new Dessin.ImageFine();
        } else {
            p = pixel;
            fine = null;
        }
    }

    /** Vrai si la vue dessine Pilou en rendu fin. */
    public boolean fin() {
        return fine != null;
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
        float avant = p;
        regler(nouveau * Dessin.ECHELLE);
        if (avant == p) return;
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

    /** Durée du vol d'un saut (ms) ; ressorts et réception en plus au niveau « complètes ». */
    static final int VOL = 520;
    private String niveau = Animations.COMPLETES;
    private int heure = 12;
    private long niveauLu = -10_000;

    /** Niveau d'animation (réglage ✧ et échelle du système) et heure, relus au plus une fois par seconde. */
    private String niveauVie(long t) {
        if (t - niveauLu >= 1000) {
            niveauLu = t;
            niveau = ScenesAnimees.niveau(getContext());
            heure = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        }
        return niveau;
    }

    private boolean marque;
    private final android.graphics.Paint pinceauMarque = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);

    /** Un petit « ! » orange en haut à droite : Pilou est revenu de son aventure et attend (bulle flottante). */
    public void marque(boolean oui) {
        if (oui == marque) return;
        marque = oui;
        invalidate();
    }

    public boolean marque() {
        return marque;
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
        // Vie du personnage (Vie.java) : selon le réglage ✧, le saut d'avant (aucune), l'arc seul (réduites) ou l'arc
        // avec ses ressorts, l'antenne en retard et la poussière à l'atterrissage (complètes).
        String niveau = niveauVie(t);
        float saut;
        int[] bond = null;
        if (Animations.AUCUNE.equals(niveau)) saut = ds < 600 ? (float) (Math.sin(Math.PI * ds / 600.0) * 3) : 0;
        else {
            bond = ds < Vie.dureeBond(VOL, niveau) ? Vie.bond(ds, VOL, 3000, niveau) : new int[]{0, 0, 0};
            saut = bond[0] / 1000f;
        }
        String e = t < finPassager ? passager : expr;
        RenduPilou.Allure a = Dessin.allure(e, t, couleur, accessoire, t < finClin, saut);
        if (bond != null) {
            a.etire = bond[1] / 1000.0;
            a.antenne = bond[2] / 1000.0;
            long atterri = ds - Vie.PREP - VOL;
            a.atterri = Animations.COMPLETES.equals(niveau) && atterri >= 0 && atterri < 3 * Vie.BOUFFEE_IMAGE ? atterri : -1;
        }
        a.vie = Animations.COMPLETES.equals(niveau);
        a.lumiere = Vie.lumiere(heure, meteo, niveau);
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
        if (fine != null) {
            // Rendu fin : un bitmap de 96 × 112 gardé d'une image à l'autre, posé avec la même marge d'un pixel de grille.
            fine.rendre(a);
            fine.dessiner(cv, p, p, p / 2);
        } else {
            Dessin.dessiner(cv, 0, 0, p, a);
        }
        if (marque) {
            // Pastille orange, texte sombre (contraste ≥ 4,5:1), qui bat doucement.
            float r = Math.max(p * 3.2f, getWidth() * 0.11f), cx = getWidth() - r - p * 0.5f, cy = r + p * 0.5f;
            float k = anime ? 1 + 0.08f * (float) Math.sin(t / 260.0) : 1;
            pinceauMarque.setColor(0xff1c2128);
            cv.drawCircle(cx, cy, r * k + p * 0.6f, pinceauMarque);
            pinceauMarque.setColor(0xfff69d50);
            cv.drawCircle(cx, cy, r * k, pinceauMarque);
            pinceauMarque.setColor(0xff1c2128);
            pinceauMarque.setTextAlign(android.graphics.Paint.Align.CENTER);
            pinceauMarque.setTextSize(r * 1.5f);
            pinceauMarque.setFakeBoldText(true);
            cv.drawText("!", cx, cy + r * 0.52f, pinceauMarque);
        }
        // Pendant un bond complet, une image toutes les 40 ms (les ressorts durent moins de 100 ms) ; sinon comme avant.
        boolean bondit = bond != null && Animations.COMPLETES.equals(niveau) && ds < Vie.dureeBond(VOL, niveau);
        if (anime) postInvalidateDelayed(bondit ? 40 : expr.equals("dort") ? 200 : 80);

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
