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
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Réglages, par sections : appairage, Pilou flottant, notifications, jeux, mises à jour, diagnostic, à propos.
 */
final class PageReglages extends Page {
    static final String DEPOT = "https://github.com/EveCrystali/Compagnon";

    private final TextView statut, dernier, plantage;
    private final EditText champCode, champRelais;
    private final Switch bulle;
    private final Button cacher, ramener, copierPlantage, effacerPlantage, autoriser;
    private final PilouVue apercu;
    private final LinearLayout blocPlantage;

    PageReglages(Principale a) {
        super(a);
        Ui.Palette p = Ui.p(a);
        corps.addView(Ui.titrePage(a, "Réglages"));
        corps.addView(Ui.sousTitre(a, "Pilou " + a.version()));

        // ---- Appairage
        corps.addView(Ui.titreSection(a, "Appairage avec le PC"));
        LinearLayout c = Ui.carte(a);
        statut = Ui.texte(a, "", 15, p.texte, true);
        c.addView(statut);
        TextView aide = Ui.texte(a, "Sur le PC : clic droit sur Pilou → Intégrations → Android : appairer. Vise le QR code avec l'appareil photo, "
                + "ou tape le code ici. Le même code relie tous tes appareils (XP partagée).", 13, p.doux, false);
        aide.setPadding(0, Ui.dp(a, 6), 0, Ui.dp(a, 6));
        c.addView(aide);
        champCode = champ(a, "XXXX-XXXX-XXXX-XXXX", InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        champCode.setTypeface(Typeface.MONOSPACE);
        c.addView(champCode, Ui.large(a, 8));
        champRelais = champ(a, Prefs.RELAIS_DEFAUT, InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        c.addView(champRelais, Ui.large(a, 10));
        c.addView(Ui.bouton(a, "Appairer", true, v -> {
            if (a.appairer(champCode.getText().toString(), champRelais.getText().toString())) {
                Toast.makeText(a, "Appairé ✓ — j'attends des nouvelles du PC…", Toast.LENGTH_LONG).show();
                rafraichir();
            } else Toast.makeText(a, "Code incomplet : 16 caractères, comme sur le PC.", Toast.LENGTH_LONG).show();
        }), Ui.large(a, 4));
        c.addView(Ui.ligne(a, "Ne plus écouter le PC", "Efface le code ; Pilou garde ses gains en attente", p.orange, v -> {
            Prefs.de(a).edit().putString("code", "").remove("etat").remove("dernierId").apply();
            Veille.arreter(a);
            champCode.setText("");
            rafraichir();
        }));
        corps.addView(c, Ui.large());

        // ---- Pilou flottant
        corps.addView(Ui.titreSection(a, "Pilou flottant"));
        c = Ui.carte(a);
        bulle = Ui.interrupteur(a, c, "Par-dessus les autres applis", "Toucher : la bulle · glisser : le déplacer · appui long : l'app",
                Prefs.bulle(a), oui -> {
                    Prefs.de(a).edit().putBoolean("bulle", oui).apply();
                    if (oui && !Settings.canDrawOverlays(a))
                        a.startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + a.getPackageName())));
                    Veille.demarrer(a);
                });
        c.addView(Ui.separateur(a));
        LinearLayout taille = Ui.rangee(a);
        taille.setPadding(Ui.dp(a, 4), Ui.dp(a, 8), 0, 0);
        LinearLayout gauche = Ui.pile(a);
        gauche.addView(Ui.texte(a, "Taille", 16, p.texte, false));
        SeekBar curseur = new SeekBar(a);
        int min = Math.round(Prefs.TAILLE_MIN * 100), max = Math.round(Prefs.TAILLE_MAX * 100);
        curseur.setMax(max - min);
        curseur.setProgress(Math.round(Prefs.taille(a) * 100) - min);
        curseur.setProgressTintList(android.content.res.ColorStateList.valueOf(p.bleu));
        curseur.setThumbTintList(android.content.res.ColorStateList.valueOf(p.bleu));
        gauche.addView(curseur, Ui.large());
        taille.addView(gauche, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        float d = a.getResources().getDisplayMetrics().density;
        apercu = new PilouVue(a, 2.2f * d * Prefs.taille(a));
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
        LinearLayout actions = Ui.rangee(a);
        cacher = Ui.bouton(a, "", false, v -> {
            boolean cache = Veille.cache(a);
            Veille.cacher(a, !cache);
            v.postDelayed(this::rafraichir, 300);
        });
        LinearLayout.LayoutParams lc = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        lc.rightMargin = Ui.dp(a, 8);
        actions.addView(cacher, lc);
        // Ramener : Pilou réapparaît, replacé dans l'écran (s'il était perdu hors du bord).
        ramener = Ui.bouton(a, "Ramener Pilou", false, v -> {
            Veille.cacher(a, false);
            Toast.makeText(a, "Pilou revient à l'écran.", Toast.LENGTH_SHORT).show();
            v.postDelayed(this::rafraichir, 300);
        });
        actions.addView(ramener, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        c.addView(actions, Ui.large());
        corps.addView(c, Ui.large());

        // ---- Notifications
        corps.addView(Ui.titreSection(a, "Notifications"));
        c = Ui.carte(a);
        Ui.interrupteur(a, c, "Une IA t'attend", "Autorisation demandée, question posée", Prefs.alerteAttente(a),
                oui -> Prefs.de(a).edit().putBoolean("alerteAttente", oui).apply());
        c.addView(Ui.separateur(a));
        Ui.interrupteur(a, c, "Une session a fini", "Fin de tour ou erreur", Prefs.alerteFin(a),
                oui -> Prefs.de(a).edit().putBoolean("alerteFin", oui).apply());
        c.addView(Ui.separateur(a));
        Ui.interrupteur(a, c, "Mises à jour de Pilou", "Une fois par jour au plus", Prefs.alerteMaj(a),
                oui -> Prefs.de(a).edit().putBoolean("alerteMaj", oui).apply());
        c.addView(Ui.separateur(a));
        autoriser = Ui.bouton(a, "Autoriser les notifications", true, v -> a.demanderNotifications());
        c.addView(autoriser, Ui.large(a, 4));
        c.addView(Ui.ligne(a, "Réglages système des notifications", "Sons, vibrations, écran verrouillé", 0, v -> {
            Intent i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, a.getPackageName());
            a.startActivity(i);
        }));
        corps.addView(c, Ui.large());

        // ---- Jeux
        corps.addView(Ui.titreSection(a, "Jeux"));
        c = Ui.carte(a);
        Ui.interrupteur(a, c, "Sons", "Petits bruits rétro dans Chasse aux bugs", Prefs.son(a),
                oui -> Prefs.de(a).edit().putBoolean("son", oui).apply());
        c.addView(Ui.separateur(a));
        Ui.interrupteur(a, c, "Vibrations", "Quand Pilou est touché, quand un boss tombe", Prefs.vibrations(a),
                oui -> Prefs.de(a).edit().putBoolean("vibrations", oui).apply());
        corps.addView(c, Ui.large());

        // ---- Mises à jour
        corps.addView(Ui.titreSection(a, "Mises à jour"));
        c = Ui.carte(a);
        c.addView(Ui.ligne(a, "Version " + a.version(), "Pilou vérifie une fois par jour ; tu peux le faire maintenant", 0,
                v -> a.startActivity(new Intent(a, Installation.class))));
        corps.addView(c, Ui.large());

        // ---- Diagnostic
        corps.addView(Ui.titreSection(a, "Diagnostic"));
        c = Ui.carte(a);
        dernier = Ui.texte(a, "", 14, p.texte, false);
        c.addView(dernier);
        c.addView(Ui.ligne(a, "Copier le diagnostic", "À coller dans un message pour signaler un souci", 0, v -> copier("Diagnostic de Pilou", diagnostic())));
        blocPlantage = Ui.pile(a);
        blocPlantage.addView(Ui.separateur(a));
        blocPlantage.addView(Ui.texte(a, "Dernier plantage", 15, p.orange, true));
        plantage = Ui.texte(a, "", 12, p.doux, false);
        plantage.setTypeface(Typeface.MONOSPACE);
        plantage.setTextIsSelectable(true);
        plantage.setPadding(0, Ui.dp(a, 6), 0, Ui.dp(a, 8));
        blocPlantage.addView(plantage);
        LinearLayout r = Ui.rangee(a);
        copierPlantage = Ui.bouton(a, "Copier le rapport", false, v -> copier("Plantage de Pilou", Journal.dernier(a)));
        effacerPlantage = Ui.bouton(a, "Effacer", false, v -> {
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
        corps.addView(Ui.titreSection(a, "À propos"));
        c = Ui.carte(a);
        c.addView(Ui.texte(a, "Pilou, le compagnon de tes IA de code. Il suit tes sessions Claude et Codex depuis ton PC, "
                + "pêche, cuisine et chasse les bugs avec toi.", 14, p.texte, false));
        c.addView(Ui.ligne(a, "Code source", "github.com/EveCrystali/Compagnon", 0,
                v -> a.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(DEPOT)))));
        c.addView(Ui.separateur(a));
        TextView lic = Ui.texte(a, "Logiciel libre. Aucune bibliothèque tierce : seulement le framework Android. "
                + "Relais : ntfy (logiciel libre), messages chiffrés de bout en bout (AES-256-GCM).", 12, p.doux, false);
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
        e.setTextColor(p.texte);
        e.setHintTextColor(p.doux);
        e.setBackground(Ui.arrondi(a, p.surface2, 12, p.bord));
        e.setPadding(Ui.dp(a, 14), Ui.dp(a, 12), Ui.dp(a, 14), Ui.dp(a, 12));
        return e;
    }

    private void copier(String titre, String texte) {
        ClipboardManager cm = app.getSystemService(ClipboardManager.class);
        cm.setPrimaryClip(ClipData.newPlainText(titre, texte));
        Toast.makeText(app, "Copié : colle-le dans ton message.", Toast.LENGTH_SHORT).show();
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
                + "\nflottant : " + Prefs.bulle(app) + " · permission " + Settings.canDrawOverlays(app) + " · caché " + Veille.cache(app)
                + "\nnotifications : " + app.notificationsPermises();
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
}
