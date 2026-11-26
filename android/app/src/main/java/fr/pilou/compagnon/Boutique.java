package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Boutique de Pilou (gratuite, virtuelle) : même catalogue que Boutique.cs sur le PC. Les pièces d'or (po)
 * se gagnent en quêtes ; aucun achat réel. Le PC tient le solde : le téléphone demande, le PC applique.
 * Rayons par emplacement ; dans chaque rayon, des rangées par palier de niveau (1, 5, 10, 15, 20, 30, 40, 50) :
 * le niveau ouvre la rangée, les po achètent l'objet. Les offres du jour sont une vitrine (la première à -25 %).
 */
public final class Boutique {
    public static final String TETE = "tete", YEUX = "yeux", COU = "cou", DOS = "dos", MAIN = "main", PIEDS = "pieds", COMPAGNON = "compagnon",
            EFFET = "effet", COULEUR = "couleur", FOND = "fond", BULLE = "bulle";
    public static final String[] SLOTS = {TETE, YEUX, COU, DOS, MAIN, PIEDS, COMPAGNON, EFFET, COULEUR, FOND, BULLE};
    /** « accessoire » : le chapeau historique (choisi sur le PC) ; « bonus » : actif dès qu'il est possédé ;
     *  « consommable » : s'achète plusieurs fois. Les trois forment le rayon « Spéciaux ». */
    public static final String ACCESSOIRE = "accessoire", BONUS = "bonus", CONSOMMABLE = "consommable", SPECIAUX = "speciaux";
    public static final String[] RAYONS = {TETE, YEUX, COU, DOS, MAIN, PIEDS, COMPAGNON, EFFET, COULEUR, FOND, BULLE, SPECIAUX};
    public static final int[] PALIERS = {1, 5, 10, 15, 20, 30, 40, 50};
    public static final String TRAINEE_ETOILES = "trainee-etoiles", CANNE_DOREE = "canne-doree", MARMITE_CUIVRE = "marmite-cuivre",
            PIERRE_CALME = "pierre-calme";

    public static final class Article {
        public final String id, nom, slot;
        public final int prix, niveauMin, rarete;
        public final boolean permanent;

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
        CATALOGUE = Collections.unmodifiableList(l);
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

    /** Articles d'un rayon dans la rangée d'un palier. */
    public static List<Article> rangee(String rayon, int palier) {
        List<Article> r = new ArrayList<>();
        for (Article a : CATALOGUE) if (rayonDe(a.slot).equals(rayon) && a.niveauMin == palier) r.add(a);
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
        for (String ray : RAYONS) if (!rangee(ray, palier).isEmpty()) r.add(ray);
        return r;
    }

    /** Ce qui se dessine sur Pilou lui-même (ni la couleur, ni le décor, ni le cadre de bulle). */
    public static boolean surPilou(String slot) {
        return !COULEUR.equals(slot) && !FOND.equals(slot) && !BULLE.equals(slot);
    }

    public static StyleBulle style(String id) {
        if (id == null) return null;
        switch (id) {
            case "bulle-doree": return new StyleBulle(0xffc9a227, 4, 0, 0, false);
            case "bulle-nuit": return new StyleBulle(0xff6cb6ff, 3, 0, 0xff16365e, true);
            case "bulle-pixel": return new StyleBulle(0xfff69d50, 5, 0, 0, false);
            case "bulle-nuages": return new StyleBulle(0xff9b8cff, 3, 12, 0, false);
            default: return null;
        }
    }

    public static Article trouver(String id) {
        for (Article a : CATALOGUE) if (a.id.equals(id)) return a;
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
            case ACCESSOIRE: return "Accessoires";
            case BONUS: return "Bonus";
            case CONSOMMABLE: return "Consommables";
            case SPECIAUX: return "Spéciaux";
            default: return slot;
        }
    }

    /** Ce qui empêche d'acheter (null : on peut). La rangée doit être ouverte ; plus de « pas aujourd'hui ». */
    public static String refus(Article a, int niveau, int solde, String promo, boolean possede) {
        if (possede && !a.slot.equals(CONSOMMABLE)) return "à toi";
        if (!ouvert(a, niveau)) return "niveau " + a.niveauMin;
        int prix = prix(a, promo);
        if (solde < prix) return "il manque " + (prix - solde) + " po";
        return null;
    }
}
