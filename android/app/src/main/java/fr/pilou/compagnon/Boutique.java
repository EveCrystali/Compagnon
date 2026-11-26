package fr.pilou.compagnon;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

/**
 * Boutique de Pilou (gratuite, virtuelle) : même catalogue que Boutique.cs sur le PC. Les pièces d'or (po)
 * se gagnent en quêtes ; aucun achat réel. Le PC tient le solde : le téléphone demande, le PC applique.
 * Rayons par emplacement ; dans chaque rayon, des rangées par palier de niveau (1, 5, 10, 15, 20, 30, 40, 50) :
 * le niveau ouvre la rangée, les po achètent l'objet. Les offres du jour sont une vitrine (la première à -25 %).
 * Boutique garnie : /catalogue.txt (le même fichier que le PC, écrit par outils/sprites/garde_robe.py) — ensembles
 * avec bonus porté, articles de saison, articles de passage (trois jours par mois en vitrine), titres affichés,
 * collection et ses paliers. La vitrine se tire de la date exactement comme sur le PC (Hasard : FNV-1a + xorshift64*).
 */
public final class Boutique {
    public static final String TETE = "tete", YEUX = "yeux", COU = "cou", DOS = "dos", MAIN = "main", PIEDS = "pieds", COMPAGNON = "compagnon",
            EFFET = "effet", COULEUR = "couleur", FOND = "fond", BULLE = "bulle", TITRE = "titre";
    public static final String[] SLOTS = {TETE, YEUX, COU, DOS, MAIN, PIEDS, COMPAGNON, EFFET, COULEUR, FOND, BULLE, TITRE};
    /** « accessoire » : le chapeau historique (choisi sur le PC) ; « bonus » : actif dès qu'il est possédé ;
     *  « consommable » : s'achète plusieurs fois. Les trois forment le rayon « Spéciaux ». */
    public static final String ACCESSOIRE = "accessoire", BONUS = "bonus", CONSOMMABLE = "consommable", SPECIAUX = "speciaux";
    /** Rayon transversal : les pièces des ensembles thématiques. */
    public static final String RAYON_ENSEMBLES = "ensembles";
    public static final String[] RAYONS = {RAYON_ENSEMBLES, TETE, YEUX, COU, DOS, MAIN, PIEDS, COMPAGNON, EFFET, COULEUR, FOND, BULLE, TITRE, SPECIAUX};
    public static final int MYTHIQUE = 5;
    public static final String[] SAISONS = {"hiver", "printemps", "ete", "automne", "frissons", "fetes"};
    public static final int JOURS_PASSAGE = 3;
    public static final int[] PALIERS = {1, 5, 10, 15, 20, 30, 40, 50};
    public static final String TRAINEE_ETOILES = "trainee-etoiles", CANNE_DOREE = "canne-doree", MARMITE_CUIVRE = "marmite-cuivre",
            PIERRE_CALME = "pierre-calme";

    public static final class Article {
        public final String id, nom, slot;
        public final int prix, niveauMin, rarete;
        public final boolean permanent;
        /** Boutique garnie : numéro stable (0 : catalogue d'origine), saison, ensemble, passage ; récompense (se gagne). */
        public int numero;
        public String saison = "", ensemble = "";
        public boolean passage, recompense;

        Article(String id, String nom, String slot, int prix, int niveauMin, int rarete, boolean permanent) {
            this.id = id;
            this.nom = nom;
            this.slot = slot;
            this.prix = prix;
            this.niveauMin = niveauMin;
            this.rarete = rarete;
            this.permanent = permanent;
        }
    }

    /** Ensemble thématique : porté en entier, un effet (bonus) ; possédé en entier, un titre. */
    public static final class Ensemble {
        public final String id, nom, signe, bonus, titre;
        public final List<String> pieces;

        Ensemble(String id, String nom, String signe, String bonus, String titre, List<String> pieces) {
            this.id = id;
            this.nom = nom;
            this.signe = signe;
            this.bonus = bonus;
            this.titre = titre;
            this.pieces = Collections.unmodifiableList(pieces);
        }

        public String idTitre() {
            return "titre-ens-" + id;
        }
    }

    /** Palier de collection : à {@code nombre} articles (0 : tout), un titre ou un cadre. */
    public static final class PalierCollection {
        public final int nombre;
        public final String id, slot, nom;

        PalierCollection(int nombre, String id, String slot, String nom) {
            this.nombre = nombre;
            this.id = id;
            this.slot = slot;
            this.nom = nom;
        }
    }

    /** Cadre de bulle : bord, épaisseur (dp), arrondi (dp), fond (0 : celui du thème), texte clair imposé. */
    public static final class StyleBulle {
        public final int bord, epaisseur, rayon, fond;
        public final boolean sombre;

