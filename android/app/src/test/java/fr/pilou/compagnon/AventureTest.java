package fr.pilou.compagnon;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.robolectric.Shadows.shadowOf;

import android.app.AlarmManager;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.android.controller.ActivityController;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * L'onglet Aventure, de bout en bout, avec une horloge injectée : démarrer le prologue, choisir, attendre (l'alarme du
 * retour est posée, la notification part une seule fois), réussir une épreuve, échouer (repos, puis reprise au
 * check-point), finir (fin, souvenir, récompenses en attente du PC), mettre de côté et reprendre ; dans l'interface aussi.
 */
@RunWith(RobolectricTestRunner.class)
public class AventureTest {
    /** Une graine du prologue où le raccourci fait glisser Pilou (échec), et une où il passe. */
    static final String GLISSE = "9e3779b1", PASSE = "00000000";
    private final long[] t = {1_800_000_000_000L};
    private Context ctx;

    @Before
    public void preparer() {
        ctx = RuntimeEnvironment.getApplication();
        Prefs.de(ctx).edit().clear().commit();
        CampagnesTel.horloge = () -> t[0];
        CampagnesTel.graineEssai = GLISSE;
        CampagnesTel.prechargerMaintenant();
    }

    @After
    public void ranger() {
        CampagnesTel.EN_PLUS.clear();
        CampagnesTel.horloge = System::currentTimeMillis;
        CampagnesTel.graineEssai = null;
    }

    private Campagnes.Etat etat() {
        return CampagnesTel.etat(ctx);
    }

    private void apres(Campagnes.Etat e) {
        t[0] = e.fin + 1000;
    }

    private int notifications() {
        return shadowOf(ctx.getSystemService(NotificationManager.class)).getAllNotifications().size();
    }

    @Test
    public void parcoursCompletDuPrologue() {
        assertNull(CampagnesTel.demarrer(ctx, "prologue", false));
        Campagnes.Etat e = etat();
        assertEquals(Campagnes.Phase.Choix, e.phase);
        assertEquals("p1-sac", e.noeud);
        assertTrue(CampagnesTel.attendJoueur(ctx, e));
        assertTrue(CampagnesTel.nonLus(ctx) > 0);
        assertFalse(CampagnesTel.fil(ctx, "prologue").isEmpty());

        // Un choix : Pilou part (attente d'une minute), l'alarme du retour est posée.
        assertNull(CampagnesTel.choisir(ctx, "lampe"));
        e = etat();
        assertEquals(Campagnes.Phase.Attente, e.phase);
        assertTrue(e.fin > t[0]);
        assertFalse(CampagnesTel.attendJoueur(ctx, e));
        assertNotNull(shadowOf(ctx.getSystemService(AlarmManager.class)).getNextScheduledAlarm());
        // Trop tôt : rien.
        Retour.verifier(ctx);
        assertEquals(0, notifications());

        // Il revient : une notification, une seule (pas de relance).
        apres(e);
        Retour.verifier(ctx);
        assertEquals(1, notifications());
        Retour.verifier(ctx);
        assertEquals(1, notifications());
        Retour.effacer(ctx); // le joueur l'a touchée
        assertEquals(0, notifications());
        e = etat();
        assertEquals(Campagnes.Phase.Choix, e.phase);
        assertEquals("p1-mare", e.noeud);

        // L'épreuve, réussie.
        assertNull(CampagnesTel.choisir(ctx, "saute"));
        e = etat();
        assertEquals(Campagnes.Phase.Epreuve, e.phase);
        assertEquals("reflexe", e.jeu);
        assertTrue(e.chance > 0);
        assertNull(CampagnesTel.epreuve(ctx, true));
        e = etat();
        assertEquals("p2-chemins", e.noeud);

        // Le raccourci : il glisse (échec), se repose dix minutes.
        assertNull(CampagnesTel.choisir(ctx, "raccourci"));
        e = etat();
        assertEquals(Campagnes.Phase.Repos, e.phase);
        Campagnes.Campagne c = Campagnes.charger("prologue");
        assertEquals("Au pied de la colline", CampagnesTel.lieuReprise(c, CampagnesTel.courante(ctx), e));
        apres(e);
        Retour.verifier(ctx);
        assertEquals(1, notifications());


        // Reprise au check-point : ce que Pilou redit est marqué « reprise ».
        e = etat();
        assertEquals(Campagnes.Phase.Choix, e.phase);
        assertEquals("p2-chemins", e.noeud);
        assertTrue(e.reprise);
        boolean reprise = false;
        for (Campagnes.Message m : CampagnesTel.fil(ctx, "prologue")) reprise |= m.reprise;
        assertTrue(reprise);

        // Le sentier, puis on rentre : une fin.
        assertNull(CampagnesTel.choisir(ctx, "sentier"));
        apres(etat());
        e = etat();
        assertEquals("p2-sommet", e.noeud);
        assertNull(CampagnesTel.choisir(ctx, "rentre"));
        e = etat();
        assertEquals(Campagnes.Phase.Fin, e.phase);
        assertEquals("douce-amere", e.issue);
        assertEquals(1, Campagnes.fins(CampagnesTel.carnet(ctx), c).size());
        assertEquals(2, CampagnesTel.nombreFins(c));
        int[] attente = CampagnesTel.enAttente(ctx);
        assertTrue("les gains attendent le PC", attente[0] + attente[1] > 0);
        assertTrue(Campagnes.finie(CampagnesTel.carnet(ctx), "prologue"));
    }

