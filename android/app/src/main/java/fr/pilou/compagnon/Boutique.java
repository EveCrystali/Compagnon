package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Boutique de Pilou (gratuite, virtuelle) : même catalogue que Boutique.cs sur le PC. Les pièces d'or (po)
 * se gagnent en quêtes ; aucun achat réel. Le PC tient le solde : le téléphone demande, le PC applique.
 * Les objets ne sont pas encore dessinés : la boutique les montre par leur nom et un signe d'emplacement.
 */
public final class Boutique {
    public static final String TETE = "tete", YEUX = "yeux", COU = "cou", DOS = "dos", MAIN = "main", PIEDS = "pieds", COMPAGNON = "compagnon",
            EFFET = "effet", COULEUR = "couleur";
    public static final String[] SLOTS = {TETE, YEUX, COU, DOS, MAIN, PIEDS, COMPAGNON, EFFET, COULEUR};
    /** « accessoire » : le chapeau historique (choisi sur le PC) ; « bonus » : actif dès qu'il est possédé ;
     *  « consommable » : s'achète plusieurs fois. */
    public static final String ACCESSOIRE = "accessoire", BONUS = "bonus", CONSOMMABLE = "consommable";
    public static final String[] RAYONS = {ACCESSOIRE, TETE, YEUX, COU, DOS, MAIN, PIEDS, COMPAGNON, EFFET, COULEUR, BONUS, CONSOMMABLE};
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

    public static final List<Article> CATALOGUE;

    static {
        List<Article> l = new ArrayList<>();
        l.add(new Article("casquette", "Casquette", TETE, 80, 1, Butin.COMMUN, true));
        l.add(new Article("bandeau-ninja", "Bandeau de ninja", TETE, 120, 2, Butin.PEU_COMMUN, false));
        l.add(new Article("chapeau-pirate", "Chapeau de pirate", TETE, 220, 4, Butin.RARE, false));
        l.add(new Article("haut-de-forme", "Haut-de-forme", TETE, 260, 5, Butin.RARE, false));
        l.add(new Article("couronne-fleurs", "Couronne de fleurs", TETE, 180, 3, Butin.PEU_COMMUN, false));
        l.add(new Article("cornes-viking", "Casque à cornes", TETE, 320, 8, Butin.EPIQUE, false));
        l.add(new Article("chapeau-sorcier", "Chapeau de sorcier", TETE, 380, 10, Butin.EPIQUE, false));
        l.add(new Article("aureole", "Auréole", TETE, 450, 15, Butin.LEGENDAIRE, false));
        l.add(new Article("lunettes-rondes", "Lunettes rondes", YEUX, 90, 1, Butin.COMMUN, true));
        l.add(new Article("monocle", "Monocle", YEUX, 200, 6, Butin.RARE, false));
        l.add(new Article("masque-plongee", "Masque de plongée", YEUX, 160, 3, Butin.PEU_COMMUN, false));
        l.add(new Article("echarpe", "Écharpe", COU, 70, 1, Butin.COMMUN, true));
        l.add(new Article("medaille", "Médaille", COU, 300, 9, Butin.EPIQUE, false));
        l.add(new Article("cape", "Cape", DOS, 280, 7, Butin.RARE, false));
        l.add(new Article("tasse-cafe", "Tasse de café", MAIN, 60, 1, Butin.COMMUN, true));
        l.add(new Article("parapluie", "Parapluie", MAIN, 110, 2, Butin.PEU_COMMUN, false));
        l.add(new Article("ballon-helium", "Ballon", MAIN, 130, 3, Butin.PEU_COMMUN, false));
        l.add(new Article("baguette", "Baguette magique", MAIN, 340, 11, Butin.EPIQUE, false));
        // Météo : ce qui protège de la pluie, du froid et de la chaleur (Meteo.java).
        l.add(new Article("impermeable", "Imperméable", DOS, 180, 3, Butin.PEU_COMMUN, false));
        l.add(new Article("bottes-pluie", "Bottes de pluie", PIEDS, 90, 2, Butin.COMMUN, false));
        l.add(new Article("moufles", "Moufles", MAIN, 80, 2, Butin.COMMUN, false));
        l.add(new Article("eventail", "Éventail", MAIN, 100, 3, Butin.PEU_COMMUN, false));
        l.add(new Article("parapluie-etoile", "Parapluie étoilé", MAIN, 420, 14, Butin.EPIQUE, false));
        l.add(new Article("petit-poisson-bocal", "Poisson en bocal", COMPAGNON, 240, 5, Butin.RARE, false));
        l.add(new Article("petit-chat", "Petit chat", COMPAGNON, 520, 12, Butin.LEGENDAIRE, false));
        l.add(new Article("trainee-coeurs", "Traînée de cœurs", EFFET, 300, 6, Butin.RARE, false));
        l.add(new Article("trainee-notes", "Traînée de notes", EFFET, 340, 8, Butin.EPIQUE, false));
        l.add(new Article("aura", "Aura", EFFET, 600, 18, Butin.LEGENDAIRE, false));
        l.add(new Article("sable", "Couleur sable", COULEUR, 150, 1, Butin.COMMUN, true));
        l.add(new Article("ardoise", "Couleur ardoise", COULEUR, 150, 2, Butin.COMMUN, true));
        l.add(new Article("lavande", "Couleur lavande", COULEUR, 200, 4, Butin.PEU_COMMUN, false));
        l.add(new Article("glacier", "Couleur glacier", COULEUR, 220, 6, Butin.RARE, false));
        l.add(new Article("corail-orange", "Couleur corail", COULEUR, 250, 8, Butin.RARE, false));
        // Anciennes récompenses de niveau (Boutique.cs : même prix, même niveau d'accès).
        String[] acc = {"feuille", "Feuille d'automne", "1", "noeud", "Nœud papillon", "2", "casque", "Casque audio", "3",
                "bonnet", "Bonnet de laine", "4", "lunettes", "Lunettes de soleil", "5", "couronne", "Couronne", "7",
                "chapeaupeche", "Chapeau de pêcheur", "14", "toque", "Toque de chef", "18", "tablier", "Tablier", "22",
                "etoilemer", "Étoile de mer", "27"};
        for (int i = 0; i < acc.length; i += 3) {
            int n = Integer.parseInt(acc[i + 2]);
            l.add(new Article(acc[i], acc[i + 1], ACCESSOIRE, Math.min(600, 60 + 15 * n), n, rang(n), true));
        }
        String[] cou = {"nuit", "Couleur bleu nuit", "6", "ambre", "Couleur ambre", "8", "argent", "Couleur argent", "10",
                "aurore", "Couleur aurore", "12", "lagon", "Couleur lagon", "20", "braise", "Couleur braise", "26",
                "nacre", "Couleur nacre", "32", "abysse", "Couleur abysse", "40", "comete", "Couleur comète", "50"};
        for (int i = 0; i < cou.length; i += 3) {
            int n = Integer.parseInt(cou[i + 2]);
            l.add(new Article("couleur-" + cou[i], cou[i + 1], COULEUR, Math.min(600, 100 + 10 * n), n, rang(n), true));
        }
        l.add(new Article(TRAINEE_ETOILES, "Traînée d'étoiles", EFFET, 220, 9, Butin.RARE, true));
        l.add(new Article(CANNE_DOREE, "Canne dorée (plus de prises légendaires)", BONUS, 500, 30, Butin.LEGENDAIRE, true));
        l.add(new Article(MARMITE_CUIVRE, "Marmite en cuivre (moins de plats brûlés)", BONUS, 520, 35, Butin.LEGENDAIRE, true));
        l.add(new Article(PIERRE_CALME, "Pierre de calme (retient une évolution)", CONSOMMABLE, 150, 9, Butin.PEU_COMMUN, true));
        CATALOGUE = Collections.unmodifiableList(l);
    }

