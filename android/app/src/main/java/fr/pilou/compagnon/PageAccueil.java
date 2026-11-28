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
 * Accueil : Pilou en grand (on le caresse ; en tenue de voyage quand il est parti en aventure), son niveau et sa barre
 * d'XP ; la carte « Aventure » en tête quand une campagne est en cours (compte à rebours, ou « il t'attend ! ») ; puis
 * l'essentiel (quêtes, sessions, vitrine, métiers, « Pilou et moi » et son journal) ; le reste (nouvelles, groupe) est replié.
 * Le mot du jour de Pilou (docs/PRESENCE.md) est en tête, sous son nom.
 * Pas encore appairé : qui est Pilou, puis un guide en trois étapes.
 */
final class PageAccueil extends Page {

    private final TextView salut, nom, niveau, xp, etatPc;
    private final Style.TitreSection titreSessions;
    private final TextePixelVue motDuJour;
    /** Premier lancement : une ligne de Pilou, discrète, sous le mot du jour ; rien à toucher, elle part à la première caresse. */
    static final String BIENVENUE = "coucou ! touche-moi : une caresse. le reste est en bas, et je t'écris dans Aventure ✉";
    private TextView bienvenue;
    private final PresenceVue presence;
    private final Style.Barre barre;
    private final PilouVue pilou;
    private final TextView coeur;
    private final LinearLayout sessions, groupe, guide, carteSessions;
    private String empreinteSessions = "", empreinteGroupe = "", empreinteQuetes = "";
    private int stadeVu;
    private Style.TitreSection titreQuetes;
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
    // Aventure (campagnes) : la carte en tête, et Pilou en tenue de voyage pendant une attente.
    private final LinearLayout carteAventure;
    private String empreinteAventure = "";
    private TextView aventureCompte, legende;
    private Style.Barre aventureBarre;
    private Campagnes.Etat aventure;
    // Le reste, replié : nouvelles, groupe.
    private final LinearLayout plus;
    private final TextView plusTitre;
    // Décor acheté (derrière Pilou) et carte « Vitrine » : l'offre du jour et la prochaine rangée de la boutique.
    private final android.widget.ImageView decor;
    private final FrameLayout scene;
    private String decorVu = "";
    private final LinearLayout carteVitrine;
    private String empreinteVitrine = "";
    // Expédition (lecture seule : elle se lance sur le PC) : en route ou pas, énergie, dernier journal.
    private final LinearLayout carteExpedition;
    private String empreinteExpedition = "";
    /** Petite carte « Métiers et succès » : le métier le plus pratiqué et les succès ; un toucher ouvre la page. */
    private final LinearLayout carteMetiers;
    private final TextView metiersTexte;

