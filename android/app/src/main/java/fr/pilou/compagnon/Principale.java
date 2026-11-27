package fr.pilou.compagnon;

import android.Manifest;
import android.app.Activity;
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
 * L'app Pilou : une seule activité, cinq onglets (Accueil, Jouer, Boutique, Collection, Réglages), une barre de
 * navigation en bas et, en haut de chaque onglet, le bandeau niveau / XP / pièces d'or. Bord à bord : le contenu
 * passe sous les barres système, décalé de leur hauteur.
 */
public final class Principale extends Activity {
    static final int ACCUEIL = 0, JOUER = 1, BOUTIQUE = 2, COLLECTION = 3, REGLAGES = 4, N = 5;
    static final String EXTRA_ONGLET = "onglet";
    private static final String[] NOMS = {"Accueil", "Jouer", "Boutique", "Collection", "Réglages"};
    private static final String[][] ICONES = {Ui.ACCUEIL, Ui.JOUER, Ui.BOUTIQUE, Ui.COLLECTION, Ui.REGLAGES};

    private final Handler h = new Handler(Looper.getMainLooper());
    private final Page[] pages = new Page[N];
    private final LinearLayout[] boutons = new LinearLayout[N];
    private final Ui.Icone[] icones = new Ui.Icone[N];
    private final TextView[] libelles = new TextView[N];
    private FrameLayout contenu, cadre, entete;
    private LinearLayout nav;
    private Vitrine.Bandeau bandeau;
    private TextView pastilleBoutique;
    private View rangees;
    private int courant = -1;
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
        // Bandeau permanent (niveau, XP, po, prochaine rangée) : un toucher ouvre les niveaux.
        entete = new FrameLayout(this);
        entete.setBackgroundColor(Vitrine.NUIT);
        bandeau = new Vitrine.Bandeau(this);
        bandeau.setOnClickListener(v -> allerNiveaux());
        entete.addView(bandeau, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        racine.addView(entete, Ui.large());
        contenu = new FrameLayout(this);
        racine.addView(contenu, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        nav = Ui.rangee(this);
        nav.setBackgroundColor(p.surface);
        nav.setElevation(Ui.dp(this, 8));
        for (int i = 0; i < N; i++) nav.addView(boutonNav(i), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
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
            nav.setPadding(gauche, Ui.dp(this, 6), droite, bas + Ui.dp(this, 6));
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
        w.setNavigationBarColor(p.surface);
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
        Ui.Palette p = Ui.p(this);
        LinearLayout b = Ui.pile(this);
        b.setGravity(Gravity.CENTER_HORIZONTAL);
        b.setPadding(0, Ui.dp(this, 4), 0, Ui.dp(this, 2));
        LinearLayout fond = Ui.rangee(this);
        fond.setGravity(Gravity.CENTER);
        fond.setPadding(Ui.dp(this, 14), Ui.dp(this, 5), Ui.dp(this, 14), Ui.dp(this, 5));
        icones[i] = new Ui.Icone(this, ICONES[i], new int[]{0, p.doux}, 2);
        fond.addView(icones[i]);
        if (i == BOUTIQUE) {
            // Pastille « ! » : une rangée vient de s'ouvrir ou une offre du jour attend.
            pastilleBoutique = Ui.texte(this, "!", 10, Vitrine.ENCRE, true);
            pastilleBoutique.setBackground(Ui.arrondi(this, Vitrine.ORANGE, 8, 0));
            pastilleBoutique.setPadding(Ui.dp(this, 5), 0, Ui.dp(this, 5), 0);
            pastilleBoutique.setVisibility(View.GONE);
            LinearLayout.LayoutParams lpb = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lpb.leftMargin = Ui.dp(this, 3);
            lpb.gravity = Gravity.TOP;
            fond.addView(pastilleBoutique, lpb);
        }
        boutons[i] = fond;
        b.addView(fond);
        libelles[i] = Ui.texte(this, NOMS[i], 12, p.doux, false);
        // Le libellé prend toute la largeur de la case (pile verticale) : il faut centrer son texte.
        libelles[i].setGravity(Gravity.CENTER_HORIZONTAL);
        libelles[i].setSingleLine(true);
        libelles[i].setPadding(0, Ui.dp(this, 3), 0, 0);
        b.addView(libelles[i]);
        b.setContentDescription(NOMS[i]);
        b.setOnClickListener(v -> aller(i, true));
        return b;
    }

    Page page(int i) {
        if (pages[i] == null) {
            switch (i) {
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
        Ui.Palette p = Ui.p(this);
        for (int k = 0; k < N; k++) {
            boolean sel = k == i;
            icones[k].couleurs(new int[]{0, sel ? p.bleu : p.doux});
            boutons[k].setBackground(sel ? Ui.arrondi(this, p.voile | 0x10000000, 16, 0) : null);
            libelles[k].setTextColor(sel ? p.bleu : p.doux);
            libelles[k].setTypeface(null, sel ? android.graphics.Typeface.BOLD : android.graphics.Typeface.NORMAL);
            // L'onglet courant est annoncé « sélectionné » par TalkBack.
            if (boutons[k].getParent() instanceof View) ((View) boutons[k].getParent()).setSelected(sel);
        }
        if (i == courant) {
            page(i).defile.smoothScrollTo(0, 0);
            return;
        }
        Page nouvelle = page(i);
        if (nouvelle.getParent() == null) contenu.addView(nouvelle, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        for (int k = 0; k < N; k++) if (pages[k] != null && k != i) pages[k].setVisibility(View.GONE);
        nouvelle.setVisibility(View.VISIBLE);
        if (anime) {
            nouvelle.setAlpha(0);
            nouvelle.setTranslationY(Ui.dp(this, 14));
            nouvelle.animate().alpha(1).translationY(0).setDuration(190).start();
        }
        courant = i;
        nouvelle.montree();
        majBandeau();
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
        bandeau.mettre(n, xp, e.po < 0 ? -1 : Gains.solde(this, e), titre != null ? titre : Butin.titre(n), Vitrine.prochaineRangee(n, xp));
        boolean neuf = courant != BOUTIQUE && PageBoutique.nouveautes(this, e) > 0;
        pastilleBoutique.setVisibility(neuf ? View.VISIBLE : View.GONE);
        if (boutons[BOUTIQUE].getParent() instanceof View)
            ((View) boutons[BOUTIQUE].getParent()).setContentDescription(neuf ? "Boutique, du nouveau" : "Boutique");
        int vu = Prefs.de(this).getInt("niveauVu", 0);
        if (vu > 0 && n > vu && !Boutique.debloques(vu, n).isEmpty()) montrerRangees(vu, n);
        if (n != vu) Prefs.de(this).edit().putInt("niveauVu", n).apply();
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
        android.graphics.drawable.GradientDrawable g = new android.graphics.drawable.GradientDrawable();
        g.setColor(Vitrine.NUIT);
        g.setStroke(Ui.dp(this, 3), Vitrine.VIOLET_FONCE);
        g.setCornerRadius(Ui.dp(this, 6));
        c.setBackground(g);
        c.setPadding(Ui.dp(this, 18), Ui.dp(this, 18), Ui.dp(this, 18), Ui.dp(this, 16));
        c.addView(new Vitrine.Pixel(this, "NIVEAU " + apres + " !", 4, Vitrine.ORANGE, Vitrine.VIOLET_FONCE, false));
        Vitrine.Pixel sous = new Vitrine.Pixel(this, "RANGÉES DÉBLOQUÉES", 2, Vitrine.VIOLET, Vitrine.ENCRE, false);
        sous.setPadding(0, Ui.dp(this, 10), 0, 0);
        c.addView(sous);
        // Signe et nom insécables : une ligne ne coupe jamais « ▲ Tête » en deux ; au-delà de six rayons, « +N ».
        StringBuilder noms = new StringBuilder();
        for (int i = 0; i < Math.min(6, rayons.size()); i++)
            noms.append(i > 0 ? "   " : "").append(Boutique.signe(rayons.get(i))).append('\u00a0').append(Boutique.nomSlot(rayons.get(i)));
        if (rayons.size() > 6) noms.append("   +").append(rayons.size() - 6);
        TextView t = Ui.texte(this, noms, 14, Vitrine.ARGENT_CLAIR, true);
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
        android.widget.Button voir = Ui.bouton(this, "Voir en boutique", true, v -> {
            fermerRangees();
            allerBoutique(rayons.isEmpty() ? PageBoutique.VITRINE : rayons.get(0));
        });
        voir.setBackground(Ui.touchable(this, Ui.arrondi(this, Vitrine.ORANGE, 6, 0), 6));
        voir.setTextColor(Vitrine.ENCRE);
        b.addView(voir);
        android.widget.Button tard = Ui.bouton(this, "Plus tard", false, v -> fermerRangees());
        tard.setBackground(Ui.touchable(this, Ui.arrondi(this, Vitrine.NUIT3, 6, 0), 6));
        tard.setTextColor(Vitrine.ARGENT_CLAIR);
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
        else if (courant != ACCUEIL) aller(ACCUEIL, true);
        else super.onBackPressed();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (intent.hasExtra(EXTRA_ONGLET)) aller(intent.getIntExtra(EXTRA_ONGLET, ACCUEIL), true);
        lireLien(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        actif = true;
        Veille.demarrer(this);
        tic();
    }

    @Override
    protected void onPause() {
        super.onPause();
        actif = false;
        h.removeCallbacksAndMessages(null);
    }

    private void tic() {
        if (!actif) return;
        if (courant >= 0) pages[courant].rafraichir();
        majBandeau();
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
