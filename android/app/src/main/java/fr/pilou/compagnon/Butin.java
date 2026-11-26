package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

/**
 * Pêche, cuisine et récompenses, la partie sans dessin : même catalogue et mêmes règles que Butin.cs et
 * Recompenses.cs côté PC (23 prises, 30 recettes, plats inventés, niveaux jusqu'à 50).
 */
public final class Butin {
    private Butin() {
    }

    public static final int COMMUN = 0, PEU_COMMUN = 1, RARE = 2, EPIQUE = 3, LEGENDAIRE = 4;
    /** Seul (personne ne touche le bouchon), Pilou ferre une fois sur trois environ, jamais mieux que rare. */
    public static final double CHANCE_SEUL = 0.35;
    public static final int PLAFOND_SEUL = RARE;
    /** Le bouchon plonge : il reste 1,2 s pour le toucher. */
    public static final long FENETRE_MORSURE = 1200;
    /** Niveau d'accès en boutique de la canne dorée et de la marmite en cuivre (elles s'achètent désormais). */
    public static final int CANNE_DOREE = 30, MARMITE_CUIVRE = 35;

    public static final class Prise {
        public final String id, nom, saveur;
        public final int rarete, xp, niveauMin, couleur, clair, detail;
        public final String forme;

        Prise(String id, String nom, int rarete, int xp, int niveauMin, String forme, int couleur, int clair, int detail, String saveur) {
            this.id = id;
            this.nom = nom;
            this.rarete = rarete;
            this.xp = xp;
            this.niveauMin = niveauMin;
            this.forme = forme;
            this.couleur = couleur;
            this.clair = clair;
            this.detail = detail;
            this.saveur = saveur;
        }

        public boolean comestible() {
            return !saveur.isEmpty();
        }
    }

    public static final class Recette {
        public final String id, nom;
        public final int niveauMin, xp;
        public final String[] saveurs;

        Recette(String id, String nom, int niveauMin, String[] saveurs, int xp) {
            this.id = id;
            this.nom = nom;
            this.niveauMin = niveauMin;
            this.saveurs = saveurs;
            this.xp = xp;
        }
    }

    public static final class Plat {
        public final String id, nom;
        public final boolean decouverte, rate, inventee;
        public final int xp;
        public final List<String> utilises;

        Plat(String id, String nom, boolean decouverte, boolean rate, int xp, List<String> utilises, boolean inventee) {
            this.id = id;
            this.nom = nom;
            this.decouverte = decouverte;
            this.rate = rate;
            this.xp = xp;
            this.utilises = utilises;
            this.inventee = inventee;
        }
    }

    private static Prise p(String id, String nom, int r, int xp, int n, String f, int c, int cl, int d, String s) {
        return new Prise(id, nom, r, xp, n, f, c, cl, d, s);
    }

