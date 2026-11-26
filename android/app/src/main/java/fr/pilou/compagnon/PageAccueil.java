package fr.pilou.compagnon;

import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Calendar;
import java.util.List;

/**
 * Accueil : Pilou en grand (on le caresse), son niveau et sa barre d'XP, l'état du PC, les sessions
 * en cours, les appareils du groupe, un mot du jour. Pas encore appairé : un guide en trois étapes.
 */
final class PageAccueil extends Page {
    private static final String[] MOTS = {
            "Un commit par jour éloigne les bugs pour toujours.", "Pilou a rangé tes onglets. Enfin, presque.",
            "Une pause café ? Les tests tournent tout seuls.", "Les meilleurs bugs sont ceux qu'on trouve avant la prod.",
            "Pilou te rappelle de boire un verre d'eau.", "Pêche du jour : peut-être une perle ?",
            "Une recette jamais faite t'attend dans la marmite.", "Respire. La CI finira bien par passer.",
            "Petit pas, petit commit, grand projet.", "Pilou a battu son record de sieste.",
            "Lire le message d'erreur jusqu'au bout : la moitié de la solution.", "Les bugs détestent les tests unitaires.",
            "Aujourd'hui est un bon jour pour supprimer du code mort.", "Une session finie, une étincelle de plus pour Pilou."};

    private final TextView salut, nom, niveau, xp, etatPc, mot, titreSessions;
    private final Ui.Barre barre;
    private final PilouVue pilou;
    private final TextView coeur;
    private final LinearLayout sessions, groupe, guide, carteSessions;
    private String empreinteSessions = "", empreinteGroupe = "", empreinteQuetes = "";
    private int stadeVu;
    private TextView titreQuetes;
    private LinearLayout quetes;
    private long derniereCaresse;
    // Soins : une petite icône près de Pilou seulement quand un besoin baisse (un toucher la comble), et
    // « Prendre soin de Pilou » qui comble tout.
    private final TextView besoin;
    private String besoinMontre = "";
    private long mousseJusque;
    private final LinearLayout carteMeteo, carteNouvelles, nouvelles;
    private String empreinteNouvelles = "";
    private final TextView meteoTitre, meteoTexte;
    // Décor acheté (derrière Pilou) et carte « Vitrine » : l'offre du jour et la prochaine rangée de la boutique.
    private final android.widget.ImageView decor;
    private final FrameLayout scene;
    private String decorVu = "";
    private final LinearLayout carteVitrine;
    private String empreinteVitrine = "";

    PageAccueil(Principale a) {
        super(a);
        Ui.Palette p = Ui.p(a);
        salut = Ui.texte(a, "", 15, p.doux, false);
        salut.setPadding(Ui.dp(a, 2), Ui.dp(a, 14), 0, 0);
        corps.addView(salut);
        nom = Ui.titrePage(a, "Pilou");
        nom.setPadding(Ui.dp(a, 2), 0, 0, Ui.dp(a, 10));
        corps.addView(nom);

        // Carte principale : Pilou, niveau, XP.
        LinearLayout heros = Ui.carte(a);
        heros.setGravity(Gravity.CENTER_HORIZONTAL);
        scene = new FrameLayout(a);
        decor = new android.widget.ImageView(a);
        decor.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
        decor.setVisibility(View.GONE);
        decor.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        scene.addView(decor, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        pilou = new PilouVue(a, 5.2f * a.getResources().getDisplayMetrics().density);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
        scene.addView(pilou, lp);
        coeur = Ui.texte(a, "♥", 22, p.orange, true);
        coeur.setAlpha(0);
        scene.addView(coeur, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL | Gravity.TOP));
        besoin = Ui.texte(a, "", 24, p.orange, true);
        besoin.setPadding(Ui.dp(a, 10), Ui.dp(a, 6), Ui.dp(a, 10), Ui.dp(a, 6));
        besoin.setVisibility(View.GONE);
        besoin.setOnClickListener(v -> combler(besoinMontre));
        scene.addView(besoin, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.END | Gravity.TOP));
        heros.addView(scene, Ui.large());
        pilou.setOnClickListener(v -> caresser());
        pilou.setContentDescription("Pilou : toucher pour le caresser");
        niveau = Ui.texte(a, "", 18, p.texte, true);
        niveau.setGravity(Gravity.CENTER_HORIZONTAL);
        heros.addView(niveau, Ui.large());
        barre = new Ui.Barre(a);
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(a, 10);
        heros.addView(barre, lb);
        xp = Ui.texte(a, "", 13, p.doux, false);
        xp.setGravity(Gravity.CENTER_HORIZONTAL);
        xp.setPadding(0, Ui.dp(a, 6), 0, 0);
        heros.addView(xp, Ui.large());
        android.widget.Button soigner = Ui.bouton(a, "♥ Prendre soin de Pilou", false, v -> combler("tout"));
        LinearLayout.LayoutParams ls = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        ls.topMargin = Ui.dp(a, 10);
        ls.gravity = Gravity.CENTER_HORIZONTAL;
        heros.addView(soigner, ls);
        etatPc = Ui.puceTexte(a, "", p.doux);
        LinearLayout.LayoutParams le = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        le.topMargin = Ui.dp(a, 12);
        le.gravity = Gravity.CENTER_HORIZONTAL;
        heros.addView(etatPc, le);
        corps.addView(heros, Ui.large(a, 14));

