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

    /** Position (x, y) d'une vue dans la racine donnée (somme des positions des parents, moins leur défilement). */
    private static int[] position(View v, View racine) {
        int x = 0, y = 0;
        for (View c = v; c != racine && c != null; c = c.getParent() instanceof View ? (View) c.getParent() : null) {
            x += c.getLeft() - (c == v ? 0 : c.getScrollX());
            y += c.getTop() - (c == v ? 0 : c.getScrollY());
        }
        return new int[]{x, y};
    }

    private static List<View> toutes(View v) {
        List<View> l = new ArrayList<>();
        l.add(v);
        if (v instanceof android.view.ViewGroup)
            for (int i = 0; i < ((android.view.ViewGroup) v).getChildCount(); i++) l.addAll(toutes(((android.view.ViewGroup) v).getChildAt(i)));
        return l;
    }

    /** Rien sous le bandeau n'est écrit par la police système : tout TextView visible est un défaut ; tout signe de la police pixel est dessiné. */
    private static void sansTexteSysteme(Lecture l) {
        List<String> sys = new ArrayList<>();
        systemes(l, sys);
        org.junit.Assert.assertTrue("texte système dans la lecture : " + sys, sys.isEmpty());
        List<TextePixelVue> pv = new ArrayList<>();
        pixels(l, pv);
        PolicePixel pol = PolicePixel.texte();
        for (TextePixelVue t : pv)
            for (char ch : PolicePixel.preparer(t.texte()).toCharArray())
                if (!Character.isWhitespace(ch) && ch != 0x202F) org.junit.Assert.assertTrue("glyphe absent de la police : U+" + Integer.toHexString(ch) + " dans « " + t.texte() + " »", pol.connu(ch));
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
                // Le fil est ancré en bas : la dernière bulle finit 2 u au-dessus du bas de la zone du fil (les choix), et le
                // défilement tombe sur 0 (tout tient) ou sur le haut d'une bulle (moins 2 u) ou sur le bas du contenu.
                android.widget.ScrollView defil = (android.widget.ScrollView) l.filVue().getParent();
                android.view.ViewGroup fil = (android.view.ViewGroup) l.filVue();
                int y = defil.getScrollY();
                View derniere = fil.getChildAt(fil.getChildCount() - 1);
                org.junit.Assert.assertEquals("2 u entre la dernière bulle et les choix", 2 * l.unite(), defil.getHeight() - (derniere.getBottom() - y));
                boolean cale = y == 0 || y == fil.getHeight() - defil.getHeight();
                for (int i = 0; i < fil.getChildCount(); i++) if (fil.getChildAt(i).getTop() - 2 * l.unite() == y) cale = true;
                org.junit.Assert.assertTrue("fil calé : scrollY=" + y, cale);
                // Pas de séparateur de chapitre en tête du fil visible : le bandeau dit déjà « CHAPITRE 1 / 2 ».
                for (String s : AventureTest.textes(fil)) org.junit.Assert.assertFalse("séparateur en double : " + s, s.contains("CHAPITRE 1 - ") || s.contains("Chapitre 1 ·"));
                // La puce de lieu tient dans la scène (192 u de large, centrée), en haut à gauche à 1 u de ses bords (le bas à
                // droite est la place du personnage en pied).
                int k = l.unite(), W = m.widthPixels, scGauche = (W - 192 * k) / 2, scDroite = scGauche + 192 * k;
                View puce = l.puceLieu();
                int[] pp = position(puce, l);
                int[] pt = position(l.tete(), l);
                org.junit.Assert.assertEquals(scGauche + k, pp[0]);
                org.junit.Assert.assertTrue(pp[0] + puce.getWidth() <= scDroite - k);
                org.junit.Assert.assertEquals(pt[1] + k, pp[1]);
                org.junit.Assert.assertTrue(pp[1] + puce.getHeight() <= pt[1] + 80 * k);
                // La jauge : sous la scène, sur sa largeur exacte.
                int[] pj = position(l.jaugeVue(), l);
                org.junit.Assert.assertEquals(scGauche, pj[0]);
                org.junit.Assert.assertEquals(192 * k, l.jaugeVue().getWidth());
                org.junit.Assert.assertTrue(pj[1] >= pt[1] + 80 * k);
                // Les bulles de Pilou ont la largeur des choix.
                View bulle = null, choisir = null;
                for (View v : toutes(l)) {
                    String d = v.getContentDescription() == null ? "" : v.getContentDescription().toString();
                    if (bulle == null && d.startsWith("Pilou : ") && v instanceof CadrePixel.Pave) bulle = v;
                    if (choisir == null && d.startsWith("Choisir : ")) choisir = v;
                }
                org.junit.Assert.assertNotNull(bulle);
                org.junit.Assert.assertNotNull(choisir);
                org.junit.Assert.assertEquals(choisir.getWidth(), bulle.getWidth());
                org.junit.Assert.assertEquals(position(choisir, l)[0], position(bulle, l)[0]);
                ac[0].pause().stop().destroy();
            }
            // Les cartes du pied et la fin, en sombre : attente (compte à rebours à un tiers), fin, feuille « ⋯ ». Tout en police pixel.
            format = "jeu-telephone-portrait-sombre";
            RuntimeEnvironment.setQualifiers("w392dp-h873dp-night-440dpi");
            RuntimeEnvironment.setFontScale(1f);
            Map<String, String[]> pires = piresCas(pro);
            ActivityController<Principale>[] ap = new ActivityController[1];
            Lecture la = ouvrirLecture(pro, pires.get("attente")[0], ap);
            org.junit.Assert.assertEquals(Campagnes.Phase.Attente, CampagnesTel.etat(RuntimeEnvironment.getApplication()).phase);
            horloge[0] += (CampagnesTel.etat(RuntimeEnvironment.getApplication()).fin - horloge[0]) / 3;
            la.rafraichir();
            attendre();
            ecran(ap[0].get(), "attente");
            sansTexteSysteme(la);
            ap[0].pause().stop().destroy();

            ap = new ActivityController[1];
            Lecture lf = ouvrirLecture(pro, pires.get("fin")[0], ap);
            org.junit.Assert.assertEquals(Campagnes.Phase.Fin, CampagnesTel.etat(RuntimeEnvironment.getApplication()).phase);
            ecran(ap[0].get(), "fin");
            vue(lf.filVue(), "fin-fil");
            sansTexteSysteme(lf);
            ap[0].pause().stop().destroy();

            ap = new ActivityController[1];
            Lecture lm = ouvrirLecture(pro, "p1-sac", ap);
            View plus = AventureTest.trouver(lm, "Plus : carnet, mettre de côté");
            org.junit.Assert.assertNotNull(plus);
            plus.performClick();
            attendre();
            org.junit.Assert.assertTrue(lm.coucheOuverte());
            ecran(ap[0].get(), "menu");
            sansTexteSysteme(lm);
            ap[0].pause().stop().destroy();

            // La Grande Panne avec personnage, en sombre.
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
            // La scène : le décor entier, à une unité entière ; ancien lieu 192k × 80k, lieu HD 480 × 240 à ×2
            // (docs/SCENES-HD.md). Pilou y est à l'échelle du décor (même grille).
            org.junit.Assert.assertEquals(View.VISIBLE, l.theatre().getVisibility());
            int kScene = l.theatre().hd() ? 2 : k;
            org.junit.Assert.assertEquals((l.theatre().hd() ? 240 : 80) * kScene, l.theatre().getHeight());
            org.junit.Assert.assertEquals(kScene, l.theatre().echelleDessinee());
            // Le personnage est dessiné en pied dans la scène (même pixel, celui du théâtre) : pas de portrait par-dessus.
            // S'il n'était pas dessiné en pied, son portrait serait de 64k × 64k, k pixels d'écran par pixel fin.
            if (l.theatre().aPerso()) {
                org.junit.Assert.assertNotEquals(View.VISIBLE, l.portrait().getVisibility());
            } else {
                org.junit.Assert.assertEquals(View.VISIBLE, l.portrait().getVisibility());
                org.junit.Assert.assertEquals(64 * k, l.portrait().getWidth());
                org.junit.Assert.assertEquals(64 * k, l.portrait().getHeight());
                org.junit.Assert.assertEquals(k, l.portrait().echelle());
            }
            org.junit.Assert.assertTrue("Grumeau en pied dans la scène", l.theatre().aPerso());
            // Le mini-Pilou de repli (jamais montré avec le théâtre, mais prêt) : même pixel fin.
            org.junit.Assert.assertEquals((float) k, l.pilouRepli().pixelFin(), 0.001f);
            ac[0].pause().stop().destroy();

            Campagnes.Campagne pro = Campagnes.charger("prologue");
            ac = new ActivityController[1];
            l = ouvrirLecture(pro, pro.depart, ac);
            ecran(ac[0].get(), "prologue");
            org.junit.Assert.assertEquals(k, l.unite());
            // Le prologue est en HD : 240 unités à 2 pixels d'écran (480 px sur 1078), pas 80 × k ; l'unité du reste de l'écran ne bouge pas.
            org.junit.Assert.assertTrue(l.theatre().hd());
            org.junit.Assert.assertEquals(2 * 240, l.theatre().getHeight());
            ac[0].pause().stop().destroy();
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            RuntimeEnvironment.setQualifiers("");
        }
    }

    /** Une partie vraiment jouée depuis le début (le fil garde tout ce qui a été dit), ouverte dans la lecture. */
    private Lecture ouvrirPartieJouee(Campagnes.Campagne c, int bulles, ActivityController<Principale>[] ac) {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        appairer(ctx);
        horloge[0] = 1_790_000_000_000L;
        CampagnesTel.horloge = () -> horloge[0];
        android.provider.Settings.Global.putFloat(ctx.getContentResolver(), android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 0f);
        CampagnesTel.prechargerMaintenant();
        org.junit.Assert.assertNull(CampagnesTel.demarrer(ctx, c.id, true));
        for (int i = 0; i < 30; i++) {
            Campagnes.Etat e = CampagnesTel.etat(ctx);
            if (e.phase == Campagnes.Phase.Choix && CampagnesTel.fil(ctx, c.id).size() >= bulles + 1) break;
            if (e.phase == Campagnes.Phase.Choix && !e.options.isEmpty()) org.junit.Assert.assertNull(CampagnesTel.choisir(ctx, e.options.get(0).id));
            else if (e.phase == Campagnes.Phase.Depart) org.junit.Assert.assertNull(CampagnesTel.continuer(ctx));
            else if (e.phase == Campagnes.Phase.Epreuve) org.junit.Assert.assertNull(CampagnesTel.epreuve(ctx, true));
            else if (e.phase == Campagnes.Phase.Attente || e.phase == Campagnes.Phase.Repos) horloge[0] = e.fin + 1000;
            else break;
        }
        System.out.println("PARTIE-JOUEE " + CampagnesTel.etat(ctx).phase + " " + CampagnesTel.etat(ctx).noeud + " fil=" + CampagnesTel.fil(ctx, c.id).size());
        org.junit.Assert.assertEquals(Campagnes.Phase.Choix, CampagnesTel.etat(ctx).phase);
        ac[0] = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac[0].get();
        a.ouvrirLecture();
        attendre();
        Lecture l = ((PageAventure) a.page(Principale.AVENTURE)).lecture();
        l.accelerer();
        attendre();
        org.robolectric.shadows.ShadowSystemClock.advanceBy(java.time.Duration.ofMillis(4000));
        attendre();
        return l;
    }

    /** Ouvre la scène d'évolution de ce stade, touche la boîte de Pilou jusqu'à la question, et capture « evolution-<stade> ». */
    private void evolutionJusquaLaQuestion(int stade) {
        Context ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        appairer(ctx);
        android.provider.Settings.Global.putFloat(ctx.getContentResolver(), android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 0f);
        ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac.get();
        a.ouvrirEvolution(stade);
        attendre();
        SceneEvolution ev = a.evolution();
        org.junit.Assert.assertNotNull(ev);
        org.robolectric.shadows.ShadowSystemClock.advanceBy(java.time.Duration.ofMillis(4000));   // Pilou est entré dans la scène
        attendre();
        for (int i = 0; i < 40 && !ev.questionPosee(); i++) {
            for (View w : toutes(ev)) {
                CharSequence d = w.getContentDescription();
                if (d != null && d.toString().startsWith("Pilou raconte")) w.performClick();
            }
            attendre();
        }
        org.junit.Assert.assertTrue("la question est posée", ev.questionPosee());
        org.junit.Assert.assertEquals(3, ev.optionsVues().size());
        ecran(a, "evolution-" + stade);
        ac.pause().stop().destroy();
    }

    /**
     * Deux captures du pilote (1078 x 2400, sombre) : une lecture avec au moins trois bulles d'historique au-dessus des
     * choix (les précédentes remplissent l'espace, entières : le défilement tombe sur une bulle) ; et La Grande Panne avec
     * Grumeau en pied dans le hall.
     */
    @SuppressWarnings("unchecked")
    @Test
    public void historiqueEtPersonnageEnPiedSurTelephonePortrait() {
        dossier = new File("build/captures");
        dossier.mkdirs();
        format = "jeu-telephone-portrait-sombre";
        RuntimeEnvironment.setQualifiers("w392dp-h873dp-night-440dpi");
        RuntimeEnvironment.setFontScale(1f);
        try {
            Campagnes.Campagne pro = Campagnes.charger("prologue");
            ActivityController<Principale>[] ac = new ActivityController[1];
            Lecture l = ouvrirPartieJouee(pro, 4, ac);
            Activity a = ac[0].get();
            org.junit.Assert.assertEquals(1078, a.getResources().getDisplayMetrics().widthPixels);
            org.junit.Assert.assertEquals(2400, a.getResources().getDisplayMetrics().heightPixels);
            ecran(a, "historique");
            // Les bulles visibles au-dessus des choix : au moins trois entières, aucune coupée par le bas du fil (celle qu entame le haut est masquée par Defil, la place reste vide).
            android.widget.ScrollView defil = (android.widget.ScrollView) l.filVue().getParent();
            android.view.ViewGroup fil = (android.view.ViewGroup) l.filVue();
            int y = defil.getScrollY(), entieres = 0;
            for (int i = 0; i < fil.getChildCount(); i++) {
                View v = fil.getChildAt(i);
                String d = v.getContentDescription() == null ? "" : v.getContentDescription().toString();
                boolean bulle = false;
                for (View w : toutes(v)) {
                    String dw = w.getContentDescription() == null ? "" : w.getContentDescription().toString();
                    if (w instanceof CadrePixel.Pave && (dw.startsWith("Pilou : ") || dw.startsWith("Toi : "))) bulle = true;
                }
                if (!bulle) continue;
                boolean coupee = v.getTop() < y + defil.getHeight() && v.getBottom() > y + defil.getHeight();
                org.junit.Assert.assertFalse("bulle coupée : " + d + " top=" + v.getTop() + " bas=" + v.getBottom() + " y=" + y, coupee);
                if (v.getTop() >= y && v.getBottom() <= y + defil.getHeight()) entieres++;
            }
            org.junit.Assert.assertTrue("bulles entières visibles : " + entieres, entieres >= 3);
            ac[0].pause().stop().destroy();

            Campagnes.Campagne gp = Campagnes.charger("grande-panne");
            ac = new ActivityController[1];
            Lecture lg = ouvrirLecture(gp, "ch1-reponse", ac);
            org.junit.Assert.assertEquals(View.VISIBLE, lg.theatre().getVisibility());
            ecran(ac[0].get(), "grande-panne-grumeau-en-pied");
            ac[0].pause().stop().destroy();

            // Le phare éteint : les humains sont dessinés en pied (Perrine, à l'auberge du Bigorneau).
            Campagnes.Campagne pe = Campagnes.charger("phare-eteint");
            ac = new ActivityController[1];
            Lecture lp = ouvrirLecture(pe, "ch2-soupe", ac);
            org.junit.Assert.assertEquals(View.VISIBLE, lp.theatre().getVisibility());
            org.junit.Assert.assertTrue(lp.theatre().aPerso());
            ecran(ac[0].get(), "phare-eteint-perrine-en-pied");
            ac[0].pause().stop().destroy();

            // Petit Nuage : Brouillon flotte au-dessus du pré aux draps (personnage volant, sans alpha lissé).
            Campagnes.Campagne pn = Campagnes.charger("petit-nuage");
            ac = new ActivityController[1];
            Lecture ln = ouvrirLecture(pn, "ch2-draps", ac);
            org.junit.Assert.assertEquals(View.VISIBLE, ln.theatre().getVisibility());
            org.junit.Assert.assertTrue(ln.theatre().aPerso());
            ecran(ac[0].get(), "petit-nuage-brouillon-en-pied");
            ac[0].pause().stop().destroy();

            // Les scènes d'évolution (stades 2, 3, 4), avancées jusqu'à la question : options visibles.
            for (int stade = 2; stade <= 4; stade++) evolutionJusquaLaQuestion(stade);
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            RuntimeEnvironment.setQualifiers("");
            RuntimeEnvironment.setFontScale(1f);
        }
    }

    /**
     * Théâtre HD (docs/SCENES-HD.md) sur un téléphone de 1078 × 2400, sombre : la mare du prologue est en HD (scène de
     * 480 × 240 unités à 2 pixels d'écran, 960 × 480 px, 59 px de marge de chaque côté, rien de coupé) ; un lieu de
     * Petit Nuage, sans décor HD, reste en ancien (192 × 80 à ×5). La puce du lieu reste dans la partie visible.
     */
    @SuppressWarnings("unchecked")
    @Test
    public void lieuHdEtLieuAncienSurTelephonePortrait() {
        dossier = new File("build/captures");
        dossier.mkdirs();
        format = "jeu-telephone-portrait-sombre";
        RuntimeEnvironment.setQualifiers("w392dp-h873dp-night-440dpi");
        RuntimeEnvironment.setFontScale(1f);
        try {
            Campagnes.Campagne pro = Campagnes.charger("prologue");
            ActivityController<Principale>[] ac = new ActivityController[1];
            Lecture l = ouvrirLecture(pro, "p1-mare", ac);
            Activity a = ac[0].get();
            org.junit.Assert.assertEquals(1078, a.getResources().getDisplayMetrics().widthPixels);
            TheatreVue t = l.theatre();
            org.junit.Assert.assertEquals(View.VISIBLE, t.getVisibility());
            org.junit.Assert.assertTrue(t.hd());
            org.junit.Assert.assertEquals(480, t.largeurBitmap());
            org.junit.Assert.assertEquals(240, t.hauteurBitmap());
            org.junit.Assert.assertEquals(480, t.getHeight());
            org.junit.Assert.assertEquals(480, l.tete().getHeight());
            // La puce du lieu : dans la partie visible (960 px, centrée), pas dans la marge.
            View puce = l.puceLieu();
            org.junit.Assert.assertTrue("puce à gauche : " + puce.getLeft(), puce.getLeft() >= 59);
            org.junit.Assert.assertTrue("puce à droite : " + puce.getRight(), puce.getRight() <= 1078 - 59);
            ecran(a, "prologue-mare-hd");
            org.junit.Assert.assertEquals(2, t.echelleDessinee());
            ac[0].pause().stop().destroy();

            Campagnes.Campagne pn = Campagnes.charger("petit-nuage");
            ac = new ActivityController[1];
            Lecture ln = ouvrirLecture(pn, "ch1-orage", ac);
            org.junit.Assert.assertEquals(View.VISIBLE, ln.theatre().getVisibility());
            org.junit.Assert.assertFalse(ln.theatre().hd());
            org.junit.Assert.assertEquals(192, ln.theatre().largeurBitmap());
            org.junit.Assert.assertEquals(80, ln.theatre().hauteurBitmap());
            org.junit.Assert.assertEquals(400, ln.tete().getHeight());
            ecran(ac[0].get(), "petit-nuage-ancien");
            ac[0].pause().stop().destroy();
        } finally {
            CampagnesTel.horloge = System::currentTimeMillis;
            RuntimeEnvironment.setQualifiers("");
            RuntimeEnvironment.setFontScale(1f);
        }
    }
}