    public static final List<Prise> PRISES = List.of(
            p("goujon", "Goujon bleu", COMMUN, 3, 1, "poisson", 0xff4a8fdc, 0xffb4dbff, 0xff1f4f8a, "poisson"),
            p("ablette", "Ablette", COMMUN, 3, 1, "poisson", 0xffadbac7, 0xffe6ecf2, 0xff57606a, "poisson"),
            p("algue", "Algue frisée", COMMUN, 2, 1, "algue", 0xff3f7fd6, 0xff8fbaf0, 0xff1f4f8a, "algue"),
            p("botte", "Vieille botte", COMMUN, 1, 1, "botte", 0xff768390, 0xffadbac7, 0xff3b4654, ""),
            p("caillou", "Caillou tout lisse", COMMUN, 1, 1, "caillou", 0xff909dab, 0xffcdd9e5, 0xff57606a, ""),
            p("perche", "Perche rayée", PEU_COMMUN, 6, 2, "poisson", 0xfff2a94e, 0xffffd59a, 0xff7a4210, "poisson"),
            p("ecrevisse", "Écrevisse", PEU_COMMUN, 6, 2, "crabe", 0xffd9803a, 0xffffc89a, 0xff8a4a1f, "crustace"),
            p("spirale", "Coquillage spirale", PEU_COMMUN, 5, 2, "coquillage", 0xfff6f8fa, 0xffffffff, 0xffc9d1d9, "coquillage"),
            p("bouteille", "Bouteille à message", PEU_COMMUN, 8, 3, "bouteille", 0xff6cb6ff, 0xffd2eaff, 0xff1f4f8a, ""),
            p("truite", "Truite argentée", PEU_COMMUN, 7, 3, "poisson", 0xffb8c4d2, 0xffffffff, 0xff3b4654, "poisson"),
            p("anguille", "Anguille d'encre", RARE, 14, 5, "long", 0xff2a5ea8, 0xff6cb6ff, 0xff0d2a4d, "poisson"),
            p("crabe", "Crabe bleu", RARE, 14, 6, "crabe", 0xff3f7fd6, 0xff8fbaf0, 0xff0d2a4d, "crustace"),
            p("cle", "Clé rouillée", RARE, 12, 7, "cle", 0xffc97a28, 0xfff2a94e, 0xff7a4210, ""),
            p("pieuvre", "Pieuvre de poche", RARE, 16, 8, "pieuvre", 0xff9b8cff, 0xffd2caff, 0xff3a2a7a, "mollusque"),
            p("saumon", "Saumon des glaces", RARE, 18, 10, "poisson", 0xfff69d50, 0xffffd8b0, 0xff8a4a1f, "poisson"),
            p("lanterne", "Poisson-lanterne", EPIQUE, 30, 15, "poisson", 0xff1f4f8a, 0xffffd8b0, 0xfff69d50, "poisson"),
            p("hippocampe", "Hippocampe doré", EPIQUE, 32, 18, "hippocampe", 0xfff2a94e, 0xffffe7b8, 0xff7a4210, "poisson"),
            p("coffre", "Coffret englouti", EPIQUE, 35, 20, "coffre", 0xffc97a28, 0xfff2a94e, 0xff3b4654, ""),
            p("raie", "Raie étoilée", EPIQUE, 34, 22, "plat", 0xff6a5acd, 0xffd2caff, 0xffffd8b0, "poisson"),
            p("perle", "Perle de lune", LEGENDAIRE, 60, 25, "perle", 0xffe6ecf2, 0xffffffff, 0xff9b8cff, ""),
            p("carpe", "Carpe des pixels", LEGENDAIRE, 70, 30, "poisson", 0xfff69d50, 0xffffffff, 0xff2f7ed8, "poisson"),
            p("comete", "Poisson-comète", LEGENDAIRE, 80, 35, "long", 0xffffd8b0, 0xffffffff, 0xfff69d50, "poisson"),
            p("baleineau", "Baleineau de nuage", LEGENDAIRE, 100, 40, "baleine", 0xffb4dbff, 0xffffffff, 0xff4a8fdc, "poisson"));

    public static Prise trouver(String id) {
        for (Prise x : PRISES) if (x.id.equals(id)) return x;
        return null;
    }

    /** Signe de forme de chaque rareté (et un cadre différent au dessin), pas seulement une couleur. */
    public static String signe(int r) {
        return new String[]{"·", "◇", "◆", "✦", "★", "✺"}[r];
    }

    public static String nomRarete(int r) {
        return new String[]{"commun", "peu commun", "rare", "épique", "légendaire", "mythique"}[r];
    }

    public static double poids(int r, int niveau) {
        return poids(r, niveau, false);
    }

    public static double poids(int r, int niveau, boolean canneDoree) {
        switch (r) {
            case COMMUN: return 60;
            case PEU_COMMUN: return 26 + niveau * 0.3;
            case RARE: return 10 + niveau * 0.35;
            case EPIQUE: return 3 + niveau * 0.2;
            default: return 0.6 + niveau * 0.06 + (canneDoree ? 1.5 : 0);
        }
    }

    /** Une prise, ou null (Pilou seul a raté son coup). */
    public static Prise tirer(Random hasard, int niveau, boolean seul) {
        return tirer(hasard, niveau, seul, false);
    }

