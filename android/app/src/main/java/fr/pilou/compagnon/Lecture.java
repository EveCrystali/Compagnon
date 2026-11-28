package fr.pilou.compagnon;

import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;

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
    private final CadrePixel.Cases jauge;
    private final LinearLayout.LayoutParams jaugeLp;
    private final FrameLayout.LayoutParams lieuLp;
    private int reglageK, reglageW;
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
    private TextePixelVue compte, retourVers, refus;
    private CadrePixel.Cases barreAttente;
    private boolean finMontree;
    /** Largeur (pixels d'écran) d'une bulle et d'un choix : l'écran moins la gouttière de chaque côté. */
    private final int largeurBulle;
    /** Marge de chaque côté du fil et des choix, en u : 3 (rembourrage) + 2 (cadre du pied) pour le pied, la même pour le fil. */
    static final int GOUTTIERE = 5;
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
        u = uniteEcran(a);
        largeurBulle = a.getResources().getDisplayMetrics().widthPixels - 2 * GOUTTIERE * u;
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

        // Le lieu : un petit cadre pixel sans ombre portée, texte en police pixel (4 pixels d'écran par pixel de police) sur
        // une ligne. Il tient entièrement dans la scène (192 u de large, centrée), à 1 u de son bord droit et de son bord bas.
        CadrePixel.Pave puceLieu = new CadrePixel.Pave(a, cp, u, false);
        puceLieu.air(u, u);
        lieu = pixelFixe("", 4, false);
        lieu.maxLignes(1);
        puceLieu.encre(lieu, cp.texte);
        puceLieu.addView(lieu);
        // En haut à gauche de la scène, comme sur PC : le bas à droite est la place du personnage en pied.
        lieuLp = new LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP | Gravity.START);
        tete.addView(puceLieu, lieuLp);
        colonne.addView(tete, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(a, 184)));

        // Avancement dans la campagne : une jauge de carrés pixel sous la scène, sur sa largeur exacte (192 u), au lieu du trait.
        jauge = new CadrePixel.Cases(a, cp.bord, cp.pale, u, 1);
        jaugeLp = new LinearLayout.LayoutParams(Theatre.W * u, u);
        jaugeLp.gravity = Gravity.CENTER_HORIZONTAL;
        jaugeLp.topMargin = 2 * u;
        jauge.setContentDescription("Avancement de l'aventure");
        colonne.addView(jauge, jaugeLp);
        reglerLieu(a.getResources().getDisplayMetrics().widthPixels, u);

        // ---- Le fil.
        // Pas de fondu : le défilement se cale sur une bulle entière (Defil), donc aucune ligne n'est tranchée au repos
        // par le bord de la scène.
        fil = new Fil(a);
        fil.setOrientation(LinearLayout.VERTICAL);
        fil.setPadding(GOUTTIERE * u, 2 * u, GOUTTIERE * u, 0);
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

    /** Pour les tests : la puce de lieu (le cadre pixel) et la jauge d'avancement. */
    View puceLieu() {
        return (View) lieu.getParent();
    }

    View jaugeVue() {
        return jauge;
    }

    View tete() {
        return tete;
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
            if (k > 0) {
                reglerLieu(MeasureSpec.getSize(largeur), k);
            }
        }
        super.onMeasure(largeur, hauteur);
    }

    /** Marge droite de la puce de lieu (pixels d'écran) : le vide à droite de la scène centrée (largeur px, unité k), plus 1 u. */
    static int margeLieuDroite(int largeur, int k) {
        return Math.max(0, (largeur - Theatre.W * k) / 2) + k;
    }

    /** Largeur maximale de la puce de lieu entière : la scène moins 1 u de marge de chaque côté. */
    static int largeurPuceMax(int k) {
        return Theatre.W * k - 2 * k;
    }

    /** Largeur maximale du texte du lieu : la puce moins son cadre (2 × 2 u : bord et biseau) et son air (2 × 1 u), sans ombre. */
    static int largeurTexteLieu(int k) {
        return largeurPuceMax(k) - 6 * k;
    }

    /** Place la puce de lieu et la jauge sur la scène (largeur de l'écran et unité) ; ne fait rien si rien n'a changé. */
    private void reglerLieu(int largeur, int k) {
        if (largeur == reglageW && k == reglageK) return;
        reglageW = largeur;
        reglageK = k;
        lieuLp.leftMargin = margeLieuDroite(largeur, k);       // la marge est la même des deux côtés de la scène
        lieuLp.topMargin = k;
        lieu.maxLargeur(largeurTexteLieu(k));
        jaugeLp.width = Theatre.W * k;
        jaugeLp.height = k;
        jaugeLp.topMargin = 2 * k;
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
     * Le fil des messages, ancré en bas : la dernière bulle est juste au-dessus des choix, les précédentes entières au-dessus
     * tant qu'elles tiennent ; s'il reste de la place, elle est en haut. Il se mesure au moins à la hauteur visible du
     * défilement (ses enfants se collent au bas), et son défilement au repos se cale sur le bas.
     */
    static final class Fil extends LinearLayout {
        private int visible, marge, cible;
        /** Le séparateur du chapitre courant (le bandeau le dit déjà : il n'est jamais montré en tête de l'écran). */
        View sepCourant;

        Fil(android.content.Context c) {
            super(c);
            setGravity(android.view.Gravity.BOTTOM);
        }

        void regler(int visible, int marge) {
            this.visible = visible;
            this.marge = marge;
        }

        /** Le haut du fil, en pixels, tel que l'ancrage en bas le place. */
        int cible() {
            return cible;
        }

        /** Les hauts de bulles (moins la marge) où le défilement peut se caler. */
        int[] hauts() {
            int[] h = new int[getChildCount()];
            for (int i = 0; i < h.length; i++) h[i] = Math.max(0, getChildAt(i).getTop() - marge);
            return h;
        }

        /**
         * Le haut (dans le fil) à partir duquel tout est entier quand le défilement est à y : le haut du premier enfant
         * qui commence à y ou plus bas, en sautant le séparateur du chapitre courant s'il est en tête.
         */
        int hautEntier(int y) {
            int n = getChildCount();
            int[] tops = new int[n];
            for (int i = 0; i < n; i++) tops[i] = getChildAt(i).getTop();
            int i = premierEntier(tops, y);
            if (i < n && getChildAt(i) == sepCourant && i + 1 < n) i++;
            return i < n ? tops[i] : getHeight();
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
            int fin = y + getPaddingBottom();
            cible = cibleBas(tops, fin, visible, marge);
            if (visible > getMeasuredHeight()) setMeasuredDimension(getMeasuredWidth(), visible);
        }

        /**
         * Le haut à viser quand le fil est ancré en bas : celui qui met le bas du contenu (fin) au bas de la zone visible ;
         * 0 si tout tient ; si la dernière bulle seule dépasse la hauteur visible, le début de cette bulle (moins marge).
         */
        static int cibleBas(int[] tops, int fin, int visible, int marge) {
            if (tops.length == 0 || fin <= visible) return 0;
            int bas = fin - visible;
            int derniere = Math.max(0, tops[tops.length - 1] - marge);
            return derniere < bas ? derniere : bas;
        }

        /** L'indice du premier haut d'enfant qui est à y ou plus bas (la longueur du tableau s'il n'y en a pas). */
        static int premierEntier(int[] tops, int y) {
            for (int i = 0; i < tops.length; i++) if (tops[i] >= y) return i;
            return tops.length;
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

        /** Au repos, ancré en bas : le haut (dans le fil) sous lequel tout est entier ; au-dessus, rien n'est dessiné. -1 : pas de coupe. */
        int coupe() {
            if (doigt) return -1;
            int y = getScrollY(), max = Math.max(0, contenu.getHeight() - getHeight());
            if (y != Math.min(contenu.cible(), max)) return -1;
            return contenu.hautEntier(y);
        }

        @Override
        protected void dispatchDraw(android.graphics.Canvas c) {
            int coupe = coupe();
            if (coupe < 0) {
                super.dispatchDraw(c);
                return;
            }
            // Aucune ligne tranchée par le bord de la scène : la bulle entamée en haut est masquée, la place reste vide.
            int s = c.save();
            c.clipRect(0, coupe, getWidth(), getScrollY() + getHeight());
            super.dispatchDraw(c);
            c.restoreToCount(s);
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
        float part = (float) Math.max(0.02, Math.min(1, etat.progression + (etat.phase == Campagnes.Phase.Fin ? 0 : 0.5 / Math.max(1, etat.chapitreTotal))));
        jauge.part(part);
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
        fil.addView(r, bas(2 * u));
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
                // Une réplique est dite par le personnage en pied s'il est là ; sinon, par Pilou.
                long duree = Animations.dureeEcriture(x.texte);
                if (!(Animations.parle(x.texte) && theatre.parlePerso(duree))) theatre.parle(duree);
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
            // Le chapitre courant n'a pas de séparateur en tête du fil (le bandeau le dit) : seulement le passage d'un chapitre à l'autre.
            if (!chapitreVu.isEmpty())
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
            fil.addView(r, bas(2 * u));
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
        LinearLayout.LayoutParams lp = bas(2 * u);
        lp.topMargin = (fort ? 3 : 1) * u;
        fil.addView(r, lp);
        if (fort) fil.sepCourant = r;
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
        // Un seul narrateur : la bulle de Pilou prend toute la largeur des choix ; celle du joueur, à droite, au plus la même.
        r.addView(bulle, new LinearLayout.LayoutParams(joueur ? ViewGroup.LayoutParams.WRAP_CONTENT : ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        LinearLayout.LayoutParams lp = bas(2 * u);
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
            if (n != null) theatre.personnage(campagne.id, n.personnage);
            // Dessiné en pied dans la scène : pas de portrait par-dessus (il le cacherait) ; sinon le portrait reste.
            if (theatre.aPerso()) s = null;
            perso.montrer(s, s == null ? "" : ScenesAnimees.nomPersonnage(n.personnage));
        } catch (RuntimeException x) {
            Journal.noter("lecture : personnage", x);
            perso.montrer(null, "");
        }
    }

    static String humeurPilou(String h) {
        return h == null || h.isEmpty() || h.equals("neutre") ? "repos" : h;
    }

    // ---- Éléments communs en pixels (cartes du pied, fin, feuille)

    /** Un texte pixel en police titre (gras). */
    private TextePixelVue titrePixel(String texte, int couleur) {
        TextePixelVue t = pixelRecit(texte, couleur);
        t.titre(true);
        return t;
    }

    /** Un texte pixel de détail (couleur pâle), qui passe à la ligne dans la largeur du pied. */
    private TextePixelVue detailPixel(String texte) {
        return pixelRecit(texte, cp.pale);
    }

    /** Une taille de police pixel multiple de celle du récit (compte à rebours, signe de fin). */
    private TextePixelVue grandPixel(String texte, int couleur, int facteur) {
        TextePixelVue t = new TextePixelVue(app, pixelRecit * facteur, couleur);
        t.texte(texte);
        return t;
    }

    /**
     * Un bouton pixel : cadre avec ombre, libellé en police pixel, cible d'au moins 48 dp de haut. Le bouton principal prend le
     * fond « appuyé » (orange en sombre, bleu en clair) comme mise en avant, et un signe « ▶ » (la forme le porte aussi).
     */
    private CadrePixel.Pave action(String libelle, boolean principal, String description, View.OnClickListener ecoute) {
        CadrePixel.Pave b = new CadrePixel.Pave(app, cp, u, true);
        b.setOrientation(LinearLayout.HORIZONTAL);
        b.setGravity(Gravity.CENTER);
        b.air(2 * u, 2 * u);
        b.setMinimumHeight(Ui.dp(app, 48) + u);
        int couleur = principal ? cp.appuyeTexte : cp.texte;
        if (principal) {
            TextePixelVue s = pixelRecit("▶", couleur);
            s.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            b.encre(s, couleur);
            b.addView(s);
        }
        TextePixelVue t = pixelRecit(libelle, couleur);
        if (principal) t.setPadding(2 * u, 0, 0, 0);
        t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        b.encre(t, couleur);
        b.addView(t);
        b.setContentDescription(description != null ? description : libelle);
        b.setClickable(true);
        b.setOnClickListener(ecoute);
        if (principal) b.forcer(true);
        return b;
    }

    private LinearLayout.LayoutParams haut(int px) {
        LinearLayout.LayoutParams l = Ui.large();
        l.topMargin = px;
        return l;
    }

    /** Le signe de l'issue, dessiné par la police pixel (« ◐ » et « ▽ » n'y sont pas). */
    static String signeIssue(String issue) {
        switch (issue) {
            case "douce-amere": return "☾";
            case "mauvaise": return "▼";
            case "secrete": return "✧";
            default: return "★";
        }
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
            refus = pixelRecit("▲  " + refusPc + ".", p.orange);
            dock.addView(refus, Ui.large(app, 0));
            ((LinearLayout.LayoutParams) refus.getLayoutParams()).bottomMargin = 2 * u;
        }
        boolean bloque = refusPc != null;
        switch (etat.phase) {
            case Choix: choix(bloque); break;
            case Depart: depart(bloque); break;
            case Epreuve: epreuve(bloque); break;
            case Attente: attente(false); break;
            case Repos: attente(true); break;
            case Fin:
                // La carte de fin défile dans le fil ; le retour reste épinglé dans le pied, toujours entier.
                dock.addView(action("Retour aux aventures", true, null, v -> page.fermerLecture()), Ui.large());
                fin();
                break;
            default:
                dock.addView(pixelRecit("Cette histoire a un souci dans ses fichiers : Pilou ne sait plus où il en est. "
                        + "Mets-la de côté ; elle reprendra au dernier check-point.", cp.texte), Ui.large());
                dock.addView(action("Mettre de côté", false, null, v -> confirmerSuspension()), haut(3 * u));
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
        dock.addView(titrePixel(etat.pendant.isEmpty() ? "Pilou est prêt à repartir." : etat.pendant + ".", cp.texte), Ui.large());
        if (!duree.isEmpty()) dock.addView(detailPixel("Ça prendra " + duree + ". Il n'attend que ton signal."), haut(u));
        CadrePixel.Pave b = action("Vas-y, Pilou !", true, null, v -> decider(() -> CampagnesTel.continuer(app)));
        b.setEnabled(!bloque);
        b.setAlpha(bloque ? 0.5f : 1);
        dock.addView(b, haut(3 * u));
    }

    static String duree(int minutes) {
        if (minutes < 60) return minutes + " min";
        int h = minutes / 60, m = minutes % 60;
        return h + " h" + (m == 0 ? "" : " " + String.format(java.util.Locale.ROOT, "%02d", m));
    }

    /** La difficulté en signes de forme pixel : « ◆ » plein, « ○ » vide (« ◇ » n'est pas dans la police). */
    private static String difficultePixel(int d) {
        StringBuilder b = new StringBuilder();
        for (int i = 1; i <= 3; i++) b.append(i <= d ? "◆" : "○");
        return b.toString();
    }

    private void epreuve(boolean bloque) {
        LinearLayout tete = Ui.rangee(app);
        tete.setGravity(Gravity.CENTER_VERTICAL);
        tete.addView(titrePixel("▲  ÉPREUVE", Aventure.accentTon(app, campagne.ton)));
        View vide = new View(app);
        tete.addView(vide, new LinearLayout.LayoutParams(0, 1, 1));
        TextePixelVue diff = titrePixel(difficultePixel(etat.difficulte), cp.pale);
        diff.setContentDescription("Difficulté " + etat.difficulte + " sur 3");
        tete.addView(diff);
        dock.addView(tete, Ui.large());
        dock.addView(titrePixel(Aventure.nomJeu(etat.jeu), cp.texte), haut(2 * u));
        dock.addView(detailPixel(Aventure.consigneJeu(etat.jeu)), haut(u));
        LinearLayout r = Ui.rangee(app);
        CadrePixel.Pave jouer = action("Jouer", true, null, v -> lancerEpreuve(false));
        CadrePixel.Pave des = action("Les dés · " + etat.chance + " %", false,
                "Laisser faire les dés : " + etat.chance + " pour cent de chance", v -> lancerEpreuve(true));
        for (View b : new View[]{jouer, des}) {
            b.setEnabled(!bloque);
            b.setAlpha(bloque ? 0.5f : 1);
        }
        LinearLayout.LayoutParams lj = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        lj.rightMargin = 2 * u;
        r.addView(jouer, lj);
        r.addView(des, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        dock.addView(r, haut(3 * u));
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
        TextePixelVue quoi = titrePixel(repos ? "Pilou se repose" : etat.pendant.isEmpty() ? "Pilou est en route" : etat.pendant, cp.texte);
        quoi.maxLignes(2);
        dock.addView(quoi, Ui.large());
        LinearLayout r = Ui.rangee(app);
        r.setGravity(Gravity.CENTER_VERTICAL);
        // Le compte à rebours : police titre, deux fois la taille du récit.
        compte = grandPixel(Aventure.compte(etat.fin - maintenant), Aventure.accentTon(app, campagne.ton), 2);
        compte.titre(true);
        r.addView(compte);
        retourVers = detailPixel((repos ? "reprise vers " : "retour vers ") + CampagnesTel.heure(etat.fin));
        retourVers.setPadding(3 * u, 0, 0, 0);
        r.addView(retourVers, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        dock.addView(r, haut(3 * u));
        // L'avancement de l'attente : des carrés de 2 u séparés d'1 u, sur toute la largeur du pied.
        barreAttente = new CadrePixel.Cases(app, cp.bord, cp.pale, u, 2);
        dock.addView(barreAttente, haut(3 * u));
        String note;
        if (repos) {
            String l = CampagnesTel.lieuReprise(campagne, CampagnesTel.courante(app), etat);
            note = "Il est un peu cabossé. Reprise au dernier check-point" + (l.isEmpty() ? "." : " : " + l + ".");
        } else note = Prefs.alerteAventure(app) ? "Tu peux poser ton téléphone : je te préviens." : "Les notifications de retour sont coupées : reviens voir de temps en temps.";
        dock.addView(detailPixel(note), haut(3 * u));
        tic();
    }

    /** Chaque seconde : le compte à rebours et la barre. */
    private void tic() {
        if (compte == null || etat == null || !etat.enAttente()) return;
        long maintenant = CampagnesTel.maintenant(), reste = etat.fin - maintenant;
        compte.texte(Aventure.compte(reste));
        compte.setContentDescription("Encore " + CampagnesTel.reste(reste));
        if (barreAttente != null) {
            long total = Math.max(1, etat.fin - etat.t);
            barreAttente.part(1 - reste / (float) total);
        }
    }

    // ---- La fin

    /** Largeur du texte dans la carte de fin : celle d'un choix moins le cadre (2 × 2 u), l'air (2 × 3 u) et l'ombre (1 u). */
    private int largeurCarte() {
        return largeurBulle - 11 * u;
    }

    private TextePixelVue pixelCarte(String texte, int couleur, boolean titre, boolean centre) {
        TextePixelVue t = pixelRecit(texte, couleur);
        t.titre(titre);
        t.centre(centre);
        t.maxLargeur(largeurCarte());
        return t;
    }

    private void fin() {
        if (finMontree) return;
        finMontree = true;
        CampagnesTel.lu(app);
        FrameLayout cadre = new FrameLayout(app);
        // La carte de fin : un grand cadre pixel avec son ombre, comme les bulles et les choix.
        CadrePixel.Pave c = new CadrePixel.Pave(app, cp, u, true);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setGravity(Gravity.CENTER_HORIZONTAL);
        c.air(3 * u, 3 * u);
        int couleur = Aventure.couleurIssue(app, etat.issue);
        c.addView(pixelCarte("FIN DE L'AVENTURE", cp.pale, true, true), Ui.large());
        TextePixelVue signe = grandPixel(signeIssue(etat.issue), couleur, 3);
        signe.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        LinearLayout.LayoutParams ls = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        ls.topMargin = 2 * u;
        c.addView(signe, ls);
        c.addView(pixelCarte(Aventure.nomIssue(etat.issue), couleur, true, true), Ui.large());
        c.addView(pixelCarte(etat.titreFin.isEmpty() ? campagne.titre : etat.titreFin, cp.texte, true, true), haut(2 * u));

        Campagnes.Prime r = etat.recompenses;
        LinearLayout gains = Ui.rangee(app);
        gains.setGravity(Gravity.CENTER);
        if (!etat.rejeu && r.po > 0) gains.addView(puce("¤  +" + r.po + " po", p.orange));
        if (!etat.rejeu && r.xp > 0) gains.addView(puce("✦  +" + r.xp + " xp", p.bleu));
        if (gains.getChildCount() > 0) c.addView(gains, haut(3 * u));
        for (int i = 0; i < gains.getChildCount(); i++) ScenesAnimees.tomber(gains.getChildAt(i), Animations.delaiRecompense(i));
        // Le souvenir se pose avec un petit éclat, puis l'emblème du ton.
        LinearLayout vitrine = Ui.rangee(app);
        vitrine.setGravity(Gravity.CENTER);
        View vs = ScenesAnimees.vignette(app, Sprites.souvenir(Sprites.banque(), campagne.id, r.souvenir, 2), 72);
        if (vs != null) vitrine.addView(ScenesAnimees.eclat(app, vs, couleur, Animations.delaiRecompense(gains.getChildCount())));
        View tv = ScenesAnimees.vignette(app, Sprites.ton(Sprites.banque(), campagne.ton, 2), 36);
        if (tv != null) vitrine.addView(ScenesAnimees.eclat(app, tv, Aventure.accentTon(app, campagne.ton), Animations.delaiRecompense(gains.getChildCount() + 1)));
        if (vitrine.getChildCount() > 0) c.addView(vitrine, haut(2 * u));
        int[] attente = CampagnesTel.enAttente(app);
        String note = etat.rejeu ? "Rejouer ne redonne ni pièces ni xp : seulement ce que tu n'avais pas encore."
                : attente[0] + attente[1] > 0 ? "Ces gains attendent ton PC : il les versera dès qu'il sera allumé." : "";
        if (!note.isEmpty()) c.addView(pixelCarte(note, cp.pale, false, true), haut(2 * u));
        if (!r.titre.isEmpty()) ligneFin(c, "Titre gagné", "« " + r.titre + " »", null);
        if (!r.objet.isEmpty()) {
            String nom = r.objet;
            for (Campagnes.Nomme o : campagne.objets) if (o.id.equals(r.objet)) nom = o.nom;
            ligneFin(c, "Objet exclusif", nom, r.objet);
        }
        if (!r.souvenir.isEmpty()) {
            Campagnes.Nomme s = campagne.souvenir(r.souvenir);
            if (s != null) {
                CadrePixel.Pave sv = new CadrePixel.Pave(app, cp, u, false);
                sv.setOrientation(LinearLayout.VERTICAL);
                sv.air(2 * u, 2 * u);
                int interieur = largeurCarte() - 8 * u;   // le sous-cadre prend encore 2 × (2 u de cadre + 2 u d'air)
                TextePixelVue e = pixelRecit("◆  SOUVENIR", cp.pale);
                e.maxLargeur(interieur);
                sv.addView(e);
                TextePixelVue nomS = titrePixel(s.nom, cp.texte);
                nomS.maxLargeur(interieur);
                sv.addView(nomS);
                if (!s.texte.isEmpty()) {
                    TextePixelVue tt = detailPixel(s.texte);
                    tt.maxLargeur(interieur);
                    sv.addView(tt);
                }
                c.addView(sv, haut(3 * u));
            }
        }
        // Les fins : celles qu'on a, les autres en « ? ? ? ».
        List<Campagnes.FinObtenue> obtenues = Campagnes.fins(CampagnesTel.carnet(app), campagne);
        List<Campagnes.Noeud> toutes = CampagnesTel.finsDe(campagne);
        c.addView(pixelCarte(("Fins découvertes · " + obtenues.size() + " / " + toutes.size()).toUpperCase(java.util.Locale.FRENCH), cp.pale, false, false), haut(4 * u));
        c.addView(grilleFinsPixel(obtenues, toutes, etat.noeud), haut(2 * u));

        c.addView(action("Rejouer depuis le début", false, null, v -> page.rejouer(campagne)), haut(4 * u));
        cadre.addView(c, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        if (etat.issue.equals("bonne") || etat.issue.equals("secrete"))
            cadre.addView(new Aventure.Etincelles(app, new int[]{Vitrine.ORANGE, Vitrine.BLEU_CLAIR, Aventure.CREME, Vitrine.VIOLET}),
                    new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        fil.addView(cadre, haut(3 * u));
        apparaitre(cadre, false);
        pilou.montrer(etat.issue.equals("mauvaise") ? "triste" : etat.issue.equals("douce-amere") ? "tendre" : "joie", Prefs.etat(app).couleur);
        pilou.sauter();
        defiler();
    }

    /** Une récompense : un petit cadre pixel sans ombre, texte en couleur d'accent (le signe en tête porte aussi le sens). */
    private View puce(String texte, int couleur) {
        CadrePixel.Pave b = new CadrePixel.Pave(app, cp, u, false);
        b.air(2 * u, u);
        b.addView(pixelRecit(texte, couleur));
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        l.setMargins(u, 0, u, 0);
        b.setLayoutParams(l);
        return b;
    }

    private void ligneFin(LinearLayout c, String etiquette, String valeur, String objet) {
        LinearLayout r = Ui.rangee(app);
        r.setGravity(Gravity.CENTER_VERTICAL);
        if (objet != null) r.addView(PageAventure.imageObjet(app, objet, 1.0f));
        LinearLayout t = Ui.pile(app);
        t.setPadding(objet != null ? 3 * u : 0, 0, 0, 0);
        int largeur = largeurCarte() - (objet != null ? 3 * u + Ui.dp(app, 48) : 0);
        TextePixelVue e = pixelRecit(etiquette.toUpperCase(java.util.Locale.FRENCH), cp.pale);
        e.maxLargeur(largeur);
        t.addView(e);
        TextePixelVue v = titrePixel(valeur, cp.texte);
        v.maxLargeur(largeur);
        t.addView(v);
        if (objet != null) {
            TextePixelVue d = detailPixel("Rejoint ta collection : il se porte comme les objets de la boutique.");
            d.maxLargeur(largeur);
            t.addView(d);
        }
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        c.addView(r, haut(3 * u));
    }

    /**
     * Les fins de la campagne, deux par rangée : un petit cadre pixel chacune. Découverte : signe, nom, titre (le signe de forme
     * dit l'issue en plus de la couleur) ; sinon « ? À découvrir ». La fin qu'on vient de faire prend le fond « appuyé ».
     */
    private View grilleFinsPixel(List<Campagnes.FinObtenue> obtenues, List<Campagnes.Noeud> toutes, String nouvelle) {
        LinearLayout g = Ui.pile(app);
        LinearLayout rang = null;
        // Une cellule : (largeur de la carte − 2 u d'écart) / 2, moins son cadre (2 × 2 u) et son air (2 × 2 u).
        int largeurCellule = (largeurCarte() - 2 * u) / 2 - 8 * u;
        for (int i = 0; i < toutes.size(); i++) {
            if (i % 2 == 0) {
                rang = Ui.rangee(app);
                rang.setGravity(Gravity.TOP);
                g.addView(rang, haut(i == 0 ? 0 : 2 * u));
            }
            Campagnes.Noeud n = toutes.get(i);
            Campagnes.FinObtenue f = null;
            for (Campagnes.FinObtenue x : obtenues) if (x.noeud.equals(n.id)) f = x;
            boolean neuve = f != null && n.id.equals(nouvelle);
            CadrePixel.Pave cell = new CadrePixel.Pave(app, cp, u, false);
            cell.setOrientation(LinearLayout.VERTICAL);
            cell.air(2 * u, 2 * u);
            cell.setMinimumHeight(Ui.dp(app, 48));
            TextePixelVue a, b;
            if (f != null) {
                int couleur = Aventure.couleurIssue(app, f.issue);
                a = pixelRecit(signeIssue(f.issue) + "  " + Aventure.nomIssue(f.issue).replace("Fin ", "").replace(" fin", ""), couleur);
                b = titrePixel(f.titre, cp.texte);
                b.maxLignes(2);
                cell.setContentDescription(Aventure.nomIssue(f.issue) + " : " + f.titre);
                cell.encre(a, couleur);
                cell.encre(b, cp.texte);
            } else {
                a = pixelRecit("?  À découvrir", cp.pale);
                b = titrePixel("? ? ?", cp.pale);
                cell.setContentDescription("Fin pas encore découverte");
                cell.encre(a, cp.pale);
                cell.encre(b, cp.pale);
            }
            a.maxLignes(1);
            a.maxLargeur(largeurCellule);
            b.maxLargeur(largeurCellule);
            a.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            b.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            cell.addView(a);
            cell.addView(b);
            if (neuve) cell.forcer(true);
            LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
            if (i % 2 == 0) l.rightMargin = 2 * u;
            rang.addView(cell, l);
        }
        if (toutes.size() % 2 == 1 && rang != null) rang.addView(new View(app), new LinearLayout.LayoutParams(0, 1, 1));
        return g;
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
        // Un grand cadre pixel sans ombre collé au bas de l'écran ; titre en police titre, boutons pixel (le dernier, à
        // « true », est la mise en avant). Tout le reste de l'écran est un voile : un toucher dessus ferme la feuille.
        android.widget.FrameLayout voile = new android.widget.FrameLayout(app);
        voile.setBackgroundColor(0x990d1117);
        voile.setClickable(true);
        voile.setOnClickListener(v -> fermerCouche());
        LinearLayout f = Ui.pile(app);
        f.setBackground(new CadrePixel(cp, u, false));
        f.setPadding(5 * u, 5 * u, 5 * u, 5 * u);
        f.setClickable(true);
        int largeur = Math.max(1, app.getResources().getDisplayMetrics().widthPixels - 10 * u);
        if (titre != null) {
            TextePixelVue t = titrePixel(titre, cp.titre);
            t.maxLargeur(largeur);
            f.addView(t, Ui.large());
        }
        if (texte != null) {
            TextePixelVue t = detailPixel(texte);
            t.maxLargeur(largeur);
            f.addView(t, haut(2 * u));
        }
        for (int i = 0; i + 2 < actions.length; i += 3) {
            View.OnClickListener a = (View.OnClickListener) actions[i + 2];
            f.addView(action((String) actions[i], (Boolean) actions[i + 1], null, a), haut(i == 0 && titre == null && texte == null ? 0 : 2 * u + (i == 0 ? u : 0)));
        }
        voile.addView(f, new android.widget.FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM));
        if (Vitrine.anime(app)) {
            f.setTranslationY(Ui.dp(app, 60));
            f.animate().translationY(0).setDuration(220).setInterpolator(new android.view.animation.DecelerateInterpolator(1.8f)).start();
        }
        return voile;
    }

    private void menu() {
        montrerCouche(feuille(campagne == null ? "Aventure" : campagne.titre, null,
                "Carnet de voyage", false, (View.OnClickListener) v -> {
                    fermerCouche();
                    page.ouvrirCarnet();
                },
                "Mettre l'aventure de côté…", false, (View.OnClickListener) v -> confirmerSuspension(),
                "Animations : " + ScenesAnimees.nomNiveau(ScenesAnimees.reglage(app)) + "  →", false, (View.OnClickListener) v -> {
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
