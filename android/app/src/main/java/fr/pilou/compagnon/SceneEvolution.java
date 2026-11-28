package fr.pilou.compagnon;

import android.os.Build;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.widget.FrameLayout;
import android.widget.LinearLayout;

import java.util.ArrayList;
import java.util.List;

/**
 * Une scène d'évolution (docs/SCENES.md) en plein écran, par-dessus l'app : le titre en haut, le théâtre sur le décor du
 * fond du jardin (Pilou parle pendant qu'il écrit, et prend l'humeur de chaque réplique), et sous la scène la boîte où Pilou
 * écrit lettre à lettre. Un toucher sur la boîte termine l'écriture ou passe à la réplique suivante. À la question, les
 * trois options ; un toucher sur l'une dit sa réplique, puis la fin, puis « ▸ retour ». Les scènes viennent d'Evolutions.
 *
 * Le choix n'est gardé (Prefs « evolution.garde.<stade> ») que la première fois : revoir la scène depuis le carnet laisse
 * rechoisir, mais ne change pas ce que Pilou a gardé.
 */
final class SceneEvolution extends FrameLayout {
    private final Principale app;
    private final Evolutions.Scene sc;
    private final String variante;
    private final CadrePixel.Couleurs cp;
    private final float pixelRecit;
    private final int u;
    private final TheatreVue theatre;
    private final CadrePixel.Pave boite;
    private final TextePixelVue texte;
    private final LinearLayout bas;
    private final Runnable fermer;

    /** Les répliques jusqu'à la question (incluse, sans humeur) ; puis, après le choix, celles qui suivent la question. */
    private List<Evolutions.Replique> repliques;
    private int rang = -1;
    private boolean question, fin, ecrit, choisi;
    private long debutEcriture, dureeEcriture;
    /** Génération de l'écriture : un toucher ou une fermeture rend caduc ce qui était programmé. */
    private int gen;

    /** Clé des Prefs où est gardé le choix du stade (« evolution.garde.<stade> »). */
    static String cle(int stade) {
        return "evolution.garde." + stade;
    }

    /** L'id de ce que Pilou a gardé à ce stade, ou null si la scène n'a jamais été jouée jusqu'au choix : celui que
     *  le PC connaît d'abord (synchronisé, il ne change plus), sinon celui fait ici et pas encore reçu par le PC. */
    static String garde(android.content.Context c, int stade) {
        String pc = Prefs.etat(c).gardes.get(stade);
        return pc != null ? pc : Prefs.de(c).getString(cle(stade), null);
    }

    /** La variante du stade venue du PC (calin | espiegle), sinon « calin ». */
    static String varianteDe(android.content.Context c, int stade) {
        return Evolutions.variante(Prefs.etat(c).formes.get(stade));
    }

