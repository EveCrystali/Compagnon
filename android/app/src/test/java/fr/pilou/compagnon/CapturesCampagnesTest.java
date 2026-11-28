package fr.pilou.compagnon;

import static org.robolectric.Shadows.shadowOf;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
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
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Test de jeu (docs/TEST-JEU.md) : la lecture de chaque campagne photographiée sur ses pires cas réels — le message le
 * plus long, le choix le plus chargé (options et libellés les plus longs), un départ et une attente, l'épreuve, le repos,
 * la fin au titre le plus long — sur un petit téléphone (360 × 640 dp), en thème clair, en sombre, et en grande police
 * (× 1,3). Images dans build/captures (préfixe « jeu- »), miniatures dans le journal (lignes CAPTURE). Ne fait jamais
 * échouer le build : un écran qui refuse de se dessiner écrit CAPTURE-ERREUR.
 */
@RunWith(RobolectricTestRunner.class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = 34)
public class CapturesCampagnesTest {
    private static final String[][] FORMATS = {
            {"jeu-petit-clair", "w360dp-h640dp-notnight-xhdpi", "1"},
            {"jeu-petit-sombre", "w360dp-h640dp-night-xhdpi", "1"},
            {"jeu-petit-grandepolice", "w360dp-h640dp-notnight-xhdpi", "1.3"},
    };
    private static final String[] CAMPAGNES = {"prologue", "grande-panne", "phare-eteint", "petit-nuage"};

    private File dossier;
    private String format;
    private final long[] horloge = {0};

    @Test
    public void piresCasDeChaqueCampagne() {
        try {
            dossier = new File("build/captures");
            dossier.mkdirs();
            for (String[] f : FORMATS) {
                format = f[0];
                RuntimeEnvironment.setQualifiers(f[1]);
                RuntimeEnvironment.setFontScale(Float.parseFloat(f[2]));
                for (String id : CAMPAGNES) {
                    Campagnes.Campagne c = Campagnes.charger(id);
                    if (c == null) continue;
                    // En sombre, seulement les deux écrans les plus chargés (contraste) ; sinon tout.
                    for (Map.Entry<String, String[]> cas : piresCas(c).entrySet()) {
                        if (format.endsWith("sombre") && !cas.getKey().equals("texte") && !cas.getKey().equals("choix")) continue;
                        essayer(id + "-" + cas.getKey(), () -> photographier(c, cas.getKey(), cas.getValue()));
                    }
                }
            }
            RuntimeEnvironment.setFontScale(1f);
        } catch (Throwable t) {
            System.out.println("CAPTURES-SAUTEES " + t);
        }
    }

    /**
     * La bibliothèque d'un joueur de niveau 12 sans haut fait, avec la campagne d'essai fermée par « Plume » et par le
     * prologue : la carte dit ce qu'il manque (préfixe « bibliotheque-haut-fait »), clair et sombre.
     */
    @Test
    public void bibliothequeAvecUneCampagneFermeeParUnHautFait() {
        Context ctx = RuntimeEnvironment.getApplication();
        try {
            dossier = new File("build/captures");
            dossier.mkdirs();
            CampagnesTel.EN_PLUS.add(CampagnesTest.hautFait());
            for (String[] f : new String[][]{FORMATS[0], FORMATS[1]}) {
                format = f[0];
                RuntimeEnvironment.setQualifiers(f[1]);
                essayer("bibliotheque-haut-fait", () -> {
                    Prefs.de(ctx).edit().clear().commit();
                    appairer(ctx);
                    CampagnesTel.prechargerMaintenant();
                    ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
                    Principale a = ac.get();
                    a.aller(Principale.AVENTURE, false);
                    attendre();
                    PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
                    pa.rafraichir();
                    attendre();
                    vue(pa.corps, "bibliotheque-haut-fait");
                    ac.pause().stop().destroy();
                });
            }
        } catch (Throwable t) {
            System.out.println("CAPTURES-SAUTEES " + t);
        } finally {
            CampagnesTel.EN_PLUS.clear();
        }
    }

