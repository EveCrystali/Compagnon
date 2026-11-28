package fr.pilou.compagnon;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;

/**
 * Réglages, par sections : appairage, Pilou flottant, notifications, jeux, mises à jour, diagnostic, à propos.
 */
final class PageReglages extends Page {
    static final String DEPOT = "https://github.com/EveCrystali/Compagnon";

    private final TextView statut, dernier, plantage;
    private final EditText champCode, champRelais;
    private final Style.Coche bulle;
    private final TextView cacher, ramener, copierPlantage, effacerPlantage, autoriser;
    private final PilouVue apercu;
    private final LinearLayout blocPlantage;

    PageReglages(Principale a) {
        super(a);
        Ui.Palette p = Ui.p(a);
        corps.addView(Style.titrePage(a, "Réglages"));
        corps.addView(Style.sousTitre(a, "Pilou " + a.version()));

        // ---- Appairage
        corps.addView(Style.titreSection(a, "Appairage avec le PC"));
        LinearLayout c = Style.carte(a);
        statut = Style.texte(a, "", Ui.T_CORPS, p.texte, true);
        c.addView(statut);
        TextView aide = Style.texte(a, "Sur le PC : clic droit sur Pilou → Amis et appareils → Groupe d'appareils → Partager l'XP entre mes appareils. Vise le QR code avec l'appareil photo, "
                + "ou tape le code ici. Le même code relie tous tes appareils (XP partagée).", Ui.T_DETAIL, p.doux, false);
        aide.setPadding(0, Ui.dp(a, 6), 0, Ui.dp(a, 6));
        c.addView(aide);
        champCode = champ(a, "XXXX-XXXX-XXXX-XXXX", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        champCode.setTypeface(Typeface.MONOSPACE);
        c.addView(champCode, Ui.large(a, 8));
        champRelais = champ(a, Prefs.RELAIS_DEFAUT, InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        c.addView(champRelais, Ui.large(a, 10));
        c.addView(Style.bouton(a, "Appairer", true, v -> {
            if (a.appairer(champCode.getText().toString(), champRelais.getText().toString())) {
                Style.dire(a, "Appairé ✓ — j'attends des nouvelles du PC…", true);
                rafraichir();
            } else Style.dire(a, "Code incomplet : 16 caractères, comme sur le PC.", true);
        }), Ui.large(a, 4));
        c.addView(Style.ligne(a, "Ne plus écouter le PC", "Efface le code ; Pilou garde ses gains en attente", p.orange, v -> {
            Prefs.de(a).edit().putString("code", "").remove("etat").remove("dernierId").apply();
            Veille.arreter(a);
            champCode.setText("");
            rafraichir();
        }));
        corps.addView(c, Ui.large());

        // ---- Pilou flottant
        corps.addView(Style.titreSection(a, "Pilou flottant"));
        c = Style.carte(a);
        bulle = Style.interrupteur(a, c, "Par-dessus les autres applis", "Toucher : la bulle · glisser : le déplacer · appui long : l'app",
                Prefs.bulle(a), oui -> {
                    Prefs.de(a).edit().putBoolean("bulle", oui).apply();
                    if (oui && !Settings.canDrawOverlays(a))
                        a.startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + a.getPackageName())));
                    Veille.demarrer(a);
                });
        c.addView(Style.separateur(a));
        LinearLayout taille = Ui.rangee(a);
        taille.setPadding(Ui.dp(a, 4), Ui.dp(a, 8), 0, 0);
        LinearLayout gauche = Ui.pile(a);
        gauche.addView(Style.texte(a, "Taille", Ui.T_CORPS, p.texte, false));
        SeekBar curseur = new SeekBar(a);
        int min = Math.round(Prefs.TAILLE_MIN * 100), max = Math.round(Prefs.TAILLE_MAX * 100);
        curseur.setMax(max - min);
        curseur.setProgress(Math.round(Prefs.taille(a) * 100) - min);
        Style.curseur(curseur);
        gauche.addView(curseur, Ui.large());
        taille.addView(gauche, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        float d = a.getResources().getDisplayMetrics().density;
        apercu = new PilouVue(a, 2.2f * d * Prefs.taille(a), true);
        LinearLayout boite = Ui.rangee(a);
        boite.setGravity(Gravity.CENTER);
        boite.setMinimumWidth(Ui.dp(a, 96));
        boite.setMinimumHeight(Ui.dp(a, 110));
        boite.addView(apercu);
        taille.addView(boite);
        curseur.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar b, int v, boolean parLaPersonne) {
                if (!parLaPersonne) return;
                float t = (v + min) / 100f;
                Prefs.de(a).edit().putFloat("taille", t).apply();
                apercu.pixel(2.2f * d * Math.min(t, 1.2f));
                Veille.demarrer(a);
            }