        // Vitrine : l'offre du jour et la prochaine rangée ; un toucher ouvre la boutique.
        carteVitrine = Ui.carte(a);
        carteVitrine.setVisibility(View.GONE);
        corps.addView(carteVitrine, Ui.large(a, 14));

        // Météo (connecteur météo du PC) : le temps chez toi et ce que Pilou en pense.
        carteMeteo = Ui.carte(a);
        meteoTitre = Ui.texte(a, "", 17, p.texte, true);
        carteMeteo.addView(meteoTitre, Ui.large());
        meteoTexte = Ui.texte(a, "", 14, p.doux, false);
        meteoTexte.setPadding(0, Ui.dp(a, 4), 0, 0);
        carteMeteo.addView(meteoTexte, Ui.large());
        carteMeteo.setVisibility(View.GONE);
        corps.addView(carteMeteo, Ui.large(a, 14));

        // Nouvelles (connecteurs du PC : Discord, mail, GitHub…) : cachée tant qu'il n'y a rien.
        carteNouvelles = Ui.carte(a);
        carteNouvelles.addView(Ui.texte(a, "✉  Nouvelles", 17, p.texte, true), Ui.large());
        nouvelles = new LinearLayout(a);
        nouvelles.setOrientation(LinearLayout.VERTICAL);
        carteNouvelles.addView(nouvelles, Ui.large());
        carteNouvelles.setVisibility(View.GONE);
        corps.addView(carteNouvelles, Ui.large(a, 14));

        // Pas appairé : le guide.
        guide = Ui.carte(a);
        guide.addView(Ui.texte(a, "Pilou ne connaît pas encore ton PC", 17, p.texte, true));
        String[] etapes = {"Sur le PC, clic droit sur Pilou → Intégrations → Android : appairer.",
                "Vise le QR code avec l'appareil photo du téléphone : l'app s'ouvre et s'appaire.",
                "Ou tape le code de 16 caractères dans Réglages → Appairage."};
        for (int i = 0; i < etapes.length; i++) {
            LinearLayout r = Ui.rangee(a);
            r.setGravity(Gravity.TOP);
            r.setPadding(0, Ui.dp(a, 10), 0, 0);
            TextView n = Ui.pastille(a, String.valueOf(i + 1), p.bleu);
            r.addView(n);
            TextView t = Ui.texte(a, etapes[i], 14, p.texte, false);
            t.setPadding(Ui.dp(a, 12), Ui.dp(a, 8), 0, 0);
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            guide.addView(r, Ui.large());
        }
        LinearLayout.LayoutParams lg = Ui.large();
        lg.topMargin = Ui.dp(a, 14);
        guide.addView(Ui.bouton(a, "Appairer avec mon PC", true, v -> a.aller(Principale.REGLAGES, true)), lg);
        corps.addView(guide, Ui.large(a, 14));

        // Quêtes du jour (et de la semaine, du mois) : progrès, récompense en po, série.
        titreQuetes = Ui.titreSection(a, "Quêtes");
        corps.addView(titreQuetes);
        quetes = Ui.carte(a);
        corps.addView(quetes, Ui.large(a, 6));

