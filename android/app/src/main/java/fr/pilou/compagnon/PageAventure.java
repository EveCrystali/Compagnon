package fr.pilou.compagnon;

import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.List;

/**
 * Aventure : les campagnes (docs/CAMPAGNES.md). La liste (celle en cours d'abord, avec son compte à rebours ou « il
 * t'attend ! », puis une carte par campagne : ton, accroche, durée, niveau, progression, fins obtenues), la lecture en
 * conversation (Lecture), et le carnet de voyage (souvenirs, fins, titres, objets).
 */
final class PageAventure extends Page {
    private Lecture lecture;
    private final FrameLayout couche;
    private boolean carnet;
    private String empreinte = "";
    private TextView compte, ligneEnCours;
    private Ui.Barre barreEnCours;
    private Campagnes.Etat etat;

    PageAventure(Principale a) {
        super(a);
        couche = new FrameLayout(a);
        couche.setVisibility(View.GONE);
        addView(couche, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    }

    // ---- Navigation interne

    private boolean enLecture;

    boolean lectureOuverte() {
        return enLecture && lecture != null;
    }

    /** Pour les tests : la lecture (null si jamais ouverte). */
    Lecture lecture() {
        return lecture;
    }

    /** Ouvre la lecture de la campagne en cours (s'il y en a une). */
    void lire() {
        if (!CampagnesTel.pretes()) {
            CampagnesTel.precharger(this::lire);
            return;
        }
        Campagnes.Etat e = CampagnesTel.etat(app);
        if (e == null || !(e.enCours() || e.phase == Campagnes.Phase.Fin || e.phase == Campagnes.Phase.Cassee)) {
            rafraichir();
            return;
        }
        carnet = false;
        if (lecture == null) {
            lecture = new Lecture(app, this);
            addView(lecture, indexOfChild(couche), new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        }
        boolean deja = lectureOuverte();
        enLecture = true;
        lecture.animate().cancel();
        lecture.setVisibility(View.VISIBLE);
        defile.setVisibility(View.INVISIBLE);
        lecture.ouvrir();
        if (!deja && Vitrine.anime(app)) {
            lecture.setTranslationX(Ui.dp(app, 40));
            lecture.setAlpha(0);
            lecture.animate().translationX(0).alpha(1).setDuration(200).setInterpolator(new android.view.animation.DecelerateInterpolator(1.6f)).start();
        }
        app.majBandeau();
    }

    /** Retour à la liste (bouton ‹, touche retour, fin d'aventure). */
    void fermerLecture() {
        if (!lectureOuverte()) return;
        Lecture l = lecture;
        enLecture = false;
        defile.setVisibility(View.VISIBLE);
        empreinte = "";
        rafraichir();
        // Hors du traitement du toucher en cours : la lecture s'efface au tour suivant.
        post(() -> {
            if (enLecture) return;
            if (Vitrine.anime(app)) l.animate().translationX(Ui.dp(app, 40)).alpha(0).setDuration(160).withEndAction(() -> {
                if (!enLecture) l.setVisibility(View.GONE);
            }).start();
            else l.setVisibility(View.GONE);

        });
    }

    void ouvrirCarnet() {
        if (lectureOuverte()) fermerLecture();
        carnet = true;
        empreinte = "";
        rafraichir();
        defile.scrollTo(0, 0);
    }

    @Override
    boolean retour() {
        if (couche.getVisibility() == View.VISIBLE) {
            fermerCouche();
            return true;
        }
        if (lectureOuverte()) {
            if (lecture.coucheOuverte()) lecture.fermerCouche();
            else fermerLecture();
            return true;
        }
        if (carnet) {
            carnet = false;
            empreinte = "";
            rafraichir();
            return true;
        }
        return false;
    }

    @Override
    void retourHaut() {
        if (lectureOuverte()) return;
        if (carnet) retour();
        else super.retourHaut();
    }

    void apresDecision() {
        app.majBandeau();
    }

    // ---- Rafraîchir

    @Override
    void rafraichir() {
        if (!CampagnesTel.pretes()) {
            if (!"chargement".equals(empreinte)) {
                empreinte = "chargement";
                corps.removeAllViews();
                chargement();
            }
            CampagnesTel.precharger(this::rafraichir);
            return;
        }
        if (lectureOuverte()) {
            lecture.rafraichir();
            return;
        }
        etat = CampagnesTel.etat(app);
        Campagnes.Carnet k = CampagnesTel.carnet(app);
        int niveau = Gains.niveau(app, Prefs.etat(app));
        StringBuilder e = new StringBuilder().append(carnet).append('|').append(niveau).append('|').append(Prefs.etat(app).succes).append('|')
                .append(Campagnes.signature(k)).append('|')
                .append(k.nonLus()).append('|').append(etat == null ? "-" : etat.phase + etat.noeud).append('|').append(CampagnesTel.refus(app));
        int[] attente = CampagnesTel.enAttente(app);
        e.append('|').append(attente[0]).append(',').append(attente[1]).append('|').append(evolutionsSignature());
        String nouvelle = e.toString();
        if (!nouvelle.equals(empreinte)) {
            empreinte = nouvelle;
            corps.removeAllViews();
            compte = ligneEnCours = null;
            barreEnCours = null;
            if (carnet) carnet(k);
            else liste(k, niveau, attente);
        }
        tic();
    }

    private void chargement() {
        Ui.Palette p = Ui.p(app);
        corps.addView(Ui.titrePage(app, "Aventure"));
        LinearLayout c = Ui.carte(app);
        c.setGravity(Gravity.CENTER_HORIZONTAL);
        c.addView(new Aventure.Points(app, p.doux));
        TextView t = Ui.texte(app, "Pilou déplie ses cartes…", Ui.T_CORPS, p.doux, false);
        t.setPadding(0, Ui.dp(app, 10), 0, 0);
        c.addView(t);
        corps.addView(c, Ui.large());
    }

    /** Chaque seconde : le compte à rebours de la carte « en cours ». */
    private void tic() {
        if (compte == null || etat == null || !etat.enAttente()) return;
        long reste = etat.fin - CampagnesTel.maintenant();
        compte.setText(Aventure.compte(reste));
        compte.setContentDescription("Encore " + CampagnesTel.reste(reste));
        if (barreEnCours != null) barreEnCours.part(1 - reste / (float) Math.max(1, etat.fin - etat.t));
        if (reste <= 0) empreinte = ""; // il est revenu : la carte change
    }

    // ---- La liste

    private void liste(Campagnes.Carnet k, int niveau, int[] attente) {
        Ui.Palette p = Ui.p(app);
        corps.addView(Ui.titrePage(app, "Aventure"));
        corps.addView(Ui.sousTitre(app, "Pilou t'écrit, tu choisis, et il part pour de vrai."));
        if (attente[0] + attente[1] > 0) {
            TextView t = Ui.puceTexte(app, "◉  " + attente[0] + " po · ✦ " + attente[1] + " xp gagnés en aventure attendent ton PC", p.orange);
            t.setSingleLine(false);
            corps.addView(t, Ui.large(app, 14));
        }
        Campagnes.Partie q = k.courante;
        Campagnes.Campagne enCours = etat != null && q != null && (etat.enCours() || etat.phase == Campagnes.Phase.Fin && k.nonLus() > 0)
                ? Campagnes.charger(q.campagne) : null;
        if (enCours != null) {
            corps.addView(Ui.titreSection(app, "En cours"));
            corps.addView(enCours(enCours), Ui.large(app, 8));
        }
        corps.addView(Ui.titreSection(app, enCours != null ? "Les autres aventures" : "Les aventures"));
        boolean occupe = etat != null && etat.enCours();
        for (Campagnes.Campagne c : CampagnesTel.catalogue()) {
            if (enCours != null && c.id.equals(enCours.id)) continue;
            corps.addView(carteCampagne(c, k, niveau, occupe ? q.campagne : null), Ui.large(app, 14));
        }
        // Le carnet de voyage.
        int fins = 0, souvenirs = 0;
        for (Campagnes.Campagne c : CampagnesTel.catalogue()) {
            fins += Campagnes.fins(k, c).size();
            souvenirs += Campagnes.souvenirs(k, c).size();
        }
        LinearLayout cc = Ui.carte(app);
        cc.setBackground(Ui.touchable(app, Ui.arrondi(app, p.surface, 18, p.bord), 18));
        LinearLayout r = Ui.rangee(app);
        r.addView(Ui.pastille(app, "◈", Aventure.accentTon(app, "emotion")));
        LinearLayout t = Ui.pile(app);
        t.setPadding(Ui.dp(app, 12), 0, 0, 0);
        t.addView(Ui.texte(app, "Carnet de voyage", Ui.T_CORPS, p.texte, true));
        t.addView(Ui.texte(app, fins == 0 ? "Les souvenirs de vos aventures s'y rangeront." : fins + " fin" + (fins > 1 ? "s" : "") + " · " + souvenirs
                + " souvenir" + (souvenirs > 1 ? "s" : ""), Ui.T_DETAIL, p.doux, false));
        r.addView(t, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        r.addView(Ui.texte(app, "›", 22, p.doux, false));
        cc.addView(r, Ui.large());
        cc.setOnClickListener(v -> ouvrirCarnet());
        cc.setContentDescription("Carnet de voyage. " + fins + " fins obtenues.");
        Ui.enfoncer(cc);
        corps.addView(cc, Ui.large(app, 12));
        TextView note = Ui.texte(app, "Une aventure à la fois. Pilou avance même téléphone posé et PC éteint ; seuls ses gains attendent le PC.",
                Ui.T_DETAIL, p.doux, false);
        note.setPadding(Ui.dp(app, 4), Ui.dp(app, 4), Ui.dp(app, 4), 0);
        corps.addView(note);
    }

    /** La carte de la campagne en cours : Pilou dans sa scène, et ce qu'il fait (en route, il t'attend…). */
    private View enCours(Campagnes.Campagne c) {
        Ui.Palette p = Ui.p(app);
        LinearLayout carte = Ui.pile(app);
        carte.setBackground(Ui.touchable(app, Ui.arrondi(app, p.surface, 18, Aventure.accentTon(app, c.ton)), 18));
        carte.setClipToOutline(true);
        carte.setElevation(Ui.dp(app, 2));
        FrameLayout s = scene(c, etat.decor, 150, true);
        LinearLayout chips = Ui.rangee(app);
        chips.setPadding(Ui.dp(app, 12), Ui.dp(app, 12), Ui.dp(app, 12), 0);
        chips.addView(Ui.puceScene(app, Aventure.signeTon(c.ton) + "  Chapitre " + etat.chapitreNumero + " / " + etat.chapitreTotal));
        s.addView(chips, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP));
        carte.addView(s, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, hauteurScene()));
        LinearLayout corpsCarte = Ui.pile(app);
        corpsCarte.setPadding(Ui.dp(app, 16), Ui.dp(app, 14), Ui.dp(app, 16), Ui.dp(app, 16));
        corpsCarte.addView(Ui.texte(app, c.titre, Ui.T_CARTE, p.texte, true));
        boolean attend = CampagnesTel.attendJoueur(app, etat);
        if (etat.enAttente()) {
            boolean repos = etat.phase == Campagnes.Phase.Repos;
            ligneEnCours = Ui.texte(app, (repos ? "Pilou se repose" : etat.pendant.isEmpty() ? "Pilou est en route" : etat.pendant)
                    + " · " + (repos ? "reprise" : "retour") + " vers " + CampagnesTel.heure(etat.fin), Ui.T_DETAIL, p.doux, false);
            ligneEnCours.setPadding(0, Ui.dp(app, 4), 0, 0);
            corpsCarte.addView(ligneEnCours, Ui.large());
            LinearLayout r = Ui.rangee(app);
            r.setPadding(0, Ui.dp(app, 8), 0, Ui.dp(app, 6));
            compte = Ui.texte(app, "", 26, Aventure.accentTon(app, c.ton), true);
            compte.setTypeface(android.graphics.Typeface.create("monospace", android.graphics.Typeface.BOLD));
            r.addView(compte);
            corpsCarte.addView(r);
            barreEnCours = new Ui.Barre(app);
            corpsCarte.addView(barreEnCours, Ui.large());
        } else {
            String quoi = etat.phase == Campagnes.Phase.Fin ? "★  Le dénouement t'attend !" : attend ? "●  Il t'attend !" : "Lis la suite de son aventure.";
            TextView t = Ui.texte(app, quoi, Ui.T_CORPS, attend ? p.orange : p.doux, attend);
            t.setPadding(0, Ui.dp(app, 6), 0, 0);
            corpsCarte.addView(t, Ui.large());
            if (attend && !etat.lieu.isEmpty()) {
                TextView l = Ui.texte(app, etat.lieu, Ui.T_DETAIL, p.doux, false);
                corpsCarte.addView(l, Ui.large());
            }
            if (attend && Vitrine.anime(app)) {
                // Un battement discret, deux fois, pour attirer l'œil sans insister.
                t.animate().scaleX(1.04f).scaleY(1.04f).setDuration(260).withEndAction(() -> t.animate().scaleX(1).scaleY(1).setDuration(260).start()).start();
                t.setPivotX(0);
            }
        }
        Button b = Ui.bouton(app, etat.enAttente() ? "Relire la conversation" : "Lire la suite", !etat.enAttente(), v -> lire());
        LinearLayout.LayoutParams lb = Ui.large();
        lb.topMargin = Ui.dp(app, 12);
        corpsCarte.addView(b, lb);
        carte.addView(corpsCarte, Ui.large());
        carte.setOnClickListener(v -> lire());
        carte.setContentDescription(c.titre + ", en cours. " + (attend ? "Pilou t'attend." : ""));
        Ui.enfoncer(carte);
        return carte;
    }

    /** L'unité de pixel des scènes de cette page : celle du décor fin, comme dans la lecture (Aventure.unite). */
    private int uniteScene() {
        return Aventure.unite(app.getResources().getDisplayMetrics().widthPixels - 2 * Ui.dp(app, 16));
    }

    /** Une scène miniature montre le décor entier : 80 pixels fins de haut. */
    private int hauteurScene() {
        return Theatre.H * uniteScene();
    }

    /** Une scène miniature (décor de la campagne), avec Pilou s'il est demandé. */
    private FrameLayout scene(Campagnes.Campagne c, String decor, int hauteur, boolean avecPilou) {
        FrameLayout s = new FrameLayout(app);
        Aventure.Scene sc = new Aventure.Scene(app);
        if (decor == null || decor.isEmpty()) {
            Campagnes.Noeud n = c.noeud(c.depart);
            decor = n == null ? "" : n.decor;
            if (decor.isEmpty() && !c.decors.isEmpty()) decor = c.decors.get(0).id;
        }
        sc.regler(c.id, c.ton, decor);
        s.addView(sc, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        if (avecPilou && etat != null) {
            PilouVue pv = new PilouVue(app, Aventure.pixelUnite(uniteScene()), true);
            Etat pc = Prefs.etat(app);
            pv.equipe(Gains.porte(app, pc));
            pv.accessoire(pc.accessoire);
            if (etat.phase == Campagnes.Phase.Attente) {
                pv.tenue("voyage-" + etat.tenue);
                sc.marcher(Aventure.vitesse(etat.tenue), etat.tenue.equals("nuit"));
                pv.montrer("repos", pc.couleur);
            } else if (etat.phase == Campagnes.Phase.Repos) {
                pv.tenue("voyage-nuit");
                pv.objets(java.util.Collections.singletonList("pansement"));
                sc.marcher(0, true);
                pv.montrer("fatigue", pc.couleur);
            } else pv.montrer(CampagnesTel.attendJoueur(app, etat) ? "joie" : Lecture.humeurPilou(etat.humeur), pc.couleur);
            pv.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM | Gravity.START);
            lp.leftMargin = Ui.dp(app, 14);
            s.addView(pv, lp);
        }
        return s;
    }

    private View carteCampagne(Campagnes.Campagne c, Campagnes.Carnet k, int niveau, String autreEnCours) {
        Ui.Palette p = Ui.p(app);
        // Fermée : il manque le niveau, un haut fait (reçu du PC) ou une campagne à finir ; la ligne dit quoi, sans rien dévoiler.
        String manque = Campagnes.manque(k, c, niveau, Prefs.etat(app).succes, Campagnes::charger);
        boolean ouverte = manque.isEmpty(), parNiveau = niveau < c.niveau;
        boolean niveauSeul = parNiveau && manque.equals("s'ouvre au niveau " + c.niveau);
        String verrou = parNiveau ? "Niveau " + c.niveau : !c.succes.isEmpty() && !Prefs.etat(app).succes.containsAll(c.succes) ? "Haut fait" : "À suivre";
        Campagnes.Partie suspendue = k.suspendues.get(c.id);
        Campagnes.Etat ee = null;
        // Mise de côté à l'instant : elle est encore « la partie courante », abandonnée.
        if (suspendue == null && k.courante != null && k.courante.campagne.equals(c.id) && etat != null && etat.phase == Campagnes.Phase.Abandon) {
            suspendue = k.courante;
            ee = etat;
        }
        boolean finie = Campagnes.finie(k, c.id);
        List<Campagnes.FinObtenue> fins = Campagnes.fins(k, c);
        int total = CampagnesTel.nombreFins(c);
        LinearLayout carte = Ui.pile(app);
        carte.setBackground(Ui.arrondi(app, p.surface, 18, p.bord));
        carte.setClipToOutline(true);
        carte.setElevation(Ui.dp(app, 1));
        FrameLayout s = scene(c, null, 96, false);
        s.setAlpha(ouverte ? 1 : 0.55f);
        LinearLayout chips = Ui.rangee(app);
        chips.setPadding(Ui.dp(app, 12), Ui.dp(app, 12), Ui.dp(app, 12), 0);
        chips.addView(Ui.puceScene(app, Aventure.signeTon(c.ton) + "  " + Aventure.nomTon(c.ton)));
        View vide = new View(app);
        chips.addView(vide, new LinearLayout.LayoutParams(0, 1, 1));
        String statut = !ouverte ? "◇  " + verrou : suspendue != null ? "◐  Mise de côté" : finie ? "✓  Finie" : c.id.equals("prologue") ? "✦  Pour commencer" : "";
        if (!statut.isEmpty()) chips.addView(Ui.puceScene(app, statut));
        s.addView(chips, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP));
        carte.addView(s, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, hauteurScene()));

