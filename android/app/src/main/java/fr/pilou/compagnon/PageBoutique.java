package fr.pilou.compagnon;

import android.animation.ObjectAnimator;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.drawable.GradientDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/**
 * Boutique rétro (gratuite, aucune vraie monnaie) : enseigne néon, cabine d'essayage, onglets par rayon,
 * étagères par rangée de niveau. Le niveau ouvre la rangée, les pièces d'or achètent ; le PC vérifie et applique.
 * Chaque état a un signe de forme : ▣ fermé (« NIV 15 »), ◉ achetable, ◌ trop cher, ✓ à toi, ★ porté, ⇢ en route,
 * ⌛ saison (jours restants ou « revient »), ✧ de passage. Rareté : lisere de couleur et signe (· ◇ ◆ ✦ ★ ✺).
 * Onglet « Ensembles » (progression 3/6, bonus porté) et compteur de collection sous l'enseigne.
 */
final class PageBoutique extends Page {
    static final String VITRINE = "vitrine";

    private final LinearLayout onglets, etageres;
    private final FrameLayout scene;
    private final ImageView decor;
    private final PilouVue essai;
    private final TextView bulleEssai, nom, detail, message, collection;
    private final LinearLayout jauge;
    private final Button essayer, acheter, porter;
    private final LinearLayout cabine;
    private String rayon = VITRINE, choisi = "", empreinte = "";
    private boolean essaiActif = true;
    private int vuAvant = -1;

