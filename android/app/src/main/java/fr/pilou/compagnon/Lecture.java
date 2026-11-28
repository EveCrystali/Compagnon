package fr.pilou.compagnon;

import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

/**
 * La lecture d'une campagne, en conversation : la scène (décor, Pilou en dessin fin avec l'humeur de son message, chapitre
 * et lieu), le fil des messages (Pilou écrit « … » puis son message apparaît ; un toucher accélère), et en bas ce que le
 * joueur peut faire selon la phase : choisir, jouer une épreuve, dire « vas-y », attendre (compte à rebours), se reposer.
 * À la fin : l'issue, les récompenses, le souvenir, les fins restantes « ? ? ? ».
 */
final class Lecture extends FrameLayout {
    private final Principale app;
    private final PageAventure page;
    private final Ui.Palette p;
    private final float d;

    private final FrameLayout tete;
    private final Aventure.Scene scene;
    private final PilouVue pilou;
    /** La scène vivante (docs/SCENES.md) : décor entier, mini-Pilou, acteurs, touchers. Le décor fixe et PilouVue ne montrent
     *  que le repli, pour un lieu sans dessin fin. */
    private final TheatreVue theatre;
    private static final int BANDEAU_DP = 48;
    private String lieuTheatre = "";
    /** Pilou est parti en route (attente, repos) : la scène montre le lieu sans lui jusqu'à son retour. */
    private boolean enRoute;
    private final TextePixelVue numero, chapitre, lieu;
    private final View jauge, jaugeVide;
    private final Defil defil;
    private final Fil fil;
    private final LinearLayout dock;
    /** Les couleurs du cadre pixel selon le thème ; celles du bandeau (toujours sombre : son fond l'est). */
    private final CadrePixel.Couleurs cp, cpBandeau = CadrePixel.SOMBRE;
    private final float pixelRecit;
    /** u : le pixel de la scène en pixels d'écran, calculé dès la construction (les cadres en ont besoin avant la première mesure). */
    private final int u;
    private final FrameLayout couche;

    private Campagnes.Campagne campagne;
    private Campagnes.Etat etat;
    private final List<String> montres = new ArrayList<>();
    private final ArrayDeque<Campagnes.Message> aEcrire = new ArrayDeque<>();
    private View points;
    private boolean ecrit, vite;
    /** Génération de l'écriture : un « accélérer » ou une réouverture rend caducs les messages programmés. */
    private int gen;
    private String dockCle = "", chapitreVu = "", lieuVu = "", humeur = "repos";
    private long dernierT;
    private boolean repriseVue;
    private TextView compte, retourVers, refus;
    private Ui.Barre barreAttente;
    private boolean finMontree;
    private final int largeurBulle;
    // Animations (ScenesAnimees.java) : le personnage du message, l'écriture en cours, le fond qui respire.
    private final ScenesAnimees.Portrait perso;
    private final ScenesAnimees.Fond fond;
    private ScenesAnimees.Ecriture enCours;