    public static Prise tirer(Random hasard, int niveau, boolean seul, boolean canneDoree) {
        if (seul && hasard.nextDouble() >= CHANCE_SEUL) return null;
        List<Prise> possibles = new ArrayList<>();
        for (Prise x : PRISES) if (x.niveauMin <= niveau && (!seul || x.rarete <= PLAFOND_SEUL)) possibles.add(x);
        double total = 0;
        for (Prise x : possibles) total += poids(x.rarete, niveau, canneDoree);
        double v = hasard.nextDouble() * total;
        for (Prise x : possibles) {
            v -= poids(x.rarete, niveau, canneDoree);
            if (v < 0) return x;
        }
        return possibles.get(possibles.size() - 1);
    }

    /** La première prise d'une espèce compte double (+5). */
    public static int xpPrise(Prise x, boolean nouvelle) {
        return nouvelle ? x.xp * 2 + 5 : x.xp;
    }

    // ---- Cuisine

    private static Recette r(String id, String nom, int n, int xp, String... s) {
        return new Recette(id, nom, n, s, xp);
    }

    public static final List<Recette> RECETTES = List.of(
            r("grille", "Poisson grillé", 1, 4, "poisson"),
            r("tartine", "Tartine de la rivière", 1, 3, "algue"),
            r("soupe", "Soupe du pêcheur", 2, 8, "poisson", "algue"),
            r("croquettes", "Croquettes croustillantes", 2, 8, "poisson", "poisson"),
            r("ecume", "Bouillon d'écume", 3, 6, "coquillage"),
            r("brochette", "Brochette des berges", 3, 7, "crustace"),
            r("papillote", "Papillote aux algues", 4, 11, "poisson", "algue", "algue"),
            r("maki", "Makis de pixels", 5, 10, "poisson", "algue"),
            r("gratin", "Gratin de la marée", 5, 12, "crustace", "poisson"),
            r("tempura", "Tempura du soir", 6, 12, "crustace", "algue"),
            r("chaudree", "Chaudrée des marins", 7, 16, "coquillage", "poisson", "algue"),
            r("beignets", "Beignets de calamar", 8, 14, "mollusque"),
            r("paella", "Riz de la lagune", 9, 20, "crustace", "coquillage", "poisson"),
            r("ceviche", "Ceviche à l'ambre", 10, 18, "poisson", "poisson", "algue"),
            r("ramen", "Ramen du clavier", 11, 22, "poisson", "algue", "mollusque"),
            r("bisque", "Bisque bleue", 12, 20, "crustace", "crustace"),
            r("fumet", "Fumet de minuit", 13, 18, "poisson", "coquillage"),
            r("tourte", "Tourte du port", 14, 24, "poisson", "poisson", "crustace"),
            r("carpaccio", "Carpaccio givré", 15, 14, "poisson"),
            r("curry", "Curry des îles", 16, 28, "crustace", "mollusque", "algue"),
            r("plateau", "Plateau de la criée", 18, 30, "coquillage", "coquillage", "crustace"),
            r("bouillabaisse", "Marmite de la calanque", 20, 40, "poisson", "poisson", "crustace", "coquillage"),
            r("risotto", "Risotto d'encre", 22, 30, "mollusque", "algue"),
            r("feuillete", "Feuilleté des abysses", 24, 36, "poisson", "mollusque", "crustace"),
            r("banquet", "Banquet des mouettes", 26, 38, "poisson", "poisson", "poisson"),
            r("lune", "Velouté clair de lune", 28, 34, "coquillage", "algue", "algue"),
            r("etoile", "Tarte étoilée", 30, 42, "poisson", "crustace", "algue"),
            r("festin", "Festin du grand lac", 35, 60, "poisson", "crustace", "mollusque", "coquillage"),
            r("nuage", "Soufflé de nuage", 40, 55, "poisson", "algue", "coquillage"),
            r("legende", "Plat de légende", 45, 90, "poisson", "poisson", "crustace", "mollusque", "algue"));

    private static final String[] PREPARATIONS = {
            "Soupe", "Poêlée", "Tartine", "Brochette", "Velouté", "Gratin", "Beignets", "Papillote", "Salade", "Tourte", "Compotée",
            "Rouleaux", "Fricassée", "Bouchées", "Galette", "Croustillant", "Mijoté", "Crumble"};
    private static final String[] TOUCHES = {
            "du dimanche", "à l'ancienne", "de minuit", "façon Pilou", "aux étoiles", "du pêcheur", "en croûte de sel", "du matin",
            "au beurre noisette", "des grands jours", "à la vapeur", "au feu de bois", "du lundi", "de la lagune", "en habit de fête",
            "au clair de lune", "des copains", "sans prétention"};

