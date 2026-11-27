package fr.pilou.compagnon;

import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Jouer : « Chasse aux bugs » en vedette, puis les jeux de l'atelier (pêche, cuisine, étoile, bulles, tape m'en cinq). */
final class PageJouer extends Page {
    private final TextView record, resume, cuisine;
    private final Apercu apercu;

    PageJouer(Principale a) {
        super(a);
        Ui.Palette p = Ui.p(a);
        corps.addView(Ui.titrePage(a, "Jouer"));
        resume = Ui.sousTitre(a, "");
        corps.addView(resume);

        // En vedette : Chasse aux bugs.
        LinearLayout vedette = Ui.carte(a);
        vedette.setPadding(0, 0, 0, Ui.dp(a, 16));
        vedette.setClipToOutline(true);
        apercu = new Apercu(a);
        vedette.addView(apercu, Ui.large());
        LinearLayout infos = Ui.pile(a);
        infos.setPadding(Ui.dp(a, 16), Ui.dp(a, 14), Ui.dp(a, 16), 0);
        LinearLayout ligneTitre = Ui.rangee(a);
        ligneTitre.addView(Ui.texte(a, "Chasse aux bugs", Ui.T_CARTE, p.texte, true), new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        ligneTitre.addView(Ui.puceTexte(a, "NOUVEAU", p.orange));
        infos.addView(ligneTitre, Ui.large());
        infos.addView(Ui.texte(a, "Des vagues de bugs descendent vers la prod. Glisse pour bouger Pilou, il tire tout seul. "
                + "Café : tir rapide. ✓ Tests : bouclier. Toutes les 5 vagues, le Bug de prod.", Ui.T_DETAIL, p.doux, false));
        record = Ui.texte(a, "", Ui.T_DETAIL, p.bleu, true);
        record.setPadding(0, Ui.dp(a, 8), 0, Ui.dp(a, 12));
        infos.addView(record);
        boutonChasse = Ui.bouton(a, "Jouer", true, v -> ouvrirChasse());
        infos.addView(boutonChasse, Ui.large());
        vedette.addView(infos, Ui.large());
        vedette.setOnClickListener(v -> ouvrirChasse());
        corps.addView(vedette, Ui.large(a, 6));

        corps.addView(Ui.titreSection(a, "L'atelier de Pilou"));
        cuisine = Ui.texte(a, "", Ui.T_DETAIL, p.doux, false);
        Object[][] jeux = {
                {"Pêche", "Touche le bouchon quand il plonge", Ui.PECHE, new int[]{0, p.bleu, p.orange, p.argent, p.orange}, "peche"},
                {"Cuisine", cuisine, Ui.CUISINE, new int[]{0, p.argent, p.bleu, p.orange}, "cuisine"},
                {"Étoile filante", "Attrape-la au vol", Ui.ETOILE, new int[]{0, p.orange, 0, p.bleu}, "etoile"},
                {"Bulles", "Éclate les trois bulles", Ui.BULLES, new int[]{0, p.bleu, p.argent}, "bulles"},
                {"Tape m'en cinq", "Au bon moment !", Ui.TAPE, new int[]{0, p.orange}, "tape"},
                {"Collection", "Carnet, recettes, récompenses", Ui.COLLECTION, new int[]{0, p.bleu}, ""}};
        LinearLayout rang = null;
        for (int i = 0; i < jeux.length; i++) {
            if (i % 2 == 0) {
                rang = Ui.rangee(a);
                rang.setGravity(Gravity.TOP);
                corps.addView(rang, Ui.large(a, 12));
            }
            Object[] j = jeux[i];
            LinearLayout c = Ui.carte(a);
            c.addView(new Ui.Icone(a, (String[]) j[2], (int[]) j[3], 3));
            TextView t = Ui.texte(a, (String) j[0], Ui.T_CORPS, p.texte, true);
            t.setPadding(0, Ui.dp(a, 10), 0, Ui.dp(a, 2));
            c.addView(t);
            if (j[1] instanceof TextView) c.addView((TextView) j[1]);
            else c.addView(Ui.texte(a, (String) j[1], Ui.T_DETAIL, p.doux, false));
            String jeu = (String) j[4];
            c.setBackground(Ui.touchable(a, Ui.arrondi(a, p.surface, 18, p.bord), 18));
            c.setOnClickListener(v -> {
                if (jeu.isEmpty()) a.aller(Principale.COLLECTION, true);
                else if (!Acces.jeuOuvert(jeu, niveau())) verrou(jeu);
                else a.startActivity(new Intent(a, Atelier.class).putExtra(Atelier.EXTRA_JEU, jeu));
            });
            if (!jeu.isEmpty()) {
                TextView v = Ui.texte(a, "", Ui.T_ETIQUETTE, p.orange, true);
                c.addView(v);
                verrous.put(jeu, new View[]{c, v});
            }
            LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
            if (i % 2 == 0) l.rightMargin = Ui.dp(a, 6);
            else l.leftMargin = Ui.dp(a, 6);
            rang.addView(c, l);
        }
        TextView note = Ui.texte(a, "Tout ce que Pilou gagne ici (XP, prises, plats) part vers ton PC, qui garde la progression.", Ui.T_DETAIL, p.doux, false);
        note.setPadding(Ui.dp(a, 4), Ui.dp(a, 6), Ui.dp(a, 4), 0);
        corps.addView(note);
    }

    private final java.util.Map<String, View[]> verrous = new java.util.HashMap<>();
    private android.widget.Button boutonChasse;

    private int niveau() {
        return Gains.niveau(app, Prefs.etat(app));
    }

    private void verrou(String jeu) {
        android.widget.Toast.makeText(app, Acces.nomJeu(jeu) + " s'ouvre au niveau " + Acces.niveauJeu(jeu), android.widget.Toast.LENGTH_SHORT).show();
    }

    private void ouvrirChasse() {
        if (!Acces.jeuOuvert("chasse", niveau())) verrou("chasse");
        else app.startActivity(new Intent(app, ActiviteChasse.class));
    }

    @Override
    void rafraichir() {
        Etat e = Prefs.etat(app);
        int total = Gains.xp(app, e), n = Gains.niveau(app, e);
        for (java.util.Map.Entry<String, View[]> v : verrous.entrySet()) {
            boolean ouvert = Acces.jeuOuvert(v.getKey(), n);
            v.getValue()[0].setAlpha(ouvert ? 1f : 0.55f);
            ((TextView) v.getValue()[1]).setText(ouvert ? "" : "◇ niveau " + Acces.niveauJeu(v.getKey()));
        }
        if (boutonChasse != null) boutonChasse.setText(Acces.jeuOuvert("chasse", n) ? "Jouer" : "Niveau " + Acces.niveauJeu("chasse"));
        resume.setText("Niveau " + n + " · " + total + " xp · tes gains remontent au PC");
        int meilleur = Prefs.meilleurChasse(app);
        record.setText(meilleur > 0 ? "Record : " + meilleur : "Pas encore de record");
        int stock = 0;
        for (int v : Gains.stock(app).values()) stock += v;
        cuisine.setText(stock == 0 ? "Panier vide : va pêcher d'abord" : stock + " ingrédient" + (stock > 1 ? "s" : "") + " dans le panier");
    }

    @Override
    protected void onVisibilityChanged(View v, int visibilite) {
        super.onVisibilityChanged(v, visibilite);
        if (apercu != null) apercu.anime(visibilite == VISIBLE && isShown());
    }

    /** Petite partie qui se joue toute seule, en aperçu (Pilou vise le bug le plus proche). */
    static final class Apercu extends View {
        private final Chasse c = new Chasse(SystemClock.uptimeMillis());
        private final Paint pt = new Paint();
        private long dernier;
        private boolean anime = true;

        Apercu(Context ctx) {
            super(ctx);
            c.immortel = true;
            c.commencer();
        }

        void anime(boolean oui) {
            anime = oui;
            dernier = 0;
            invalidate();
        }

        @Override
        protected void onMeasure(int l, int h) {
            int w = MeasureSpec.getSize(l);
            setMeasuredDimension(w, Ui.dp(getContext(), 170));
        }

        @Override
        protected void onDraw(Canvas cv) {
            long t = SystemClock.uptimeMillis();
            float dt = dernier == 0 ? 0.016f : (t - dernier) / 1000f;
            dernier = t;
            Chasse.Bug cible = null;
            for (Chasse.Bug b : c.bugs) if (b.vivant && (cible == null || b.y > cible.y)) cible = b;
            if (cible != null) c.viser(cible.x + Chasse.Bug.L / 2 + (float) Math.sin(t / 700.0) * 6);
            else if (c.boss != null) c.viser(c.boss.x + Chasse.Boss.L / 2);
            c.avancer(dt);
            c.evenements();
            if (c.phase == Chasse.Phase.FIN || c.vague > 3) c.commencer();
            // Le monde (120 × 200) est cadré sur sa moitié basse, à la largeur de la carte.
            float k = getWidth() / Chasse.W, oy = getHeight() - Chasse.H * k;
            cv.save();
            cv.clipRect(0, 0, getWidth(), getHeight());
            ChasseDessin.dessiner((g, hh, d, b, col) -> {
                pt.setColor(col);
                cv.drawRect(g, hh, d, b, pt);
            }, c, 0, oy, k, t, 0);
            cv.restore();
            if (anime) postInvalidateDelayed(33);
        }
    }
}
