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

    // Un gain s'ajoute au dernier pas encore envoyé (moins de messages), sinon ouvre une nouvelle entrée.
    private static synchronized void ajouter(Context c, int xp, String prise, String plat, int caresses) {
        try {
            JSONArray f = file(c);
            JSONObject g = f.length() > 0 && f.getJSONObject(f.length() - 1).optLong("envoye", 0) == 0 ? f.getJSONObject(f.length() - 1) : null;
            if (g == null) {
                g = new JSONObject().put("v", 1).put("id", nouvelId()).put("xp", 0).put("prises", new JSONObject())
                        .put("plats", new JSONArray()).put("caresses", 0).put("cree", System.currentTimeMillis()).put("envoye", 0);
                f.put(g);
            }
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

    public static void prise(Context c, Butin.Prise x, int xp) {
        JSONObject carnet = objet(c, "carnetLocal");
        JSONObject stock = objet(c, "stock");
        try {
            carnet.put(x.id, carnet.optInt(x.id) + 1);
            if (x.comestible()) stock.put(x.id, stock.optInt(x.id) + 1);
        } catch (JSONException e) {
            return;
        }
        p(c).edit().putString("carnetLocal", carnet.toString()).putString("stock", stock.toString()).apply();
        ajouter(c, xp, x.id, null, 0);
    }

    public static void plat(Context c, Butin.Plat pl) {
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
            return;
        }
        p(c).edit().putString("stock", stock.toString()).apply();
        ajouter(c, pl.xp, null, pl.rate ? null : pl.id, 0);
    }

    public static void jeu(Context c, int xp) {
        ajouter(c, xp, null, null, 0);
    }

    public static void caresse(Context c) {
        ajouter(c, 1, null, null, 1);
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
