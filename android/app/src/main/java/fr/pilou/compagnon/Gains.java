package fr.pilou.compagnon;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/**
 * Ce que Pilou gagne sur le téléphone (atelier : pêche, cuisine, jeux, caresses). L'XP vit sur le PC :
 * chaque gain part, chiffré, sur le sujet retour ; le PC le crédite une fois (par son identifiant) et le
 * cite dans « recus » ; le téléphone le retire alors de sa file. Hors ligne, la file attend.
 */
public final class Gains {
    private static final long RENVOI = 6 * 3600_000L, OUBLI = 7 * 24 * 3600_000L;

    private Gains() {
    }

    private static SharedPreferences p(Context c) {
        return Prefs.de(c);
    }

    private static JSONArray file(Context c) {
        try {
            return new JSONArray(p(c).getString("gains", "[]"));
        } catch (JSONException e) {
            return new JSONArray();
        }
    }

    private static JSONObject objet(Context c, String cle) {
        try {
            return new JSONObject(p(c).getString(cle, "{}"));
        } catch (JSONException e) {
            return new JSONObject();
        }
    }

    static String nouvelId() {
        StringBuilder b = new StringBuilder();
        java.security.SecureRandom r = new java.security.SecureRandom();
        for (int i = 0; i < 12; i++) b.append("0123456789abcdef".charAt(r.nextInt(16)));
        return b.toString();
    }

    interface Modif {
        void sur(JSONObject g) throws JSONException;
    }

    // Un gain s'ajoute au dernier pas encore envoyé (moins de messages), sinon ouvre une nouvelle entrée.
    private static synchronized void modifier(Context c, Modif m) {
        try {
            JSONArray f = file(c);
            JSONObject g = f.length() > 0 && f.getJSONObject(f.length() - 1).optLong("envoye", 0) == 0 ? f.getJSONObject(f.length() - 1) : null;
            if (g == null) {
                g = new JSONObject().put("v", 1).put("id", nouvelId()).put("xp", 0).put("prises", new JSONObject())
                        .put("plats", new JSONArray()).put("caresses", 0).put("cree", System.currentTimeMillis()).put("envoye", 0);
                f.put(g);
            }
            m.sur(g);
            g.put("t", System.currentTimeMillis());
            p(c).edit().putString("gains", f.toString()).apply();
        } catch (JSONException e) {
            // file illisible : le gain est perdu, rien ne casse
        }
    }

    private static synchronized void ajouter(Context c, int xp, String prise, String plat, int caresses) {
        try {
            JSONArray f = file(c);
            JSONObject g = f.length() > 0 && f.getJSONObject(f.length() - 1).optLong("envoye", 0) == 0 ? f.getJSONObject(f.length() - 1) : null;
            if (g == null) {
                g = new JSONObject().put("v", 1).put("id", nouvelId()).put("xp", 0).put("prises", new JSONObject())
                        .put("plats", new JSONArray()).put("caresses", 0).put("cree", System.currentTimeMillis()).put("envoye", 0);
                f.put(g);
            }
            g.put("t", System.currentTimeMillis());
            g.put("xp", g.optInt("xp") + xp);
            g.put("caresses", g.optInt("caresses") + caresses);
            if (prise != null) {
                JSONObject pr = g.getJSONObject("prises");
                pr.put(prise, pr.optInt(prise) + 1);
            }
            if (plat != null) g.getJSONArray("plats").put(plat);
            p(c).edit().putString("gains", f.toString()).apply();
        } catch (JSONException e) {
            // file illisible : le gain est perdu, rien ne casse
        }
    }

    // ---- Ce qui arrive dans l'atelier

    /** L'XP d'un jeu du téléphone selon les soins (comme sur le PC) : × 0,6 s'il boude, × 1,2 s'il rayonne. */
    static int ajuste(Context c, int xp) {
        return Soins.bonus(xp, soins(c, Prefs.etat(c), System.currentTimeMillis()));
    }

