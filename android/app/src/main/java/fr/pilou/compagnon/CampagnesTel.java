package fr.pilou.compagnon;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * Campagnes sur le téléphone (moteur : Campagnes.java, contrat : docs/CAMPAGNES.md) : le carnet gardé dans les
 * préférences, les décisions, et la synchronisation avec les PC du groupe par le relais (sujet des campagnes, message
 * dédié et chiffré). Pas d'interface ici : c'est ce que l'interface appellera.
 *
 * <pre>
 *   CampagnesTel.etat(c)              l'état courant, à l'heure qu'il est (null : aucune partie) ; etat.fin = heure de fin de
 *                                     l'attente → notification locale à programmer ; etat.pendant, etat.tenue : Pilou occupé
 *   CampagnesTel.carnet(c)            le carnet : fil des messages (carnet.fil, carnet.nonLus()), historique
 *   CampagnesTel.lu(c)                tout le fil est lu
 *   CampagnesTel.demarrer(c, id, neuf), choisir(c, option), continuer(c), epreuve(c, reussie), auDe(c), abandonner(c)
 *                                     null si c'est fait, sinon la raison (à montrer telle quelle)
 *   CampagnesTel.enAttente(c)         { po, xp } gagnés que nul PC n'a encore versés (ils attendent le PC, comme les achats)
 *   CampagnesTel.synchroniser(c)      hors du fil principal : lit le relais, fusionne, publie si le carnet a changé
 * </pre>
 * Le téléphone avance PC éteint : l'histoire ne dépend que du carnet ; seules les récompenses attendent un PC.
 */
public final class CampagnesTel {
    /** Publication : sur changement, sinon toutes les 6 h (le relais garde les messages 12 h). */
    static final long BATTEMENT = 6 * 3600_000L;

    private static String lu = null;
    private static Campagnes.Carnet cache;

    private CampagnesTel() {
    }

    private static SharedPreferences p(Context c) {
        return Prefs.de(c);
    }

    /** Le carnet du téléphone (préférence « campagnes »). */
    public static synchronized Campagnes.Carnet carnet(Context c) {
        String json = p(c).getString("campagnes", "");
        if (cache == null || !json.equals(lu)) {
            cache = json.isEmpty() ? new Campagnes.Carnet() : Campagnes.relire(json);
            lu = json;
        }
        return cache;
    }

    private static String garde = "";

    private static synchronized void garder(Context c, Campagnes.Carnet k) {
        // L'interface demande l'état souvent : on ne réécrit le carnet que s'il a changé.
        String empreinte = Campagnes.signature(k) + "|" + k.fil.size() + "|" + k.lu + "|" + k.payesPc.size();
        if (k == cache && empreinte.equals(garde)) return;
        String json = Campagnes.sauver(k);
        garde = empreinte;
        cache = k;
        if (json.equals(lu)) return;
        p(c).edit().putString("campagnes", json).apply();
        lu = json;
    }

    /** Identifiant de ce téléphone dans le groupe (tiré une fois) : il signe ses décisions. */
    public static synchronized String appareil(Context c) {
        String a = p(c).getString("appareil", "");
        if (a.isEmpty()) {
            a = "tel-" + Gains.nouvelId();
            p(c).edit().putString("appareil", a).apply();
        }
        return a;
    }

    /** L'état courant : le temps passe (attente finie, repos fini), l'historique et le fil se complètent. */
    public static synchronized Campagnes.Etat etat(Context c) {
        Campagnes.Carnet k = carnet(c);
        Campagnes.Etat e = Campagnes.actualiser(k, Campagnes::charger, System.currentTimeMillis());
        garder(c, k);
        return e;
    }

    public static synchronized void lu(Context c) {
        Campagnes.Carnet k = carnet(c);
        Campagnes.marquerLu(k);
        garder(c, k);
    }

    /** { po, xp } acquis que nul PC n'a encore versés. */
    public static synchronized int[] enAttente(Context c) {
        return Campagnes.enAttente(carnet(c), Campagnes::charger);
    }

