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
    /** Progression (PC ≥ 0.9.4) : XP totale, accessoire porté, carnet et recettes connues, gains crédités. */
    public int xp = -1, inventes;
    public String accessoire = "aucun";
    public final java.util.Set<String> carnet = new java.util.TreeSet<>(), plats = new java.util.TreeSet<>();
    public final List<String> recus = new ArrayList<>();
    /** Boutique et quêtes (PC ≥ 0.9.10) : solde en po (-1 : inconnu), objets possédés, objets portés par
     *  emplacement, offres du jour (la première en promo), série de jours, quêtes en cours. */
    public int po = -1, serie;
    /** Stade d'évolution affiché sur le PC (0 : inconnu, le téléphone le déduit du niveau). */
    public int stade;
    public final java.util.Set<String> objets = new java.util.TreeSet<>();
    public final java.util.Map<String, String> porte = new java.util.TreeMap<>();
    public final List<String> offres = new ArrayList<>();
    public String promo = "";
    public final List<Quete> quetes = new ArrayList<>();
    /** Météo vue par le PC (connecteur météo actif), ou null. */
    public Meteo meteo;
    /** Au-delà, la météo reçue est trop vieille pour être montrée. */
    public static final long METEO_VALIDE = 3 * 3600_000L;

    public static final class Quete {
        /** 0 jour, 1 semaine, 2 mois. */
        public final int periode, fait, objectif, po;
        public final String texte;
        public final boolean reussie;

        Quete(int periode, String texte, int fait, int objectif, int po, boolean reussie) {
            this.periode = periode;
            this.texte = texte;
            this.fait = fait;
            this.objectif = objectif;
            this.po = po;
            this.reussie = reussie;
        }
    }

    /** Appareils du groupe (PC ≥ 0.9.6) : nom, XP de chacun, dernière nouvelle ; le PC qui publie en tête. */
    public final List<Appareil> appareils = new ArrayList<>();

    public static final class Appareil {
        public final String nom;
        public final int xp;
        public final long t;

        Appareil(String nom, int xp, long t) {
            this.nom = nom;
            this.xp = xp;
            this.t = t;
        }

        public String texte(long maintenant) {
            return nom + " · " + xp + " xp · " + (t <= 0 ? "jamais vu" : "vu il y a " + duree(maintenant - t));
        }
    }

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
        Etat e = new Etat(r.optString("nom", "Pilou"), r.optString("titre"), r.optString("couleur", "bleu"),
                r.optString("humeur", "repos"), r.optInt("niveau", 1), r.optInt("calmes", 0), t + decalage, decalage, liste);
        e.xp = r.optInt("xp", -1);
        e.accessoire = r.optString("accessoire", "aucun");
        e.inventes = r.optInt("inventes", 0);
        for (String cle : new String[]{"carnet", "plats", "recus"}) {
            JSONArray a = r.optJSONArray(cle);
            if (a == null) continue;
            for (int i = 0; i < a.length(); i++) {
                String v = a.optString(i, "");
                if (v.isEmpty()) continue;
                if (cle.equals("carnet")) e.carnet.add(v);
                else if (cle.equals("plats")) e.plats.add(v);
                else e.recus.add(v);
            }
        }
        e.po = r.optInt("po", -1);
        e.stade = r.optInt("stade", 0);
        e.serie = r.optInt("serie", 0);
        e.promo = r.optString("promo", "");
        JSONArray ob = r.optJSONArray("objets");
        if (ob != null) for (int i = 0; i < ob.length(); i++) if (!ob.optString(i, "").isEmpty()) e.objets.add(ob.optString(i));
        JSONObject po = r.optJSONObject("porte");
        if (po != null)
            for (java.util.Iterator<String> k = po.keys(); k.hasNext(); ) {
                String slot = k.next();
                if (!po.optString(slot, "").isEmpty()) e.porte.put(slot, po.optString(slot));
            }
        JSONArray of = r.optJSONArray("offres");
        if (of != null) for (int i = 0; i < of.length(); i++) if (!of.optString(i, "").isEmpty()) e.offres.add(of.optString(i));
        JSONArray qu = r.optJSONArray("quetes");
        if (qu != null)
            for (int i = 0; i < Math.min(12, qu.length()); i++) {
                JSONArray q = qu.optJSONArray(i);
                if (q == null || q.length() < 6) continue;
                e.quetes.add(new Quete(q.optInt(0), q.optString(1), q.optInt(2), Math.max(1, q.optInt(3)), q.optInt(4), q.optInt(5) == 1));
            }
        e.meteo = Meteo.lire(r.optJSONObject("meteo"));
        JSONArray ap = r.optJSONArray("appareils");
        if (ap != null)
            for (int i = 0; i < Math.min(10, ap.length()); i++) {
                JSONObject o = ap.optJSONObject(i);
                if (o == null || o.optString("nom").isEmpty()) continue;
                e.appareils.add(new Appareil(o.optString("nom"), o.optInt("xp", 0), o.optLong("t", 0) + decalage));
            }
        return e;
    }

    /** La météo encore valable (le PC a parlé il y a moins de trois heures), ou null. */
    public Meteo meteo(long maintenant) {
        return meteo != null && t > 0 && maintenant - t < METEO_VALIDE ? meteo : null;
    }

    /** Identifiant d'état météo valable, ou "" : ce que PilouVue.meteo attend. */
    public String etatMeteo(long maintenant) {
        Meteo m = meteo(maintenant);
        return m == null ? "" : m.etat;
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