    /** Une prise : au carnet, au stock si elle se mange, et l'XP (ajustée, renvoyée). */
    public static int prise(Context c, Butin.Prise x, int xpBrute) {
        int xp = ajuste(c, xpBrute);
        JSONObject carnet = objet(c, "carnetLocal");
        JSONObject stock = objet(c, "stock");
        try {
            carnet.put(x.id, carnet.optInt(x.id) + 1);
            if (x.comestible()) stock.put(x.id, stock.optInt(x.id) + 1);
        } catch (JSONException e) {
            return 0;
        }
        p(c).edit().putString("carnetLocal", carnet.toString()).putString("stock", stock.toString()).apply();
        ajouter(c, xp, x.id, null, 0);
        return xp;
    }

    /** Un plat cuisiné : les ingrédients sortent du stock ; renvoie l'XP ajustée. */
    public static int plat(Context c, Butin.Plat pl) {
        JSONObject stock = objet(c, "stock");
        try {
            for (String id : pl.utilises) stock.put(id, Math.max(0, stock.optInt(id) - 1));
            if (!pl.rate) {
                JSONArray plats = new JSONArray(p(c).getString("platsLocal", "[]"));
                boolean deja = false;
                for (int i = 0; i < plats.length(); i++) deja |= plats.optString(i).equals(pl.id);
                if (!deja) plats.put(pl.id);
                p(c).edit().putString("platsLocal", plats.toString()).apply();
            }
        } catch (JSONException e) {
            return 0;
        }
        p(c).edit().putString("stock", stock.toString()).apply();
        int xp = ajuste(c, pl.xp);
        ajouter(c, xp, null, pl.rate ? null : pl.id, 0);
        return xp;
    }

    /** Un petit jeu gagné (atelier) : de l'XP (ajustée, renvoyée), et une partie pour les quêtes. */
    public static int jeu(Context c, int xpBrute) {
        int xp = ajuste(c, xpBrute);
        modifier(c, g -> {
            g.put("xp", g.optInt("xp") + xp);
            g.put("jeux", g.optInt("jeux") + 1);
        });
        return xp;
    }

    /** Une partie de Chasse aux bugs : XP (ajustée), une partie, et le meilleur score (quêtes « atteins N points »). */
    public static void chasse(Context c, int xpBrute, int score) {
        int xp = ajuste(c, xpBrute);
        modifier(c, g -> {
            g.put("xp", g.optInt("xp") + xp);
            g.put("jeux", g.optInt("jeux") + 1);
            g.put("chasse", Math.max(g.optInt("chasse"), score));
        });
    }

    /** Achat demandé à la boutique : le PC vérifie le solde et l'applique (il reste l'arbitre). */
    public static void acheter(Context c, String id) {
        modifier(c, g -> {
            JSONArray a = g.optJSONArray("achats");
            if (a == null) g.put("achats", a = new JSONArray());
            for (int i = 0; i < a.length(); i++) if (id.equals(a.optString(i))) return;
            a.put(id);
        });
    }

    /** Porter (ou retirer, id vide) : montré tout de suite ici, transmis au PC. */
    public static void equiper(Context c, String slot, String id) {
        modifier(c, g -> {
            JSONObject e = g.optJSONObject("equipe");
            if (e == null) g.put("equipe", e = new JSONObject());
            e.put(slot, id);
        });
        JSONObject local = objet(c, "equipeLocal");
        try {
            local.put(slot, new JSONObject().put("id", id).put("t", System.currentTimeMillis()));
        } catch (JSONException ignore) {
            return;
        }
        p(c).edit().putString("equipeLocal", local.toString()).apply();
    }

    /** Achats partis mais pas encore confirmés par le PC (ils ne sont pas encore dans ses objets). */
    public static Set<String> achatsEnAttente(Context c, Etat e) {
        Set<String> s = new TreeSet<>();
        JSONArray f = file(c);
        for (int i = 0; i < f.length(); i++) {
            JSONObject g = f.optJSONObject(i);
            JSONArray a = g == null ? null : g.optJSONArray("achats");
            if (a == null) continue;
            for (int k = 0; k < a.length(); k++) if (!e.objets.contains(a.optString(k))) s.add(a.optString(k));
        }
        return s;
    }

    /** Objet possédé (selon le PC). */
    public static boolean possede(Context c, String id) {
        return Prefs.etat(c).objets.contains(id);
    }

