package fr.pilou.compagnon;

import android.app.Activity;
import android.content.Intent;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** L'atelier de Pilou : pêcher, cuisiner, attraper l'étoile, éclater les bulles, taper dans la main. */
public final class Atelier extends Activity implements Terrain.Ecoute {
    static final String EXTRA_JEU = "jeu";
    private TextView entete, message;
    private Button cuisiner;
    private Terrain terrain;

    @Override
    protected void onCreate(Bundle sauve) {
        super.onCreate(sauve);
        Journal.installer(this);
        Ui.Palette p = Ui.p(this);
        getWindow().setBackgroundDrawable(new ColorDrawable(p.fond));
        getWindow().setStatusBarColor(p.fond);
        getWindow().setNavigationBarColor(p.fond);
        LinearLayout pile = Ui.pile(this);
        int m = Ui.dp(this, 16);
        pile.setPadding(m, m, m, m);

        LinearLayout barre = Ui.rangee(this);
        TextView retour = Ui.texte(this, "‹  Retour", 16, p.bleu, true);
        retour.setPadding(0, Ui.dp(this, 6), Ui.dp(this, 16), Ui.dp(this, 6));
        retour.setOnClickListener(v -> finish());
        barre.addView(retour);
        pile.addView(barre);
        pile.addView(Ui.titrePage(this, "L'atelier de Pilou"));
        entete = Ui.texte(this, "", 14, p.doux, false);
        entete.setPadding(0, 0, 0, Ui.dp(this, 12));
        pile.addView(entete);

        LinearLayout carte = Ui.carte(this);
        carte.setPadding(0, 0, 0, 0);
        carte.setClipToOutline(true);
        terrain = new Terrain(this, this);
        carte.addView(terrain, Ui.large());
        pile.addView(carte, Ui.large(this, 10));

        message = Ui.texte(this, "Touche Pilou pour le caresser.", 15, p.texte, false);
        message.setGravity(Gravity.CENTER_HORIZONTAL);
        message.setMinLines(2);
        message.setPadding(0, Ui.dp(this, 4), 0, Ui.dp(this, 10));
        pile.addView(message, Ui.large());

        LinearLayout r1 = Ui.rangee(this);
        r1.addView(Ui.bouton(this, "Pêcher", true, v -> terrain.pecher()), poids(true));
        cuisiner = Ui.bouton(this, "Cuisiner", true, v -> terrain.cuisiner());
        r1.addView(cuisiner, poids(false));
        pile.addView(r1, Ui.large(this, 8));
        LinearLayout r2 = Ui.rangee(this);
        r2.addView(Ui.bouton(this, "Étoile", false, v -> terrain.jouer(0)), poids(true));
        r2.addView(Ui.bouton(this, "Bulles", false, v -> terrain.jouer(1)), poids(true));
        r2.addView(Ui.bouton(this, "Tape 5", false, v -> terrain.jouer(2)), poids(false));
        pile.addView(r2, Ui.large(this, 8));
        pile.addView(Ui.ligne(this, "Carnet, recettes, récompenses", "Dans l'onglet Collection", 0, v -> {
            startActivity(new Intent(this, Principale.class).putExtra(Principale.EXTRA_ONGLET, Principale.COLLECTION)
                    .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP));
            finish();
        }));

        TextView note = Ui.texte(this, "Pêche : touche le bouchon quand il plonge (« ! »), tu as 1,2 s. Si tu ne fais rien, Pilou ferre tout seul, "
                + "avec bien moins de chance et jamais mieux que « rare ». Ce que tu gagnes ici part vers ton PC, qui garde l'XP.", 12, p.doux, false);
        note.setPadding(Ui.dp(this, 4), Ui.dp(this, 10), Ui.dp(this, 4), 0);
        pile.addView(note);

        ScrollView defile = new ScrollView(this);
        defile.addView(pile);
        setContentView(defile);
        change();
        String jeu = getIntent().getStringExtra(EXTRA_JEU);
        if (jeu != null && sauve == null) terrain.post(() -> lancer(jeu));
    }

    private LinearLayout.LayoutParams poids(boolean marge) {
        LinearLayout.LayoutParams l = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        if (marge) l.rightMargin = Ui.dp(this, 8);
        return l;
    }

    private void lancer(String jeu) {
        int n = Gains.niveau(this, Prefs.etat(this));
        if (!Acces.jeuOuvert(jeu, n)) {
            android.widget.Toast.makeText(this, Acces.nomJeu(jeu) + " : niveau " + Acces.niveauJeu(jeu), android.widget.Toast.LENGTH_SHORT).show();
            return;
        }
        switch (jeu) {
            case "peche": terrain.pecher(); break;
            case "cuisine": terrain.cuisiner(); break;
            case "etoile": terrain.jouer(0); break;
            case "bulles": terrain.jouer(1); break;
            case "tape": terrain.jouer(2); break;
            default: break;
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        change();
    }

    @Override
    protected void onPause() {
        super.onPause();
        new Thread(() -> Gains.envoyer(getApplicationContext()), "pilou-gains").start();
    }

    // ---- Terrain.Ecoute

    @Override
    public void message(String texte) {
        message.setText(texte);
    }

    @Override
    public int niveau() {
        return Gains.niveau(this, Prefs.etat(this));
    }

    @Override
    public void change() {
        Etat e = Prefs.etat(this);
        int xp = Gains.xp(this, e), n = Gains.niveau(this, e), attente = Gains.enAttente(this);
        entete.setText("Niveau " + n + " · " + Butin.titre(n) + " · " + xp + " / " + Butin.xpPourNiveau(n + 1) + " xp"
                + (attente > 0 ? "  (+" + attente + " en route vers le PC)" : ""));
        terrain.tenue(e.couleur, e.accessoire);
        int stock = 0;
        for (int v : Gains.stock(this).values()) stock += v;
        cuisiner.setText("Cuisiner (" + stock + ")");
    }
}
