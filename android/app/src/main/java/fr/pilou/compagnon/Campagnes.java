package fr.pilou.compagnon;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;

/**
 * Campagnes (docs/CAMPAGNES.md) : de longs récits à choix, en temps réel. Pilou écrit, le joueur choisit, Pilou met du
 * vrai temps à agir. Cette classe est le MOTEUR, sans interface ni Android (Java pur + org.json) : la copie exacte de
 * apps/PilouBureau/Campagnes.cs (mêmes règles, mêmes tirages, mêmes messages). Les vecteurs partagés
 * src/test/resources/campagnes-vecteurs.txt, écrits par le PC, sont rejoués par CampagnesTest.
 *
 * <p>API, pour qui écrit l'interface (détail : docs/CAMPAGNES.md, « API du moteur ») ; côté Android, passer par
 * CampagnesTel, qui garde le carnet dans les préférences et le synchronise :
 * <pre>
 *   Bibliothèque   Campagnes.disponibles()            ids des campagnes embarquées (ressources /campagnes/&lt;id&gt;/)
 *                  Campagnes.charger(id)              la campagne (fiche + chapitres), null si inconnue
 *   Carnet         Campagnes.Carnet                   partie en cours, parties suspendues, historique, fil des messages
 *   État courant   Campagnes.actualiser(carnet, Campagnes::charger, maintenant) → Etat (null : aucune partie)
 *                    etat.phase   Choix | Epreuve | Depart | Attente | Repos | Fin | Abandon | Cassee
 *                    etat.options (Choix), etat.jeu / difficulte / aide (Epreuve), etat.fin (ms : fin de l'attente ou
 *                    du repos → notification locale), etat.pendant et etat.tenue (Pilou occupé), etat.lieu, etat.decor,
 *                    etat.humeur, etat.chapitre…, etat.progression, etat.issue (fin obtenue)
 *                    carnet.fil : les messages (Pilou et joueur), carnet.nonLus(), Campagnes.marquerLu(carnet)
 *   Décisions      Campagnes.demarrer(carnet, campagne, niveau, maintenant, appareil, biblio, graine, neuf) → null ou le refus
 *                  Campagnes.choisir(carnet, campagne, maintenant, appareil, idOption)   (phase Choix)
 *                  Campagnes.continuer(…)        « vas-y » : Pilou part (phase Depart)
 *                  Campagnes.epreuve(…, reussie) résultat d'un mini-jeu (phase Epreuve)
 *                  Campagnes.epreuveAuDe(…)      l'appareil ne sait pas jouer ce jeu : tirage « des » à la place
 *                  Campagnes.abandonner(…)       la partie s'arrête ; demarrer la reprendra au dernier check-point
 *   Synchro        Campagnes.messages(carnet, appareil, "tel") → 1 ou 2 JSON (≤ TAILLE_JSON) à chiffrer et publier sur
 *                  Campagnes.sujet(code) ; Campagnes.recevoir(carnet, json, appareil, biblio, maintenant)
 * </pre>
 *
 * <p>Principe : l'état se déduit d'un journal, la liste des décisions (étape, heure, appareil, nœud, valeur).
 * rejouer(campagne, partie, maintenant) redonne toujours le même état. Deux appareils décident pour la même étape : la
 * plus ancienne gagne (égalité : plus petit identifiant d'appareil). Une partie = un résumé d'état (« base », posée à
 * un check-point) + les décisions prises depuis. Dans les messages, nœuds, variables, objets, drapeaux et décors sont
 * désignés par un code de 4 caractères tiré de leur identifiant.
 */
public final class Campagnes {
    private Campagnes() {
    }

    public enum Phase {Aucune, Choix, Epreuve, Depart, Attente, Repos, Fin, Abandon, Cassee}

    /** Valeurs d'une décision qui n'est pas un choix (un choix : le rang de l'option, ≥ 0). */
    public static final int SUITE = -1, REUSSITE = -2, RATE = -3, ABANDON = -4;
    public static final long GRACE = 600_000;
    public static final int MAX_ENTREES = 24, GARDE_ENTREES = 12, MAX_PAR_ETAPE = 6, MAX_AVANCE = 64, MAX_PAS = 4000, MAX_FIL = 150;
    /** JSON d'un message de synchronisation, au plus (chiffré puis base64 : sous les 3 800 octets du relais). */
    public static final int TAILLE_JSON = 2750;
    public static final List<String> JEUX = Arrays.asList("reflexe", "memoire", "rythme", "visee", "des");
    public static final List<String> HUMEURS = Arrays.asList("joie", "peur", "triste", "surpris", "determine", "fatigue", "tendre", "colere", "malice", "neutre");
    public static final List<String> TENUES = Arrays.asList("marche", "course", "bateau", "grimpe", "nage", "nuit", "cache", "attend");

    // ---- Modèle d'une campagne (lu des fichiers JSON)

    public static final class Condition {
        /** var, objet, drapeau, non, tous, un ; autre chose : fausse. */
        public String sorte = "inconnue", nom = "";
        public Integer min, max;
        public final List<Condition> sous = new ArrayList<>();
    }

    /** sorte : var (valeur ajoutée), objet ou drapeau (valeur 1 : donné / posé, 0 : perdu / ôté). */
    public static final class Effet {
        public final String sorte, nom;
        public final int valeur;

        Effet(String sorte, String nom, int valeur) {
            this.sorte = sorte;
            this.nom = nom;
            this.valeur = valeur;
        }
    }

    public static final class Option {
        public final String id, libelle, vers;
        public final Condition si;
        public final List<Effet> effets;

        Option(String id, String libelle, String vers, Condition si, List<Effet> effets) {
            this.id = id;
            this.libelle = libelle;
            this.vers = vers;
            this.si = si;
            this.effets = effets;
        }
    }

    public static final class IssueHasard {
        public final int poids;
        public final String vers;
        public final Condition si;

        IssueHasard(int poids, String vers, Condition si) {
            this.poids = poids;
            this.vers = vers;
            this.si = si;
        }
    }

    public static final class Prime {
        public final int po, xp;
        public final String souvenir, titre, objet;

        Prime(int po, int xp, String souvenir, String titre, String objet) {
            this.po = po;
            this.xp = xp;
            this.souvenir = souvenir;
            this.titre = titre;
            this.objet = objet;
        }

        public boolean vide() {
            return po <= 0 && xp <= 0 && souvenir.isEmpty() && titre.isEmpty() && objet.isEmpty();
        }
    }

    public static final class Chapitre {
        public final String id, titre, fichier;

        Chapitre(String id, String titre, String fichier) {
            this.id = id;
            this.titre = titre;
            this.fichier = fichier;
        }
    }

    /** Objet, souvenir ou décor déclaré : id, nom, texte (ou description). */
    public static final class Nomme {
        public final String id, nom, texte;

        Nomme(String id, String nom, String texte) {
            this.id = id;
            this.nom = nom;
            this.texte = texte;
        }
    }

    public static final class Noeud {
        public String id = "", chapitre = "", type = "", lieu = "", humeur = "neutre", decor = "", suite = "", pendant = "", tenue = "",
                jeu = "", bonus = "", reussite = "", echec = "", issue = "", titre = "";
        public final List<String> texte = new ArrayList<>();
        public boolean checkpoint;
        public List<Effet> effets = new ArrayList<>();
        public Prime recompense = new Prime(0, 0, "", "", "");
        public final List<Option> options = new ArrayList<>();
        public final List<IssueHasard> issues = new ArrayList<>();
        public int dureeMin, dureeMax, difficulte = 1, reposMin;
    }

    public static final class Campagne {
        public String id = "", titre = "", ton = "", accroche = "", duree = "", depart = "";
        public int niveau = 1;
        public final List<Chapitre> chapitres = new ArrayList<>();
        public final TreeMap<String, Integer> variables = new TreeMap<>();
        public List<Nomme> objets = new ArrayList<>(), souvenirs = new ArrayList<>(), decors = new ArrayList<>();
        public final Map<String, Noeud> noeuds = new HashMap<>();
        /** code court → identifiant, par famille (n nœuds, v variables, o objets, d drapeaux, c décors). */
        private final Map<String, String> codes = new HashMap<>();

        public Noeud noeud(String id) {
            return noeuds.get(id);
        }

        public String decode(char famille, String code) {
            return codes.get(famille + code);
        }

        public Nomme souvenir(String id) {
            for (Nomme s : souvenirs) if (s.id.equals(id)) return s;
            return null;
        }

        private void ajouter(char famille, Iterable<String> ids) {
            TreeSet<String> tries = new TreeSet<>();
            for (String id : ids) tries.add(id);
            for (String id : tries)
                if (!codes.containsKey(famille + code(id))) codes.put(famille + code(id), id); // deux ids de même code : le premier
        }

        void indexer() {
            codes.clear();
            ajouter('n', noeuds.keySet());
            ajouter('v', variables.keySet());
            List<String> o = new ArrayList<>(), c = new ArrayList<>();
            for (Nomme x : objets) o.add(x.id);
            for (Nomme x : decors) c.add(x.id);
            ajouter('o', o);
            ajouter('c', c);
            TreeSet<String> drapeaux = new TreeSet<>();
            for (Noeud n : noeuds.values()) {
                for (Effet e : n.effets) if (e.sorte.equals("drapeau")) drapeaux.add(e.nom);
                for (Option op : n.options) for (Effet e : op.effets) if (e.sorte.equals("drapeau")) drapeaux.add(e.nom);
            }
            ajouter('d', drapeaux);
        }
    }

    // ---- Codes courts et tirages (identiques sur le PC et le téléphone)

    private static final String ALPHABET64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

    /** Tirage déterministe, identique à Hasard (Boutique.cs) : FNV-1a 64 bits puis xorshift64*. */
    public static final class Hasard {
        private long s;

        Hasard(long graine) {
            s = graine == 0 ? 0x9E3779B97F4A7C15L : graine;
        }

        static long graine(String t) {
            long h = 0xcbf29ce484222325L;
            for (int i = 0; i < t.length(); i++) {
                h ^= t.charAt(i);
                h *= 0x100000001b3L;
            }
            return h;
        }

        long brut() {
            s ^= s >>> 12;
            s ^= s << 25;
            s ^= s >>> 27;
            return s * 2685821657736338717L;
        }

        public int suivant(int max) {
            return max <= 1 ? 0 : (int) Long.remainderUnsigned(brut(), max);
        }

        public int entre(int min, int max) {
            return min >= max ? min : min + suivant(max - min + 1);
        }
    }