        LinearLayout b = Ui.pile(app);
        b.setPadding(Ui.dp(app, 16), Ui.dp(app, 14), Ui.dp(app, 16), Ui.dp(app, 16));
        b.addView(Ui.texte(app, c.titre, Ui.T_CARTE, ouverte ? p.texte : p.doux, true));
        TextView acc = Ui.texte(app, c.accroche, Ui.T_CORPS, ouverte ? p.texte : p.doux, false);
        acc.setPadding(0, Ui.dp(app, 4), 0, 0);
        acc.setMaxLines(4);
        acc.setEllipsize(android.text.TextUtils.TruncateAt.END);
        b.addView(acc, Ui.large());
        String meta = "◷ " + c.duree + "  ·  " + c.chapitres.size() + " chapitre" + (c.chapitres.size() > 1 ? "s" : "")
                + (c.niveau > 1 ? "  ·  niveau " + c.niveau : "");
        TextView m = Ui.texte(app, meta, Ui.T_DETAIL, p.doux, false);
        m.setPadding(0, Ui.dp(app, 8), 0, 0);
        b.addView(m, Ui.large());
        if (suspendue != null) {
            int rang = CampagnesTel.chapitreReprise(c, suspendue, ee) - 1;
            String l = CampagnesTel.lieuReprise(c, suspendue, ee);

            TextView pr = Ui.texte(app, "Chapitre " + (rang + 1) + " / " + c.chapitres.size() + (l.isEmpty() ? "" : " · reprise : " + l), Ui.T_DETAIL, p.texte, true);
            pr.setPadding(0, Ui.dp(app, 8), 0, Ui.dp(app, 4));
            b.addView(pr, Ui.large());
            Ui.Barre barre = new Ui.Barre(app);
            barre.part((rang + 0.5f) / Math.max(1, c.chapitres.size()));
            b.addView(barre, Ui.large());
        }
        if (!fins.isEmpty() || finie) {
            StringBuilder sg = new StringBuilder();
            for (Campagnes.FinObtenue f : fins) sg.append(Aventure.signeIssue(f.issue)).append(' ');
            for (int i = fins.size(); i < total; i++) sg.append("? ");
            TextView tf = Ui.texte(app, "Fins " + fins.size() + " / " + total + "   " + sg.toString().trim(), Ui.T_DETAIL, Aventure.accentTon(app, c.ton), true);
            tf.setPadding(0, Ui.dp(app, 8), 0, 0);
            tf.setContentDescription(fins.size() + " fins obtenues sur " + total);
            b.addView(tf, Ui.large());
        }
        // Les actions.
        LinearLayout actions = Ui.rangee(app);
        actions.setPadding(0, Ui.dp(app, 14), 0, 0);
        String refus = autreEnCours != null ? "Une aventure à la fois : « " + titre(autreEnCours) + " » est en cours." : null;
        if (!ouverte) {
            int ecart = c.niveau - niveau;
            Button v = Ui.bouton(app, niveauSeul ? "◇  Niveau " + c.niveau + " requis" : "◇  " + verrou, false, x -> {
            });
            v.setEnabled(false);
            v.setAlpha(0.7f);
            actions.addView(v, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            String ligne = niveauSeul ? "Encore " + ecart + " niveau" + (ecart > 1 ? "x" : "") + " : Pilou grandit en jouant et pendant que tu travailles."
                    : Character.toUpperCase(manque.charAt(0)) + manque.substring(1) + ".";
            TextView t = Ui.texte(app, ligne, Ui.T_DETAIL, p.doux, false);
            t.setPadding(0, Ui.dp(app, 8), 0, 0);
            b.addView(actions, Ui.large());
            b.addView(t, Ui.large());
        } else {
            if (suspendue != null) {
                Button rep = Ui.bouton(app, "Reprendre", true, x -> demarrer(c, false));
                Button neuf = Ui.bouton(app, "Recommencer", false, x -> confirmerRecommencer(c));
                LinearLayout.LayoutParams l1 = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
                l1.rightMargin = Ui.dp(app, 8);
                actions.addView(rep, l1);
                actions.addView(neuf, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            } else {
                Button go = Ui.bouton(app, finie ? "Rejouer" : "Commencer", !finie, x -> demarrer(c, finie));
                actions.addView(go, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            }
            for (int i = 0; i < actions.getChildCount(); i++) {
                View v = actions.getChildAt(i);
                v.setEnabled(refus == null);
                v.setAlpha(refus == null ? 1 : 0.5f);
                Ui.enfoncer(v);
            }
            b.addView(actions, Ui.large());
            if (refus != null) {
                TextView t = Ui.texte(app, refus, Ui.T_DETAIL, p.doux, false);
                t.setPadding(0, Ui.dp(app, 8), 0, 0);
                b.addView(t, Ui.large());
            }
        }
        carte.addView(b, Ui.large());
        carte.setContentDescription(c.titre + ". " + Aventure.nomTon(c.ton) + ". " + c.accroche);
        return carte;
    }

    private static String titre(String id) {
        Campagnes.Campagne c = Campagnes.charger(id);
        return c == null ? id : c.titre;
    }

    private void demarrer(Campagnes.Campagne c, boolean neuf) {
        String r = CampagnesTel.demarrer(app, c.id, neuf);
        if (r != null) {
            android.widget.Toast.makeText(app, r, android.widget.Toast.LENGTH_LONG).show();
            return;
        }
        Ui.vibrer(app, 10);
        empreinte = "";
        lire();
    }

    /** Depuis la carte de fin : rejouer la campagne du début. */
    void rejouer(Campagnes.Campagne c) {
        fermerLecture();
        post(() -> demarrer(c, true));
    }

    private void confirmerRecommencer(Campagnes.Campagne c) {
        montrerCouche(Aventure.feuille(app, "Recommencer « " + c.titre + " » ?",
                "Pilou repart du tout début. La partie mise de côté est remplacée ; les fins, les souvenirs et les titres déjà gagnés restent à toi.",
                this::fermerCouche,
                "Recommencer du début", false, (View.OnClickListener) v -> {
                    fermerCouche();
                    demarrer(c, true);
                },
                "Garder ma partie", true, (View.OnClickListener) v -> fermerCouche()));
    }

    private void montrerCouche(View v) {
        couche.removeAllViews();
        couche.addView(v, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        couche.setVisibility(View.VISIBLE);
        couche.bringToFront();
    }

    private void fermerCouche() {
        post(() -> {
            couche.removeAllViews();
            couche.setVisibility(View.GONE);
        });
    }

    // ---- Le carnet de voyage

    /** Le stade d'évolution atteint : celui du PC, sinon celui du niveau (comme l'accueil). */
    private int stadeAtteint() {
        Etat e = Prefs.etat(app);
        return e.stade > 0 ? e.stade : Acces.stade(Gains.niveau(app, e));
    }

    /** Ce que le carnet montre des évolutions (change quand un stade est atteint ou qu'un choix est gardé) : sert à l'empreinte. */
    private String evolutionsSignature() {
        StringBuilder b = new StringBuilder().append(stadeAtteint());
        for (int s = 2; s <= 4; s++) b.append(',').append(SceneEvolution.garde(app, s));
        return b.toString();
    }

    /** « Ses évolutions » : pour chaque stade atteint (2 à 4), le titre de la scène, ce que Pilou a gardé, et « ▸ revoir ». */
    private void evolutions() {
        Ui.Palette p = Ui.p(app);
        int atteint = stadeAtteint();
        boolean titre = false;
        for (int stade = 2; stade <= atteint; stade++) {
            Evolutions.Scene sc = Evolutions.scenes().get(stade);
            if (sc == null) continue;
            if (!titre) {
                corps.addView(Ui.titreSection(app, "Ses évolutions"));
                titre = true;
            }
            LinearLayout carte = Ui.carte(app);
            carte.addView(Ui.texte(app, Acces.nomStade(stade), Ui.T_DETAIL, p.doux, false));
            carte.addView(Ui.texte(app, sc.titre, Ui.T_CARTE, p.texte, true));
            String id = SceneEvolution.garde(app, stade);
            String libelle = id == null ? null : sc.libelle(id);
            if (libelle != null) carte.addView(Ui.texte(app, "il a gardé : " + libelle, Ui.T_CORPS, p.texte, false), Ui.large(app, 2));
            final int st = stade;
            TextView revoir = Ui.texte(app, "▸ revoir", Ui.T_CORPS, p.bleu, true);
            revoir.setMinHeight(Ui.dp(app, 48));
            revoir.setGravity(Gravity.CENTER_VERTICAL);
            revoir.setContentDescription("Revoir la scène : " + sc.titre);
            revoir.setOnClickListener(v -> app.ouvrirEvolution(st));
            carte.addView(revoir);
            corps.addView(carte, Ui.large(app, 10));
        }
    }

    private void carnet(Campagnes.Carnet k) {
        Ui.Palette p = Ui.p(app);
        TextView retour = Ui.texte(app, "‹  Aventures", Ui.T_CORPS, p.bleu, true);
        retour.setMinHeight(Ui.dp(app, 48));
        retour.setGravity(Gravity.CENTER_VERTICAL);
        retour.setPadding(Ui.dp(app, 2), 0, Ui.dp(app, 12), 0);
        retour.setOnClickListener(v -> retour());
        LinearLayout.LayoutParams lr = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        corps.addView(retour, lr);
        TextView titre = Ui.titrePage(app, "Carnet de voyage");
        titre.setPadding(0, 0, 0, Ui.dp(app, 2));
        corps.addView(titre);
        corps.addView(Ui.sousTitre(app, "Les fins, les souvenirs et les titres de vos aventures."));
        evolutions();
        boolean rien = true;
        for (Campagnes.Campagne c : CampagnesTel.catalogue()) {
            List<Campagnes.FinObtenue> fins = Campagnes.fins(k, c);
            if (fins.isEmpty() && !k.suspendues.containsKey(c.id) && (k.courante == null || !k.courante.campagne.equals(c.id))) continue;
            rien = false;
            LinearLayout carte = Ui.carte(app);
            LinearLayout tete = Ui.rangee(app);
            tete.addView(Ui.pastille(app, Aventure.signeTon(c.ton), Aventure.accentTon(app, c.ton)));
            LinearLayout tt = Ui.pile(app);
            tt.setPadding(Ui.dp(app, 12), 0, 0, 0);
            tt.addView(Ui.texte(app, c.titre, Ui.T_CARTE, p.texte, true));
            List<Campagnes.Noeud> toutes = CampagnesTel.finsDe(c);
            tt.addView(Ui.texte(app, fins.size() + " / " + toutes.size() + " fins découvertes", Ui.T_DETAIL, p.doux, false));
            tete.addView(tt, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            carte.addView(tete, Ui.large());
            LinearLayout.LayoutParams lg = Ui.large();
            lg.topMargin = Ui.dp(app, 12);
            carte.addView(grilleFins(app, c, fins, toutes, null), lg);
            List<Campagnes.Nomme> souvenirs = Campagnes.souvenirs(k, c);
            if (!souvenirs.isEmpty()) {
                carte.addView(etiquette("Souvenirs"));
                for (Campagnes.Nomme s : souvenirs) {
                    LinearLayout sv = Ui.pile(app);
                    sv.setBackground(Ui.arrondi(app, p.surface2, 12, 0));
                    sv.setPadding(Ui.dp(app, 12), Ui.dp(app, 10), Ui.dp(app, 12), Ui.dp(app, 10));
                    sv.addView(Ui.texte(app, "◈  " + s.nom, Ui.T_CORPS, p.texte, true));
                    if (!s.texte.isEmpty()) sv.addView(Ui.texte(app, s.texte, Ui.T_DETAIL, p.doux, false));
                    carte.addView(sv, Ui.large(app, 6));
                }
            }
            List<String> titres = Campagnes.titres(k, c);
            if (!titres.isEmpty()) {
                carte.addView(etiquette("Titres"));
                for (String t : titres) carte.addView(Ui.texte(app, "« " + t + " »", Ui.T_CORPS, p.texte, true), Ui.large(app, 2));
            }
            List<String> objets = Campagnes.objetsGagnes(k, c);
            if (!objets.isEmpty()) {
                carte.addView(etiquette("Objets exclusifs"));
                LinearLayout ro = Ui.rangee(app);
                for (String o : objets) {
                    LinearLayout col = Ui.pile(app);
                    col.setGravity(Gravity.CENTER_HORIZONTAL);
                    col.setPadding(0, 0, Ui.dp(app, 12), 0);
                    col.addView(imageObjet(app, o, 0.8f));
                    String nom = o;
                    for (Campagnes.Nomme x : c.objets) if (x.id.equals(o)) nom = x.nom;
                    TextView tn = Ui.texte(app, nom, Ui.T_DETAIL, p.texte, false);
                    tn.setMaxWidth(Ui.dp(app, 96));
                    tn.setGravity(Gravity.CENTER);
                    col.addView(tn);
                    ro.addView(col);
                }
                android.widget.HorizontalScrollView hs = new android.widget.HorizontalScrollView(app);
                hs.setHorizontalScrollBarEnabled(false);
                hs.addView(ro);
                carte.addView(hs, Ui.large());
            }
            corps.addView(carte, Ui.large(app, 14));
        }
        if (rien) {
            LinearLayout c = Ui.carte(app);
            c.setGravity(Gravity.CENTER_HORIZONTAL);
            PilouVue pv = new PilouVue(app, Aventure.pixelUnite(uniteScene()), true);
            pv.montrer("tendre", Prefs.etat(app).couleur);
            pv.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            c.addView(pv);
            TextView t = Ui.texte(app, "Ton carnet est encore vierge", Ui.T_CARTE, p.texte, true);
            t.setGravity(Gravity.CENTER);
            t.setPadding(0, Ui.dp(app, 8), 0, Ui.dp(app, 4));
            c.addView(t, Ui.large());
            TextView t2 = Ui.texte(app, "Chaque fin d'aventure y laisse un souvenir, un titre, parfois un objet que personne d'autre n'a.", Ui.T_CORPS, p.doux, false);
            t2.setGravity(Gravity.CENTER);
            c.addView(t2, Ui.large());
            Campagnes.Campagne pro = Campagnes.charger("prologue");
            if (pro != null && (k.courante == null || !CampagnesTel.etat(app).enCours())) {
                LinearLayout.LayoutParams lb = Ui.large();
                lb.topMargin = Ui.dp(app, 14);
                c.addView(Ui.bouton(app, "Commencer le prologue", true, v -> {
                    carnet = false;
                    demarrer(pro, false);
                }), lb);
            }
            corps.addView(c, Ui.large());
        }
    }

    private TextView etiquette(String s) {
        TextView t = Ui.texte(app, s.toUpperCase(java.util.Locale.FRENCH), Ui.T_ETIQUETTE, Ui.p(app).doux, true);
        t.setLetterSpacing(0.08f);
        t.setPadding(0, Ui.dp(app, 14), 0, Ui.dp(app, 6));
        return t;
    }

    // ---- Pièces partagées avec la lecture

    /** Les fins d'une campagne, deux par ligne : obtenues (signe, titre), à découvrir (« ? ? ? »). */
    static View grilleFins(Principale a, Campagnes.Campagne c, List<Campagnes.FinObtenue> obtenues, List<Campagnes.Noeud> toutes, String nouvelle) {
        Ui.Palette p = Ui.p(a);
        LinearLayout g = Ui.pile(a);
        LinearLayout rang = null;
        for (int i = 0; i < toutes.size(); i++) {
            if (i % 2 == 0) {
                rang = Ui.rangee(a);
                rang.setGravity(Gravity.TOP);
                g.addView(rang, Ui.large(a, 6));
            }
            Campagnes.Noeud n = toutes.get(i);
            Campagnes.FinObtenue f = null;
            for (Campagnes.FinObtenue x : obtenues) if (x.noeud.equals(n.id)) f = x;
            LinearLayout cell = Ui.pile(a);
            boolean neuve = f != null && n.id.equals(nouvelle);
            int couleur = f == null ? p.doux : Aventure.couleurIssue(a, f.issue);
            cell.setBackground(Ui.arrondi(a, f == null ? p.surface2 : (couleur & 0x00ffffff) | 0x1c000000, 12, neuve ? couleur : 0));
            cell.setPadding(Ui.dp(a, 10), Ui.dp(a, 8), Ui.dp(a, 10), Ui.dp(a, 8));
            cell.setMinimumHeight(Ui.dp(a, 56));
            if (f != null) {
                cell.addView(Ui.texte(a, Aventure.signeIssue(f.issue) + "  " + Aventure.nomIssue(f.issue).replace("Fin ", "").replace(" fin", ""), Ui.T_ETIQUETTE, couleur, true));
                TextView t = Ui.texte(a, f.titre, Ui.T_DETAIL, p.texte, true);
                t.setMaxLines(2);
                t.setEllipsize(android.text.TextUtils.TruncateAt.END);
                cell.addView(t);
                cell.setContentDescription(Aventure.nomIssue(f.issue) + " : " + f.titre);
            } else {
                cell.addView(Ui.texte(a, "?  À découvrir", Ui.T_ETIQUETTE, p.doux, true));
                cell.addView(Ui.texte(a, "? ? ?", Ui.T_DETAIL, p.doux, true));
                cell.setContentDescription("Fin pas encore découverte");
            }
            LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
            if (i % 2 == 0) l.rightMargin = Ui.dp(a, 6);
            else l.leftMargin = Ui.dp(a, 6);
            rang.addView(cell, l);
        }
        if (toutes.size() % 2 == 1 && rang != null) rang.addView(new View(a), new LinearLayout.LayoutParams(0, 1, 1));
        return g;
    }

    /** L'objet exclusif : Pilou qui le porte (dessin de la banque), ou un « ? » le temps que l'illustrateur le dessine. */
    static View imageObjet(Principale a, String id, float k) {
        Ui.Palette p = Ui.p(a);
        float d = a.getResources().getDisplayMetrics().density;
        if (Sprites.banque().get(id) != null) {
            ImageView im = new ImageView(a);
            RenduPilou.Allure al = Dessin.allure("joie", 0, Prefs.etat(a).couleur, "", false, 0);
            al.objets = java.util.Collections.singletonList(id);
            im.setImageBitmap(Vitrine.pilou(al, 1.4f * k * d, false));
            im.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            return im;
        }
        TextView t = Ui.texte(a, "?", 28, p.doux, true);
        t.setGravity(Gravity.CENTER);
        t.setBackground(Ui.arrondi(a, p.surface2, 14, p.bord));
        int c = Math.round(Ui.dp(a, 64) * k);
        t.setLayoutParams(new LinearLayout.LayoutParams(c, c));
        t.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        return t;
    }
}