    @Test
    public void notificationCoupeeDansLesReglages() {
        Prefs.de(ctx).edit().putBoolean("alerteAventure", false).commit();
        assertNull(CampagnesTel.demarrer(ctx, "prologue", false));
        assertNull(CampagnesTel.choisir(ctx, "lampe"));
        apres(etat());
        Retour.verifier(ctx);
        assertEquals(0, notifications());
    }

    @Test
    public void miseDeCoteEtReprise() {
        assertNull(CampagnesTel.demarrer(ctx, "prologue", false));
        assertNull(CampagnesTel.choisir(ctx, "lampe"));
        // Même pendant l'attente, on peut la mettre de côté ; elle reprend au dernier check-point.
        assertNull(CampagnesTel.abandonner(ctx));
        assertEquals(Campagnes.Phase.Abandon, etat().phase);
        Campagnes.Campagne c = Campagnes.charger("prologue");
        assertTrue(Campagnes.reprenable(CampagnesTel.carnet(ctx), c, t[0]));
        assertNull(CampagnesTel.demarrer(ctx, "prologue", false));
        Campagnes.Etat e = etat();
        assertTrue(e.reprise);
        assertEquals("p1-sac", e.noeud);
        // Le fil de la campagne garde la conversation d'avant.
        boolean lampe = false;
        for (Campagnes.Message m : CampagnesTel.fil(ctx, "prologue")) lampe |= m.qui.equals("joueur");
        assertTrue(lampe);
    }

    // ---- Dans l'interface