    /** 4 caractères tirés de l'identifiant (FNV-1a 64 bits, 24 bits gardés) : ce qui voyage dans les messages. */
    public static String code(String id) {
        long h = Hasard.graine(id);
        char[] c = new char[4];
        for (int i = 0; i < 4; i++) c[i] = ALPHABET64.charAt((int) ((h >>> (6 * i)) & 63));
        return new String(c);
    }

    /** Le n-ième tirage d'une partie (hasard, duree_max, épreuve « des ») : il ne dépend que de la graine et de n. */
    public static Hasard tirage(String graine, int n) {
        return new Hasard(Hasard.graine("campagne|" + graine + "|" + n));
    }

    private static int borne(int v, int min, int max) {
        return Math.max(min, Math.min(max, v));
    }

    /** Chance de réussir une épreuve au dé, en % : 70, 55, 40 selon la difficulté, ± 5 par point de la variable bonus. */
    public static int chanceDe(int difficulte, int bonus) {
        return borne(85 - 15 * borne(difficulte, 1, 3) + 5 * borne(bonus, -20, 20), 10, 95);
    }

    public static boolean jeuAuto(String jeu) {
        return jeu.equals("des") || !JEUX.contains(jeu);
    }

    private static long seconde(long ms) {
        return ms - ms % 1000;
    }

    // ---- Lecture des fichiers (mêmes tolérances que le PC : un champ du mauvais type vaut son défaut)

    private static String s(JSONObject o, String cle, String defaut) {
        Object v = o == null ? null : o.opt(cle);
        return v instanceof String ? (String) v : defaut;
    }

    private static String s(JSONObject o, String cle) {
        return s(o, cle, "");
    }

    private static Integer entier(Object v) {
        return v instanceof Integer ? (Integer) v : null;
    }

    private static int n(JSONObject o, String cle, int defaut) {
        Integer v = o == null ? null : entier(o.opt(cle));
        return v == null ? defaut : v;
    }

    private static long l(JSONObject o, String cle) {
        Object v = o == null ? null : o.opt(cle);
        return v instanceof Integer || v instanceof Long ? ((Number) v).longValue() : 0;
    }

    private static boolean b(JSONObject o, String cle, boolean defaut) {
        Object v = o == null ? null : o.opt(cle);
        return v instanceof Boolean ? (Boolean) v : defaut;
    }

    private static List<Object> liste(JSONObject o, String cle) {
        List<Object> r = new ArrayList<>();
        JSONArray a = o == null ? null : o.optJSONArray(cle);
        if (a != null) for (int i = 0; i < a.length(); i++) r.add(a.opt(i));
        return r;
    }

    private static JSONObject objet(Object v) {
        return v instanceof JSONObject ? (JSONObject) v : null;
    }

    private static Condition lireCondition(Object brut) {
        Condition c = new Condition();
        JSONObject v = objet(brut);
        if (v == null) return c;
        if (v.has("non")) {
            c.sorte = "non";
            c.sous.add(lireCondition(v.opt("non")));
        } else if (v.optJSONArray("tous") != null) {
            c.sorte = "tous";
            for (Object x : liste(v, "tous")) c.sous.add(lireCondition(x));
        } else if (v.optJSONArray("un") != null) {
            c.sorte = "un";
            for (Object x : liste(v, "un")) c.sous.add(lireCondition(x));
        } else if (!s(v, "var").isEmpty()) {
            c.sorte = "var";
            c.nom = s(v, "var");
            c.min = entier(v.opt("min"));
            c.max = entier(v.opt("max"));
            if (c.min == null && c.max == null) c.min = 1;
        } else if (!s(v, "objet").isEmpty()) {
            c.sorte = "objet";
            c.nom = s(v, "objet");
        } else if (!s(v, "drapeau").isEmpty()) {
            c.sorte = "drapeau";
            c.nom = s(v, "drapeau");
        }
        return c;
    }

    private static Condition lireSi(JSONObject o) {
        return o != null && o.has("si") ? lireCondition(o.opt("si")) : null;
    }

    private static List<Effet> lireEffets(JSONObject o) {
        List<Effet> r = new ArrayList<>();
        for (Object x : liste(o, "effets")) {
            JSONObject e = objet(x);
            if (e == null) continue;
            if (!s(e, "var").isEmpty()) r.add(new Effet("var", s(e, "var"), n(e, "plus", 0)));
            else if (!s(e, "objet").isEmpty()) r.add(new Effet("objet", s(e, "objet"), b(e, "donne", true) ? 1 : 0));
            else if (!s(e, "drapeau").isEmpty()) r.add(new Effet("drapeau", s(e, "drapeau"), b(e, "ote", false) ? 0 : 1));
        }
        return r;
    }

    private static Prime lirePrime(JSONObject o, String cle, boolean fin) {
        JSONObject r = o == null ? null : objet(o.opt(cle));
        if (r == null) return new Prime(0, 0, "", "", "");
        int po = Math.max(0, n(r, "po", 0)), xp = Math.max(0, n(r, "xp", 0));
        return fin ? new Prime(po, xp, s(r, "souvenir"), s(r, "titre"), s(r, "objet")) : new Prime(po, xp, "", "", "");
    }

    private static List<Nomme> lireNommes(JSONObject o, String cle) {
        List<Nomme> r = new ArrayList<>();
        for (Object x : liste(o, cle)) {
            JSONObject e = objet(x);
            if (e != null && !s(e, "id").isEmpty()) r.add(new Nomme(s(e, "id"), s(e, "nom"), s(e, "texte", s(e, "description"))));
        }
        return r;
    }

    private static Noeud lireNoeud(String id, String chapitre, JSONObject o) {
        Noeud n = new Noeud();
        n.id = id;
        n.chapitre = chapitre;
        n.type = s(o, "type");
        n.lieu = s(o, "lieu");
        n.humeur = s(o, "humeur", "neutre");
        if (!HUMEURS.contains(n.humeur)) n.humeur = "neutre";
        n.decor = s(o, "decor");
        n.suite = s(o, "suite");
        n.pendant = s(o, "pendant");
        n.tenue = s(o, "tenue");
        n.jeu = s(o, "jeu");
        n.bonus = s(o, "bonus");
        n.reussite = s(o, "reussite");
        n.echec = s(o, "echec");
        n.issue = s(o, "issue");
        n.titre = s(o, "titre");
        n.checkpoint = b(o, "checkpoint", false);
        n.effets = lireEffets(o);
        n.dureeMin = n(o, "duree_min", 0);
        n.dureeMax = n(o, "duree_max", 0);
        n.difficulte = n(o, "difficulte", 1);
        n.reposMin = n(o, "repos_min", 0);
        Object t = o.opt("texte");
        if (t instanceof String) n.texte.add((String) t);
        else if (t instanceof JSONArray)
            for (int i = 0; i < ((JSONArray) t).length(); i++)
                if (((JSONArray) t).opt(i) instanceof String) n.texte.add((String) ((JSONArray) t).opt(i));
        for (Object x : liste(o, "options")) {
            JSONObject e = objet(x);
            n.options.add(new Option(s(e, "id"), s(e, "libelle"), s(e, "vers"), lireSi(e), lireEffets(e)));
        }
        for (Object x : liste(o, "issues")) {
            JSONObject e = objet(x);
            n.issues.add(new IssueHasard(n(e, "poids", 1), s(e, "vers"), lireSi(e)));
        }
        // Un nœud ordinaire : « recompense » (po, xp). Une fin : « recompenses » (po, xp, souvenir, titre, objet).
        n.recompense = n.type.equals("fin") ? lirePrime(o, "recompenses", true) : lirePrime(o, "recompense", false);
        return n;
    }

    /** D'où vient le texte d'un fichier de chapitre (null : absent). */
    public interface Fichiers {
        String lire(String nom);
    }

    /** D'où viennent les campagnes (null : inconnue de cet appareil). */
    public interface Biblio {
        Campagne charger(String id);
    }

    /** La fiche (campagne.json) et ses chapitres ; null si la fiche est illisible. Un chapitre absent ou illisible est sauté. */
    public static Campagne lire(String fiche, Fichiers fichiers) {
        try {
            JSONObject r = new JSONObject(fiche);
            if (s(r, "id").isEmpty()) return null;
            Campagne c = new Campagne();
            c.id = s(r, "id");
            c.titre = s(r, "titre");
            c.ton = s(r, "ton");
            c.accroche = s(r, "accroche");
            c.duree = s(r, "duree");
            c.depart = s(r, "depart");
            c.niveau = Math.max(1, n(r, "niveau", 1));
            c.objets = lireNommes(r, "objets");
            c.souvenirs = lireNommes(r, "souvenirs");
            c.decors = lireNommes(r, "decors");
            JSONObject vars = objet(r.opt("variables"));
            if (vars != null)
                for (Iterator<String> i = vars.keys(); i.hasNext(); ) {
                    String cle = i.next();
                    Integer v = entier(vars.opt(cle));
                    c.variables.put(cle, v == null ? 0 : v);
                }
            for (Object x : liste(r, "chapitres")) {
                JSONObject e = objet(x);
                Chapitre ch = new Chapitre(s(e, "id"), s(e, "titre"), s(e, "fichier"));
                c.chapitres.add(ch);
                String texte = fichiers.lire(ch.fichier);
                if (texte == null) continue;
                try {
                    JSONObject noeuds = objet(new JSONObject(texte).opt("noeuds"));
                    if (noeuds == null) continue;
                    for (Iterator<String> i = noeuds.keys(); i.hasNext(); ) {
                        String id = i.next();
                        JSONObject o = objet(noeuds.opt(id));
                        if (o != null && !c.noeuds.containsKey(id)) c.noeuds.put(id, lireNoeud(id, ch.id, o));
                    }
                } catch (JSONException illisible) {
                    // chapitre illisible : sauté
                }
            }
            c.indexer();
            return c;
        } catch (JSONException e) {
            return null;
        }
    }

    // ---- Bibliothèque : les campagnes embarquées (ressources Java /campagnes/<id>/<fichier>, index /campagnes/index.txt)

    private static final Map<String, Campagne> CACHE = new HashMap<>();

