package fr.pilou.compagnon;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

/**
 * Météo reçue du PC (champ facultatif « meteo » du message) et ce qu'elle fait à Pilou.
 * Mêmes règles que Meteo.cs : sous la pluie sans parapluie ni imperméable, il est mouillé et râle ;
 * dans le froid sans bonnet, écharpe ni moufles, il grelotte ; en pleine chaleur sans lunettes ni éventail, il sue.
 * Le téléphone ne contacte aucun service météo : seul le PC interroge Open-Meteo pour la ville choisie.
 */
public final class Meteo {
    public static final String DEGAGE = "degage", NUAGEUX = "nuageux", PLUIE = "pluie", AVERSE = "averse", ORAGE = "orage",
            NEIGE = "neige", BROUILLARD = "brouillard", VENT = "vent", CHALEUR = "chaleur", FROID = "froid";

    static final List<String> CONTRE_PLUIE = Arrays.asList("parapluie", "parapluie-etoile", "impermeable");
    static final List<String> CONTRE_FROID = Arrays.asList("acc-bonnet", "echarpe", "moufles", "impermeable");
    static final List<String> CONTRE_CHALEUR = Arrays.asList("acc-lunettes", "eventail");

    public final String etat, ville, signe;
    public final int temperature;

    public Meteo(String etat, int temperature, String ville, String signe) {
        this.etat = etat;
        this.temperature = temperature;
        this.ville = ville;
        this.signe = signe.isEmpty() ? signe(etat) : signe;
    }

    /** Lit le champ « meteo » ; null s'il manque ou ne dit rien de connu. */
    public static Meteo lire(JSONObject o) {
        if (o == null) return null;
        String etat = o.optString("etat", "");
        if (signe(etat).equals("·")) return null;           // état inconnu
        return new Meteo(etat, (int) Math.round(o.optDouble("temperature", 0)), o.optString("ville", ""), o.optString("signe", ""));
    }

    /** « ☂ pluie · 8 °C · Paris ». */
    public String ligne() {
        String s = signe + " " + nom(etat) + " · " + temperature + " °C";
        return ville.isEmpty() ? s : s + " · " + ville;
    }

    public static boolean pluvieux(String etat) {
        return PLUIE.equals(etat) || AVERSE.equals(etat) || ORAGE.equals(etat);
    }

    public static String signe(String etat) {
        switch (etat) {
            case DEGAGE: return "☀";
            case NUAGEUX: return "☁";
            case PLUIE:
            case AVERSE: return "☂";
            case ORAGE: return "⚡";
            case NEIGE: return "❄";
            case BROUILLARD: return "≋";
            case VENT: return "≈";
            case CHALEUR: return "☼";
            case FROID: return "✻";
            default: return "·";
        }
    }

    public static String nom(String etat) {
        switch (etat) {
            case DEGAGE: return "dégagé";
            case NUAGEUX: return "nuageux";
            case PLUIE: return "pluie";
            case AVERSE: return "averses";
            case ORAGE: return "orage";
            case NEIGE: return "neige";
            case BROUILLARD: return "brouillard";
            case VENT: return "vent fort";
            case CHALEUR: return "chaleur";
            case FROID: return "froid";
            default: return etat;
        }
    }

    /** Ce que la météo fait à Pilou : sprites ajoutés, protégé ou non, inconfort, tremblement, réaction. */
    public static final class Effet {
        public static final Effet AUCUN = new Effet(Collections.<String>emptyList(), true, "", 0, "");
        public final List<String> sprites;
        public final boolean protege;
        public final String inconfort, reaction;
        public final double tremble;

        Effet(List<String> sprites, boolean protege, String inconfort, double tremble, String reaction) {
            this.sprites = sprites;
            this.protege = protege;
            this.inconfort = inconfort;
            this.tremble = tremble;
            this.reaction = reaction;
        }

        /** Mouillé ou gelé : Pilou fait la grimace de temps en temps. */
        public boolean grognon() {
            return inconfort.equals("mouille") || inconfort.equals("froid");
        }
    }

    private static boolean un(List<String> liste, Collection<String> portes) {
        for (String x : liste) if (portes.contains(x)) return true;
        return false;
    }