    private static void idle(long ms) {
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(ms));
    }

    private static void textes(View v, List<String> l) {
        if (v.getVisibility() != View.VISIBLE) return;
        if (v instanceof TextView) l.add(((TextView) v).getText().toString());
        if (v.getContentDescription() != null) l.add(v.getContentDescription().toString());
        if (v instanceof ViewGroup) for (int i = 0; i < ((ViewGroup) v).getChildCount(); i++) textes(((ViewGroup) v).getChildAt(i), l);
    }

    static List<String> textes(View v) {
        List<String> l = new ArrayList<>();
        textes(v, l);
        return l;
    }

    /** La première vue visible dont le texte ou la description vaut s. */
    static View trouver(View v, String s) {
        if (v.getVisibility() != View.VISIBLE) return null;
        if (v instanceof TextView && s.equals(((TextView) v).getText().toString())) return v;
        if (v.getContentDescription() != null && s.equals(v.getContentDescription().toString())) return v;
        if (v instanceof ViewGroup)
            for (int i = 0; i < ((ViewGroup) v).getChildCount(); i++) {
                View r = trouver(((ViewGroup) v).getChildAt(i), s);
                if (r != null) return r;
            }
        return null;
    }

    private static void toucher(View racine, String s) {
        View v = trouver(racine, s);
        assertNotNull("introuvable : " + s + " dans " + textes(racine), v);
        v.performClick();
        idle(400);
    }

    private static boolean contient(View racine, String morceau) {
        for (String s : textes(racine)) if (s.contains(morceau)) return true;
        return false;
    }

    /** Une campagne fermée par un haut fait : la carte dit ce qu'il manque, en une ligne, avec le signe ◇ ; pas de bouton actif. */
    @Test
    public void uneCampagneFermeeParUnHautFaitDitCeQuIlManque() {
        CampagnesTel.EN_PLUS.add(CampagnesTest.hautFait());
        ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac.get();
        a.aller(Principale.AVENTURE, false);
        idle(200);
        PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
        assertTrue(textes(pa).toString(), contient(pa, "S'ouvre au niveau 2, avec le haut fait « Plume » et après « La colline d'en face »."));
        assertTrue(contient(pa, "◇  Niveau 2"));
        ac.pause().stop().destroy();
    }

    @Test
    public void parcoursDansLInterface() {
        Campagnes.Campagne c = Campagnes.charger("prologue");
        ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac.get();
        a.aller(Principale.AVENTURE, false);
        idle(200);
        PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
        assertTrue(textes(pa).toString(), contient(pa, "La colline d'en face"));
        // Niveau 1 : seul le prologue s'ouvre, les autres montrent leur niveau.
        assertTrue(contient(pa, "Niveau 3 requis"));
        toucher(pa, "Commencer");
        assertTrue(pa.lectureOuverte());
        Lecture l = pa.lecture();
        l.accelerer();
        idle(800);
        assertTrue(contient(l, "CHAPITRE 1 / 2"));
        toucher(l, "Choisir : " + c.noeud("p1-sac").options.get(0).libelle);
        l.accelerer();
        idle(800);
        assertEquals(Campagnes.Phase.Attente, etat().phase);
        assertTrue(textes(l).toString(), contient(l, "je te préviens"));
        assertTrue(contient(l, "retour vers"));

        // Il revient : la suite s'écrit, puis le choix suivant.
        apres(etat());
        a.page(Principale.AVENTURE).rafraichir();
        l.accelerer();
        idle(800);
        toucher(l, "Choisir : " + c.noeud("p1-mare").options.get(0).libelle);
        l.accelerer();
        idle(800);
        assertEquals(Campagnes.Phase.Epreuve, etat().phase);
        assertTrue(contient(l, "ÉPREUVE"));
        l.ouvrirEpreuve(false);
        idle(300);
        Epreuves.Ecran ec = l.epreuveOuverte();
        assertNotNull(ec);
        ec.forcer(true);
        idle(300);
        toucher(ec, "Continuer");
        l.accelerer();
        idle(800);
        assertEquals("p2-chemins", etat().noeud);

        // L'échec : le repos, le check-point annoncé.
        toucher(l, "Choisir : " + c.noeud("p2-chemins").options.get(1).libelle);
        l.accelerer();
        idle(800);
        assertEquals(Campagnes.Phase.Repos, etat().phase);
        assertTrue(textes(l).toString(), contient(l, "Reprise au dernier check-point : Au pied de la colline"));
        apres(etat());
        a.page(Principale.AVENTURE).rafraichir();
        l.accelerer();
        idle(800);
        assertTrue(contient(l, "On reprend au dernier check-point"));

        // La fin : issue, fins « ? ? ? », retour à la liste.
        toucher(l, "Choisir : " + c.noeud("p2-chemins").options.get(0).libelle);
        l.accelerer();
        idle(800);
        apres(etat());
        a.page(Principale.AVENTURE).rafraichir();
        l.accelerer();
        idle(800);
        String rentre = null;
        for (Campagnes.Option o : c.noeud("p2-sommet").options) if (o.id.equals("rentre")) rentre = o.libelle;
        toucher(l, "Choisir : " + rentre);
        l.accelerer();
        idle(1200);
        assertEquals(Campagnes.Phase.Fin, etat().phase);
        assertTrue(textes(l).toString(), contient(l, "FIN DE L'AVENTURE"));
        assertTrue(contient(l, "Fin pas encore découverte"));
        toucher(l, "Retour aux aventures");
        idle(400);
        assertFalse(pa.lectureOuverte());
        assertTrue(textes(pa).toString(), contient(pa, "Rejouer"));
        assertTrue(contient(pa, "1 fins obtenues sur 2"));

        // Le carnet.
        pa.ouvrirCarnet();
        idle(300);
        assertTrue(contient(pa, "Carnet de voyage"));
        assertTrue(pa.retour());
        ac.pause().stop().destroy();
    }

    @Test
    public void miseDeCoteEnDeuxGestes() {
        ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class).setup().visible();
        Principale a = ac.get();
        a.aller(Principale.AVENTURE, false);
        idle(200);
        PageAventure pa = (PageAventure) a.page(Principale.AVENTURE);
        toucher(pa, "Commencer");
        Lecture l = pa.lecture();
        l.accelerer();
        idle(500);
        toucher(l, "Plus : carnet, mettre de côté");
        toucher(l, "Mettre l'aventure de côté…");
        assertTrue(contient(l, "Rien de ce qui est acquis ne se perd"));
        toucher(l, "Mettre de côté");
        idle(500);
        assertEquals(Campagnes.Phase.Abandon, etat().phase);
        assertFalse(pa.lectureOuverte());
        assertTrue(textes(pa).toString(), contient(pa, "Reprendre"));
        toucher(pa, "Reprendre");
        assertTrue(pa.lectureOuverte());
        assertTrue(etat().reprise);
        ac.pause().stop().destroy();
    }

    @Test
    public void notificationOuvreLaLecture() {
        assertNull(CampagnesTel.demarrer(ctx, "prologue", false));
        Intent i = new Intent(ctx, Principale.class).putExtra(Principale.EXTRA_ONGLET, Principale.AVENTURE).putExtra(Principale.EXTRA_LECTURE, true);
        ActivityController<Principale> ac = Robolectric.buildActivity(Principale.class, i).setup().visible();
        idle(300);
        PageAventure pa = (PageAventure) ac.get().page(Principale.AVENTURE);
        assertTrue(pa.lectureOuverte());
        ac.pause().stop().destroy();
    }
}
