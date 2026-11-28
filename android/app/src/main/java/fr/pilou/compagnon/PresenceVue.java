package fr.pilou.compagnon;

import android.graphics.Typeface;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Locale;

/**
 * Sur l'Accueil, la carte « Pilou et moi » (docs/PRESENCE.md) : complicité (palier, jours ensemble, jauge vers le palier
 * suivant), la question du prénom (une seule fois, refuser aussi simple qu'accepter), et le journal de Pilou, feuilletable
 * jour par jour, avec un petit dessin de lui dans l'humeur du jour. Et, dans les Réglages, la section « Pilou et moi ».
 */
final class PresenceVue extends LinearLayout {
    private final Principale app;
    private final TextView palier, jours, suite, date, humeur, texte, page;
    private final Style.Barre jauge;
    private final ImageView dessin;
    private final LinearLayout question, journal;
    private final TextView avant, apres;
    private List<Presence.Entree> entrees = java.util.Collections.emptyList();
    private int i;
    private String empreinte = "";

    PresenceVue(Principale a) {
        super(a);
        app = a;
        setOrientation(VERTICAL);
        Ui.Palette p = Ui.p(a);
        Style.fond(this, Style.arrondi(a, p.surface, 18, p.bord));
        int m = Ui.dp(a, 16);
        setPadding(m, Ui.dp(a, 14), m, Ui.dp(a, 14));
        addView(Style.texte(a, "♥  Pilou et moi", Ui.T_CARTE, p.texte, true), Ui.large());
        LinearLayout r = Ui.rangee(a);
        r.setPadding(0, Ui.dp(a, 6), 0, 0);
        palier = Style.texte(a, "", Ui.T_CORPS, p.bleu, true);
        r.addView(palier);
        jours = Style.texte(a, "", Ui.T_DETAIL, p.doux, false);
        jours.setPadding(Ui.dp(a, 10), 0, 0, 0);
        r.addView(jours, new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1));
        addView(r, Ui.large());
        jauge = new Style.Barre(a);
        LayoutParams lj = Ui.large();
        lj.topMargin = Ui.dp(a, 8);
        addView(jauge, lj);
        suite = Style.texte(a, "", Ui.T_ETIQUETTE, p.doux, false);
        suite.setPadding(0, Ui.dp(a, 4), 0, 0);
        addView(suite, Ui.large());

        // La question du prénom (seulement quand Pilou la pose : une fois).
        question = Ui.pile(a);
        question.setVisibility(GONE);
        addView(question, Ui.large());

