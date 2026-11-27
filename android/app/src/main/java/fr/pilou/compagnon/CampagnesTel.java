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

    /** L'horloge des campagnes (ms Unix) : les tests l'avancent à la main pour traverser une attente. */
    static volatile java.util.function.LongSupplier horloge = System::currentTimeMillis;

    private CampagnesTel() {
    }

    public static long maintenant() {
        return horloge.getAsLong();
    }

    /** Les campagnes embarquées sont-elles lues ? (la première lecture se fait hors du fil d'interface : precharger) */
    private static volatile boolean pretes;

    public static boolean pretes() {
        return pretes;
    }

    /** Lit toutes les campagnes embarquées, une fois ; puis fait (sur le fil d'interface) ce qu'on lui donne. */
    public static void precharger(Runnable ensuite) {
        if (pretes) {
            if (ensuite != null) ensuite.run();
            return;
        }
        android.os.Handler h = new android.os.Handler(android.os.Looper.getMainLooper());
        new Thread(() -> {
            try {
                for (String id : Campagnes.disponibles()) Campagnes.charger(id);
            } catch (RuntimeException e) {
                Journal.noter("campagnes", e);
            }
            pretes = true;
            if (ensuite != null) h.post(ensuite);
        }, "pilou-campagnes-lecture").start();
    }

    /** Pour les tests : lit tout de suite, sur ce fil. */
    static void prechargerMaintenant() {
        for (String id : Campagnes.disponibles()) Campagnes.charger(id);
        pretes = true;
    }

    /** Pour les tests : la graine des prochaines parties (null : tirée au hasard). */
    static volatile String graineEssai;

    /** Les campagnes à proposer, dans l'ordre du joueur : le prologue d'abord, puis par niveau requis. */
    public static List<Campagnes.Campagne> catalogue() {
        List<Campagnes.Campagne> l = new java.util.ArrayList<>();
        for (String id : Campagnes.disponibles()) {
            Campagnes.Campagne x = Campagnes.charger(id);
            if (x != null) l.add(x);
        }
        java.util.Collections.sort(l, (a, b) -> a.id.equals("prologue") ? -1 : b.id.equals("prologue") ? 1
                : a.niveau != b.niveau ? Integer.compare(a.niveau, b.niveau) : a.titre.compareTo(b.titre));
        return l;
    }

    /** Nombre de fins d'une campagne. */
    public static int nombreFins(Campagnes.Campagne c) {
        int n = 0;
        for (Campagnes.Noeud x : c.noeuds.values()) if (x.type.equals("fin")) n++;
        return n;
    }

    /** Les nœuds de fin, dans l'ordre des chapitres puis des identifiants (pour la grille des fins « ? ? ? »). */
    public static List<Campagnes.Noeud> finsDe(Campagnes.Campagne c) {
        List<Campagnes.Noeud> l = new java.util.ArrayList<>();
        for (Campagnes.Noeud x : c.noeuds.values()) if (x.type.equals("fin")) l.add(x);
        java.util.Collections.sort(l, (a, b) -> {
            int ia = rangChapitre(c, a.chapitre), ib = rangChapitre(c, b.chapitre);
            return ia != ib ? Integer.compare(ia, ib) : a.id.compareTo(b.id);
        });
        return l;
    }

    static int rangChapitre(Campagnes.Campagne c, String chapitre) {
        for (int i = 0; i < c.chapitres.size(); i++) if (c.chapitres.get(i).id.equals(chapitre)) return i;
        return -1;
    }

    /** La partie en cours (ou null), telle que le carnet la garde. */
    public static synchronized Campagnes.Partie courante(Context c) {
        return carnet(c).courante;
    }

    /** Le lieu où Pilou reprendra après un repos ou une partie mise de côté : celui du dernier check-point. */
    public static synchronized String lieuReprise(Campagnes.Campagne c, Campagnes.Partie p, Campagnes.Etat e) {
        Campagnes.Instantane x = null;
        if (e != null)
            for (Campagnes.Point pt : e.points) if (pt.naturel && !pt.base.abandonnee) x = pt.base.ici;
        if (x == null && p != null) x = p.cp != null ? p.cp : p.ici;
        if (x == null) return "";
        String noeud = c.decode('n', x.n);
        Campagnes.Noeud n = noeud == null ? null : c.noeud(noeud);
        if (n != null && !n.lieu.isEmpty()) return n.lieu;
        String de = x.lieu.isEmpty() ? null : c.decode('n', x.lieu);
        Campagnes.Noeud l = de == null ? null : c.noeud(de);
        return l == null ? "" : l.lieu;
    }

    /** Le lieu de reprise d'une partie mise de côté (son « ici » est le check-point). */
    public static String lieuReprise(Campagnes.Campagne c, Campagnes.Partie p) {
        return lieuReprise(c, p, null);
    }

    /** Le tirage des dés de l'épreuve en cours (0 à 99) : celui que fera auDe ; réussi s'il est sous e.chance. */
    public static synchronized int tirageDe(Context c, Campagnes.Etat e) {
        Campagnes.Partie p = carnet(c).courante;
        if (p == null || e == null) return 0;
        return Campagnes.tirage(p.graine, e.tirages).suivant(100);
    }

    /**
     * Le fil de la campagne courante : ses messages (et ceux des parties qu'elle reprend, à la suite), les plus anciens
     * d'abord. Le carnet ne dit pas à quelle campagne appartient une partie passée : le téléphone le note au passage.
     */
    public static synchronized List<Campagnes.Message> fil(Context c, String campagne) {
        Campagnes.Carnet k = carnet(c);
        noterParties(c, k);
        java.util.Set<Integer> parties = new java.util.HashSet<>();
        String chaine = p(c).getString("campParties", "");
        // « p:campagne:r » ; r = 1 si la partie en reprend une autre (même fil), 0 si elle repart du début.
        java.util.List<String[]> l = new java.util.ArrayList<>();
        for (String s : chaine.split(";")) {
            String[] x = s.split(":");
            if (x.length == 3) l.add(x);
        }
        java.util.Collections.sort(l, (a, b) -> Integer.compare(entier(b[0]), entier(a[0])));
        for (String[] x : l) {
            if (!x[1].equals(campagne)) continue;
            parties.add(entier(x[0]));
            if (x[2].equals("0")) break;
        }
        List<Campagnes.Message> r = new java.util.ArrayList<>();
        for (Campagnes.Message m : k.fil) if (parties.contains(m.p)) r.add(m);
        return r;
    }

    private static int entier(String s) {
        try {
            return Integer.parseInt(s);
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    private static void noterParties(Context c, Campagnes.Carnet k) {
        Campagnes.Partie q = k.courante;
        if (q == null) return;
        String chaine = p(c).getString("campParties", "");
        String cle = q.p + ":";
        if (chaine.startsWith(cle) || chaine.contains(";" + cle)) return;
        String neuve = q.p + ":" + q.campagne + ":" + (q.reprise ? 1 : 0);
        // Les 40 dernières parties suffisent (le fil n'en garde pas plus).
        String[] avant = chaine.isEmpty() ? new String[0] : chaine.split(";");
        StringBuilder b = new StringBuilder(neuve);
        for (int i = 0; i < Math.min(39, avant.length); i++) b.append(';').append(avant[i]);
        p(c).edit().putString("campParties", b.toString()).apply();
    }

    /** Messages de Pilou pas encore lus. */
    public static synchronized int nonLus(Context c) {
        return carnet(c).nonLus();
    }

    /** Ce message est-il nouveau (pas encore lu) ? */
    public static synchronized boolean nonLu(Context c, Campagnes.Message m) {
        return Campagnes.nonLu(carnet(c), m);
    }

    /** Pilou attend le joueur (il a écrit et rien n'est lu, ou il a besoin d'une décision) : le « ! » de l'onglet et de la bulle. */
    public static boolean attendJoueur(Context c, Campagnes.Etat e) {
        if (e == null) return false;
        boolean geste = e.phase == Campagnes.Phase.Choix || e.phase == Campagnes.Phase.Depart || e.phase == Campagnes.Phase.Epreuve;
        return geste || (e.phase == Campagnes.Phase.Fin && nonLus(c) > 0);
    }

    /** « Pilou longe la falaise · retour vers 15 h 40 », en plus court pour la bulle : « en route · retour 15 h 40 ». */
    public static String heure(long ms) {
        java.util.Calendar k = java.util.Calendar.getInstance();
        k.setTimeInMillis(ms);
        return k.get(java.util.Calendar.HOUR_OF_DAY) + " h " + String.format(java.util.Locale.ROOT, "%02d", k.get(java.util.Calendar.MINUTE));
    }

    /** « 12 min », « 1 h 05 », « moins d'une minute » : ce qu'il reste avant ms. */
    public static String reste(long ms) {
        long s = Math.max(0, ms) / 1000;
        if (s < 60) return "moins d'une minute";
        long m = (s + 59) / 60;
        if (m < 60) return m + " min";
        return (m / 60) + " h " + String.format(java.util.Locale.ROOT, "%02d", m % 60);
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
        Campagnes.Etat e = Campagnes.actualiser(k, Campagnes::charger, maintenant());
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
        String r = d.sur(k, campagne, maintenant(), appareil(c));
        if (r == null) {
            garder(c, k);
            Context app = c.getApplicationContext();
            Retour.programmer(app); // la notification de retour suit l'attente qui commence (ou s'annule)
            new Thread(() -> synchroniser(app), "pilou-campagnes").start(); // les PC du groupe l'apprennent sans attendre
        }
        return r;
    }

    /** Démarre la campagne, ou la reprend à son dernier check-point (neuf : depuis le début quand même). */
    public static String demarrer(Context c, String id, boolean neuf) {
        int niveau = Gains.niveau(c, Prefs.etat(c));
        return decider(c, id, false, (k, campagne, t, a) -> Campagnes.demarrer(k, campagne, niveau, t, a, Campagnes::charger, graineEssai, neuf));

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
        if ("robolectric".equals(android.os.Build.FINGERPRINT)) return; // tests : jamais de relais réel

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
                        Campagnes.recevoir(k, Chiffre.dechiffrer(code, ev.optString("message")), moi, Campagnes::charger, maintenant());
                    } catch (Exception illisible) {
                        // pas pour nous (autre code, message altéré) : ignoré
                    }
                }
                Campagnes.actualiser(k, Campagnes::charger, maintenant());
                garder(c, k);
            }
            Retour.programmer(c); // un autre appareil a peut-être fait partir Pilou
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
        long maintenant = maintenant();
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
