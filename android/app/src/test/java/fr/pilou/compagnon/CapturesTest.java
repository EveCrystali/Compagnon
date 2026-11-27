package fr.pilou.compagnon;

import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Looper;
import android.util.Base64;
import android.view.View;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.time.Duration;

/**
 * Captures d'écran de toute l'app, pour les revues d'interface : chaque écran, en thème clair et sombre,
 * sur un petit (360 × 640 dp) et un grand téléphone (412 × 915 dp). Images dans app/build/captures/
 * (artefact CI « captures-ui ») ; les miniatures du petit téléphone sont aussi écrites dans la sortie
 * du test, en base64 (lignes « CAPTURE »), lisibles depuis les journaux de la CI.
 * Ne fait jamais échouer le build : sans rendu graphique natif, les captures sont simplement sautées.
 */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class CapturesTest {
    private static final String[][] FORMATS = {
            {"petit-clair", "w360dp-h640dp-notnight-xhdpi"},
            {"petit-sombre", "w360dp-h640dp-night-xhdpi"},
            {"grand-clair", "w412dp-h915dp-notnight-xxhdpi"},
            {"grand-sombre", "w412dp-h915dp-night-xxhdpi"},
    };

    private File dossier;
    private String format;
    private boolean miniatures;

    @Test
    public void toutesLesPages() {
        try {
            dossier = new File("build/captures");
            dossier.mkdirs();
            for (String[] f : FORMATS) {
                format = f[0];
                miniatures = f[0].startsWith("petit");
                RuntimeEnvironment.setQualifiers(f[1]);
                Prefs.de(RuntimeEnvironment.getApplication()).edit().clear().commit();
                essayer("neuf", () -> ecrans("neuf"));
                appairer();
                essayer("appaire", () -> ecrans("appaire"));
                essayer("soins", this::soins);
                appairer();
                essayer("pluie", this::pluie);
                appairer();
                essayer("boutique", this::boutique);
                appairer();
                essayer("metiers", this::metiers);
                appairer();
                appairer();
                essayer("aventure", this::aventure);
                appairer();
                essayer("aventure-suspendue", this::aventureSuspendue);
                essayer("epreuves", this::epreuves);
                essayer("atelier-peche", () -> atelier("peche"));
                essayer("atelier-cuisine", () -> atelier("cuisine"));
                essayer("chasse", this::chasse);
                essayer("installation", this::installation);
            }
        } catch (Throwable t) {
            // Rendu natif indisponible ou écran qui refuse de se dessiner : pas de captures, pas d'échec.
            System.out.println("CAPTURES-SAUTEES " + t);
        }
    }

    // Un écran qui refuse de se dessiner n'empêche pas les autres.
    private void essayer(String nom, Runnable r) {
        try {
            r.run();
        } catch (Throwable t) {
            System.out.println("CAPTURE-ERREUR " + format + "-" + nom + " " + t);
        }
    }

    private void appairer() {
        appairer("");
    }

    // Accueil sous la pluie (connecteur météo du PC) : Pilou sans parapluie est mouillé et râle.
    private void pluie() {
        appairer("\"meteo\":{\"etat\":\"pluie\",\"temperature\":8,\"ville\":\"Paris\",\"signe\":\"☂\"},");
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        attendre();
        c.get().aller(Principale.ACCUEIL, false);
        attendre();
        ecran(c.get(), "pluie-accueil");
        c.pause().stop().destroy();
    }

    // Boutique rétro : vitrine, rayon Dos (rangées ouvertes et fermées), essayage, décor, fenêtre « Rangées débloquées ».
    private void boutique() {
        Context ctx = RuntimeEnvironment.getApplication();
        String etat = Prefs.de(ctx).getString("etat", "").replace("\"objets\":[\"echarpe\",\"petit-chat\"],\"porte\":{\"cou\":\"echarpe\",\"compagnon\":\"petit-chat\"},",
                "\"objets\":[\"echarpe\",\"petit-chat\",\"fond-nuit\",\"bonnet-pompon\",\"sac-a-dos\",\"chapeau-explorateur\",\"jumelles\",\"boussole\"],"
                        + "\"porte\":{\"cou\":\"echarpe\",\"compagnon\":\"petit-chat\",\"fond\":\"fond-nuit\",\"tete\":\"bonnet-pompon\"},");
        // La dernière visite date du niveau 9 : les rangées du palier 10 clignotent « débloquées ! ».
        Prefs.de(ctx).edit().putString("etat", etat).putInt("boutiqueVue", 9).putInt("niveauVu", 13).commit();
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.aller(Principale.ACCUEIL, false);
        attendre();
        ecran(a, "boutique-accueil-decor");
        a.aller(Principale.BOUTIQUE, false);
        attendre();
        PageBoutique b = (PageBoutique) a.page(Principale.BOUTIQUE);
        ecran(a, "boutique-vitrine");
        contenu(b, "boutique-vitrine-long");
        b.rayon(Boutique.DOS);
        b.choisir("cape");
        attendre();
        contenu(b, "boutique-dos-essai");
        b.rayon(Boutique.TETE);
        b.choisir("sombrero");
        attendre();
        contenu(b, "boutique-tete");
        b.rayon(Boutique.FOND);
        b.choisir("fond-arcade");
        attendre();
        contenu(b, "boutique-decors");
        // Boutique garnie : onglet Ensembles (progression, bonus porté), rayon Titres (titres à gagner).
        b.rayon(Boutique.RAYON_ENSEMBLES);
        b.choisir("boussole");
        attendre();
        contenu(b, "boutique-ensembles");
        b.rayon(Boutique.TITRE);
        b.choisir("titre-reveur");
        attendre();
        contenu(b, "boutique-titres");
        a.montrerRangees(9, 15);
        attendre();
        ecran(a, "boutique-rangees-debloquees");
        c.pause().stop().destroy();
    }

    // Métiers et succès : la carte de l'accueil, puis la page (Collection → Métiers) qu'elle ouvre.
    private void metiers() {
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.aller(Principale.ACCUEIL, false);
        attendre();
        contenu(a.page(Principale.ACCUEIL), "metiers-accueil-long");
        a.allerMetiers();
        attendre();
        ecran(a, "metiers");
        contenu(a.page(Principale.COLLECTION), "metiers-long");
        c.pause().stop().destroy();
    }

    private void appairer(String plus) {
        Context ctx = RuntimeEnvironment.getApplication();
        long t = System.currentTimeMillis();
        String etat = "{\"v\":1," + plus + "\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":12,\"titre\":\"Pêcheur du dimanche\",\"couleur\":\"bleu\","
                + "\"humeur\":\"repos\",\"calmes\":2,\"sessions\":["
                + "{\"id\":\"b\",\"source\":\"codex\",\"libelle\":\"site-vitrine\",\"etat\":\"permission\",\"depuis\":" + (t - 40_000) + ",\"outil\":\"\"},"
                + "{\"id\":\"a\",\"source\":\"claude\",\"libelle\":\"refonte du module de facturation\",\"etat\":\"travail\",\"depuis\":" + (t - 95_000) + ",\"outil\":\"Bash\"},"
                + "{\"id\":\"c\",\"source\":\"claude\",\"libelle\":\"docs\",\"etat\":\"fini\",\"depuis\":" + (t - 180_000) + ",\"outil\":\"\"}],"
                + "\"xp\":3600,\"accessoire\":\"feuille\",\"carnet\":[\"truite\",\"carpe\",\"botte\"],\"plats\":[],\"recus\":[],"
                + "\"po\":240,\"objets\":[\"echarpe\",\"petit-chat\"],\"porte\":{\"cou\":\"echarpe\",\"compagnon\":\"petit-chat\"},"
                + "\"offres\":[\"cape\",\"monocle\",\"aura\",\"parapluie\"],\"promo\":\"cape\",\"serie\":3,\"stade\":2,"
                + "\"quetes\":[[0,\"Pêcher 3 poissons\",1,3,30,0],[0,\"Finir 5 tours de Claude\",5,5,40,1],[1,\"Cuisiner 4 plats\",2,4,120,0]],"
                + "\"metiers\":{\"codeur\":2,\"musicien\":3,\"joueur\":1},\"succes\":[\"marathon\",\"melomane\",\"dactylo\"],"
                + "\"heures\":{\"codeur\":412,\"musicien\":187,\"joueur\":34,\"facteur\":57,\"cinephile\":3},"
                + "\"avance\":{\"codeur-confirme\":412,\"gamer\":34,\"visio-man\":30,\"rempart\":70,\"photographe\":20},"
                + "\"appareils\":[{\"nom\":\"RTX4070Ti\",\"xp\":3100,\"t\":" + (t - 20_000) + "},{\"nom\":\"PC-TAGG\",\"xp\":500,\"t\":" + (t - 7_200_000) + "}]}";
        Prefs.de(ctx).edit().putString("code", "ABCDEFGHJKMNPQRS").putString("etat", etat).putLong("recu", t)
                .putBoolean("bulle", true).commit();
    }

    // Soins : Pilou a un petit creux (icône près de lui), variante câlin au stade 2 ; puis tout comblé.
    private void soins() {
        Context ctx = RuntimeEnvironment.getApplication();
        long t = System.currentTimeMillis();
        String etat = Prefs.de(ctx).getString("etat", "").replace("\"stade\":2,",
                "\"stade\":2,\"soins\":{\"f\":12,\"p\":64,\"m\":55,\"s\":72,\"t\":" + t + ",\"r\":\"normal\",\"v\":0},\"formes\":{\"2\":\"calin\"},");
        Prefs.de(ctx).edit().putString("etat", etat).commit();
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        a.aller(Principale.ACCUEIL, false);
        attendre();
        ecran(a, "soins-accueil");
        Gains.soin(ctx, "soin", "croquettes");
        a.page(Principale.ACCUEIL).rafraichir();
        attendre();
        ecran(a, "soins-accueil-comble");
        c.pause().stop().destroy();
    }

    private void ecrans(String etat) {
        ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = c.get();
        attendre();
        String[] noms = {"accueil", "aventure", "jouer", "boutique", "collection", "reglages"};
        for (int i = 0; i < Principale.N; i++) {
            a.aller(i, false);
            attendre();
            ecran(a, etat + "-" + noms[i]);
            Page p = a.page(i);
            if (i == Principale.COLLECTION) {
                String[] sous = {"carnet", "recettes", "niveaux", "style", "metiers"};
                for (int k = 0; k <= PageCollection.METIERS; k++) {
                    ((PageCollection) p).choisir(k);
                    attendre();
                    contenu(p, etat + "-collection-" + (k < sous.length ? sous[k] : String.valueOf(k)));
                }
            } else contenu(p, etat + "-" + noms[i] + "-long");
        }
        c.pause().stop().destroy();
    }

    // ---- Aventure (campagnes) : liste, lecture, attente, épreuve, repos, reprise, fin, carnet ; horloge injectée.

    private final long[] horloge = {0};

    private void sansAnimations(boolean oui) {
        android.provider.Settings.Global.putFloat(RuntimeEnvironment.getApplication().getContentResolver(),
                android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, oui ? 0f : 1f);
    }

    private void avancer(long ms) {
        horloge[0] += ms;
    }

    private void aventure() {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().remove("campagnes").remove("campParties").commit();
        sansAnimations(true);
        horloge[0] = System.currentTimeMillis();
        CampagnesTel.horloge = () -> horloge[0];
        CampagnesTel.graineEssai = AventureTest.GLISSE;
        CampagnesTel.prechargerMaintenant();
        try {
            ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
            Principale a = c.get();
            a.aller(Principale.AVENTURE, false);
            attendre();
            PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
            ecran(a, "aventure-liste");
            contenu(pa, "aventure-liste-long");
            Campagnes.Campagne pro = Campagnes.charger("prologue");
            CampagnesTel.demarrer(ctx, "prologue", false);
            a.ouvrirLecture();
            attendre();
            Lecture l = pa.lecture();
            l.accelerer();
            attendre();
            ecran(a, "aventure-lecture-choix");
            CampagnesTel.choisir(ctx, "lampe");
            l.rafraichir();
            l.accelerer();
            attendre();
            ecran(a, "aventure-attente");
            a.aller(Principale.ACCUEIL, false);
            attendre();
            ecran(a, "aventure-accueil-attente");
            avancer(CampagnesTel.etat(ctx).fin - horloge[0] + 1000);
            a.page(Principale.ACCUEIL).rafraichir();
            a.majBandeau();
            attendre();
            ecran(a, "aventure-accueil-il-attend");
            a.ouvrirLecture();
            attendre();
            l.accelerer();
            attendre();
            ecran(a, "aventure-lecture-retour");
            CampagnesTel.choisir(ctx, "saute");
            l.rafraichir();
            l.accelerer();
            attendre();
            ecran(a, "aventure-epreuve");
            l.ouvrirEpreuve(false);
            attendre();
            ecran(a, "aventure-epreuve-ecran");
            l.epreuveOuverte().forcer(true);
            attendre();
            ecran(a, "aventure-epreuve-reussie");
            l.fermerCouche();
            CampagnesTel.epreuve(ctx, true);
            attendre();
            l.rafraichir();
            l.accelerer();
            attendre();
            CampagnesTel.choisir(ctx, "raccourci");
            l.rafraichir();
            l.accelerer();
            attendre();
            ecran(a, "aventure-repos");
            avancer(CampagnesTel.etat(ctx).fin - horloge[0] + 1000);
            l.rafraichir();
            l.accelerer();
            attendre();
            ecran(a, "aventure-reprise");
            CampagnesTel.choisir(ctx, "sentier");
            avancer(CampagnesTel.etat(ctx).fin - horloge[0] + 1000);
            l.rafraichir();
            l.accelerer();
            attendre();
            CampagnesTel.choisir(ctx, "lampe");
            l.rafraichir();
            l.accelerer();
            attendre();
            ecran(a, "aventure-depart-ou-attente");
            Campagnes.Etat e = CampagnesTel.etat(ctx);
            if (e.phase == Campagnes.Phase.Depart) {
                CampagnesTel.continuer(ctx);
                e = CampagnesTel.etat(ctx);
            }
            if (e.enAttente()) avancer(e.fin - horloge[0] + 1000);
            l.rafraichir();
            l.accelerer();
            attendre();
            ecran(a, "aventure-fin");
            vue(l.filVue(), "aventure-fin-long");
            a.page(Principale.AVENTURE).retour();
            attendre();
            contenu(pa, "aventure-liste-apres-long");
            pa.ouvrirCarnet();
            attendre();
            contenu(pa, "aventure-carnet-long");
            c.pause().stop().destroy();
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            CampagnesTel.graineEssai = null;
            sansAnimations(false);
        }
    }

    // Une aventure mise de côté (la confirmation en deux gestes), puis la liste qui propose de la reprendre.
    private void aventureSuspendue() {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().remove("campagnes").remove("campParties").commit();
        sansAnimations(true);
        CampagnesTel.prechargerMaintenant();
        try {
            ActivityController<Principale> c = Robolectric.buildActivity(Principale.class).setup().visible();
            Principale a = c.get();
            CampagnesTel.demarrer(ctx, "phare-eteint", false);
            a.ouvrirLecture();
            attendre();
            PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
            Lecture l = pa.lecture();
            l.accelerer();
            attendre();
            ecran(a, "aventure-phare");
            l.confirmerSuspension();
            attendre();
            ecran(a, "aventure-confirmation");
            CampagnesTel.abandonner(ctx);
            l.fermerCouche();
            attendre();
            pa.fermerLecture();
            attendre();
            contenu(pa, "aventure-liste-suspendue-long");
            c.pause().stop().destroy();
        } finally {
            sansAnimations(false);
        }
    }

    // Les mini-jeux des épreuves, en cours de partie (un toucher les lance, un peu de temps passe).
    private void epreuves() {
        sansAnimations(false);
        for (String jeu : new String[]{"reflexe", "memoire", "rythme", "visee", "des"}) {
            ActivityController<Atelier> c = Robolectric.buildActivity(Atelier.class).setup().visible();
            Epreuves.Ecran e = new Epreuves.Ecran(c.get(), jeu, 2, 55, 31, "mystere", ok -> {
            }, () -> {
            });
            c.get().setContentView(e);
            attendre();
            vue(e, "epreuve-" + jeu + "-depart");
            Epreuves.Jeu j = e.jeu();
            long t0 = android.os.SystemClock.uptimeMillis();
            j.dispatchTouchEvent(android.view.MotionEvent.obtain(t0, t0, android.view.MotionEvent.ACTION_DOWN, j.getWidth() / 2f, j.getHeight() / 2f, 0));
            shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(jeu.equals("memoire") ? 1300 : jeu.equals("rythme") ? 1500 : 900));
            vue(e, "epreuve-" + jeu);
            c.pause().stop().destroy();
        }
    }

    // Une vue quelconque, à la taille de l'écran (ou à sa hauteur naturelle si elle est plus haute).
    private void vue(View v, String nom) {
        android.util.DisplayMetrics m = v.getResources().getDisplayMetrics();
        int w = m.widthPixels;
        v.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        int h = Math.max(m.heightPixels / 2, Math.min(v.getMeasuredHeight(), 12_000));
        if (v instanceof Epreuves.Ecran) h = m.heightPixels;
        v.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(h, View.MeasureSpec.EXACTLY));
        v.layout(0, 0, w, h);
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        cv.drawColor(Ui.p(v.getContext()).fond);
        v.draw(cv);
        ecrire(b, nom);
    }

    private void atelier(String jeu) {

        Intent i = new Intent(RuntimeEnvironment.getApplication(), Atelier.class).putExtra(Atelier.EXTRA_JEU, jeu);
        ActivityController<Atelier> c = Robolectric.buildActivity(Atelier.class, i).setup().visible();
        attendre();
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(3));
        ecran(c.get(), "atelier-" + jeu);
        c.pause().stop().destroy();
    }

    private void installation() {
        ActivityController<Installation> c = Robolectric.buildActivity(Installation.class).setup().visible();
        attendre();
        ecran(c.get(), "installation");
        c.pause().stop().destroy();
    }

    // Chasse aux bugs se dessine dans une SurfaceView : on rend son monde directement, comme le fait le jeu.
    private void chasse() {
        Chasse jeu = new Chasse(7);
        rendreChasse(jeu, "chasse-accueil");
        jeu.commencer();
        for (int k = 0; k < 90; k++) jeu.avancer(1 / 60f);
        rendreChasse(jeu, "chasse-partie");
        jeu.pause(true);
        rendreChasse(jeu, "chasse-pause");
    }

    private void rendreChasse(Chasse jeu, String nom) {
        android.util.DisplayMetrics m = RuntimeEnvironment.getApplication().getResources().getDisplayMetrics();
        int w = m.widthPixels, h = m.heightPixels;
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        cv.drawColor(ChasseDessin.NUIT);
        Paint pt = new Paint();
        float k = Math.min(w / Chasse.W, h / Chasse.H);
        float ox = (w - Chasse.W * k) / 2, oy = (h - Chasse.H * k) / 2;
        ChasseDessin.dessiner((g, ht, d, bas, couleur) -> {
            pt.setColor(couleur);
            cv.drawRect(g, ht, d, bas, pt);
        }, jeu, ox, oy, k, 1000, 1240);
        ecrire(b, nom);
    }

    // ---- Prise de vue

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

    // Tout le contenu d'une page, même la partie qu'il faut faire défiler.
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
        String fichier = format + "-" + nom;
        try (FileOutputStream f = new FileOutputStream(new File(dossier, fichier + ".png"))) {
            b.compress(Bitmap.CompressFormat.PNG, 100, f);
        } catch (Exception e) {
            System.out.println("CAPTURE-ERREUR " + fichier + " " + e);
        }
        if (!miniatures) return;
        // Miniature lisible depuis les journaux de la CI : ~560 px de haut (les pages longues, plus).
        float k = Math.min(1f, 560f / Math.min(b.getHeight(), b.getWidth() * 2f));
        Bitmap mini = Bitmap.createScaledBitmap(b, Math.max(1, Math.round(b.getWidth() * k)), Math.max(1, Math.round(b.getHeight() * k)), true);
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        mini.compress(Bitmap.CompressFormat.PNG, 100, o);
        String s = Base64.encodeToString(o.toByteArray(), Base64.NO_WRAP);
        int n = (s.length() + 3999) / 4000;
        for (int i = 0; i < n; i++)
            System.out.println("CAPTURE " + fichier + " " + (i + 1) + "/" + n + " " + s.substring(i * 4000, Math.min(s.length(), (i + 1) * 4000)));
    }
}
