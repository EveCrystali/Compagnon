package fr.pilou.compagnon;

/**
 * Ce que les niveaux ouvrent (même table que Progression.cs sur le PC) : les jeux, les stades d'évolution,
 * l'accès aux objets de la boutique. Les objets s'achètent en pièces d'or ; chaque niveau en rapporte.
 */
public final class Acces {
    /** id, nom, niveau d'accès. */
    public static final Object[][] JEUX = {
            {"etoile", "Étoile filante", 1}, {"bulles", "Bulles", 1}, {"peche", "Pêche", 2},
            {"tape", "Tape m'en cinq", 3}, {"cuisine", "Cuisine", 4}, {"chasse", "Chasse aux bugs", 5}};

    /** stade, nom (provisoire), niveau. */
    public static final Object[][] STADES = {{1, "Gouttelette", 1}, {2, "Pilou", 10}, {3, "Pilou Nimbus", 25}, {4, "Pilou Astral", 40}};

    private Acces() {
    }

    public static int niveauJeu(String id) {
        for (Object[] j : JEUX) if (j[0].equals(id)) return (Integer) j[2];
        return 1;
    }

    public static String nomJeu(String id) {
        for (Object[] j : JEUX) if (j[0].equals(id)) return (String) j[1];
        return id;
    }

    public static boolean jeuOuvert(String id, int niveau) {
        return niveau >= niveauJeu(id);
    }

    public static int stade(int niveau) {
        int s = 1;
        for (Object[] x : STADES) if (niveau >= (Integer) x[2]) s = (Integer) x[0];
        return s;
    }

    public static String nomStade(int stade) {
        for (Object[] x : STADES) if ((Integer) x[0] == stade) return (String) x[1];
        return "Pilou";
    }

    public static int poNiveau(int niveau) {
        return 20 + 5 * niveau;
    }
}