    /** Solde affiché : celui du PC, moins les achats en route. */
    public static int solde(Context c, Etat e) {
        int s = Math.max(0, e.po);
        for (String id : achatsEnAttente(c, e)) {
            Boutique.Article a = Boutique.trouver(id);
            if (a != null) s -= Boutique.prix(a, e.promo);
        }
        return Math.max(0, s);
    }

    /** Ce que Pilou porte : l'état du PC, recouvert par les choix récents du téléphone (moins de 10 min). */
    public static java.util.Map<String, String> porte(Context c, Etat e) {
        java.util.Map<String, String> m = new java.util.TreeMap<>(e.porte);
        JSONObject local = objet(c, "equipeLocal");
        long maintenant = System.currentTimeMillis();
        for (Iterator<String> i = local.keys(); i.hasNext(); ) {
            String slot = i.next();
            JSONObject o = local.optJSONObject(slot);
            if (o == null || maintenant - o.optLong("t") > 10 * 60_000L) continue;
            if (o.optString("id").isEmpty()) m.remove(slot);
            else m.put(slot, o.optString("id"));
        }
        return m;
    }

    public static void caresse(Context c) {
        ajouter(c, 1, null, null, 1);
    }

    /** Un soin fait sur le téléphone (nourrir, laver, calin, soin, vacances) : il part au PC. */
    public static void soin(Context c, String type, String objet) {
        Soins.Action a = new Soins.Action(nouvelId(), type, System.currentTimeMillis(), objet);
        modifier(c, g -> {
            JSONArray s = g.optJSONArray("soins");
            if (s == null) g.put("soins", s = new JSONArray());
            if (s.length() < 40) s.put(Soins.json(a));
        });
        if (!Chiffre.valide(Prefs.code(c)) && p(c).getString("soinsBase", "").isEmpty())
            p(c).edit().putString("soinsBase", String.valueOf(a.t - 1)).apply();
    }

    /** Soins en route vers le PC (pas encore accusés). */
    static java.util.List<Soins.Action> soinsEnAttente(Context c) {
        java.util.List<Soins.Action> l = new java.util.ArrayList<>();
        JSONArray f = file(c);
        for (int i = 0; i < f.length(); i++) {
            JSONObject g = f.optJSONObject(i);
            JSONArray s = g == null ? null : g.optJSONArray("soins");
            if (s == null) continue;
            for (int k = 0; k < s.length(); k++) {
                Soins.Action a = Soins.lireAction(s.optJSONArray(k));
                if (a != null) l.add(a);
            }
        }
        return l;
    }

    /** État des soins ici : celui du PC (ou, sans PC, un Pilou soigné au premier lancement), plus les soins
     *  du téléphone que le PC n'a pas encore pu compter. */
    public static Soins.EtatSoins soins(Context c, Etat e, long maintenant) {
        Soins.EtatSoins base = e.soins;
        if (base == null) {
            double debut;
            try {
                debut = Double.parseDouble(p(c).getString("soinsBase", ""));
            } catch (NumberFormatException x) {
                debut = maintenant;
                p(c).edit().putString("soinsBase", String.valueOf(debut)).apply();
            }
            base = Soins.neuf(debut);
        }
        java.util.List<Soins.Action> neuves = new java.util.ArrayList<>();
        for (Soins.Action a : soinsEnAttente(c)) if (a.t > base.t) neuves.add(a);
        return Soins.calculer(base, neuves, Math.max(maintenant, base.t));
    }

    // ---- Ce que l'atelier montre

    public static Map<String, Integer> stock(Context c) {
        Map<String, Integer> m = new HashMap<>();
        JSONObject s = objet(c, "stock");
        for (Iterator<String> i = s.keys(); i.hasNext(); ) {
            String k = i.next();
            if (s.optInt(k) > 0) m.put(k, s.optInt(k));
        }
        return m;
    }

    /** Espèces déjà pêchées : celles du PC et celles du téléphone. */
    public static Set<String> carnet(Context c, Etat e) {
        Set<String> s = new TreeSet<>(e.carnet);
        for (Iterator<String> i = objet(c, "carnetLocal").keys(); i.hasNext(); ) s.add(i.next());
        return s;
    }

