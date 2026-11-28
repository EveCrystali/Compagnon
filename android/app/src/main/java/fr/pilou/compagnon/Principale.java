package fr.pilou.compagnon;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;

import android.content.pm.PackageManager;
import android.graphics.Insets;
import android.graphics.drawable.ColorDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/**
 * L'app Pilou : une seule activité, cinq onglets (Accueil, Aventure, Jouer, Boutique, Collection), une barre de
 * navigation en bas et, en haut, le bandeau niveau / XP / pièces d'or, avec la roue des Réglages. Bord à bord : le
 * contenu passe sous les barres système, décalé de leur hauteur.
 */
public final class Principale extends Activity {
    /** Pages : les cinq onglets de la barre (NAV), puis les Réglages (la roue du bandeau). */
    static final int ACCUEIL = 0, AVENTURE = 1, JOUER = 2, BOUTIQUE = 3, COLLECTION = 4, REGLAGES = 5, N = 6, NAV = 5;
    static final String EXTRA_ONGLET = "onglet", EXTRA_LECTURE = "lecture";
    private static final String[] NOMS = {"Accueil", "Aventure", "Jouer", "Boutique", "Collection", "Réglages"};
    private static final String[] ICONES = {"ui-accueil", "ui-aventure", "ui-jouer", "ui-boutique", "ui-collection", "ui-reglages"};

    private final Handler h = new Handler(Looper.getMainLooper());
    private final Page[] pages = new Page[N];
    private final View[] boutons = new View[N], onglets = new View[N];
    private final Style.Icone[] icones = new Style.Icone[N];
    private final TextView[] libelles = new TextView[N];
    private FrameLayout contenu, cadre, entete;
    private LinearLayout nav;
    private int pixelNav;
    private Vitrine.Bandeau bandeau;
    private TextView pastilleBoutique, pastilleAventure;
    private Style.Icone roue;
    private View boutonRoue;
    private View rangees;
    private int courant = -1, avantReglages = ACCUEIL;
    private boolean actif;

