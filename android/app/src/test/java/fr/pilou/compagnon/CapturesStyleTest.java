package fr.pilou.compagnon;

import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.Looper;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

import java.io.File;
import java.io.FileOutputStream;

/**
 * Captures du guide de style (docs/STYLE.md) : les écrans hors Aventure au format d'un vrai téléphone en portrait
 * (1078 × 2400, 440 dpi), en clair, en sombre et en grande police (× 1,3). Images dans app/build/captures/style/
 * (artefact CI « captures-ui »). Ne fait jamais échouer le build : sans rendu natif, elles sont sautées.
 */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class CapturesStyleTest {
    private static final Object[][] FORMATS = {
            {"tel-clair", "w392dp-h873dp-notnight-440dpi", 1f},
            {"tel-sombre", "w392dp-h873dp-night-440dpi", 1f},
            {"tel-grand", "w392dp-h873dp-notnight-440dpi", 1.3f},
    };

    private File dossier;
    private String format;

    @Test
    public void ecransHorsAventure() {
        try {
            dossier = new File("build/captures/style");
            dossier.mkdirs();
            for (Object[] f : FORMATS) {
                format = (String) f[0];
                RuntimeEnvironment.setQualifiers((String) f[1]);
                RuntimeEnvironment.setFontScale((Float) f[2]);
                Context ctx = RuntimeEnvironment.getApplication();
                Prefs.de(ctx).edit().clear().commit();
                essayer("planche", this::planche);
                essayer("neuf", this::neuf);
                appairer();
                essayer("pages", this::pages);
            }
            RuntimeEnvironment.setFontScale(1f);
        } catch (Throwable t) {
            System.out.println("CAPTURES-STYLE-SAUTEES " + t);
        }
    }

    private void essayer(String nom, Runnable r) {
        try {
            r.run();
        } catch (Throwable t) {
            System.out.println("CAPTURE-STYLE-ERREUR " + format + "-" + nom + " " + t);
        }
    }

    // La planche du guide (docs/STYLE.md) : chaque pièce de Style.java, dessinée par le vrai code de l'app.
    private void planche() {
        ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
        Activity c = ac.get();
        Style.Palette p = Style.p(c);
        int u = Style.u(c);
        android.widget.LinearLayout l = Ui.pile(c);
        l.setBackgroundColor(p.page);
        l.setPadding(Ui.dp(c, 18), Ui.dp(c, 14), Ui.dp(c, 18), Ui.dp(c, 18));
        l.addView(Style.titrePage(c, "La main de Pilou"));
        l.addView(Style.sousTitre(c, "Guide de style · module de " + u + " px · police " + Style.pixel(c, Style.PETIT) + " / "
                + Style.pixel(c, Style.CORPS) + " / " + Style.pixel(c, Style.PAGE) + " px"));

        l.addView(Style.titreSection(c, "Palette"));
        int[] couleurs = {p.page, p.carte, p.creux, p.texte, p.pale, p.eteint, p.accent, p.coche, p.titre, p.orange, p.bord, p.pointilles};
        String[] noms = {"page", "carte", "creux", "texte", "pâle", "éteint", "accent", "coche", "titre", "orange", "bord", "pointillés"};
        for (int r = 0; r < 2; r++) {
            android.widget.LinearLayout rang = Ui.rangee(c);
            for (int i = r * 6; i < r * 6 + 6; i++) {
                android.widget.LinearLayout k = Ui.pile(c);
                View v = new View(c);
                v.setBackground(Style.plat(c, couleurs[i], p.bordExt));
                k.addView(v, new android.widget.LinearLayout.LayoutParams(android.view.ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(c, 26)));
                k.addView(Style.texte(c, noms[i], 12, p.pale, false));
                android.widget.LinearLayout.LayoutParams lk = new android.widget.LinearLayout.LayoutParams(0, android.view.ViewGroup.LayoutParams.WRAP_CONTENT, 1);
                lk.rightMargin = Ui.dp(c, 6);
                rang.addView(k, lk);
            }
            l.addView(rang, Ui.large(c, 6));
        }

        l.addView(Style.titreSection(c, "Cadre"));
        android.widget.LinearLayout carte = Style.carte(c);
        carte.addView(Style.texte(c, "Carte : bord, biseau, ombre portée", 19, p.texte, true));
        carte.addView(Style.texte(c, "Bord et biseau d'un module, coins en escalier, ombre portée, 12 dp de marge. Jamais d'arrondi lissé.", 15, p.pale, false));
        carte.addView(Style.separateur(c));
        android.widget.LinearLayout puces = Ui.rangee(c);
        String[] mots = {"● en ligne", "! il t'attend", "▣ fermé"};
        int[] teintes = {p.coche, p.orange, p.eteint};
        for (int i = 0; i < mots.length; i++) {
            android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(android.view.ViewGroup.LayoutParams.WRAP_CONTENT, android.view.ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.rightMargin = Ui.dp(c, 6);
            puces.addView(Style.puce(c, mots[i], teintes[i]), lp);
        }
        carte.addView(puces);
        l.addView(carte, Ui.large(c, 8));
        android.widget.LinearLayout appel = Style.carte(c);
        Style.fond(appel, Style.cadre(c, p, p.orange));
        appel.addView(Style.texte(c, "Carte qui appelle : le module de couleur passe à l'orange", 15, p.texte, false));
        l.addView(appel, Ui.large(c, 8));

        l.addView(Style.titreSection(c, "Boutons : repos, appui, fermé"));
        for (int plein = 1; plein >= 0; plein--) {
            android.widget.LinearLayout rang = Ui.rangee(c);
            String[] etats = {plein == 1 ? "Jouer" : "Plus tard", "Appui", "Fermé"};
            for (int i = 0; i < 3; i++) {
                Style.Texte b = Style.bouton(c, etats[i], plein == 1, null);
                if (i == 1) b.setPressed(true);
                if (i == 2) {
                    b.setEnabled(false);
                    b.icone("ui-cadenas");
                }
                android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(0, android.view.ViewGroup.LayoutParams.WRAP_CONTENT, 1);
                lp.rightMargin = Ui.dp(c, 6);
                rang.addView(b, lp);
            }
            l.addView(rang, Ui.large(c, 6));
        }

        l.addView(Style.titreSection(c, "États : la forme d'abord"));
        android.widget.LinearLayout cases = Ui.rangee(c);
        String[] signes = {"✓", "○", "!", "◐", "▣", "★"};
        String[] sens = {"fait", "à faire", "attend", "en cours", "fermé", "rare"};
        int[] tons = {p.coche, p.pale, p.orange, p.coche, p.eteint, p.titre};
        for (int i = 0; i < signes.length; i++) {
            android.widget.LinearLayout k = Ui.pile(c);
            k.setGravity(android.view.Gravity.CENTER_HORIZONTAL);
            k.addView(Style.caseSigne(c, signes[i], tons[i]));
            k.addView(Style.texte(c, sens[i], 12, p.pale, false));
            cases.addView(k, new android.widget.LinearLayout.LayoutParams(0, android.view.ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        }
        l.addView(cases, Ui.large(c, 6));
        Style.Barre barre = new Style.Barre(c);
        barre.part(0.62f);
        l.addView(barre, Ui.large(c, 8));

        l.addView(Style.titreSection(c, "Texte"));
        l.addView(Style.texte(c, "Titre de carte (police « titre »)", 19, p.texte, true));
        l.addView(Style.texte(c, "Corps : « c'est le soir ! j'ai voulu éteindre la lumière, je n'ai pas trouvé l'interrupteur »", 15, p.texte, false));
        l.addView(Style.texte(c, "Petit : 300 / 625 xp · niveau 14 dans 325 xp · ¤ 240 po · ❖ ◇ ✺ ⌛ ✉ ⚔", 12, p.pale, false));

        l.addView(Style.titreSection(c, "Icônes"));
        String[] ids = {"accueil", "aventure", "jouer", "boutique", "collection", "reglages", "menu", "retour", "suite", "fermer", "plus",
                "curseur", "coche", "cadenas", "nouveau", "coeur", "etoile", "eclair", "lettre", "epees", "lune", "horloge", "outil", "piece"};
        for (int r = 0; r < 2; r++) {
            android.widget.LinearLayout rang = Ui.rangee(c);
            for (int i = r * 12; i < r * 12 + 12; i++) {
                android.widget.FrameLayout k = new android.widget.FrameLayout(c);
                k.addView(new Style.Icone(c, "ui-" + ids[i], i % 12 == 0 ? p.coche : p.texte, 2), new android.widget.FrameLayout.LayoutParams(
                        android.view.ViewGroup.LayoutParams.WRAP_CONTENT, android.view.ViewGroup.LayoutParams.WRAP_CONTENT, android.view.Gravity.CENTER));
                rang.addView(k, new android.widget.LinearLayout.LayoutParams(0, android.view.ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            }
            l.addView(rang, Ui.large(c, 8));
        }
        android.util.DisplayMetrics dm = c.getResources().getDisplayMetrics();
        l.measure(View.MeasureSpec.makeMeasureSpec(dm.widthPixels, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        l.layout(0, 0, dm.widthPixels, l.getMeasuredHeight());
        Bitmap b = Bitmap.createBitmap(dm.widthPixels, l.getMeasuredHeight(), Bitmap.Config.ARGB_8888);
        l.draw(new Canvas(b));
        ecrire(b, "planche");
        ac.pause().stop().destroy();
    }

    // Pas encore appairé : l'Accueil et son guide.
    private void neuf() {
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        attendre();
        ecran(c.get(), "neuf-accueil");
        contenu(c.get().page(Principale.ACCUEIL), "neuf-accueil-long");
        c.pause().stop().destroy();
    }

    private void pages() {
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        attendre();
        int[] onglets = {Principale.ACCUEIL, Principale.JOUER, Principale.BOUTIQUE, Principale.COLLECTION, Principale.REGLAGES};
        String[] noms = {"accueil", "jouer", "boutique", "collection", "reglages"};
        for (int i = 0; i < onglets.length; i++) {
            a.aller(onglets[i], false);
            attendre();
            ecran(a, noms[i]);
            Page p = a.page(onglets[i]);
            if (onglets[i] == Principale.COLLECTION) {
                String[] sous = {"carnet", "recettes", "niveaux", "style", "metiers"};
                for (int k = 0; k <= PageCollection.METIERS; k++) {
                    ((PageCollection) p).choisir(k);
                    attendre();
                    contenu(p, "collection-" + sous[k]);
                }
            } else contenu(p, noms[i] + "-long");
        }
        PageBoutique b = (PageBoutique) a.page(Principale.BOUTIQUE);
        a.aller(Principale.BOUTIQUE, false);
        b.rayon(Boutique.DOS);
        b.choisir("cape");
        attendre();
        ecran(a, "boutique-dos");
        contenu(b, "boutique-dos-long");
        a.montrerRangees(9, 15);
        attendre();
        ecran(a, "rangees-debloquees");
        c.pause().stop().destroy();
    }

    // Le même état de démonstration que CapturesTest : rien de personnel.
    private void appairer() {
        appairer(RuntimeEnvironment.getApplication());
    }

    static void appairer(Context ctx) {
        long t = System.currentTimeMillis();
        String etat = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":12,\"titre\":\"Pêcheur du dimanche\",\"couleur\":\"bleu\","
                + "\"humeur\":\"repos\",\"calmes\":2,\"sessions\":["
                + "{\"id\":\"b\",\"source\":\"codex\",\"libelle\":\"site-vitrine\",\"etat\":\"permission\",\"depuis\":" + (t - 40_000) + ",\"outil\":\"\"},"
                + "{\"id\":\"a\",\"source\":\"claude\",\"libelle\":\"refonte du module de facturation\",\"etat\":\"travail\",\"depuis\":" + (t - 95_000) + ",\"outil\":\"Bash\"},"
                + "{\"id\":\"c\",\"source\":\"claude\",\"libelle\":\"docs\",\"etat\":\"fini\",\"depuis\":" + (t - 180_000) + ",\"outil\":\"\"}],"
                + "\"xp\":3900,\"accessoire\":\"feuille\",\"carnet\":[\"truite\",\"carpe\",\"botte\"],\"plats\":[],\"recus\":[],"
                + "\"po\":240,\"objets\":[\"echarpe\",\"petit-chat\"],\"porte\":{\"cou\":\"echarpe\",\"compagnon\":\"petit-chat\"},"
                + "\"offres\":[\"cape\",\"monocle\",\"aura\",\"parapluie\"],\"promo\":\"cape\",\"serie\":3,\"stade\":2,"
                + "\"quetes\":[[0,\"Pêcher 3 poissons\",1,3,30,0],[0,\"Finir 5 tours de Claude\",5,5,40,1],[1,\"Cuisiner 4 plats\",2,4,120,0]],"
                + "\"metiers\":{\"codeur\":2,\"musicien\":3,\"joueur\":1},\"succes\":[\"marathon\",\"melomane\",\"dactylo\"],"
                + "\"heures\":{\"codeur\":412,\"musicien\":187,\"joueur\":34,\"facteur\":57,\"cinephile\":3},"
                + "\"avance\":{\"codeur-confirme\":412,\"gamer\":34,\"visio-man\":30,\"rempart\":70,\"photographe\":20},"
                + "\"appareils\":[{\"nom\":\"PC-SALON\",\"xp\":3100,\"t\":" + (t - 20_000) + "},{\"nom\":\"PC-BUREAU\",\"xp\":500,\"t\":" + (t - 7_200_000) + "}]}";
        Prefs.de(ctx).edit().putString("code", "ABCDEFGHJKMNPQRS").putString("etat", etat).putLong("recu", t)
                .putBoolean("bulle", true).putInt("boutiqueVue", 9).putInt("niveauVu", 12).commit();
    }

    private static void attendre() {
        shadowOf(Looper.getMainLooper()).idle();
    }

    private void ecran(Activity a, String nom) {
        View racine = a.getWindow().getDecorView();
        android.util.DisplayMetrics m = a.getResources().getDisplayMetrics();
        int w = m.widthPixels, h = m.heightPixels;
        racine.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(h, View.MeasureSpec.EXACTLY));
        racine.layout(0, 0, w, h);
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        racine.draw(new Canvas(b));
        ecrire(b, nom);
    }

    private void contenu(Page p, String nom) {
        View v = p.corps;
        int w = Math.max(1, p.getWidth() > 0 ? p.getWidth() : p.getResources().getDisplayMetrics().widthPixels);
        v.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        int h = Math.max(1, Math.min(v.getMeasuredHeight(), 12_000));
        v.layout(0, 0, w, h);
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        cv.drawColor(Ui.p(p.getContext()).fond);
        v.draw(cv);
        ecrire(b, nom);
    }

    private void ecrire(Bitmap b, String nom) {
        try (FileOutputStream f = new FileOutputStream(new File(dossier, format + "-" + nom + ".png"))) {
            b.compress(Bitmap.CompressFormat.PNG, 100, f);
        } catch (Exception e) {
            System.out.println("CAPTURE-STYLE-ERREUR " + format + "-" + nom + " " + e);
        }
    }
}