    PageAccueil(Principale a) {
        super(a);
        Ui.Palette p = Ui.p(a);
        salut = Style.texte(a, "", Ui.T_DETAIL, p.doux, false);
        salut.setPadding(Ui.dp(a, 2), Ui.dp(a, 14), 0, 0);
        corps.addView(salut);
        nom = Style.titrePage(a, "Pilou");
        nom.setPadding(Ui.dp(a, 2), 0, 0, Ui.dp(a, 10));
        corps.addView(nom);
        // Le mot du jour, en tête : le même que celui du soir, du widget et de la bulle.
        motDuJour = PresenceVue.motTete(a);
        corps.addView(motDuJour, Ui.large(a, 14));
        if (!Prefs.bienvenueVue(a)) {
            Prefs.marquerBienvenue(a); // une seule fois : au prochain lancement, elle ne revient pas
            bienvenue = Ui.texte(a, BIENVENUE, Ui.T_DETAIL, p.doux, false);
            bienvenue.setPadding(Ui.dp(a, 2), 0, 0, 0);
            corps.addView(bienvenue, Ui.large(a, 14));
        }

        // L'aventure en cours, en tête : il t'attend, ou il revient à telle heure.
        carteAventure = Ui.pile(a);
        carteAventure.setVisibility(View.GONE);
        corps.addView(carteAventure, Ui.large(a, 14));

        // Carte principale : Pilou, niveau, XP.
        LinearLayout heros = Style.carte(a);
        heros.setGravity(Gravity.CENTER_HORIZONTAL);
        scene = new FrameLayout(a);
        decor = new android.widget.ImageView(a);
        decor.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
        decor.setVisibility(View.GONE);
        decor.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        scene.addView(decor, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        pilou = new PilouVue(a, 5.2f * a.getResources().getDisplayMetrics().density, true);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
        scene.addView(pilou, lp);
        coeur = Style.texte(a, "♥", 22, p.orange, true);
        coeur.setAlpha(0);
        scene.addView(coeur, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.CENTER_HORIZONTAL | Gravity.TOP));
        besoin = Style.texte(a, "", 24, p.orange, true);
        besoin.setPadding(Ui.dp(a, 10), Ui.dp(a, 6), Ui.dp(a, 10), Ui.dp(a, 6));
        besoin.setVisibility(View.GONE);
        besoin.setOnClickListener(v -> combler(besoinMontre));
        scene.addView(besoin, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.END | Gravity.TOP));
        heros.addView(scene, Ui.large());
        pilou.setOnClickListener(v -> caresser());
        pilou.setContentDescription("Pilou : toucher pour le caresser");
        // Pendant une aventure : ce qu'il fait, sous lui (« en route · retour vers 15 h 40 »).
        legende = Style.puce(a, "", Aventure.accentTon(a, "humour"));
        legende.setVisibility(View.GONE);
        LinearLayout.LayoutParams lle = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lle.gravity = Gravity.CENTER_HORIZONTAL;
        lle.bottomMargin = Ui.dp(a, 8);
        heros.addView(legende, lle);
        niveau = Style.texte(a, "", Ui.T_CARTE, p.texte, true);
        niveau.setGravity(Gravity.CENTER_HORIZONTAL);
        heros.addView(niveau, Ui.large());
        barre = new Style.Barre(a);
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(a, 10);
        heros.addView(barre, lb);
        xp = Style.texte(a, "", Ui.T_DETAIL, p.doux, false);
        xp.setGravity(Gravity.CENTER_HORIZONTAL);
        xp.setPadding(0, Ui.dp(a, 6), 0, 0);
        heros.addView(xp, Ui.large());
        TextView soigner = Style.bouton(a, "♥ Prendre soin de Pilou", false, v -> combler("tout"));
        LinearLayout.LayoutParams ls = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        ls.topMargin = Ui.dp(a, 10);
        ls.gravity = Gravity.CENTER_HORIZONTAL;
        heros.addView(soigner, ls);
        etatPc = Style.puce(a, "", p.doux);
        LinearLayout.LayoutParams le = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        le.topMargin = Ui.dp(a, 12);
        le.gravity = Gravity.CENTER_HORIZONTAL;
        heros.addView(etatPc, le);
        corps.addView(heros, Ui.large(a, 14));


        carteExpedition = Style.carte(a);
        carteExpedition.setVisibility(View.GONE);
        corps.addView(carteExpedition, Ui.large(a, 14));

        // Météo (connecteur météo du PC) : le temps chez toi et ce que Pilou en pense.
        carteMeteo = Style.carte(a);
        meteoTitre = Style.texte(a, "", Ui.T_CARTE, p.texte, true);
        carteMeteo.addView(meteoTitre, Ui.large());
        meteoTexte = Style.texte(a, "", Ui.T_DETAIL, p.doux, false);
        meteoTexte.setPadding(0, Ui.dp(a, 4), 0, 0);
        carteMeteo.addView(meteoTexte, Ui.large());
        carteMeteo.setVisibility(View.GONE);
        corps.addView(carteMeteo, Ui.large(a, 14));

        // Nouvelles (connecteurs du PC : Discord, mail, GitHub…) : cachée tant qu'il n'y a rien ; dans « Plus ».
        carteNouvelles = Style.carte(a);
        carteNouvelles.addView(Style.texte(a, "✉  Nouvelles", Ui.T_CARTE, p.texte, true), Ui.large());
        nouvelles = new LinearLayout(a);
        nouvelles.setOrientation(LinearLayout.VERTICAL);
        carteNouvelles.addView(nouvelles, Ui.large());
        carteNouvelles.setVisibility(View.GONE);

        // Pas appairé : le guide.
        guide = Style.carte(a);
        guide.addView(Style.texte(a, "Un petit compagnon qui vit en bas de ton écran", Ui.T_CARTE, p.texte, true));
        TextView intro = Style.texte(a, "Pilou mène sa petite vie sans te déranger : il joue, mange, pêche, part à l'aventure, et grandit "
                + "pendant que tu travailles. S'il est branché à tes applis, il te prévient quand une IA t'attend.",
                Ui.T_CORPS, p.doux, false);
        intro.setPadding(0, Ui.dp(a, 6), 0, 0);
        guide.addView(intro, Ui.large());
        TextView relier = Style.texte(a, "Pour le retrouver ici, relie-le à ton PC :", Ui.T_CORPS, p.texte, true);
        relier.setPadding(0, Ui.dp(a, 12), 0, 0);
        guide.addView(relier, Ui.large());
        String[] etapes = {"Sur le PC, clic droit sur Pilou → Amis et appareils → Groupe d'appareils → Partager l'XP entre mes appareils.",
                "Vise le QR code avec l'appareil photo du téléphone : l'app s'ouvre et s'appaire.",
                "Ou tape le code de 16 caractères dans Réglages → Appairage."};
        for (int i = 0; i < etapes.length; i++) {
            LinearLayout r = Ui.rangee(a);
            r.setGravity(Gravity.TOP);
            r.setPadding(0, Ui.dp(a, 10), 0, 0);
            TextView n = Style.caseSigne(a, String.valueOf(i + 1), p.bleu);
            r.addView(n);
            TextView t = Style.texte(a, etapes[i], Ui.T_CORPS, p.texte, false);
            t.setPadding(Ui.dp(a, 12), Ui.dp(a, 8), 0, 0);
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            guide.addView(r, Ui.large());
        }
        LinearLayout.LayoutParams lg = Ui.large();
        lg.topMargin = Ui.dp(a, 14);
        guide.addView(Style.bouton(a, "Appairer avec mon PC", true, v -> a.aller(Principale.REGLAGES, true)), lg);
        corps.addView(guide, Ui.large(a, 14));