    Lecture(Principale a, PageAventure page) {
        super(a);
        this.app = a;
        this.page = page;
        p = Ui.p(a);
        d = a.getResources().getDisplayMetrics().density;
        largeurBulle = Math.round(a.getResources().getDisplayMetrics().widthPixels * 0.82f);
        u = uniteEcran(a);
        cp =CadrePixel.de(a);
        pixelRecit = CadrePixel.policeDp(a);
        setBackgroundColor(p.fond);
        setClickable(true);

        fond = new ScenesAnimees.Fond(a);
        fond.base(p.fond);
        addView(fond, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        LinearLayout colonne = Ui.pile(a);
        addView(colonne, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        // ---- La scène : décor, Pilou, chapitre, lieu, avancement.
        tete = new FrameLayout(a);
        tete.setClipChildren(true);
        scene = new Aventure.Scene(a);
        scene.plein(true);
        tete.addView(scene, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        pilou = new PilouVue(a, Aventure.pixelUnite(1), true);
        pilou.setContentDescription("Pilou");
        LayoutParams lp = new LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM | Gravity.START);
        lp.leftMargin = Ui.dp(a, 10);
        lp.bottomMargin = Ui.dp(a, 2);
        tete.addView(pilou, lp);
        pilou.setOnClickListener(v -> { pilou.jouer("caresse", 1600); Sons.jouer(v.getContext(), Sons.CARESSE); });
        // Par-dessus le repli : la scène du théâtre, sur toute la largeur. Un toucher y fait réagir la scène (jamais accélérer le texte).
        theatre = new TheatreVue(a);
        theatre.setVisibility(View.GONE);
        theatre.setContentDescription("Scène : Pilou dans le lieu de l'aventure");
        tete.addView(theatre, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        tete.setBackgroundColor(0xff0a0d1a);

        // Le bandeau au-dessus de la scène : ‹ à gauche, chapitre et titre au milieu, ⋯ à droite. Rien de tout cela
        // ne se pose sur le décor (il porte seulement le petit cartouche du lieu).
        LinearLayout barreHaut = Ui.rangee(a);
        barreHaut.setGravity(Gravity.CENTER_VERTICAL);
        barreHaut.setBackgroundColor(0xff0a0d1a);
        TextePixelVue fleche = pixelFixe("◀", 4, false);
        View retour = bouton(fleche, cp.texte, "Retour aux aventures");
        retour.setOnClickListener(v -> page.fermerLecture());
        barreHaut.addView(retour);
        LinearLayout titres = Ui.pile(a);
        titres.setGravity(Gravity.CENTER);
        // Texte clair sur le fond sombre du bandeau, quel que soit le thème. Numéro en police titre (3 pixels d'écran par
        // pixel de police), titre du chapitre en police texte (4), une seule ligne chacun.
        numero = pixelFixe("", 3, true);
        numero.couleur(cpBandeau.pale);
        numero.centre(true);
        numero.maxLignes(1);
        titres.addView(numero, Ui.large());
        chapitre = pixelFixe("", 4, false);
        chapitre.couleur(cpBandeau.texte);
        chapitre.centre(true);
        chapitre.maxLignes(1);
        titres.addView(chapitre, Ui.large());
        barreHaut.addView(titres, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        View menu = bouton(new CadrePixel.TroisPoints(a, cp.texte, u), cp.texte, "Plus : carnet, mettre de côté");
        menu.setOnClickListener(v -> menu());
        barreHaut.addView(menu);
        colonne.addView(barreHaut, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(a, BANDEAU_DP)));

        // Le personnage que le message fait parler ou décrit : au bord droit de la scène, au-dessus du lieu.
        perso = new ScenesAnimees.Portrait(a);
        perso.setVisibility(View.GONE);
        LayoutParams lpp = new LayoutParams(64, 64, Gravity.BOTTOM | Gravity.END);
        lpp.rightMargin = Ui.dp(a, 14);
        lpp.bottomMargin = Ui.dp(a, 40);
        tete.addView(perso, lpp);
        // Sur un petit écran, la scène rapetisse et le portrait remonte jusqu'à la barre : boutons et titre restent devant.
        barreHaut.bringToFront();

        // Le lieu : un petit cadre pixel sans ombre, texte en police pixel (4 pixels d'écran par pixel de police).
        CadrePixel.Pave puceLieu = new CadrePixel.Pave(a, cp, u, false);
        puceLieu.air(u, u);
        lieu = pixelFixe("", 4, false);
        lieu.maxLignes(1);
        lieu.maxLargeur(Ui.dp(a, 190) - 4 * u - 2 * u);
        puceLieu.encre(lieu, cp.texte);
        puceLieu.addView(lieu);
        LayoutParams ll = new LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM | Gravity.END);
        ll.rightMargin = 3 * u;
        ll.bottomMargin = 3 * u;
        tete.addView(puceLieu, ll);

        // Avancement dans la campagne (chapitres) : un trait fin au pied de la scène.
        LinearLayout avance = Ui.rangee(a);
        jauge = new View(a);
        jaugeVide = new View(a);
        jaugeVide.setBackgroundColor(0x55000000);
        avance.addView(jauge, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 0));
        avance.addView(jaugeVide, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 1));
        tete.addView(avance, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(a, 4), Gravity.BOTTOM));
        colonne.addView(tete, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(a, 184)));

        // ---- Le fil.
        // Pas de fondu : le défilement se cale sur une bulle entière (Defil), donc aucune ligne n'est tranchée au repos
        // par le bord de la scène.
        fil = new Fil(a);
        fil.setOrientation(LinearLayout.VERTICAL);
        fil.setPadding(3 * u, 2 * u, 3 * u, 4 * u);
        defil = new Defil(a, fil);
        defil.setVerticalScrollBarEnabled(false);
        defil.setClipToPadding(false);
        defil.addView(fil);
        // Un toucher sur le fil : Pilou écrit plus vite (le reste du message arrive tout de suite).
        fil.setOnClickListener(v -> accelerer());
        colonne.addView(defil, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        // ---- Ce que le joueur peut faire.
        dock = Ui.pile(a);
        dock.setPadding(3 * u, 3 * u, 3 * u, 3 * u);
        dock.setVisibility(View.GONE);
        // Quatre options de deux lignes (ou une grande police) ne tiennent pas toujours sous la scène d'un petit
        // téléphone : le bas défile alors, borné pour que le fil reste lisible, au lieu de cacher les dernières options.
        DockDefilant cadreDock = new DockDefilant(a, tete);
        // Le pied : un grand cadre pixel sans ombre (ni coins arrondis, ni élévation).
        cadreDock.setBackground(new CadrePixel(cp, u, false));
        cadreDock.setPadding(2 * u, 2 * u, 2 * u, 2 * u);
        cadreDock.addView(dock, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        colonne.addView(cadreDock, Ui.large());

        couche = new FrameLayout(a);
        couche.setVisibility(View.GONE);
        addView(couche, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    /** Le bas de l'écran (options, départ, attente…) : jamais plus de 65 % de ce que la scène laisse ; au-delà, il défile. */
    static final class DockDefilant extends ScrollView {
        private final View scene;

        DockDefilant(android.content.Context c, View scene) {
            super(c);
            this.scene = scene;
            setClipToPadding(false);
            setVerticalFadingEdgeEnabled(true);
            setFadingEdgeLength(Ui.dp(c, 28));
            setOverScrollMode(OVER_SCROLL_IF_CONTENT_SCROLLS);
        }

        @Override
        protected void onMeasure(int largeur, int hauteur) {
            // La colonne mesure le bas avant de partager le reste au fil : la hauteur proposée est celle de toute la
            // colonne, scène comprise. On retire la scène, et on garde au fil au moins un bon tiers.
            if (MeasureSpec.getMode(hauteur) != MeasureSpec.UNSPECIFIED) {
                ViewGroup.LayoutParams lp = scene.getLayoutParams();
                int dispo = MeasureSpec.getSize(hauteur) - (lp != null && lp.height > 0 ? lp.height : 0) - Ui.dp(getContext(), BANDEAU_DP);
                hauteur = MeasureSpec.makeMeasureSpec(Math.max(Ui.dp(getContext(), 120), dispo * 65 / 100), MeasureSpec.AT_MOST);
            }
            super.onMeasure(largeur, hauteur);
        }
    }

    // UNE seule unité de pixel pour tout l'écran : k = le plus grand entier qui tient dans la largeur (au moins 1 ; réduit
    // seulement si la scène dépasserait 42 % de la hauteur, en paysage). La scène fait exactement 192k × 80k ; le portrait
    // (64 × 64 fin) 64k × 64k ; le mini-Pilou de repli k pixels d'écran par pixel fin. On ajuste la taille des vues, jamais
    // l'échelle d'une couche.
    private int unite = 1;

    /** Pour les tests : l'unité de pixel de l'écran. */
    int unite() {
        return unite;
    }

    ScenesAnimees.Portrait portrait() {
        return perso;
    }

    TheatreVue theatre() {
        return theatre;
    }

    PilouVue pilouRepli() {
        return pilou;
    }

    @Override
    protected void onMeasure(int largeur, int hauteur) {
        if (MeasureSpec.getMode(hauteur) != MeasureSpec.UNSPECIFIED) {
            int k = Aventure.unite(MeasureSpec.getSize(largeur));
            int kMax = MeasureSpec.getSize(hauteur) * 42 / 100 / Theatre.H;
            k = Math.max(1, Math.min(k, kMax));
            ViewGroup.LayoutParams lp = tete.getLayoutParams();
            if (lp != null && lp.height != k * Theatre.H) lp.height = k * Theatre.H;
            if (k != unite) {
                unite = k;
                ViewGroup.LayoutParams lq = perso.getLayoutParams();
                lq.width = lq.height = 64 * k;
                perso.setLayoutParams(lq);
                pilou.pixel(Aventure.pixelUnite(k));
            }
        }
        super.onMeasure(largeur, hauteur);
    }

    /** Le pixel de la scène pour cet écran : comme onMeasure (le plus grand entier qui tient dans la largeur, borné par la hauteur). */
    static int uniteEcran(android.content.Context c) {
        android.util.DisplayMetrics m = c.getResources().getDisplayMetrics();
        return Math.max(1, Math.min(Aventure.unite(m.widthPixels), m.heightPixels * 42 / 100 / Theatre.H));
    }

    /** Le signe du ton pour la police pixel : « ☼ » n'y est pas dessiné, « ☀ » oui. */
    static String signe(String ton) {
        String s = Aventure.signeTon(ton);
        return s.equals("☼") ? "☀" : s;
    }

    /** Un texte pixel d'une taille exacte : px pixels d'écran par pixel de police (pas d'échelle de police du système). */
    private TextePixelVue pixelFixe(String texte, int px, boolean titre) {
        TextePixelVue t = new TextePixelVue(app, px / d, 0xffffffff);
        t.titre(titre);
        t.texte(texte);
        return t;
    }

    /** Un texte pixel du récit ou d'un choix : 4 pixels d'écran à 2,75 de densité, fois l'échelle de police. */
    private TextePixelVue pixelRecit(String texte, int couleur) {
        TextePixelVue t = new TextePixelVue(app, pixelRecit, couleur);
        t.texte(texte);
        return t;
    }

    /**
     * Bouton carré du bandeau : un cadre pixel de 13 u × 13 u (ombre comprise) au milieu d'une zone tactile d'au moins 48 dp
     * de large sur toute la hauteur du bandeau. Le glyphe est un texte pixel ou une vue de pixels.
     */
    private View bouton(View glyphe, int couleur, String description) {
        FrameLayout zone = new FrameLayout(app);
        zone.setClickable(true);
        zone.setContentDescription(description);
        CadrePixel.Pave pave = new CadrePixel.Pave(app, cp, u, true);
        pave.setGravity(Gravity.CENTER);
        pave.air(0, 0);
        if (glyphe instanceof TextePixelVue) pave.encre((TextePixelVue) glyphe, couleur);
        pave.addView(glyphe, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        zone.addView(pave, new FrameLayout.LayoutParams(13 * u, 13 * u, Gravity.CENTER));
        zone.setLayoutParams(new LinearLayout.LayoutParams(Math.max(Ui.dp(app, 48), 13 * u), ViewGroup.LayoutParams.MATCH_PARENT));
        return zone;
    }

    /**
     * Le fil des messages. Il se mesure à la hauteur visible du défilement et prolonge son contenu d'un vide en bas quand
     * il le faut, pour que le calage en bas (le haut de la plus ancienne bulle telle que toutes les suivantes tiennent)
     * soit toujours possible.
     */
    static final class Fil extends LinearLayout {
        private int visible, marge, cible;

        Fil(android.content.Context c) {
            super(c);
        }

        void regler(int visible, int marge) {
            this.visible = visible;
            this.marge = marge;
        }

        /** Le haut du fil, en pixels, tel que le calage en bas le place. */
        int cible() {
            return cible;
        }

        /** Les hauts de bulles (moins la marge) où le défilement peut se caler. */
        int[] hauts() {
            int[] h = new int[getChildCount()];
            for (int i = 0; i < h.length; i++) h[i] = Math.max(0, getChildAt(i).getTop() - marge);
            return h;
        }

        @Override
        protected void onMeasure(int mw, int mh) {
            super.onMeasure(mw, mh);
            int n = getChildCount();
            cible = 0;
            if (visible <= 0 || n == 0) return;
            int[] tops = new int[n];
            int y = getPaddingTop();
            for (int i = 0; i < n; i++) {
                View v = getChildAt(i);
                LayoutParams lp = (LayoutParams) v.getLayoutParams();
                tops[i] = y + lp.topMargin;
                y = tops[i] + v.getMeasuredHeight() + lp.bottomMargin;
            }
            cible = cibleBas(tops, y + getPaddingBottom(), visible, marge);
            if (cible + visible > getMeasuredHeight()) setMeasuredDimension(getMeasuredWidth(), cible + visible);
        }

        /**
         * Le haut à viser quand le fil est calé en bas : celui de la plus ancienne bulle (moins marge) telle que tout ce qui
         * la suit tient dans la hauteur visible ; à défaut (la dernière bulle est plus haute que l'écran), le haut de la dernière.
         */
        static int cibleBas(int[] tops, int fin, int visible, int marge) {
            if (tops.length == 0) return 0;
            for (int top : tops) {
                int t = Math.max(0, top - marge);
                if (fin - t <= visible) return t;
            }
            return Math.max(0, tops[tops.length - 1] - marge);
        }
    }

    /** Le défilement du fil : calé sur une bulle entière en bas, et, quand l'utilisateur lâche, sur la bulle la plus proche. */
    final class Defil extends ScrollView {
        private final Fil contenu;
        private boolean suivre, doux, doigt;
        private int dernier = -1;
        private final Runnable caler = this::calerSurBulle;

        Defil(android.content.Context c, Fil contenu) {
            super(c);
            this.contenu = contenu;
        }

        /** Cale le fil en bas (au prochain passage de mise en page) ; doux : en glissant, sinon d'un coup. */
        void calerEnBas(boolean doux) {
            suivre = true;
            this.doux = doux;
            dernier = -1;
            requestLayout();
        }

        @Override
        protected void onMeasure(int largeur, int hauteur) {
            contenu.regler(MeasureSpec.getMode(hauteur) == MeasureSpec.UNSPECIFIED ? 0 : MeasureSpec.getSize(hauteur) - getPaddingTop() - getPaddingBottom(), 2 * u);
            super.onMeasure(largeur, hauteur);
        }

        @Override
        protected void onLayout(boolean changed, int l, int t, int r, int b) {
            super.onLayout(changed, l, t, r, b);
            if (!suivre) return;
            int y = Math.max(0, Math.min(contenu.cible(), contenu.getHeight() - getHeight()));
            if (getScrollY() == y) {
                dernier = y;
                return;
            }
            if (doux && Vitrine.anime(app)) {
                if (y != dernier) smoothScrollTo(0, y);   // une seule fois : les passages de mise en page suivants ne la relancent pas
            } else scrollTo(0, y);
            dernier = y;
        }

        @Override
        public boolean dispatchTouchEvent(android.view.MotionEvent e) {
            switch (e.getActionMasked()) {
                case android.view.MotionEvent.ACTION_DOWN:
                    suivre = false;
                    doigt = true;
                    removeCallbacks(caler);
                    break;
                case android.view.MotionEvent.ACTION_UP:
                case android.view.MotionEvent.ACTION_CANCEL:
                    doigt = false;
                    postDelayed(caler, 140);
                    break;
                default:
                    break;
            }
            return super.dispatchTouchEvent(e);
        }

        @Override
        protected void onScrollChanged(int l, int t, int ol, int ot) {
            super.onScrollChanged(l, t, ol, ot);
            if (doigt || suivre) return;
            removeCallbacks(caler);
            postDelayed(caler, 140);   // à l'arrêt (fin d'un coup de pouce) : on cale
        }

        /** À l'arrêt : le haut de la bulle la plus proche (ou la position du calage en bas). */
        void calerSurBulle() {
            if (doigt || suivre) return;
            int max = Math.max(0, contenu.getHeight() - getHeight());
            int meilleur = Math.max(0, Math.min(contenu.cible(), max)), y = getScrollY();
            for (int h : contenu.hauts()) {
                h = Math.min(h, max);
                if (Math.abs(h - y) < Math.abs(meilleur - y)) meilleur = h;
            }
            if (meilleur == y) return;
            if (Vitrine.anime(app)) smoothScrollTo(0, meilleur);
            else scrollTo(0, meilleur);
        }
    }

    // ---- Ouverture, rafraîchissement

    /** Recommence l'affichage de zéro (ouverture de la lecture). */
    void ouvrir() {
        gen++;
        montres.clear();
        aEcrire.clear();
        fil.removeAllViews();
        points = null;
        ecrit = false;
        vite = ScenesAnimees.texteInstantane(app);
        enCours = null;
        perso.montrer(null, "");
        enRoute = false;
        lieuTheatre = "";
        dockCle = chapitreVu = lieuVu = "";
        dernierT = 0;
        repriseVue = false;
        finMontree = false;
        fermerCouche();
        campagne = null;
        Retour.effacer(app);
        rafraichir();
        defil.calerEnBas(false);
    }

    void rafraichir() {
        Campagnes.Etat e = CampagnesTel.etat(app);
        Campagnes.Partie q = CampagnesTel.courante(app);
        Campagnes.Campagne c = q == null ? null : Campagnes.charger(q.campagne);
        if (e == null || c == null || e.phase == Campagnes.Phase.Abandon || e.phase == Campagnes.Phase.Aucune) {
            page.fermerLecture();
            return;
        }
        if (campagne != null && !campagne.id.equals(c.id)) {
            ouvrir();
            return;
        }
        campagne = c;
        etat = e;
        entete();
        lireFil();
        if (!ecrit && aEcrire.isEmpty()) {
            majTheatre();
            majDock();
        }
        tic();
    }

    // ---- La scène vivante (mêmes moments qu'au PC : FenetreAventure.cs)

    /** Montre le lieu (décor de la campagne) ; sans dessin fin, le repli (décor fixe et PilouVue) reprend la place. */
    private void lieuTheatre(String decor, boolean glisser) {
        if (campagne == null) return;
        String k = campagne.id + "|" + decor;
        if (k.equals(lieuTheatre)) return;
        lieuTheatre = k;
        boolean ok = false;
        try {
            ok = theatre.lieu(campagne.id, decor, glisser);
        } catch (RuntimeException x) {
            Journal.noter("lecture : théâtre", x);
        }
        theatre.setVisibility(ok ? View.VISIBLE : View.GONE);
        scene.setVisibility(ok ? View.GONE : View.VISIBLE);
        pilou.setVisibility(ok ? View.GONE : View.VISIBLE);
    }

    /** Tout est écrit : le lieu de l'état (sans travelling), l'humeur du dernier message, et Pilou en route s'il attend. */
    private void majTheatre() {
        if (etat == null) return;
        lieuTheatre(etat.decor, false);
        theatre.humeur(humeur, false);
        // Revenu de sa route : la prochaine réplique le fait rentrer dans la scène.
        if (enRoute && !etat.enAttente() && etat.phase != Campagnes.Phase.Repos) enRoute = false;
        // Ouverte pendant une attente : il est déjà en route, la scène montre le lieu sans lui.
        if (!enRoute && (etat.phase == Campagnes.Phase.Attente || etat.phase == Campagnes.Phase.Repos)) {
            theatre.absent();
            enRoute = true;
        }
    }

    private void entete() {
        numero.texte(etat.chapitreTotal > 0 ? ("CHAPITRE " + etat.chapitreNumero + " / " + etat.chapitreTotal) : campagne.titre.toUpperCase(java.util.Locale.FRENCH));
        chapitre.texte(etat.chapitreTitre.isEmpty() ? campagne.titre : etat.chapitreTitre);
        String l = etat.lieu.isEmpty() ? campagne.titre : etat.lieu;
        lieu.texte(signe(campagne.ton) + "  " + l);
        lieu.setContentDescription("Lieu : " + l);
        scene.regler(campagne.id, campagne.ton, etat.decor);
        fond.ton(campagne.ton);
        jauge.setBackgroundColor(Aventure.cielTon(campagne.ton)[4]);
        float part = (float) Math.max(0.02, Math.min(1, etat.progression + (etat.phase == Campagnes.Phase.Fin ? 0 : 0.5 / Math.max(1, etat.chapitreTotal))));
        ((LinearLayout.LayoutParams) jauge.getLayoutParams()).weight = part;
        ((LinearLayout.LayoutParams) jaugeVide.getLayoutParams()).weight = 1 - part;
        jauge.requestLayout();
        Etat pc = Prefs.etat(app);
        java.util.Map<String, String> porte = Gains.porte(app, pc);
        pilou.equipe(porte);
        pilou.accessoire(pc.accessoire);
        // La couleur de Pilou : celle du niveau, ou la couleur achetée à la boutique (comme PilouVue).
        String achetee = porte.get(Boutique.COULEUR);
        theatre.couleur(achetee != null && !achetee.isEmpty() ? Vitrine.teinte(achetee) : pc.couleur);
        boolean fini = !ecrit && aEcrire.isEmpty();
        if (fini && etat.phase == Campagnes.Phase.Attente) {
            pilou.tenue("voyage-" + etat.tenue);
            pilou.objets(null);
            pilou.montrer("repos", pc.couleur);
            scene.marcher(Aventure.vitesse(etat.tenue), etat.tenue.equals("nuit"));
        } else if (fini && etat.phase == Campagnes.Phase.Repos) {
            pilou.tenue("voyage-nuit");
            pilou.objets(java.util.Collections.singletonList("pansement"));
            pilou.montrer("fatigue", pc.couleur);
            scene.marcher(0, true);
        } else {
            pilou.tenue("");
            pilou.objets(null);
            pilou.montrer(humeur, pc.couleur);
            scene.marcher(0, false);
        }
    }

    private static String cle(Campagnes.Message m) {
        return m.p + "." + m.e + "." + m.i + "." + m.qui;
    }

    /** Ajoute au fil ce qui est nouveau ; Pilou écrit ses messages un à un. Si le fil a changé en arrière, on refait tout. */
    private void lireFil() {
        List<Campagnes.Message> l = CampagnesTel.fil(app, campagne.id);
        int n = Math.min(montres.size(), l.size());
        boolean prefixe = montres.size() <= l.size();
        for (int i = 0; i < n && prefixe; i++) if (!montres.get(i).equals(cle(l.get(i)))) prefixe = false;
        if (!prefixe) {
            // Une décision d'un autre appareil a gagné : le fil est réécrit, sans animation.
            gen++;
            montres.clear();
            aEcrire.clear();
            fil.removeAllViews();
            points = null;
            ecrit = false;
            chapitreVu = lieuVu = "";
            dernierT = 0;
            repriseVue = false;
            finMontree = false;
        }
        boolean premier = montres.isEmpty();
        for (int i = montres.size(); i < l.size(); i++) {
            Campagnes.Message m = l.get(i);
            montres.add(cle(m));
            boolean nouveau = m.qui.equals("pilou") && CampagnesTel.nonLu(app, m) && !m.reprise;
            if (nouveau && !vite) aEcrire.add(m);
            else if (!aEcrire.isEmpty()) aEcrire.add(m);
            else ajouter(m, !premier, false);
        }
        if (!aEcrire.isEmpty() && !ecrit) ecrire();
        else if (aEcrire.isEmpty() && !ecrit) toutLu();
        if (premier) defil.calerEnBas(false);
    }

    private void toutLu() {
        if (CampagnesTel.nonLus(app) > 0) CampagnesTel.lu(app);
    }

    // ---- Pilou écrit

    private long delai(Campagnes.Message m) {
        if (vite) return 60;
        return Animations.attente(m.texte);
    }

    private void ecrire() {
        Campagnes.Message m = aEcrire.peekFirst();
        if (m == null) {
            ecrit = false;
            toutLu();
            dockCle = "";
            rafraichir();
            return;
        }
        if (!ecrit) masquerDock();
        ecrit = true;
        int g = gen;
        if (!m.qui.equals("pilou")) {
            aEcrire.pollFirst();
            ajouter(m, true, false);
            postDelayed(() -> {
                if (g == gen) ecrire();
            }, vite ? 30 : 380);
            return;
        }
        // Les points « … », puis le message.
        dividers(m);
        LinearLayout r = rangee(false);
        CadrePixel.Pave b = new CadrePixel.Pave(app, cp, u, true);
        b.air(2 * u, 2 * u);
        b.addView(new Aventure.Points(app, cp.pale));
        r.addView(b);
        fil.addView(r, bas(3 * u));
        points = r;
        apparaitre(r, false);
        defiler();
        postDelayed(() -> {
            if (g != gen || points != r) return;
            fil.removeView(r);
            points = null;
            Campagnes.Message x = aEcrire.pollFirst();
            // Un message nouveau, écrit lettre à lettre : le lieu arrive en travelling (au rattrapage, d'un coup).
            TextePixelVue t = x != null ? ajouter(x, true, !vite && x.qui.equals("pilou")) : null;
            Runnable suite = () -> postDelayed(() -> {
                if (g == gen) ecrire();
            }, vite ? 40 : 420);
            if (t != null && !vite && x.qui.equals("pilou")) {
                // Lettre à lettre (la bulle a déjà sa taille) ; le personnage parle pendant ses répliques.
                perso.parle(Animations.parle(x.texte));
                if (!enRoute) theatre.revient();
                theatre.humeur(humeur, true);
                theatre.parle(Animations.dureeEcriture(x.texte));
                enCours = new ScenesAnimees.Ecriture(t, x.texte, () -> {
                    perso.parle(false);
                    theatre.tait();
                    if (g == gen) suite.run();
                });
            } else suite.run();
        }, delai(m));
    }

    /** Pendant que Pilou écrit, le pied s'efface (on lit d'abord, on choisit ensuite). */
    private void masquerDock() {
        dockCle = "";
        if (dock.getVisibility() != View.VISIBLE) return;
        if (!Vitrine.anime(app)) {
            dock.setVisibility(View.GONE);
            return;
        }
        dock.animate().alpha(0).translationY(Ui.dp(app, 16)).setDuration(160).withEndAction(() -> {
            if (ecrit) dock.setVisibility(View.GONE);
        }).start();
    }

    /** Toucher : tout ce qui reste à écrire arrive d'un coup. */
    void accelerer() {
        if (!ecrit && aEcrire.isEmpty()) return;
        vite = true;
        gen++;
        if (enCours != null) {
            enCours.terminer();
            enCours = null;
        }
        perso.parle(false);
        theatre.tait();
        if (points != null) {

            fil.removeView(points);
            points = null;
        }
        while (!aEcrire.isEmpty()) ajouter(aEcrire.pollFirst(), false, false);
        ecrit = false;
        toutLu();
        dockCle = "";
        rafraichir();
        defiler();
    }

    private void defiler() {
        defil.calerEnBas(true);
    }

    // ---- Les messages

    private LinearLayout rangee(boolean joueur) {
        LinearLayout r = Ui.rangee(app);
        r.setGravity(joueur ? Gravity.END : Gravity.START);
        return r;
    }

    private void apparaitre(View v, boolean joueur) {
        if (!Vitrine.anime(app)) return;
        v.setAlpha(0);
        v.setTranslationY(Ui.dp(app, 10));
        v.setTranslationX(joueur ? Ui.dp(app, 16) : 0);
        v.animate().alpha(1).translationY(0).translationX(0).setDuration(220)
                .setInterpolator(new android.view.animation.DecelerateInterpolator(1.5f)).start();
    }

    /** Séparateurs : chapitre qui commence, reprise au check-point, heure (après une longue absence), lieu qui change. */
    private void dividers(Campagnes.Message m) {
        Campagnes.Noeud n = campagne.noeud(m.noeud);
        String ch = n == null ? "" : n.chapitre;
        if (!ch.isEmpty() && !ch.equals(chapitreVu)) {
            int rang = CampagnesTel.rangChapitre(campagne, ch);
            String titre = rang >= 0 ? campagne.chapitres.get(rang).titre : "";
            if (!chapitreVu.isEmpty() || montres.size() <= 2)
                separateur(("Chapitre " + (rang + 1) + (titre.isEmpty() ? "" : " · " + titre)).toUpperCase(java.util.Locale.FRENCH), true);
            chapitreVu = ch;
        }
        if (m.reprise && !repriseVue) {
            TextePixelVue t = pixelRecit("◀  On reprend au dernier check-point", p.orange);
            t.maxLargeur(Math.round(largeurBulle * 0.9f));
            t.centre(true);
            LinearLayout r = Ui.rangee(app);
            r.setGravity(Gravity.CENTER);
            r.addView(t);
            fil.addView(r, bas(3 * u));
            repriseVue = true;
        } else if (!m.reprise) repriseVue = false;
        if (dernierT > 0 && m.t - dernierT > 10 * 60_000L) separateur(quand(m.t), false);
        dernierT = m.t;
        if (!m.lieu.isEmpty() && !m.lieu.equals(lieuVu)) {
            if (!lieuVu.isEmpty()) separateur(signe(campagne.ton) + "  " + m.lieu, false);
            lieuVu = m.lieu;
        }
    }

    private String quand(long t) {
        java.util.Calendar k = java.util.Calendar.getInstance(), maintenant = java.util.Calendar.getInstance();
        k.setTimeInMillis(t);
        maintenant.setTimeInMillis(CampagnesTel.maintenant());
        int jours = maintenant.get(java.util.Calendar.DAY_OF_YEAR) - k.get(java.util.Calendar.DAY_OF_YEAR)
                + 365 * (maintenant.get(java.util.Calendar.YEAR) - k.get(java.util.Calendar.YEAR));
        String h = CampagnesTel.heure(t);
        return jours <= 0 ? h : jours == 1 ? "hier, " + h : "il y a " + jours + " jours, " + h;
    }

    private void separateur(String texte, boolean fort) {
        // Deux traits en pointillés de pixels (1 u tous les 2 u) de part et d'autre du texte en police pixel.
        LinearLayout r = Ui.rangee(app);
        r.setGravity(Gravity.CENTER_VERTICAL);
        View g = new CadrePixel.Pointilles(app, cp.pointilles, u), dr = new CadrePixel.Pointilles(app, cp.pointilles, u);
        TextePixelVue t = pixelRecit(texte, fort ? cp.titre : p.doux);
        t.titre(fort);
        t.maxLargeur(Math.round(largeurBulle * 0.9f));
        t.setPadding(2 * u, 0, 2 * u, 0);
        r.addView(g, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        r.addView(t);
        r.addView(dr, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        LinearLayout.LayoutParams lp = bas((fort ? 3 : 2) * u);
        lp.topMargin = (fort ? 3 : 1) * u;
        fil.addView(r, lp);
    }

    private LinearLayout.LayoutParams bas(int px) {
        LinearLayout.LayoutParams l = Ui.large();
        l.bottomMargin = px;
        return l;
    }

    private TextePixelVue ajouter(Campagnes.Message m, boolean anime, boolean nouveau) {
        boolean joueur = m.qui.equals("joueur");
        if (!joueur) {
            dividers(m);
            lieuTheatre(m.decor, nouveau);
        }
        LinearLayout r = rangee(joueur);
        // La bulle : un cadre pixel (Pilou : fond du cadre ; le joueur : les couleurs « appuyé », orange ou bleu, et à droite).
        CadrePixel.Couleurs c = joueur ? CadrePixel.joueur(cp) : cp;
        CadrePixel.Pave bulle = new CadrePixel.Pave(app, c, u, true);
        bulle.air(2 * u, 2 * u);
        TextePixelVue t = pixelRecit(m.texte, c.texte);
        t.maxLargeur(largeurBulle - 2 * bulle.cadre().dedans() - 4 * u - bulle.cadre().ombre());
        t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        bulle.addView(t);
        bulle.setContentDescription((joueur ? "Toi : " : "Pilou : ") + m.texte);
        if (m.reprise) bulle.setAlpha(0.62f);
        r.addView(bulle);
        LinearLayout.LayoutParams lp = bas(3 * u);
        if (joueur) lp.topMargin = u;
        fil.addView(r, lp);
        if (!joueur) {
            humeur = humeurPilou(m.humeur);
            if (anime && (humeur.equals("joie") || humeur.equals("surpris") || humeur.equals("peur"))) pilou.sauter();
            pilou.tenue("");
            pilou.montrer(humeur, Prefs.etat(app).couleur);
            personnage(m);
        }
        if (anime) {
            apparaitre(r, joueur);
            defiler();
        }
        return t;
    }

    /** Le personnage du nœud de ce message (champ « personnage ») ; personne : le portrait s'efface. */
    private void personnage(Campagnes.Message m) {
        try {
            Campagnes.Noeud n = campagne == null ? null : campagne.noeud(m.noeud);
            Sprites.Sprite s = n == null ? null : Animations.portrait(Sprites.banque(), campagne.id, n.personnage, n.expression, 2);
            perso.montrer(s, s == null ? "" : ScenesAnimees.nomPersonnage(n.personnage));
        } catch (RuntimeException x) {
            Journal.noter("lecture : personnage", x);
            perso.montrer(null, "");
        }
    }

    static String humeurPilou(String h) {
        return h == null || h.isEmpty() || h.equals("neutre") ? "repos" : h;
    }

    // ---- Le pied : ce que le joueur peut faire

    private void majDock() {
        if (etat == null) return;
        String refusPc = CampagnesTel.refus(app);
        String k = etat.phase + "|" + etat.noeud + "|" + etat.e + "|" + refusPc + "|" + etat.options.size();
        if (k.equals(dockCle)) return;
        dockCle = k;
        dock.removeAllViews();
        if (dock.getParent() instanceof ScrollView) ((ScrollView) dock.getParent()).scrollTo(0, 0);
        compte = retourVers = refus = null;
        barreAttente = null;
        dock.setVisibility(View.VISIBLE);
        if (refusPc != null && etat.phase != Campagnes.Phase.Attente && etat.phase != Campagnes.Phase.Repos && etat.phase != Campagnes.Phase.Fin) {
            refus = Ui.texte(app, "⚠  " + refusPc + ".", Ui.T_DETAIL, p.orange, true);
            refus.setPadding(0, 0, 0, Ui.dp(app, 10));
            dock.addView(refus, Ui.large());
        }
        boolean bloque = refusPc != null;
        switch (etat.phase) {
            case Choix: choix(bloque); break;
            case Depart: depart(bloque); break;
            case Epreuve: epreuve(bloque); break;
            case Attente: attente(false); break;
            case Repos: attente(true); break;
            case Fin:
                dock.setVisibility(View.GONE);
                fin();
                break;
            default:
                dock.addView(Ui.texte(app, "Cette histoire a un souci dans ses fichiers : Pilou ne sait plus où il en est. "
                        + "Mets-la de côté ; elle reprendra au dernier check-point.", Ui.T_CORPS, p.texte, false));
                Button b = Ui.bouton(app, "Mettre de côté", false, v -> confirmerSuspension());
                LinearLayout.LayoutParams l = Ui.large();
                l.topMargin = Ui.dp(app, 10);
                dock.addView(b, l);
        }
        // Le pied grandit doucement : le fil remonte au lieu de sauter.
        if (Vitrine.anime(app) && dock.getVisibility() == View.VISIBLE) {
            dock.setAlpha(0);
            dock.setTranslationY(Ui.dp(app, 24));
            dock.animate().alpha(1).translationY(0).setDuration(240).setInterpolator(new android.view.animation.DecelerateInterpolator(1.5f)).start();
        }
        defiler();
    }

    private void choix(boolean bloque) {
        int i = 0;
        for (Campagnes.OptionVue o : etat.options) {
            View b = option(o, i, bloque);
            LinearLayout.LayoutParams l = Ui.large();
            if (i > 0) l.topMargin = 2 * u;
            dock.addView(b, l);
            if (Vitrine.anime(app)) {
                b.setAlpha(0);
                b.setTranslationY(Ui.dp(app, 12));
                b.animate().alpha(bloque ? 0.5f : 1).translationY(0).setStartDelay(90L * i + 120).setDuration(220).start();
            } else if (bloque) b.setAlpha(0.5f);
            i++;
        }
    }

    /** Un choix : un cadre pixel avec son ombre, la puce « ▶ » à la couleur du bord, le libellé en police pixel. */
    private View option(Campagnes.OptionVue o, int rang, boolean bloque) {
        CadrePixel.Pave r = new CadrePixel.Pave(app, cp, u, true);
        r.setOrientation(LinearLayout.HORIZONTAL);
        r.setGravity(Gravity.CENTER_VERTICAL);
        r.air(2 * u, 2 * u);
        r.setMinimumHeight(Ui.dp(app, 48) + u);   // la cible tactile fait au moins 48 dp (l'ombre d'1 u en plus)
        TextePixelVue s = pixelRecit("▶", cp.bord);
        s.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        r.encre(s, cp.bord);
        r.addView(s);
        TextePixelVue t = pixelRecit(o.libelle, cp.texte);
        t.setPadding(2 * u, 0, 0, 0);
        t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        r.encre(t, cp.texte);
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        r.setContentDescription("Choisir : " + o.libelle);
        r.setEnabled(!bloque);
        r.setClickable(true);
        r.setOnClickListener(v -> choisir(o, r));
        return r;
    }

    private void choisir(Campagnes.OptionVue o, View choisie) {
        // Le choix s'illumine, les autres s'effacent, puis la bulle « à lui » part dans le fil.
        for (int i = 0; i < dock.getChildCount(); i++) {
            View v = dock.getChildAt(i);
            v.setEnabled(false);
            if (v != choisie) v.animate().alpha(0.25f).setDuration(140).start();
        }
        if (choisie instanceof CadrePixel.Pave) ((CadrePixel.Pave) choisie).forcer(true);   // le choix s'enfonce : fond « appuyé »
        Ui.vibrer(app, 8);
        Sons.jouer(app, Sons.CHOIX);
        postDelayed(() -> decider(() -> CampagnesTel.choisir(app, o.id)), Vitrine.anime(app) ? 170 : 0);
    }

    private void depart(boolean bloque) {
        Campagnes.Noeud n = campagne.noeud(etat.noeud);
        String duree = "";
        if (n != null) {
            int a = Math.max(1, n.dureeMin), b = Math.max(a, n.dureeMax);
            duree = a == b ? duree(a) : "entre " + duree(a) + " et " + duree(b);
        }
        TextView t = Ui.texte(app, etat.pendant.isEmpty() ? "Pilou est prêt à repartir." : etat.pendant + ".", Ui.T_CORPS, p.texte, true);
        dock.addView(t, Ui.large());
        if (!duree.isEmpty()) {
            TextView s = Ui.texte(app, "◷  Ça prendra " + duree + ". Il n'attend que ton signal.", Ui.T_DETAIL, p.doux, false);
            s.setPadding(0, Ui.dp(app, 4), 0, 0);
            dock.addView(s, Ui.large());
        }
        Button b = Ui.bouton(app, "Vas-y, Pilou !", true, v -> decider(() -> CampagnesTel.continuer(app)));
        b.setEnabled(!bloque);
        b.setAlpha(bloque ? 0.5f : 1);
        Ui.enfoncer(b);
        LinearLayout.LayoutParams l = Ui.large();
        l.topMargin = Ui.dp(app, 12);
        dock.addView(b, l);
    }

    static String duree(int minutes) {
        if (minutes < 60) return minutes + " min";
        int h = minutes / 60, m = minutes % 60;
        return h + " h" + (m == 0 ? "" : " " + String.format(java.util.Locale.ROOT, "%02d", m));
    }

    private void epreuve(boolean bloque) {
        LinearLayout tete = Ui.rangee(app);
        tete.addView(Ui.puceTexte(app, "▲  ÉPREUVE", Aventure.accentTon(app, campagne.ton)));
        View vide = new View(app);
        tete.addView(vide, new LinearLayout.LayoutParams(0, 1, 1));
        TextView diff = Ui.texte(app, Aventure.difficulte(etat.difficulte), 14, p.doux, true);
        diff.setContentDescription("Difficulté " + etat.difficulte + " sur 3");
        tete.addView(diff);
        dock.addView(tete, Ui.large());
        TextView nom = Ui.texte(app, Aventure.nomJeu(etat.jeu), Ui.T_CARTE, p.texte, true);
        nom.setPadding(0, Ui.dp(app, 8), 0, Ui.dp(app, 2));
        dock.addView(nom, Ui.large());
        dock.addView(Ui.texte(app, Aventure.consigneJeu(etat.jeu), Ui.T_DETAIL, p.doux, false), Ui.large());
        LinearLayout r = Ui.rangee(app);
        r.setPadding(0, Ui.dp(app, 12), 0, 0);
        Button jouer = Ui.bouton(app, "Jouer", true, v -> lancerEpreuve(false));
        Button des = Ui.bouton(app, "Les dés · " + etat.chance + "\u00a0%", false, v -> lancerEpreuve(true));
        des.setContentDescription("Laisser faire les dés : " + etat.chance + " pour cent de chance");
        for (Button b : new Button[]{jouer, des}) {
            b.setEnabled(!bloque);
            b.setAlpha(bloque ? 0.5f : 1);
            Ui.enfoncer(b);
        }
        LinearLayout.LayoutParams lj = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        lj.rightMargin = Ui.dp(app, 8);
        r.addView(jouer, lj);
        r.addView(des, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        dock.addView(r, Ui.large());
    }

    private void lancerEpreuve(boolean auxDes) {
        int tirage = CampagnesTel.tirageDe(app, etat);
        Epreuves.Ecran ecran = new Epreuves.Ecran(app, auxDes ? "des" : etat.jeu, etat.difficulte, etat.chance, tirage, campagne.ton,
                reussie -> {
                    fermerCouche();
                    decider(() -> auxDes ? CampagnesTel.auDe(app) : CampagnesTel.epreuve(app, reussie));
                }, this::fermerCouche);
        montrerCouche(ecran);
    }

    private void attente(boolean repos) {
        long maintenant = CampagnesTel.maintenant();
        LinearLayout tete = Ui.rangee(app);
        TextView quoi = Ui.texte(app, repos ? "Pilou se repose" : etat.pendant.isEmpty() ? "Pilou est en route" : etat.pendant, Ui.T_CORPS, p.texte, true);
        quoi.setMaxLines(2);
        tete.addView(quoi, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        dock.addView(tete, Ui.large());
        LinearLayout r = Ui.rangee(app);
        r.setPadding(0, Ui.dp(app, 10), 0, Ui.dp(app, 4));
        compte = Ui.texte(app, Aventure.compte(etat.fin - maintenant), 30, Aventure.accentTon(app, campagne.ton), true);
        compte.setTypeface(Typeface.create("monospace", Typeface.BOLD));
        r.addView(compte);
        retourVers = Ui.texte(app, (repos ? "reprise vers " : "retour vers ") + CampagnesTel.heure(etat.fin), Ui.T_DETAIL, p.doux, false);
        retourVers.setPadding(Ui.dp(app, 12), 0, 0, 0);
        r.addView(retourVers, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        dock.addView(r, Ui.large());
        barreAttente = new Ui.Barre(app);
        dock.addView(barreAttente, Ui.large());
        String note;
        if (repos) {
            String l = CampagnesTel.lieuReprise(campagne, CampagnesTel.courante(app), etat);
            note = "Il est un peu cabossé. Reprise au dernier check-point" + (l.isEmpty() ? "." : " : " + l + ".");
        } else note = Prefs.alerteAventure(app) ? "Tu peux poser ton téléphone : je te préviens." : "Les notifications de retour sont coupées : reviens voir de temps en temps.";
        TextView n = Ui.texte(app, note, Ui.T_DETAIL, p.doux, false);
        n.setPadding(0, Ui.dp(app, 8), 0, 0);
        dock.addView(n, Ui.large());
        tic();
    }

    /** Chaque seconde : le compte à rebours et la barre. */
    private void tic() {
        if (compte == null || etat == null || !etat.enAttente()) return;
        long maintenant = CampagnesTel.maintenant(), reste = etat.fin - maintenant;
        compte.setText(Aventure.compte(reste));
        compte.setContentDescription("Encore " + CampagnesTel.reste(reste));
        if (barreAttente != null) {
            long total = Math.max(1, etat.fin - etat.t);
            barreAttente.part(1 - reste / (float) total);
        }
    }

    // ---- La fin

    private void fin() {
        if (finMontree) return;
        finMontree = true;
        CampagnesTel.lu(app);
        FrameLayout cadre = new FrameLayout(app);
        LinearLayout c = Ui.carte(app);
        c.setGravity(Gravity.CENTER_HORIZONTAL);
        int couleur = Aventure.couleurIssue(app, etat.issue);
        c.setBackground(Ui.arrondi(app, p.surface, 20, couleur));
        TextView etiquette = Ui.texte(app, "FIN DE L'AVENTURE", Ui.T_ETIQUETTE, p.doux, true);
        etiquette.setLetterSpacing(0.14f);
        c.addView(etiquette);
        TextView signe = Ui.texte(app, Aventure.signeIssue(etat.issue), 44, couleur, true);
        signe.setPadding(0, Ui.dp(app, 6), 0, 0);
        signe.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        c.addView(signe);
        TextView issue = Ui.texte(app, Aventure.nomIssue(etat.issue), Ui.T_DETAIL, couleur, true);
        c.addView(issue);
        TextView titre = Ui.texte(app, etat.titreFin.isEmpty() ? campagne.titre : etat.titreFin, 22, p.texte, true);
        titre.setGravity(Gravity.CENTER);
        titre.setPadding(0, Ui.dp(app, 6), 0, Ui.dp(app, 12));
        c.addView(titre, Ui.large());

        Campagnes.Prime r = etat.recompenses;
        LinearLayout gains = Ui.rangee(app);
        gains.setGravity(Gravity.CENTER);
        if (!etat.rejeu && r.po > 0) gains.addView(puce("◉  +" + r.po + " po", p.orange));
        if (!etat.rejeu && r.xp > 0) gains.addView(puce("✦  +" + r.xp + " xp", p.bleu));
        if (gains.getChildCount() > 0) c.addView(gains);
        for (int i = 0; i < gains.getChildCount(); i++) ScenesAnimees.tomber(gains.getChildAt(i), Animations.delaiRecompense(i));
        // Le souvenir se pose avec un petit éclat, puis l'emblème du ton.
        LinearLayout vitrine = Ui.rangee(app);
        vitrine.setGravity(Gravity.CENTER);
        View vs = ScenesAnimees.vignette(app, Sprites.souvenir(Sprites.banque(), campagne.id, r.souvenir, 2), 72);
        if (vs != null) vitrine.addView(ScenesAnimees.eclat(app, vs, couleur, Animations.delaiRecompense(gains.getChildCount())));
        View tv = ScenesAnimees.vignette(app, Sprites.ton(Sprites.banque(), campagne.ton, 2), 36);
        if (tv != null) vitrine.addView(ScenesAnimees.eclat(app, tv, Aventure.accentTon(app, campagne.ton), Animations.delaiRecompense(gains.getChildCount() + 1)));
        if (vitrine.getChildCount() > 0) {
            LinearLayout.LayoutParams lv = Ui.large();
            lv.topMargin = Ui.dp(app, 8);
            c.addView(vitrine, lv);
        }
        int[] attente = CampagnesTel.enAttente(app);
        String note = etat.rejeu ? "Rejouer ne redonne ni pièces ni xp : seulement ce que tu n'avais pas encore."
                : attente[0] + attente[1] > 0 ? "Ces gains attendent ton PC : il les versera dès qu'il sera allumé." : "";
        if (!note.isEmpty()) {
            TextView t = Ui.texte(app, note, Ui.T_DETAIL, p.doux, false);
            t.setGravity(Gravity.CENTER);
            t.setPadding(0, Ui.dp(app, 8), 0, 0);
            c.addView(t, Ui.large());
        }
        if (!r.titre.isEmpty()) ligneFin(c, "Titre gagné", "« " + r.titre + " »", null);
        if (!r.objet.isEmpty()) {
            String nom = r.objet;
            for (Campagnes.Nomme o : campagne.objets) if (o.id.equals(r.objet)) nom = o.nom;
            ligneFin(c, "Objet exclusif", nom, r.objet);
        }
        if (!r.souvenir.isEmpty()) {
            Campagnes.Nomme s = campagne.souvenir(r.souvenir);
            if (s != null) {
                LinearLayout sv = Ui.pile(app);
                sv.setBackground(Ui.arrondi(app, p.surface2, 14, 0));
                sv.setPadding(Ui.dp(app, 14), Ui.dp(app, 12), Ui.dp(app, 14), Ui.dp(app, 12));
                sv.addView(Ui.texte(app, "◈  SOUVENIR", Ui.T_ETIQUETTE, p.doux, true));
                sv.addView(Ui.texte(app, s.nom, Ui.T_CORPS, p.texte, true));
                if (!s.texte.isEmpty()) sv.addView(Ui.texte(app, s.texte, Ui.T_DETAIL, p.doux, false));
                LinearLayout.LayoutParams l = Ui.large();
                l.topMargin = Ui.dp(app, 12);
                c.addView(sv, l);
            }
        }
        // Les fins : celles qu'on a, les autres en « ? ? ? ».
        List<Campagnes.FinObtenue> obtenues = Campagnes.fins(CampagnesTel.carnet(app), campagne);
        List<Campagnes.Noeud> toutes = CampagnesTel.finsDe(campagne);
        TextView tf = Ui.texte(app, ("Fins découvertes · " + obtenues.size() + " / " + toutes.size()).toUpperCase(java.util.Locale.FRENCH), Ui.T_ETIQUETTE, p.doux, true);
        tf.setLetterSpacing(0.08f);
        tf.setPadding(0, Ui.dp(app, 16), 0, Ui.dp(app, 6));
        c.addView(tf, Ui.large());
        c.addView(PageAventure.grilleFins(app, campagne, obtenues, toutes, etat.noeud), Ui.large());

        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 16);
        c.addView(Ui.bouton(app, "Retour aux aventures", true, v -> page.fermerLecture()), lb);
        LinearLayout.LayoutParams lr = Ui.large();
        lr.topMargin = Ui.dp(app, 8);
        c.addView(Ui.bouton(app, "Rejouer depuis le début", false, v -> page.rejouer(campagne)), lr);
        cadre.addView(c, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        if (etat.issue.equals("bonne") || etat.issue.equals("secrete"))
            cadre.addView(new Aventure.Etincelles(app, new int[]{Vitrine.ORANGE, Vitrine.BLEU_CLAIR, Aventure.CREME, Vitrine.VIOLET}),
                    new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        LinearLayout.LayoutParams lc = Ui.large();
        lc.topMargin = Ui.dp(app, 12);
        fil.addView(cadre, lc);
        apparaitre(cadre, false);
        pilou.montrer(etat.issue.equals("mauvaise") ? "triste" : etat.issue.equals("douce-amere") ? "tendre" : "joie", Prefs.etat(app).couleur);
        pilou.sauter();
        defiler();
    }

    private TextView puce(String texte, int couleur) {
        TextView t = Ui.puceTexte(app, texte, couleur);
        t.setTextSize(android.util.TypedValue.COMPLEX_UNIT_SP, 14);
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        l.setMargins(Ui.dp(app, 4), 0, Ui.dp(app, 4), 0);
        t.setLayoutParams(l);
        return t;
    }

    private void ligneFin(LinearLayout c, String etiquette, String valeur, String objet) {
        LinearLayout r = Ui.rangee(app);
        r.setPadding(0, Ui.dp(app, 12), 0, 0);
        if (objet != null) r.addView(PageAventure.imageObjet(app, objet, 1.0f));
        LinearLayout t = Ui.pile(app);
        t.setPadding(objet != null ? Ui.dp(app, 12) : 0, 0, 0, 0);
        t.addView(Ui.texte(app, etiquette.toUpperCase(java.util.Locale.FRENCH), Ui.T_ETIQUETTE, p.doux, true));
        t.addView(Ui.texte(app, valeur, Ui.T_CORPS, p.texte, true));
        if (objet != null) t.addView(Ui.texte(app, "Rejoint ta collection : il se porte comme les objets de la boutique.", Ui.T_DETAIL, p.doux, false));
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        c.addView(r, Ui.large());
    }

    // ---- Décider

    private void decider(java.util.function.Supplier<String> d) {
        String r;
        try {
            r = d.get();
        } catch (RuntimeException x) {
            Journal.noter("campagne : décision", x);
            r = "petit souci, réessaie";
        }
        // Un choix, « vas-y » ou une épreuve qui mène à une attente ou un repos : Pilou part pour de vrai, il sort de la scène en marchant.
        if (r == null && !enRoute) {
            Campagnes.Etat suite = CampagnesTel.etat(app);
            if (suite != null && (suite.phase == Campagnes.Phase.Attente || suite.phase == Campagnes.Phase.Repos)) {
                theatre.depart();
                enRoute = true;
            }
        }
        dockCle = "";
        if (r != null) {
            android.widget.Toast.makeText(app, r, android.widget.Toast.LENGTH_LONG).show();
        } else Ui.vibrer(app, 6);
        rafraichir();
        page.apresDecision();
    }

    // ---- Couche (épreuves, menu, confirmation)

    private void montrerCouche(View v) {
        couche.removeAllViews();
        couche.addView(v, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        couche.setVisibility(View.VISIBLE);
        if (Vitrine.anime(app)) {
            couche.setAlpha(0);
            couche.animate().alpha(1).setDuration(160).start();
        }
    }

    void fermerCouche() {
        if (couche.getVisibility() != View.VISIBLE) return;
        // Après le toucher : la vue touchée quitte l'écran au tour suivant.
        post(() -> {
            couche.removeAllViews();
            couche.setVisibility(View.GONE);
        });
    }

    boolean coucheOuverte() {
        return couche.getVisibility() == View.VISIBLE;
    }

    /** Feuille du bas : un titre, un texte, des actions. */
    private View feuille(String titre, String texte, Object... actions) {
        return Aventure.feuille(app, titre, texte, this::fermerCouche, actions);
    }

    private void menu() {
        montrerCouche(feuille(campagne == null ? "Aventure" : campagne.titre, null,
                "Carnet de voyage", false, (View.OnClickListener) v -> {
                    fermerCouche();
                    page.ouvrirCarnet();
                },
                "Mettre l'aventure de côté…", false, (View.OnClickListener) v -> confirmerSuspension(),
                "Animations : " + ScenesAnimees.nomNiveau(ScenesAnimees.reglage(app)) + "  ›", false, (View.OnClickListener) v -> {
                    String n = ScenesAnimees.reglage(app);
                    ScenesAnimees.regler(app, Animations.COMPLETES.equals(n) ? Animations.REDUITES : Animations.REDUITES.equals(n) ? Animations.AUCUNE : Animations.COMPLETES);
                    fermerCouche();
                    post(this::menu);
                },
                "Texte instantané : " + (Prefs.de(app).getBoolean("texteInstantane", false) ? "oui" : "non"), false, (View.OnClickListener) v -> {
                    ScenesAnimees.texteInstantane(app, !Prefs.de(app).getBoolean("texteInstantane", false));
                    vite = ScenesAnimees.texteInstantane(app);
                    fermerCouche();
                    post(this::menu);
                },
                "Continuer la lecture", true, (View.OnClickListener) v -> fermerCouche()));
    }

    /** Deuxième geste : on dit clairement ce qui se passe, et ce qui ne se perd pas. */
    void confirmerSuspension() {
        if (campagne == null) return;
        String l = CampagnesTel.lieuReprise(campagne, CampagnesTel.courante(app), etat);
        montrerCouche(feuille("Mettre « " + campagne.titre + " » de côté ?",
                "Pilou rentre à la maison. Tu pourras reprendre plus tard au dernier check-point"
                        + (l.isEmpty() ? "" : " (" + l + ")") + ". Rien de ce qui est acquis ne se perd.",
                "Mettre de côté", false, (View.OnClickListener) v -> {
                    fermerCouche();
                    decider(() -> CampagnesTel.abandonner(app));
                },
                "Continuer l'aventure", true, (View.OnClickListener) v -> fermerCouche()));
    }

    /** Pour les tests et la touche retour : terminer l'épreuve en cours comme si le joueur l'avait jouée. */
    void terminerEpreuve(boolean reussie) {
        fermerCouche();
        decider(() -> CampagnesTel.epreuve(app, reussie));
    }

    /** Pour les tests : l'écran d'épreuve ouvert (null : aucun). */
    Epreuves.Ecran epreuveOuverte() {
        for (int i = 0; i < couche.getChildCount(); i++) if (couche.getChildAt(i) instanceof Epreuves.Ecran) return (Epreuves.Ecran) couche.getChildAt(i);
        return null;
    }

    /** Pour les tests : le fil entier (capture longue). */
    View filVue() {
        return fil;
    }

    /** Pour les tests : ouvrir l'épreuve (aux dés ou non). */
    void ouvrirEpreuve(boolean auxDes) {
        if (etat != null && etat.phase == Campagnes.Phase.Epreuve) lancerEpreuve(auxDes);
    }
}