    private Boutique() {
    }

    private static int rang(int niveau) {
        return niveau <= 3 ? Butin.COMMUN : niveau <= 8 ? Butin.PEU_COMMUN : niveau <= 15 ? Butin.RARE : niveau <= 30 ? Butin.EPIQUE : Butin.LEGENDAIRE;
    }

    public static Article trouver(String id) {
        for (Article a : CATALOGUE) if (a.id.equals(id)) return a;
        return null;
    }

    /** Prix du jour : -25 % pour l'objet en promo (le premier des offres du PC). */
    public static int prix(Article a, String promo) {
        return a.id.equals(promo) ? a.prix * 3 / 4 : a.prix;
    }

    /** En vente aujourd'hui : toujours disponible, ou dans les offres du jour envoyées par le PC. */
    public static boolean enVente(Article a, List<String> offres) {
        return a.permanent || offres.contains(a.id);
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
            case ACCESSOIRE: return "◆";
            case BONUS: return "★";
            case CONSOMMABLE: return "◇";
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
            case COMPAGNON: return "Compagnon";
            case EFFET: return "Effet";
            case COULEUR: return "Couleur";
            case ACCESSOIRE: return "Accessoires";
            case BONUS: return "Bonus";
            case CONSOMMABLE: return "Consommables";
            default: return slot;
        }
    }

    /** Ce qui empêche d'acheter (null : on peut). */
    public static String refus(Article a, int niveau, int solde, List<String> offres, String promo, boolean possede) {
        if (possede && !a.slot.equals(CONSOMMABLE)) return "à toi";
        if (!enVente(a, offres)) return "pas aujourd'hui";
        if (niveau < a.niveauMin) return "niveau " + a.niveauMin;
        int prix = prix(a, promo);
        if (solde < prix) return "il manque " + (prix - solde) + " po";
        return null;
    }
}