    private void essayer(String nom, Runnable r) {
        try {
            r.run();
        } catch (Throwable t) {
            System.out.println("CAPTURE-ERREUR " + format + "-" + nom + " " + t);
        }
    }

    // ---- Les pires cas, tirés des fichiers de la campagne : { nœud, geste (1) ou départ à confirmer (0) }

    static Map<String, String[]> piresCas(Campagnes.Campagne c) {
        Map<String, String[]> l = new java.util.LinkedHashMap<>();
        Campagnes.Noeud texte = null, choix = null, attente = null, epreuve = null, repos = null, fin = null;
        int mTexte = -1, mChoix = -1, mAttente = -1, mEpreuve = -1, mRepos = -1, mFin = -1;
        List<String> ids = new ArrayList<>(c.noeuds.keySet());
        java.util.Collections.sort(ids);
        for (String id : ids) {
            Campagnes.Noeud n = c.noeuds.get(id);
            int mots = 0;
            for (String t : n.texte) mots = Math.max(mots, t.split("\\s+").length);
            if (mots > mTexte) {
                mTexte = mots;
                texte = n;
            }
            switch (n.type) {
                case "choix": {
                    // Ce qui sera vraiment proposé (sans rien, ou avec tout ce qui se gagne en route) : le plus d'options,
                    // puis les libellés les plus longs.
                    int s = 0;
                    for (boolean tout : new boolean[]{false, true}) {
                        Campagnes.Etat e = Campagnes.rejouer(c, Campagnes.lirePartie(partie(c, id, true, 1_790_000_000_000L, tout)), 1_790_000_000_000L);
                        int v = e.options.size() * 1000;
                        for (Campagnes.OptionVue o : e.options) v += o.libelle.length();
                        s = Math.max(s, v);
                    }
                    if (s > mChoix) {
                        mChoix = s;
                        choix = n;
                    }
                    break;
                }
                case "attente": {
                    int s = n.pendant.length() * 10 + mots;
                    if (s > mAttente) {
                        mAttente = s;
                        attente = n;
                    }
                    break;
                }
                case "epreuve":
                    if (!n.jeu.equals("des") && mots > mEpreuve) {
                        mEpreuve = mots;
                        epreuve = n;
                    }
                    break;
                case "echec":
                    if (mots > mRepos) {
                        mRepos = mots;
                        repos = n;
                    }
                    break;
                case "fin": {
                    int s = n.titre.length() * 10 + mots;
                    if (s > mFin) {
                        mFin = s;
                        fin = n;
                    }
                    break;
                }
                default:
                    break;
            }
        }
        if (texte != null) l.put("texte", new String[]{texte.id, "1"});
        if (choix != null) l.put("choix", new String[]{choix.id, "1"});
        if (attente != null) {
            l.put("depart", new String[]{attente.id, "0"});
            l.put("attente", new String[]{attente.id, "1"});
        }
        if (epreuve != null) l.put("epreuve", new String[]{epreuve.id, "1"});
        if (repos != null) l.put("repos", new String[]{repos.id, "1"});
        if (fin != null) l.put("fin", new String[]{fin.id, "1"});
        return l;
    }

    /** Décor et nœud du lieu hérités en arrivant à chaque nœud (premier chemin trouvé depuis le départ). */
    static Map<String, String[]> herites(Campagnes.Campagne c) {
        Map<String, String[]> vu = new HashMap<>();
        ArrayDeque<String[]> file = new ArrayDeque<>();
        file.add(new String[]{c.depart, "", ""});
        while (!file.isEmpty()) {
            String[] x = file.poll();
            Campagnes.Noeud n = c.noeuds.get(x[0]);
            if (n == null || vu.containsKey(x[0])) continue;
            vu.put(x[0], new String[]{x[1], x[2]});
            String decor = n.decor.isEmpty() ? x[1] : n.decor, lieu = n.lieu.isEmpty() ? x[2] : n.id;
            List<String> suites = new ArrayList<>();
            if (!n.suite.isEmpty()) suites.add(n.suite);
            for (Campagnes.Option o : n.options) suites.add(o.vers);
            for (Campagnes.IssueHasard h : n.issues) suites.add(h.vers);
            if (!n.reussite.isEmpty()) suites.add(n.reussite);
            if (!n.echec.isEmpty()) suites.add(n.echec);
            for (String s : suites) file.add(new String[]{s, decor, lieu});
        }
        return vu;
    }