    /**
     * Pourquoi Pilou ne peut pas répondre à sa campagne maintenant : il est en expédition ou en visite sur le PC
     * (pas de campagne pendant une expédition ou une visite, et inversement). null s'il le peut, ou si le PC se tait.
     */
    public static String refus(Context c) {
        Etat e = Prefs.etat(c);
        if (e.muet(System.currentTimeMillis())) return null;
        if (e.expedition != null && e.expedition.enRoute()) return "Pilou est en expédition : la campagne attendra son retour";
        if (!e.visite.isEmpty()) return "Pilou est en visite chez un ami : la campagne attendra son retour";
        return null;
    }

    private interface Decision {
        String sur(Campagnes.Carnet k, Campagnes.Campagne campagne, long maintenant, String appareil);
    }

    private static synchronized String decider(Context c, String id, boolean memeOccupe, Decision d) {
        String refus = memeOccupe ? null : refus(c);
        if (refus != null) return refus;
        Campagnes.Carnet k = carnet(c);
        Campagnes.Campagne campagne = id != null ? Campagnes.charger(id) : k.courante == null ? null : Campagnes.charger(k.courante.campagne);
        if (campagne == null) return id == null ? "aucune partie en cours" : "campagne inconnue";
        String r = d.sur(k, campagne, System.currentTimeMillis(), appareil(c));
        if (r == null) {
            garder(c, k);
            Context app = c.getApplicationContext();
            new Thread(() -> synchroniser(app), "pilou-campagnes").start(); // les PC du groupe l'apprennent sans attendre
        }
        return r;
    }

    /** Démarre la campagne, ou la reprend à son dernier check-point (neuf : depuis le début quand même). */
    public static String demarrer(Context c, String id, boolean neuf) {
        int niveau = Gains.niveau(c, Prefs.etat(c));
        return decider(c, id, false, (k, campagne, t, a) -> Campagnes.demarrer(k, campagne, niveau, t, a, Campagnes::charger, null, neuf));
    }

    public static String choisir(Context c, String option) {
        return decider(c, null, false, (k, campagne, t, a) -> Campagnes.choisir(k, campagne, t, a, option));
    }

    /** « Vas-y » : Pilou part (phase Depart). */
    public static String continuer(Context c) {
        return decider(c, null, false, (k, campagne, t, a) -> Campagnes.continuer(k, campagne, t, a));
    }

    /** Résultat d'un mini-jeu (phase Epreuve). */
    public static String epreuve(Context c, boolean reussie) {
        return decider(c, null, false, (k, campagne, t, a) -> Campagnes.epreuve(k, campagne, t, a, reussie));
    }

    /** L'appareil ne sait pas jouer ce jeu : le tirage « des » le remplace. */
    public static String auDe(Context c) {
        return decider(c, null, false, (k, campagne, t, a) -> Campagnes.epreuveAuDe(k, campagne, t, a));
    }

    /** Abandonner reste possible quand Pilou est occupé ailleurs. */
    public static String abandonner(Context c) {
        return decider(c, null, true, (k, campagne, t, a) -> Campagnes.abandonner(k, campagne, t, a));
    }

    // ---- Avec le groupe : sujet des campagnes du relais (lecture par sondage, publication sur changement)

    private static String lire(String adresse) throws Exception {
        HttpURLConnection h = (HttpURLConnection) new URL(adresse).openConnection();
        h.setConnectTimeout(15_000);
        h.setReadTimeout(15_000);
        h.setRequestProperty("User-Agent", "pilou-android");
        try (BufferedReader r = new BufferedReader(new InputStreamReader(h.getInputStream(), StandardCharsets.UTF_8))) {
            StringBuilder b = new StringBuilder();
            String ligne;
            while ((ligne = r.readLine()) != null) b.append(ligne).append('\n');
            return b.toString();
        } finally {
            h.disconnect();
        }
    }

    private static boolean poster(String adresse, String corps) throws Exception {
        HttpURLConnection h = (HttpURLConnection) new URL(adresse).openConnection();
        h.setRequestMethod("POST");
        h.setDoOutput(true);
        h.setConnectTimeout(15_000);
        h.setReadTimeout(15_000);
        h.setRequestProperty("User-Agent", "pilou-android");
        try (OutputStream o = h.getOutputStream()) {
            o.write(corps.getBytes(StandardCharsets.UTF_8));
        }
        boolean ok = h.getResponseCode() / 100 == 2;
        h.disconnect();
        return ok;
    }

