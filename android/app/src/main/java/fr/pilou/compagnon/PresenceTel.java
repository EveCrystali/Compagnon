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
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;
import java.util.function.Consumer;

/**
 * La présence de Pilou au quotidien sur le téléphone (docs/PRESENCE.md) : l'état (préférence « presence », même format
 * que presence.txt sur le PC), le mot du jour (en tête de l'Accueil, dans le widget et la bulle, et le soir en
 * notification discrète : MotDuSoir), les faits du jour pour le journal, la complicité, le prénom, et la synchronisation
 * avec le groupe (sujet à part du relais, chiffré). Le moteur est Presence.java, copie exacte de celui du PC.
 * Rien de tout cela ne doit faire tomber l'app : chaque entrée publique est protégée.
 */
public final class PresenceTel {
    private static Presence.Etat cache;
    private static String lu;
    private static long ensembleMs;

    private PresenceTel() {
    }

    private static SharedPreferences p(Context c) {
        return Prefs.de(c);
    }

    /** L'état de la présence de ce téléphone (lu une fois, puis gardé en mémoire). */
    public static synchronized Presence.Etat etat(Context c) {
        String texte = p(c).getString("presence", "");
        if (cache == null || !texte.equals(lu)) {
            try {
                cache = Presence.Etat.lire(texte);
            } catch (RuntimeException e) {
                Journal.noter("présence : lecture", e);
                cache = new Presence.Etat();
            }
            lu = texte;
        }
        cache.moi.id = CampagnesTel.appareil(c);
        cache.moi.sorte = "tel";
        return cache;
    }

    public static synchronized void garder(Context c, Presence.Etat e) {
        try {
            String texte = e.texte();
            if (texte.equals(lu)) return;
            p(c).edit().putString("presence", texte).apply();
            lu = texte;
            cache = e;
        } catch (RuntimeException x) {
            Journal.noter("présence : écriture", x);
        }
    }

    /** Un fait du jour et son compteur de complicité (« caresses », « soins », « jeux », ou "" : juste un jour ensemble). */
    public static synchronized void vecu(Context c, Consumer<Presence.FaitsDuJour> modif, String compteur) {
        try {
            Presence.Etat e = etat(c);
            LocalDateTime maintenant = LocalDateTime.now();
            if (e.journalActif && modif != null) modif.accept(e.aujourdhui(Presence.jourTexte(maintenant)));
            if (compteur != null && !compteur.isEmpty()) e.ajouter(compteur, 1, maintenant);
            else e.marquer(Presence.jour(maintenant));
            garder(c, e);
        } catch (RuntimeException x) {
            Journal.noter("présence : fait", x);
        }
    }

    public static void prise(Context c, Butin.Prise x) {
        if (x == null) return;
        String nom = Presence.avecArticle(x.id, x.nom);
        vecu(c, f -> {
            f.pc++;
            if (f.px.isEmpty() || x.rarete > f.pq || (x.rarete == f.pq && nom.compareTo(f.px) < 0)) {
                f.px = nom;
                f.pq = x.rarete;
            }
        }, "jeux");
    }

    public static void plat(Context c, Butin.Plat pl) {
        if (pl == null) return;
        vecu(c, f -> {
            f.cu++;
            if (!pl.rate && !pl.inventee && f.cx.isEmpty()) f.cx = Presence.avecArticle(pl.id, pl.nom);
        }, "jeux");
    }

    /** L'app est ouverte (chaque seconde, Principale.tic) : le temps passé ensemble, compté à la minute. */
    public static synchronized void seconde(Context c, long ms) {
        ensembleMs += Math.max(0, Math.min(ms, 5000));
        if (ensembleMs < 60_000) return;
        int m = (int) (ensembleMs / 60_000);
        ensembleMs -= m * 60_000L;
        try {
            Presence.Etat e = etat(c);
            LocalDateTime maintenant = LocalDateTime.now();
            e.ajouter("minutes", m, maintenant);
            if (e.journalActif) {
                Presence.FaitsDuJour f = e.aujourdhui(Presence.jourTexte(maintenant));
                f.mn += m;
                if (Presence.totLeMatin(maintenant.getHour(), maintenant.getMinute())) f.ma = 1;
                String meteo = meteo(c);
                if (!meteo.isEmpty()) {
                    Presence.FaitsDuJour x = new Presence.FaitsDuJour();
                    x.me = meteo;
                    f.me = Presence.FaitsDuJour.fusion(f, x).me;
                }
            }
            garder(c, e);
        } catch (RuntimeException x) {
            Journal.noter("présence : minutes", x);
        }
    }

    private static String meteo(Context c) {
        Meteo m = Prefs.etat(c).meteo(System.currentTimeMillis());
        return m == null || m.etat == null ? "" : m.etat;
    }

    // ---- Le mot du jour

    /** Pilou me parle : normal, peu, jamais. */
    public static String parle(Context c) {
        return etat(c).parle;
    }