    // Une partie posée au nœud voulu (base « ici »), tous drapeaux et objets acquis quand cela montre plus d'options.
    private static String partie(Campagnes.Campagne c, String noeud, boolean geste, long t, boolean tout) {
        String[] h = herites(c).get(noeud);
        String decor = h == null || h[0].isEmpty() ? "" : Campagnes.code(h[0]), lieu = h == null || h[1].isEmpty() ? "" : Campagnes.code(h[1]);
        StringBuilder objets = new StringBuilder(), drapeaux = new StringBuilder();
        if (tout) {
            for (Campagnes.Nomme o : c.objets) if (!o.portable) objets.append(Campagnes.code(o.id));
            java.util.TreeSet<String> d = new java.util.TreeSet<>();
            for (Campagnes.Noeud n : c.noeuds.values()) {
                for (Campagnes.Effet e : n.effets) if (e.sorte.equals("drapeau")) d.add(Campagnes.code(e.nom));
                for (Campagnes.Option o : n.options) for (Campagnes.Effet e : o.effets) if (e.sorte.equals("drapeau")) d.add(Campagnes.code(e.nom));
            }
            for (String x : d) drapeaux.append(x);
        }
        return "{\"c\":\"" + c.id + "\",\"p\":1,\"d\":" + t / 1000 + ",\"o\":\"tel-capture\",\"g\":\"capture\",\"x\":" + (geste ? 2 : 0)
                + ",\"e\":0,\"r\":0,\"i\":0,\"n\":0,\"t\":" + t / 1000 + ",\"ici\":[\"" + Campagnes.code(noeud) + "\",{},\"" + objets + "\",\"" + drapeaux
                + "\",\"" + decor + "\",\"" + lieu + "\"]}";
    }

    private void photographier(Campagnes.Campagne c, String cas, String[] quoi) {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        appairer(ctx);
        horloge[0] = 1_790_000_000_000L;
        CampagnesTel.horloge = () -> horloge[0];
        android.provider.Settings.Global.putFloat(ctx.getContentResolver(), android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 0f);
        CampagnesTel.prechargerMaintenant();
        try {
            Campagnes.Carnet k = new Campagnes.Carnet();
            String json = partie(c, quoi[0], quoi[1].equals("1"), horloge[0], false);
            if (cas.equals("choix")) {
                // Le plus d'options possible : avec ou sans tout ce qui se gagne en route.
                String tout = partie(c, quoi[0], true, horloge[0], true);
                Campagnes.Etat a = Campagnes.rejouer(c, Campagnes.lirePartie(json), horloge[0]);
                Campagnes.Etat b = Campagnes.rejouer(c, Campagnes.lirePartie(tout), horloge[0]);
                if (b.options.size() > a.options.size()) json = tout;
            }
            k.courante = Campagnes.lirePartie(json);
            Prefs.de(ctx).edit().putString("campagnes", Campagnes.sauver(k)).commit();
            Campagnes.Etat e = CampagnesTel.etat(ctx);
            if (cas.equals("attente") && e.phase == Campagnes.Phase.Attente) horloge[0] += (e.fin - horloge[0]) / 3;
            ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
            Principale a = ac.get();
            a.ouvrirLecture();
            attendre();
            PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
            Lecture l = pa.lecture();
            l.accelerer();
            attendre();
            ecran(a, c.id + "-" + cas);
            if (cas.equals("texte") || cas.equals("fin")) vue(l.filVue(), c.id + "-" + cas + "-fil");
            if (cas.equals("epreuve")) {
                l.ouvrirEpreuve(false);
                attendre();
                ecran(a, c.id + "-" + cas + "-jeu");
                l.fermerCouche();
            }
            ac.pause().stop().destroy();
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            android.provider.Settings.Global.putFloat(ctx.getContentResolver(), android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 1f);
        }
    }