    @Override
    protected void onCreate(Bundle sauve) {
        super.onCreate(sauve);
        Journal.installer(this);
        Ui.Palette p = Ui.p(this);
        Window w = getWindow();
        w.setBackgroundDrawable(new ColorDrawable(p.fond)); // remplace l'écran de démarrage

        LinearLayout racine = Ui.pile(this);
        racine.setBackgroundColor(p.fond);
        // Bandeau permanent (niveau, XP, po, prochaine rangée), sur toute la largeur : un toucher ouvre les niveaux.
        entete = new FrameLayout(this);
        entete.setBackgroundColor(Vitrine.NUIT);
        bandeau = new Vitrine.Bandeau(this);
        bandeau.setOnClickListener(v -> allerNiveaux());
        entete.addView(bandeau, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        // La roue des Réglages : 48 dp de toucher, posée sur le bandeau, à droite des pièces d'or. Ouverte : elle
        // prend un cadre et la couleur d'accent (la forme le dit, pas la seule couleur).
        FrameLayout r = new FrameLayout(this);
        roue = new Style.Icone(this, ICONES[REGLAGES], Vitrine.ARGENT, 2);
        r.addView(roue, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER));
        r.setContentDescription("Réglages");
        r.setOnClickListener(v -> aller(courant == REGLAGES ? avantReglages : REGLAGES, true));
        FrameLayout.LayoutParams lr = new FrameLayout.LayoutParams(Ui.dp(this, 48), Ui.dp(this, 48), Gravity.TOP | Gravity.END);
        lr.rightMargin = Ui.dp(this, 2);
        lr.topMargin = Ui.dp(this, 2);
        entete.addView(r, lr);
        boutonRoue = r;
        racine.addView(entete, Ui.large());
        contenu = new FrameLayout(this);
        racine.addView(contenu, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        // Barre du bas : un liseré d'un module, puis les cinq onglets. Le libellé prend la plus grande taille de police
        // pixel qui laisse chaque nom dans sa case (« Collection » ne touche plus « Boutique » en grande police).
        Style.Palette st = Style.p(this);
        View lisere = new View(this);
        lisere.setBackgroundColor(st.bord);
        racine.addView(lisere, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Style.u(this)));
        nav = Ui.rangee(this);
        nav.setBackgroundColor(st.carte);
        int caseNav = getResources().getDisplayMetrics().widthPixels / NAV - 4 * Style.u(this);
        pixelNav = Style.pixelQuiTient(this, java.util.Arrays.copyOf(NOMS, NAV), Style.PETIT, false, caseNav);
        for (int i = 0; i < NAV; i++) nav.addView(boutonNav(i), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        racine.addView(nav, Ui.large());
        racine.setOnApplyWindowInsetsListener((v, ins) -> {
            int haut, bas, gauche, droite;
            if (Build.VERSION.SDK_INT >= 30) {
                Insets b = ins.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
                haut = b.top;
                bas = b.bottom;
                gauche = b.left;
                droite = b.right;
            } else {
                haut = ins.getSystemWindowInsetTop();
                bas = ins.getSystemWindowInsetBottom();
                gauche = ins.getSystemWindowInsetLeft();
                droite = ins.getSystemWindowInsetRight();
            }
            entete.setPadding(gauche, haut, droite, 0);
            contenu.setPadding(gauche, 0, droite, 0);
            nav.setPadding(gauche, Ui.dp(this, 4), droite, bas + Ui.dp(this, 4));
            return ins;
        });
        // Cadre : l'app, et par-dessus, la fenêtre « Rangées débloquées » quand un niveau en ouvre.
        cadre = new FrameLayout(this);
        cadre.addView(racine, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(cadre);
        // Après setContentView : la fenêtre (DecorView) existe, son contrôleur des barres système aussi.
        bordABord(w, p);

        int onglet = sauve != null ? sauve.getInt(EXTRA_ONGLET, ACCUEIL) : getIntent().getIntExtra(EXTRA_ONGLET, ACCUEIL);
        aller(onglet, false);
        if (sauve == null && getIntent().getBooleanExtra(EXTRA_LECTURE, false)) ouvrirLecture();
        majBandeau();
        lireLien(getIntent());
        if (sauve == null && !Prefs.de(this).getBoolean("notifDemandee", false)) {
            Prefs.de(this).edit().putBoolean("notifDemandee", true).apply();
            demanderNotifications();
        }
    }

    @SuppressWarnings("deprecation")
    private void bordABord(Window w, Ui.Palette p) {
        w.setStatusBarColor(0x00000000);
        w.setNavigationBarColor(Style.p(this).carte);
        boolean clair = !Ui.sombre(this);
        if (Build.VERSION.SDK_INT >= 30) {
            w.getDecorView(); // crée la fenêtre si besoin : getInsetsController() en dépend
            w.setDecorFitsSystemWindows(false);
            WindowInsetsController c = w.getInsetsController();
            if (c != null) {
                int f = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
                c.setSystemBarsAppearance(clair ? WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS : 0, f);
            }
        } else {
            int f = View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;
            if (clair && Build.VERSION.SDK_INT >= 26) f |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            w.getDecorView().setSystemUiVisibility(f);
        }
    }

    private View boutonNav(int i) {
        Style.Palette p = Style.p(this);
        int u = Style.u(this);
        LinearLayout b = Ui.pile(this);
        b.setGravity(Gravity.CENTER_HORIZONTAL);
        b.setPadding(0, u, 0, u);
        b.setMinimumHeight(Ui.dp(this, 48));
        // L'icône dans sa case : un cadre plat l'entoure quand l'onglet est ouvert.
        FrameLayout fond = new FrameLayout(this);
        fond.setPadding(3 * u, 2 * u, 3 * u, 2 * u);
        icones[i] = new Style.Icone(this, ICONES[i], p.pale, 2);
        fond.addView(icones[i], new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER));
        FrameLayout pose = new FrameLayout(this);
        pose.addView(fond, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER));
        if (i == BOUTIQUE || i == AVENTURE) {
            // Pastille « ! » : une rangée vient de s'ouvrir (boutique) ; Pilou est revenu et attend (aventure).
            Style.Texte pastille = new Style.Texte(this, "!", pixelNav, Vitrine.ENCRE, true, true);
            pastille.setBackground(Style.plat(this, Vitrine.ORANGE, Vitrine.ENCRE));
            pastille.setPadding(u, u, u, u);
            pastille.setGravity(Gravity.CENTER);
            pastille.setMinimumWidth(9 * pixelNav + 2 * u);
            pastille.setVisibility(View.GONE);
            pastille.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            FrameLayout.LayoutParams lpb = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP | Gravity.END);
            pose.addView(pastille, lpb);
            pose.setPadding(4 * u, 0, 4 * u, 0);
            if (i == BOUTIQUE) pastilleBoutique = pastille;
            else pastilleAventure = pastille;
        }
        boutons[i] = fond;
        b.addView(pose);
        libelles[i] = new Style.Texte(this, NOMS[i], pixelNav, p.pale, false, true);
        libelles[i].setGravity(Gravity.CENTER_HORIZONTAL);
        libelles[i].setSingleLine(true);
        b.addView(libelles[i], Ui.large());
        b.setContentDescription(NOMS[i]);
        b.setOnClickListener(v -> aller(i, true));
        onglets[i] = b;
        return b;
    }

    Page page(int i) {
        if (pages[i] == null) {
            switch (i) {
                case AVENTURE: pages[i] = new PageAventure(this); break;
                case JOUER: pages[i] = new PageJouer(this); break;
                case BOUTIQUE: pages[i] = new PageBoutique(this); break;
                case COLLECTION: pages[i] = new PageCollection(this); break;
                case REGLAGES: pages[i] = new PageReglages(this); break;
                default: pages[i] = new PageAccueil(this);
            }
        }
        return pages[i];
    }

    /** Va à l'onglet i (fondu et léger glissement). */
    void aller(int i, boolean anime) {
        if (i < 0 || i >= N) i = ACCUEIL;
        if (i == REGLAGES && courant != REGLAGES && courant >= 0) avantReglages = courant;
        Style.Palette p = Style.p(this);
        roue.couleur(i == REGLAGES ? Vitrine.ORANGE : Vitrine.ARGENT);
        boutonRoue.setBackground(i == REGLAGES ? Style.plat(this, Vitrine.NUIT3, Vitrine.ORANGE) : null);
        boutonRoue.setSelected(i == REGLAGES);
        for (int k = 0; k < NAV; k++) {
            // Onglet ouvert : un cadre autour de l'icône (la forme), et la couleur du choix (le bleu de la coche).
            boolean sel = k == i;
            icones[k].couleur(sel ? p.coche : p.pale);
            boutons[k].setBackground(sel ? Style.plat(this, Style.melange(p.carte, p.coche, 0.14f), p.coche) : null);
            int u = Style.u(this);
            boutons[k].setPadding(3 * u, 2 * u, 3 * u, 2 * u); // le cadre remet sa propre marge : on repose la nôtre
            libelles[k].setTextColor(sel ? p.coche : p.pale);
            // L'onglet courant est annoncé « sélectionné » par TalkBack.
            onglets[k].setSelected(sel);
        }
        if (i == courant) {
            page(i).retourHaut();
            return;
        }
        Page nouvelle = page(i);
        if (nouvelle.getParent() == null) contenu.addView(nouvelle, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        for (int k = 0; k < N; k++) if (pages[k] != null && k != i) pages[k].setVisibility(View.GONE);
        nouvelle.setVisibility(View.VISIBLE);
        if (anime && Vitrine.anime(this)) {
            // Transition courte : fondu et léger glissement dans le sens de la navigation.
            int sens = courant < 0 ? 0 : i > courant ? 1 : -1;
            nouvelle.setAlpha(0);
            nouvelle.setTranslationX(Ui.dp(this, 18) * sens);
            nouvelle.setTranslationY(sens == 0 ? Ui.dp(this, 10) : 0);
            nouvelle.animate().alpha(1).translationX(0).translationY(0).setDuration(180)
                    .setInterpolator(new android.view.animation.DecelerateInterpolator(1.6f)).start();
        }
        courant = i;
        nouvelle.montree();
        majBandeau();
    }

    /** Aventure, directement dans la lecture de la campagne en cours (notification de retour, carte de l'accueil, bulle). */
    void ouvrirLecture() {
        Sons.jouer(this, Sons.AVENTURE);
        aller(AVENTURE, true);
        ((PageAventure) page(AVENTURE)).lire();
    }

    /** Boutique, sur un rayon (PageBoutique.VITRINE : la vitrine). */
    void allerBoutique(String rayon) {
        aller(BOUTIQUE, true);
        ((PageBoutique) page(BOUTIQUE)).rayon(rayon);
    }

    /** Collection → Niveaux (le bandeau y mène). */
    void allerNiveaux() {
        aller(COLLECTION, true);
        ((PageCollection) page(COLLECTION)).choisir(PageCollection.NIVEAUX);
    }

    /** Collection → Métiers et succès (la carte de l'accueil y mène). */
    void allerMetiers() {
        aller(COLLECTION, true);
        ((PageCollection) page(COLLECTION)).choisir(PageCollection.METIERS);
    }

    /** Bandeau, pastille de la boutique, et fenêtre « Rangées débloquées » au passage d'un palier. */
    void majBandeau() {
        if (bandeau == null) return;
        Etat e = Prefs.etat(this);
        int n = Gains.niveau(this, e), xp = Gains.xp(this, e);
        // Titre porté (boutique, ensemble complet, collection) à la place du titre de niveau.
        String titre = Boutique.nomTitre(Gains.porte(this, e).get(Boutique.TITRE));
        bandeau.mettre(n, xp, e.po < 0 ? -1 : Gains.solde(this, e), titre != null ? titre : Butin.titre(n), Vitrine.prochainesRangees(n, xp));
        boolean neuf = courant != BOUTIQUE && PageBoutique.nouveautes(this, e) > 0;
        pastilleBoutique.setVisibility(neuf ? View.VISIBLE : View.GONE);
        onglets[BOUTIQUE].setContentDescription(neuf ? "Boutique, du nouveau" : "Boutique");
        // Le niveau ne se compte qu'appairé : l'appairage d'un Pilou déjà grand n'ouvre pas la fenêtre « Rangées débloquées ».
        boolean appaire = Chiffre.valide(Prefs.code(this));
        int vu = appaire ? Prefs.de(this).getInt("niveauVu", 0) : 0;
        if (vu > 0 && n > vu && !Boutique.debloques(vu, n).isEmpty()) montrerRangees(vu, n);
        if (appaire && n != vu) Prefs.de(this).edit().putInt("niveauVu", n).apply();
        majAventure();
    }

    private String aventureVue = "";

    /** Pastille « ! » de l'onglet Aventure : Pilou est revenu, il a écrit, il attend. */
    void majAventure() {
        if (pastilleAventure == null || !CampagnesTel.pretes()) return;
        Campagnes.Etat e = CampagnesTel.etat(this);
        boolean attend = courant != AVENTURE && CampagnesTel.attendJoueur(this, e);
        String vu = String.valueOf(attend);
        if (vu.equals(aventureVue)) return;
        aventureVue = vu;
        pastilleAventure.setVisibility(attend ? View.VISIBLE : View.GONE);
        if (attend && Vitrine.anime(this)) {
            pastilleAventure.setScaleX(0.2f);
            pastilleAventure.setScaleY(0.2f);
            pastilleAventure.animate().scaleX(1).scaleY(1).setDuration(260).setInterpolator(new android.view.animation.OvershootInterpolator(2.5f)).start();
        }
        onglets[AVENTURE].setContentDescription(attend ? "Aventure, Pilou t'attend" : "Aventure");
    }

    /** « NIVEAU 15 ! Rangées débloquées » : les objets entrés en rayon, « Voir en boutique » ou « Plus tard ». */
    void montrerRangees(int avant, int apres) {
        if (rangees != null) cadre.removeView(rangees);
        java.util.List<Boutique.Article> neufs = Boutique.debloques(avant, apres);
        java.util.List<String> rayons = new java.util.ArrayList<>();
        for (String r : Boutique.RAYONS)
            for (Boutique.Article a : neufs) if (Boutique.rayonDe(a.slot).equals(r) && !rayons.contains(r)) rayons.add(r);
        FrameLayout voile = new FrameLayout(this);
        voile.setBackgroundColor(0xaa0d1117);
        voile.setClickable(true);
        LinearLayout c = Ui.pile(this);
        c.setGravity(Gravity.CENTER_HORIZONTAL);
        c.setPadding(Ui.dp(this, 18), Ui.dp(this, 18), Ui.dp(this, 18), Ui.dp(this, 16));
        Style.fond(c, Style.cadre(this, Style.NUIT));
        c.addView(new Vitrine.Pixel(this, "NIVEAU " + apres + " !", 4, Vitrine.ORANGE, Vitrine.VIOLET_FONCE, false));
        Vitrine.Pixel sous = new Vitrine.Pixel(this, "RANGÉES DÉBLOQUÉES", 2, Vitrine.VIOLET, Vitrine.ENCRE, false);
        sous.setPadding(0, Ui.dp(this, 10), 0, 0);
        c.addView(sous);
        // Signe et nom insécables : une ligne ne coupe jamais « ▲ Tête » en deux ; au-delà de six rayons, « +N ».
        StringBuilder noms = new StringBuilder();
        for (int i = 0; i < Math.min(6, rayons.size()); i++)
            noms.append(i > 0 ? "   " : "").append(Boutique.signe(rayons.get(i))).append('\u00a0').append(Boutique.nomSlot(rayons.get(i)));
        if (rayons.size() > 6) noms.append("   +").append(rayons.size() - 6);
        TextView t = Style.texte(this, noms, 14, Vitrine.ARGENT_CLAIR, true);
        t.setGravity(Gravity.CENTER);
        t.setPadding(0, Ui.dp(this, 10), 0, Ui.dp(this, 6));
        c.addView(t, Ui.large());
        LinearLayout r = Ui.rangee(this);
        r.setGravity(Gravity.CENTER);
        float d = getResources().getDisplayMetrics().density;
        int k = 0;
        for (Boutique.Article a : neufs) {
            if (!Boutique.surPilou(a.slot) || !java.util.Arrays.asList(Boutique.SLOTS).contains(a.slot) || k >= 4) continue;
            android.widget.ImageView im = new android.widget.ImageView(this);
            RenduPilou.Allure al = Vitrine.allure(a, 0);
            al.expr = "fete";
            im.setImageBitmap(Vitrine.pilou(al, 1.15f * d, false));
            im.setContentDescription(a.nom);
            r.addView(im);
            k++;
        }
        c.addView(r);
        LinearLayout b = Ui.rangee(this);
        b.setPadding(0, Ui.dp(this, 14), 0, 0);
        TextView voir = Style.bouton(this, Style.NUIT, "Voir en boutique", true, v -> {
            fermerRangees();
            allerBoutique(rayons.isEmpty() ? PageBoutique.VITRINE : rayons.get(0));
        });
        b.addView(voir);
        TextView tard = Style.bouton(this, Style.NUIT, "Plus tard", false, v -> fermerRangees());
        LinearLayout.LayoutParams lt = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lt.leftMargin = Ui.dp(this, 8);
        b.addView(tard, lt);
        c.addView(b);
        FrameLayout.LayoutParams lc = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
        lc.leftMargin = lc.rightMargin = Ui.dp(this, 22);
        voile.addView(c, lc);
        cadre.addView(voile, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        rangees = voile;
        if (Vitrine.anime(this)) {
            c.setScaleX(0.85f);
            c.setScaleY(0.85f);
            c.setAlpha(0);
            c.animate().scaleX(1).scaleY(1).alpha(1).setDuration(260).start();
        }
    }

    private void fermerRangees() {
        if (rangees == null) return;
        View v = rangees;
        rangees = null;
        // Après le toucher (jamais pendant) : la vue touchée quitte l'écran au tour suivant.
        h.post(() -> cadre.removeView(v));
    }

    @Override
    protected void onSaveInstanceState(Bundle b) {
        super.onSaveInstanceState(b);
        b.putInt(EXTRA_ONGLET, courant);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (rangees != null) fermerRangees();
        else if (courant >= 0 && page(courant).retour()) return;
        else if (courant == REGLAGES) aller(avantReglages, true);
        else if (courant != ACCUEIL) aller(ACCUEIL, true);
        else super.onBackPressed();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (intent.hasExtra(EXTRA_ONGLET)) aller(intent.getIntExtra(EXTRA_ONGLET, ACCUEIL), true);
        if (intent.getBooleanExtra(EXTRA_LECTURE, false)) ouvrirLecture();
        lireLien(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        actif = true;
        Retour.auPremierPlan = true;
        Veille.demarrer(this);
        // Les campagnes se lisent hors du fil d'interface ; puis l'alarme du retour est remise d'aplomb.
        Context app = getApplicationContext();
        CampagnesTel.precharger(() -> {
            if (courant >= 0 && actif) page(courant).rafraichir();
            // Les nouvelles des PC du groupe (une décision prise ailleurs), puis l'alarme du retour remise d'aplomb.
            new Thread(() -> {
                CampagnesTel.synchroniser(app);
                Retour.programmer(app);
                // Présence au quotidien : un jour ensemble de plus, le groupe relu, le mot du soir reprogrammé.
                PresenceTel.vecu(app, null, "");
                PresenceTel.synchroniser(app);
                MotDuSoir.programmer(app);
            }, "pilou-retour").start();

        });
        tic();
    }

    @Override
    protected void onPause() {
        super.onPause();
        actif = false;
        Retour.auPremierPlan = false;
        h.removeCallbacksAndMessages(null);
    }

    private void tic() {
        if (!actif) return;
        if (courant >= 0) pages[courant].rafraichir();
        majBandeau();
        PresenceTel.seconde(this, 1000); // le temps passé ensemble, l'app ouverte
        h.postDelayed(this::tic, 1000);
    }

    // pilou://appairer?c=CODE[&s=relais] : le QR code du PC, scanné avec l'appareil photo.
    private void lireLien(Intent i) {
        Uri u = i == null ? null : i.getData();
        if (u == null || !"pilou".equals(u.getScheme())) return;
        String c = u.getQueryParameter("c");
        String s = u.getQueryParameter("s");
        if (c != null && appairer(c, s == null ? Prefs.RELAIS_DEFAUT : s)) {
            Toast.makeText(this, "Appairé avec ton PC ✓", Toast.LENGTH_LONG).show();
            aller(ACCUEIL, true);
        }
    }

    /** Enregistre le code et (re)lance l'écoute ; false si le code est incomplet. */
    boolean appairer(String code, String relais) {
        if (!Chiffre.valide(code)) return false;
        String r = relais == null || relais.trim().isEmpty() ? Prefs.RELAIS_DEFAUT : relais.trim().replaceAll("/+$", "");
        Prefs.de(this).edit().putString("code", Chiffre.normaliser(code)).putString("relais", r)
                .remove("etat").remove("dernierId").apply();
        Veille.demarrer(this); // le service voit le nouveau code et repart
        if (pages[REGLAGES] != null) pages[REGLAGES].rafraichir();
        return true;
    }

    void demanderNotifications() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
    }

    boolean notificationsPermises() {
        return Build.VERSION.SDK_INT < 33 || checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    String version() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return "?";
        }
    }
}
