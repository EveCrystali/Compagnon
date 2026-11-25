package fr.pilou.compagnon;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** Ce que le PC a publié (Telephone.Charge) et ce que la bulle en dit, comme Statut.cs. */
public final class Etat {
    public static final long FINI_VISIBLE = 2 * 3600_000L;
    /** Sans nouvelles du PC depuis 25 min (il publie au moins toutes les 15 min) : il dort ou il est éteint. */
    public static final long PC_MUET = 25 * 60_000L;
    private static final String[] ROUE = {"◐", "◓", "◑", "◒"};

    public enum Ton {ATTENTE, TRAVAIL, FINI, NEUTRE}

    public static final class Session {
        public final String id, source, libelle, etat, outil;
        public final long depuis;

        Session(String id, String source, String libelle, String etat, long depuis, String outil) {
            this.id = id;
            this.source = source;
            this.libelle = libelle;
            this.etat = etat;
            this.depuis = depuis;
            this.outil = outil;
        }

        public boolean attend() {
            return etat.equals("permission") || etat.equals("question");
        }

        public String nom() {
            return source.equals("claude") || source.isEmpty() ? libelle : etiquette(source) + " · " + libelle;
        }
    }

    public static final class Ligne {
        public final String signe, libelle, texte;
        public final Ton ton;
        public final boolean nouveau;

        Ligne(String signe, String libelle, String texte, Ton ton, boolean nouveau) {
            this.signe = signe;
            this.libelle = libelle;
            this.texte = texte;
            this.ton = ton;
            this.nouveau = nouveau;
        }

        @Override
        public String toString() {
            return signe + " " + libelle + " · " + texte;
        }
    }

    public final String nom, titre, couleur, humeur;
    public final int niveau, calmes;
    public final long t;
    /** Écart d'horloge téléphone − PC, mesuré à la réception (0 si le message sort du cache du relais). */
    public final long decalage;
    public final List<Session> sessions;

    private Etat(String nom, String titre, String couleur, String humeur, int niveau, int calmes, long t, long decalage, List<Session> sessions) {
        this.nom = nom;
        this.titre = titre;
        this.couleur = couleur;
        this.humeur = humeur;
        this.niveau = niveau;
        this.calmes = calmes;
        this.t = t;
        this.decalage = decalage;
        this.sessions = sessions;
    }

    public static Etat vide() {
        return new Etat("Pilou", "", "bleu", "dort", 1, 0, 0, 0, new ArrayList<>());
    }

    public static Etat lire(String json, long recu) throws JSONException {
        JSONObject r = new JSONObject(json);
        long t = r.optLong("t", 0);
        long ecart = recu - t;
        long decalage = Math.abs(ecart) < 120_000 ? ecart : 0;
        List<Session> liste = new ArrayList<>();
        JSONArray s = r.optJSONArray("sessions");
        if (s != null)
            for (int i = 0; i < s.length(); i++) {
                JSONObject o = s.getJSONObject(i);
                liste.add(new Session(o.optString("id"), o.optString("source", "claude"), o.optString("libelle"),
                        o.optString("etat"), o.optLong("depuis", 0) + decalage, o.optString("outil")));
            }
        return new Etat(r.optString("nom", "Pilou"), r.optString("titre"), r.optString("couleur", "bleu"),
                r.optString("humeur", "repos"), r.optInt("niveau", 1), r.optInt("calmes", 0), t + decalage, decalage, liste);
    }

    public static String etiquette(String source) {
        switch (source) {
            case "claude": return "Claude";
            case "codex": return "Codex";
            case "gemini": return "Gemini";
            case "copilot": return "Copilot";
            default: return source.isEmpty() ? "?" : Character.toUpperCase(source.charAt(0)) + source.substring(1);
        }
    }

    public static String duree(long ms) {
        long s = Math.max(0, ms / 1000);
        if (s < 60) return s + " s";
        if (s < 3600) return (s / 60) + " min";
        return (s / 3600) + " h " + String.format(java.util.Locale.ROOT, "%02d", s % 3600 / 60);
    }

    public boolean muet(long maintenant) {
        return t == 0 || maintenant - t > PC_MUET;
    }

    public boolean attend() {
        for (Session s : sessions) if (s.attend()) return true;
        return false;
    }

    public List<Ligne> lignes(long maintenant, int image) {
        List<Ligne> l = new ArrayList<>();
        for (Session s : sessions) {
            long il = maintenant - s.depuis;
            switch (s.etat) {
                case "permission":
                    l.add(new Ligne("❗", s.nom(), "attend ton autorisation", Ton.ATTENTE, false));
                    break;
                case "question":
                    l.add(new Ligne("?", s.nom(), "te pose une question", Ton.ATTENTE, false));
                    break;
                case "travail": {
                    boolean connu = s.depuis > 0 && il < 24 * 3600_000L;
                    String texte = !s.outil.isEmpty() ? s.outil : connu ? "réfléchit · " + duree(il) : "réfléchit";
                    l.add(new Ligne(ROUE[Math.floorMod(image, ROUE.length)], s.nom(), texte, Ton.TRAVAIL, false));
                    break;
                }
                case "fini":
                    if (il < FINI_VISIBLE)
                        l.add(new Ligne("✓", s.nom(), il < 60_000 ? "vient de finir" : "fini · il y a " + duree(il), Ton.FINI, il < 60_000));
                    break;
                case "interrompu":
                    if (il < FINI_VISIBLE) l.add(new Ligne("■", s.nom(), "interrompu · il y a " + duree(il), Ton.NEUTRE, false));
                    break;
                case "erreur":
                    if (il < FINI_VISIBLE) l.add(new Ligne("✕", s.nom(), "erreur · il y a " + duree(il), Ton.ATTENTE, false));
                    break;
                default:
                    break;
            }
        }
        return l;
    }

    /** « ❗ 1 t'attend · ◐ 2 en cours · ✓ 3 finies », ou l'état du PC. */
    public String resume(long maintenant) {
        if (muet(maintenant)) return t == 0 ? "en attente du PC…" : "le PC dort (rien depuis " + duree(maintenant - t) + ")";
        int a = 0, w = 0, f = 0;
        for (Ligne l : lignes(maintenant, 0)) {
            if (l.ton == Ton.ATTENTE && !l.signe.equals("✕")) a++;
            else if (l.ton == Ton.TRAVAIL) w++;
            else if (l.ton == Ton.FINI) f++;
        }
        List<String> m = new ArrayList<>();
        if (a > 0) m.add("❗ " + a + " t'attend" + (a > 1 ? "ent" : ""));
        if (w > 0) m.add("◐ " + w + " en cours");
        if (f > 0) m.add("✓ " + f + " fini" + (f > 1 ? "es" : "e"));
        if (m.isEmpty()) m.add(calmes > 0 ? calmes + " session" + (calmes > 1 ? "s" : "") + " au calme" : "aucune session ouverte");
        return String.join("  ·  ", m);
    }

    /** Expression de Pilou : il dort si le PC se tait, s'inquiète si on attend, sinon suit le PC. */
    public String expression(long maintenant) {
        if (muet(maintenant)) return "dort";
        if (attend()) return "inquiet";
        for (Session s : sessions) if (s.etat.equals("travail")) return "concentre";
        return humeur.isEmpty() ? "repos" : humeur;
    }
}