        // Quêtes du jour (et de la semaine, du mois) : progrès, récompense en po, série.
        titreQuetes = Style.titreSection(a, "Quêtes");
        corps.addView(titreQuetes);
        quetes = Style.carte(a);
        corps.addView(quetes, Ui.large(a, 14));

        // Sessions.
        titreSessions = Style.titreSection(a, "Sessions");
        corps.addView(titreSessions);
        carteSessions = Style.carte(a);
        sessions = Ui.pile(a);
        carteSessions.addView(sessions, Ui.large());
        corps.addView(carteSessions, Ui.large(a, 14));

        // Vitrine : l'offre du jour et la prochaine rangée ; un toucher ouvre la boutique.
        carteVitrine = Style.carte(a);
        carteVitrine.setVisibility(View.GONE);
        corps.addView(carteVitrine, Ui.large(a, 14));

        carteMetiers = Style.carte(a);
        carteMetiers.addView(Style.texte(a, Metiers.TRAVAIL + "  Métiers et succès", Ui.T_CARTE, p.texte, true), Ui.large());
        metiersTexte = Style.texte(a, "", Ui.T_DETAIL, p.doux, false);
        metiersTexte.setPadding(0, Ui.dp(a, 4), 0, 0);
        carteMetiers.addView(metiersTexte, Ui.large());
        TextView voir = Style.texte(a, "Voir les métiers et les succès ›", Ui.T_DETAIL, p.bleu, true);
        voir.setPadding(0, Ui.dp(a, 8), 0, 0);
        carteMetiers.addView(voir, Ui.large());
        Style.fond(carteMetiers, Style.touchable(a, Style.arrondi(a, p.surface, 18, p.bord), 18));
        carteMetiers.setClickable(true);
        carteMetiers.setOnClickListener(v -> a.allerMetiers());
        carteMetiers.setVisibility(View.GONE);
        corps.addView(carteMetiers, Ui.large(a, 14));

        // Pilou et moi : complicité, prénom (demandé une fois), journal feuilletable.
        presence = new PresenceVue(a);
        corps.addView(presence, Ui.large(a, 14));

