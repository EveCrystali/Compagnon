package fr.pilou.compagnon;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Soins (même modèle que apps/PilouBureau/Soins.cs) : trois besoins qui baissent lentement, au même rythme
 * pour tout le monde — faim, propreté, moral. L'état est une fonction pure d'une base et d'actions
 * horodatées ; rien ne s'affiche tant que tout va bien, sous 30 % une petite icône près de Pilou, et un
 * toucher la comble. Négligé, Pilou boude (ronchon, gains × 0,6 pendant un temps — c'est tout) ; bien
 * soigné, il rayonne (× 1,2).
 */
final class Soins {
    static final String FAIM = "faim", PROPRETE = "proprete", MORAL = "moral";
    static final String[] BESOINS = {FAIM, PROPRETE, MORAL};
    static final double SEUIL = 30, SEUIL_RAYONNANT = 70;
    /** Bouderie : un besoin sous 20 % depuis 6 h, ou deux à la fois ; une fois soigné, il traîne encore 30 min. */
    static final double SEUIL_BOUDERIE = 20, AVANT_BOUDERIE = 6 * 3600_000.0, RANCUNE = 30 * 60_000.0;
    static final double MALUS_BOUDERIE = 0.6, BONUS_RAYONNANT = 1.2;
    static final double HEURES_FAIM = 36, HEURES_PROPRETE = 48, HEURES_MORAL = 30;
    private static final double HEURE = 3600_000, TAU_SCORE = 3 * 24 * HEURE;
    /** En-cas, du meilleur au plus simple (bonus de moral) : les croquettes sont toujours là, gratuites. */
    static final String[] EN_CAS = {"gateau", "soupe", "pomme", "croquettes"};
    private static final int[] BONUS_EN_CAS = {15, 10, 5, 0};

    private Soins() {
    }

    static final class EtatSoins {
        double faim = 100, proprete = 100, moral = 100, score = 80, t;
        boolean vacances;
        /** Bouderie : temps passé avec un besoin sous 20 % (ms), s'il boude, fin de la rancune (0 : il boude pour de bon). */
        double neglige, finBouderie;
        boolean boude;

        EtatSoins copie() {
            EtatSoins e = new EtatSoins();
            e.faim = faim;
            e.proprete = proprete;
            e.moral = moral;
            e.score = score;
            e.t = t;
            e.vacances = vacances;
            e.neglige = neglige;
            e.boude = boude;
            e.finBouderie = finBouderie;
            return e;
        }
    }

    static final class Action {
        final String id, type, objet;
        final double t;

        Action(String id, String type, double t, String objet) {
            this.id = id;
            this.type = type;
            this.t = t;
            this.objet = objet == null ? "" : objet;
        }
    }

    static EtatSoins neuf(double t) {
        EtatSoins e = new EtatSoins();
        e.t = t;
        return e;
    }

    /** L'état à « maintenant » : la base, puis chaque action dans l'ordre (heure, identifiant). */
    static EtatSoins calculer(EtatSoins base, List<Action> actions, double maintenant) {
        EtatSoins e = base.copie();
        List<Action> l = new ArrayList<>(actions);
        Collections.sort(l, (a, b) -> {
            int c = Double.compare(Math.max(a.t, base.t), Math.max(b.t, base.t));
            return c != 0 ? c : a.id.compareTo(b.id);
        });
        for (Action a : l) {
            double t = Math.max(a.t, base.t);
            if (t > maintenant) break;
            avancer(e, t);
            appliquer(e, a);
        }
        avancer(e, Math.max(maintenant, e.t));
        return e;
    }

    static void avancer(EtatSoins e, double jusqua) {
        while (e.t < jusqua) {
            double dt = Math.min(HEURE, jusqua - e.t);
            if (!e.vacances) {
                double f = dt / HEURE * 100;
                e.faim = Math.max(0, e.faim - f / HEURES_FAIM);
                e.proprete = Math.max(0, e.proprete - f / HEURES_PROPRETE);
                e.moral = Math.max(0, e.moral - f / HEURES_MORAL);
                double moyenne = (e.faim + e.proprete + e.moral) / 3;
                e.score += (moyenne - e.score) * (1 - Math.exp(-dt / TAU_SCORE));
                // Bouderie : on regarde à la fin de chaque tranche (≤ 1 h).
                int bas = bas(e);
                e.neglige = bas > 0 ? e.neglige + dt : 0;
                if (bas >= 2 || (bas >= 1 && e.neglige >= AVANT_BOUDERIE)) {
                    e.boude = true;
                    e.finBouderie = 0;
                }
            }
            e.t += dt;
            // Amadoué : la rancune passée, il ne boude plus.
            if (e.boude && e.finBouderie > 0 && e.t >= e.finBouderie) {
                e.boude = false;
                e.finBouderie = 0;
            }
        }
    }

    static void appliquer(EtatSoins e, Action a) {
        switch (a.type) {
            case "nourrir":
                e.faim = 100;
                e.moral = Math.min(100, e.moral + bonusEnCas(a.objet));
                break;
            case "laver":
                e.proprete = 100;
                break;
            case "calin":
                e.moral = 100;
                break;
            case "soin":
                e.faim = e.proprete = e.moral = 100;
                break;
            case "caresse":
                e.moral = Math.min(100, e.moral + 10);
                break;
            case "jouer":
                e.moral = Math.min(100, e.moral + 15);
                break;
            case "vacances":
                e.vacances = "1".equals(a.objet);
                break;
            default: // « rythme » (ancien réglage de difficulté) : ignoré, tout le monde a le même rythme
                break;
        }
        // Soigné pendant qu'il boude : plus aucun besoin bas → il se laisse amadouer, mais garde 30 min de rancune.
        if (bas(e) == 0) e.neglige = 0;
        if (e.boude && e.finBouderie == 0 && bas(e) == 0) e.finBouderie = e.t + RANCUNE;
    }

    private static int bas(EtatSoins e) {
        int n = 0;
        for (String b : BESOINS) if (valeur(e, b) < SEUIL_BOUDERIE) n++;
        return n;
    }

    static int bonusEnCas(String objet) {
        if (objet.startsWith("plat")) return 15;
        for (int i = 0; i < EN_CAS.length; i++) if (EN_CAS[i].equals(objet)) return BONUS_EN_CAS[i];
        return 0;
    }

    static double valeur(EtatSoins e, String besoin) {
        return FAIM.equals(besoin) ? e.faim : PROPRETE.equals(besoin) ? e.proprete : e.moral;
    }

    /** Besoins sous le seuil, du plus pressant au moins pressant. */
    static List<String> manques(EtatSoins e) {
        List<String> l = new ArrayList<>();
        for (String b : BESOINS) if (valeur(e, b) < SEUIL) l.add(b);
        Collections.sort(l, (a, b) -> Double.compare(valeur(e, a), valeur(e, b)));
        return l;
    }

    static boolean rayonnant(EtatSoins e) {
        return !e.vacances && e.faim > SEUIL_RAYONNANT && e.proprete > SEUIL_RAYONNANT && e.moral > SEUIL_RAYONNANT;
    }

    /** Il boude (ronchon, gains réduits) ; « amadoué » : soigné, mais il boude encore un peu. */
    static boolean boudeur(EtatSoins e) {
        return !e.vacances && e.boude;
    }

    static boolean amadoue(EtatSoins e) {
        return boudeur(e) && e.finBouderie > 0;
    }

    /** Multiplicateur des gains d'XP et de po : × 0,6 s'il boude, × 1,2 s'il rayonne, sinon × 1. */
    static double multiplicateur(EtatSoins e) {
        return boudeur(e) ? MALUS_BOUDERIE : rayonnant(e) ? BONUS_RAYONNANT : 1;
    }

    /** Un gain ajusté (arrondi ; un gain positif rapporte toujours au moins 1). */
    static int bonus(int gain, EtatSoins e) {
        if (gain <= 0 || e == null) return gain;
        double m = multiplicateur(e);
        return m == 1 ? gain : Math.max(1, (int) Math.floor(gain * m + 0.5));
    }

    /** Signe de forme de chaque besoin (jamais la couleur seule). */
    static String signe(String besoin) {
        return FAIM.equals(besoin) ? "◒" : PROPRETE.equals(besoin) ? "✦" : "♥";
    }

    static String nom(String besoin) {
        return FAIM.equals(besoin) ? "faim" : PROPRETE.equals(besoin) ? "propreté" : "moral";
    }

    static String resume(EtatSoins e) {
        StringBuilder b = new StringBuilder();
        for (String x : BESOINS) {
            if (b.length() > 0) b.append(" · ");
            b.append(signe(x)).append(' ').append(nom(x)).append(' ').append(Math.round(valeur(e, x))).append(" %");
        }
        return b.toString();
    }

    // ---- Échanges

    /** L'état envoyé par le PC (clés f, p, m, s, t, v, n, b, fb ; « r », l'ancien rythme, est ignoré) ; null s'il manque. */
    static EtatSoins lireEtat(JSONObject r) {
        if (r == null || r.optDouble("t", 0) <= 0) return null;
        EtatSoins e = new EtatSoins();
        e.faim = borne(r.optDouble("f", 100));
        e.proprete = borne(r.optDouble("p", 100));
        e.moral = borne(r.optDouble("m", 100));
        e.score = borne(r.optDouble("s", 80));
        e.t = r.optDouble("t", 0);
        e.vacances = r.optInt("v", 0) == 1;
        e.neglige = Math.max(0, r.optDouble("n", 0));
        e.boude = r.optInt("b", 0) == 1;
        e.finBouderie = Math.max(0, r.optDouble("fb", 0));
        return e;
    }

    private static double borne(double v) {
        return Double.isNaN(v) ? 100 : Math.max(0, Math.min(100, v));
    }

    static JSONArray json(Action a) {
        JSONArray j = new JSONArray().put(a.id).put(a.type);
        try {
            j.put(a.t);
        } catch (org.json.JSONException ignore) {
            // nombre fini : n'arrive pas
        }
        if (!a.objet.isEmpty()) j.put(a.objet);
        return j;
    }

    static Action lireAction(JSONArray j) {
        if (j == null || j.length() < 3 || j.optString(0, "").isEmpty() || j.optString(1, "").isEmpty()) return null;
        return new Action(j.optString(0), j.optString(1), j.optDouble(2, 0), j.optString(3, ""));
    }
}