    // Un téléphone appairé, au milieu d'un niveau (rien de personnel : nom et appareils fictifs).
    private static void appairer(Context ctx) {
        long t = System.currentTimeMillis();
        String etat = "{\"v\":1,\"t\":" + t + ",\"nom\":\"Pilou\",\"niveau\":12,\"titre\":\"Pêcheur du dimanche\",\"couleur\":\"bleu\","
                + "\"humeur\":\"repos\",\"calmes\":2,\"sessions\":[],\"xp\":3900,\"accessoire\":\"\",\"carnet\":[],\"plats\":[],\"recus\":[],"
                + "\"po\":240,\"objets\":[],\"porte\":{},\"stade\":2}";
        Prefs.de(ctx).edit().putString("code", "ABCDEFGHJKMNPQRS").putString("etat", etat).putLong("recu", t).commit();
    }

    // ---- Prise de vue (comme CapturesTest)

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

    private void vue(View v, String nom) {
        android.util.DisplayMetrics m = v.getResources().getDisplayMetrics();
        int w = m.widthPixels;
        v.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(0, View.MeasureSpec.UNSPECIFIED));
        int h = Math.max(m.heightPixels / 2, Math.min(v.getMeasuredHeight(), 12_000));
        v.measure(View.MeasureSpec.makeMeasureSpec(w, View.MeasureSpec.EXACTLY), View.MeasureSpec.makeMeasureSpec(h, View.MeasureSpec.EXACTLY));
        v.layout(0, 0, w, h);
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        cv.drawColor(Ui.p(v.getContext()).fond);
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
        float k = Math.min(1f, 560f / Math.min(b.getHeight(), b.getWidth() * 2f));
        Bitmap mini = Bitmap.createScaledBitmap(b, Math.max(1, Math.round(b.getWidth() * k)), Math.max(1, Math.round(b.getHeight() * k)), true);
        ByteArrayOutputStream o = new ByteArrayOutputStream();
        mini.compress(Bitmap.CompressFormat.PNG, 100, o);
        String s = Base64.encodeToString(o.toByteArray(), Base64.NO_WRAP);
        int n = (s.length() + 3999) / 4000;
        for (int i = 0; i < n; i++)
            System.out.println("CAPTURE " + fichier + " " + (i + 1) + "/" + n + " " + s.substring(i * 4000, Math.min(s.length(), (i + 1) * 4000)));
        System.out.println(String.format(Locale.ROOT, "CAPTURE-TAILLE %s %dx%d", fichier, b.getWidth(), b.getHeight()));
    }

    // ---- Une seule unité de pixel sur tout l'écran Aventure (téléphone portrait 1080 × 2400, densité 2,75)

    /** Un nœud de La Grande Panne où un personnage parle, dans un lieu dessiné (comme l'essai PC « personnage »). */
    private static String noeudAvecPersonnage(Campagnes.Campagne c) {
        List<String> ids = new ArrayList<>(c.noeuds.keySet());
        java.util.Collections.sort(ids);
        Map<String, String[]> h = herites(c);
        for (String id : ids) {
            Campagnes.Noeud n = c.noeuds.get(id);
            String[] d = h.get(id);
            if (n.personnage.isEmpty() || n.texte.isEmpty() || d == null || d[0].isEmpty()) continue;
            if (!n.type.equals("texte") && !n.type.equals("choix")) continue;
            if (Animations.portrait(Sprites.banque(), c.id, n.personnage, n.expression, 2) == null) continue;
            if (Sprites.decor(Sprites.banque(), c.id, d[0], 2) == null) continue;
            return id;
        }
        throw new AssertionError("aucun nœud avec personnage dans " + c.id);
    }

    private Lecture ouvrirLecture(Campagnes.Campagne c, String noeud, ActivityController<Principale>[] ac) {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        appairer(ctx);
        horloge[0] = 1_790_000_000_000L;
        CampagnesTel.horloge = () -> horloge[0];
        android.provider.Settings.Global.putFloat(ctx.getContentResolver(), android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 0f);
        CampagnesTel.prechargerMaintenant();
        Campagnes.Carnet k = new Campagnes.Carnet();
        k.courante = Campagnes.lirePartie(partie(c, noeud, true, horloge[0], false));
        Prefs.de(ctx).edit().putString("campagnes", Campagnes.sauver(k)).commit();
        ac[0] = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac[0].get();
        a.ouvrirLecture();
        attendre();
        Lecture l = ((PageAventure) a.page(Principale.AVENTURE)).lecture();
        l.accelerer();
        attendre();
        org.robolectric.shadows.ShadowSystemClock.advanceBy(java.time.Duration.ofMillis(4000));   // Pilou est entré dans la scène
        attendre();
        return l;
    }

    private static void pixels(View v, List<TextePixelVue> l) {
        if (v.getVisibility() != View.VISIBLE) return;
        if (v instanceof TextePixelVue) l.add((TextePixelVue) v);
        if (v instanceof android.view.ViewGroup)
            for (int i = 0; i < ((android.view.ViewGroup) v).getChildCount(); i++) pixels(((android.view.ViewGroup) v).getChildAt(i), l);
    }

    private static void systemes(View v, List<String> l) {
        if (v.getVisibility() != View.VISIBLE) return;
        if (v instanceof android.widget.TextView && ((android.widget.TextView) v).getText().length() > 0) l.add(((android.widget.TextView) v).getText().toString());
        if (v instanceof android.view.ViewGroup)
            for (int i = 0; i < ((android.view.ViewGroup) v).getChildCount(); i++) systemes(((android.view.ViewGroup) v).getChildAt(i), l);
    }

    /**
     * La lecture « main de Pilou » (cadres et police pixel) sur un téléphone 1078 × 2400 (392 × 873 dp, 440 dpi, densité 2,75) :
     * le prologue à son premier choix en sombre, en clair, en grande police (× 1,3, sombre), et La Grande Panne avec son
     * personnage en sombre. Images dans build/captures (jeu-telephone-portrait-*).
     */
    @SuppressWarnings("unchecked")
    @Test
    public void lecturePixelSurTelephonePortrait() {
        dossier = new File("build/captures");
        dossier.mkdirs();
        String[][] cas = {
                {"sombre", "w392dp-h873dp-night-440dpi", "1", "4"},
                {"clair", "w392dp-h873dp-notnight-440dpi", "1", "4"},
                {"grandepolice-sombre", "w392dp-h873dp-night-440dpi", "1.3", "5"},
        };
        try {
            Campagnes.Campagne pro = Campagnes.charger("prologue");
            for (String[] c : cas) {
                format = "jeu-telephone-portrait-" + c[0];
                RuntimeEnvironment.setQualifiers(c[1]);
                RuntimeEnvironment.setFontScale(Float.parseFloat(c[2]));
                ActivityController<Principale>[] ac = new ActivityController[1];
                Lecture l = ouvrirLecture(pro, "p1-sac", ac);
                Activity a = ac[0].get();
                ecran(a, "prologue-choix");
                android.util.DisplayMetrics m = a.getResources().getDisplayMetrics();
                org.junit.Assert.assertEquals(1078, m.widthPixels);
                org.junit.Assert.assertEquals(5, l.unite());
                // Le texte du récit et des choix : police pixel entière (4 pixels d'écran, 5 en grande police), jamais la police système.
                List<TextePixelVue> pv = new ArrayList<>();
                pixels(l, pv);
                int choix = 0;
                List<TextePixelVue> bulles = new ArrayList<>();
                pixels(l.filVue(), bulles);
                org.junit.Assert.assertFalse(bulles.isEmpty());
                for (TextePixelVue t : bulles) org.junit.Assert.assertEquals(Integer.parseInt(c[3]), t.pixel());
                for (Campagnes.OptionVue o : CampagnesTel.etat(RuntimeEnvironment.getApplication()).options)
                    for (TextePixelVue t : pv) if (t.texte().equals(o.libelle)) {
                        choix++;
                        org.junit.Assert.assertEquals(Integer.parseInt(c[3]), t.pixel());
                    }
                org.junit.Assert.assertTrue("choix en police pixel", choix > 0);
                List<String> sys = new ArrayList<>();
                systemes(l, sys);
                for (String s : sys) org.junit.Assert.assertFalse("texte système sous la scène : " + s, s.contains("CHAPITRE") || s.contains("Devant"));
                // Le fil est calé sur une bulle entière : son haut tombe sur le haut d'une bulle (moins 2 u) ou sur 0.
                android.widget.ScrollView defil = (android.widget.ScrollView) l.filVue().getParent();
                int y = defil.getScrollY();
                boolean cale = y == 0;
                for (int i = 0; i < ((android.view.ViewGroup) l.filVue()).getChildCount(); i++)
                    if (((android.view.ViewGroup) l.filVue()).getChildAt(i).getTop() - 2 * l.unite() == y) cale = true;
                org.junit.Assert.assertTrue("fil calé sur une bulle : scrollY=" + y, cale);
                ac[0].pause().stop().destroy();
            }
            // La Grande Panne avec personnage, en sombre.
            format = "jeu-telephone-portrait-sombre";
            RuntimeEnvironment.setQualifiers("w392dp-h873dp-night-440dpi");
            RuntimeEnvironment.setFontScale(1f);
            Campagnes.Campagne gp = Campagnes.charger("grande-panne");
            ActivityController<Principale>[] ac = new ActivityController[1];
            ouvrirLecture(gp, noeudAvecPersonnage(gp), ac);
            ecran(ac[0].get(), "grande-panne-personnage-pixel");
            ac[0].pause().stop().destroy();
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            RuntimeEnvironment.setQualifiers("");
            RuntimeEnvironment.setFontScale(1f);
        }
    }

    @SuppressWarnings("unchecked")
    @Test
    public void uneSeuleUniteDePixelSurTelephonePortrait() {
        dossier = new File("build/captures");
        dossier.mkdirs();
        format = "jeu-telephone-portrait";
        RuntimeEnvironment.setQualifiers("w392dp-h873dp-notnight-440dpi");
        RuntimeEnvironment.setFontScale(1f);
        try {
            Campagnes.Campagne gp = Campagnes.charger("grande-panne");
            String noeud = noeudAvecPersonnage(gp);
            ActivityController<Principale>[] ac = new ActivityController[1];
            Lecture l = ouvrirLecture(gp, noeud, ac);
            Activity a = ac[0].get();
            ecran(a, "grande-panne-personnage");
            int largeur = a.getResources().getDisplayMetrics().widthPixels;
            int k = l.unite();
            org.junit.Assert.assertEquals(Math.max(1, largeur / 192), k);
            org.junit.Assert.assertEquals(5, k);
            // La scène : 192k × 80k, le décor entier ; Pilou y est à l'échelle du décor (même grille fine).
            org.junit.Assert.assertEquals(View.VISIBLE, l.theatre().getVisibility());
            org.junit.Assert.assertEquals(80 * k, l.theatre().getHeight());
            org.junit.Assert.assertEquals(k, l.theatre().echelleDessinee());
            // Le portrait du personnage : 64k × 64k, k pixels d'écran par pixel fin.
            org.junit.Assert.assertEquals(View.VISIBLE, l.portrait().getVisibility());
            org.junit.Assert.assertEquals(64 * k, l.portrait().getWidth());
            org.junit.Assert.assertEquals(64 * k, l.portrait().getHeight());
            org.junit.Assert.assertEquals(k, l.portrait().echelle());
            // Le mini-Pilou de repli (jamais montré avec le théâtre, mais prêt) : même pixel fin.
            org.junit.Assert.assertEquals((float) k, l.pilouRepli().pixelFin(), 0.001f);
            ac[0].pause().stop().destroy();

            Campagnes.Campagne pro = Campagnes.charger("prologue");
            ac = new ActivityController[1];
            l = ouvrirLecture(pro, pro.depart, ac);
            ecran(ac[0].get(), "prologue");
            org.junit.Assert.assertEquals(k, l.unite());
            org.junit.Assert.assertEquals(80 * k, l.theatre().getHeight());
            ac[0].pause().stop().destroy();
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            RuntimeEnvironment.setQualifiers("");
        }
    }
}