    /** Discrétion (mêmes valeurs que Meteo.cs) : un éclair bref toutes les 12 s, une grimace 6 s sur 30. */
    static final long PERIODE_ECLAIR = 12_000, DUREE_ECLAIR = 280, PERIODE_GRIMACE = 6000;
    static final int CYCLE_GRIMACE = 5;

    static boolean eclairVisible(double t) {
        return ((t % PERIODE_ECLAIR) + PERIODE_ECLAIR) % PERIODE_ECLAIR < DUREE_ECLAIR;
    }

    /** portes : objets de boutique portés, et l'accessoire sous la forme « acc-&lt;nom&gt; ». t en millisecondes. */
    public static Effet effet(String etat, Collection<String> portes, double t) {
        if (etat == null || etat.isEmpty()) return Effet.AUCUN;
        double frisson = Math.sin(t / 55.0) * 0.35;
        switch (etat) {
            case PLUIE:
            case AVERSE:
            case ORAGE: {
                boolean sec = un(CONTRE_PLUIE, portes);
                List<String> s = new ArrayList<>();
                s.add(etat.equals(PLUIE) ? "meteo-pluie" : "meteo-averse");
                if (etat.equals(ORAGE) && eclairVisible(t)) s.add("meteo-eclair");
                if (!sec) s.add("meteo-mouille");
                return new Effet(s, sec, sec ? "" : "mouille", sec ? 0 : frisson, "");
            }
            case NEIGE: {
                boolean chaud = un(CONTRE_FROID, portes);
                List<String> s = new ArrayList<>();
                s.add("meteo-neige");
                if (!chaud) s.add("meteo-givre");
                return new Effet(s, chaud, chaud ? "" : "froid", chaud ? 0 : frisson, "");
            }
            case FROID: {
                boolean chaud = un(CONTRE_FROID, portes);
                return new Effet(chaud ? Collections.<String>emptyList() : Collections.singletonList("meteo-givre"), chaud,
                        chaud ? "" : "froid", chaud ? 0 : frisson * 0.7, "");
            }
            case CHALEUR: {
                boolean frais = un(CONTRE_CHALEUR, portes);
                return new Effet(Collections.singletonList("meteo-soleil"), frais, frais ? "" : "chaud", 0, frais ? "" : "sueur");
            }
            case VENT:
                return new Effet(Collections.singletonList("meteo-vent"), true, "", Math.sin(t / 160.0) * 0.25, "");
            case BROUILLARD:
                return new Effet(Collections.singletonList("meteo-brouillard"), true, "", 0, "");
            default:
                return Effet.AUCUN;
        }
    }

    /** Applique la météo à une allure : objets ajoutés, frisson, sueur, grimace de temps en temps. */
    public static Effet appliquer(RenduPilou.Allure a, String etat, long t) {
        List<String> portes = new ArrayList<>(a.objets);
        if (a.accessoire != null && !a.accessoire.isEmpty()) portes.add("acc-" + a.accessoire);
        Effet m = effet(etat, portes, t);
        if (m == Effet.AUCUN) return m;
        List<String> objets = new ArrayList<>(a.objets);
        objets.addAll(m.sprites);
        a.objets = objets;
        a.tremble += m.tremble;
        if (a.reaction == null || a.reaction.isEmpty()) a.reaction = m.reaction;
        if (m.grognon() && "repos".equals(a.expr) && (t / PERIODE_GRIMACE) % CYCLE_GRIMACE == 0) a.expr = "grimace";
        return m;
    }

    /** Ce que Pilou dit, en bref (carte Accueil). */
    public static String phrase(String etat, Effet e) {
        switch (e.inconfort) {
            case "mouille": return "brr, je suis trempé ! un parapluie ?";
            case "froid": return "je grelotte… un bonnet, des moufles ?";
            case "chaud": return "je fonds ! des lunettes, un éventail ?";
            default: break;
        }
        if (pluvieux(etat)) return "bien au sec, je suis paré !";
        if (NEIGE.equals(etat)) return "bien couvert, j'adore la neige !";
        if (CHALEUR.equals(etat)) return "grand soleil, lunettes de rigueur";
        if (VENT.equals(etat)) return "ça souffle ! je tiens mon antenne…";
        if (BROUILLARD.equals(etat)) return "on n'y voit rien…";
        return "";
    }
}