        // Le journal.
        journal = Ui.pile(a);
        journal.setPadding(0, Ui.dp(a, 12), 0, 0);
        LinearLayout tete = Ui.rangee(a);
        avant = fleche("◀", "Page précédente du journal", v -> feuilleter(1));
        tete.addView(avant);
        LinearLayout centre = Ui.pile(a);
        centre.setGravity(Gravity.CENTER_HORIZONTAL);
        TextView titre = Style.texte(a, "Le journal de Pilou", Ui.T_ETIQUETTE, p.doux, true);
        titre.setGravity(Gravity.CENTER);
        centre.addView(titre, Ui.large());
        date = Style.texte(a, "", Ui.T_CORPS, p.texte, true);
        date.setGravity(Gravity.CENTER);
        centre.addView(date, Ui.large());
        tete.addView(centre, new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1));
        apres = fleche("▶", "Page suivante du journal", v -> feuilleter(-1));
        tete.addView(apres);
        journal.addView(tete, Ui.large());
        LinearLayout corpsJ = Ui.rangee(a);
        corpsJ.setGravity(Gravity.TOP);
        corpsJ.setPadding(0, Ui.dp(a, 8), 0, 0);
        dessin = new ImageView(a);
        dessin.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        corpsJ.addView(dessin);
        LinearLayout droite = Ui.pile(a);
        droite.setPadding(Ui.dp(a, 12), 0, 0, 0);
        humeur = Style.texte(a, "", Ui.T_ETIQUETTE, p.doux, false);
        droite.addView(humeur, Ui.large());
        texte = Style.texte(a, "", Ui.T_CORPS, p.texte, false);
        texte.setLineSpacing(Ui.dp(a, 2), 1f);
        droite.addView(texte, Ui.large());
        corpsJ.addView(droite, new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1));
        journal.addView(corpsJ, Ui.large());
        page = Style.texte(a, "", Ui.T_ETIQUETTE, p.doux, false);
        page.setGravity(Gravity.CENTER);
        page.setPadding(0, Ui.dp(a, 6), 0, 0);
        journal.addView(page, Ui.large());
        addView(journal, Ui.large());
    }

    private TextView fleche(String s, String description, OnClickListener l) {
        Ui.Palette p = Ui.p(app);
        TextView t = Style.texte(app, s, 18, p.bleu, true);
        t.setGravity(Gravity.CENTER);
        t.setMinWidth(Ui.dp(app, 48));
        t.setMinHeight(Ui.dp(app, 48));
        t.setContentDescription(description);
        Style.fond(t, Style.touchable(app, Style.arrondi(app, 0x00000000, 14, 0), 14));
        t.setOnClickListener(l);
        return t;
    }

    private void feuilleter(int pas) {
        i = Math.max(0, Math.min(Math.max(0, entrees.size() - 1), i + pas));
        empreinte = "";
        rafraichir();
    }

    static String signe(String humeur) {
        switch (humeur) {
            case "fete": return "★ jour de fête";
            case "tendre": return "♥ tout doux";
            case "caresse": return "♥ bien soigné";
            case "joie": return "☀ content";
            case "fatigue": return "☾ un peu fatigué";
            case "concentre": return "✎ appliqué";
            default: return "· tranquille";
        }
    }

    static String dateLongue(String jour) {
        try {
            String s = LocalDate.parse(jour).format(DateTimeFormatter.ofPattern("EEEE d MMMM", Locale.FRENCH));
            return Character.toUpperCase(s.charAt(0)) + s.substring(1);
        } catch (RuntimeException e) {
            return jour;
        }
    }

    void rafraichir() {
        try {
            Presence.Etat e = PresenceTel.etat(app);
            Presence.Totaux t = e.totaux();
            String emp = t.points + "|" + t.jours + "|" + e.journal.size() + "|" + e.texte().hashCode() + "|" + i + "|" + PresenceTel.demanderPrenom(app);
            if (emp.equals(empreinte)) return;
            empreinte = emp;
            Ui.Palette p = Ui.p(app);
            palier.setText(Presence.nomPalier(t.palier));
            jours.setText(t.jours + " jour" + (t.jours > 1 ? "s" : "") + " ensemble");
            boolean haut = t.palier + 1 >= Presence.SEUILS.length;
            int bas = Presence.SEUILS[t.palier], cible = haut ? bas : Presence.SEUILS[t.palier + 1];
            jauge.part(haut ? 1 : (t.points - bas) / (float) Math.max(1, cible - bas));
            suite.setText(haut ? "★ le plus haut palier : inséparables" : "vers « " + Presence.nomPalier(t.palier + 1) + " » — la complicité ne baisse jamais");
            setContentDescription("Pilou et moi : " + Presence.nomPalier(t.palier) + ", " + t.jours + " jours ensemble.");
            questionPrenom(p);
            entrees = e.entrees(Presence.gabarits());
            i = Math.min(i, Math.max(0, entrees.size() - 1));
            avant.setVisibility(i < entrees.size() - 1 ? VISIBLE : INVISIBLE);
            apres.setVisibility(i > 0 ? VISIBLE : INVISIBLE);
            Etat pc = Prefs.etat(app);
            if (entrees.isEmpty()) {
                date.setText("Pas encore de page");
                humeur.setText("");
                texte.setText(e.journalActif ? "Ce soir, s'il s'est passé quelque chose, Pilou prendra sa plume."
                        : "Le journal est en pause (Réglages → Pilou et moi).");
                page.setText("");
                dessin.setImageBitmap(Dessin.image("repos", pc.couleur, pc.accessoire, 2));
                return;
            }
            Presence.Entree x = entrees.get(i);
            date.setText(dateLongue(x.jour));
            humeur.setText(signe(x.humeur));
            texte.setText(x.texte);
            page.setText("page " + (entrees.size() - i) + " sur " + entrees.size());
            dessin.setImageBitmap(Dessin.image(x.humeur, pc.couleur, pc.accessoire, 2));
            journal.setContentDescription(dateLongue(x.jour) + ". " + x.texte);
        } catch (RuntimeException ex) {
            Journal.noter("présence : carte", ex);
        }
    }

    private void questionPrenom(Ui.Palette p) {
        boolean demander = PresenceTel.demanderPrenom(app);
        question.setVisibility(demander ? VISIBLE : GONE);
        if (!demander || question.getChildCount() > 0) return;
        question.setPadding(0, Ui.dp(app, 12), 0, 0);
        TextView q = Style.texte(app, "« dis… comment tu t'appelles ? tu peux aussi ne rien dire, c'est bien aussi »", Ui.T_CORPS, p.texte, false);
        q.setTypeface(Typeface.DEFAULT, Typeface.ITALIC);
        question.addView(q, Ui.large());
        TextView aide = Style.texte(app, "Un prénom ou un surnom. Il reste entre tes appareils (groupe chiffré), jamais chez tes amis.",
                Ui.T_ETIQUETTE, p.doux, false);
        aide.setPadding(0, Ui.dp(app, 4), 0, Ui.dp(app, 8));
        question.addView(aide, Ui.large());
        EditText champ = champ(app, "Ton prénom ou un surnom");
        question.addView(champ, Ui.large(app, 8));
        LinearLayout r = Ui.rangee(app);
        LayoutParams l1 = new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1);
        l1.rightMargin = Ui.dp(app, 8);
        r.addView(Style.bouton(app, "C'est ça", false, v -> {
            String n = Presence.nettoyerPrenom(champ.getText().toString());
            PresenceTel.prenom(app, n, n.isEmpty());
            question.removeAllViews();
            empreinte = "";
            rafraichir();
        }), l1);
        r.addView(Style.bouton(app, "Je préfère ne pas dire", false, v -> {
            PresenceTel.prenom(app, "", true);
            question.removeAllViews();
            empreinte = "";
            rafraichir();
        }), new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1));
        question.addView(r, Ui.large());
    }

    static EditText champ(Principale a, String indice) {
        Ui.Palette p = Ui.p(a);
        EditText e = new EditText(a);
        e.setHint(indice);
        e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_WORDS | InputType.TYPE_TEXT_VARIATION_PERSON_NAME);
        e.setSingleLine(true);
        e.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(Presence.PRENOM_MAX)});
        Style.champ(e);
        return e;
    }

    // ---- Réglages « Pilou et moi »

    private interface Choix {
        void choisir(String v);
    }

    private static LinearLayout segments(Principale a, String titre, String sous, String[] noms, String[] valeurs, String actuel, Choix choix) {
        Ui.Palette p = Ui.p(a);
        LinearLayout bloc = Ui.pile(a);
        bloc.setPadding(Ui.dp(a, 4), Ui.dp(a, 8), 0, Ui.dp(a, 8));
        bloc.addView(Style.texte(a, titre, Ui.T_CORPS, p.texte, false));
        if (!sous.isEmpty()) bloc.addView(Style.texte(a, sous, Ui.T_DETAIL, p.doux, false));
        LinearLayout r = Ui.rangee(a);
        Style.fond(r, Style.arrondi(a, p.surface2, 14, 0));
        r.setPadding(Ui.dp(a, 4), Ui.dp(a, 4), Ui.dp(a, 4), Ui.dp(a, 4));
        TextView[] t = new TextView[noms.length];
        for (int k = 0; k < noms.length; k++) {
            TextView x = Style.texte(a, noms[k], Ui.T_ETIQUETTE, p.doux, true);
            x.setGravity(Gravity.CENTER);
            x.setMinHeight(Ui.dp(a, 40));
            int kk = k;
            x.setOnClickListener(v -> {
                choix.choisir(valeurs[kk]);
                for (int j = 0; j < t.length; j++) {
                    t[j].setTextColor(j == kk ? p.bleu : p.doux);
                    Style.fond(t[j], j == kk ? Style.arrondi(a, p.surface, 11, p.bleu) : null);
                    t[j].setText((j == kk ? "● " : "") + noms[j]);
                }
            });
            boolean choisi = valeurs[k].equals(actuel);
            x.setTextColor(choisi ? p.bleu : p.doux);
            Style.fond(x, choisi ? Style.arrondi(a, p.surface, 11, p.bleu) : null);
            x.setText((choisi ? "● " : "") + noms[k]);
            t[k] = x;
            r.addView(x, new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1));
        }
        LayoutParams lr = Ui.large();
        lr.topMargin = Ui.dp(a, 8);
        bloc.addView(r, lr);
        return bloc;
    }

    /** La section « Pilou et moi » des Réglages : tout est désactivable. */
    static void reglages(Principale a, LinearLayout corps) {
        Ui.Palette p = Ui.p(a);
        corps.addView(Style.titreSection(a, "Pilou et moi"));
        LinearLayout c = Style.carte(a);
        Presence.Etat e = PresenceTel.etat(a);
        c.addView(segments(a, "Pilou me parle", "Ses petits mots : jamais pour te réclamer, jamais pour te presser",
                new String[]{"Peu", "Normalement", "Jamais"}, new String[]{"peu", "normal", "jamais"}, e.parle, v -> {
                    Presence.Etat x = PresenceTel.etat(a);
                    x.parle = v;
                    x.motJour = "";
                    PresenceTel.garder(a, x);
                    MotDuSoir.programmer(a);
                }));
        c.addView(Style.separateur(a));
        c.addView(segments(a, "Le mot du soir", "Une notification silencieuse, sans badge, entre 19 h et 20 h 30. Jamais de relance.",
                new String[]{"Chaque jour", "Parfois", "Jamais"}, new String[]{"chaque", "parfois", "jamais"}, e.frequence, v -> {
                    Presence.Etat x = PresenceTel.etat(a);
                    x.frequence = v;
                    PresenceTel.garder(a, x);
                    MotDuSoir.programmer(a);
                }));
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Son journal", "Une page par jour, de son point de vue, à partir de ce qu'il a vécu", e.journalActif, oui -> {
            Presence.Etat x = PresenceTel.etat(a);
            x.journalActif = oui;
            PresenceTel.garder(a, x);
        });
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Petits gestes de complicité", "Il te fait signe quand tu reviens", e.gestes, oui -> {
            Presence.Etat x = PresenceTel.etat(a);
            x.gestes = oui;
            PresenceTel.garder(a, x);
        });
        c.addView(Style.separateur(a));
        LinearLayout bloc = Ui.pile(a);
        bloc.setPadding(Ui.dp(a, 4), Ui.dp(a, 8), 0, Ui.dp(a, 4));
        bloc.addView(Style.texte(a, "Mon prénom pour Pilou", Ui.T_CORPS, p.texte, false));
        bloc.addView(Style.texte(a, "Facultatif. Il reste entre tes appareils (groupe chiffré), jamais chez tes amis.", Ui.T_DETAIL, p.doux, false));
        EditText champ = champ(a, "Pas de prénom");
        champ.setText(PresenceTel.prenom(a));
        LayoutParams lc = Ui.large();
        lc.topMargin = Ui.dp(a, 8);
        bloc.addView(champ, lc);
        LinearLayout r = Ui.rangee(a);
        r.setPadding(0, Ui.dp(a, 8), 0, 0);
        LayoutParams l1 = new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1);
        l1.rightMargin = Ui.dp(a, 8);
        r.addView(Style.bouton(a, "Enregistrer", false, v -> {
            String n = Presence.nettoyerPrenom(champ.getText().toString());
            PresenceTel.prenom(a, n, false);
            champ.setText(n);
            Style.dire(a, n.isEmpty() ? "Prénom effacé." : "Pilou s'en souviendra : " + n, false);
        }), l1);
        r.addView(Style.bouton(a, "Effacer", false, v -> {
            PresenceTel.prenom(a, "", false);
            champ.setText("");
            Style.dire(a, "Prénom effacé. Pilou ne le redemandera pas.", false);
        }), new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1));
        bloc.addView(r, Ui.large());
        c.addView(bloc, Ui.large());
        corps.addView(c, Ui.large());
    }

    /** Le mot du jour, en tête de l'Accueil (italique, discret) ; vide : rien. */
    /** Le mot du jour en tête de l'Accueil, dans la police pixel de Pilou (sa voix écrite, docs/POLICE.md). */
    static TextePixelVue motTete(Principale a) {
        Ui.Palette p = Ui.p(a);
        TextePixelVue t = new TextePixelVue(a, 1.6f, p.texte);
        // La bulle du bureau : bord bleu d'un module et demi (3 unités du PC), coins carrés, fond de carte.
        Style.fond(t, Style.plat(a, Style.p(a).carte, Vitrine.BLEU));
        t.setPadding(Ui.dp(a, 14), Ui.dp(a, 10), Ui.dp(a, 14), Ui.dp(a, 10));
        t.setVisibility(View.GONE);
        return t;
    }
}