    private static String de(String mot) {
        return "aeiouyéèêàâîôûh".indexOf(Character.toLowerCase(mot.charAt(0))) >= 0 ? "d'" + mot : "de " + mot;
    }

    public static String inventer(Random hasard, Prise ingredient) {
        String nom = Character.toLowerCase(ingredient.nom.charAt(0)) + ingredient.nom.substring(1);
        return PREPARATIONS[hasard.nextInt(PREPARATIONS.length)] + " " + de(nom) + " " + TOUCHES[hasard.nextInt(TOUCHES.length)];
    }

    /** Ingrédients pris pour cette recette (le plus commun d'abord), ou null si le stock ne suffit pas. */
    public static List<String> choisir(Recette rec, Map<String, Integer> stock) {
        Map<String, Integer> reste = new HashMap<>(stock);
        List<String> pris = new ArrayList<>();
        for (String saveur : rec.saveurs) {
            Prise choisie = null;
            for (Map.Entry<String, Integer> e : reste.entrySet()) {
                Prise x = trouver(e.getKey());
                if (x == null || e.getValue() <= 0 || !x.saveur.equals(saveur)) continue;
                if (choisie == null || x.rarete < choisie.rarete || (x.rarete == choisie.rarete && x.xp < choisie.xp)
                        || (x.rarete == choisie.rarete && x.xp == choisie.xp && x.id.compareTo(choisie.id) < 0))
                    choisie = x;
            }
            if (choisie == null) return null;
            reste.put(choisie.id, reste.get(choisie.id) - 1);
            pris.add(choisie.id);
        }
        return pris;
    }

    public static boolean peutCuisiner(Map<String, Integer> stock) {
        for (Map.Entry<String, Integer> e : stock.entrySet()) {
            Prise x = trouver(e.getKey());
            if (e.getValue() > 0 && x != null && x.comestible()) return true;
        }
        return false;
    }

    /** Chance de rater (fumée noire) : 8 %, moins avec le niveau ; remuer la marmite l'annule. */
    public static double chanceRate(int niveau, boolean remue) {
        return chanceRate(niveau, remue, false);
    }

    public static double chanceRate(int niveau, boolean remue, boolean marmiteCuivre) {
        return remue ? 0 : Math.max(0.02, 0.08 - (marmiteCuivre ? 0.04 : 0) - niveau * 0.0005);
    }

    /** Une recette du livre si le stock le permet (plutôt une pas encore faite), sinon un plat inventé. */
    public static Plat cuisiner(Random hasard, int niveau, Map<String, Integer> stock, Collection<String> connues, boolean remue) {
        return cuisiner(hasard, niveau, stock, connues, remue, false);
    }

    public static Plat cuisiner(Random hasard, int niveau, Map<String, Integer> stock, Collection<String> connues, boolean remue, boolean marmiteCuivre) {
        if (!peutCuisiner(stock)) return null;
        List<Recette> possibles = new ArrayList<>();
        List<List<String>> pris = new ArrayList<>();
        for (Recette rec : RECETTES) {
            if (rec.niveauMin > niveau) continue;
            List<String> x = choisir(rec, stock);
            if (x == null) continue;
            possibles.add(rec);
            pris.add(x);
        }
        List<Integer> nouvelles = new ArrayList<>();
        for (int i = 0; i < possibles.size(); i++) if (!connues.contains(possibles.get(i).id)) nouvelles.add(i);
        boolean rate = hasard.nextDouble() < chanceRate(niveau, remue, marmiteCuivre);
        int choix = -1;
        if (!nouvelles.isEmpty() && hasard.nextDouble() < 0.75) choix = nouvelles.get(hasard.nextInt(nouvelles.size()));
        else if (!possibles.isEmpty() && hasard.nextDouble() < 0.5) choix = hasard.nextInt(possibles.size());
        if (choix >= 0) {
            Recette rec = possibles.get(choix);
            boolean neuf = !connues.contains(rec.id);
            if (rate) return new Plat(rec.id, rec.nom, false, true, 1, pris.get(choix), false);
            return new Plat(rec.id, rec.nom, neuf, false, neuf ? rec.xp * 2 : rec.xp, pris.get(choix), false);
        }
        List<Prise> comestibles = new ArrayList<>();
        for (Map.Entry<String, Integer> e : stock.entrySet()) {
            Prise x = trouver(e.getKey());
            if (e.getValue() > 0 && x != null && x.comestible()) comestibles.add(x);
        }
        comestibles.sort(Comparator.comparingInt((Prise x) -> x.rarete).thenComparing(x -> x.id));
        int plusCommune = comestibles.get(0).rarete;
        List<Prise> memeRang = new ArrayList<>();
        for (Prise x : comestibles) if (x.rarete == plusCommune) memeRang.add(x);
        Prise ingredient = memeRang.get(hasard.nextInt(memeRang.size()));
        String nom = inventer(hasard, ingredient);
        String id = "inv:" + nom;
        if (rate) return new Plat(id, nom, false, true, 1, List.of(ingredient.id), true);
        boolean decouverte = !connues.contains(id);
        return new Plat(id, nom, decouverte, false, 2 + ingredient.xp + (decouverte ? 4 : 0), List.of(ingredient.id), true);
    }

