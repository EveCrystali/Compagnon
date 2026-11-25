package fr.pilou.compagnon;

import java.text.Normalizer;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** Police pixel 3 × 5 (chiffres, lettres sans accents, quelques signes), pour le jeu et les icônes. */
public final class Police {
    private static final Map<Character, String[]> G = new HashMap<>();

    static {
        String[] lettres = {
                "A", "010101111101101", "B", "110101110101110", "C", "011100100100011", "D", "110101101101110",
                "E", "111100110100111", "F", "111100110100100", "G", "011100101101011", "H", "101101111101101",
                "I", "111010010010111", "J", "001001001101010", "K", "101101110101101", "L", "100100100100111",
                "M", "101111111101101", "N", "110101101101101", "O", "010101101101010", "P", "110101110100100",
                "Q", "010101101110011", "R", "110101110101101", "S", "011100010001110", "T", "111010010010010",
                "U", "101101101101111", "V", "101101101101010", "W", "101101111111101", "X", "101101010101101",
                "Y", "101101010010010", "Z", "111001010100111",
                "0", "111101101101111", "1", "010110010010111", "2", "110001010100111", "3", "110001010001110",
                "4", "101101111001001", "5", "111100110001110", "6", "111100111101111", "7", "111001010010010",
                "8", "111101111101111", "9", "111101111001111",
                " ", "000000000000000", ".", "000000000000010", ",", "000000000010100", ":", "000010000010000",
                "!", "010010010000010", "?", "110001010000010", "-", "000000111000000", "+", "000010111010000",
                "/", "001001010100100", "'", "010010000000000", "×", "000101010101000", "(", "010100100100010",
                ")", "010001001001010", "%", "101001010100101", "*", "000101010101000", "#", "101111101111101",
                "✓", "000001001101010", "<", "001010100010001", ">", "100010001010100", "=", "000111000111000"};
        for (int i = 0; i < lettres.length; i += 2) {
            String b = lettres[i + 1];
            G.put(lettres[i].charAt(0), new String[]{b.substring(0, 3), b.substring(3, 6), b.substring(6, 9), b.substring(9, 12), b.substring(12, 15)});
        }
    }

    private Police() {
    }

    /** Majuscules sans accents (« Été » → « ETE »). */
    public static String simple(String s) {
        String n = Normalizer.normalize(s, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
        return n.replace('œ', 'O').replace('Œ', 'O').toUpperCase(Locale.ROOT);
    }

    /** Largeur d'un texte, en pixels de police (3 par lettre, 1 d'espace). */
    public static int largeur(String s) {
        int n = simple(s).length();
        return n == 0 ? 0 : n * 4 - 1;
    }

    /** Écrit s à partir de (x, y), pixel de taille p. */
    public static void ecrire(Dessin.Peintre pe, String s, float x, float y, float p, int couleur) {
        String t = simple(s);
        for (int i = 0; i < t.length(); i++) {
            String[] g = G.get(t.charAt(i));
            if (g == null) g = G.get('?');
            for (int r = 0; r < 5; r++)
                for (int k = 0; k < 3; k++)
                    if (g[r].charAt(k) == '1') {
                        float gx = x + (i * 4 + k) * p, gy = y + r * p;
                        pe.rect(gx, gy, gx + p, gy + p, couleur);
                    }
        }
    }

    /** Écrit centré sur cx, avec une ombre d'un pixel. */
    public static void centre(Dessin.Peintre pe, String s, float cx, float y, float p, int couleur, int ombre) {
        float x = cx - largeur(s) * p / 2;
        if (ombre != 0) ecrire(pe, s, x + p, y + p, p, ombre);
        ecrire(pe, s, x, y, p, couleur);
    }

    /** Motif de caractères ('0' vide, '1'… indice de palette). */
    public static void motif(Dessin.Peintre pe, String[] m, float x, float y, float p, int[] pal) {
        for (int r = 0; r < m.length; r++)
            for (int k = 0; k < m[r].length(); k++) {
                int v = m[r].charAt(k) - '0';
                if (v > 0 && v < pal.length && pal[v] != 0) pe.rect(x + k * p, y + r * p, x + (k + 1) * p, y + (r + 1) * p, pal[v]);
            }
    }
}