    /**
     * Lit ce que les autres appareils ont publié depuis la dernière fois, le fusionne (idempotent), puis publie le carnet
     * s'il a changé (ou toutes les 6 h). Hors du fil principal ; hors ligne, rien ne se perd : on réessaiera.
     */
    public static void synchroniser(Context c) {
        String code = Prefs.code(c);
        if (!Chiffre.valide(code)) return;
        String base;
        try {
            base = Prefs.relais(c).replaceAll("/+$", "") + "/" + Campagnes.sujet(code);
        } catch (Exception e) {
            return;
        }
        String moi = appareil(c);
        try {
            String depuis = p(c).getString("campDernierId", "");
            String texte = lire(base + "/json?poll=1&since=" + (depuis.isEmpty() ? "12h" : depuis));
            String dernier = depuis;
            synchronized (CampagnesTel.class) {
                Campagnes.Carnet k = carnet(c);
                for (String ligne : texte.split("\n")) {
                    if (ligne.isEmpty()) continue;
                    try {
                        JSONObject ev = new JSONObject(ligne);
                        if (!"message".equals(ev.optString("event"))) continue;
                        if (!ev.optString("id").isEmpty()) dernier = ev.optString("id");
                        Campagnes.recevoir(k, Chiffre.dechiffrer(code, ev.optString("message")), moi, Campagnes::charger, System.currentTimeMillis());
                    } catch (Exception illisible) {
                        // pas pour nous (autre code, message altéré) : ignoré
                    }
                }
                Campagnes.actualiser(k, Campagnes::charger, System.currentTimeMillis());
                garder(c, k);
            }
            if (!dernier.equals(depuis)) p(c).edit().putString("campDernierId", dernier).apply();
        } catch (Exception horsLigne) {
            // relais injoignable : on publiera quand même si possible, on relira plus tard
        }
        List<String> messages;
        String signature;
        synchronized (CampagnesTel.class) {
            Campagnes.Carnet k = carnet(c);
            signature = Campagnes.signature(k);
            messages = Campagnes.messages(k, moi, "tel");
        }
        long maintenant = System.currentTimeMillis();
        boolean change = !signature.equals(p(c).getString("campEnvoyee", ""));
        if (messages.isEmpty() || (!change && maintenant - p(c).getLong("campEnvoi", 0) < BATTEMENT)) return;
        try {
            for (String m : messages) if (!poster(base, Chiffre.chiffrer(code, m))) return;
            p(c).edit().putString("campEnvoyee", signature).putLong("campEnvoi", maintenant).apply();
        } catch (Exception horsLigne) {
            // on réessaiera au prochain passage
        }
    }

    /** Une ligne pour le diagnostic (Réglages) : campagnes embarquées, partie en cours, récompenses en attente du PC. */
    public static String diagnostic(Context c) {
        try {
            List<String> ids = Campagnes.disponibles();
            StringBuilder b = new StringBuilder(ids.size() + " embarquée" + (ids.size() > 1 ? "s" : ""));
            for (String id : ids) {
                Campagnes.Campagne x = Campagnes.charger(id);
                b.append(" · ").append(id).append(x == null ? " (illisible)" : " (" + x.noeuds.size() + " nœuds)");
            }
            Campagnes.Carnet k = carnet(c);
            Campagnes.Etat e = etat(c);
            b.append(" · en cours : ").append(k.courante == null ? "aucune" : k.courante.campagne + (e == null ? " (inconnue ici)" : ", " + e.phase + " au nœud " + e.noeud));
            int[] attente = enAttente(c);
            if (attente[0] > 0 || attente[1] > 0) b.append(" · en attente du PC : ").append(attente[0]).append(" po, ").append(attente[1]).append(" xp");
            return b.toString();
        } catch (RuntimeException e) {
            return "erreur (" + e + ")";
        }
    }
}
