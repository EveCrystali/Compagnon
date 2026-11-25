package fr.pilou.compagnon;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.Map;
import java.util.Set;

/** L'atelier de Pilou dans l'app : pêcher, cuisiner, jouer, le caresser ; carnet, recettes, récompenses. */
public final class Atelier extends Activity implements Terrain.Ecoute {
    private TextView entete, message;
    private Button cuisiner;
    private Terrain terrain;

    @Override
    protected void onCreate(Bundle sauve) {
        super.onCreate(sauve);
        Journal.installer(this);
        float d = getResources().getDisplayMetrics().density;
        LinearLayout pile = new LinearLayout(this);
        pile.setOrientation(LinearLayout.VERTICAL);
        int m = (int) (14 * d);
        pile.setPadding(m, m, m, m);

        entete = new TextView(this);
        entete.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        entete.setTypeface(Typeface.DEFAULT_BOLD);
        pile.addView(entete);

        terrain = new Terrain(this, this);
        LinearLayout.LayoutParams lt = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lt.topMargin = (int) (8 * d);
        pile.addView(terrain, lt);

        message = new TextView(this);
        message.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        message.setGravity(Gravity.CENTER_HORIZONTAL);
        message.setPadding(0, (int) (8 * d), 0, (int) (8 * d));
        message.setMinLines(2);
        message.setText("Touche Pilou pour le caresser.");
        pile.addView(message);

        pile.addView(rangee(bouton("🎣 Pêcher", v -> terrain.pecher()),
                cuisiner = bouton("🍲 Cuisiner", v -> terrain.cuisiner()),
                bouton("✦ Jouer", v -> terrain.jouer())));
        pile.addView(rangee(bouton("Carnet de pêche", v -> carnet()),
                bouton("Livre de recettes", v -> recettes()),
                bouton("Récompenses", v -> recompenses())));

        TextView note = new TextView(this);
        note.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        note.setPadding(0, (int) (10 * d), 0, 0);
        note.setText("Pêche : touche le bouchon quand il plonge (« ! »), tu as 1,2 s. Si tu ne fais rien, Pilou ferre tout seul, "
                + "avec bien moins de chance et jamais mieux que « rare ». Ce que tu gagnes ici part vers ton PC, qui garde l'XP "
                + "(« en attente » tant que le PC ne l'a pas reçu).");
        pile.addView(note);

        ScrollView defile = new ScrollView(this);
        defile.addView(pile);
        setContentView(defile);
        change();
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

    private LinearLayout rangee(View... vues) {
        LinearLayout r = new LinearLayout(this);
        r.setOrientation(LinearLayout.HORIZONTAL);
        for (View v : vues) r.addView(v, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        return r;
    }

    private Button bouton(String s, View.OnClickListener a) {
        Button b = new Button(this);
        b.setText(s);
        b.setAllCaps(false);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        b.setOnClickListener(a);
        return b;
    }

    // ---- Terrain.Ecoute

    @Override
    public void message(String texte) {
        message.setText(texte);
    }

    @Override
    public int niveau() {
        return Butin.niveau(Gains.xp(this, Prefs.etat(this)));
    }

    @Override
    public void change() {
        Etat e = Prefs.etat(this);
        int xp = Gains.xp(this, e), n = Butin.niveau(xp), attente = Gains.enAttente(this);
        entete.setText(e.nom + " · niveau " + n + " · " + Butin.titre(n) + "\n" + xp + " / " + Butin.xpPourNiveau(n + 1) + " xp"
                + (attente > 0 ? "  (+" + attente + " en attente du PC)" : ""));
        terrain.tenue(e.couleur, e.accessoire);
        int stock = 0;
        for (int v : Gains.stock(this).values()) stock += v;
        cuisiner.setText("🍲 Cuisiner (" + stock + ")");
    }

    // ---- Carnet, recettes, récompenses

    private void montrer(String titre, String texte) {
        TextView t = new TextView(this);
        int m = (int) (20 * getResources().getDisplayMetrics().density);
        t.setPadding(m, m / 2, m, 0);
        t.setText(texte);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        ScrollView s = new ScrollView(this);
        s.addView(t);
        new AlertDialog.Builder(this).setTitle(titre).setView(s).setPositiveButton("Fermer", null).show();
    }

    private void carnet() {
        Etat e = Prefs.etat(this);
        Set<String> connues = Gains.carnet(this, e);
        int n = niveau();
        StringBuilder b = new StringBuilder();
        b.append(connues.size()).append(" / ").append(Butin.PRISES.size()).append(" espèces\n\n");
        for (Butin.Prise x : Butin.PRISES) {
            if (connues.contains(x.id)) {
                int ici = Gains.prises(this, x.id);
                b.append(Butin.signe(x.rarete)).append("  ").append(x.nom).append("  · ").append(Butin.nomRarete(x.rarete))
                        .append(ici > 0 ? "  · ×" + ici + " ici" : "").append('\n');
            } else
                b.append(Butin.signe(x.rarete)).append("  ???  · ").append(Butin.nomRarete(x.rarete))
                        .append(x.niveauMin > n ? "  · dès le niveau " + x.niveauMin : "").append('\n');
        }
        Map<String, Integer> stock = Gains.stock(this);
        if (!stock.isEmpty()) {
            b.append("\nDans le panier : ");
            boolean premier = true;
            for (Map.Entry<String, Integer> k : stock.entrySet()) {
                Butin.Prise x = Butin.trouver(k.getKey());
                if (x == null) continue;
                b.append(premier ? "" : ", ").append(x.nom).append(" ×").append(k.getValue());
                premier = false;
            }
        }
        montrer("Carnet de pêche", b.toString());
    }

    private void recettes() {
        Etat e = Prefs.etat(this);
        Set<String> faits = Gains.plats(this, e);
        int n = niveau(), inventes = e.inventes;
        for (String p : faits) if (p.startsWith("inv:")) inventes++;
        StringBuilder b = new StringBuilder();
        for (Butin.Recette r : Butin.RECETTES) {
            if (faits.contains(r.id)) b.append("✓  ").append(r.nom).append('\n');
            else if (r.niveauMin > n) b.append("niv ").append(r.niveauMin).append("  ???\n");
            else b.append("·  ???  (").append(String.join(" + ", r.saveurs)).append(")\n");
        }
        b.append("\nPlats inventés : ").append(inventes);
        montrer("Livre de recettes", b.toString());
    }

    private void recompenses() {
        int n = niveau();
        StringBuilder b = new StringBuilder("Niveau " + n + " · " + Butin.titre(n) + "\n\n");
        for (String[] r : Butin.RECOMPENSES) {
            int niv = Integer.parseInt(r[0]);
            b.append(niv <= n ? "✓  " : "niv " + niv + "  ").append(r[2]).append("  (").append(r[1]).append(")\n");
        }
        b.append("\nAccessoires et couleurs se choisissent sur le PC (clic droit sur Pilou) ; le téléphone montre ceux du PC.");
        montrer("Récompenses", b.toString());
    }
}