    static String ressource(String chemin) {
        try (InputStream in = Campagnes.class.getResourceAsStream(chemin)) {
            if (in == null) return null;
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] tampon = new byte[8192];
            int lu;
            while ((lu = in.read(tampon)) > 0) out.write(tampon, 0, lu);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            return null;
        }
    }

    /** Index des campagnes disponibles (ids, triés). L'index est écrit à la compilation (android/app/build.gradle). */
    public static List<String> disponibles() {
        TreeSet<String> ids = new TreeSet<>();
        String index = ressource("/campagnes/index.txt");
        if (index != null)
            for (String ligne : index.replace("\r", "").split("\n"))
                if (!ligne.trim().isEmpty() && !ligne.startsWith("#")) ids.add(ligne.trim());
        return new ArrayList<>(ids);
    }

    public static synchronized Campagne charger(String id) {
        if (CACHE.containsKey(id)) return CACHE.get(id);
        Campagne c = null;
        if (idValide(id)) {
            String fiche = ressource("/campagnes/" + id + "/campagne.json");
            c = fiche == null ? null : lire(fiche, f -> ressource("/campagnes/" + id + "/" + f));
            if (c != null && !c.id.equals(id)) c = null;
        }
        CACHE.put(id, c);
        return c;
    }

    // ---- Partie : un résumé d'état (la base) et les décisions prises depuis

    /** Une décision. e : étape ; t : heure (ms, à la seconde) ; a : appareil ; n : code du nœud ; v : option ou SUITE… */
    public static final class Entree {
        public final int e, v;
        public final long t;
        public final String a, n;

        public Entree(int e, long t, String a, String n, int v) {
            this.e = e;
            this.t = t;
            this.a = a;
            this.n = n;
            this.v = v;
        }

        int comparer(Entree x) {
            if (e != x.e) return Integer.compare(e, x.e);
            if (t != x.t) return Long.compare(t, x.t);
            int c = a.compareTo(x.a);
            if (c != 0) return c;
            c = n.compareTo(x.n);
            return c != 0 ? c : Integer.compare(v, x.v);
        }
    }

    /** État à un point de l'histoire, en codes : nœud, variables (≠ valeur de départ), objets, drapeaux, décor, nœud du lieu. */
    public static final class Instantane {
        public String n = "", decor = "", lieu = "";
        public final TreeMap<String, Integer> v = new TreeMap<>();
        public List<String> o = new ArrayList<>(), d = new ArrayList<>();

        Instantane copie() {
            Instantane x = new Instantane();
            x.n = n;
            x.decor = decor;
            x.lieu = lieu;
            x.v.putAll(v);
            x.o = new ArrayList<>(o);
            x.d = new ArrayList<>(d);
            return x;
        }
    }

    public static final class Partie {
        /** Identité : campagne, numéro de partie, heure de départ (ms), appareil d'origine, graine. */
        public String campagne = "", o = "", graine = "";
        public int p;
        public long d;
        /** Campagne déjà finie une fois quand la partie a commencé : ni po ni xp. */
        public boolean rejeu;
        /** Base : décisions consommées, rang, messages déjà émis dans l'étape, tirages faits, curseur de temps (ms). */
        public int e, r, i, tirages;
        public long t;
        public boolean geste, entre, abandonnee;
        public Instantane ici = new Instantane();
        /** Dernier check-point (null : c'est « ici », pas encore entré). */
        public Instantane cp;
        public List<Entree> journal = new ArrayList<>();

        public Partie copie() {
            Partie q = new Partie();
            q.campagne = campagne;
            q.p = p;
            q.d = d;
            q.o = o;
            q.graine = graine;
            q.rejeu = rejeu;
            q.e = e;
            q.r = r;
            q.i = i;
            q.tirages = tirages;
            q.t = t;
            q.geste = geste;
            q.entre = entre;
            q.abandonnee = abandonnee;
            q.ici = ici.copie();
            q.cp = cp == null ? null : cp.copie();
            q.journal = new ArrayList<>(journal);
            return q;
        }
    }

    /** Un message du fil : Pilou (« pilou ») ou le choix du joueur (« joueur »). Clé stable : partie, étape, rang. */
    public static final class Message {
        public final int p, e, i;
        public final String qui, texte, noeud, lieu, humeur, decor;
        public final long t;

        public Message(int p, int e, int i, String qui, String texte, String noeud, String lieu, String humeur, String decor, long t) {
            this.p = p;
            this.e = e;
            this.i = i;
            this.qui = qui;
            this.texte = texte;
            this.noeud = noeud;
            this.lieu = lieu;
            this.humeur = humeur;
            this.decor = decor;
            this.t = t;
        }
    }

    /** Point où la base peut avancer. mur : heure de la dernière décision qui y mène. naturel : check-point ou abandon. */
    static final class Point {
        final Partie base;
        final long mur;
        final boolean naturel;

        Point(Partie base, long mur, boolean naturel) {
            this.base = base;
            this.mur = mur;
            this.naturel = naturel;
        }
    }

    public static final class OptionVue {
        public final int rang;
        public final String id, libelle;

        OptionVue(int rang, String id, String libelle) {
            this.rang = rang;
            this.id = id;
            this.libelle = libelle;
        }
    }

    /** Ce que l'interface affiche. */
    public static final class Etat {
        public Phase phase = Phase.Aucune;
        public String campagne = "", noeud = "", lieu = "", decor = "", humeur = "neutre", chapitre = "", chapitreTitre = "";
        public int chapitreNumero, chapitreTotal;
        public double progression;
        /** Prochaine étape, tirages faits, curseur de temps, fin de l'attente ou du repos (0 : aucune), en ms. */
        public int e, tirages;
        public long t, fin;
        public String pendant = "", tenue = "";
        public final List<OptionVue> options = new ArrayList<>();
        public String jeu = "";
        public int difficulte, aide, chance;
        public final TreeMap<String, Integer> variables = new TreeMap<>();
        public List<String> objets = new ArrayList<>(), drapeaux = new ArrayList<>();
        /** Messages émis depuis la base (le fil complet est dans le carnet), nœuds à récompense franchis, fin obtenue. */
        public List<Message> messages = new ArrayList<>();
        public List<String> credits = new ArrayList<>();
        public String issue = "", titreFin = "";
        public Prime recompenses = new Prime(0, 0, "", "", "");
        public boolean rejeu;
        List<Point> points = new ArrayList<>();

        public boolean enAttente() {
            return phase == Phase.Attente || phase == Phase.Repos;
        }

        public boolean enCours() {
            return phase == Phase.Choix || phase == Phase.Epreuve || phase == Phase.Depart || enAttente();
        }

        /** Texte canonique (une ligne), pour les vecteurs partagés avec le PC. */
        public String texte() {
            long h = 0xcbf29ce484222325L;
            for (Message m : messages) {
                String s = m.e + "." + m.i + "." + m.qui + "." + m.noeud + "." + m.humeur + "." + m.decor + "." + m.lieu + "." + m.t + "." + m.texte + "\n";
                for (int k = 0; k < s.length(); k++) {
                    h ^= s.charAt(k);
                    h *= 0x100000001b3L;
                }
            }
            List<String> o = new ArrayList<>(), v = new ArrayList<>();
            for (OptionVue x : options) o.add(x.rang + ":" + x.id);
            for (Map.Entry<String, Integer> kv : variables.entrySet()) v.add(kv.getKey() + ":" + kv.getValue());
            return String.join("|", Arrays.asList(
                    "phase=" + phase.name(), "noeud=" + noeud, "e=" + e, "t=" + t, "fin=" + fin, "tirages=" + tirages,
                    "chapitre=" + chapitre + ":" + chapitreNumero + "/" + chapitreTotal,
                    "lieu=" + lieu, "decor=" + decor, "humeur=" + humeur, "pendant=" + pendant, "tenue=" + tenue,
                    "options=" + String.join(",", o),
                    "jeu=" + jeu + ":" + difficulte + ":" + aide + ":" + chance,
                    "vars=" + String.join(",", v),
                    "objets=" + String.join(",", objets), "drapeaux=" + String.join(",", drapeaux),
                    "credits=" + String.join(",", credits), "issue=" + issue + ":" + recompenses.po + ":" + recompenses.xp,
                    "messages=" + messages.size() + ":" + String.format(Locale.ROOT, "%016x", h)));
        }
    }

    // ---- Rejeu

    private static final class Cours {
        String noeud = "", decor = "", lieuDe = "";
        TreeMap<String, Integer> vars = new TreeMap<>();
        TreeSet<String> objets = new TreeSet<>(), drapeaux = new TreeSet<>();
        boolean avecCp;
        String cpNoeud = "", cpDecor = "", cpLieuDe = "";
        TreeMap<String, Integer> cpVars = new TreeMap<>();
        TreeSet<String> cpObjets = new TreeSet<>(), cpDrapeaux = new TreeSet<>();
        int e, r, i, tirages, pas;
        long t, fin, mur = Long.MIN_VALUE;
        boolean geste;
        Phase phase = Phase.Aucune;
        List<Message> messages = new ArrayList<>();
        List<String> credits = new ArrayList<>();
        List<Point> points = new ArrayList<>();

        Cours copie() {
            Cours x = new Cours();
            x.noeud = noeud;
            x.decor = decor;
            x.lieuDe = lieuDe;
            x.vars = new TreeMap<>(vars);
            x.objets = new TreeSet<>(objets);
            x.drapeaux = new TreeSet<>(drapeaux);
            x.avecCp = avecCp;
            x.cpNoeud = cpNoeud;
            x.cpDecor = cpDecor;
            x.cpLieuDe = cpLieuDe;
            x.cpVars = new TreeMap<>(cpVars);
            x.cpObjets = new TreeSet<>(cpObjets);
            x.cpDrapeaux = new TreeSet<>(cpDrapeaux);
            x.e = e;
            x.r = r;
            x.i = i;
            x.tirages = tirages;
            x.pas = pas;
            x.t = t;
            x.fin = fin;
            x.mur = mur;
            x.geste = geste;
            x.phase = phase;
            x.messages = new ArrayList<>(messages);
            x.credits = new ArrayList<>(credits);
            x.points = new ArrayList<>(points);
            return x;
        }

        int var(String nom) {
            Integer v = vars.get(nom);
            return v == null ? 0 : v;
        }
    }

    private static final int NEUF = 0, REPRIS = 1, SUIVI = 2;

    private static final class Moteur {
        private final Campagne c;
        private final Partie p;

        Moteur(Campagne c, Partie p) {
            this.c = c;
            this.p = p;
        }

        boolean vrai(Condition k, Cours s) {
            if (k == null) return true;
            switch (k.sorte) {
                case "var": {
                    int v = s.var(k.nom);
                    return (k.min == null || v >= k.min) && (k.max == null || v <= k.max);
                }
                case "objet": return s.objets.contains(k.nom);
                case "drapeau": return s.drapeaux.contains(k.nom);
                case "non": return k.sous.size() == 1 && !vrai(k.sous.get(0), s);
                case "tous":
                    for (Condition x : k.sous) if (!vrai(x, s)) return false;
                    return true;
                case "un":
                    for (Condition x : k.sous) if (vrai(x, s)) return true;
                    return false;
                default: return false;
            }
        }

        static void appliquer(List<Effet> effets, Cours s) {
            for (Effet e : effets) {
                if (e.sorte.equals("var")) s.vars.put(e.nom, s.var(e.nom) + e.valeur);
                else if (e.sorte.equals("objet")) {
                    if (e.valeur != 0) s.objets.add(e.nom);
                    else s.objets.remove(e.nom);
                } else if (e.sorte.equals("drapeau")) {
                    if (e.valeur != 0) s.drapeaux.add(e.nom);
                    else s.drapeaux.remove(e.nom);
                }
            }
        }

        /** Instantané (en codes) d'un état, prêt à entrer dans le nœud donné. */
        Instantane photo(String noeud, TreeMap<String, Integer> vars, TreeSet<String> objets, TreeSet<String> drapeaux, String decor, String lieuDe) {
            Instantane x = new Instantane();
            x.n = code(noeud);
            x.decor = decor.isEmpty() ? "" : code(decor);
            x.lieu = lieuDe.isEmpty() ? "" : code(lieuDe);
            for (Map.Entry<String, Integer> kv : vars.entrySet()) {
                Integer depart = c.variables.get(kv.getKey());
                if (kv.getValue() != (depart == null ? 0 : depart)) x.v.put(code(kv.getKey()), kv.getValue());
            }
            for (String o : objets) x.o.add(code(o));
            for (String d : drapeaux) x.d.add(code(d));
            Collections.sort(x.o);
            Collections.sort(x.d);
            return x;
        }

        Instantane photoCp(Cours s) {
            return photo(s.cpNoeud, s.cpVars, s.cpObjets, s.cpDrapeaux, s.cpDecor, s.cpLieuDe);
        }

        Partie base(Cours s, Instantane ici, Instantane cp, int i, boolean entre, boolean abandonnee) {
            Partie q = new Partie();
            q.campagne = p.campagne;
            q.p = p.p;
            q.d = p.d;
            q.o = p.o;
            q.graine = p.graine;
            q.rejeu = p.rejeu;
            q.e = s.e;
            q.r = s.r;
            q.i = i;
            q.tirages = s.tirages;
            q.t = s.t;
            q.geste = s.geste;
            q.entre = entre;
            q.abandonnee = abandonnee;
            q.ici = ici;
            q.cp = cp;
            return q;
        }

        void charger(Instantane x, Cours s, boolean cp) {
            TreeMap<String, Integer> vars = new TreeMap<>(c.variables);
            for (Map.Entry<String, Integer> kv : x.v.entrySet()) {
                String id = c.decode('v', kv.getKey());
                if (id != null) vars.put(id, kv.getValue());
            }
            TreeSet<String> objets = new TreeSet<>(), drapeaux = new TreeSet<>();
            for (String k : x.o) {
                String id = c.decode('o', k);
                if (id != null) objets.add(id);
            }
            for (String k : x.d) {
                String id = c.decode('d', k);
                if (id != null) drapeaux.add(id);
            }
            String decor = x.decor.isEmpty() ? null : c.decode('c', x.decor), lieu = x.lieu.isEmpty() ? null : c.decode('n', x.lieu);
            String noeud = c.decode('n', x.n);
            if (cp) {
                s.avecCp = true;
                s.cpNoeud = noeud == null ? "" : noeud;
                s.cpVars = vars;
                s.cpObjets = objets;
                s.cpDrapeaux = drapeaux;
                s.cpDecor = decor == null ? "" : decor;
                s.cpLieuDe = lieu == null ? "" : lieu;
            } else {
                s.noeud = noeud == null ? "" : noeud;
                s.vars = vars;
                s.objets = objets;
                s.drapeaux = drapeaux;
                s.decor = decor == null ? "" : decor;
                s.lieuDe = lieu == null ? "" : lieu;
            }
        }

        String lieu(Cours s) {
            Noeud n = s.lieuDe.isEmpty() ? null : c.noeud(s.lieuDe);
            return n == null ? "" : n.lieu;
        }

        void dire(Cours s, String qui, String texte, Noeud n) {
            s.messages.add(new Message(p.p, s.e, s.i++, qui, texte, n.id, lieu(s), qui.equals("pilou") ? n.humeur : "neutre", s.decor, s.t));
        }

        boolean lancerDe(Cours s, Noeud n) {
            return tirage(p.graine, s.tirages).suivant(100) < chanceDe(n.difficulte, n.bonus.isEmpty() ? 0 : s.var(n.bonus));
        }

        void partir(Cours s, Noeud n) {
            int minutes = Math.max(1, n.dureeMin);
            if (n.dureeMax > n.dureeMin) minutes = tirage(p.graine, s.tirages++).entre(Math.max(1, n.dureeMin), n.dureeMax);
            s.fin = s.t + minutes * 60_000L;
            s.phase = Phase.Attente;
        }

        /** Entre dans un nœud et suit les nœuds automatiques jusqu'à un arrêt (décision, attente, repos, fin). */
        void entrer(Cours s, String id, int mode) {
            while (true) {
                Noeud n = c.noeud(id);
                if (++s.pas > MAX_PAS || n == null) {
                    s.phase = Phase.Cassee;
                    return;
                }
                s.noeud = id;
                int avant = s.i;
                if (mode == NEUF) {
                    if (n.checkpoint || !s.avecCp) {
                        s.avecCp = true;
                        s.cpNoeud = id;
                        s.cpVars = new TreeMap<>(s.vars);
                        s.cpObjets = new TreeSet<>(s.objets);
                        s.cpDrapeaux = new TreeSet<>(s.drapeaux);
                        s.cpDecor = s.decor;
                        s.cpLieuDe = s.lieuDe;
                        if (n.checkpoint) s.points.add(new Point(base(s, photoCp(s), null, s.i, false, false), s.mur, true));
                        if (n.checkpoint) s.r++;
                    }
                    if (!n.decor.isEmpty()) s.decor = n.decor;
                    if (!n.lieu.isEmpty()) s.lieuDe = id;
                    appliquer(n.effets, s);
                    if ((n.type.equals("fin") || !n.recompense.vide()) && !s.credits.contains(id)) s.credits.add(id);
                }
                if (mode != SUIVI) for (String t : n.texte) dire(s, "pilou", t, n);
                switch (n.type) {
                    case "recit":
                        id = n.suite;
                        mode = NEUF;
                        continue;
                    case "choix":
                        s.phase = Phase.Choix;
                        break;
                    case "attente":
                        if (!s.geste) s.phase = Phase.Depart;
                        else {
                            partir(s, n);
                            return;
                        }
                        break;
                    case "epreuve":
                        if (jeuAuto(n.jeu)) {
                            boolean ok = lancerDe(s, n);
                            s.tirages++;
                            id = ok ? n.reussite : n.echec;
                            mode = NEUF;
                            continue;
                        }
                        s.phase = Phase.Epreuve;
                        break;
                    case "hasard": {
                        List<IssueHasard> possibles = new ArrayList<>();
                        for (IssueHasard x : n.issues) if (vrai(x.si, s)) possibles.add(x);
                        if (possibles.isEmpty()) possibles = n.issues;
                        if (possibles.isEmpty()) {
                            s.phase = Phase.Cassee;
                            return;
                        }
                        int total = 0;
                        for (IssueHasard x : possibles) total += Math.max(1, x.poids);
                        int tire = tirage(p.graine, s.tirages++).suivant(total);
                        IssueHasard issue = possibles.get(possibles.size() - 1);
                        for (IssueHasard x : possibles) {
                            tire -= Math.max(1, x.poids);
                            if (tire < 0) {
                                issue = x;
                                break;
                            }
                        }
                        id = issue.vers;
                        mode = NEUF;
                        continue;
                    }
                    case "echec":
                        s.fin = s.t + Math.max(1, n.reposMin) * 60_000L;
                        s.phase = Phase.Repos;
                        return;
                    case "fin":
                        s.phase = Phase.Fin;
                        return;
                    default:
                        s.phase = Phase.Cassee;
                        return;
                }
                // Arrêt sur une décision : un point de secours (base au milieu d'un chapitre, si le journal devient trop long).
                s.points.add(new Point(base(s, photo(s.noeud, s.vars, s.objets, s.drapeaux, s.decor, s.lieuDe), photoCp(s), avant, true, false), s.mur, false));
                return;
            }
        }

        /** L'attente ou le repos est fini : Pilou revient (ou repart du dernier check-point). */
        void ecouler(Cours s) {
            Noeud n = c.noeud(s.noeud);
            s.t = s.fin;
            s.fin = 0;
            s.geste = false;
            if (s.phase == Phase.Attente) entrer(s, n.suite, NEUF);
            else {
                s.vars = new TreeMap<>(s.cpVars);
                s.objets = new TreeSet<>(s.cpObjets);
                s.drapeaux = new TreeSet<>(s.cpDrapeaux);
                s.decor = s.cpDecor;
                s.lieuDe = s.cpLieuDe;
                entrer(s, s.cpNoeud, NEUF);
            }
        }

        boolean valide(Cours s, Entree x) {
            if (!x.n.equals(code(s.noeud))) return false;
            switch (s.phase) {
                case Choix: {
                    Noeud n = c.noeud(s.noeud);
                    return x.v == ABANDON || (x.v >= 0 && x.v < n.options.size() && vrai(n.options.get(x.v).si, s));
                }
                case Epreuve: return x.v == REUSSITE || x.v == RATE || x.v == ABANDON;
                case Depart: return x.v == SUITE || x.v == ABANDON;
                case Attente:
                case Repos: return x.v == ABANDON && x.t < s.fin;
                default: return false;
            }
        }

        Entree premierValide(Cours s, List<Entree> candidats) {
            for (Entree x : candidats) if (valide(s, x)) return x;
            return null;
        }

        void decider(Cours s, Entree x) {
            Noeud n = c.noeud(s.noeud);
            Phase phase = s.phase;
            s.t = Math.max(s.t, x.t);
            s.mur = x.t;
            s.e++;
            s.i = 0;
            s.fin = 0;
            if (x.v == ABANDON) {
                s.phase = Phase.Abandon;
                s.points.add(new Point(base(s, photoCp(s), null, 0, false, true), s.mur, true));
                return;
            }
            s.geste = true;
            switch (phase) {
                case Choix: {
                    Option o = n.options.get(x.v);
                    dire(s, "joueur", o.libelle, n);
                    appliquer(o.effets, s);
                    entrer(s, o.vers, NEUF);
                    break;
                }
                case Epreuve:
                    s.tirages++;
                    entrer(s, x.v == REUSSITE ? n.reussite : n.echec, NEUF);
                    break;
                case Depart:
                    partir(s, n);
                    break;
                default:
                    break;
            }
        }

        static boolean timer(Cours s) {
            return s.phase == Phase.Attente || s.phase == Phase.Repos;
        }

        static boolean terminal(Cours s) {
            return s.phase == Phase.Fin || s.phase == Phase.Abandon || s.phase == Phase.Cassee || s.phase == Phase.Aucune;
        }

        Cours jouer(long maintenant) {
            Cours s = new Cours();
            s.e = p.e;
            s.r = p.r;
            s.i = p.i;
            s.tirages = p.tirages;
            s.t = p.t;
            s.geste = p.geste;
            charger(p.ici, s, false);
            if (p.cp != null) charger(p.cp, s, true);
            if (p.abandonnee) {
                // Base d'une partie abandonnée : « ici » est le check-point où elle reprendra.
                charger(p.ici, s, true);
                s.phase = Phase.Abandon;
                return s;
            }
            if (s.noeud.isEmpty() || c.noeud(s.noeud) == null) {
                s.phase = Phase.Cassee;
                return s;
            }
            entrer(s, s.noeud, p.entre ? REPRIS : NEUF);

            Map<Integer, List<Entree>> parEtape = new HashMap<>();
            for (Entree x : ordonner(p.journal)) {
                List<Entree> l = parEtape.get(x.e);
                if (l == null) parEtape.put(x.e, l = new ArrayList<>());
                l.add(x);
            }
            List<Entree> aucun = new ArrayList<>();
            while (!terminal(s)) {
                List<Entree> candidats = parEtape.containsKey(s.e) ? parEtape.get(s.e) : aucun;
                Entree v = premierValide(s, candidats);
                if (!timer(s)) {
                    if (v == null) break;
                    decider(s, v);
                    continue;
                }
                if (v != null) {
                    decider(s, v); // abandon pendant l'attente
                    continue;
                }
                if (maintenant >= s.fin) {
                    ecouler(s);
                    continue;
                }
                // L'attente n'est pas finie ici, mais un autre appareil (horloge en avance) a peut-être déjà décidé la
                // suite : on regarde plus loin sans rien changer, et on n'y va que si une décision valide nous y attend.
                if (candidats.isEmpty()) break;
                Cours plus = s.copie();
                Entree trouve = null;
                while (timer(plus) && trouve == null) {
                    ecouler(plus);
                    if (terminal(plus)) break;
                    trouve = premierValide(plus, candidats);
                }
                if (trouve == null) break;
                s = plus;
                decider(s, trouve);
            }
            return s;
        }

        Etat vue(Cours s) {
            Etat e = new Etat();
            e.phase = s.phase;
            e.campagne = c.id;
            e.noeud = s.noeud;
            e.lieu = lieu(s);
            e.decor = s.decor;
            e.e = s.e;
            e.tirages = s.tirages;
            e.t = s.t;
            e.fin = timer(s) ? s.fin : 0;
            e.messages = s.messages;
            e.credits = s.credits;
            e.points = s.points;
            e.rejeu = p.rejeu;
            e.chapitreTotal = c.chapitres.size();
            e.variables.putAll(s.vars);
            e.objets = new ArrayList<>(s.objets);
            e.drapeaux = new ArrayList<>(s.drapeaux);
            Noeud n = c.noeud(s.noeud);
            if (n == null) return e;
            e.humeur = n.humeur;
            e.chapitre = n.chapitre;
            int rang = -1;
            for (int i = 0; i < c.chapitres.size() && rang < 0; i++) if (c.chapitres.get(i).id.equals(n.chapitre)) rang = i;
            e.chapitreNumero = rang + 1;
            e.chapitreTitre = rang >= 0 ? c.chapitres.get(rang).titre : "";
            e.progression = s.phase == Phase.Fin ? 1 : c.chapitres.isEmpty() ? 0 : Math.max(0, rang) / (double) c.chapitres.size();
            switch (s.phase) {
                case Choix:
                    for (int i = 0; i < n.options.size(); i++)
                        if (vrai(n.options.get(i).si, s)) e.options.add(new OptionVue(i, n.options.get(i).id, n.options.get(i).libelle));
                    break;
                case Epreuve:
                    e.jeu = n.jeu;
                    e.difficulte = borne(n.difficulte, 1, 3);
                    e.aide = n.bonus.isEmpty() ? 0 : s.var(n.bonus);
                    e.chance = chanceDe(n.difficulte, e.aide);
                    break;
                case Depart:
                case Attente:
                    e.pendant = n.pendant;
                    e.tenue = TENUES.contains(n.tenue) ? n.tenue : "marche";
                    break;
                case Repos:
                    e.pendant = "Pilou se repose";
                    e.tenue = "nuit";
                    break;
                case Fin:
                    e.issue = n.issue;
                    e.titreFin = n.titre;
                    e.recompenses = n.recompense;
                    break;
                default:
                    break;
            }
            return e;
        }
    }

    /** Ordre canonique des décisions : étape, heure, appareil, nœud, valeur. Doublons retirés. */
    public static List<Entree> ordonner(List<Entree> journal) {
        List<Entree> l = new ArrayList<>(journal);
        Collections.sort(l, Entree::comparer);
        List<Entree> r = new ArrayList<>();
        for (Entree x : l) if (r.isEmpty() || r.get(r.size() - 1).comparer(x) != 0) r.add(x);
        return r;
    }

    /** Journal borné : à partir de l'étape de la base, au plus MAX_PAR_ETAPE décisions par étape (les plus anciennes). */
    private static List<Entree> borner(List<Entree> journal, int depuis) {
        List<Entree> r = new ArrayList<>();
        int etape = Integer.MIN_VALUE, n = 0;
        for (Entree x : ordonner(journal)) {
            if (x.e < depuis || x.e > depuis + MAX_AVANCE) continue;
            if (x.e != etape) {
                etape = x.e;
                n = 0;
            }
            if (++n <= MAX_PAR_ETAPE) r.add(x);
        }
        return r;
    }

    /** L'état d'une partie à l'heure donnée (ms) : pur, même résultat partout. */
    public static Etat rejouer(Campagne c, Partie p, long maintenant) {
        Moteur m = new Moteur(c, p);
        return m.vue(m.jouer(maintenant));
    }

    /** Nouvelle partie, au nœud de départ. p : numéro de partie (plus grand que tous ceux connus du groupe). */
    public static Partie nouvelle(Campagne c, int p, long maintenant, String appareil, String graine, boolean rejeu) {
        Partie q = new Partie();
        q.campagne = c.id;
        q.p = p;
        q.d = q.t = seconde(maintenant);
        q.o = appareil;
        q.graine = graine;
        q.rejeu = rejeu;
        q.geste = true;
        q.ici.n = code(c.depart);
        return q;
    }

    /** Ajoute une décision au journal si elle est valide maintenant ; null sinon (rien ne change). */
    public static Partie decider(Campagne c, Partie p, long maintenant, String appareil, int valeur) {
        Moteur m = new Moteur(c, p);
        Cours s = m.jouer(maintenant);
        Entree x = new Entree(s.e, seconde(maintenant), appareil, code(s.noeud), valeur);
        if (!m.valide(s, x)) return null;
        Partie q = p.copie();
        q.journal.add(x);
        q.journal = borner(q.journal, q.e);
        return q;
    }

    /** Le tirage « des » qui remplace un mini-jeu que l'appareil ne sait pas jouer (même résultat partout). */
    public static boolean deDe(Partie p, Etat e) {
        return tirage(p.graine, e.tirages).suivant(100) < chanceDe(e.difficulte, e.aide);
    }

    /** Avance la base : au dernier check-point (ou abandon) mûr, ou au milieu d'un chapitre si le journal est trop long. */
    public static Partie compacter(Campagne c, Partie p, long maintenant) {
        Etat e = rejouer(c, p, maintenant);
        Point choisi = null;
        for (Point pt : e.points) if (pt.naturel && pt.mur <= maintenant - GRACE) choisi = pt;
        if (e.e - (choisi == null ? p.e : choisi.base.e) > MAX_ENTREES)
            for (Point pt : e.points)
                if (e.e - pt.base.e <= GARDE_ENTREES) {
                    choisi = pt;
                    break;
                }
        Partie q = choisi == null || !avance(choisi.base, p) ? p.copie() : choisi.base.copie();
        q.journal = borner(p.journal, q.e);
        return q;
    }

    // ---- Comparaisons et fusion (sans les fichiers de campagne : tout est en codes)

    private static int compareIdentite(Partie a, Partie b) {
        if (a.p != b.p) return Integer.compare(b.p, a.p);          // le plus grand numéro d'abord
        if (a.d != b.d) return Long.compare(a.d, b.d);             // puis la plus ancienne
        int c = a.o.compareTo(b.o);
        if (c != 0) return c;
        c = a.campagne.compareTo(b.campagne);
        return c != 0 ? c : a.graine.compareTo(b.graine);
    }

    /** &lt; 0 : la base de a est préférée (plus avancée ; à égalité la plus ancienne, puis l'ordre du texte). */
    private static int compareBase(Partie a, Partie b) {
        if (a.e != b.e) return Integer.compare(b.e, a.e);
        if (a.r != b.r) return Integer.compare(b.r, a.r);
        if (a.t != b.t) return Long.compare(a.t, b.t);
        return jsonPartie(a, false).compareTo(jsonPartie(b, false));
    }

    private static boolean avance(Partie a, Partie b) {
        return compareBase(a, b) < 0;
    }

    /** Deux vues de la même partie : la meilleure base, l'union des décisions. */
    private static Partie unir(Partie a, Partie b) {
        Partie q = (compareBase(a, b) <= 0 ? a : b).copie();
        List<Entree> tout = new ArrayList<>(a.journal);
        tout.addAll(b.journal);
        q.journal = borner(tout, q.e);
        return q;
    }

    /** La partie qui fait foi entre deux (null : absente). */
    private static Partie meilleure(Partie a, Partie b) {
        if (a == null) return b == null ? null : b.copie();
        if (b == null) return a.copie();
        int c = compareIdentite(a, b);
        return c == 0 ? unir(a, b) : c < 0 ? a.copie() : b.copie();
    }

    // ---- Carnet : ce qu'un appareil garde

    /** Bilan d'une campagne dans le groupe : dernière partie commencée, dernière partie finie, fins (code → secondes), nœuds acquis. */
    public static final class Bilan {
        public int p, finie;
        public final TreeMap<String, Long> fins = new TreeMap<>();
        public final TreeSet<String> noeuds = new TreeSet<>();
    }

    public static final class Carnet {
        public Partie courante;
        public final TreeMap<String, Partie> suspendues = new TreeMap<>();
        public final TreeMap<String, Bilan> historique = new TreeMap<>();
        /** Propre à l'appareil : le fil (les MAX_FIL derniers messages), la clé du dernier message lu, ce qu'un PC a déjà versé. */
        public final List<Message> fil = new ArrayList<>();
        public String lu = "";
        public final TreeSet<String> payesPc = new TreeSet<>();

        public int nonLus() {
            int n = 0;
            for (Message m : fil) if (m.qui.equals("pilou") && apresLu(m, lu)) n++;
            return n;
        }
    }

    private static boolean apresLu(Message m, String lu) {
        String[] c = lu.split("\\.");
        if (c.length != 3) return true;
        try {
            int p = Integer.parseInt(c[0]), e = Integer.parseInt(c[1]), i = Integer.parseInt(c[2]);
            return m.p != p ? m.p > p : m.e != e ? m.e > e : m.i > i;
        } catch (NumberFormatException x) {
            return true;
        }
    }

    public static boolean nonLu(Carnet k, Message m) {
        return apresLu(m, k.lu);
    }

    public static void marquerLu(Carnet k) {
        if (k.fil.isEmpty()) return;
        Message m = k.fil.get(k.fil.size() - 1);
        k.lu = m.p + "." + m.e + "." + m.i;
    }

    private static Bilan bilanDe(Carnet k, String campagne) {
        Bilan b = k.historique.get(campagne);
        if (b == null) k.historique.put(campagne, b = new Bilan());
        return b;
    }

    private static int prochain(Carnet k) {
        int p = k.courante == null ? 0 : k.courante.p;
        for (Partie s : k.suspendues.values()) p = Math.max(p, s.p);
        for (Bilan b : k.historique.values()) p = Math.max(p, Math.max(b.p, b.finie));
        return p + 1;
    }

    /** Ce que la partie apporte à l'historique (récompenses acquises, fin obtenue). */
    private static void noter(Carnet k, Partie p, Etat e) {
        Bilan b = bilanDe(k, p.campagne);
        b.p = Math.max(b.p, p.p);
        if (!p.rejeu) for (String id : e.credits) b.noeuds.add(code(id));
        if (e.phase == Phase.Fin) {
            String code = code(e.noeud);
            long t = e.t / 1000;
            Long avant = b.fins.get(code);
            if (avant == null || t < avant) b.fins.put(code, t);
            b.finie = Math.max(b.finie, p.p);
        }
    }

    /** Parties suspendues périmées : remplacées par une partie plus récente de la même campagne, ou finie depuis. */
    private static void nettoyer(Carnet k) {
        if (k.courante != null) bilanDe(k, k.courante.campagne).p = Math.max(bilanDe(k, k.courante.campagne).p, k.courante.p);
        for (String id : new ArrayList<>(k.suspendues.keySet())) {
            Partie s = k.suspendues.get(id);
            Bilan b = bilanDe(k, id);
            b.p = Math.max(b.p, s.p);
            if (s.p < b.p || s.p <= b.finie || (k.courante != null && k.courante.campagne.equals(id) && compareIdentite(k.courante, s) <= 0))
                k.suspendues.remove(id);
        }
    }

    private static Partie dernierAbandon(Etat e) {
        Partie r = null;
        for (Point pt : e.points) if (pt.base.abandonnee) r = pt.base;
        return r;
    }

    /** La partie mise de côté : sa base au dernier check-point, marquée abandonnée (null : finie, rien à garder). */
    private static Partie suspendre(Carnet k, Partie p, Biblio biblio, long maintenant) {
        if (p.abandonnee && p.journal.isEmpty()) return p.copie();
        Campagne c = biblio.charger(p.campagne);
        if (c == null) return p.copie(); // campagne inconnue ici : gardée telle quelle
        Etat e = rejouer(c, p, maintenant);
        noter(k, p, e);
        if (e.phase == Phase.Fin || e.phase == Phase.Cassee) return null;
        Partie abandon = dernierAbandon(e);
        if (abandon != null) return abandon.copie();
        Partie q = decider(c, p, Math.max(maintenant, e.t), p.o, ABANDON);
        if (q == null) return p.copie();
        abandon = dernierAbandon(rejouer(c, q, maintenant));
        return abandon == null ? p.copie() : abandon.copie();
    }

    private static void ranger(Carnet k, Partie perdante, Biblio biblio, long maintenant) {
        Partie s = suspendre(k, perdante, biblio, maintenant);
        if (s != null) k.suspendues.put(s.campagne, meilleure(k.suspendues.get(s.campagne), s));
    }

    /**
     * À appeler régulièrement (et après chaque décision ou réception) : rejoue la partie en cours, note les récompenses
     * acquises dans l'historique, avance la base, complète le fil. Renvoie l'état (null : aucune partie, ou campagne
     * inconnue de cet appareil).
     */
    public static Etat actualiser(Carnet k, Biblio biblio, long maintenant) {
        nettoyer(k);
        Partie p = k.courante;
        Campagne c = p == null ? null : biblio.charger(p.campagne);
        if (c == null) return null;
        Etat e = rejouer(c, p, maintenant);
        noter(k, p, e);
        // Le fil : ce qui précède la base reste ; ce qui la suit est remplacé par le rejeu (une décision peut avoir perdu).
        for (Iterator<Message> i = k.fil.iterator(); i.hasNext(); ) {
            Message m = i.next();
            if (m.p == p.p && (m.e > p.e || (m.e == p.e && m.i >= p.i))) i.remove();
        }
        k.fil.addAll(e.messages);
        while (k.fil.size() > MAX_FIL) k.fil.remove(0);
        k.courante = compacter(c, p, maintenant);
        return e;
    }

    // ---- Décisions sur le carnet (ce qu'appelle l'interface). Chaque fonction renvoie null si c'est fait, sinon la raison.

    public static String nouvelleGraine() {
        StringBuilder b = new StringBuilder();
        java.security.SecureRandom r = new java.security.SecureRandom();
        for (int i = 0; i < 8; i++) b.append("0123456789abcdef".charAt(r.nextInt(16)));
        return b.toString();
    }

    public static boolean finie(Carnet k, String campagne) {
        Bilan b = k.historique.get(campagne);
        return b != null && !b.fins.isEmpty();
    }

    /** Une partie est-elle en cours (ni finie, ni abandonnée) ? */
    public static boolean enCours(Carnet k, Biblio biblio, long maintenant) {
        if (k.courante == null) return false;
        Campagne c = biblio.charger(k.courante.campagne);
        if (c == null) return !k.courante.abandonnee;
        return rejouer(c, k.courante, maintenant).enCours();
    }

    /** Peut-on reprendre cette campagne à un check-point (partie abandonnée ou mise de côté) ? */
    public static boolean reprenable(Carnet k, Campagne c, long maintenant) {
        return k.suspendues.containsKey(c.id)
                || (k.courante != null && k.courante.campagne.equals(c.id) && rejouer(c, k.courante, maintenant).phase == Phase.Abandon);
    }

    /**
     * Démarre la campagne, ou la reprend à son dernier check-point si elle avait été abandonnée (neuf : repartir du début
     * quand même). Une seule campagne à la fois : il faut finir ou abandonner celle en cours. graine null : tirée au hasard.
     */
    public static String demarrer(Carnet k, Campagne c, int niveau, long maintenant, String appareil, Biblio biblio, String graine, boolean neuf) {
        if (niveau < c.niveau) return "niveau " + c.niveau + " requis";
        if (c.noeud(c.depart) == null) return "campagne illisible";
        actualiser(k, biblio, maintenant);
        if (enCours(k, biblio, maintenant)) return "une campagne est déjà en cours";
        int numero = prochain(k);
        if (k.courante != null) ranger(k, k.courante, biblio, maintenant);
        Partie reprise = k.suspendues.remove(c.id);
        // Reprise : l'état du dernier check-point, sous une nouvelle identité de partie.
        Partie b = reprise == null || neuf ? null : suspendre(k, reprise, biblio, maintenant);
        Partie p;
        if (b != null) {
            p = b.copie();
            p.journal = new ArrayList<>();
            if (p.abandonnee) {
                p.entre = false;
                p.cp = null;
                p.i = 0;
            }
            p.abandonnee = false;
            p.p = numero;
            p.d = p.t = seconde(maintenant);
            p.o = appareil;
            p.geste = true;
            p.rejeu = p.rejeu || finie(k, c.id);
        } else p = nouvelle(c, numero, maintenant, appareil, graine == null ? nouvelleGraine() : graine, finie(k, c.id));
        k.courante = p;
        actualiser(k, biblio, maintenant);
        return null;
    }

    private static String decider(Carnet k, Campagne c, long maintenant, String appareil, int valeur) {
        if (k.courante == null || !k.courante.campagne.equals(c.id)) return "aucune partie en cours";
        Partie q = decider(c, k.courante, maintenant, appareil, valeur);
        if (q == null) return "ce n'est pas possible maintenant";
        k.courante = q;
        actualiser(k, id -> c, maintenant);
        return null;
    }

    public static String choisir(Carnet k, Campagne c, long maintenant, String appareil, String option) {
        if (k.courante == null || !k.courante.campagne.equals(c.id)) return "aucune partie en cours";
        Etat e = rejouer(c, k.courante, maintenant);
        if (e.phase == Phase.Choix)
            for (OptionVue o : e.options) if (o.id.equals(option)) return decider(k, c, maintenant, appareil, o.rang);
        return "ce n'est pas possible maintenant";
    }

    public static String continuer(Carnet k, Campagne c, long maintenant, String appareil) {
        return decider(k, c, maintenant, appareil, SUITE);
    }

    public static String epreuve(Carnet k, Campagne c, long maintenant, String appareil, boolean reussie) {
        return decider(k, c, maintenant, appareil, reussie ? REUSSITE : RATE);
    }

    public static String epreuveAuDe(Carnet k, Campagne c, long maintenant, String appareil) {
        if (k.courante == null || !k.courante.campagne.equals(c.id)) return "aucune partie en cours";
        Etat e = rejouer(c, k.courante, maintenant);
        return e.phase != Phase.Epreuve ? "ce n'est pas possible maintenant" : epreuve(k, c, maintenant, appareil, deDe(k.courante, e));
    }

    public static String abandonner(Carnet k, Campagne c, long maintenant, String appareil) {
        return decider(k, c, maintenant, appareil, ABANDON);
    }

    // ---- Ce que montre l'interface, en plus de l'état

    public static final class FinObtenue {
        public final String noeud, issue, titre;
        public final long t;
        public final Nomme souvenir;

        FinObtenue(String noeud, String issue, String titre, long t, Nomme souvenir) {
            this.noeud = noeud;
            this.issue = issue;
            this.titre = titre;
            this.t = t;
            this.souvenir = souvenir;
        }
    }

    /** Les fins déjà obtenues d'une campagne (les plus anciennes d'abord), avec leur souvenir. */
    public static List<FinObtenue> fins(Carnet k, Campagne c) {
        List<FinObtenue> l = new ArrayList<>();
        Bilan b = k.historique.get(c.id);
        if (b == null) return l;
        for (Map.Entry<String, Long> kv : b.fins.entrySet()) {
            String id = c.decode('n', kv.getKey());
            Noeud n = id == null ? null : c.noeud(id);
            if (n != null && n.type.equals("fin"))
                l.add(new FinObtenue(id, n.issue, n.titre, kv.getValue() * 1000, n.recompense.souvenir.isEmpty() ? null : c.souvenir(n.recompense.souvenir)));
        }
        Collections.sort(l, (x, y) -> x.t != y.t ? Long.compare(x.t, y.t) : x.noeud.compareTo(y.noeud));
        return l;
    }

    public static List<Nomme> souvenirs(Carnet k, Campagne c) {
        List<Nomme> l = new ArrayList<>();
        for (FinObtenue f : fins(k, c)) if (f.souvenir != null && !l.contains(f.souvenir)) l.add(f.souvenir);
        return l;
    }

    /** Titres et objets exclusifs gagnés (toutes fins obtenues). */
    public static List<String> titres(Carnet k, Campagne c) {
        List<String> l = new ArrayList<>();
        for (FinObtenue f : fins(k, c)) {
            String t = c.noeud(f.noeud).recompense.titre;
            if (!t.isEmpty() && !l.contains(t)) l.add(t);
        }
        return l;
    }

    public static List<String> objetsGagnes(Carnet k, Campagne c) {
        List<String> l = new ArrayList<>();
        for (FinObtenue f : fins(k, c)) {
            String t = c.noeud(f.noeud).recompense.objet;
            if (!t.isEmpty() && !l.contains(t)) l.add(t);
        }
        return l;
    }

    /** Po et xp acquis dans cette campagne (selon l'historique du groupe) : { po, xp }. */
    public static int[] acquis(Carnet k, Campagne c) {
        int po = 0, xp = 0;
        Bilan b = k.historique.get(c.id);
        if (b != null)
            for (String code : b.noeuds) {
                String id = c.decode('n', code);
                Noeud n = id == null ? null : c.noeud(id);
                if (n == null) continue;
                po += n.recompense.po;
                xp += n.recompense.xp;
            }
        return new int[]{po, xp};
    }

    /** Récompenses acquises que nul PC n'a encore versées : elles attendent le PC, comme les achats de la boutique. { po, xp } */
    public static int[] enAttente(Carnet k, Biblio biblio) {
        int po = 0, xp = 0;
        for (Map.Entry<String, Bilan> kv : k.historique.entrySet()) {
            Campagne c = biblio.charger(kv.getKey());
            if (c == null) continue;
            for (String code : kv.getValue().noeuds) {
                String id = c.decode('n', code);
                Noeud n = id == null ? null : c.noeud(id);
                if (n == null || k.payesPc.contains(kv.getKey() + "/" + code)) continue;
                po += n.recompense.po;
                xp += n.recompense.xp;
            }
        }
        return new int[]{po, xp};
    }

    private static String heure(long ms) {
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(ms);
        return c.get(Calendar.HOUR_OF_DAY) + " h " + String.format(Locale.ROOT, "%02d", c.get(Calendar.MINUTE));
    }

    /** « Pilou longe la falaise · retour vers 15 h 40 » (attente), « Pilou se repose · jusqu'à 15 h 40 » (repos), "" sinon. */
    public static String ligne(Etat e) {
        if (e.phase == Phase.Attente) return (e.pendant.isEmpty() ? "Pilou est en route" : e.pendant) + " · retour vers " + heure(e.fin);
        if (e.phase == Phase.Repos) return "Pilou se repose · jusqu'à " + heure(e.fin);
        return "";
    }

    // ---- Synchronisation : un message dédié, sur un sujet à part (les anciens appareils ne l'écoutent pas)

    /** Sujet des campagnes, tiré du code du groupe : même calcul que Campagnes.Sujet côté PC. */
    public static String sujet(String code) throws java.security.GeneralSecurityException {
        byte[] h = Chiffre.hmac(code, "pilou-campagne-v1");
        StringBuilder b = new StringBuilder("pilou-");
        for (int i = 0; i < 12; i++) b.append(String.format(Locale.ROOT, "%02x", h[i]));
        return b.toString();
    }

    private static void chaine(StringBuilder b, String s) {
        b.append('"');
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '"' || ch == '\\') b.append('\\').append(ch);
            else if (ch < ' ') b.append(String.format(Locale.ROOT, "\\u%04x", (int) ch));
            else b.append(ch);
        }
        b.append('"');
    }

    private static void jsonInstantane(StringBuilder b, Instantane x) {
        b.append('[');
        chaine(b, x.n);
        b.append(",{");
        boolean premier = true;
        for (Map.Entry<String, Integer> kv : x.v.entrySet()) {
            if (!premier) b.append(',');
            premier = false;
            chaine(b, kv.getKey());
            b.append(':').append(kv.getValue());
        }
        b.append("},");
        List<String> o = new ArrayList<>(x.o), d = new ArrayList<>(x.d);
        Collections.sort(o);
        Collections.sort(d);
        chaine(b, String.join("", o));
        b.append(',');
        chaine(b, String.join("", d));
        b.append(',');
        chaine(b, x.decor);
        b.append(',');
        chaine(b, x.lieu);
        b.append(']');
    }

    public static String jsonPartie(Partie p) {
        return jsonPartie(p, true);
    }

    /**
     * Une partie en JSON compact. Heures en secondes ; celles des décisions, relatives à la base.
     * {"c":campagne,"p":n°,"d":départ,"o":origine,"g":graine,"x":drapeaux (1 rejeu, 2 geste, 4 entré, 8 abandonnée),
     * "e":étape,"r":rang,"i":messages,"n":tirages,"t":curseur,"ici":[…],"cp":[…]?,"l":[appareils],"j":[[e,dt,a,nœud,v]…]}
     */
    public static String jsonPartie(Partie p, boolean journal) {
        StringBuilder b = new StringBuilder();
        b.append("{\"c\":");
        chaine(b, p.campagne);
        b.append(",\"p\":").append(p.p).append(",\"d\":").append(p.d / 1000).append(",\"o\":");
        chaine(b, p.o);
        b.append(",\"g\":");
        chaine(b, p.graine);
        int x = (p.rejeu ? 1 : 0) | (p.geste ? 2 : 0) | (p.entre ? 4 : 0) | (p.abandonnee ? 8 : 0);
        b.append(",\"x\":").append(x).append(",\"e\":").append(p.e).append(",\"r\":").append(p.r)
                .append(",\"i\":").append(p.i).append(",\"n\":").append(p.tirages)
                .append(",\"t\":").append(p.t / 1000).append(",\"ici\":");
        jsonInstantane(b, p.ici);
        if (p.cp != null) {
            b.append(",\"cp\":");
            jsonInstantane(b, p.cp);
        }
        if (journal && !p.journal.isEmpty()) {
            List<Entree> l = ordonner(p.journal);
            TreeSet<String> tries = new TreeSet<>();
            for (Entree e : l) tries.add(e.a);
            List<String> appareils = new ArrayList<>(tries);
            b.append(",\"l\":[");
            for (int i = 0; i < appareils.size(); i++) {
                if (i > 0) b.append(',');
                chaine(b, appareils.get(i));
            }
            b.append("],\"j\":[");
            for (int i = 0; i < l.size(); i++) {
                if (i > 0) b.append(',');
                b.append('[').append(l.get(i).e).append(',').append((l.get(i).t - p.t) / 1000).append(',')
                        .append(appareils.indexOf(l.get(i).a)).append(',');
                chaine(b, l.get(i).n);
                b.append(',').append(l.get(i).v).append(']');
            }
            b.append(']');
        }
        b.append('}');
        return b.toString();
    }

    private static void jsonBilan(StringBuilder b, Bilan x) {
        b.append('[').append(x.p).append(',').append(x.finie).append(",{");
        boolean premier = true;
        for (Map.Entry<String, Long> kv : x.fins.entrySet()) {
            if (!premier) b.append(',');
            premier = false;
            chaine(b, kv.getKey());
            b.append(':').append(kv.getValue());
        }
        b.append("},");
        chaine(b, String.join("", x.noeuds));
        b.append(']');
    }

    /** {"v":1,"a":appareil,"k":"pc"|"tel","q":partie en cours?,"s":[parties suspendues],"h":{campagne:[P,Finie,{fin:t},"nœuds"]}} */
    private static String jsonMessage(Carnet k, String appareil, String sorte, boolean courante, List<Partie> suspendues, boolean historique) {
        List<Partie> s = new ArrayList<>(suspendues);
        Collections.sort(s, (x, y) -> x.campagne.compareTo(y.campagne));
        StringBuilder b = new StringBuilder();
        b.append("{\"v\":1,\"a\":");
        chaine(b, appareil);
        b.append(",\"k\":");
        chaine(b, sorte);
        if (courante && k.courante != null) b.append(",\"q\":").append(jsonPartie(k.courante));
        if (!s.isEmpty()) {
            b.append(",\"s\":[");
            for (int i = 0; i < s.size(); i++) {
                if (i > 0) b.append(',');
                b.append(jsonPartie(s.get(i)));
            }
            b.append(']');
        }
        if (historique) {
            b.append(",\"h\":{");
            boolean premier = true;
            for (Map.Entry<String, Bilan> kv : k.historique.entrySet()) {
                if (!premier) b.append(',');
                premier = false;
                chaine(b, kv.getKey());
                b.append(':');
                jsonBilan(b, kv.getValue());
            }
            b.append('}');
        }
        b.append('}');
        return b.toString();
    }

    public static int octets(String json) {
        return json.getBytes(StandardCharsets.UTF_8).length;
    }

    /**
     * Ce que l'appareil publie : un message s'il tient sous TAILLE_JSON, sinon la partie en cours et l'historique d'abord,
     * puis les parties suspendues (une par message au besoin). Vide si le carnet n'a rien à dire.
     */
    public static List<String> messages(Carnet k, String appareil, String sorte) {
        List<String> l = new ArrayList<>();
        if (k.courante == null && k.suspendues.isEmpty() && k.historique.isEmpty()) return l;
        List<Partie> toutes = new ArrayList<>(k.suspendues.values()), aucune = new ArrayList<>();
        String tout = jsonMessage(k, appareil, sorte, true, toutes, true);
        if (octets(tout) <= TAILLE_JSON || toutes.isEmpty()) {
            l.add(tout);
            return l;
        }
        l.add(jsonMessage(k, appareil, sorte, true, aucune, true));
        List<Partie> lot = new ArrayList<>();
        for (Partie s : toutes) {
            lot.add(s);
            if (octets(jsonMessage(k, appareil, sorte, false, lot, false)) <= TAILLE_JSON || lot.size() == 1) continue;
            lot.remove(lot.size() - 1);
            l.add(jsonMessage(k, appareil, sorte, false, lot, false));
            lot = new ArrayList<>();
            lot.add(s);
        }
        if (!lot.isEmpty()) l.add(jsonMessage(k, appareil, sorte, false, lot, false));
        return l;
    }

    /** Signature de ce qui est synchronisé (pour ne publier que sur changement) : aussi la forme gardée dans les préférences. */
    public static String signature(Carnet k) {
        return jsonMessage(k, "", "", true, new ArrayList<>(k.suspendues.values()), true);
    }

    private static boolean codeValide(String s) {
        if (s.length() != 4) return false;
        for (int i = 0; i < 4; i++) if (ALPHABET64.indexOf(s.charAt(i)) < 0) return false;
        return true;
    }

    private static List<String> codes(String s) {
        TreeSet<String> l = new TreeSet<>();
        if (s.length() % 4 != 0 || s.length() > 4 * 400) return new ArrayList<>();
        for (int i = 0; i < s.length(); i += 4) if (codeValide(s.substring(i, i + 4))) l.add(s.substring(i, i + 4));
        return new ArrayList<>(l);
    }

    static boolean idValide(String s) {
        if (s.isEmpty() || s.length() > 40) return false;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (!((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '-')) return false;
        }
        return true;
    }

    private static Instantane lireInstantane(JSONObject o, String cle) {
        JSONArray a = o.optJSONArray(cle);
        if (a == null || a.length() != 6) return null;
        Instantane x = new Instantane();
        x.n = a.opt(0) instanceof String ? (String) a.opt(0) : "";
        x.o = codes(a.opt(2) instanceof String ? (String) a.opt(2) : "");
        x.d = codes(a.opt(3) instanceof String ? (String) a.opt(3) : "");
        x.decor = a.opt(4) instanceof String ? (String) a.opt(4) : "";
        x.lieu = a.opt(5) instanceof String ? (String) a.opt(5) : "";
        if (!codeValide(x.n) || (!x.decor.isEmpty() && !codeValide(x.decor)) || (!x.lieu.isEmpty() && !codeValide(x.lieu))) return null;
        JSONObject v = objet(a.opt(1));
        if (v != null)
            for (Iterator<String> i = v.keys(); i.hasNext(); ) {
                String cleVar = i.next();
                Integer n = entier(v.opt(cleVar));
                if (codeValide(cleVar) && n != null && x.v.size() < 200) x.v.put(cleVar, n);
            }
        return x;
    }

    /** Une partie lue d'un message ; null si elle est mal formée (on ne garde rien d'à moitié lu). */
    public static Partie lirePartie(JSONObject o) {
        if (o == null) return null;
        int x = n(o, "x", 0);
        Partie p = new Partie();
        p.campagne = s(o, "c");
        p.p = n(o, "p", 0);
        p.d = l(o, "d") * 1000;
        p.o = s(o, "o");
        p.graine = s(o, "g");
        p.rejeu = (x & 1) != 0;
        p.geste = (x & 2) != 0;
        p.entre = (x & 4) != 0;
        p.abandonnee = (x & 8) != 0;
        p.e = n(o, "e", 0);
        p.r = n(o, "r", 0);
        p.i = n(o, "i", 0);
        p.tirages = n(o, "n", 0);
        p.t = l(o, "t") * 1000;
        if (!idValide(p.campagne) || p.p < 1 || p.e < 0 || p.r < 0 || p.i < 0 || p.tirages < 0 || p.o.isEmpty() || p.o.length() > 64
                || p.graine.isEmpty() || p.graine.length() > 32 || p.d <= 0 || p.t <= 0)
            return null;
        Instantane ici = lireInstantane(o, "ici");
        if (ici == null) return null;
        p.ici = ici;
        p.cp = lireInstantane(o, "cp");
        List<String> appareils = new ArrayList<>();
        for (Object a : liste(o, "l")) appareils.add(a instanceof String ? (String) a : "");
        for (Object brut : liste(o, "j")) {
            if (p.journal.size() >= 400) break;
            JSONArray j = brut instanceof JSONArray ? (JSONArray) brut : null;
            if (j == null || j.length() != 5) continue;
            Integer e = entier(j.opt(0)), a = entier(j.opt(2)), v = entier(j.opt(4));
            Object dt = j.opt(1);
            if (e == null || a == null || v == null || !(dt instanceof Integer || dt instanceof Long)) continue;
            String noeud = j.opt(3) instanceof String ? (String) j.opt(3) : "";
            if (a < 0 || a >= appareils.size() || appareils.get(a).isEmpty() || appareils.get(a).length() > 64 || !codeValide(noeud)
                    || v < ABANDON || v > 16 || e < p.e)
                continue;
            p.journal.add(new Entree(e, p.t + ((Number) dt).longValue() * 1000, appareils.get(a), noeud, v));
        }
        p.journal = borner(p.journal, p.e);
        return p;
    }

    public static Partie lirePartie(String json) {
        try {
            return lirePartie(new JSONObject(json));
        } catch (JSONException e) {
            return null;
        }
    }

    private static void fusionBilan(Bilan b, JSONArray a) {
        if (a == null || a.length() != 4) return;
        Integer p = entier(a.opt(0)), f = entier(a.opt(1));
        if (p != null) b.p = Math.max(b.p, p);
        if (f != null) b.finie = Math.max(b.finie, f);
        JSONObject fins = objet(a.opt(2));
        if (fins != null)
            for (Iterator<String> i = fins.keys(); i.hasNext(); ) {
                String code = i.next();
                Object v = fins.opt(code);
                if (!codeValide(code) || !(v instanceof Integer || v instanceof Long)) continue;
                long t = ((Number) v).longValue();
                Long avant = b.fins.get(code);
                if (t > 0 && (avant != null || b.fins.size() < 40) && (avant == null || t < avant)) b.fins.put(code, t);
            }
        if (a.opt(3) instanceof String) b.noeuds.addAll(codes((String) a.opt(3)));
    }

    /** Ce qu'un message apporte au carnet (sans regarder qui l'envoie). */
    private static void fusionner(Carnet k, JSONObject r, Biblio biblio, long maintenant) {
        JSONObject h = objet(r.opt("h"));
        if (h != null) {
            TreeSet<String> cles = new TreeSet<>();
            for (Iterator<String> i = h.keys(); i.hasNext(); ) cles.add(i.next());
            for (String campagne : cles) {
                if (!idValide(campagne) || (k.historique.size() >= 40 && !k.historique.containsKey(campagne))) continue;
                JSONArray a = h.optJSONArray(campagne);
                fusionBilan(bilanDe(k, campagne), a);
                // Ce qu'un PC annonce comme acquis, il l'a versé (ou le versera) : le téléphone n'attend plus.
                if (s(r, "k").equals("pc") && a != null && a.length() == 4 && a.opt(3) instanceof String)
                    for (String code : codes((String) a.opt(3))) k.payesPc.add(campagne + "/" + code);
            }
        }
        for (Object x : liste(r, "s")) {
            Partie s = lirePartie(objet(x));
            if (s != null) k.suspendues.put(s.campagne, meilleure(k.suspendues.get(s.campagne), s));
        }
        Partie recue = lirePartie(objet(r.opt("q")));
        if (recue != null) {
            Partie mienne = k.courante;
            if (mienne == null) k.courante = recue;
            else {
                int c = compareIdentite(mienne, recue);
                if (c == 0) k.courante = unir(mienne, recue);
                else {
                    Partie gagne = c < 0 ? mienne : recue, perd = c < 0 ? recue : mienne;
                    k.courante = gagne.copie();
                    if (!perd.campagne.equals(gagne.campagne)) ranger(k, perd, biblio, maintenant);
                }
            }
        }
        nettoyer(k);
    }

    /**
     * Fusion d'un message reçu (d'un autre appareil du groupe) : idempotente, insensible à l'ordre et aux doublons.
     * Renvoie true si le carnet a changé. Appeler ensuite actualiser.
     */
    public static boolean recevoir(Carnet k, String json, String moi, Biblio biblio, long maintenant) {
        try {
            JSONObject r = new JSONObject(json);
            if (n(r, "v", 0) != 1) return false;
            String appareil = s(r, "a");
            if (appareil.isEmpty() || appareil.equals(moi)) return false;
            String avant = signature(k) + "|" + String.join(",", k.payesPc);
            fusionner(k, r, biblio, maintenant);
            return !avant.equals(signature(k) + "|" + String.join(",", k.payesPc));
        } catch (JSONException e) {
            return false;
        }
    }

    // ---- Garder le carnet (préférences du téléphone) : ce qui est synchronisé, tel qu'il voyage, et ce qui est propre à l'appareil

    public static String sauver(Carnet k) {
        try {
            JSONArray fil = new JSONArray();
            for (Message m : k.fil)
                fil.put(new JSONArray().put(m.p).put(m.e).put(m.i).put(m.qui).put(m.texte).put(m.noeud).put(m.lieu).put(m.humeur).put(m.decor).put(m.t));
            JSONArray pc = new JSONArray();
            for (String cle : k.payesPc) pc.put(cle);
            return new JSONObject().put("m", new JSONObject(signature(k))).put("fil", fil).put("lu", k.lu).put("pc", pc).toString();
        } catch (JSONException e) {
            return "{}";
        }
    }

    public static Carnet relire(String json) {
        Carnet k = new Carnet();
        try {
            JSONObject r = new JSONObject(json);
            JSONObject m = objet(r.opt("m"));
            if (m != null) fusionner(k, m, id -> null, 0);
            k.payesPc.clear();
            for (Object x : liste(r, "pc")) if (x instanceof String) k.payesPc.add((String) x);
            k.lu = s(r, "lu");
            for (Object x : liste(r, "fil")) {
                JSONArray a = x instanceof JSONArray ? (JSONArray) x : null;
                if (a == null || a.length() != 10) continue;
                k.fil.add(new Message(a.optInt(0), a.optInt(1), a.optInt(2), a.optString(3), a.optString(4), a.optString(5), a.optString(6),
                        a.optString(7), a.optString(8), a.optLong(9)));
            }
        } catch (JSONException e) {
            // carnet illisible : on repart d'un carnet vide (les autres appareils du groupe le rempliront)
        }
        return k;
    }
}
