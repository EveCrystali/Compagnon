package fr.pilou.compagnon;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Écran de l'app : appairer avec le PC, choisir ce que Pilou montre, donner les autorisations. */
public final class Principale extends Activity {
    private final Handler h = new Handler(Looper.getMainLooper());
    private TextView statut;
    private EditText champCode, champRelais;
    private PilouVue pilou;
    private long derniereCaresse;
    private CheckBox bulle;

    @Override
    protected void onCreate(Bundle sauve) {
        super.onCreate(sauve);
        Journal.installer(this);
        float d = getResources().getDisplayMetrics().density;
        LinearLayout pile = new LinearLayout(this);
        pile.setOrientation(LinearLayout.VERTICAL);
        int m = (int) (20 * d);
        pile.setPadding(m, m, m, m);

        pilou = new PilouVue(this, 4 * d * Prefs.taille(this) / 1.6f);
        LinearLayout.LayoutParams centre = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        centre.gravity = Gravity.CENTER_HORIZONTAL;
        pile.addView(pilou, centre);

        statut = new TextView(this);
        statut.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        statut.setGravity(Gravity.CENTER_HORIZONTAL);
        statut.setPadding(0, 0, 0, (int) (16 * d));
        pile.addView(statut);
        // Toucher Pilou : une caresse (comptée au plus toutes les 3 s, créditée au PC).
        pilou.setOnClickListener(v -> {
            pilou.jouer("caresse", 2400);
            long t = android.os.SystemClock.uptimeMillis();
            if (t - derniereCaresse > 3000) {
                derniereCaresse = t;
                Gains.caresse(this);
            }
        });
        Button atelier = bouton("🎣 Atelier de Pilou : pêcher, cuisiner, jouer", v -> startActivity(new Intent(this, Atelier.class)));
        atelier.setTypeface(Typeface.DEFAULT_BOLD);
        pile.addView(atelier);

        pile.addView(titre("Appairer avec le PC"));
        pile.addView(note("Sur le PC : clic droit sur Pilou → Intégrations → Android : appairer. Vise le QR code avec "
                + "l'appareil photo du téléphone, ou tape le code ici."));
        champCode = new EditText(this);
        champCode.setHint("XXXX-XXXX-XXXX-XXXX");
        champCode.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        champCode.setTypeface(Typeface.MONOSPACE);
        champCode.setText(Chiffre.formater(Prefs.code(this)));
        pile.addView(champCode);
        champRelais = new EditText(this);
        champRelais.setHint(Prefs.RELAIS_DEFAUT);
        champRelais.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        champRelais.setText(Prefs.relais(this));
        pile.addView(champRelais);
        pile.addView(bouton("Appairer", v -> appairer(champCode.getText().toString(), champRelais.getText().toString())));

        pile.addView(titre("Ce que Pilou montre"));
        pile.addView(note("Toujours : une notification avec l'état des sessions, et le widget si tu l'ajoutes à l'écran d'accueil."));
        bulle = caseACocher("Pilou flottant par-dessus les applis", Prefs.bulle(this), oui -> {
            Prefs.de(this).edit().putBoolean("bulle", oui).apply();
            if (oui && !Settings.canDrawOverlays(this))
                startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + getPackageName())));
            Veille.demarrer(this);
        });
        pile.addView(bulle);
        pile.addView(note("Taille de Pilou flottant"));
        pile.addView(curseurTaille());
        pile.addView(caseACocher("Me prévenir quand une IA attend", Prefs.alerteAttente(this),
                oui -> Prefs.de(this).edit().putBoolean("alerteAttente", oui).apply()));
        pile.addView(caseACocher("Me prévenir quand une session finit", Prefs.alerteFin(this),
                oui -> Prefs.de(this).edit().putBoolean("alerteFin", oui).apply()));

        pile.addView(titre("Autorisations"));
        pile.addView(bouton("Autoriser les notifications", v -> demanderNotifications()));
        pile.addView(bouton("Autoriser Pilou par-dessus les applis",
                v -> startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + getPackageName())))));
        pile.addView(titre("Version " + versionInstallee()));
        pile.addView(bouton("Chercher une mise à jour", v -> startActivity(new Intent(this, Installation.class))));
        pile.addView(bouton("Ne plus écouter le PC", v -> {
            Prefs.de(this).edit().putString("code", "").remove("etat").remove("dernierId").apply();
            Veille.arreter(this);
            champCode.setText("");
            rafraichir();
        }));

        // Dernier plantage : visible ici, à copier pour le signaler.
        String plantage = Journal.dernier(this);
        if (!plantage.isEmpty()) {
            pile.addView(titre("Dernier plantage"));
            TextView trace = note(plantage.length() > 1200 ? plantage.substring(0, 1200) + "…" : plantage);
            trace.setTypeface(Typeface.MONOSPACE);
            trace.setTextSize(TypedValue.COMPLEX_UNIT_SP, 10);
            trace.setTextIsSelectable(true);
            pile.addView(trace);
            pile.addView(bouton("Copier le rapport", v -> {
                android.content.ClipboardManager cm = getSystemService(android.content.ClipboardManager.class);
                cm.setPrimaryClip(android.content.ClipData.newPlainText("Plantage de Pilou", plantage));
                statut.setText("Rapport copié : colle-le à Claude.");
            }));
            pile.addView(bouton("Effacer", v -> {
                Journal.effacer(this);
                recreate();
            }));
        }

        ScrollView defile = new ScrollView(this);
        defile.addView(pile);
        setContentView(defile);
        lireLien(getIntent());
        demanderNotifications();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        lireLien(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        bulle.setChecked(Prefs.bulle(this) && Settings.canDrawOverlays(this));
        Veille.demarrer(this);
        rafraichir();
    }

    @Override
    protected void onPause() {
        super.onPause();
        h.removeCallbacksAndMessages(null);
    }

    // pilou://appairer?c=CODE[&s=relais] : le QR code du PC, scanné avec l'appareil photo.
    private void lireLien(Intent i) {
        Uri u = i == null ? null : i.getData();
        if (u == null || !"pilou".equals(u.getScheme())) return;
        String c = u.getQueryParameter("c");
        String s = u.getQueryParameter("s");
        if (c != null) appairer(c, s == null ? Prefs.RELAIS_DEFAUT : s);
    }

    private void appairer(String code, String relais) {
        if (!Chiffre.valide(code)) {
            statut.setText("Code incomplet : 16 caractères, comme sur le PC.");
            return;
        }
        String r = relais == null || relais.trim().isEmpty() ? Prefs.RELAIS_DEFAUT : relais.trim().replaceAll("/+$", "");
        Prefs.de(this).edit().putString("code", Chiffre.normaliser(code)).putString("relais", r)
                .remove("etat").remove("dernierId").apply();
        champCode.setText(Chiffre.formater(code));
        champRelais.setText(r);
        Veille.demarrer(this); // le service voit le nouveau code et repart
        statut.setText("Appairé ✓ — j'attends des nouvelles du PC…");
    }

    private void rafraichir() {
        long maintenant = System.currentTimeMillis();
        Etat e = Prefs.etat(this);
        pilou.montrer(e.expression(maintenant), e.couleur);
        pilou.accessoire(e.accessoire);
        if (!Chiffre.valide(Prefs.code(this))) statut.setText("Pas encore appairé avec un PC.");
        else statut.setText(e.nom + " · niveau " + e.niveau + (e.titre.isEmpty() ? "" : " · " + e.titre) + "\n" + e.resume(maintenant));
        h.postDelayed(this::rafraichir, 5000);
    }

    private String versionInstallee() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (PackageManager.NameNotFoundException e) {
            return "?";
        }
    }

    private void demanderNotifications() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
    }

    private TextView titre(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding(0, (int) (18 * getResources().getDisplayMetrics().density), 0, 4);
        return t;
    }

    private TextView note(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        return t;
    }

    private Button bouton(String s, View.OnClickListener action) {
        Button b = new Button(this);
        b.setText(s);
        b.setAllCaps(false);
        b.setOnClickListener(action);
        return b;
    }

    // Curseur de 60 % à 250 % ; l'aperçu en haut de l'écran et le Pilou flottant suivent en direct.
    private View curseurTaille() {
        android.widget.SeekBar s = new android.widget.SeekBar(this);
        int min = Math.round(Prefs.TAILLE_MIN * 100), max = Math.round(Prefs.TAILLE_MAX * 100);
        s.setMax(max - min);
        s.setProgress(Math.round(Prefs.taille(this) * 100) - min);
        float d = getResources().getDisplayMetrics().density;
        s.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(android.widget.SeekBar b, int v, boolean parLaPersonne) {
                if (!parLaPersonne) return;
                float t = (v + min) / 100f;
                Prefs.de(Principale.this).edit().putFloat("taille", t).apply();
                pilou.pixel(4 * d * t / 1.6f);
                Veille.demarrer(Principale.this);
            }

            @Override
            public void onStartTrackingTouch(android.widget.SeekBar b) {
            }

            @Override
            public void onStopTrackingTouch(android.widget.SeekBar b) {
            }
        });
        return s;
    }

    interface Choix {
        void choisir(boolean oui);
    }

    private CheckBox caseACocher(String s, boolean coche, Choix choix) {
        CheckBox c = new CheckBox(this);
        c.setText(s);
        c.setChecked(coche);
        c.setOnClickListener(v -> choix.choisir(c.isChecked()));
        return c;
    }
}