    PageBoutique(Principale a) {
        super(a);
        // Enseigne : « BOUTIQUE » en néon pixel sur fond nuit.
        LinearLayout enseigne = Ui.pile(a);
        enseigne.setGravity(Gravity.CENTER_HORIZONTAL);
        enseigne.setBackground(cadre(a, Vitrine.NUIT, Vitrine.VIOLET_FONCE, 3));
        enseigne.setPadding(Ui.dp(a, 12), Ui.dp(a, 16), Ui.dp(a, 12), Ui.dp(a, 12));
        enseigne.addView(new Vitrine.Pixel(a, "BOUTIQUE", 4.2f, Vitrine.ORANGE, Vitrine.VIOLET_FONCE, true));
        TextView sous = Ui.texte(a, "Ton niveau ouvre les rangées, tes pièces d'or achètent. Tout est gratuit : les po se gagnent en quêtes.", Ui.T_ETIQUETTE, Vitrine.ARGENT, false);
        sous.setGravity(Gravity.CENTER);
        sous.setPadding(0, Ui.dp(a, 10), 0, 0);
        enseigne.addView(sous, Ui.large());
        collection = Ui.texte(a, "", Ui.T_DETAIL, Vitrine.ARGENT_CLAIR, true);
        collection.setGravity(Gravity.CENTER);
        collection.setPadding(0, Ui.dp(a, 8), 0, Ui.dp(a, 4));
        enseigne.addView(collection, Ui.large());
        jauge = Ui.rangee(a);
        jauge.setGravity(Gravity.CENTER);
        jauge.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        enseigne.addView(jauge, Ui.large());
        corps.addView(enseigne, Ui.large(a, 12));

        // Cabine d'essayage : décor, Pilou avec l'objet essayé, boutons.
        cabine = Ui.pile(a);
        cabine.setBackground(cadre(a, Vitrine.NUIT, Vitrine.NUIT3, 2));
        cabine.setPadding(Ui.dp(a, 12), Ui.dp(a, 12), Ui.dp(a, 12), Ui.dp(a, 12));
        cabine.addView(new Vitrine.Pixel(a, "ESSAYAGE", 2, Vitrine.VIOLET, Vitrine.ENCRE, false));
        scene = new FrameLayout(a);
        scene.setBackgroundColor(Vitrine.CIEL);
        scene.setClipChildren(true);
        decor = new ImageView(a);
        decor.setScaleType(ImageView.ScaleType.CENTER_CROP);
        scene.addView(decor, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        essai = new PilouVue(a, 3.2f * a.getResources().getDisplayMetrics().density, true);
        essai.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        scene.addView(essai, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER_HORIZONTAL | Gravity.BOTTOM));
        bulleEssai = Ui.texte(a, "ça te va bien !", Ui.T_ETIQUETTE, Vitrine.ENCRE, false);
        bulleEssai.setPadding(Ui.dp(a, 10), Ui.dp(a, 4), Ui.dp(a, 10), Ui.dp(a, 5));
        bulleEssai.setVisibility(View.GONE);
        FrameLayout.LayoutParams lbu = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER_HORIZONTAL | Gravity.TOP);
        lbu.topMargin = Ui.dp(a, 8);
        scene.addView(bulleEssai, lbu);
        LinearLayout.LayoutParams ls = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(a, 210));
        ls.topMargin = Ui.dp(a, 8);
        cabine.addView(scene, ls);
        nom = Ui.texte(a, "", Ui.T_CARTE, Vitrine.ARGENT_CLAIR, true);
        nom.setPadding(0, Ui.dp(a, 10), 0, 0);
        cabine.addView(nom, Ui.large());
        detail = Ui.texte(a, "", Ui.T_DETAIL, Vitrine.ARGENT, false);
        cabine.addView(detail, Ui.large());
        LinearLayout boutons = Ui.rangee(a);
        boutons.setPadding(0, Ui.dp(a, 10), 0, 0);
        essayer = bouton(a, "Essayer", false, v -> {
            essaiActif = !essaiActif;
            empreinte = "";
            rafraichir();
        });
        acheter = bouton(a, "Acheter", true, v -> acheter());
        porter = bouton(a, "Porter", false, v -> porter());
        for (Button b : new Button[]{essayer, acheter, porter}) {
            LinearLayout.LayoutParams lb = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
            lb.rightMargin = Ui.dp(a, 6);
            boutons.addView(b, lb);
        }
        cabine.addView(boutons, Ui.large());
        message = Ui.texte(a, "", Ui.T_ETIQUETTE, Vitrine.VIOLET, false);
        message.setPadding(0, Ui.dp(a, 6), 0, 0);
        cabine.addView(message, Ui.large());
        corps.addView(cabine, Ui.large(a, 12));

        // Rayonnage : onglets des rayons (défilement horizontal) puis étagères, toujours sur fond nuit (arcade),
        // quel que soit le thème du téléphone : les titres pixel gardent leur contraste.
        LinearLayout rayonnage = Ui.pile(a);
        rayonnage.setBackground(cadre(a, Vitrine.NUIT, Vitrine.NUIT3, 2));
        rayonnage.setPadding(Ui.dp(a, 10), Ui.dp(a, 10), Ui.dp(a, 10), Ui.dp(a, 6));
        HorizontalScrollView bande = new HorizontalScrollView(a);
        bande.setHorizontalScrollBarEnabled(false);
        onglets = Ui.rangee(a);
        bande.addView(onglets);
        rayonnage.addView(bande, Ui.large(a, 4));
        etageres = Ui.pile(a);
        rayonnage.addView(etageres, Ui.large());
        corps.addView(rayonnage, Ui.large());
    }

    private static GradientDrawable cadre(Context c, int fond, int bord, float ep) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fond);
        g.setCornerRadius(Ui.dp(c, 4));
        g.setStroke(Ui.dp(c, ep), bord);
        return g;
    }

    private static Button bouton(Context c, String s, boolean plein, View.OnClickListener action) {
        Button b = Ui.bouton(c, s, plein, action);
        b.setTextSize(14);
        b.setPadding(Ui.dp(c, 6), Ui.dp(c, 10), Ui.dp(c, 6), Ui.dp(c, 10));
        b.setBackground(Ui.touchable(c, cadre(c, plein ? Vitrine.ORANGE : Vitrine.NUIT3, plein ? Vitrine.ENCRE : Vitrine.VIOLET_FONCE, 2), 4));
        b.setTextColor(plein ? Vitrine.ENCRE : Vitrine.ARGENT_CLAIR);
        return b;
    }

    // ---- Ce que le test et les autres pages pilotent

    void rayon(String r) {
        rayon = r;
        empreinte = "";
        rafraichir();
    }

    void choisir(String id) {
        choisi = id;
        essaiActif = true;
        message.setText("");
        empreinte = "";
        rafraichir();
    }

    static String aujourdhui() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date());
    }

    /** Nouveautés : articles des rangées ouvertes depuis la dernière visite (pas encore à nous) + offres du jour pas vues. */
    static int nouveautes(Context c, Etat e) {
        if (e.po < 0) return 0;
        int n = Gains.niveau(c, e), vu = Prefs.de(c).getInt("boutiqueVue", 0), k = 0;
        if (vu > 0) for (Boutique.Article a : Boutique.debloques(vu, n)) if (!e.objets.contains(a.id)) k++;
        if (!aujourdhui().equals(Prefs.de(c).getString("boutiqueOffres", "")))
            for (String id : e.offres) {
                Boutique.Article a = Boutique.trouver(id);
                if (a != null && Boutique.ouvert(a, n) && !e.objets.contains(id)) k++;
            }
        return k;
    }

    @Override
    void montree() {
        Etat e = Prefs.etat(app);
        int n = Gains.niveau(app, e);
        int vu = Prefs.de(app).getInt("boutiqueVue", 0);
        vuAvant = vu <= 0 ? n : vu;
        Prefs.de(app).edit().putInt("boutiqueVue", Math.max(vu, n)).putString("boutiqueOffres", aujourdhui()).apply();
        empreinte = "";
        super.montree();
    }

    @Override
    void rafraichir() {
        Etat e = Prefs.etat(app);
        int n = Gains.niveau(app, e), xp = Gains.xp(app, e), solde = Gains.solde(app, e);
        if (vuAvant < 0) vuAvant = n;
        Set<String> attente = Gains.achatsEnAttente(app, e);
        Map<String, String> porte = Gains.porte(app, e);
        String nouvelle = rayon + "|" + n + "|" + xp + "|" + solde + "|" + e.po + "|" + e.objets + "|" + porte + "|" + e.offres + "|" + e.promo
                + "|" + attente + "|" + choisi + "|" + essaiActif;
        if (nouvelle.equals(empreinte)) return;
        empreinte = nouvelle;
        cabine(e, n, xp, solde, attente, porte);
        collection(e);
        ongletsRayons(e, n);
        etageres.removeAllViews();
        if (e.po < 0) {
            TextView t = Ui.texte(app, "La boutique s'ouvre quand le PC donne des nouvelles (Pilou ≥ 0.9.10 sur le PC). En attendant, on peut regarder.", Ui.T_DETAIL, Vitrine.ARGENT, false);
            t.setPadding(Ui.dp(app, 4), Ui.dp(app, 10), 0, Ui.dp(app, 4));
            etageres.addView(t, Ui.large());
        }
        if (rayon.equals(VITRINE)) vitrine(e, n, xp, solde, attente, porte);
        else if (rayon.equals(Boutique.RAYON_ENSEMBLES)) ensembles(e, n, xp, solde, attente, porte);
        else {
            // Titres et cadres à gagner (ensembles complets, paliers de collection) : en tête de leur rayon.
            List<Boutique.Article> gagnables = new ArrayList<>();
            int gagnes = 0;
            for (Boutique.Article t : Boutique.TROPHEES)
                if (t.slot.equals(rayon)) {
                    gagnables.add(t);
                    if (Boutique.peutPorter(e.objets, t.slot, t.id)) gagnes++;
                }
            if (!gagnables.isEmpty()) {
                entete(rayon.equals(Boutique.TITRE) ? "TITRES À GAGNER" : "CADRES DE COLLECTION", gagnes + " / " + gagnables.size()
                        + " gagnés · ensembles complets et paliers de collection", Vitrine.VIOLET, false, false);
                etagere(gagnables, e, n, xp, solde, attente, porte, false);
            }
            for (int palier : Boutique.PALIERS) {
                List<Boutique.Article> l = Boutique.rangee(rayon, palier);
                if (!l.isEmpty()) rangee(palier, l, e, n, xp, solde, attente, porte);
            }
        }
    }

    static LocalDate jour() {
        return LocalDate.now();
    }

    /** « ❖ Collection 37/249 · à 50 : « Fin connaisseur » » et une jauge en cases. */
    private void collection(Etat e) {
        int n = Boutique.collection(e.objets), total = Boutique.TOTAL_COLLECTION;
        Boutique.PalierCollection p = Boutique.prochainPalierCollection(n);
        collection.setText("❖ Collection " + n + "/" + total + (p == null ? " · tout est à toi !" : " · à " + Boutique.seuil(p) + " : " + p.nom));
        jauge.removeAllViews();
        int cases = 24, pleines = total == 0 ? 0 : n * cases / total;
        for (int i = 0; i < cases; i++) {
            View c = new View(app);
            c.setBackground(cadre(app, i < pleines ? Vitrine.VIOLET : Vitrine.NUIT2, Vitrine.VIOLET_FONCE, i < pleines ? 0 : 1));
            LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(Ui.dp(app, 9), Ui.dp(app, 6));
            l.rightMargin = Ui.dp(app, 2);
            jauge.addView(c, l);
        }
    }

    /** Onglet Ensembles : chaque ensemble, sa progression, son bonus ; porter d'un coup les pièces qu'on a. */
    private void ensembles(Etat e, int n, int xp, int solde, Set<String> attente, Map<String, String> porte) {
        for (Boutique.Ensemble en : Boutique.ENSEMBLES) {
            int a = Boutique.possedes(en, e.objets);
            boolean complet = a == en.pieces.size(), actif = Boutique.porteEnEntier(en, porte);
            String saison = "";
            List<Boutique.Article> pieces = new ArrayList<>();
            for (String id : en.pieces) {
                Boutique.Article x = Boutique.trouver(id);
                if (x == null) continue;
                pieces.add(x);
                if (!x.saison.isEmpty()) saison = x.saison;
            }
            String sous = a + " / " + en.pieces.size() + " · " + (actif ? "★ bonus actif" : complet ? "✓ complet : titre " + en.titre + " gagné"
                    : "complet : titre " + en.titre + " + effet")
                    + (saison.isEmpty() ? "" : Boutique.enSaison(saison, jour()) ? " · ⌛ " + Boutique.nomSaison(saison) + " : encore "
                    + Boutique.joursRestants(saison, jour()) + " j" : " · ⌛ " + Boutique.nomSaison(saison));
            entete(en.signe + " " + en.nom.toUpperCase(Locale.ROOT), sous, actif ? Vitrine.ORANGE : complet ? Vitrine.VIOLET : Vitrine.BLEU,
                    false, false);
            if (a > 0 && !actif) {
                Button tout = bouton(app, "Porter les " + a + " pièces", false, v -> {
                    for (Boutique.Article x : pieces) if (e.objets.contains(x.id)) Gains.equiper(app, x.slot, x.id);
                    envoyer();
                    message.setText("★ Pilou porte l'ensemble " + en.nom);
                    empreinte = "";
                    rafraichir();
                });
                etageres.addView(tout, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            }
            etagere(pieces, e, n, xp, solde, attente, porte, false);
        }
    }

    /** « ⌛ hors saison · revient le 1 déc. » ; « ✧ prochain passage le 14 déc. ». */
    static String indispo(Boutique.Article a) {
        java.time.format.DateTimeFormatter f = java.time.format.DateTimeFormatter.ofPattern("d MMM", Locale.FRENCH);
        if (!a.saison.isEmpty() && !Boutique.enSaison(a.saison, jour())) {
            LocalDate r = Boutique.retour(a.saison, jour());
            return "⌛ hors saison · revient " + (r == null ? "" : "le " + r.format(f)) + " (" + Boutique.nomSaison(a.saison) + ")";
        }
        LocalDate d = Boutique.prochainPassage(a, jour());
        return "✧ de passage seulement" + (d == null ? "" : " · prochain passage le " + d.format(f));
    }

    // ---- Cabine d'essayage

    private void cabine(Etat e, int n, int xp, int solde, Set<String> attente, Map<String, String> porte) {
        Boutique.Article a = Boutique.trouver(choisi);
        Map<String, String> vu = new TreeMap<>(porte);
        boolean essaie = a != null && essaiActif;
        if (essaie && java.util.Arrays.asList(Boutique.SLOTS).contains(a.slot)) vu.put(a.slot, a.id);
        String fond = vu.get(Boutique.FOND);
        decor.setImageDrawable(fond == null ? null : Vitrine.decor(app, fond));
        scene.setBackgroundColor(Vitrine.CIEL);
        essai.montrer(essaie ? "fete" : "repos", e.couleur);
        essai.accessoire(essaie && a.slot.equals(Boutique.ACCESSOIRE) ? a.id : e.accessoire);
        essai.stade(e.stade > 0 ? e.stade : Acces.stade(n));
        essai.equipe(vu);
        Boutique.StyleBulle st = Boutique.style(vu.get(Boutique.BULLE));
        bulleEssai.setVisibility(st == null ? View.GONE : View.VISIBLE);
        if (st != null) {
            GradientDrawable g = new GradientDrawable();
            g.setColor(st.fond != 0 ? st.fond : 0xfff6f8fa);
            g.setStroke(Ui.dp(app, st.epaisseur), st.bord);
            g.setCornerRadius(Ui.dp(app, st.rayon));
            bulleEssai.setBackground(g);
            bulleEssai.setTextColor(st.sombre ? Vitrine.ARGENT_CLAIR : Vitrine.ENCRE);
        }
        if (a == null) {
            nom.setText("Choisis un objet sur les étagères");
            detail.setText("Un toucher sur un objet : Pilou l'essaie ici. Les rangées s'ouvrent avec ton niveau.");
            essayer.setVisibility(View.GONE);
            acheter.setVisibility(View.GONE);
            porter.setVisibility(View.GONE);
            return;
        }
        boolean consommable = a.slot.equals(Boutique.CONSOMMABLE), bonus = a.slot.equals(Boutique.BONUS), surPc = a.slot.equals(Boutique.ACCESSOIRE);
        boolean possede = a.recompense ? Boutique.peutPorter(e.objets, a.slot, a.id) : !consommable && e.objets.contains(a.id);
        boolean enRoute = attente.contains(a.id), dispo = Boutique.disponible(a, jour());
        boolean porteIci = a.id.equals(porte.get(a.slot));
        int prix = Boutique.prix(a, e.promo);
        nom.setText(Boutique.signeRarete(a.rarete) + "  " + a.nom);
        nom.setTextColor(Boutique.couleurRarete(a.rarete));
        String etat = a.recompense ? (porteIci ? "★ porté" : possede ? "✓ gagné" : "▣ à gagner")
                : !Boutique.ouvert(a, n) ? "▣ rangée fermée : niveau " + a.niveauMin + " (encore " + Math.max(0, Butin.xpPourNiveau(a.niveauMin) - xp) + " xp)"
                : porteIci ? "★ porté" : possede ? (bonus ? "✓ actif" : surPc ? "✓ à toi · se porte depuis le PC" : "✓ à toi")
                : enRoute ? "⇢ achat en route vers le PC…"
                : !dispo ? indispo(a)
                : solde >= prix ? "◉ " + prix + " po" + (prix < a.prix ? " (au lieu de " + a.prix + ")" : "")
                : "◌ " + prix + " po · il manque " + (prix - solde) + " po";
        StringBuilder plus = new StringBuilder();
        if (!a.saison.isEmpty() && Boutique.enSaison(a.saison, jour()))
            plus.append("\n⌛ ").append(Boutique.nomSaison(a.saison)).append(" : encore ").append(Boutique.joursRestants(a.saison, jour())).append(" j");
        if (Boutique.dePassage(a, jour())) plus.append("\n✧ de passage : encore ").append(Boutique.passageRestant(a, jour())).append(" j");
        for (Boutique.Ensemble en : Boutique.ENSEMBLES)
            if (en.pieces.contains(a.id)) plus.append("\n").append(en.signe).append(" ensemble ").append(en.nom).append(" : ")
                    .append(Boutique.possedes(en, e.objets)).append("/").append(en.pieces.size());
        detail.setText(Boutique.signe(a.slot) + " " + Boutique.nomSlot(Boutique.rayonDe(a.slot)) + " · " + Boutique.nomRarete(a.rarete)
                + (a.recompense ? "" : " · rangée niveau " + a.niveauMin) + "\n" + etat + plus);
        boolean essayable = java.util.Arrays.asList(Boutique.SLOTS).contains(a.slot) || surPc;
        essayer.setVisibility(essayable ? View.VISIBLE : View.GONE);
        essayer.setText(essaiActif ? "Enlever" : "Essayer");
        acheter.setVisibility(possede || a.recompense ? View.GONE : View.VISIBLE);
        String refus = enRoute && !consommable ? "en route" : e.po < 0 ? "PC ?" : Boutique.refus(a, n, solde, e.promo, false, jour());
        acheter.setText(refus == null ? "Acheter · " + prix + " po" : refus);
        acheter.setEnabled(refus == null);
        acheter.setAlpha(refus == null ? 1f : 0.55f);
        porter.setVisibility(possede && !bonus && !surPc ? View.VISIBLE : View.GONE);
        porter.setText(porteIci ? "Retirer" : "Porter");
    }

    private void acheter() {
        Boutique.Article a = Boutique.trouver(choisi);
        if (a == null) return;
        Gains.acheter(app, a.id);
        // Un objet portable se porte dès qu'il arrive (le PC applique l'achat puis l'équipement).
        if (java.util.Arrays.asList(Boutique.SLOTS).contains(a.slot)) Gains.equiper(app, a.slot, a.id);
        envoyer();
        message.setText("✓ " + a.nom + " : achat envoyé au PC.");
        empreinte = "";
        rafraichir();
    }

    private void porter() {
        Boutique.Article a = Boutique.trouver(choisi);
        if (a == null) return;
        boolean porteIci = a.id.equals(Gains.porte(app, Prefs.etat(app)).get(a.slot));
        Gains.equiper(app, a.slot, porteIci ? "" : a.id);
        envoyer();
        message.setText(porteIci ? a.nom + " rangé." : "★ Pilou porte : " + a.nom);
        empreinte = "";
        rafraichir();
    }

    private void envoyer() {
        Context c = app.getApplicationContext();
        new Thread(() -> Gains.envoyer(c), "pilou-boutique").start();
    }

    // ---- Onglets

    private void ongletsRayons(Etat e, int n) {
        onglets.removeAllViews();
        onglets.addView(onglet(VITRINE, "◆ Vitrine", false));
        for (String r : Boutique.RAYONS) {
            boolean neuf = false;
            for (Boutique.Article a : Boutique.CATALOGUE)
                if (Boutique.rayonDe(a.slot).equals(r) && a.niveauMin > vuAvant && a.niveauMin <= n && !e.objets.contains(a.id)) neuf = true;
            onglets.addView(onglet(r, Boutique.signe(r) + " " + Boutique.nomSlot(r), neuf));
        }
    }

    private View onglet(String r, String texte, boolean neuf) {
        boolean actif = r.equals(rayon);
        TextView t = Ui.texte(app, neuf ? texte + "  !" : texte, Ui.T_DETAIL, actif ? 0xffffffff : Vitrine.ARGENT, true);
        t.setBackground(cadre(app, actif ? Vitrine.VIOLET_FONCE : Vitrine.NUIT2, actif ? 0xffd2caff : neuf ? Vitrine.ORANGE : Vitrine.FERME, 2));
        t.setPadding(Ui.dp(app, 12), Ui.dp(app, 9), Ui.dp(app, 12), Ui.dp(app, 9));
        t.setOnClickListener(v -> rayon(r));
        t.setContentDescription(texte.substring(2) + (actif ? ", rayon affiché" : "") + (neuf ? ", nouvelle rangée" : ""));
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        l.rightMargin = Ui.dp(app, 6);
        l.bottomMargin = Ui.dp(app, 6);
        t.setLayoutParams(l);
        return t;
    }

    // ---- Étagères

    private void vitrine(Etat e, int n, int xp, int solde, Set<String> attente, Map<String, String> porte) {
        List<Boutique.Article> offres = new ArrayList<>();
        for (String id : e.offres) {
            Boutique.Article a = Boutique.trouver(id);
            if (a != null) offres.add(a);
        }
        // Sans nouvelles du PC : la même vitrine, tirée de la date comme sur le PC.
        if (offres.isEmpty()) offres = Boutique.offresDuJour(jour());
        if (!offres.isEmpty()) {
            entete("OFFRES DU JOUR", "la première à -25 % · elles changent chaque jour", Vitrine.BLEU, false, false);
            etagere(offres, e, n, xp, solde, attente, porte, true);
        }
        List<Boutique.Article> passages = Boutique.passages(jour());
        if (!passages.isEmpty()) {
            entete("DE PASSAGE", "rares : quelques jours par mois seulement", 0xfff5d76e, false, false);
            etagere(passages, e, n, xp, solde, attente, porte, false);
        }
        List<Boutique.Article> saison = new ArrayList<>();
        for (Boutique.Article a : Boutique.CATALOGUE)
            if (!a.saison.isEmpty() && Boutique.enSaison(a.saison, jour()) && !e.objets.contains(a.id)) saison.add(a);
        saison.sort((x, y) -> Integer.compare(x.prix, y.prix));
        if (!saison.isEmpty()) {
            entete("DE SAISON", "ils repartent à la fin de leur saison (⌛ jours restants)", Vitrine.BLEU, false, false);
            etagere(saison.subList(0, Math.min(6, saison.size())), e, n, xp, solde, attente, porte, false);
        }
        List<Boutique.Article> neufs = new ArrayList<>();
        for (Boutique.Article a : Boutique.debloques(vuAvant, n)) if (!e.objets.contains(a.id)) neufs.add(a);
        if (!neufs.isEmpty()) {
            entete("RANGÉES DÉBLOQUÉES !", neufs.size() + " nouveauté" + (neufs.size() > 1 ? "s" : "") + " depuis ta dernière visite",
                    Vitrine.ORANGE, false, true);
            etagere(neufs.subList(0, Math.min(9, neufs.size())), e, n, xp, solde, attente, porte, false);
        }
        int p = Boutique.prochainPalier(n);
        if (p > 0) {
            List<Boutique.Article> bientot = new ArrayList<>();
            for (Boutique.Article a : Boutique.CATALOGUE) if (a.niveauMin == p) bientot.add(a);
            entete("PROCHAINE RANGÉE : NIV " + p, "encore " + Math.max(0, Butin.xpPourNiveau(p) - xp) + " xp", Vitrine.ARGENT, true, false);
            etagere(bientot.subList(0, Math.min(6, bientot.size())), e, n, xp, solde, attente, porte, false);
        }
        List<Boutique.Article> portee = new ArrayList<>();
        for (Boutique.Article a : Boutique.CATALOGUE)
            if (Boutique.ouvert(a, n) && !e.objets.contains(a.id) && !a.slot.equals(Boutique.CONSOMMABLE) && Boutique.disponible(a, jour())
                    && Boutique.prix(a, e.promo) <= solde)
                portee.add(a);
        portee.sort((x, y) -> Integer.compare(y.prix, x.prix));
        if (!portee.isEmpty() && e.po >= 0) {
            entete("À TA PORTÉE", "ouvert et dans tes moyens", Vitrine.VIOLET, false, false);
            etagere(portee.subList(0, Math.min(6, portee.size())), e, n, xp, solde, attente, porte, false);
        }
    }

    private void rangee(int palier, List<Boutique.Article> l, Etat e, int n, int xp, int solde, Set<String> attente, Map<String, String> porte) {
        boolean ouvert = n >= palier, neuf = ouvert && palier > vuAvant;
        int miens = 0;
        for (Boutique.Article a : l) if (e.objets.contains(a.id)) miens++;
        entete(neuf ? "RANGÉE NIV " + palier + " DÉBLOQUÉE !" : "RANGÉE NIV " + palier,
                ouvert ? miens + " / " + l.size() + " à toi" : "encore " + Math.max(0, Butin.xpPourNiveau(palier) - xp) + " xp",
                neuf ? Vitrine.ORANGE : ouvert ? Vitrine.BLEU : Vitrine.ARGENT, !ouvert, neuf);
        etagere(l, e, n, xp, solde, attente, porte, false);
    }

    private void entete(String titre, String sous, int couleur, boolean ferme, boolean flash) {
        LinearLayout l = Ui.pile(app);
        l.setPadding(Ui.dp(app, 2), Ui.dp(app, 16), 0, Ui.dp(app, 8));
        LinearLayout r = Ui.rangee(app);
        if (ferme) {
            ImageView cad = new ImageView(app);
            Bitmap b = Vitrine.sprite("cadenas", Ui.dp(app, 1.6f), 0, false);
            if (b != null) cad.setImageBitmap(b);
            cad.setPadding(0, 0, Ui.dp(app, 8), 0);
            cad.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            r.addView(cad);
        }
        Vitrine.Pixel t = new Vitrine.Pixel(app, titre, 2.2f, couleur, Vitrine.ENCRE, false);
        r.addView(t);
        l.addView(r);
        TextView s = Ui.texte(app, sous, Ui.T_ETIQUETTE, Vitrine.ARGENT, false);
        s.setPadding(0, Ui.dp(app, 4), 0, 0);
        l.addView(s);
        if (flash && Vitrine.anime(app)) {
            // « Rangée débloquée ! » : le titre clignote quelques fois, puis reste allumé.
            ObjectAnimator an = ObjectAnimator.ofFloat(t, "alpha", 1f, 0.25f);
            an.setDuration(260);
            an.setRepeatCount(7);
            an.setRepeatMode(ValueAnimator.REVERSE);
            an.start();
        }
        etageres.addView(l, Ui.large());
    }

    // Une étagère : trois cases par ligne, posées sur une planche de métal.
    private void etagere(List<Boutique.Article> l, Etat e, int n, int xp, int solde, Set<String> attente, Map<String, String> porte, boolean offres) {
        LinearLayout ligne = null;
        for (int i = 0; i < l.size(); i++) {
            if (i % 3 == 0) {
                if (ligne != null) planche(ligne);
                ligne = Ui.rangee(app);
                ligne.setGravity(Gravity.BOTTOM);
            }
            String ruban = offres && i == 0 && l.get(i).id.equals(e.promo) ? "-25 %" : null;
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
            lp.leftMargin = i % 3 == 0 ? 0 : Ui.dp(app, 4);
            lp.rightMargin = i % 3 == 2 ? 0 : Ui.dp(app, 4);
            ligne.addView(tuile(l.get(i), e, n, solde, attente, porte, ruban), lp);
        }
        if (ligne != null) {
            for (int k = l.size() % 3; k != 0 && k < 3; k++) ligne.addView(new View(app), new LinearLayout.LayoutParams(0, 1, 1));
            planche(ligne);
        }
    }

    private void planche(LinearLayout ligne) {
        LinearLayout pile = Ui.pile(app);
        pile.addView(ligne, Ui.large());
        View reflet = new View(app);
        reflet.setBackgroundColor(Vitrine.GRIS);
        pile.addView(reflet, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(app, 2)));
        View bois = new View(app);
        bois.setBackgroundColor(Vitrine.FERME);
        pile.addView(bois, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(app, 6)));
        View ombre = new View(app);
        ombre.setBackgroundColor(Vitrine.ENCRE);
        LinearLayout.LayoutParams lo = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(app, 2));
        lo.leftMargin = lo.rightMargin = Ui.dp(app, 6);
        pile.addView(ombre, lo);
        etageres.addView(pile, Ui.large(app, 10));
    }

    private View tuile(Boutique.Article a, Etat e, int n, int solde, Set<String> attente, Map<String, String> porte, String ruban) {
        boolean consommable = a.slot.equals(Boutique.CONSOMMABLE);
        boolean possede = a.recompense ? Boutique.peutPorter(e.objets, a.slot, a.id) : !consommable && e.objets.contains(a.id);
        boolean ouvert = a.recompense ? possede : Boutique.ouvert(a, n), enRoute = attente.contains(a.id), dispo = Boutique.disponible(a, jour());
        boolean porteIci = possede && a.id.equals(porte.get(a.slot));
        if (ruban == null && Boutique.dePassage(a, jour()) && !possede) ruban = "✧ " + Boutique.passageRestant(a, jour()) + " J";
        if (ruban == null && !possede && !a.saison.isEmpty() && Boutique.enSaison(a.saison, jour()))
            ruban = "⌛ " + Boutique.joursRestants(a.saison, jour()) + " J";
        int prix = Boutique.prix(a, e.promo);
        boolean choisie = a.id.equals(choisi);
        int bord;
        String signe;
        if (!ouvert) { bord = Vitrine.FERME; signe = ""; }
        else if (porteIci) { bord = Vitrine.ORANGE; signe = "★"; }
        else if (possede) { bord = Vitrine.VIOLET; signe = "✓"; }
        else if (enRoute) { bord = Vitrine.BLEU_CLAIR; signe = "⇢"; }
        else if (!dispo) { bord = Vitrine.FERME; signe = a.passage ? "✧" : "⌛"; }
        else if (solde >= prix && e.po >= 0) { bord = Vitrine.BLEU; signe = "◉"; }
        else { bord = Vitrine.GRIS; signe = "◌"; }

        LinearLayout c = Ui.pile(app);
        c.setGravity(Gravity.CENTER_HORIZONTAL);
        c.setBackground(Ui.touchable(app, cadre(app, choisie ? Vitrine.NUIT3 : Vitrine.NUIT2, choisie ? Vitrine.ARGENT_CLAIR : bord,
                choisie || porteIci ? 3 : 2), 4));
        c.setPadding(Ui.dp(app, 4), Ui.dp(app, 4), Ui.dp(app, 4), Ui.dp(app, 6));
        FrameLayout haut = new FrameLayout(app);
        ImageView im = new ImageView(app);
        im.setImageBitmap(vignette(a, !ouvert));
        im.setScaleType(ImageView.ScaleType.CENTER);
        haut.addView(im, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(app, 84), Gravity.CENTER));
        // Rareté : signe dans sa couleur (et celui de l'ensemble), en bas à gauche ; lisere au-dessus.
        String ens = "";
        for (Boutique.Ensemble en : Boutique.ENSEMBLES) if (en.pieces.contains(a.id)) ens = " " + en.signe;
        TextView rar = Ui.texte(app, Boutique.signeRarete(a.rarete) + ens, Ui.T_DETAIL, Boutique.couleurRarete(a.rarete), true);
        haut.addView(rar, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.START | Gravity.BOTTOM));
        View lisere = new View(app);
        lisere.setBackgroundColor(Boutique.couleurRarete(a.rarete));
        LinearLayout.LayoutParams ll = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(app, 3));
        ll.leftMargin = ll.rightMargin = Ui.dp(app, 6);
        ll.bottomMargin = Ui.dp(app, 2);
        c.addView(lisere, ll);
        if (!signe.isEmpty()) {
            TextView s = Ui.texte(app, signe, Ui.T_CORPS, bord, true);
            haut.addView(s, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.END | Gravity.TOP));
        }
        if (ruban != null) {
            TextView r = Ui.texte(app, ruban, 10, Vitrine.ENCRE, true);
            r.setBackgroundColor(Vitrine.ORANGE);
            r.setPadding(Ui.dp(app, 4), 0, Ui.dp(app, 4), Ui.dp(app, 1));
            haut.addView(r, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.START | Gravity.TOP));
        }
        c.addView(haut, Ui.large());
        TextView nomT = Ui.texte(app, a.nom, 12, ouvert ? Vitrine.ARGENT_CLAIR : Vitrine.ARGENT, false);
        nomT.setSingleLine(true);
        nomT.setEllipsize(TextUtils.TruncateAt.END);
        nomT.setGravity(Gravity.CENTER);
        c.addView(nomT, Ui.large());
        c.addView(etiquette(a, ouvert, possede, porteIci, enRoute, prix, solde, bord, e.po >= 0, dispo));
        c.setOnClickListener(v -> {
            choisir(a.id);
            defile.smoothScrollTo(0, Math.max(0, cabine.getTop() - Ui.dp(app, 8)));
        });
        c.setContentDescription(a.nom + ", " + Boutique.nomRarete(a.rarete) + ", " + (a.recompense && !possede ? "à gagner"
                : !ouvert ? "rangée fermée, niveau " + a.niveauMin : porteIci ? "porté" : possede ? "à toi" : !dispo ? indispo(a)
                : enRoute ? "achat en route" : prix + " pièces d'or" + (solde >= prix ? "" : ", trop cher pour l'instant")) + ". Toucher pour essayer.");
        return c;
    }

    // Étiquette : pièce qui tourne + prix ; ou « ▣ NIV 15 », « ✓ à toi », « ★ porté ».
    private View etiquette(Boutique.Article a, boolean ouvert, boolean possede, boolean porteIci, boolean enRoute, int prix, int solde, int bord,
                           boolean connu, boolean dispo) {
        LinearLayout r = Ui.rangee(app);
        r.setGravity(Gravity.CENTER);
        r.setBackground(cadre(app, Vitrine.ENCRE, bord, 1));
        r.setPadding(Ui.dp(app, 6), Ui.dp(app, 2), Ui.dp(app, 6), Ui.dp(app, 2));
        if (a.recompense && !possede) r.addView(Ui.texte(app, "▣ à gagner", 12, Vitrine.ARGENT, true));
        else if (!ouvert) {
            ImageView cad = new ImageView(app);
            Bitmap b = Vitrine.sprite("cadenas", Ui.dp(app, 1), 0, false);
            if (b != null) cad.setImageBitmap(b);
            cad.setPadding(0, 0, Ui.dp(app, 4), 0);
            r.addView(cad);
            r.addView(Ui.texte(app, "NIV " + a.niveauMin, 12, Vitrine.ARGENT, true));
        } else if (porteIci) r.addView(Ui.texte(app, "★ porté", 12, Vitrine.ORANGE, true));
        else if (possede) r.addView(Ui.texte(app, a.recompense ? "✓ gagné" : "✓ à toi", 12, Vitrine.VIOLET, true));
        else if (enRoute) r.addView(Ui.texte(app, "⇢ en route", 12, Vitrine.BLEU_CLAIR, true));
        else if (!dispo) {
            LocalDate d = Boutique.prochainPassage(a, jour());
            r.addView(Ui.texte(app, a.passage ? (d == null ? "✧ vitrine" : "✧ " + d.format(java.time.format.DateTimeFormatter.ofPattern("d MMM", Locale.FRENCH)))
                    : "⌛ " + Boutique.nomSaison(a.saison), 12, Vitrine.ARGENT, true));
        }
        else {
            Vitrine.Piece pc = new Vitrine.Piece(app, 1.1f);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.rightMargin = Ui.dp(app, 4);
            r.addView(pc, lp);
            boolean assez = connu && solde >= prix;
            r.addView(Ui.texte(app, prix + (prix < a.prix ? " (" + a.prix + ")" : "") + (assez ? "" : " ◌"), 12, assez ? Vitrine.ORANGE : Vitrine.ARGENT, true));
        }
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        l.topMargin = Ui.dp(app, 4);
        r.setLayoutParams(l);
        return r;
    }

    // Image d'un article : Pilou qui le porte, le décor, la bulle, ou l'icône du bonus.
    private Bitmap vignette(Boutique.Article a, boolean ferme) {
        float d = app.getResources().getDisplayMetrics().density;
        if (a.slot.equals(Boutique.FOND)) {
            Bitmap b = Vitrine.sprite(a.id, 1.35f * d, 0, ferme);
            if (b != null) return b;
        }
        if (a.slot.equals(Boutique.BULLE)) {
            Boutique.StyleBulle st = Boutique.style(a.id);
            int w = Math.round(70 * d), h = Math.round(42 * d);
            Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            GradientDrawable g = new GradientDrawable();
            g.setColor(ferme ? Vitrine.NUIT2 : st != null && st.fond != 0 ? st.fond : 0xfff6f8fa);
            g.setStroke(Math.round((st == null ? 2 : st.epaisseur) * d), ferme ? Vitrine.FERME : st == null ? Vitrine.BLEU : st.bord);
            g.setCornerRadius((st == null ? 0 : st.rayon) * d);
            g.setBounds(0, 0, w, h);
            android.graphics.Canvas cv = new android.graphics.Canvas(b);
            g.draw(cv);
            android.graphics.Paint pt = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            pt.setColor(ferme ? Vitrine.FERME : st != null && st.sombre ? Vitrine.ARGENT_CLAIR : Vitrine.ENCRE);
            pt.setTextSize(18 * d);
            pt.setTextAlign(android.graphics.Paint.Align.CENTER);
            cv.drawText("…", w / 2f, h / 2f + 4 * d, pt);
            return b;
        }
        if (a.slot.equals(Boutique.TITRE)) {
            int w = Math.round(92 * d), h = Math.round(44 * d);
            Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            android.graphics.Canvas cv = new android.graphics.Canvas(b);
            GradientDrawable g = new GradientDrawable();
            g.setColor(Vitrine.NUIT);
            g.setStroke(Math.round(2 * d), ferme ? Vitrine.FERME : Boutique.couleurRarete(a.rarete));
            g.setBounds(0, 0, w, h);
            g.draw(cv);
            android.text.TextPaint pt = new android.text.TextPaint(android.graphics.Paint.ANTI_ALIAS_FLAG);
            pt.setColor(ferme ? Vitrine.ARGENT : Vitrine.ARGENT_CLAIR);
            pt.setTextSize(10.5f * d);
            pt.setTextSkewX(-0.2f);
            android.text.StaticLayout l = android.text.StaticLayout.Builder.obtain(a.nom, 0, a.nom.length(), pt, w - Math.round(8 * d))
                    .setAlignment(android.text.Layout.Alignment.ALIGN_CENTER).build();
            cv.translate(4 * d, (h - l.getHeight()) / 2f);
            l.draw(cv);
            return b;
        }
        if (Boutique.rayonDe(a.slot).equals(Boutique.SPECIAUX) && !a.slot.equals(Boutique.ACCESSOIRE)) {
            Sprites.Sprite s = Sprites.banque().get(Vitrine.icone(a.id));
            if (s != null) {
                float p = Math.min(4, 48f / Math.max(s.w(), s.h())) * d;
                Bitmap b = Vitrine.sprite(s.id, p, 0, ferme);
                if (b != null) return b;
            }
        }
        return Vitrine.pilou(Vitrine.allure(a, 0), 1.45f * d, ferme);
    }
}
