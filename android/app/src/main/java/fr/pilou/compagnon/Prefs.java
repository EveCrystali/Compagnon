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

    /** Taille du Pilou flottant : 0,6 (petit) à 2,5 (très grand) ; 1 = taille d'origine. */
    public static final float TAILLE_MIN = 0.6f, TAILLE_MAX = 2.5f;

    public static float taille(Context c) {
        return Math.max(TAILLE_MIN, Math.min(TAILLE_MAX, de(c).getFloat("taille", 1f)));
    }

    public static boolean alerteAttente(Context c) {
        return de(c).getBoolean("alerteAttente", true);
    }

    public static boolean alerteFin(Context c) {
        return de(c).getBoolean("alerteFin", true);
    }

    /** « Pilou a besoin de toi » : désactivée par défaut, une fois par jour au plus. */
    public static boolean alerteSoins(Context c) {
        return de(c).getBoolean("alerteSoins", false);
    }

    /** Retour de Pilou d'une étape de campagne : une notification à la fin d'une attente ou d'un repos. */
    public static boolean alerteAventure(Context c) {
        return de(c).getBoolean("alerteAventure", true);
    }

    public static boolean alerteMaj(Context c) {
        return de(c).getBoolean("alerteMaj", true);
    }

    public static boolean son(Context c) {
        return de(c).getBoolean("son", true);
    }

    public static boolean vibrations(Context c) {
        return de(c).getBoolean("vibrations", true);
    }

    public static int meilleurChasse(Context c) {
        return de(c).getInt("meilleurChasse", 0);
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
