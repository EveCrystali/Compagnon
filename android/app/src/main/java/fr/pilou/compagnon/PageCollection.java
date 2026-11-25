package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/** Collection : carnet de pêche, livre de recettes, récompenses, style (accessoires et couleurs). */
final class PageCollection extends Page {
    private static final String[] ONGLETS = {"Carnet", "Recettes", "Récompenses", "Style"};
    static final Map<String, String> ACCESSOIRES = new HashMap<>(), COULEURS = new HashMap<>();

    static {
        String[] a = {"Feuille d'automne", "feuille", "Nœud papillon", "noeud", "Casque audio", "casque", "Bonnet de laine", "bonnet",
                "Lunettes de soleil", "lunettes", "Couronne", "couronne", "Chapeau de pêcheur", "chapeaupeche", "Toque de chef", "toque",
                "Tablier", "tablier", "Étoile de mer", "etoilemer"};
        for (int i = 0; i < a.length; i += 2) ACCESSOIRES.put(a[i], a[i + 1]);
        String[] c = {"Bleu ciel", "bleu", "Bleu nuit", "nuit", "Ambre", "ambre", "Argent", "argent", "Aurore", "aurore", "Lagon", "lagon",
                "Braise", "braise", "Nacre", "nacre", "Abysse", "abysse", "Comète", "comete"};
        for (int i = 0; i < c.length; i += 2) COULEURS.put(c[i], c[i + 1]);
    }

    private final TextView[] onglets = new TextView[4];
    private final LinearLayout contenu;
    private int choisi = 0;
    private String empreinte = "";

    PageCollection(Principale a) {
        super(a);
        corps.addView(Ui.titrePage(a, "Collection"));
        corps.addView(Ui.sousTitre(a, "Ce que Pilou a pêché, cuisiné et débloqué."));
        LinearLayout segments = Ui.rangee(a);
        Ui.Palette p = Ui.p(a);
        segments.setBackground(Ui.arrondi(a, p.surface2, 14, 0));
        segments.setPadding(Ui.dp(a, 4), Ui.dp(a, 4), Ui.dp(a, 4), Ui.dp(a, 4));
        for (int i = 0; i < 4; i++) {
            TextView t = Ui.texte(a, ONGLETS[i], 13, p.doux, true);
            t.setGravity(Gravity.CENTER);
            t.setPadding(0, Ui.dp(a, 9), 0, Ui.dp(a, 9));
            int k = i;
            t.setOnClickListener(v -> choisir(k));
            onglets[i] = t;
            segments.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        }
        corps.addView(segments, Ui.large(a, 14));
        contenu = Ui.pile(a);
        corps.addView(contenu, Ui.large());
        choisir(0);
    }

    private void choisir(int i) {
        choisi = i;
        Ui.Palette p = Ui.p(app);
        for (int k = 0; k < 4; k++) {
            onglets[k].setTextColor(k == i ? p.bleu : p.doux);
            onglets[k].setBackground(k == i ? Ui.arrondi(app, p.surface, 11, 0) : null);
        }
        empreinte = "";
        rafraichir();
    }

    @Override
    void rafraichir() {
        Etat e = Prefs.etat(app);
        int n = Butin.niveau(Gains.xp(app, e));
        Set<String> carnet = Gains.carnet(app, e), plats = Gains.plats(app, e);
        String nouvelle = choisi + "|" + n + "|" + carnet + "|" + plats + "|" + e.couleur + "|" + e.accessoire + "|" + Gains.stock(app);
        if (nouvelle.equals(empreinte)) return;
        empreinte = nouvelle;
        contenu.removeAllViews();
        switch (choisi) {
            case 1: recettes(e, n, plats); break;
            case 2: recompenses(n); break;
            case 3: style(e, n); break;
            default: carnet(n, carnet);
        }
        contenu.setAlpha(0);
        contenu.animate().alpha(1).setDuration(150).start();
    }

    // ---- Carnet

