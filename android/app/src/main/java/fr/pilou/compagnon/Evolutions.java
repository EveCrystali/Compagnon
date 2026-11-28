package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Les scènes d'évolution (docs/SCENES.md, « Scènes d'évolution ») : lecteur de assets/evolutions.txt, traduction exacte de
 * outils/sprites/evolutions.py (la référence) et d'Evolutions.cs (PC). Mêmes scènes, mêmes répliques dans le même ordre
 * pour une variante et un choix donnés, même temps d'écriture. EvolutionsTest relit outils/sprites/evolutions-reference.txt.
 * Sans Android : la vue de la scène est SceneEvolution.
 */
final class Evolutions {
    static final String[] VARIANTES = {"calin", "espiegle"};
    /** Pilou écrit une lettre toutes les 30 ms (il parle pendant ce temps-là). */
    static final int MS_LETTRE = 30;
    static final int MS_MIN = 900, MS_MAX = 7000;

    private Evolutions() {
    }

    /** Une réplique : l'humeur (vide pour la question) et le texte. */
    static final class Replique {
        final String humeur, texte;

        Replique(String humeur, String texte) {
            this.humeur = humeur;
            this.texte = texte;
        }
    }

    /** Un élément du script : sorte (pilou | calin | espiegle | choix | apres), clé (id de l'option pour « apres »), humeur, texte. */
    static final class Element {
        final String sorte, cle, humeur, texte;

        Element(String sorte, String cle, String humeur, String texte) {
            this.sorte = sorte;
            this.cle = cle;
            this.humeur = humeur;
            this.texte = texte;
        }
    }

    static final class Option {
        final String id, libelle;

        Option(String id, String libelle) {
            this.id = id;
            this.libelle = libelle;
        }
    }

    static final class Scene {
        final int stade;
        String titre = "", decor = "", question = "";
        /** Morceau de assets/musiques.txt (docs/SONS.md) ; vide : la boucle du ton « émotion ». */
        String musique = "";
        final List<Option> options = new ArrayList<>();
        final List<Element> elements = new ArrayList<>();

        Scene(int stade) {
            this.stade = stade;
        }

        /** Le libellé de l'option, ou null si l'id est inconnu. */
        String libelle(String id) {
            for (Option o : options) if (o.id.equals(id)) return o.libelle;
            return null;
        }
    }

    /** Comme str.partition(" ") : { avant, après } ; sans espace, { s, "" }. */
    private static String[] partager(String s) {
        int i = s.indexOf(' ');
        return i < 0 ? new String[]{s, ""} : new String[]{s.substring(0, i), s.substring(i + 1)};
    }

    /** {stade: Scene}, dans l'ordre des stades ; une ligne inconnue est ignorée (un fichier plus récent reste lisible). */
    static Map<Integer, Scene> lire(String texte) {
        Map<Integer, Scene> scenes = new TreeMap<>();
        Scene sc = null;
        for (String brute : texte.split("\r?\n", -1)) {
            String ligne = brute.trim();
            if (ligne.isEmpty() || ligne.startsWith("#")) continue;
            String[] mr = partager(ligne);
            String mot = mr[0], reste = mr[1];
            if (mot.equals("scene")) {
                sc = new Scene(Integer.parseInt(reste.trim()));
                scenes.put(sc.stade, sc);
            } else if (sc == null) {
                continue;
            } else if (mot.equals("titre")) {
                sc.titre = reste;
            } else if (mot.equals("decor")) {
                sc.decor = reste;
            } else if (mot.equals("musique")) {
                sc.musique = reste;
            } else if (mot.equals("pilou") || mot.equals("calin") || mot.equals("espiegle")) {
                String[] ht = partager(reste);
                sc.elements.add(new Element(mot, "", ht[0], ht[1]));
            } else if (mot.equals("choix")) {
                sc.question = reste;
                sc.elements.add(new Element("choix", "", "", reste));
            } else if (mot.equals("option")) {
                String[] il = partager(reste);
                sc.options.add(new Option(il[0], il[1]));
            } else if (mot.equals("apres")) {
                String[] ir = partager(reste);
                String[] ht = partager(ir[1]);
                sc.elements.add(new Element("apres", ir[0], ht[0], ht[1]));
            }
        }
        return scenes;
    }

    /** La variante du stade (Soins.Variante) ; inconnue ou absente : câline. */
    static String variante(String v) {
        for (String x : VARIANTES) if (x.equals(v)) return v;
        return "calin";
    }

    /**
     * Les répliques dites, dans l'ordre. choix null : jusqu'à la question (incluse, sans humeur) ; sinon, toute la scène
     * avec la réplique de ce choix.
     */
    static List<Replique> deroule(Scene sc, String var, String choix) {
        var = variante(var);
        List<Replique> out = new ArrayList<>();
        for (Element e : sc.elements) {
            if (e.sorte.equals("pilou") || e.sorte.equals(var)) {
                out.add(new Replique(e.humeur, e.texte));
            } else if (e.sorte.equals("choix")) {
                if (choix == null) {
                    out.add(new Replique("", e.texte));
                    return out;
                }
            } else if (e.sorte.equals("apres") && e.cle.equals(choix)) {
                out.add(new Replique(e.humeur, e.texte));
            }
        }
        return out;
    }

    /** Le temps que Pilou met à écrire une réplique (et à la dire dans la scène). Longueur : String.length(). */
    static int msEcriture(String texte) {
        return Math.max(MS_MIN, Math.min(MS_MAX, MS_LETTRE * texte.length()));
    }

    private static Map<Integer, Scene> embarquees;

    /** Les scènes embarquées (ressource /evolutions.txt) ; vide si elles manquent. */
    static synchronized Map<Integer, Scene> scenes() {
        if (embarquees == null) embarquees = lire(Sprites.ressource("/evolutions.txt"));
        return embarquees;
    }
}