    /** Le mot du jour ("" : Pilou se tait). Choisi une fois par jour, puis le même partout (accueil, widget, bulle, soir). */
    public static synchronized String motDuJour(Context c) {
        try {
            Presence.Etat e = etat(c);
            if (e.parle.equals("jamais")) return "";
            LocalDateTime maintenant = LocalDateTime.now();
            String jour = Presence.jourTexte(maintenant);
            if (jour.equals(e.motJour)) return e.motTexte;
            // Les traits de personnalité (Traits.java) : relus une fois par jour, avant de choisir le mot.
            boolean neuf = Traits.decouvrir(e);
            Presence.Contexte x = contexte(c, e, maintenant);
            Presence.Choix ch = Presence.mot(x, Presence.banque(), e.dits, jour + "|" + e.moi.id + "|tel");
            e.motJour = jour;
            e.motTexte = ch == null ? "" : ch.texte;
            e.motNotifie = "";
            if (ch != null) {
                Presence.retenir(e.dits, ch.ligne.id, Presence.jour(maintenant));
                if (ch.famille.startsWith("date-")) e.moi.fetes.add(x.dateAFeter);
                if (ch.famille.startsWith("palier-")) e.moi.palierAnnonce = Math.max(e.moi.palierAnnonce, x.palier);
                // Un trait n'est annoncé qu'une fois dans le groupe.
                if (ch.famille.startsWith("annonce-")) {
                    Traits.Trait t = Traits.trouver(ch.famille.substring("annonce-".length()));
                    if (t != null) e.moi.traitsDits |= t.bit();
                    neuf = true;
                }
            }
            garder(c, e);
            if (neuf) p(c).edit().putBoolean("presenceUrgent", true).apply();
            return e.motTexte;
        } catch (RuntimeException x) {
            Journal.noter("présence : mot du jour", x);
            return "";
        }
    }

    static Presence.Contexte contexte(Context c, Presence.Etat e, LocalDateTime maintenant) {
        Presence.Totaux t = e.totaux();
        int auj = Presence.jour(maintenant);
        String jour = Presence.jourTexte(maintenant);
        Etat pc = Prefs.etat(c);
        Presence.Contexte x = new Presence.Contexte(maintenant, Presence.Moment.Telephone);
        x.palier = t.palier;
        int n = Gains.niveau(c, pc);
        x.stade = pc.stade > 0 ? pc.stade : Acces.stade(n);
        String v = pc.formes.get(x.stade);
        x.variante = v == null ? "" : v;
        x.prenom = t.prenom;
        x.meteo = meteo(c);
        Presence.FaitsDuJour hier = e.faitsDu(Presence.jourTexte(auj - 1)), ajd = e.faitsDu(jour);
        x.metier = !ajd.mo.isEmpty() ? ajd.mo : hier.mo;
        x.niveau = ajd.nv;
        x.prise = hier.px;
        x.plat = hier.cx;
        List<String> objets = new ArrayList<>();
        for (Map.Entry<String, String> en : Gains.porte(c, pc).entrySet()) {
            Boutique.Article a = Boutique.trouver(en.getValue());
            if (a != null && Boutique.surPilou(en.getKey())) objets.add(a.nom);
        }
        java.util.Collections.sort(objets);
        x.objet = objets.isEmpty() ? "" : objets.get(Presence.tirer(jour + "|objet", objets.size()));
        TreeSet<String> finies = new TreeSet<>(e.moi.finies);
        for (Presence.Appareil a : e.autres.values()) finies.addAll(a.finies);
        List<String> f = new ArrayList<>(finies);
        x.souvenir = f.isEmpty() || t.palier < 1 ? "" : f.get(Presence.tirer(jour + "|souvenir", f.size()));
        x.dateAFeter = Presence.dateAFeter(t, auj);
        x.palierNouveau = t.palier > t.palierAnnonce ? t.palier : -1;
        x.joursEnsemble = t.jours;
        x.annees = x.dateAFeter.startsWith("a") ? Presence.entier(x.dateAFeter.substring(1), 0, 99) : 0;
        // Traits : un seul à annoncer ; les répliques ne viennent que des dominants déjà annoncés.
        Traits.Trait nouveau = Traits.aAnnoncer(Traits.tous(), t.traits, t.traitsDits);
        x.traitNouveau = nouveau == null ? "" : nouveau.id;
        StringBuilder dominants = new StringBuilder();
        for (Traits.Trait d : Traits.dominants(Traits.tous(), t.traits & t.traitsDits, Traits.journal(e), auj)) {
            if (dominants.length() > 0) dominants.append(',');
            dominants.append(d.id);
        }
        x.traits = dominants.toString();
        return x;
    }