        // Le reste, replié : un toucher l'ouvre (le choix est gardé).
        plusTitre = Style.texte(a, "", Ui.T_CORPS, p.bleu, true);
        plusTitre.setGravity(Gravity.CENTER);
        plusTitre.setMinHeight(Ui.dp(a, 48));
        Style.fond(plusTitre, Style.touchable(a, Style.arrondi(a, 0x00000000, 14, 0), 14));
        plusTitre.setOnClickListener(v -> {
            Prefs.de(a).edit().putBoolean("accueilPlus", !Prefs.de(a).getBoolean("accueilPlus", false)).apply();
            deplier(true);
        });
        LinearLayout.LayoutParams lpt = Ui.large();
        lpt.topMargin = Ui.dp(a, 8);
        corps.addView(plusTitre, lpt);
        plus = Ui.pile(a);
        corps.addView(plus, Ui.large());
        plus.addView(carteNouvelles, Ui.large(a, 14));
        // Groupe.
        groupe = Ui.pile(a);
        plus.addView(groupe, Ui.large());
        deplier(false);
    }

    private void deplier(boolean anime) {
        boolean ouvert = Prefs.de(app).getBoolean("accueilPlus", false);
        plusTitre.setText(ouvert ? "Moins de choses  ▴" : "Nouvelles et groupe  ▾");
        plusTitre.setContentDescription(ouvert ? "Replier les nouvelles et le groupe" : "Déplier les nouvelles et le groupe");
        plus.setVisibility(ouvert ? View.VISIBLE : View.GONE);
        if (anime && ouvert && Vitrine.anime(app)) {
            plus.setAlpha(0);
            plus.setTranslationY(-Ui.dp(app, 8));
            plus.animate().alpha(1).translationY(0).setDuration(200).start();
            defile.post(() -> defile.smoothScrollBy(0, Ui.dp(app, 160)));
        }
    }

    // ---- Aventure

    private void aventure(Etat pc) {
        Ui.Palette p = Ui.p(app);
        Campagnes.Etat e = CampagnesTel.pretes() ? CampagnesTel.etat(app) : null;
        aventure = e;
        boolean enCours = e != null && (e.enCours() || e.phase == Campagnes.Phase.Fin && CampagnesTel.nonLus(app) > 0);
        Campagnes.Partie q = enCours ? CampagnesTel.courante(app) : null;
        Campagnes.Campagne c = q == null ? null : Campagnes.charger(q.campagne);
        // Pilou en tenue de voyage pendant l'attente ; la légende dit où il en est.
        if (c != null && e.phase == Campagnes.Phase.Attente) {
            pilou.tenue("voyage-" + e.tenue);
            // Ce qu'il fait est dit par la carte Aventure, juste au-dessus : la légende tient en une ligne courte.
            legende.setText("→ en route · retour vers " + CampagnesTel.heure(e.fin));
            legende.setVisibility(View.VISIBLE);
        } else if (c != null && e.phase == Campagnes.Phase.Repos) {
            pilou.tenue("voyage-nuit");
            legende.setText("☾ au repos · reprise vers " + CampagnesTel.heure(e.fin));
            legende.setVisibility(View.VISIBLE);
        } else {
            pilou.tenue("");
            legende.setVisibility(View.GONE);
        }
        boolean attend = c != null && CampagnesTel.attendJoueur(app, e);
        // Jamais joué : une invitation discrète au prologue (une seule carte, qui disparaît dès la première partie).
        Campagnes.Carnet k = CampagnesTel.pretes() ? CampagnesTel.carnet(app) : null;
        boolean inviter = c == null && k != null && k.courante == null && k.historique.isEmpty() && Campagnes.charger("prologue") != null;
        String emp = c == null ? (inviter ? "invitation" : "") : c.id + "|" + e.phase + "|" + e.noeud + "|" + attend;
        if (!emp.equals(empreinteAventure)) {
            empreinteAventure = emp;
            carteAventure.removeAllViews();
            aventureCompte = null;
            aventureBarre = null;
            carteAventure.setVisibility(c == null && !inviter ? View.GONE : View.VISIBLE);
            if (c != null) carteAventure(c, e, attend, pc, p);
            else if (inviter) invitation(Campagnes.charger("prologue"), p);
        }
        if (aventureCompte != null && e != null && e.enAttente()) {
            long reste = e.fin - CampagnesTel.maintenant();
            aventureCompte.setText(Aventure.compte(reste));
            aventureCompte.setContentDescription("Retour dans " + CampagnesTel.reste(reste));
            if (aventureBarre != null) aventureBarre.part(1 - reste / (float) Math.max(1, e.fin - e.t));
        }
    }

    private void invitation(Campagnes.Campagne c, Ui.Palette p) {
        Style.fond(carteAventure, Style.touchable(app, Style.arrondi(app, p.surface, 18, p.bord), 18));
        LinearLayout r = Ui.rangee(app);
        r.setPadding(Ui.dp(app, 16), Ui.dp(app, 14), Ui.dp(app, 12), Ui.dp(app, 14));
        r.addView(Style.caseSigne(app, Aventure.signeTon(c.ton), Aventure.accentTon(app, c.ton)));
        LinearLayout t = Ui.pile(app);
        t.setPadding(Ui.dp(app, 12), 0, 0, 0);
        t.addView(Style.texte(app, "Sa première aventure", Ui.T_CORPS, p.texte, true));
        t.addView(Style.texte(app, c.titre + " · " + c.duree + " · il t'écrira", Ui.T_DETAIL, p.doux, false));
        r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        r.addView(Style.chevron(app, p.doux));
        carteAventure.addView(r, Ui.large());
        carteAventure.setOnClickListener(v -> app.aller(Principale.AVENTURE, true));
        carteAventure.setContentDescription("Sa première aventure : " + c.titre + ". Toucher pour la découvrir.");
    }

    private void carteAventure(Campagnes.Campagne c, Campagnes.Etat e, boolean attend, Etat pc, Ui.Palette p) {

        int accent = Aventure.accentTon(app, c.ton);
        Style.fond(carteAventure, Style.touchable(app, Style.arrondi(app, p.surface, 18, attend ? accent : p.bord), 18));
        // Bande de décor, Pilou dedans (il marche s'il est en route).
        FrameLayout bande = new FrameLayout(app);
        Aventure.Scene sc = new Aventure.Scene(app);
        sc.regler(c.id, c.ton, e.decor);
        bande.addView(sc, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        // Étiquette posée sur le décor : cadre plat de nuit, police pixel (une ligne ; un titre trop long finit par « … »).
        Style.Texte etiquette = new Style.Texte(app, Aventure.signeTon(c.ton) + " " + c.titre + (e.chapitreTotal > 0 ? " · " + e.chapitreNumero + "/" + e.chapitreTotal : ""),
                Style.PETIT, Vitrine.ARGENT_CLAIR, true);
        etiquette.setSingleLine(true);
        etiquette.setBackground(Style.plat(app, 0xe6151a2e, Vitrine.VIOLET_FONCE));
        etiquette.setPadding(Style.u(app) + Ui.dp(app, 6), Style.u(app) + Ui.dp(app, 1), Style.u(app) + Ui.dp(app, 6), Style.u(app) + Ui.dp(app, 1));
        FrameLayout.LayoutParams le = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.TOP | Gravity.END);
        le.setMargins(Ui.dp(app, 12), Ui.dp(app, 10), Ui.dp(app, 12), 0);
        etiquette.setMaxWidth(Ui.dp(app, 260));
        bande.addView(etiquette, le);
        PilouVue pv = new PilouVue(app, Aventure.pixelPour(app, 66), true);
        pv.equipe(Gains.porte(app, pc));
        pv.accessoire(pc.accessoire);
        if (e.phase == Campagnes.Phase.Attente) {
            pv.tenue("voyage-" + e.tenue);
            sc.marcher(Aventure.vitesse(e.tenue), e.tenue.equals("nuit"));
            pv.montrer("repos", pc.couleur);
        } else if (e.phase == Campagnes.Phase.Repos) {
            pv.tenue("voyage-nuit");
            sc.marcher(0, true);
            pv.montrer("fatigue", pc.couleur);
        } else pv.montrer("joie", pc.couleur);
        pv.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM | Gravity.START);
        lp.leftMargin = Ui.dp(app, 12);
        bande.addView(pv, lp);
        carteAventure.addView(bande, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, Ui.dp(app, 84)));
        LinearLayout b = Ui.pile(app);
        b.setPadding(Ui.dp(app, 16), Ui.dp(app, 12), Ui.dp(app, 16), Ui.dp(app, 14));
        if (e.enAttente()) {
            boolean repos = e.phase == Campagnes.Phase.Repos;
            LinearLayout r = Ui.rangee(app);
            LinearLayout t = Ui.pile(app);
            t.addView(Style.texte(app, repos ? "Pilou se repose" : e.pendant.isEmpty() ? "Pilou est en route" : e.pendant, Ui.T_CORPS, p.texte, true));
            t.addView(Style.texte(app, (repos ? "reprise" : "retour") + " vers " + CampagnesTel.heure(e.fin) + " · je te préviens", Ui.T_DETAIL, p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            aventureCompte = Style.texte(app, "", 22, accent, true);
            aventureCompte.setTypeface(android.graphics.Typeface.create("monospace", android.graphics.Typeface.BOLD));
            aventureCompte.setPadding(Ui.dp(app, 10), 0, 0, 0);
            r.addView(aventureCompte);
            b.addView(r, Ui.large());
            aventureBarre = new Style.Barre(app);
            LinearLayout.LayoutParams lb = Ui.large();
            lb.topMargin = Ui.dp(app, 10);
            b.addView(aventureBarre, lb);
        } else {
            LinearLayout r = Ui.rangee(app);
            LinearLayout t = Ui.pile(app);
            String titre = e.phase == Campagnes.Phase.Fin ? "★  Le dénouement t'attend !" : attend ? "●  Il t'attend !" : "Une aventure en cours";
            t.addView(Style.texte(app, titre, Ui.T_CARTE, attend ? p.orange : p.texte, true));
            t.addView(Style.texte(app, e.lieu.isEmpty() ? "Il a besoin de toi pour la suite." : e.lieu + " · il a besoin de toi", Ui.T_DETAIL, p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            r.addView(Style.chevron(app, p.doux));
            b.addView(r, Ui.large());
        }
        carteAventure.addView(b, Ui.large());
        carteAventure.setOnClickListener(v -> app.ouvrirLecture());
        carteAventure.setContentDescription("Aventure : " + c.titre + ". " + (attend ? "Pilou t'attend. Toucher pour lire." : "Toucher pour la lire."));
        if (Vitrine.anime(app)) {
            carteAventure.setAlpha(0);
            carteAventure.animate().alpha(1).setDuration(220).start();
        }
    }

    private void caresser() {
        if (bienvenue != null) {
            bienvenue.animate().alpha(0).setDuration(600).withEndAction(() -> bienvenue.setVisibility(View.GONE)).start();
        }
        pilou.jouer("caresse", 2400);
        Sons.jouer(app, Sons.CARESSE);
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
        // Même titre que le bandeau : celui que Pilou porte, sinon celui du niveau.
        String titrePorte = Boutique.nomTitre(Gains.porte(app, e).get(Boutique.TITRE));
        niveau.setText("Niveau " + n + " · " + (titrePorte != null ? titrePorte : Butin.titre(n)));
        barre.part((total - bas) / (float) Math.max(1, haut - bas));
        int attente = Gains.enAttente(app);
        String humeur = Soins.amadoue(s) ? "\n☁  Pilou se laisse amadouer : gains ×0,6"
                : Soins.boudeur(s) ? "\n☁  Pilou boude : gains ×0,6" : "";
        String energie = e.expedition != null && e.expedition.energie >= 0 ? "   ·   ⚡ " + e.expedition.energie : "";
        // Même lecture que le bandeau (et le PC) : l'XP dans le niveau, puis ce qu'il manque pour le suivant.
        String dansNiveau = "niveau " + (n + 1) + " dans " + Math.max(0, haut - total) + " xp";

        xp.setText(dansNiveau + energie + (attente > 0 ? "   ·   +" + attente + " en route vers le PC" : "") + humeur);
        aventure(e);
        expedition(e, appaire, maintenant, p);
        boolean metiers = appaire && Metiers.connus(e);
        carteMetiers.setVisibility(metiers ? View.VISIBLE : View.GONE);
        if (metiers) {
            metiersTexte.setText(Metiers.resume(e));
            carteMetiers.setContentDescription("Métiers et succès : " + Metiers.resume(e) + ". Toucher pour les voir.");
        }

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
        Style.puce((Style.Texte) etatPc, etatPc.getCurrentTextColor());

        guide.setVisibility(appaire ? View.GONE : View.VISIBLE);
        titreSessions.setVisibility(appaire ? View.VISIBLE : View.GONE);
        carteSessions.setVisibility(appaire ? View.VISIBLE : View.GONE);
        if (appaire) sessions(e, maintenant, p);
        quetes(e, p);
        groupe(e, maintenant, p);
        presenceDuJour();
    }

    // Le mot du jour en tête, la carte « Pilou et moi » ; et, la première fois du jour, un petit signe de Pilou (Copain).
    private void presenceDuJour() {
        try {
            String m = PresenceTel.motDuJour(app);
            motDuJour.setVisibility(m.isEmpty() ? View.GONE : View.VISIBLE);
            motDuJour.texte(m.isEmpty() ? "" : "« " + m + " »");
            motDuJour.setContentDescription(m.isEmpty() ? null : "Pilou dit : " + m);
            presence.rafraichir();
            Presence.Etat e = PresenceTel.etat(app);
            String jour = Presence.jourTexte(java.time.LocalDateTime.now());
            if (e.gestes && !jour.equals(Prefs.de(app).getString("presenceSigne", "")) && e.totaux().palier >= 1) {
                Prefs.de(app).edit().putString("presenceSigne", jour).apply();
                pilou.jouer("joie", 1600);
            }
        } catch (RuntimeException ex) {
            Journal.noter("présence : accueil", ex);
        }
    }

    // Expédition du Pilou du PC : une carte seulement quand il y a quelque chose à dire.
    private void expedition(Etat e, boolean appaire, long maintenant, Ui.Palette p) {
        Etat.Expedition x = appaire ? e.expedition : null;
        boolean vide = x == null || (!x.enRoute() && x.journal.isEmpty());
        carteExpedition.setVisibility(vide ? View.GONE : View.VISIBLE);
        if (vide) return;
        String emp = x.etat + x.lieu + x.retour + x.energie + x.reste + x.t + (maintenant / 60_000) + x.journal.size();
        if (emp.equals(empreinteExpedition)) return;
        empreinteExpedition = emp;
        carteExpedition.removeAllViews();
        carteExpedition.addView(Style.texte(app, "⚔  Expédition" + (x.energie >= 0 ? "   ·   ⚡ " + x.energie + "/100" : ""), Ui.T_CARTE, p.texte, true), Ui.large());
        TextView etat = Style.texte(app, x.ligne(maintenant), Ui.T_DETAIL, x.enRoute() ? p.orange : p.doux, x.enRoute());
        etat.setPadding(0, Ui.dp(app, 4), 0, 0);
        carteExpedition.addView(etat, Ui.large());
        if (x.journal.isEmpty()) return;
        TextView titre = Style.texte(app, x.signe() + "  Dernière : " + x.dernier + " · " + x.nomIssue()
                + (x.t > 0 ? " · " + Etat.Expedition.heure(x.t) : ""), Ui.T_CORPS, p.texte, true);
        titre.setPadding(0, Ui.dp(app, 10), 0, Ui.dp(app, 2));
        carteExpedition.addView(titre, Ui.large());
        for (String l : x.journal) {
            TextView t = Style.texte(app, l, Ui.T_DETAIL, p.doux, false);
            t.setPadding(0, Ui.dp(app, 2), 0, 0);
            carteExpedition.addView(t, Ui.large());
        }
    }

    // Décor de la boutique derrière Pilou (scène aux coins nets, image pixel sans lissage).
    private void decor(String id) {
        String v = id == null ? "" : id;
        if (v.equals(decorVu)) return;
        decorVu = v;
        android.graphics.drawable.BitmapDrawable d = v.isEmpty() ? null : Vitrine.decor(app, v);
        decor.setImageDrawable(d);
        decor.setVisibility(d == null ? View.GONE : View.VISIBLE);
        Style.fond(scene, d == null ? null : Style.arrondi(app, Vitrine.CIEL, 12, 0));
    }

    private void vitrine(Etat e) {
        int n = Gains.niveau(app, e), xp = Gains.xp(app, e), solde = Gains.solde(app, e);
        String emp = n + "|" + xp + "|" + solde + "|" + e.po + "|" + e.offres + "|" + e.promo + "|" + e.objets;
        if (emp.equals(empreinteVitrine)) return;
        empreinteVitrine = emp;
        carteVitrine.removeAllViews();
        carteVitrine.setVisibility(View.VISIBLE);
        Style.fond(carteVitrine, Style.touchable(app, Style.arrondi(app, Vitrine.NUIT, 18, Vitrine.VIOLET_FONCE), 18));
        carteVitrine.setOnClickListener(v -> app.allerBoutique(PageBoutique.VITRINE));
        LinearLayout tete = Ui.rangee(app);
        tete.addView(new Vitrine.Pixel(app, "VITRINE", 2.4f, Vitrine.ORANGE, Vitrine.VIOLET_FONCE, false));
        View vide = new View(app);
        tete.addView(vide, new LinearLayout.LayoutParams(0, 1, 1));
        Vitrine.Piece piece = new Vitrine.Piece(app, 1.4f);
        tete.addView(piece);
        TextView po = Style.texte(app, e.po < 0 ? " — po" : " " + solde + " po", Ui.T_CORPS, Vitrine.ORANGE, true);
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
            t.addView(Style.texte(app, "Offre du jour", Ui.T_ETIQUETTE, Vitrine.ARGENT, false));
            t.addView(Style.texte(app, offre.nom, Ui.T_CORPS, Vitrine.ARGENT_CLAIR, true));
            int prix = Boutique.prix(offre, e.promo);
            boolean possede = e.objets.contains(offre.id);
            String etat = possede ? "✓ déjà à toi" : !ouvert ? "▣ rangée du niveau " + offre.niveauMin
                    : prix < offre.prix ? "¤ " + prix + " po au lieu de " + offre.prix + " (-25 %)" : "¤ " + prix + " po";
            t.addView(Style.texte(app, etat, Ui.T_DETAIL, possede ? Vitrine.VIOLET : ouvert ? Vitrine.ORANGE : Vitrine.ARGENT, true));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            carteVitrine.addView(r, Ui.large());
        }
        String suite = Vitrine.prochaineRangee(n, xp);
        if (!suite.isEmpty()) {
            TextView s = Style.texte(app, suite, Ui.T_DETAIL, Vitrine.VIOLET, false);
            s.setPadding(0, Ui.dp(app, 10), 0, 0);
            carteVitrine.addView(s, Ui.large());
        }
        TextView aller = Style.texte(app, "Ouvrir la boutique ›", Ui.T_CORPS, Vitrine.BLEU, true);
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
            l.addView(Style.texte(app, n.titre, Ui.T_CORPS, p.texte, true), Ui.large());
            if (!n.texte.isEmpty()) l.addView(Style.texte(app, n.texte, Ui.T_DETAIL, p.doux, false), Ui.large());
            if (n.t > 0) l.addView(Style.texte(app, "il y a " + Etat.duree(Math.max(0, maintenant - n.t)), Ui.T_ETIQUETTE, p.doux, false), Ui.large());
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
        titreQuetes.setText(("Quêtes · ¤ " + Gains.solde(app, e) + " po" + (e.serie > 0 ? " · série " + e.serie + " j" : "")).toUpperCase(java.util.Locale.FRENCH));
        String[] signes = {"◔", "◑", "●"}, noms = {"du jour", "de la semaine", "du mois"};
        int derniere = -1;
        for (Etat.Quete q : e.quetes) {
            if (q.periode != derniere) {
                derniere = q.periode;
                TextView sec = Style.texte(app, signes[Math.max(0, Math.min(2, q.periode))] + "  " + noms[Math.max(0, Math.min(2, q.periode))], Ui.T_ETIQUETTE, p.doux, true);
                sec.setPadding(0, quetes.getChildCount() == 0 ? 0 : Ui.dp(app, 10), 0, Ui.dp(app, 2));
                quetes.addView(sec);
            }
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Style.caseSigne(app, q.reussie ? "✓" : "○", q.reussie ? p.bleu : p.argent));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Style.texte(app, q.texte, Ui.T_DETAIL, q.reussie ? p.doux : p.texte, !q.reussie));
            Style.Barre b = new Style.Barre(app);
            b.part(q.fait / (float) Math.max(1, q.objectif));
            LinearLayout.LayoutParams lb = Ui.large();
            lb.topMargin = Ui.dp(app, 4);
            t.addView(b, lb);
            t.addView(Style.texte(app, q.fait + " / " + q.objectif + "   ·   +" + q.po + " po", Ui.T_ETIQUETTE, q.reussie ? p.bleu : p.doux, false));
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
            TextView vide = Style.texte(app, e.muet(maintenant) ? "Pilou attend des nouvelles du PC." : "Aucune session en cours — Pilou se repose.", Ui.T_DETAIL, p.doux, false);
            vide.setPadding(Ui.dp(app, 2), Ui.dp(app, 4), 0, Ui.dp(app, 4));
            sessions.addView(vide);
            return;
        }
        for (int i = 0; i < lignes.size(); i++) {
            Etat.Ligne l = lignes.get(i);
            if (i > 0) sessions.addView(Style.separateur(app));
            int couleur = l.ton == Etat.Ton.ATTENTE ? p.orange : l.ton == Etat.Ton.TRAVAIL || l.nouveau ? p.bleu : p.argent;
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 6), 0, Ui.dp(app, 6));
            r.addView(Style.caseSigne(app, l.signe, couleur));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            TextView titre = Style.texte(app, l.libelle, Ui.T_CORPS, p.texte, true);
            titre.setSingleLine(true);
            titre.setEllipsize(android.text.TextUtils.TruncateAt.END);
            t.addView(titre);
            t.addView(Style.texte(app, l.texte, Ui.T_DETAIL, l.ton == Etat.Ton.ATTENTE ? p.orange : p.doux, false));
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
        groupe.addView(Style.titreSection(app, "Appareils du groupe" + (e.xp >= 0 ? " · " + e.xp + " xp" : "")));
        LinearLayout c = Style.carte(app);
        for (int i = 0; i < e.appareils.size(); i++) {
            Etat.Appareil a = e.appareils.get(i);
            if (i > 0) c.addView(Style.separateur(app));
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Style.caseSigne(app, "✦", p.bleu));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Style.texte(app, a.nom, Ui.T_CORPS, p.texte, true));
            t.addView(Style.texte(app, a.xp + " xp · " + (a.t <= 0 ? "jamais vu" : "vu il y a " + Etat.duree(maintenant - a.t)), Ui.T_DETAIL, p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            c.addView(r, Ui.large());
        }
        groupe.addView(c, Ui.large(app, 6));
    }

    // Amis du Pilou (ajoutés sur le PC) : en ligne, niveau, stade ; et la visite en cours, s'il est parti.
    private void amis(Etat e, long maintenant, Ui.Palette p) {
        if (e.amis.isEmpty() && e.visite.isEmpty()) return;
        groupe.addView(Style.titreSection(app, "Amis de " + e.nom));
        LinearLayout c = Style.carte(app);
        if (!e.visite.isEmpty()) {
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            r.addView(Style.caseSigne(app, "➜", p.orange));
            TextView t = Style.texte(app, e.visite, Ui.T_CORPS, p.orange, true);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            c.addView(r, Ui.large());
        }
        for (int i = 0; i < e.amis.size(); i++) {
            Etat.Ami a = e.amis.get(i);
            if (i > 0 || !e.visite.isEmpty()) c.addView(Style.separateur(app));
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 4));
            // En ligne : cœur plein bleu ; ailleurs : cercle vide gris (la forme dit l'état autant que la couleur).
            boolean la = a.enLigne(maintenant);
            r.addView(Style.caseSigne(app, la ? "♥" : "○", la ? p.bleu : p.argent));
            LinearLayout t = Ui.pile(app);
            t.setPadding(Ui.dp(app, 12), 0, 0, 0);
            t.addView(Style.texte(app, a.nom, Ui.T_CORPS, p.texte, true));
            t.addView(Style.texte(app, a.texte(maintenant), Ui.T_DETAIL, p.doux, false));
            r.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
            c.addView(r, Ui.large());
        }
        groupe.addView(c, Ui.large(app, 6));
    }
}