            @Override
            public void onStartTrackingTouch(SeekBar b) {
            }

            @Override
            public void onStopTrackingTouch(SeekBar b) {
            }
        });
        apercu.pixel(2.2f * d * Math.min(Prefs.taille(a), 1.2f));
        c.addView(taille, Ui.large());
        // L'un sous l'autre : en grande police, deux boutons côte à côte couperaient leur libellé.
        LinearLayout actions = Ui.pile(a);
        cacher = Style.bouton(a, "", false, v -> {
            boolean cache = Veille.cache(a);
            Veille.cacher(a, !cache);
            v.postDelayed(this::rafraichir, 300);
        });
        actions.addView(cacher, Ui.large(a, 8));
        // Ramener : Pilou réapparaît, replacé dans l'écran (s'il était perdu hors du bord).
        ramener = Style.bouton(a, "Ramener Pilou", false, v -> {
            Veille.cacher(a, false);
            Style.dire(a, "Pilou revient à l'écran.", false);
            v.postDelayed(this::rafraichir, 300);
        });
        actions.addView(ramener, Ui.large());
        c.addView(actions, Ui.large());
        corps.addView(c, Ui.large());

        // ---- Pilou et moi (docs/PRESENCE.md) : ses petits mots, le mot du soir, son journal, mon prénom
        PresenceVue.reglages(a, corps);

        // ---- Notifications
        corps.addView(Style.titreSection(a, "Notifications"));
        c = Style.carte(a);
        Style.interrupteur(a, c, "Une IA t'attend", "Autorisation demandée, question posée", Prefs.alerteAttente(a),
                oui -> Prefs.de(a).edit().putBoolean("alerteAttente", oui).apply());
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Une session a fini", "Fin de tour ou erreur", Prefs.alerteFin(a),
                oui -> Prefs.de(a).edit().putBoolean("alerteFin", oui).apply());
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Retours de Pilou (aventures)", "Une seule notification quand il revient d'une étape, jamais de relance",
                Prefs.alerteAventure(a), oui -> {
                    Prefs.de(a).edit().putBoolean("alerteAventure", oui).apply();
                    new Thread(() -> Retour.programmer(a.getApplicationContext()), "pilou-retour").start();
                });
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Mises à jour de Pilou", "Une fois par jour au plus", Prefs.alerteMaj(a),

                oui -> Prefs.de(a).edit().putBoolean("alerteMaj", oui).apply());
        c.addView(Style.separateur(a));
        autoriser = Style.bouton(a, "Autoriser les notifications", true, v -> a.demanderNotifications());
        c.addView(autoriser, Ui.large(a, 4));
        c.addView(Style.ligne(a, "Réglages système des notifications", "Sons, vibrations, écran verrouillé", 0, v -> {
            Intent i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, a.getPackageName());
            a.startActivity(i);
        }));
        corps.addView(c, Ui.large());

        // ---- Soins
        corps.addView(Style.titreSection(a, "Soins"));
        c = Style.carte(a);
        Soins.EtatSoins es = Gains.soins(a, Prefs.etat(a), System.currentTimeMillis());
        Style.interrupteur(a, c, "Vacances", "Tout est figé : ses besoins ne baissent plus", es.vacances,
                oui -> Gains.soin(a, "vacances", oui ? "1" : "0"));
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Me prévenir s'il a besoin de moi", "Une fois par jour au plus", Prefs.alerteSoins(a),
                oui -> Prefs.de(a).edit().putBoolean("alerteSoins", oui).apply());
        corps.addView(c, Ui.large());

        // ---- Jeux
        corps.addView(Style.titreSection(a, "Jeux"));
        c = Style.carte(a);
        c.addView(choixSons(a));
        c.addView(Style.separateur(a));
        c.addView(choixMusique(a));
        c.addView(essaiSon(a));
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Sons de Chasse aux bugs", "Petits bruits rétro pendant la partie", Prefs.son(a),
                oui -> Prefs.de(a).edit().putBoolean("son", oui).apply());
        c.addView(Style.separateur(a));
        Style.interrupteur(a, c, "Vibrations", "Quand Pilou est touché, quand un boss tombe", Prefs.vibrations(a),
                oui -> Prefs.de(a).edit().putBoolean("vibrations", oui).apply());
        corps.addView(c, Ui.large());

        // ---- Mises à jour
        corps.addView(Style.titreSection(a, "Mises à jour"));
        c = Style.carte(a);
        c.addView(Style.ligne(a, "Version " + a.version(), "Pilou vérifie une fois par jour ; tu peux le faire maintenant", 0,
                v -> a.startActivity(new Intent(a, Installation.class))));
        corps.addView(c, Ui.large());

        // ---- Diagnostic
        corps.addView(Style.titreSection(a, "Diagnostic"));
        c = Style.carte(a);
        dernier = Style.texte(a, "", Ui.T_CORPS, p.texte, false);
        c.addView(dernier);
        c.addView(Style.ligne(a, "Copier le diagnostic", "À coller dans un message pour signaler un souci", 0, v -> copier("Diagnostic de Pilou", diagnostic())));
        blocPlantage = Ui.pile(a);
        blocPlantage.addView(Style.separateur(a));
        blocPlantage.addView(Style.texte(a, "Dernier plantage", Ui.T_CORPS, p.orange, true));
        plantage = Style.texte(a, "", Ui.T_ETIQUETTE, p.doux, false);
        plantage.setTypeface(Typeface.MONOSPACE);
        plantage.setTextIsSelectable(true);
        plantage.setPadding(0, Ui.dp(a, 6), 0, Ui.dp(a, 8));
        blocPlantage.addView(plantage);
        LinearLayout r = Ui.rangee(a);
        copierPlantage = Style.bouton(a, "Copier le rapport", false, v -> copier("Plantage de Pilou", Journal.dernier(a)));
        effacerPlantage = Style.bouton(a, "Effacer", false, v -> {
            Journal.effacer(a);
            rafraichir();
        });
        LinearLayout.LayoutParams lr = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        lr.rightMargin = Ui.dp(a, 8);
        r.addView(copierPlantage, lr);
        r.addView(effacerPlantage, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        blocPlantage.addView(r, Ui.large());
        c.addView(blocPlantage, Ui.large());
        corps.addView(c, Ui.large());

        // ---- À propos
        corps.addView(Style.titreSection(a, "À propos"));
        c = Style.carte(a);
        c.addView(Style.texte(a, "Pilou, un petit compagnon qui vit en bas de ton écran. Il mène sa petite vie sans te déranger, "
                + "grandit pendant que tu travailles, joue, mange, pêche, cuisine et chasse les bugs avec toi ; "
                + "tout le reste est en option, pour le personnaliser. Et au passage, branché à tes applis "
                + "(IA de code, Discord, musique, agenda…), il te prévient de ce qui compte.", Ui.T_CORPS, p.texte, false));
        c.addView(Style.ligne(a, "Code source", "github.com/EveCrystali/Compagnon", 0,
                v -> a.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(DEPOT)))));
        c.addView(Style.separateur(a));
        TextView lic = Style.texte(a, "Logiciel libre. Aucune bibliothèque tierce : seulement le framework Android. "
                + "Relais : ntfy (logiciel libre), messages chiffrés de bout en bout (AES-256-GCM).", Ui.T_ETIQUETTE, p.doux, false);
        lic.setPadding(Ui.dp(a, 4), Ui.dp(a, 6), Ui.dp(a, 4), 0);
        c.addView(lic);
        corps.addView(c, Ui.large());
    }

    private static EditText champ(Principale a, String indice, int type) {
        Ui.Palette p = Ui.p(a);
        EditText e = new EditText(a);
        e.setHint(indice);
        e.setInputType(type);
        e.setSingleLine(true);
        Style.champ(e);
        return e;
    }

    private void copier(String titre, String texte) {
        ClipboardManager cm = app.getSystemService(ClipboardManager.class);
        cm.setPrimaryClip(ClipData.newPlainText(titre, texte));
        Style.dire(app, "Copié : colle-le dans ton message.", false);
    }

    private String diagnostic() {
        long maintenant = System.currentTimeMillis();
        long recu = Prefs.de(app).getLong("recu", 0);
        Etat e = Prefs.etat(app);
        return "Pilou " + app.version() + " · Android " + Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ") · " + Build.MODEL
                + "\nappairé : " + Chiffre.valide(Prefs.code(app)) + " · relais : " + Prefs.relais(app)
                + "\ndernier message : " + (recu == 0 ? "aucun" : "il y a " + Etat.duree(maintenant - recu))
                + " · id " + Prefs.de(app).getString("dernierId", "-")
                + "\nPC : " + e.resume(maintenant) + " · sessions " + e.sessions.size()
                + "\ngains en attente : " + Gains.enAttente(app) + " xp"
                + "\ncampagnes : " + CampagnesTel.diagnostic(app)
                + "\nflottant : " + Prefs.bulle(app) + " · permission " + Settings.canDrawOverlays(app) + " · caché " + Veille.cache(app)
                + "\nnotifications : " + app.notificationsPermises()
                + "\nsons : " + Sons.niveau(app) + " · musique " + Musique.niveau(app) + " · geste "
                + (Sons.empechement(app, false).isEmpty() ? "possible" : Sons.empechement(app, false))
                + (Journal.sons(app).isEmpty() ? "" : "\n" + Journal.sons(app));
    }

    @Override
    void rafraichir() {
        Ui.Palette p = Ui.p(app);
        long maintenant = System.currentTimeMillis();
        boolean appaire = Chiffre.valide(Prefs.code(app));
        long recu = Prefs.de(app).getLong("recu", 0);
        statut.setText(!appaire ? "○  Pas encore appairé" : recu == 0 ? "◐  Appairé · aucun message reçu pour l'instant"
                : "●  Appairé · dernier message il y a " + Etat.duree(maintenant - recu));
        statut.setTextColor(appaire ? p.bleu : p.doux);
        if (!champCode.hasFocus() && champCode.getText().length() == 0 && appaire) champCode.setText(Chiffre.formater(Prefs.code(app)));
        if (!champRelais.hasFocus() && champRelais.getText().length() == 0) champRelais.setText(Prefs.relais(app));
        if (bulle.isChecked() != (Prefs.bulle(app) && android.provider.Settings.canDrawOverlays(app)))
            bulle.setChecked(Prefs.bulle(app) && Settings.canDrawOverlays(app));
        boolean cache = Veille.cache(app);
        cacher.setText(cache ? "Montrer Pilou maintenant" : "Cacher Pilou 10 min");
        cacher.setEnabled(Prefs.bulle(app));
        ramener.setEnabled(Prefs.bulle(app) && Settings.canDrawOverlays(app));
        autoriser.setVisibility(app.notificationsPermises() ? View.GONE : View.VISIBLE);
        dernier.setText("Dernier message du relais : " + (recu == 0 ? "aucun" : "il y a " + Etat.duree(maintenant - recu)));
        String pl = Journal.dernier(app);
        blocPlantage.setVisibility(pl.isEmpty() ? View.GONE : View.VISIBLE);
        plantage.setText(pl.length() > 1200 ? pl.substring(0, 1200) + "…" : pl);
    }

    // Sons de Pilou (docs/SONS.md) : aucun, discrets, normaux (par défaut) ; le choix fait entendre le « pouic ».
    private static LinearLayout choixSons(Principale a) {
        return choixNiveau(a, "Sons de Pilou", "Quelques notes quand tu le touches ou choisis ; au volume multimédia, jamais en appel",
                "sons", Sons.NIVEAUX, new String[]{"Aucun", "Discrets", "Normaux"}, () -> Sons.niveau(a),
                () -> Sons.jouer(a, Sons.CARESSE));
    }

    // Musique et ambiances de l'Aventure (docs/SONS.md) : aucune, discrète (par défaut), normale.
    private static LinearLayout choixMusique(Principale a) {
        return choixNiveau(a, "Musique de l'Aventure", "Une boucle très basse pendant la lecture d'une campagne, et le bruit du lieu ; au volume multimédia",
                "musique", Musique.NIVEAUX, new String[]{"Aucune", "Discrète", "Normale"}, () -> Musique.niveau(a), () -> { });
    }

    /**
     * « Essayer » : un son tout de suite, au volume multimédia ; si rien ne peut sortir, la raison en clair. Un réglage
     * coché qui ne produit rien sans explication est un défaut (docs/SONS.md).
     */
    private static LinearLayout essaiSon(Principale a) {
        Ui.Palette p = Ui.p(a);
        LinearLayout bloc = Ui.pile(a);
        bloc.setPadding(Ui.dp(a, 4), 0, 0, Ui.dp(a, 8));
        TextView resultat = Style.texte(a, "", Ui.T_DETAIL, p.doux, false);
        resultat.setVisibility(View.GONE);
        bloc.addView(Style.bouton(a, "Essayer", false, v -> {
            String r = Sons.jouer(a, Sons.CARESSE, true);
            android.media.AudioManager am = a.getSystemService(android.media.AudioManager.class);
            String vol = am == null ? "" : " (" + am.getStreamVolume(android.media.AudioManager.STREAM_MUSIC) + " sur "
                    + am.getStreamMaxVolume(android.media.AudioManager.STREAM_MUSIC) + ")";
            String texte = r.isEmpty() ? "♪  Un « pouic » vient de partir au volume multimédia" + vol + "."
                    : "◇  Rien ne peut sortir : " + r + ".";
            if (r.isEmpty() && Sons.niveau(a).equals("aucun")) texte += " Les sons de Pilou sont sur « Aucun » : rien d'autre ne sonnera.";
            resultat.setText(texte);
            resultat.setTextColor(r.isEmpty() ? p.bleu : p.orange);
            resultat.setVisibility(View.VISIBLE);
        }), Ui.large());
        LinearLayout.LayoutParams lr = Ui.large();
        lr.topMargin = Ui.dp(a, 6);
        bloc.addView(resultat, lr);
        return bloc;
    }

    private static LinearLayout choixNiveau(Principale a, String titre, String detail, String cle, String[] niveaux,
                                            String[] noms, java.util.function.Supplier<String> actuel, Runnable apres) {
        Ui.Palette p = Ui.p(a);
        LinearLayout bloc = Ui.pile(a);
        bloc.setPadding(Ui.dp(a, 4), Ui.dp(a, 8), 0, Ui.dp(a, 8));
        bloc.addView(Style.texte(a, titre, Ui.T_CORPS, p.texte, false));
        bloc.addView(Style.texte(a, detail, Ui.T_DETAIL, p.doux, false));
        LinearLayout r = Ui.rangee(a);
        Style.fond(r, Style.arrondi(a, p.surface2, 14, 0));
        r.setPadding(Ui.dp(a, 4), Ui.dp(a, 4), Ui.dp(a, 4), Ui.dp(a, 4));
        TextView[] t = new TextView[noms.length];
        Runnable peindre = () -> {
            String choix = actuel.get();
            for (int j = 0; j < t.length; j++) {
                boolean choisi = niveaux[j].equals(choix);
                t[j].setTextColor(choisi ? p.bleu : p.doux);
                Style.fond(t[j], choisi ? Style.arrondi(a, p.surface, 11, p.bleu) : null);
                t[j].setText((choisi ? "● " : "") + noms[j]);
            }
        };
        for (int k = 0; k < noms.length; k++) {
            TextView x = new Style.Texte(a, noms[k], Style.pixelOptions(a, noms), p.doux, false, true);
            x.setSingleLine(true);
            x.setGravity(Gravity.CENTER);
            x.setMinHeight(Ui.dp(a, 40));
            int kk = k;
            x.setOnClickListener(v -> {
                Prefs.de(a).edit().putString(cle, niveaux[kk]).apply();
                peindre.run();
                apres.run();
            });
            t[k] = x;
            r.addView(x, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        }
        peindre.run();
        LinearLayout.LayoutParams lr = Ui.large();
        lr.topMargin = Ui.dp(a, 8);
        bloc.addView(r, lr);
        return bloc;
    }
}
