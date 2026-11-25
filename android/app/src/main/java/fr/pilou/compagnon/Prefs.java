package fr.pilou.compagnon;

import android.content.Context;
import android.content.SharedPreferences;

/** Réglages et dernier état reçu, gardés sur le téléphone. */
public final class Prefs {
    public static final String RELAIS_DEFAUT = "https://ntfy.sh";

    private Prefs() {
    }

    public static SharedPreferences de(Context c) {
        return c.getSharedPreferences("pilou", Context.MODE_PRIVATE);
    }

    public static String code(Context c) {
        return de(c).getString("code", "");
    }

    public static String relais(Context c) {
        return de(c).getString("relais", RELAIS_DEFAUT);
    }

    public static boolean bulle(Context c) {
        return de(c).getBoolean("bulle", true);
    }

    public static boolean alerteAttente(Context c) {
        return de(c).getBoolean("alerteAttente", true);
    }

    public static boolean alerteFin(Context c) {
        return de(c).getBoolean("alerteFin", true);
    }

    /** Dernier état déchiffré (pour le widget et au redémarrage). */
    public static Etat etat(Context c) {
        String json = de(c).getString("etat", "");
        if (json.isEmpty()) return Etat.vide();
        try {
            return Etat.lire(json, de(c).getLong("recu", 0));
        } catch (org.json.JSONException e) {
            return Etat.vide();
        }
    }
}
