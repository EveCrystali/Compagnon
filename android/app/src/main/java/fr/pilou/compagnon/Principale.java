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
 * L'app Pilou : une seule activité, quatre onglets (Accueil, Jouer, Collection, Réglages) et une barre de
 * navigation en bas. Bord à bord : le contenu passe sous les barres système, décalé de leur hauteur.
 */
public final class Principale extends Activity {
    static final int ACCUEIL = 0, JOUER = 1, COLLECTION = 2, REGLAGES = 3;
    static final String EXTRA_ONGLET = "onglet";
    private static final String[] NOMS = {"Accueil", "Jouer", "Collection", "Réglages"};
    private static final String[][] ICONES = {Ui.ACCUEIL, Ui.JOUER, Ui.COLLECTION, Ui.REGLAGES};

    private final Handler h = new Handler(Looper.getMainLooper());
    private final Page[] pages = new Page[4];
    private final LinearLayout[] boutons = new LinearLayout[4];
    private final Ui.Icone[] icones = new Ui.Icone[4];
    private final TextView[] libelles = new TextView[4];
    private FrameLayout contenu;
    private LinearLayout nav;
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
        contenu = new FrameLayout(this);
        racine.addView(contenu, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        nav = Ui.rangee(this);
        nav.setBackgroundColor(p.surface);
        nav.setElevation(Ui.dp(this, 8));
        for (int i = 0; i < 4; i++) nav.addView(boutonNav(i), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
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
            contenu.setPadding(gauche, haut, droite, 0);
            nav.setPadding(gauche, Ui.dp(this, 6), droite, bas + Ui.dp(this, 6));
            return ins;
        });
        setContentView(racine);
        // Après setContentView : la fenêtre (DecorView) existe, son contrôleur des barres système aussi.
        bordABord(w, p);

        int onglet = sauve != null ? sauve.getInt(EXTRA_ONGLET, ACCUEIL) : getIntent().getIntExtra(EXTRA_ONGLET, ACCUEIL);
        aller(onglet, false);
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
                c.setSystemBarsAppearance(clair ? f : 0, f);
            }
        } else {
            int f = View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN;
            if (clair) f |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
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
        fond.setPadding(Ui.dp(this, 18), Ui.dp(this, 5), Ui.dp(this, 18), Ui.dp(this, 5));
        icones[i] = new Ui.Icone(this, ICONES[i], new int[]{0, p.doux}, 2);
        fond.addView(icones[i]);
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
                case COLLECTION: pages[i] = new PageCollection(this); break;
                case REGLAGES: pages[i] = new PageReglages(this); break;
                default: pages[i] = new PageAccueil(this);
            }
        }
        return pages[i];
    }

    /** Va à l'onglet i (fondu et léger glissement). */
    void aller(int i, boolean anime) {
        if (i < 0 || i > 3) i = ACCUEIL;
        Ui.Palette p = Ui.p(this);
        for (int k = 0; k < 4; k++) {
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
        for (int k = 0; k < 4; k++) if (pages[k] != null && k != i) pages[k].setVisibility(View.GONE);
        nouvelle.setVisibility(View.VISIBLE);
        if (anime) {
            nouvelle.setAlpha(0);
            nouvelle.setTranslationY(Ui.dp(this, 14));
            nouvelle.animate().alpha(1).translationY(0).setDuration(190).start();
        }
        courant = i;
        nouvelle.montree();
    }

    @Override
    protected void onSaveInstanceState(Bundle b) {
        super.onSaveInstanceState(b);
        b.putInt(EXTRA_ONGLET, courant);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (courant != ACCUEIL) aller(ACCUEIL, true);
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
