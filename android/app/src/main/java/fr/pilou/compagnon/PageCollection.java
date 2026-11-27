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

/** Collection : carnet de pêche, livre de recettes, récompenses, style (accessoires et couleurs), métiers et succès. */
final class PageCollection extends Page {
    private static final String[] ONGLETS = {"Carnet", "Recettes", "Niveaux", "Style", "Métiers"};
    static final int NIVEAUX = 2, STYLE = 3, METIERS = 4;
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

    private final TextView[] onglets = new TextView[ONGLETS.length];
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
        for (int i = 0; i < ONGLETS.length; i++) {
            TextView t = Ui.texte(a, ONGLETS[i], Ui.T_ETIQUETTE, p.doux, true);
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

    void choisir(int i) {
        choisi = i;
        Ui.Palette p = Ui.p(app);
        for (int k = 0; k < ONGLETS.length; k++) {
            onglets[k].setTextColor(k == i ? p.bleu : p.doux);
            onglets[k].setBackground(k == i ? Ui.arrondi(app, p.surface, 11, 0) : null);
        }
        empreinte = "";
        rafraichir();
    }

    @Override
    void rafraichir() {
        Etat e = Prefs.etat(app);
        int n = Gains.niveau(app, e);
        Set<String> carnet = Gains.carnet(app, e), plats = Gains.plats(app, e);
        String nouvelle = choisi + "|" + n + "|" + carnet + "|" + plats + "|" + e.couleur + "|" + e.accessoire + "|" + Gains.stock(app)
                + "|" + Gains.solde(app, e) + "|" + e.objets + "|" + Gains.porte(app, e) + "|" + e.offres + "|" + Gains.achatsEnAttente(app, e)
                + "|" + e.metiers + "|" + e.heures + "|" + e.avance + "|" + e.succes;
        if (nouvelle.equals(empreinte)) return;
        empreinte = nouvelle;
        contenu.removeAllViews();
        switch (choisi) {
            case 1: recettes(e, n, plats); break;
            case 2: recompenses(n); break;
            case 3: style(e, n); break;
            case 4: metiers(e); break;
            default: carnet(n, carnet);
        }
        contenu.setAlpha(0);
        contenu.animate().alpha(1).setDuration(150).start();
    }

    // ---- Carnet

    private void carnet(int n, Set<String> connues) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        tete.addView(Ui.texte(app, connues.size() + " / " + Butin.PRISES.size() + " espèces", Ui.T_CARTE, p.texte, true));
        Ui.Barre b = new Ui.Barre(app);
        b.part(connues.size() / (float) Butin.PRISES.size());
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 8);
        tete.addView(b, lb);
        Map<String, Integer> stock = Gains.stock(app);
        int total = 0;
        for (int v : stock.values()) total += v;
        TextView panier = Ui.texte(app, total == 0 ? "Panier vide." : "Dans le panier : " + total + " ingrédient" + (total > 1 ? "s" : ""), Ui.T_DETAIL, p.doux, false);
        panier.setPadding(0, Ui.dp(app, 8), 0, 0);
        tete.addView(panier);
        TextView legende = Ui.texte(app, "· commun   ◇ peu commun   ◆ rare   ✦ épique   ★ légendaire", Ui.T_ETIQUETTE, p.doux, false);
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
            TextView nom = Ui.texte(app, connue ? x.nom : "???", Ui.T_DETAIL, connue ? p.texte : p.doux, true);
            nom.setGravity(Gravity.CENTER);
            nom.setPadding(0, Ui.dp(app, 6), 0, 0);
            c.addView(nom, Ui.large());
            String sous = Butin.signe(x.rarete) + " " + Butin.nomRarete(x.rarete);
            if (!connue && x.niveauMin > n) sous = "niveau " + x.niveauMin;
            else if (connue && Gains.prises(app, x.id) > 0) sous += " · ×" + Gains.prises(app, x.id);
            TextView s = Ui.texte(app, sous, Ui.T_ETIQUETTE, x.rarete >= Butin.EPIQUE ? p.orange : x.rarete == Butin.RARE ? p.bleu : p.doux, false);
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
        tete.addView(Ui.texte(app, connues + " / " + Butin.RECETTES.size() + " recettes", Ui.T_CARTE, p.texte, true));
        Ui.Barre b = new Ui.Barre(app);
        b.part(connues / (float) Butin.RECETTES.size());
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 8);
        tete.addView(b, lb);
        TextView inv = Ui.texte(app, "Plats inventés : " + inventes, Ui.T_DETAIL, p.doux, false);
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
            t.addView(Ui.texte(app, fait ? r.nom : "???", Ui.T_CORPS, fait ? p.texte : p.doux, true));
            t.addView(Ui.texte(app, verrou ? "dès le niveau " + r.niveauMin : (fait ? "" : "indice : ") + String.join(" + ", r.saveurs) + "  ·  +" + r.xp + " xp", Ui.T_ETIQUETTE, p.doux, false));
            l.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            liste.addView(l, Ui.large());
        }
        contenu.addView(liste, Ui.large());
    }

    // ---- Récompenses

    private void recompenses(int n) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        Etat e = Prefs.etat(app);
        int stade = e.stade > 0 ? e.stade : Acces.stade(n);
        tete.addView(Ui.texte(app, "Niveau " + n + " · " + Butin.titre(n), Ui.T_CARTE, p.texte, true));
        tete.addView(Ui.texte(app, Acces.nomStade(stade) + " · prochain niveau : +" + Acces.poNiveau(n + 1) + " po", Ui.T_DETAIL, p.doux, false));
        TextView explique = Ui.texte(app, "Les niveaux ouvrent l'accès : jeux, objets de la boutique, évolutions. Les objets s'achètent en pièces d'or.", Ui.T_ETIQUETTE, p.doux, false);
        explique.setPadding(0, Ui.dp(app, 6), 0, 0);
        tete.addView(explique);
        contenu.addView(tete, Ui.large(app, 12));
        int nbArticles = 0;
        for (Boutique.Article a : Boutique.CATALOGUE) if (a.niveauMin <= n) nbArticles++;
        prochaineRangee(e, n);
        java.util.List<String[]> lignes = new java.util.ArrayList<>();
        for (Object[] j : Acces.JEUX) lignes.add(new String[]{String.valueOf(j[2]), (String) j[1], "jeu"});
        for (Object[] s : Acces.STADES) if ((Integer) s[0] > 1) lignes.add(new String[]{String.valueOf(s[2]), (String) s[1], "évolution"});
        for (String[] r : Butin.RECOMPENSES) if (r[1].equals("titre")) lignes.add(new String[]{r[0], r[2], "titre"});
        lignes.sort((x, y) -> Integer.compare(Integer.parseInt(x[0]), Integer.parseInt(y[0])));
        LinearLayout liste = Ui.carte(app);
        liste.addView(Ui.texte(app, "◆ Boutique : " + nbArticles + " / " + Boutique.CATALOGUE.size() + " articles dans les rangées ouvertes", Ui.T_CORPS, p.texte, true));
        for (String[] r : lignes) {
            int niv = Integer.parseInt(r[0]);
            boolean ok = niv <= n;
            liste.addView(Ui.separateur(app));
            LinearLayout l = Ui.rangee(app);
            l.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            TextView badge = Ui.pastille(app, ok ? "✓" : String.valueOf(niv), ok ? p.bleu : p.argent);
            badge.setTextSize(13);
            l.addView(badge);
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, r[1], Ui.T_CORPS, ok ? p.texte : p.doux, true));
            t.addView(Ui.texte(app, r[2] + (ok ? " · ouvert" : " · niveau " + niv), Ui.T_ETIQUETTE, p.doux, false));
            l.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            liste.addView(l, Ui.large());
        }
        contenu.addView(liste, Ui.large());
    }

    // ---- Métiers et succès (le temps passé dans chaque activité sur les PC du groupe ; les défis réussis)

    private void metiers(Etat e) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        java.util.List<Metiers.Ligne> lignes = Metiers.lignes(e);
        int commences = 0;
        for (Metiers.Ligne l : lignes) if (l.commence()) commences++;
        tete.addView(Ui.texte(app, commences + " / " + Metiers.TOUS.size() + " métiers commencés", Ui.T_CARTE, p.texte, true));
        TextView explique = Ui.texte(app, Metiers.connus(e)
                ? "Le temps passé dans chaque activité sur tes PC fait monter un métier, de Novice à Légende."
                : "Le PC n'a encore rien envoyé : les métiers et les succès arrivent avec sa prochaine nouvelle.", Ui.T_DETAIL, p.doux, false);
        explique.setPadding(0, Ui.dp(app, 6), 0, 0);
        tete.addView(explique, Ui.large());
        TextView legende = Ui.texte(app, Metiers.TRAVAIL + " travail (paliers 6 → 1500 h)   " + Metiers.LOISIR + " loisir (1 → 250 h)", Ui.T_ETIQUETTE, p.doux, false);
        legende.setPadding(0, Ui.dp(app, 6), 0, 0);
        tete.addView(legende, Ui.large());
        contenu.addView(tete, Ui.large(app, 12));

        LinearLayout liste = Ui.carte(app);
        for (int i = 0; i < lignes.size(); i++) {
            Metiers.Ligne l = lignes.get(i);
            if (i > 0) liste.addView(Ui.separateur(app));
            boolean actif = l.commence();
            int teinte = !actif ? p.argent : l.metier.travail ? p.bleu : p.orange;
            LinearLayout r = Ui.rangee(app);
            r.setGravity(Gravity.TOP);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Ui.pastille(app, l.metier.signe(), teinte));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, l.metier.nom + " · " + l.grade(), Ui.T_CORPS, actif ? p.texte : p.doux, true), Ui.large());
            if (actif && l.dixiemes > 0) {
                Ui.Barre b = new Ui.Barre(app);
                b.part(l.part());
                LinearLayout.LayoutParams lb = Ui.large();
                lb.topMargin = Ui.dp(app, 5);
                lb.bottomMargin = Ui.dp(app, 3);
                t.addView(b, lb);
            }
            t.addView(Ui.texte(app, l.texte(), Ui.T_ETIQUETTE, p.doux, false), Ui.large());
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            r.setAlpha(actif ? 1f : 0.6f);
            r.setContentDescription(l.metier.nom + (l.metier.travail ? ", métier de travail" : ", loisir") + ", " + l.grade() + ", " + l.texte());
            liste.addView(r, Ui.large());
        }
        contenu.addView(liste, Ui.large(app, 12));

        int obtenus = Metiers.obtenus(e);
        LinearLayout tetes = Ui.carte(app);
        tetes.addView(Ui.texte(app, "Succès " + obtenus + "/" + Metiers.SUCCES.size(), Ui.T_CARTE, p.texte, true));
        Ui.Barre bs = new Ui.Barre(app);
        bs.part(obtenus / (float) Metiers.SUCCES.size());
        LinearLayout.LayoutParams lbs = Ui.large();
        lbs.topMargin = Ui.dp(app, 8);
        tetes.addView(bs, lbs);
        contenu.addView(tetes, Ui.large(app, 12));
        LinearLayout succes = Ui.carte(app);
        java.util.List<Metiers.Succes> tries = Metiers.succesTries(e);
        for (int i = 0; i < tries.size(); i++) {
            Metiers.Succes s = tries.get(i);
            if (i > 0) succes.addView(Ui.separateur(app));
            boolean ok = e.succes.contains(s.id);
            Integer a = e.avance.get(s.id);
            String progres = ok || a == null ? "" : Metiers.progres(s, a);
            LinearLayout r = Ui.rangee(app);
            r.setGravity(Gravity.TOP);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Ui.pastille(app, ok ? "✓" : "·", ok ? p.bleu : p.argent));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, s.nom, Ui.T_CORPS, ok ? p.texte : p.doux, true), Ui.large());
            t.addView(Ui.texte(app, s.description + (progres.isEmpty() ? "" : " · " + progres) + "  ·  +" + s.xp + " xp", Ui.T_ETIQUETTE, p.doux, false), Ui.large());
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            r.setContentDescription(s.nom + (ok ? ", obtenu" : ", pas encore") + ", " + s.description + (progres.isEmpty() ? "" : ", " + progres));
            succes.addView(r, Ui.large());
        }
        contenu.addView(succes, Ui.large());
    }

    // ---- Style

    // Prochaine rangée de la boutique : niveau, XP qui manque, aperçu des objets (en silhouette), « Voir en boutique ».
    private void prochaineRangee(Etat e, int n) {
        int palier = Boutique.prochainPalier(n);
        if (palier == 0) return;
        int xp = Gains.xp(app, e);
        LinearLayout c = Ui.carte(app);
        c.setBackground(Ui.arrondi(app, Vitrine.NUIT, 18, Vitrine.VIOLET_FONCE));
        c.addView(new Vitrine.Pixel(app, "PROCHAINE RANGÉE", 2, Vitrine.VIOLET, Vitrine.ENCRE, false));
        java.util.List<String> rayons = Boutique.rayonsDuPalier(palier);
        StringBuilder noms = new StringBuilder();
        for (String r : rayons) noms.append(noms.length() > 0 ? ", " : "").append(Boutique.nomSlot(r));
        TextView t = Ui.texte(app, noms + " — niveau " + palier + " (encore " + Math.max(0, Butin.xpPourNiveau(palier) - xp) + " xp)", Ui.T_DETAIL,
                Vitrine.ARGENT_CLAIR, true);
        t.setPadding(0, Ui.dp(app, 8), 0, Ui.dp(app, 6));
        c.addView(t, Ui.large());
        LinearLayout r = Ui.rangee(app);
        float d = app.getResources().getDisplayMetrics().density;
        int k = 0;
        for (Boutique.Article a : Boutique.CATALOGUE) {
            if (a.niveauMin != palier || !Boutique.surPilou(a.slot) || k >= 4) continue;
            ImageView im = new ImageView(app);
            im.setImageBitmap(Vitrine.pilou(Vitrine.allure(a, 0), 1.1f * d, true));
            im.setContentDescription(a.nom + ", rangée du niveau " + palier);
            r.addView(im, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            k++;
        }
        c.addView(r, Ui.large());
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 10);
        c.addView(Ui.bouton(app, "Voir en boutique", true, v -> app.allerBoutique(rayons.isEmpty() ? PageBoutique.VITRINE : rayons.get(0))), lb);
        contenu.addView(c, Ui.large(app, 12));
    }

    private void style(Etat e, int n) {
        Ui.Palette p = Ui.p(app);
        LinearLayout tete = Ui.carte(app);
        tete.setGravity(Gravity.CENTER_HORIZONTAL);
        ImageView actuel = new ImageView(app);
        actuel.setImageBitmap(Dessin.image("repos", e.couleur, e.accessoire, 5));
        tete.addView(actuel);
        TextView t = Ui.texte(app, "Ce que tu possèdes s'achète à la Boutique (pièces d'or) ; Pilou porte ce que tu choisis.", Ui.T_DETAIL, p.doux, false);
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
            String cle = accessoires ? ACCESSOIRES.getOrDefault(r[2], "aucun") : COULEURS.getOrDefault(r[2], "bleu");
            // Possédé : acheté à la boutique (ou déjà acquis avant la boutique) ; le bleu de base, toujours.
            boolean ok = !accessoires && cle.equals("bleu") || e.objets.contains(accessoires ? cle : "couleur-" + cle);
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
            TextView nom = Ui.texte(app, r[2], Ui.T_ETIQUETTE, ok ? p.texte : p.doux, true);
            nom.setGravity(Gravity.CENTER);
            c.addView(nom, Ui.large());
            TextView sous = Ui.texte(app, porte ? "● porté" : ok ? "✓ à toi" : niv > n ? "◇ niveau " + niv : "◆ boutique", Ui.T_ETIQUETTE, porte ? p.bleu : p.doux, false);
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