    private void carnet(int n, Set<String> connues) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        tete.addView(Ui.texte(app, connues.size() + " / " + Butin.PRISES.size() + " espèces", 18, p.texte, true));
        Ui.Barre b = new Ui.Barre(app);
        b.part(connues.size() / (float) Butin.PRISES.size());
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 8);
        tete.addView(b, lb);
        Map<String, Integer> stock = Gains.stock(app);
        int total = 0;
        for (int v : stock.values()) total += v;
        TextView panier = Ui.texte(app, total == 0 ? "Panier vide." : "Dans le panier : " + total + " ingrédient" + (total > 1 ? "s" : ""), 13, p.doux, false);
        panier.setPadding(0, Ui.dp(app, 8), 0, 0);
        tete.addView(panier);
        TextView legende = Ui.texte(app, "· commun   ◇ peu commun   ◆ rare   ✦ épique   ★ légendaire", 12, p.doux, false);
        legende.setPadding(0, Ui.dp(app, 6), 0, 0);
        tete.addView(legende);
        contenu.addView(tete, Ui.large(app, 12));

        LinearLayout rang = null;
        for (int i = 0; i < Butin.PRISES.size(); i++) {
            if (i % 3 == 0) {
                rang = Ui.rangee(app);
                rang.setGravity(Gravity.TOP);
                contenu.addView(rang, Ui.large(app, 10));
            }
            Butin.Prise x = Butin.PRISES.get(i);
            boolean connue = connues.contains(x.id);
            LinearLayout c = Ui.carte(app);
            c.setGravity(Gravity.CENTER_HORIZONTAL);
            c.setPadding(Ui.dp(app, 6), Ui.dp(app, 10), Ui.dp(app, 6), Ui.dp(app, 10));
            c.addView(new Vignette(app, x, connue));
            TextView nom = Ui.texte(app, connue ? x.nom : "???", 13, connue ? p.texte : p.doux, true);
            nom.setGravity(Gravity.CENTER);
            nom.setPadding(0, Ui.dp(app, 6), 0, 0);
            c.addView(nom, Ui.large());
            String sous = Butin.signe(x.rarete) + " " + Butin.nomRarete(x.rarete);
            if (!connue && x.niveauMin > n) sous = "niveau " + x.niveauMin;
            else if (connue && Gains.prises(app, x.id) > 0) sous += " · ×" + Gains.prises(app, x.id);
            TextView s = Ui.texte(app, sous, 11, x.rarete >= Butin.EPIQUE ? p.orange : x.rarete == Butin.RARE ? p.bleu : p.doux, false);
            s.setGravity(Gravity.CENTER);
            c.addView(s, Ui.large());
            LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
            l.leftMargin = i % 3 == 0 ? 0 : Ui.dp(app, 5);
            l.rightMargin = i % 3 == 2 ? 0 : Ui.dp(app, 5);
            rang.addView(c, l);
        }
        // Compléter la dernière rangée pour garder la grille.
        int reste = (3 - Butin.PRISES.size() % 3) % 3;
        for (int i = 0; i < reste && rang != null; i++) rang.addView(new View(app), new LinearLayout.LayoutParams(0, 1, 1));
    }

    /** Sprite d'une prise, cadre selon la rareté (aucun, coins, trait, double, étoilé) ; silhouette si inconnue. */
    static final class Vignette extends View {
        private final Butin.Prise x;
        private final boolean connue;
        private final Paint pt = new Paint();

        Vignette(Context c, Butin.Prise x, boolean connue) {
            super(c);
            this.x = x;
            this.connue = connue;
        }

        @Override
        protected void onMeasure(int l, int h) {
            int d = Ui.dp(getContext(), 64);
            setMeasuredDimension(d, d);
        }

        @Override
        protected void onDraw(Canvas cv) {
            Ui.Palette p = Ui.p(getContext());
            String[] m = Terrain.sprite(x.forme);
            float s = Math.min(getWidth() / 20f, getHeight() / 20f);
            float ox = (getWidth() - m[0].length() * s) / 2, oy = (getHeight() - m.length * s) / 2;
            Dessin.Peintre pe = (g, hh, d, b, col) -> {
                pt.setColor(col);
                cv.drawRect(g, hh, d, b, pt);
            };
            int cadre = x.rarete >= Butin.EPIQUE ? p.orange : x.rarete == Butin.RARE ? p.bleu : p.argent;
            float g = s, d = getWidth() - s, h = s, b = getHeight() - s;
            if (x.rarete == Butin.PEU_COMMUN)
                for (float[] k : new float[][]{{g, h}, {d - 3 * s, h}, {g, b - s}, {d - 3 * s, b - s}}) pe.rect(k[0], k[1], k[0] + 3 * s, k[1] + s, cadre);
            if (x.rarete >= Butin.RARE) contour(pe, g, h, d, b, s, cadre);
            if (x.rarete >= Butin.EPIQUE) contour(pe, g + 2 * s, h + 2 * s, d - 2 * s, b - 2 * s, s, cadre);
            if (x.rarete == Butin.LEGENDAIRE)
                for (float[] k : new float[][]{{0, 0}, {getWidth() - 3 * s, 0}, {0, getHeight() - 3 * s}, {getWidth() - 3 * s, getHeight() - 3 * s}})
                    Police.motif(pe, new String[]{"010", "111", "010"}, k[0], k[1], s, new int[]{0, 0xffffd8b0});
            int[] pal = connue ? new int[]{0, 0xff1c2128, x.couleur, x.clair, x.detail} : new int[]{0, p.bord, p.bord, p.bord, p.bord};
            Police.motif(pe, m, ox, oy, s, pal);
        }

        private static void contour(Dessin.Peintre pe, float g, float h, float d, float b, float s, int c) {
            pe.rect(g, h, d, h + s, c);
            pe.rect(g, b - s, d, b, c);
            pe.rect(g, h, g + s, b, c);
            pe.rect(d - s, h, d, b, c);
        }
    }

    // ---- Recettes

    private void recettes(Etat e, int n, Set<String> faits) {
        Ui.Palette p = Ui.p(app);
        int inventes = e.inventes, connues = 0;
        for (String f : faits) if (f.startsWith("inv:")) inventes++;
        for (Butin.Recette r : Butin.RECETTES) if (faits.contains(r.id)) connues++;
        LinearLayout tete = Ui.carte(app);
        tete.addView(Ui.texte(app, connues + " / " + Butin.RECETTES.size() + " recettes", 18, p.texte, true));
        Ui.Barre b = new Ui.Barre(app);
        b.part(connues / (float) Butin.RECETTES.size());
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 8);
        tete.addView(b, lb);
        TextView inv = Ui.texte(app, "Plats inventés : " + inventes, 13, p.doux, false);
        inv.setPadding(0, Ui.dp(app, 8), 0, 0);
        tete.addView(inv);
        contenu.addView(tete, Ui.large(app, 12));
        LinearLayout liste = Ui.carte(app);
        for (int i = 0; i < Butin.RECETTES.size(); i++) {
            Butin.Recette r = Butin.RECETTES.get(i);
            if (i > 0) liste.addView(Ui.separateur(app));
            boolean fait = faits.contains(r.id), verrou = !fait && r.niveauMin > n;
            LinearLayout l = Ui.rangee(app);
            l.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            l.addView(Ui.pastille(app, fait ? "✓" : verrou ? "·" : "?", fait ? p.bleu : p.argent));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, fait ? r.nom : "???", 15, fait ? p.texte : p.doux, true));
            t.addView(Ui.texte(app, verrou ? "dès le niveau " + r.niveauMin : (fait ? "" : "indice : ") + String.join(" + ", r.saveurs) + "  ·  +" + r.xp + " xp", 12, p.doux, false));
            l.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            liste.addView(l, Ui.large());
        }
        contenu.addView(liste, Ui.large());
    }

    // ---- Récompenses

    private void recompenses(int n) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        tete.addView(Ui.texte(app, "Niveau " + n + " · " + Butin.titre(n), 18, p.texte, true));
        int suivant = 0;
        for (String[] r : Butin.RECOMPENSES) if (Integer.parseInt(r[0]) > n) { suivant = Integer.parseInt(r[0]); break; }
        tete.addView(Ui.texte(app, suivant == 0 ? "Tout est débloqué : Pilou éternel !" : "Prochaine récompense au niveau " + suivant, 13, p.doux, false));
        contenu.addView(tete, Ui.large(app, 12));
        LinearLayout liste = Ui.carte(app);
        for (int i = 0; i < Butin.RECOMPENSES.length; i++) {
            String[] r = Butin.RECOMPENSES[i];
            int niv = Integer.parseInt(r[0]);
            boolean ok = niv <= n;
            if (i > 0) liste.addView(Ui.separateur(app));
            LinearLayout l = Ui.rangee(app);
            l.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            TextView badge = Ui.pastille(app, ok ? "✓" : String.valueOf(niv), ok ? p.bleu : p.argent);
            badge.setTextSize(13);
            l.addView(badge);
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, r[2], 15, ok ? p.texte : p.doux, true));
            t.addView(Ui.texte(app, r[1] + (ok ? " · débloqué" : " · niveau " + niv), 12, r[1].equals("effet") && ok ? p.orange : p.doux, false));
            l.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            liste.addView(l, Ui.large());
        }
        contenu.addView(liste, Ui.large());
    }

    // ---- Style

    private void style(Etat e, int n) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        tete.setGravity(Gravity.CENTER_HORIZONTAL);
        ImageView actuel = new ImageView(app);
        actuel.setImageBitmap(Dessin.image("repos", e.couleur, e.accessoire, 5));
        tete.addView(actuel);
        TextView t = Ui.texte(app, "Pilou porte ce que tu as choisi sur le PC (clic droit sur Pilou → Accessoire, Couleur).", 13, p.doux, false);
        t.setGravity(Gravity.CENTER);
        tete.addView(t, Ui.large());
        contenu.addView(tete, Ui.large(app, 6));
        contenu.addView(Ui.titreSection(app, "Accessoires"));
        grille(n, "accessoire", e, true);
        contenu.addView(Ui.titreSection(app, "Couleurs"));
        grille(n, "couleur", e, false);
    }

    private void grille(int n, String type, Etat e, boolean accessoires) {
        Ui.Palette p = Ui.p(app);
        LinearLayout rang = null;
        int i = 0;
        for (String[] r : Butin.RECOMPENSES) {
            if (!r[1].equals(type)) continue;
            if (i % 3 == 0) {
                rang = Ui.rangee(app);
                rang.setGravity(Gravity.TOP);
                contenu.addView(rang, Ui.large(app, 10));
            }
            int niv = Integer.parseInt(r[0]);
            boolean ok = niv <= n;
            String cle = accessoires ? ACCESSOIRES.getOrDefault(r[2], "aucun") : COULEURS.getOrDefault(r[2], "bleu");
            boolean porte = accessoires ? cle.equals(e.accessoire) : cle.equals(e.couleur);
            LinearLayout c = Ui.carte(app);
            c.setGravity(Gravity.CENTER_HORIZONTAL);
            c.setPadding(Ui.dp(app, 6), Ui.dp(app, 8), Ui.dp(app, 6), Ui.dp(app, 10));
            if (porte) c.setBackground(Ui.arrondi(app, p.surface, 18, p.bleu));
            ImageView img = new ImageView(app);
            Bitmap bm = Dessin.image("repos", accessoires ? e.couleur : cle, accessoires ? cle : e.accessoire, 2);
            img.setImageBitmap(bm);
            img.setAlpha(ok ? 1f : 0.3f);
            c.addView(img);
            TextView nom = Ui.texte(app, r[2], 12, ok ? p.texte : p.doux, true);
            nom.setGravity(Gravity.CENTER);
            c.addView(nom, Ui.large());
            TextView sous = Ui.texte(app, porte ? "● porté" : ok ? "✓ débloqué" : "niveau " + niv, 11, porte ? p.bleu : p.doux, false);
            sous.setGravity(Gravity.CENTER);
            c.addView(sous, Ui.large());
            LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
            l.leftMargin = i % 3 == 0 ? 0 : Ui.dp(app, 5);
            l.rightMargin = i % 3 == 2 ? 0 : Ui.dp(app, 5);
            rang.addView(c, l);
            i++;
        }
        int reste = (3 - i % 3) % 3;
        for (int k = 0; k < reste && rang != null; k++) rang.addView(new View(app), new LinearLayout.LayoutParams(0, 1, 1));
    }
}