        StyleBulle(int bord, int epaisseur, int rayon, int fond, boolean sombre) {
            this.bord = bord;
            this.epaisseur = epaisseur;
            this.rayon = rayon;
            this.fond = fond;
            this.sombre = sombre;
        }
    }

    public static final List<Article> CATALOGUE;
    public static final List<Ensemble> ENSEMBLES;
    public static final List<PalierCollection> PALIERS_COLLECTION;
    /** Titres d'ensemble et récompenses de collection : ne s'achètent pas. */
    public static final List<Article> TROPHEES;
    private static final Map<String, Article> PAR_ID = new HashMap<>();
    private static final Map<Integer, String> PAR_NUMERO = new HashMap<>();
    public static final int TOTAL_COLLECTION;

    private static void a(List<Article> l, String id, String nom, String slot, int prix, int niveau, int rarete) {
        l.add(new Article(id, nom, slot, prix, niveau, rarete, false));
    }

    static {
        List<Article> l = new ArrayList<>();
        // Tête
        l.add(new Article("casquette", "Casquette", TETE, 80, 1, Butin.COMMUN, true));
        a(l, "beret", "Béret", TETE, 90, 1, Butin.COMMUN);
        a(l, "bonnet-pompon", "Bonnet à pompon", TETE, 110, 1, Butin.COMMUN);
        a(l, "bandeau-ninja", "Bandeau de ninja", TETE, 120, 1, Butin.PEU_COMMUN);
        a(l, "couronne-fleurs", "Couronne de fleurs", TETE, 180, 5, Butin.PEU_COMMUN);
        a(l, "casque-chantier", "Casque de chantier", TETE, 180, 5, Butin.PEU_COMMUN);
        a(l, "chapeau-pirate", "Chapeau de pirate", TETE, 220, 5, Butin.RARE);
        a(l, "haut-de-forme", "Haut-de-forme", TETE, 260, 5, Butin.RARE);
        a(l, "sombrero", "Sombrero", TETE, 280, 10, Butin.RARE);
        a(l, "chapeau-cowboy", "Chapeau de cowboy", TETE, 300, 10, Butin.RARE);
        a(l, "cornes-viking", "Casque à cornes", TETE, 320, 10, Butin.EPIQUE);
        a(l, "chapeau-sorcier", "Chapeau de sorcier", TETE, 380, 10, Butin.EPIQUE);
        a(l, "oreilles-chat", "Oreilles de chat", TETE, 360, 15, Butin.RARE);
        a(l, "aureole", "Auréole", TETE, 450, 15, Butin.LEGENDAIRE);
        a(l, "couronne-laurier", "Couronne de laurier", TETE, 520, 20, Butin.EPIQUE);
        a(l, "antenne-neon", "Antennes néon", TETE, 1000, 40, Butin.LEGENDAIRE);
        // Yeux
        l.add(new Article("lunettes-rondes", "Lunettes rondes", YEUX, 90, 1, Butin.COMMUN, true));
        a(l, "masque-plongee", "Masque de plongée", YEUX, 160, 1, Butin.PEU_COMMUN);
        a(l, "lunettes-3d", "Lunettes 3D", YEUX, 160, 5, Butin.PEU_COMMUN);
        a(l, "monocle", "Monocle", YEUX, 200, 5, Butin.RARE);
        a(l, "visiere-pilote", "Visière de pilote", YEUX, 380, 15, Butin.RARE);
        a(l, "lunettes-coeur", "Lunettes cœur", YEUX, 450, 20, Butin.EPIQUE);
        // Cou
        l.add(new Article("echarpe", "Écharpe", COU, 70, 1, Butin.COMMUN, true));
        a(l, "bandana", "Bandana", COU, 80, 1, Butin.COMMUN);
        a(l, "noeud-pois", "Nœud à pois", COU, 150, 5, Butin.PEU_COMMUN);
        a(l, "medaille", "Médaille", COU, 300, 5, Butin.EPIQUE);
        a(l, "cravate", "Cravate", COU, 240, 10, Butin.RARE);
        a(l, "collier-perles", "Collier de perles", COU, 750, 30, Butin.EPIQUE);
        // Dos (l'imperméable protège aussi de la pluie)
        a(l, "impermeable", "Imperméable", DOS, 180, 1, Butin.PEU_COMMUN);
        a(l, "sac-a-dos", "Sac à dos", DOS, 170, 5, Butin.PEU_COMMUN);
        a(l, "cape", "Cape", DOS, 280, 5, Butin.RARE);
        a(l, "carapace", "Carapace", DOS, 420, 15, Butin.RARE);
        a(l, "ailes-papillon", "Ailes de papillon", DOS, 900, 30, Butin.EPIQUE);
        a(l, "jetpack", "Jetpack", DOS, 1500, 50, Butin.LEGENDAIRE);
        // Main (parapluie, moufles, éventail : contre la pluie, le froid, la chaleur — Meteo.java)
        l.add(new Article("tasse-cafe", "Tasse de café", MAIN, 60, 1, Butin.COMMUN, true));
        a(l, "sucette", "Sucette", MAIN, 70, 1, Butin.COMMUN);
        a(l, "moufles", "Moufles", MAIN, 80, 1, Butin.COMMUN);
        a(l, "eventail", "Éventail", MAIN, 100, 1, Butin.PEU_COMMUN);
        a(l, "parapluie", "Parapluie", MAIN, 110, 1, Butin.PEU_COMMUN);
        a(l, "ballon-helium", "Ballon", MAIN, 130, 1, Butin.PEU_COMMUN);
        a(l, "epee-mousse", "Épée en mousse", MAIN, 190, 5, Butin.PEU_COMMUN);
        a(l, "lanterne", "Lanterne", MAIN, 260, 10, Butin.RARE);
        a(l, "baguette", "Baguette magique", MAIN, 340, 10, Butin.EPIQUE);
        a(l, "parapluie-etoile", "Parapluie étoilé", MAIN, 420, 10, Butin.EPIQUE);
        a(l, "guitare", "Guitare", MAIN, 560, 20, Butin.EPIQUE);
        a(l, "canne-or", "Canne à pêche dorée", MAIN, 820, 30, Butin.LEGENDAIRE);
        // Pieds
        a(l, "bottes-pluie", "Bottes de pluie", PIEDS, 90, 1, Butin.COMMUN);
        a(l, "baskets", "Baskets", PIEDS, 100, 1, Butin.COMMUN);
        a(l, "palmes", "Palmes", PIEDS, 230, 10, Butin.RARE);
        a(l, "patins", "Patins", PIEDS, 480, 20, Butin.EPIQUE);
        // Compagnons
        a(l, "petit-poisson-bocal", "Poisson en bocal", COMPAGNON, 240, 5, Butin.RARE);
        a(l, "oiseau", "Oiseau", COMPAGNON, 450, 10, Butin.RARE);
        a(l, "petit-chat", "Petit chat", COMPAGNON, 520, 10, Butin.LEGENDAIRE);
        a(l, "petit-robot", "Petit robot", COMPAGNON, 700, 20, Butin.EPIQUE);
        a(l, "fantome", "Fantôme", COMPAGNON, 900, 30, Butin.EPIQUE);
        a(l, "mini-dragon", "Mini-dragon", COMPAGNON, 1300, 40, Butin.LEGENDAIRE);
        // Effets
        a(l, "bulles-savon", "Bulles de savon", EFFET, 260, 5, Butin.PEU_COMMUN);
        a(l, "trainee-coeurs", "Traînée de cœurs", EFFET, 300, 5, Butin.RARE);
        a(l, "trainee-notes", "Traînée de notes", EFFET, 340, 5, Butin.EPIQUE);
        a(l, "confettis", "Confettis", EFFET, 420, 15, Butin.RARE);
        a(l, "aura", "Aura", EFFET, 600, 15, Butin.LEGENDAIRE);
        a(l, "trainee-prisme", "Arc prisme", EFFET, 950, 30, Butin.EPIQUE);
        a(l, "aura-feu", "Aura de feu", EFFET, 1500, 50, Butin.LEGENDAIRE);
        // Couleurs (teintes de Pilou)
        l.add(new Article("sable", "Couleur sable", COULEUR, 150, 1, Butin.COMMUN, true));
        l.add(new Article("ardoise", "Couleur ardoise", COULEUR, 150, 1, Butin.COMMUN, true));
        a(l, "lavande", "Couleur lavande", COULEUR, 200, 1, Butin.PEU_COMMUN);
        a(l, "glacier", "Couleur glacier", COULEUR, 220, 5, Butin.RARE);
        a(l, "pervenche", "Couleur pervenche", COULEUR, 220, 5, Butin.PEU_COMMUN);
        a(l, "corail-orange", "Couleur corail", COULEUR, 250, 5, Butin.RARE);
        a(l, "mandarine", "Couleur mandarine", COULEUR, 300, 10, Butin.RARE);
        a(l, "miel", "Couleur miel", COULEUR, 380, 15, Butin.RARE);
        a(l, "prune", "Couleur prune", COULEUR, 450, 20, Butin.EPIQUE);
        a(l, "acier", "Couleur acier", COULEUR, 600, 30, Butin.EPIQUE);
        a(l, "peche", "Couleur pêche", COULEUR, 800, 40, Butin.LEGENDAIRE);
        // Décors : derrière Pilou dans l'app
        a(l, "fond-nuit", "Décor nuit étoilée", FOND, 120, 1, Butin.COMMUN);
        a(l, "fond-foret", "Décor forêt bleutée", FOND, 250, 5, Butin.PEU_COMMUN);
        a(l, "fond-plage", "Décor plage", FOND, 350, 10, Butin.RARE);
        a(l, "fond-arcade", "Décor salle d'arcade", FOND, 600, 20, Butin.EPIQUE);
        a(l, "fond-espace", "Décor espace", FOND, 900, 30, Butin.LEGENDAIRE);
        // Cadres de bulle
        a(l, "bulle-doree", "Bulle dorée", BULLE, 200, 5, Butin.PEU_COMMUN);
        a(l, "bulle-nuit", "Bulle de nuit", BULLE, 260, 10, Butin.RARE);
        a(l, "bulle-pixel", "Bulle pixel", BULLE, 320, 15, Butin.RARE);
        a(l, "bulle-nuages", "Bulle nuage", BULLE, 400, 20, Butin.EPIQUE);
        // Anciennes récompenses de niveau (Boutique.cs : même prix ; rangée = palier de l'ancien niveau).
        String[] acc = {"feuille", "Feuille d'automne", "1", "noeud", "Nœud papillon", "2", "casque", "Casque audio", "3",
                "bonnet", "Bonnet de laine", "4", "lunettes", "Lunettes de soleil", "5", "couronne", "Couronne", "7",
                "chapeaupeche", "Chapeau de pêcheur", "14", "toque", "Toque de chef", "18", "tablier", "Tablier", "22",
                "etoilemer", "Étoile de mer", "27"};
        for (int i = 0; i < acc.length; i += 3) {
            int n = Integer.parseInt(acc[i + 2]);
            l.add(new Article(acc[i], acc[i + 1], ACCESSOIRE, Math.min(600, 60 + 15 * n), palier(n), rang(n), true));
        }
        String[] cou = {"nuit", "Couleur bleu nuit", "6", "ambre", "Couleur ambre", "8", "argent", "Couleur argent", "10",
                "aurore", "Couleur aurore", "12", "lagon", "Couleur lagon", "20", "braise", "Couleur braise", "26",
                "nacre", "Couleur nacre", "32", "abysse", "Couleur abysse", "40", "comete", "Couleur comète", "50"};
        for (int i = 0; i < cou.length; i += 3) {
            int n = Integer.parseInt(cou[i + 2]);
            l.add(new Article("couleur-" + cou[i], cou[i + 1], COULEUR, Math.min(600, 100 + 10 * n), palier(n), rang(n), true));
        }
        l.add(new Article(TRAINEE_ETOILES, "Traînée d'étoiles", EFFET, 220, 5, Butin.RARE, true));
        l.add(new Article(CANNE_DOREE, "Canne dorée (plus de prises légendaires)", BONUS, 500, 30, Butin.LEGENDAIRE, true));
        l.add(new Article(MARMITE_CUIVRE, "Marmite en cuivre (moins de plats brûlés)", BONUS, 520, 30, Butin.LEGENDAIRE, true));
        l.add(new Article(PIERRE_CALME, "Pierre de calme (retient une évolution)", CONSOMMABLE, 150, 5, Butin.PEU_COMMUN, true));
        // Boutique garnie (même fichier que le PC) : articles, ensembles, paliers de collection.
        List<Ensemble> ens = new ArrayList<>();
        List<PalierCollection> pal = new ArrayList<>();
        for (String brut : ressource("/catalogue.txt").replace("\r", "").split("\n")) {
            if (brut.isEmpty() || brut.startsWith("#")) continue;
            String[] c = brut.split("\\|", -1);
            if (c[0].equals("article") && c.length == 11 && entier(c[1]) > 0 && entier(c[5]) >= 0 && entier(c[6]) >= 1
                    && entier(c[7]) >= 0 && entier(c[7]) <= MYTHIQUE) {
                Article a = new Article(c[2], c[3], c[4], entier(c[5]), entier(c[6]), entier(c[7]), false);
                a.numero = entier(c[1]);
                a.saison = c[8];
                a.ensemble = c[9];
                a.passage = c[10].equals("1");
                l.add(a);
                PAR_NUMERO.put(a.numero, a.id);
            } else if (c[0].equals("ensemble") && c.length >= 8) {
                ens.add(new Ensemble(c[1], c[2], c[3], c[4], c[5], new ArrayList<>(Arrays.asList(c).subList(6, c.length))));
            } else if (c[0].equals("palier") && c.length == 5 && entier(c[1]) >= 0) {
                pal.add(new PalierCollection(entier(c[1]), c[2], c[3], c[4]));
            }
        }
        CATALOGUE = Collections.unmodifiableList(l);
        ENSEMBLES = Collections.unmodifiableList(ens);
        PALIERS_COLLECTION = Collections.unmodifiableList(pal);
        for (Article a : CATALOGUE) if (!PAR_ID.containsKey(a.id)) PAR_ID.put(a.id, a);
        List<Article> tr = new ArrayList<>();
        for (Ensemble e : ens) {
            Article a = new Article(e.idTitre(), e.titre, TITRE, 0, 1, Butin.EPIQUE, false);
            a.ensemble = e.id;
            a.recompense = true;
            tr.add(a);
        }
        for (PalierCollection p : pal) {
            Article a = new Article(p.id, p.nom, p.slot, 0, 1, p.nombre == 0 ? MYTHIQUE : p.nombre >= 120 ? Butin.LEGENDAIRE
                    : p.nombre >= 50 ? Butin.EPIQUE : Butin.RARE, false);
            a.recompense = true;
            tr.add(a);
        }
        TROPHEES = Collections.unmodifiableList(tr);
        int n = 0;
        for (Article a : CATALOGUE) if (collectionnable(a)) n++;
        TOTAL_COLLECTION = n;
    }