    public static int prises(Context c, String id) {
        return objet(c, "carnetLocal").optInt(id);
    }

    /** Plats déjà faits : ceux du PC et ceux du téléphone. */
    public static Set<String> plats(Context c, Etat e) {
        Set<String> s = new TreeSet<>(e.plats);
        try {
            JSONArray a = new JSONArray(p(c).getString("platsLocal", "[]"));
            for (int i = 0; i < a.length(); i++) s.add(a.optString(i));
        } catch (JSONException ignore) {
            // rien
        }
        return s;
    }

    public static int enAttente(Context c) {
        JSONArray f = file(c);
        int xp = 0;
        for (int i = 0; i < f.length(); i++) xp += f.optJSONObject(i) == null ? 0 : f.optJSONObject(i).optInt("xp");
        return xp;
    }

    /** Niveau affiché : celui du PC (qui garde le niveau acquis), ou la courbe si l'XP en attente le dépasse. */
    public static int niveau(Context c, Etat e) {
        return Math.max(e.niveau, Butin.niveau(xp(c, e)));
    }

    /** XP connue : celle du PC (s'il la donne) plus ce qui n'est pas encore crédité. */
    public static int xp(Context c, Etat e) {
        int base = e.xp >= 0 ? e.xp : Butin.xpPourNiveau(e.niveau);
        return base + enAttente(c);
    }

    // ---- Avec le PC

    /** Le PC cite les gains qu'il a crédités : ils quittent la file. */
    public static synchronized void accuser(Context c, Etat e) {
        JSONArray f = file(c), reste = new JSONArray();
        long maintenant = System.currentTimeMillis();
        for (int i = 0; i < f.length(); i++) {
            JSONObject g = f.optJSONObject(i);
            if (g == null || e.recus.contains(g.optString("id"))) continue;
            if (maintenant - g.optLong("cree", maintenant) > OUBLI) continue;
            reste.put(g);
        }
        if (reste.length() != f.length()) p(c).edit().putString("gains", reste.toString()).apply();
    }

    /** Envoie ce qui n'est pas parti (ou parti il y a plus de 6 h sans accusé). Hors du fil principal. */
    public static void envoyer(Context c) {
        String code = Prefs.code(c);
        if (!Chiffre.valide(code)) return;
        JSONArray f;
        synchronized (Gains.class) {
            f = file(c);
        }
        long maintenant = System.currentTimeMillis();
        for (int i = 0; i < f.length(); i++) {
            JSONObject g = f.optJSONObject(i);
            if (g == null) continue;
            long envoye = g.optLong("envoye", 0);
            if (envoye != 0 && maintenant - envoye < RENVOI) continue;
            try {
                JSONObject message = new JSONObject(g.toString());
                message.remove("envoye");
                message.remove("cree");
                URL url = new URL(Prefs.relais(c).replaceAll("/+$", "") + "/" + Chiffre.sujetRetour(code));
                HttpURLConnection h = (HttpURLConnection) url.openConnection();
                h.setRequestMethod("POST");
                h.setDoOutput(true);
                h.setConnectTimeout(15_000);
                h.setReadTimeout(15_000);
                h.setRequestProperty("User-Agent", "pilou-android");
                try (OutputStream o = h.getOutputStream()) {
                    o.write(Chiffre.chiffrer(code, message.toString()).getBytes(StandardCharsets.UTF_8));
                }
                boolean ok = h.getResponseCode() / 100 == 2;
                h.disconnect();
                if (!ok) return;
                marquerEnvoye(c, g.getString("id"), maintenant);
            } catch (Exception e) {
                return; // hors ligne : on réessaiera
            }
        }
    }

    private static synchronized void marquerEnvoye(Context c, String id, long quand) throws JSONException {
        JSONArray f = file(c);
        for (int i = 0; i < f.length(); i++) {
            JSONObject g = f.optJSONObject(i);
            if (g != null && id.equals(g.optString("id"))) g.put("envoye", quand);
        }
        p(c).edit().putString("gains", f.toString()).apply();
    }
}