    // ---- Niveaux et récompenses (Profil.cs, Recompenses.cs)

    /** Courbe : xp(n) = 25·(n−1)² (comme Profil.cs). Le niveau affiché ne descend jamais sous le niveau acquis (Gains.niveau). */
    public static int niveau(int xp) {
        return (int) Math.floor(Math.sqrt(Math.max(0, xp) / 25.0)) + 1;
    }

    public static int xpPourNiveau(int niveau) {
        return 25 * (niveau - 1) * (niveau - 1);
    }

    /** Catalogue : niveau, type, nom. */
    public static final String[][] RECOMPENSES = {
            {"1", "titre", "Petit pixel"}, {"1", "couleur", "Bleu ciel"}, {"1", "accessoire", "Feuille d'automne"},
            {"2", "accessoire", "Nœud papillon"}, {"3", "titre", "Apprenti"}, {"3", "accessoire", "Casque audio"},
            {"4", "accessoire", "Bonnet de laine"}, {"5", "titre", "Compagnon fidèle"}, {"5", "accessoire", "Lunettes de soleil"},
            {"6", "couleur", "Bleu nuit"}, {"7", "accessoire", "Couronne"}, {"8", "titre", "Gardien des sessions"},
            {"8", "couleur", "Ambre"}, {"9", "effet", "Traînée d'étoiles"}, {"10", "couleur", "Argent"},
            {"12", "titre", "Légende du bureau"}, {"12", "couleur", "Aurore"}, {"13", "titre", "Pêcheur du dimanche"},
            {"14", "accessoire", "Chapeau de pêcheur"}, {"16", "titre", "Marmiton"}, {"18", "accessoire", "Toque de chef"},
            {"20", "titre", "Pêcheur aguerri"}, {"20", "couleur", "Lagon"}, {"22", "accessoire", "Tablier"},
            {"24", "titre", "Chef de pixels"}, {"26", "couleur", "Braise"}, {"27", "accessoire", "Étoile de mer"},
            {"28", "titre", "Dompteur d'anguilles"}, {"30", "effet", "Canne dorée (plus de prises légendaires)"},
            {"32", "titre", "Grand cuisinier"}, {"32", "couleur", "Nacre"}, {"35", "effet", "Marmite en cuivre (moins de plats brûlés)"},
            {"36", "titre", "Maître des marées"}, {"40", "titre", "Étoile des abysses"}, {"40", "couleur", "Abysse"},
            {"45", "titre", "Légende des lacs"}, {"50", "titre", "Pilou éternel"}, {"50", "couleur", "Comète"}};

    public static String titre(int niveau) {
        String t = "Petit pixel";
        for (String[] r : RECOMPENSES) if (r[1].equals("titre") && Integer.parseInt(r[0]) <= niveau) t = r[2];
        return t;
    }

    public static String nomPrise(Prise x) {
        return signe(x.rarete) + " " + x.nom + " (" + nomRarete(x.rarete) + ")";
    }

    static String minuscule(String s) {
        return s.toLowerCase(Locale.ROOT);
    }
}