    SceneEvolution(Principale a, int stade, Runnable fermer) {
        super(a);
        app = a;
        this.fermer = fermer;
        sc = Evolutions.scenes().get(stade);
        if (sc == null) throw new IllegalArgumentException("pas de scène d'évolution pour le stade " + stade);
        variante = varianteDe(a, stade);
        Ui.Palette p = Ui.p(a);
        cp = CadrePixel.de(a);
        pixelRecit = CadrePixel.policeDp(a);
        u = Lecture.uniteEcran(a);
        setBackgroundColor(p.fond);
        setClickable(true);
        setContentDescription("Évolution de Pilou : " + sc.titre);
        Musique.suivre(this, () -> "evolution", () -> "emotion", () -> sc.decor);   // docs/SONS.md

        LinearLayout colonne = Ui.pile(a);
        addView(colonne, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        // Le titre : en haut, en police titre, sur le bandeau sombre (comme la lecture).
        TextePixelVue titre = new TextePixelVue(a, 4f / a.getResources().getDisplayMetrics().density, 0xffffffff);
        titre.titre(true);
        titre.centre(true);
        titre.maxLignes(2);
        titre.couleur(CadrePixel.SOMBRE.texte);
        titre.texte(sc.titre);
        titre.setContentDescription(sc.titre);
        LinearLayout barre = Ui.pile(a);
        barre.setGravity(Gravity.CENTER);
        barre.setBackgroundColor(0xff0a0d1a);
        barre.setPadding(3 * u, 3 * u, 3 * u, 3 * u);
        titre.maxLargeur(Math.max(1, a.getResources().getDisplayMetrics().widthPixels - 6 * u));
        barre.addView(titre, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        colonne.addView(barre, Ui.large());

        // La scène : exactement 192 × 80 pixels de décor, comme dans la lecture.
        theatre = new TheatreVue(a);
        theatre.setContentDescription("Scène : Pilou au fond du jardin");
        int k = Aventure.unite(a.getResources().getDisplayMetrics().widthPixels);
        LinearLayout.LayoutParams lt = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, k * Theatre.H);
        colonne.addView(theatre, lt);
        Etat pc = Prefs.etat(a);
        String achetee = Gains.porte(a, pc).get(Boutique.COULEUR);
        theatre.couleur(achetee != null && !achetee.isEmpty() ? Vitrine.teinte(achetee) : pc.couleur);
        try {
            theatre.lieu("evolution", sc.decor, false);
        } catch (RuntimeException x) {
            Journal.noter("évolution : théâtre", x);
        }

        // Comme la lecture des campagnes : la boîte et les choix se posent en bas, à portée du pouce ; la place qui reste
        // est entre la scène et la boîte.
        colonne.addView(new View(a), new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        // La boîte de Pilou : un cadre pixel avec ombre, le texte écrit lettre à lettre.
        boite = new CadrePixel.Pave(a, cp, u, true);
        boite.air(2 * u, 2 * u);
        boite.setClickable(true);
        boite.setContentDescription("Pilou raconte : toucher pour continuer");
        texte = new TextePixelVue(a, pixelRecit, cp.texte);
        texte.maxLargeur(a.getResources().getDisplayMetrics().widthPixels - 2 * Lecture.GOUTTIERE * u - 2 * boite.cadre().dedans() - 4 * u - boite.cadre().ombre());
        texte.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        boite.encre(texte, cp.texte);
        boite.addView(texte);
        boite.setOnClickListener(v -> toucher());
        LinearLayout.LayoutParams lb = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lb.setMargins(3 * u, 3 * u, 3 * u, 0);
        colonne.addView(boite, lb);

        // Sous la boîte : les options (à la question), puis « ▸ retour » (à la fin).
        bas = Ui.pile(a);
        bas.setPadding(3 * u, 3 * u, 3 * u, 3 * u);
        colonne.addView(bas, Ui.large());

        // Barres système : le contenu reste dans la zone visible.
        setOnApplyWindowInsetsListener((v, ins) -> {
            int haut, basse;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets b = ins.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                haut = b.top;
                basse = b.bottom;
            } else {
                haut = ins.getSystemWindowInsetTop();
                basse = ins.getSystemWindowInsetBottom();
            }
            colonne.setPadding(0, haut, 0, basse);
            return ins;
        });

        repliques = Evolutions.deroule(sc, variante, null);
        suivante();
    }

    // ---- Pour les tests

    /** La question est posée et ses options sont montrées. */
    boolean questionPosee() {
        return question && !ecrit;
    }

    boolean finie() {
        return fin;
    }

    /** Les options montrées sous la boîte (pour les tests) : les vues touchables, dans l'ordre. */
    List<View> optionsVues() {
        List<View> l = new ArrayList<>();
        for (int i = 0; i < bas.getChildCount(); i++) l.add(bas.getChildAt(i));
        return l;
    }

    String texteMontre() {
        return texte.texte();
    }

    // ---- Le déroulé

    private void toucher() {
        if (ecrit) {
            terminer();
        } else if (!question && !fin) {
            suivante();
        }
    }

    /** Dit la réplique suivante ; à la fin de la liste : la question (avant le choix) ou « ▸ retour » (après). */
    private void suivante() {
        rang++;
        if (rang >= repliques.size()) {
            if (choisi) montrerFin();
            return;
        }
        Evolutions.Replique r = repliques.get(rang);
        question = r.humeur.isEmpty();
        bas.removeAllViews();
        texte.texte(r.texte);
        int g = ++gen;
        boolean parle = !question;
        if (parle) {
            theatre.revient();
            theatre.humeur(Lecture.humeurPilou(r.humeur), true);
        }
        dureeEcriture = Evolutions.msEcriture(r.texte);
        if (ScenesAnimees.texteInstantane(app)) {
            ecrit = false;
            apresEcriture();
            return;
        }
        ecrit = true;
        debutEcriture = SystemClock.uptimeMillis();
        texte.revele(0f);
        if (parle) theatre.parle(dureeEcriture);
        Runnable tour = new Runnable() {
            @Override
            public void run() {
                if (g != gen || !ecrit) return;
                long ecoule = SystemClock.uptimeMillis() - debutEcriture;
                if (ecoule >= dureeEcriture) {
                    terminer();
                    return;
                }
                texte.revele(ecoule / (float) dureeEcriture);
                postDelayed(this, 33);
            }
        };
        post(tour);
    }

    /** L'écriture finit d'un coup (fin du temps, ou toucher). */
    private void terminer() {
        if (!ecrit) return;
        ecrit = false;
        gen++;
        texte.revele(1f);
        theatre.tait();
        apresEcriture();
    }

    private void apresEcriture() {
        texte.revele(1f);
        if (question) montrerOptions();
        else if (choisi && rang == repliques.size() - 1) montrerFin();
    }

    private void montrerOptions() {
        bas.removeAllViews();
        int i = 0;
        for (Evolutions.Option o : sc.options) {
            View b = option(o);
            LinearLayout.LayoutParams l = Ui.large();
            if (i > 0) l.topMargin = 2 * u;
            bas.addView(b, l);
            if (Vitrine.anime(app)) {
                b.setAlpha(0);
                b.setTranslationY(Ui.dp(app, 12));
                b.animate().alpha(1).translationY(0).setStartDelay(90L * i + 120).setDuration(220).start();
            }
            i++;
        }
    }

    /** Une option : même cadre pixel que les choix de la lecture, puce « ▶ » à la couleur du bord. */
    private View option(Evolutions.Option o) {
        CadrePixel.Pave r = new CadrePixel.Pave(app, cp, u, true);
        r.setOrientation(LinearLayout.HORIZONTAL);
        r.setGravity(Gravity.CENTER_VERTICAL);
        r.air(2 * u, 2 * u);
        r.setMinimumHeight(Ui.dp(app, 48) + u);
        TextePixelVue s = new TextePixelVue(app, pixelRecit, cp.bord);
        s.texte("▶");
        s.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        r.encre(s, cp.bord);
        r.addView(s);
        TextePixelVue t = new TextePixelVue(app, pixelRecit, cp.texte);
        t.texte(o.libelle);
        t.setPadding(2 * u, 0, 0, 0);
        t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        r.encre(t, cp.texte);
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        r.setContentDescription("Garder : " + o.libelle);
        r.setClickable(true);
        r.setOnClickListener(v -> choisir(o, r));
        return r;
    }

    /** Un choix : il s'illumine, les autres s'effacent ; Pilou dit sa réplique, puis la fin. */
    void choisir(Evolutions.Option o, View choisie) {
        if (choisi || !question || ecrit) return;
        choisi = true;
        for (int i = 0; i < bas.getChildCount(); i++) {
            View v = bas.getChildAt(i);
            v.setEnabled(false);
            if (v != choisie) v.animate().alpha(0.25f).setDuration(140).start();
        }
        if (choisie instanceof CadrePixel.Pave) ((CadrePixel.Pave) choisie).forcer(true);
        Ui.vibrer(app, 8);
        Sons.jouer(app, Sons.CHOIX);
        // La première fois seulement : ce que Pilou garde ne change plus ensuite.
        if (garde(app, sc.stade) == null) {
            Prefs.de(app).edit().putString(cle(sc.stade), o.id).apply();
            Gains.garde(app, sc.stade, o.id);      // il part au PC, qui le partage avec les autres appareils
        }
        List<Evolutions.Replique> toutes = Evolutions.deroule(sc, variante, o.id);
        int deja = repliques.size() - 1;   // la question n'est pas dans le déroulé complet
        repliques = new ArrayList<>(toutes.subList(Math.min(deja, toutes.size()), toutes.size()));
        rang = -1;
        question = false;
        postDelayed(this::suivante, Vitrine.anime(app) ? 170 : 0);
    }

    private void montrerFin() {
        if (fin) return;
        fin = true;
        question = false;
        bas.removeAllViews();
        CadrePixel.Pave b = new CadrePixel.Pave(app, cp, u, true);
        b.setOrientation(LinearLayout.HORIZONTAL);
        b.setGravity(Gravity.CENTER);
        b.air(2 * u, 2 * u);
        b.setMinimumHeight(Ui.dp(app, 48) + u);
        TextePixelVue t = new TextePixelVue(app, pixelRecit, cp.appuyeTexte);
        t.texte("▸ retour");
        t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        b.encre(t, cp.appuyeTexte);
        b.addView(t);
        b.setContentDescription("Retour");
        b.setClickable(true);
        b.setOnClickListener(v -> fermer.run());
        bas.addView(b, Ui.large());
    }
}