    private static int entier(String s) {
        try {
            return Integer.parseInt(s);
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    private static String ressource(String chemin) {
        try (InputStream in = Boutique.class.getResourceAsStream(chemin)) {
            if (in == null) return "";
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] tampon = new byte[8192];
            int n;
            while ((n = in.read(tampon)) > 0) out.write(tampon, 0, n);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            return "";
        }
    }

    private Boutique() {
    }

    private static int rang(int niveau) {
        return niveau <= 3 ? Butin.COMMUN : niveau <= 8 ? Butin.PEU_COMMUN : niveau <= 15 ? Butin.RARE : niveau <= 30 ? Butin.EPIQUE : Butin.LEGENDAIRE;
    }

    /** Plus haut palier atteint au niveau n (1 au minimum). */
    public static int palier(int niveau) {
        int r = 1;
        for (int p : PALIERS) if (p <= niveau) r = p;
        return r;
    }

    /** Prochain palier après le niveau n (0 : tout est ouvert). */
    public static int prochainPalier(int niveau) {
        for (int p : PALIERS) if (p > niveau) return p;
        return 0;
    }

    public static String rayonDe(String slot) {
        return ACCESSOIRE.equals(slot) || BONUS.equals(slot) || CONSOMMABLE.equals(slot) ? SPECIAUX : slot;
    }

    public static boolean ouvert(Article a, int niveau) {
        return niveau >= a.niveauMin;
    }

    /** Pièce d'un ensemble (y compris un décor d'origine repris dans un ensemble). */
    public static boolean estPiece(Article a) {
        for (Ensemble e : ENSEMBLES) if (e.pieces.contains(a.id)) return true;
        return false;
    }

    public static boolean dansRayon(Article a, String rayon) {
        return RAYON_ENSEMBLES.equals(rayon) ? estPiece(a) : rayonDe(a.slot).equals(rayon);
    }

    /** Articles d'un rayon dans la rangée d'un palier. */
    public static List<Article> rangee(String rayon, int palier) {
        List<Article> r = new ArrayList<>();
        for (Article a : CATALOGUE) if (dansRayon(a, rayon) && a.niveauMin == palier) r.add(a);
        return r;
    }

    /** Articles des rangées ouvertes entre deux niveaux (avant exclu, après inclus). */
    public static List<Article> debloques(int avant, int apres) {
        List<Article> r = new ArrayList<>();
        for (Article a : CATALOGUE) if (a.niveauMin > avant && a.niveauMin <= apres) r.add(a);
        return r;
    }

    /** Rayons qui gagnent une rangée à ce palier. */
    public static List<String> rayonsDuPalier(int palier) {
        List<String> r = new ArrayList<>();
        for (String ray : RAYONS) if (!RAYON_ENSEMBLES.equals(ray) && !rangee(ray, palier).isEmpty()) r.add(ray);
        return r;
    }

    /** Ce qui se dessine sur Pilou lui-même (ni la couleur, ni le décor, ni le cadre de bulle). */
    public static boolean surPilou(String slot) {
        return !COULEUR.equals(slot) && !FOND.equals(slot) && !BULLE.equals(slot) && !TITRE.equals(slot);
    }

    public static StyleBulle style(String id) {
        if (id == null) return null;
        switch (id) {
            case "bulle-doree": return new StyleBulle(0xffc9a227, 4, 0, 0, false);
            case "bulle-nuit": return new StyleBulle(0xff6cb6ff, 3, 0, 0xff16365e, true);
            case "bulle-pixel": return new StyleBulle(0xfff69d50, 5, 0, 0, false);
            case "bulle-nuages": return new StyleBulle(0xff9b8cff, 3, 12, 0, false);
            case "bulle-bois": return new StyleBulle(0xffa86f3c, 4, 2, 0xfff3e2c4, false);
            case "bulle-lagon": return new StyleBulle(0xff3fb8e0, 3, 6, 0, false);
            case "bulle-parchemin": return new StyleBulle(0xff8a6e4b, 3, 1, 0xfff6ead0, false);
            case "bulle-givre": return new StyleBulle(0xffb4dbff, 4, 10, 0xffeaf6ff, false);
            case "bulle-guirlande": return new StyleBulle(0xfff69d50, 5, 6, 0xff16365e, true);
            case "bulle-ronde": return new StyleBulle(0xff6cb6ff, 3, 18, 0, false);
            case "bulle-encre": return new StyleBulle(0xff9b8cff, 3, 4, 0xff1c2128, true);
            case "bulle-ambre": return new StyleBulle(0xfff2a94e, 4, 3, 0xff3a2410, true);
            case "bulle-cristal": return new StyleBulle(0xffd2caff, 5, 14, 0xfff4f1ff, false);
            case "cadre-bronze": return new StyleBulle(0xffc4783a, 4, 2, 0, false);
            case "cadre-argent": return new StyleBulle(0xffb8c4d2, 5, 3, 0, false);
            case "cadre-or": return new StyleBulle(0xfff5d76e, 5, 4, 0xfffff9e0, false);
            case "cadre-prisme": return new StyleBulle(0xff9b8cff, 6, 8, 0xff0d2a4d, true);
            default: return null;
        }
    }

    public static Article trouver(String id) {
        return id == null ? null : PAR_ID.get(id);
    }

    /** Article ou récompense (titre d'ensemble, titre ou cadre de collection). */
    public static Article trouverTout(String id) {
        Article a = trouver(id);
        if (a != null || id == null) return a;
        for (Article t : TROPHEES) if (t.id.equals(id)) return t;
        return null;
    }

    /** Prix du jour : -25 % pour l'objet en promo (le premier des offres du PC). */
    public static int prix(Article a, String promo) {
        return a.id.equals(promo) ? a.prix * 3 / 4 : a.prix;
    }

    public static String signe(String slot) {
        switch (slot) {
            case TETE: return "▲";
            case YEUX: return "◉";
            case COU: return "◡";
            case DOS: return "▼";
            case MAIN: return "✚";
            case PIEDS: return "▬";
            case COMPAGNON: return "♣";
            case EFFET: return "✧";
            case COULEUR: return "■";
            case FOND: return "▧";
            case BULLE: return "❝";
            case TITRE: return "❞";
            case RAYON_ENSEMBLES: return "❖";
            case ACCESSOIRE: return "◆";
            case BONUS: return "★";
            case CONSOMMABLE: return "◇";
            case SPECIAUX: return "★";
            default: return "·";
        }
    }

    public static String nomSlot(String slot) {
        switch (slot) {
            case TETE: return "Tête";
            case YEUX: return "Yeux";
            case COU: return "Cou";
            case DOS: return "Dos";
            case MAIN: return "Main";
            case PIEDS: return "Pieds";
            case COMPAGNON: return "Compagnons";
            case EFFET: return "Effets";
            case COULEUR: return "Couleurs";
            case FOND: return "Décors";
            case BULLE: return "Bulles";
            case TITRE: return "Titres";
            case RAYON_ENSEMBLES: return "Ensembles";
            case ACCESSOIRE: return "Accessoires";
            case BONUS: return "Bonus";
            case CONSOMMABLE: return "Consommables";
            case SPECIAUX: return "Spéciaux";
            default: return slot;
        }
    }

    /** Ce qui empêche d'acheter aujourd'hui (null : on peut). */
    public static String refus(Article a, int niveau, int solde, String promo, boolean possede) {
        return refus(a, niveau, solde, promo, possede, LocalDate.now());
    }

    /** Ce qui empêche d'acheter (null : on peut). La rangée doit être ouverte, l'article de saison ou de passage. */
    public static String refus(Article a, int niveau, int solde, String promo, boolean possede, LocalDate jour) {
        if (a.recompense) return "à gagner";
        if (possede && !a.slot.equals(CONSOMMABLE)) return "à toi";
        if (!ouvert(a, niveau)) return "niveau " + a.niveauMin;
        if (!a.saison.isEmpty() && !enSaison(a.saison, jour)) return "hors saison";
        if (a.passage && !dePassage(a, jour)) return "pas en vitrine";
        int prix = prix(a, promo);
        if (solde < prix) return "il manque " + (prix - solde) + " po";
        return null;
    }

    // ---- Raretés : signe de forme et couleur (jamais rouge / vert), de commun à mythique.

    public static String signeRarete(int r) {
        return new String[]{"·", "◇", "◆", "✦", "★", "✺"}[Math.max(0, Math.min(MYTHIQUE, r))];
    }

    public static String nomRarete(int r) {
        return r >= MYTHIQUE ? "mythique" : Butin.nomRarete(r);
    }

    /** Argent, bleu, violet, orange, or, crème. */
    public static int couleurRarete(int r) {
        return new int[]{0xffadbac7, 0xff6cb6ff, 0xff9b8cff, 0xfff69d50, 0xfff5d76e, 0xfffff6cc}[Math.max(0, Math.min(MYTHIQUE, r))];
    }

    // ---- Saisons

    public static boolean enSaison(String saison, LocalDate j) {
        int m = j.getMonthValue(), d = j.getDayOfMonth();
        switch (saison) {
            case "": return true;
            case "hiver": return m == 12 || m == 1 || m == 2;
            case "printemps": return m >= 3 && m <= 5;
            case "ete": return m >= 6 && m <= 8;
            case "automne": return m >= 9 && m <= 11;
            case "frissons": return (m == 10 && d >= 15) || (m == 11 && d <= 5);
            case "fetes": return (m == 12 && d >= 10) || (m == 1 && d <= 6);
            default: return false;
        }
    }

    public static String nomSaison(String saison) {
        switch (saison) {
            case "ete": return "été";
            case "frissons": return "Nuit des frissons";
            case "fetes": return "Fêtes de l'hiver";
            default: return saison;
        }
    }

    /** Jours restants (aujourd'hui compris) ; 0 hors saison. */
    public static int joursRestants(String saison, LocalDate j) {
        if (saison.isEmpty()) return 0;
        int n = 0;
        while (n < 370 && enSaison(saison, j.plusDays(n))) n++;
        return n;
    }

    /** Premier jour de la prochaine saison après j, ou null. */
    public static LocalDate retour(String saison, LocalDate j) {
        for (int i = 1; i <= 370; i++)
            if (enSaison(saison, j.plusDays(i)) && !enSaison(saison, j.plusDays(i - 1))) return j.plusDays(i);
        return null;
    }

    // ---- Passages (comme le PC : graine « passage|id|aaaa-mm »)

    private static int debutPassage(String id, LocalDate j) {
        return 1 + new Hasard(Hasard.graine(String.format(java.util.Locale.ROOT, "passage|%s|%04d-%02d", id, j.getYear(), j.getMonthValue())))
                .suivant(26);
    }

    public static boolean dePassage(Article a, LocalDate j) {
        if (!a.passage) return false;
        int d = debutPassage(a.id, j);
        return j.getDayOfMonth() >= d && j.getDayOfMonth() < d + JOURS_PASSAGE;
    }

    public static int passageRestant(Article a, LocalDate j) {
        return dePassage(a, j) ? debutPassage(a.id, j) + JOURS_PASSAGE - j.getDayOfMonth() : 0;
    }

    public static LocalDate prochainPassage(Article a, LocalDate j) {
        if (!a.passage) return null;
        for (int i = 1; i <= 62; i++) if (dePassage(a, j.plusDays(i))) return j.plusDays(i);
        return null;
    }

    public static List<Article> passages(LocalDate j) {
        List<Article> r = new ArrayList<>();
        for (Article a : CATALOGUE) if (dePassage(a, j)) r.add(a);
        return r;
    }

    public static boolean disponible(Article a, LocalDate j) {
        return !a.recompense && enSaison(a.saison, j) && (!a.passage || dePassage(a, j));
    }

    /** Offres du jour tirées de la date (4, la première en promo) : les mêmes que Boutique.OffresDuJour sur le PC, sans la pluie. */
    public static List<Article> offresDuJour(LocalDate jour) {
        Hasard h = new Hasard(Hasard.graine("boutique|" + jour));
        List<Article> pool = new ArrayList<>();
        for (Article a : CATALOGUE) if (!a.permanent && !a.passage && enSaison(a.saison, jour)) pool.add(a);
        List<Article> r = new ArrayList<>();
        while (r.size() < 4 && !pool.isEmpty()) r.add(pool.remove(h.suivant(pool.size())));
        return r;
    }

    // ---- Collection, ensembles, récompenses

    public static boolean collectionnable(Article a) {
        return !CONSOMMABLE.equals(a.slot) && !a.recompense;
    }

    public static int collection(Collection<String> inventaire) {
        int n = 0;
        for (String id : new LinkedHashSet<>(inventaire)) {
            Article a = trouver(id);
            if (a != null && collectionnable(a)) n++;
        }
        return n;
    }

    public static int seuil(PalierCollection p) {
        return p.nombre <= 0 ? TOTAL_COLLECTION : p.nombre;
    }

    public static PalierCollection prochainPalierCollection(int possedes) {
        PalierCollection r = null;
        for (PalierCollection p : PALIERS_COLLECTION) if (seuil(p) > possedes && (r == null || seuil(p) < seuil(r))) r = p;
        return r;
    }

    public static Ensemble ensemble(String id) {
        for (Ensemble e : ENSEMBLES) if (e.id.equals(id)) return e;
        return null;
    }

    public static int possedes(Ensemble e, Collection<String> inventaire) {
        int n = 0;
        for (String p : e.pieces) if (inventaire.contains(p)) n++;
        return n;
    }

    public static boolean porteEnEntier(Ensemble e, Map<String, String> porte) {
        for (String p : e.pieces) {
            Article a = trouver(p);
            if (a == null || !p.equals(porte.get(a.slot))) return false;
        }
        return true;
    }

    /** Effets des ensembles portés en entier (à dessiner en plus). */
    public static List<String> bonusPortes(Map<String, String> porte) {
        List<String> r = new ArrayList<>();
        for (Ensemble e : ENSEMBLES) if (porteEnEntier(e, porte)) r.add(e.bonus);
        return r;
    }

    public static List<String> gagnees(Collection<String> inventaire) {
        List<String> r = new ArrayList<>();
        for (Ensemble e : ENSEMBLES) if (possedes(e, inventaire) == e.pieces.size()) r.add(e.idTitre());
        int n = collection(inventaire);
        for (PalierCollection p : PALIERS_COLLECTION) if (n >= seuil(p)) r.add(p.id);
        return r;
    }

    public static boolean peutPorter(Collection<String> inventaire, String slot, String id) {
        Article a = trouverTout(id);
        return a != null && a.slot.equals(slot) && (a.recompense ? gagnees(inventaire).contains(id) : inventaire.contains(id));
    }

    /** Nom du titre porté, ou null. */
    public static String nomTitre(String id) {
        Article a = trouverTout(id);
        return a != null && TITRE.equals(a.slot) ? a.nom : null;
    }

    // ---- Synchro compacte (comme Boutique.Garde / Deplier sur le PC)

    public static String garde(Collection<String> inventaire) {
        int max = 0;
        for (String id : inventaire) {
            Article a = trouver(id);
            if (a != null) max = Math.max(max, a.numero);
        }
        if (max == 0) return "";
        byte[] o = new byte[(max + 7) / 8];
        for (String id : inventaire) {
            Article a = trouver(id);
            if (a != null && a.numero > 0) o[(a.numero - 1) / 8] |= (byte) (1 << ((a.numero - 1) % 8));
        }
        return Base64.getUrlEncoder().withoutPadding().encodeToString(o);
    }

    public static List<String> deplier(String garde) {
        List<String> r = new ArrayList<>();
        if (garde == null || garde.isEmpty() || garde.length() > 400) return r;
        byte[] o;
        try {
            o = Base64.getUrlDecoder().decode(garde);
        } catch (IllegalArgumentException e) {
            return r;
        }
        for (int i = 0; i < o.length * 8; i++)
            if ((o[i / 8] >> (i % 8) & 1) != 0 && PAR_NUMERO.containsKey(i + 1)) r.add(PAR_NUMERO.get(i + 1));
        return r;
    }

    public static List<String> horsGarde(Collection<String> inventaire) {
        List<String> r = new ArrayList<>();
        for (String id : inventaire) {
            Article a = trouver(id);
            if (a == null || a.numero == 0) r.add(id);
        }
        return r;
    }

    /** Tirage déterministe, identique à Hasard (Boutique.cs) : FNV-1a 64 bits puis xorshift64*. */
    static final class Hasard {
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

        int suivant(int max) {
            return max <= 1 ? 0 : (int) Long.remainderUnsigned(brut(), max);
        }
    }
}
