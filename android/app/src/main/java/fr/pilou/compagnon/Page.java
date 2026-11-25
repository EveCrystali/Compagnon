package fr.pilou.compagnon;

import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;

/** Une page de l'app (onglet) : un défilement vertical, rafraîchi chaque seconde tant qu'elle est visible. */
abstract class Page extends FrameLayout {
    protected final Principale app;
    protected final LinearLayout corps;
    protected final ScrollView defile;

    Page(Principale app) {
        super(app);
        this.app = app;
        defile = new ScrollView(app);
        defile.setClipToPadding(false);
        defile.setVerticalScrollBarEnabled(false);
        corps = Ui.pile(app);
        int m = Ui.dp(app, 18);
        corps.setPadding(m, Ui.dp(app, 8), m, Ui.dp(app, 24));
        defile.addView(corps);
        addView(defile);
    }

    /** Appelé chaque seconde quand la page est montrée, et à chaque arrivée sur l'onglet. */
    abstract void rafraichir();

    /** L'onglet devient visible. */
    void montree() {
        rafraichir();
    }
}