        // Sessions.
        titreSessions = Ui.titreSection(a, "Sessions");
        corps.addView(titreSessions);
        carteSessions = Ui.carte(a);
        sessions = Ui.pile(a);
        carteSessions.addView(sessions, Ui.large());
        corps.addView(carteSessions, Ui.large(a, 6));

        // Groupe.
        groupe = Ui.pile(a);
        corps.addView(groupe, Ui.large());

        // Mot du jour.
        corps.addView(Ui.titreSection(a, "Le mot de Pilou"));
        LinearLayout carteMot = Ui.carte(a);
        carteMot.setBackground(Ui.arrondi(a, p.voile | 0x11000000, 18, 0));
        mot = Ui.texte(a, "", 15, p.texte, false);
        carteMot.addView(mot);
        corps.addView(carteMot, Ui.large());
    }

    private void caresser() {
        pilou.jouer("caresse", 2400);
        coeur.setAlpha(1);
        coeur.setTranslationY(0);
        coeur.animate().alpha(0).translationY(-Ui.dp(app, 36)).setDuration(900).start();
        long t = SystemClock.uptimeMillis();
        if (t - derniereCaresse > 3000) {
            derniereCaresse = t;
            Gains.caresse(app);
        }
    }

    // Un toucher : ce besoin-là est comblé (« tout » : repas, toilette et câlin d'un coup). Il part au PC.
    private void combler(String quoi) {
        long t = SystemClock.uptimeMillis();
        Soins.EtatSoins avant = Gains.soins(app, Prefs.etat(app), System.currentTimeMillis());
        switch (quoi) {
            case Soins.FAIM:
                Gains.soin(app, "nourrir", "croquettes");
                pilou.jouer("fete", 1400);
                break;
            case Soins.PROPRETE:
                Gains.soin(app, "laver", "");
                mousseJusque = t + 2000;
                break;
            case Soins.MORAL:
                Gains.soin(app, "calin", "");
                pilou.jouer("caresse", 2400);
                break;
            default:
                Gains.soin(app, "soin", avant.faim < 80 ? "croquettes" : "");
                if (avant.proprete < 80) mousseJusque = t + 2000;
                pilou.jouer("caresse", 2400);
                break;
        }
        coeur.setText(quoi.equals("tout") ? "♥" : Soins.signe(quoi));
        coeur.setAlpha(1);
        coeur.setTranslationY(0);
        coeur.animate().alpha(0).translationY(-Ui.dp(app, 36)).setDuration(900).start();
        rafraichir();
        if (mousseJusque > t) pilou.postDelayed(this::rafraichir, 2100);
    }

    private Soins.EtatSoins soins(Etat e, int stade, long maintenant) {
        Soins.EtatSoins s = Gains.soins(app, e, maintenant);
        java.util.List<String> objets = new java.util.ArrayList<>();
        String v = e.formes.get(stade);
        if (stade >= 2 && v != null) {
            objets.add("variante-" + v + "-" + stade);
            objets.add("variante-" + v + "-" + stade + "-tete");
        }
        if (Soins.rayonnant(s)) objets.add("rayonnant");
        if (SystemClock.uptimeMillis() < mousseJusque) objets.add("mousse");
        // Il boude : moue, nuage gris (PilouVue l'anime) ; amadoué, une éclaircie.
        pilou.soins(objets, Soins.amadoue(s) ? PilouVue.AMADOUE : Soins.boudeur(s) ? PilouVue.BOUDE : PilouVue.CONTENT);
        java.util.List<String> manques = Soins.manques(s);
        String b = manques.isEmpty() ? "" : manques.get(0);
        if (b.equals(besoinMontre)) return s;
        besoinMontre = b;
        besoin.setVisibility(b.isEmpty() ? View.GONE : View.VISIBLE);
        besoin.setText(b.isEmpty() ? "" : Soins.signe(b));
        besoin.setContentDescription(b.equals(Soins.FAIM) ? "Pilou a un petit creux : toucher pour le nourrir"
                : b.equals(Soins.PROPRETE) ? "Pilou aimerait une toilette : toucher pour le laver"
                : "Pilou a besoin d'un câlin : toucher pour un câlin");
        return s;
    }

    @Override
    void rafraichir() {
        Ui.Palette p = Ui.p(app);
        long maintenant = System.currentTimeMillis();
        Etat e = Prefs.etat(app);
        boolean appaire = Chiffre.valide(Prefs.code(app));
        int h = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        salut.setText(h < 6 ? "Il se fait tard…" : h < 12 ? "Bonjour !" : h < 18 ? "Bon après-midi !" : h < 22 ? "Bonsoir !" : "Il se fait tard…");
        nom.setText(e.nom);
        pilou.montrer(appaire ? e.expression(maintenant) : "dort", e.couleur);
        pilou.accessoire(e.accessoire);
        pilou.equipe(Gains.porte(app, e));
        decor(Gains.porte(app, e).get(Boutique.FOND));
        vitrine(e);
        meteo(e, appaire, maintenant, p);
        nouvelles(e, appaire, maintenant, p);

        // Niveau acquis gardé : si l'XP est sous son palier, la barre part du palier de la courbe.
        int total = Gains.xp(app, e), n = Gains.niveau(app, e), bas = Butin.xpPourNiveau(Math.min(n, Butin.niveau(total))), haut = Butin.xpPourNiveau(n + 1);
        // Stade d'évolution : celui du PC, sinon celui du niveau ; s'il grandit sous nos yeux, Pilou évolue.
        int stade = e.stade > 0 ? e.stade : Acces.stade(n);
        if (stadeVu > 0 && stade > stadeVu) pilou.evoluer(stade);
        else pilou.stade(stade);
        stadeVu = stade;
        Soins.EtatSoins s = soins(e, stade, maintenant);
        niveau.setText("Niveau " + n + " · " + Butin.titre(n));
        barre.part((total - bas) / (float) Math.max(1, haut - bas));
        int attente = Gains.enAttente(app);
        String humeur = Soins.amadoue(s) ? "\n☁  Pilou se laisse amadouer : gains ×0,6"
                : Soins.boudeur(s) ? "\n☁  Pilou boude : gains ×0,6" : "";
        xp.setText(total + " / " + haut + " xp" + (attente > 0 ? "   ·   +" + attente + " en route vers le PC" : "") + humeur);

        if (!appaire) {
            etatPc.setText("◌  pas encore appairé");
            etatPc.setTextColor(p.doux);
        } else if (e.muet(maintenant)) {
            etatPc.setText(e.t == 0 ? "◌  en attente du PC…" : "◌  le PC dort · rien depuis " + Etat.duree(maintenant - e.t));
            etatPc.setTextColor(p.doux);
        } else {
            long recu = Prefs.de(app).getLong("recu", 0);
            etatPc.setText("●  PC en ligne · dernier signe il y a " + Etat.duree(maintenant - Math.max(recu, e.t)));
            etatPc.setTextColor(p.bleu);
        }
        etatPc.setBackground(Ui.arrondi(app, (etatPc.getCurrentTextColor() & 0x00ffffff) | 0x22000000, 12, 0));

        guide.setVisibility(appaire ? View.GONE : View.VISIBLE);
        titreSessions.setVisibility(appaire ? View.VISIBLE : View.GONE);
        carteSessions.setVisibility(appaire ? View.VISIBLE : View.GONE);
        if (appaire) sessions(e, maintenant, p);
        quetes(e, p);
        groupe(e, maintenant, p);
        mot.setText("« " + MOTS[Calendar.getInstance().get(Calendar.DAY_OF_YEAR) % MOTS.length] + " »");
    }

    // Décor de la boutique derrière Pilou (scène aux coins nets, image pixel sans lissage).
    private void decor(String id) {
        String v = id == null ? "" : id;
        if (v.equals(decorVu)) return;
        decorVu = v;
        android.graphics.drawable.BitmapDrawable d = v.isEmpty() ? null : Vitrine.decor(app, v);
        decor.setImageDrawable(d);
        decor.setVisibility(d == null ? View.GONE : View.VISIBLE);
        scene.setClipToOutline(true);
        scene.setBackground(d == null ? null : Ui.arrondi(app, Vitrine.CIEL, 12, 0));
    }

    private void vitrine(Etat e) {
        int n = Gains.niveau(app, e), xp = Gains.xp(app, e), solde = Gains.solde(app, e);
        String emp = n + "|" + xp + "|" + solde + "|" + e.po + "|" + e.offres + "|" + e.promo + "|" + e.objets;
        if (emp.equals(empreinteVitrine)) return;
        empreinteVitrine = emp;
        carteVitrine.removeAllViews();
        carteVitrine.setVisibility(View.VISIBLE);
        carteVitrine.setBackground(Ui.touchable(app, Ui.arrondi(app, Vitrine.NUIT, 18, Vitrine.VIOLET_FONCE), 18));
        carteVitrine.setOnClickListener(v -> app.allerBoutique(PageBoutique.VITRINE));
        LinearLayout tete = Ui.rangee(app);
        tete.addView(new Vitrine.Pixel(app, "VITRINE", 2.4f, Vitrine.ORANGE, Vitrine.VIOLET_FONCE, false));
        View vide = new View(app);
        tete.addView(vide, new LinearLayout.LayoutParams(0, 1, 1));
        Vitrine.Piece piece = new Vitrine.Piece(app, 1.4f);
        tete.addView(piece);
        TextView po = Ui.texte(app, e.po < 0 ? " — po" : " " + solde + " po", 15, Vitrine.ORANGE, true);
        tete.addView(po);
        carteVitrine.addView(tete, Ui.large());
        float d = app.getResources().getDisplayMetrics().density;
        // L'offre du jour (la promo à -25 %), Pilou qui la porte.
        Boutique.Article offre = Boutique.trouver(e.promo);
        if (offre == null && !e.offres.isEmpty()) offre = Boutique.trouver(e.offres.get(0));
        if (offre != null) {
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 10), 0, 0);
            android.widget.ImageView im = new android.widget.ImageView(app);
            boolean ouvert = Boutique.ouvert(offre, n);
            im.setImageBitmap(Vitrine.pilou(Vitrine.allure(offre, 0), 1.3f * d, !ouvert));
            im.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            r.addView(im);
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, "Offre du jour", 12, Vitrine.ARGENT, false));
            t.addView(Ui.texte(app, offre.nom, 16, Vitrine.ARGENT_CLAIR, true));
            int prix = Boutique.prix(offre, e.promo);
            boolean possede = e.objets.contains(offre.id);
            String etat = possede ? "✓ déjà à toi" : !ouvert ? "▣ rangée du niveau " + offre.niveauMin
                    : prix < offre.prix ? "◉ " + prix + " po au lieu de " + offre.prix + " (-25 %)" : "◉ " + prix + " po";
            t.addView(Ui.texte(app, etat, 13, possede ? Vitrine.VIOLET : ouvert ? Vitrine.ORANGE : Vitrine.ARGENT, true));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            carteVitrine.addView(r, Ui.large());
        }
        String suite = Vitrine.prochaineRangee(n, xp);
        if (!suite.isEmpty()) {
            TextView s = Ui.texte(app, suite, 13, Vitrine.VIOLET, false);
            s.setPadding(0, Ui.dp(app, 10), 0, 0);
            carteVitrine.addView(s, Ui.large());
        }
        TextView aller = Ui.texte(app, "Ouvrir la boutique ›", 14, Vitrine.BLEU, true);
        aller.setPadding(0, Ui.dp(app, 10), 0, 0);
        carteVitrine.addView(aller, Ui.large());
        carteVitrine.setContentDescription("Vitrine de la boutique" + (offre != null ? ", offre du jour : " + offre.nom : "") + ". " + suite);
    }

    private void nouvelles(Etat e, boolean appaire, long maintenant, Ui.Palette p) {
        boolean vide = !appaire || e.annonces.isEmpty();
        carteNouvelles.setVisibility(vide ? View.GONE : View.VISIBLE);
        StringBuilder emp = new StringBuilder();
        if (!vide) for (Etat.Annonce n : e.annonces) emp.append(n.t).append('|').append(n.titre).append('|').append(maintenant / 60_000).append(';');
        if (emp.toString().equals(empreinteNouvelles)) return;
        empreinteNouvelles = emp.toString();
        nouvelles.removeAllViews();
        if (vide) return;
        for (Etat.Annonce n : e.annonces) {
            LinearLayout l = new LinearLayout(app);
            l.setOrientation(LinearLayout.VERTICAL);
            l.setPadding(0, Ui.dp(app, 8), 0, 0);
            l.addView(Ui.texte(app, n.titre, 14, p.texte, true), Ui.large());
            if (!n.texte.isEmpty()) l.addView(Ui.texte(app, n.texte, 13, p.doux, false), Ui.large());
            if (n.t > 0) l.addView(Ui.texte(app, "il y a " + Etat.duree(Math.max(0, maintenant - n.t)), 12, p.doux, false), Ui.large());
            nouvelles.addView(l, Ui.large());
        }
    }

    private void meteo(Etat e, boolean appaire, long maintenant, Ui.Palette p) {
        Meteo m = appaire ? e.meteo(maintenant) : null;
        pilou.meteo(m == null ? "" : m.etat);
        carteMeteo.setVisibility(m == null ? View.GONE : View.VISIBLE);
        if (m == null) return;
        java.util.List<String> portes = new java.util.ArrayList<>(Gains.porte(app, e).values());
        if (!"aucun".equals(e.accessoire)) portes.add("acc-" + e.accessoire);
        Meteo.Effet ef = Meteo.effet(m.etat, portes, 0);
        meteoTitre.setText(m.ligne());
        String dit = Meteo.phrase(m.etat, ef);
        meteoTexte.setText(dit.isEmpty() ? "Pilou profite du temps qu'il fait." : "Pilou : « " + dit + " »");
        meteoTexte.setTextColor(ef.protege ? p.doux : p.orange);
    }

    private void quetes(Etat e, Ui.Palette p) {
        boolean vide = e.quetes.isEmpty();
        titreQuetes.setVisibility(vide ? View.GONE : View.VISIBLE);
        quetes.setVisibility(vide ? View.GONE : View.VISIBLE);
        StringBuilder emp = new StringBuilder().append(e.serie).append('|').append(Gains.solde(app, e));
        for (Etat.Quete q : e.quetes) emp.append(q.texte).append(q.fait).append(q.reussie).append('|');
        String nouvelle = emp.toString();
        if (vide || nouvelle.equals(empreinteQuetes)) return;
        empreinteQuetes = nouvelle;
        quetes.removeAllViews();
        titreQuetes.setText(("Quêtes · ◉ " + Gains.solde(app, e) + " po" + (e.serie > 0 ? " · série " + e.serie + " j" : "")).toUpperCase(java.util.Locale.FRENCH));
        String[] signes = {"◔", "◑", "●"}, noms = {"du jour", "de la semaine", "du mois"};
        int derniere = -1;
        for (Etat.Quete q : e.quetes) {
            if (q.periode != derniere) {
                derniere = q.periode;
                TextView sec = Ui.texte(app, signes[Math.max(0, Math.min(2, q.periode))] + "  " + noms[Math.max(0, Math.min(2, q.periode))], 12, p.doux, true);
                sec.setPadding(0, quetes.getChildCount() == 0 ? 0 : Ui.dp(app, 10), 0, Ui.dp(app, 2));
                quetes.addView(sec);
            }
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Ui.pastille(app, q.reussie ? "✓" : "○", q.reussie ? p.bleu : p.argent));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, q.texte, 14, q.reussie ? p.doux : p.texte, !q.reussie));
            Ui.Barre b = new Ui.Barre(app);
            b.part(q.fait / (float) Math.max(1, q.objectif));
            LinearLayout.LayoutParams lb = Ui.large();
            lb.topMargin = Ui.dp(app, 4);
            t.addView(b, lb);
            t.addView(Ui.texte(app, q.fait + " / " + q.objectif + "   ·   +" + q.po + " po", 12, q.reussie ? p.bleu : p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            quetes.addView(r, Ui.large());
        }
    }

    private void sessions(Etat e, long maintenant, Ui.Palette p) {
        List<Etat.Ligne> lignes = e.lignes(maintenant, (int) (maintenant / 300));
        StringBuilder emp = new StringBuilder();
        for (Etat.Ligne l : lignes) emp.append(l.signe).append(l.libelle).append(l.texte).append('|');
        if (lignes.isEmpty()) emp.append(e.resume(maintenant));
        String nouvelle = emp.toString();
        if (nouvelle.equals(empreinteSessions)) return;
        empreinteSessions = nouvelle;
        sessions.removeAllViews();
        titreSessions.setText(("Sessions" + (lignes.isEmpty() ? "" : " · " + lignes.size())).toUpperCase(java.util.Locale.FRENCH));
        if (lignes.isEmpty()) {
            TextView vide = Ui.texte(app, e.muet(maintenant) ? "Pilou attend des nouvelles du PC." : "Aucune session en cours — Pilou se repose.", 14, p.doux, false);
            vide.setPadding(Ui.dp(app, 2), Ui.dp(app, 4), 0, Ui.dp(app, 4));
            sessions.addView(vide);
            return;
        }
        for (int i = 0; i < lignes.size(); i++) {
            Etat.Ligne l = lignes.get(i);
            if (i > 0) sessions.addView(Ui.separateur(app));
            int couleur = l.ton == Etat.Ton.ATTENTE ? p.orange : l.ton == Etat.Ton.TRAVAIL || l.nouveau ? p.bleu : p.argent;
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 6), 0, Ui.dp(app, 6));
            r.addView(Ui.pastille(app, l.signe, couleur));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            TextView titre = Ui.texte(app, l.libelle, 15, p.texte, true);
            titre.setSingleLine(true);
            titre.setEllipsize(android.text.TextUtils.TruncateAt.END);
            t.addView(titre);
            t.addView(Ui.texte(app, l.texte, 13, l.ton == Etat.Ton.ATTENTE ? p.orange : p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            sessions.addView(r, Ui.large());
        }
    }

    private void groupe(Etat e, long maintenant, Ui.Palette p) {
        StringBuilder emp = new StringBuilder();
        for (Etat.Appareil a : e.appareils) emp.append(a.texte(maintenant)).append('|');
        for (Etat.Ami a : e.amis) emp.append(a.nom).append(a.texte(maintenant)).append('|');
        emp.append(e.visite);
        String nouvelle = emp.toString();
        if (nouvelle.equals(empreinteGroupe)) return;
        empreinteGroupe = nouvelle;
        groupe.removeAllViews();
        amis(e, maintenant, p);
        if (e.appareils.isEmpty()) return;
        groupe.addView(Ui.titreSection(app, "Appareils du groupe" + (e.xp >= 0 ? " · " + e.xp + " xp" : "")));
        LinearLayout c = Ui.carte(app);
        for (int i = 0; i < e.appareils.size(); i++) {
            Etat.Appareil a = e.appareils.get(i);
            if (i > 0) c.addView(Ui.separateur(app));
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Ui.pastille(app, "✦", p.bleu));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, a.nom, 15, p.texte, true));
            t.addView(Ui.texte(app, a.xp + " xp · " + (a.t <= 0 ? "jamais vu" : "vu il y a " + Etat.duree(maintenant - a.t)), 13, p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            c.addView(r, Ui.large());
        }
        groupe.addView(c, Ui.large(app, 6));
    }

    // Amis du Pilou (ajoutés sur le PC) : en ligne, niveau, stade ; et la visite en cours, s'il est parti.
    private void amis(Etat e, long maintenant, Ui.Palette p) {
        if (e.amis.isEmpty() && e.visite.isEmpty()) return;
        groupe.addView(Ui.titreSection(app, "Amis de " + e.nom));
        LinearLayout c = Ui.carte(app);
        if (!e.visite.isEmpty()) {
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Ui.pastille(app, "➜", p.orange));
            TextView t = Ui.texte(app, e.visite, 14, p.orange, true);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            c.addView(r, Ui.large());
        }
        for (int i = 0; i < e.amis.size(); i++) {
            Etat.Ami a = e.amis.get(i);
            if (i > 0 || !e.visite.isEmpty()) c.addView(Ui.separateur(app));
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            // En ligne : cœur plein bleu ; ailleurs : cercle vide gris (la forme dit l'état autant que la couleur).
            boolean la = a.enLigne(maintenant);
            r.addView(Ui.pastille(app, la ? "♥" : "○", la ? p.bleu : p.argent));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Ui.texte(app, a.nom, 15, p.texte, true));
            t.addView(Ui.texte(app, a.texte(maintenant), 13, p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            c.addView(r, Ui.large());
        }
        groupe.addView(c, Ui.large(app, 6));
    }
}