    /** Les campagnes finies (carnet partagé) comptent pour la complicité. */
    static void campagnes(Context c) {
        try {
            Campagnes.Carnet k = CampagnesTel.carnet(c);
            Presence.Etat e = etat(c);
            boolean change = false;
            for (Map.Entry<String, Campagnes.Bilan> en : k.historique.entrySet())
                if (en.getValue().finie > 0) change |= e.moi.finies.add(Presence.propre(en.getKey()));
            if (change) garder(c, e);
        } catch (RuntimeException x) {
            Journal.noter("présence : campagnes", x);
        }
    }

    // ---- Les traits de personnalité (Traits.java, docs/TRAITS.md)

    /** Les trois traits dominants de Pilou en ce moment (au plus) : pour la carte « Pilou et moi » et les saynètes. */
    public static List<Traits.Trait> traitsDominants(Context c) {
        try {
            return Traits.dominants(etat(c), Presence.jour(LocalDateTime.now()));
        } catch (RuntimeException x) {
            Journal.noter("présence : traits", x);
            return new ArrayList<>();
        }
    }

    // ---- Le prénom

    /** Faut-il le demander (une seule fois, quand on se connaît un peu) ? */
    public static boolean demanderPrenom(Context c) {
        try {
            Presence.Totaux t = etat(c).totaux();
            return !t.prenomDemande && t.prenom.isEmpty() && t.palier >= 1 && !etat(c).parle.equals("jamais");
        } catch (RuntimeException x) {
            return false;
        }
    }

    public static synchronized void prenom(Context c, String prenom, boolean refus) {
        Presence.Etat e = etat(c);
        if (refus) e.moi.prenomDemande = true;
        else e.choisirPrenom(prenom, System.currentTimeMillis());
        e.motJour = ""; // le mot du jour peut maintenant le dire (avec parcimonie)
        garder(c, e);
        p(c).edit().putBoolean("presenceUrgent", true).apply();
        if (Chiffre.valide(Prefs.code(c)) && !"robolectric".equals(android.os.Build.FINGERPRINT))
            new Thread(() -> synchroniser(c.getApplicationContext()), "pilou-presence").start();
    }

    public static String prenom(Context c) {
        try {
            return etat(c).prenom();
        } catch (RuntimeException x) {
            return "";
        }
    }

    // ---- Avec le groupe (sujet à part du relais ; jamais vers les amis)

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

    /** Lit le groupe, fusionne (idempotent), puis publie si quelque chose a changé (au plus tous les quarts d'heure). */
    public static void synchroniser(Context c) {
        String code = Prefs.code(c);
        if (!Chiffre.valide(code)) return;
        if ("robolectric".equals(android.os.Build.FINGERPRINT)) return; // tests : jamais de relais réel
        String base;
        try {
            base = Prefs.relais(c).replaceAll("/+$", "") + "/" + Presence.sujet(code);
        } catch (Exception e) {
            return;
        }
        campagnes(c);
        int auj = Presence.jour(LocalDateTime.now());
        try {
            String depuis = p(c).getString("presenceDernierId", "");
            String texte = lire(base + "/json?poll=1&since=" + (depuis.isEmpty() ? "12h" : depuis));
            String dernier = depuis;
            synchronized (PresenceTel.class) {
                Presence.Etat e = etat(c);
                boolean change = false;
                for (String ligne : texte.split("\n")) {
                    if (ligne.isEmpty()) continue;
                    try {
                        JSONObject ev = new JSONObject(ligne);
                        if (!"message".equals(ev.optString("event"))) continue;
                        if (!ev.optString("id").isEmpty()) dernier = ev.optString("id");
                        Presence.Appareil a = Presence.Appareil.lireMessage(Chiffre.dechiffrer(code, ev.optString("message")));
                        if (a != null) change |= e.recevoir(a, auj);
                    } catch (Exception illisible) {
                        // pas pour nous : ignoré
                    }
                }
                e.compacter(auj);
                // Les faits des autres appareils peuvent faire naître un trait ici aussi.
                if (Traits.decouvrir(e)) {
                    change = true;
                    p(c).edit().putBoolean("presenceUrgent", true).apply();
                }
                if (change) garder(c, e);
            }
            if (!dernier.equals(depuis)) p(c).edit().putString("presenceDernierId", dernier).apply();
        } catch (Exception horsLigne) {
            // relais injoignable : on relira plus tard
        }
        String message;
        synchronized (PresenceTel.class) {
            message = etat(c).message(auj);
        }
        long maintenant = System.currentTimeMillis();
        long envoi = p(c).getLong("presenceEnvoi", 0);
        boolean urgent = p(c).getBoolean("presenceUrgent", false);
        boolean battement = maintenant - envoi >= 6 * 3600_000L;
        if (!battement && (message.equals(p(c).getString("presenceEnvoyee", "")) || (!urgent && maintenant - envoi < 15 * 60_000L))) return;
        try {
            if (poster(base, Chiffre.chiffrer(code, message)))
                p(c).edit().putString("presenceEnvoyee", message).putLong("presenceEnvoi", maintenant).putBoolean("presenceUrgent", false).apply();
        } catch (Exception horsLigne) {
            // on réessaiera
        }
    }
}
