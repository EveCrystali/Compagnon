package fr.pilou.compagnon;

/**
 * Dessin de « Chasse aux bugs » par rectangles (Dessin.Peintre) : sur un Canvas Android, ou dans une
 * image de contrôle sur JVM. Palette bleu / orange / argent / neutres (jamais rouge-vert) ; chaque chose
 * a sa forme : bugs (3 silhouettes), étincelles (traits), tirs des bugs (petites croix), boucliers { }.
 */
public final class ChasseDessin {
    static final int NUIT = 0xff0f141a, NUIT2 = 0xff161b22, ENCRE = 0xff1c2128, BLANC = 0xfff6f8fa, GRIS = 0xff768390,
            ARGENT = 0xffb8c4d2, BLEU = 0xff6cb6ff, BLEU_CLAIR = 0xffb4dbff, BLEU_FONCE = 0xff2f7ed8, ORANGE = 0xfff69d50,
            ORANGE_CLAIR = 0xffffd8b0, BRUN = 0xff8a4a1f, VOILE = 0xb30f141a;

    /** Zones à toucher (unités du monde) : x, y, largeur, hauteur. */
    public static final float[] PAUSE = {104, 3, 13, 11}, REJOUER = {14, 136, 44, 14}, QUITTER = {62, 136, 44, 14};

    // Bugs : 1 corps, 2 yeux, 3 reflet. Deux images chacun (pattes).
    static final String[][][] BUGS = {
            {   // scarabée
                    {"010000010", "001000100", "011111110", "123111321", "111111111", "101111101", "100000001"},
                    {"010000010", "001000100", "011111110", "123111321", "111111111", "101111101", "010000010"}},
            {   // araignée
                    {"001000100", "100111001", "011232110", "001111100", "011111110", "100101001", "010000010"},
                    {"001000100", "010111010", "001232100", "101111101", "011111110", "010101010", "100000001"}},
            {   // ver
                    {"000000000", "001111000", "012311110", "011111111", "000001111", "000000110", "000000000"},
                    {"000000000", "000111100", "011231110", "011111111", "001111000", "000110000", "000000000"}}};

    static final String[] BOSS = {
            "000001000000100000",
            "000000100001000000",
            "001111111111111100",
            "011111111111111110",
            "112211111111112211",
            "112311111111113211",
            "111111111111111111",
            "111114444444411111",
            "011111111111111110",
            "101011111111110101",
            "100100100100100101"};

    static final String[] CAFE = {"000202", "002020", "111110", "131011", "111110", "011100"};
    static final String[] TESTS = {"111111", "100001", "100011", "110101", "101001", "111111"};
    static final String[] VIE = {"01110", "11111", "12121", "11111"};

    private ChasseDessin() {
    }

    static final String[] ID_BUGS = {"bug-scarabee", "bug-araignee", "bug-ver"};

    /** Sprite HD de la banque (deux fois plus fin que les unités du jeu), ou false s'il manque. */
    static boolean hd(Dessin.Peintre pe, String id, float x, float y, float p, long t) {
        Sprites.Sprite s = Sprites.banque().get(id);
        if (s == null) return false;
        Sprites.dessiner(pe, s, x, y, p, t, false);
        return true;
    }

    public static void dessiner(Dessin.Peintre pe, Chasse c, float ox, float oy, float k, long t, int meilleur) {
        // Fond : nuit et étoiles qui défilent.
        pe.rect(ox, oy, ox + Chasse.W * k, oy + Chasse.H * k, NUIT);
        for (int i = 0; i < 46; i++) {
            float sx = (i * 37 + 11) % 120, vitesse = 4 + (i % 3) * 5;
            float sy = ((i * 53 + 7) + t / 1000f * vitesse) % Chasse.H;
            int col = i % 3 == 0 ? GRIS : i % 3 == 1 ? NUIT2 + 0x202020 : 0xff3b4654;
            pe.rect(ox + sx * k, oy + sy * k, ox + (sx + 1) * k, oy + (sy + 1) * k, col);
        }
        // Ligne de la prod.
        for (float x = 0; x < Chasse.W; x += 4)
            pe.rect(ox + x * k, oy + (Chasse.LIGNE_PROD + 1) * k, ox + (x + 2) * k, oy + (Chasse.LIGNE_PROD + 1.5f) * k, 0xff2d333b);

        // Boucliers en accolades.
        for (int n = 0; n < 3; n++) {
            float bx = Chasse.boucliersX(n);
            for (int r = 0; r < c.boucliers[n].length; r++)
                for (int q = 0; q < c.boucliers[n][r].length; q++) {
                    int pv = c.boucliers[n][r][q];
                    if (pv == 0) continue;
                    float x = bx + q * Chasse.CASE, y = Chasse.BOUCLIER_Y + r * Chasse.CASE;
                    pe.rect(ox + x * k, oy + y * k, ox + (x + Chasse.CASE) * k, oy + (y + Chasse.CASE) * k, pv == 2 ? ARGENT : GRIS);
                }
        }

        // Bugs.
        int image = (int) (t / 380) % 2;
        for (Chasse.Bug b : c.bugs) {
            if (!b.vivant) continue;
            int corps = b.type == 0 ? ORANGE : b.type == 1 ? BLEU : ARGENT;
            int reflet = b.type == 0 ? ORANGE_CLAIR : b.type == 1 ? BLEU_CLAIR : BLANC;
            float dy = (float) Math.sin(t / 260.0 + b.col) * 0.8f;
            if (!hd(pe, ID_BUGS[b.type], ox + b.x * k, oy + (b.y + dy) * k, k / 2, t + b.col * 150L))
                Police.motif(pe, BUGS[b.type][image], ox + b.x * k, oy + (b.y + dy) * k, k, new int[]{0, corps, ENCRE, reflet});
        }
        // Le Bug de prod.
        if (c.boss != null) {
            Chasse.Boss b = c.boss;
            boolean eclair = (t / 120) % 2 == 0 && b.pv < b.pvMax / 3;
            if (eclair || !hd(pe, "bug-prod", ox + b.x * k, oy + b.y * k, k, t))
                Police.motif(pe, BOSS, ox + b.x * k, oy + b.y * k, 2 * k, new int[]{0, eclair ? ORANGE_CLAIR : ORANGE, ENCRE, BLANC, BRUN});
            // Barre de vie : contour argent, remplissage orange.
            float l = 60, x0 = (Chasse.W - l) / 2, y0 = 18;
            pe.rect(ox + (x0 - 1) * k, oy + (y0 - 1) * k, ox + (x0 + l + 1) * k, oy + (y0 + 4) * k, ARGENT);
            pe.rect(ox + x0 * k, oy + y0 * k, ox + (x0 + l) * k, oy + (y0 + 3) * k, ENCRE);
            pe.rect(ox + x0 * k, oy + y0 * k, ox + (x0 + l * b.pv / (float) b.pvMax) * k, oy + (y0 + 3) * k, ORANGE);
            Police.centre(pe, "BUG DE PROD", ox + Chasse.W / 2 * k, oy + 24 * k, k, ORANGE_CLAIR, ENCRE);
        }

        // Tirs : étincelles de Pilou (traits orange), tirs des bugs (croix bleu clair cernées).
        for (Chasse.Tir s : c.tirs) {
            if (s.y < -50) continue;
            if (s.ami) {
                pe.rect(ox + s.x * k, oy + s.y * k, ox + (s.x + 1) * k, oy + (s.y + 4) * k, ORANGE);
                pe.rect(ox + s.x * k, oy + s.y * k, ox + (s.x + 1) * k, oy + (s.y + 1) * k, ORANGE_CLAIR);
            } else {
                float x = s.x - 1, y = s.y - 1;
                Police.motif(pe, new String[]{"101", "010", "101"}, ox + x * k, oy + y * k, k, new int[]{0, BLEU_CLAIR});
            }
        }
        // Bonus.
        for (Chasse.Bonus b : c.bonus)
            if (!hd(pe, b.cafe ? "bonus-cafe" : "bonus-tests", ox + b.x * k, oy + b.y * k, k / 2, t))
                Police.motif(pe, b.cafe ? CAFE : TESTS, ox + b.x * k, oy + b.y * k, k,
                        b.cafe ? new int[]{0, ORANGE, ARGENT, ORANGE_CLAIR} : new int[]{0, BLEU, 0, 0});
        // Éclats.
        for (Chasse.Eclat e : c.eclats)
            pe.rect(ox + e.x * k, oy + e.y * k, ox + (e.x + 1) * k, oy + (e.y + 1) * k, e.couleur);

        // Pilou.
        boolean clignote = c.invulnerable > 0 && (t / 90) % 2 == 0;
        if (!clignote) {
            String expr = c.phase == Chasse.Phase.FIN ? "dort" : c.invulnerable > 0.6f ? "grimace"
                    : c.phase == Chasse.Phase.ENTRE_VAGUES ? "fete" : "concentre";
            // Pilou : son corps (≈ 32 pixels de la grille 48 × 56) fait la largeur du joueur ; pieds au bas de la zone
            // (dernière rangée des pieds : 52 avec la marge d'un pixel).
            float p = Chasse.JOUEUR_L / 32f, sx = c.joueurX + Chasse.JOUEUR_L / 2 - (Dessin.W + 2) * p / 2;
            Dessin.dessiner(pe, ox + sx * k, oy + (Chasse.JOUEUR_Y + 13 - 53 * p) * k, p * k, expr, t, "bleu", "aucun", false, 0);
        }
        if (c.tests > 0) {   // bouclier « tests verts » : anneau bleu en pointillé
            float cx = c.joueurX + Chasse.JOUEUR_L / 2, cy = Chasse.JOUEUR_Y + 6;
            for (int i = 0; i < 16; i++) {
                double a = i * Math.PI / 8 + t / 400.0;
                float x = cx + (float) Math.cos(a) * 10, y = cy + (float) Math.sin(a) * 9;
                pe.rect(ox + x * k, oy + y * k, ox + (x + 1) * k, oy + (y + 1) * k, BLEU_CLAIR);
            }
        }

        // Bandeau du haut : score, vague, vies, pause.
        pe.rect(ox, oy, ox + Chasse.W * k, oy + 15 * k, NUIT2);
        Police.ecrire(pe, String.format(java.util.Locale.ROOT, "%06d", c.score), ox + 3 * k, oy + 3 * k, k, BLANC);
        Police.ecrire(pe, "MAX " + Math.max(meilleur, c.score), ox + 3 * k, oy + 9 * k, k, GRIS);
        Police.centre(pe, "VAGUE " + Math.max(1, c.vague), ox + 60 * k, oy + 3 * k, k, BLEU_CLAIR, 0);
        for (int i = 0; i < c.vies; i++)
            Police.motif(pe, VIE, ox + (52 + i * 6) * k, oy + 9 * k, k, new int[]{0, BLEU, ENCRE});
        if (c.cafe > 0) Police.motif(pe, CAFE, ox + 84 * k, oy + 4 * k, k, new int[]{0, ORANGE, ARGENT, ORANGE_CLAIR});
        if (c.tests > 0) Police.motif(pe, TESTS, ox + 92 * k, oy + 4 * k, k, new int[]{0, BLEU, 0, 0});
        bouton(pe, ox, oy, k, PAUSE, c.phase == Chasse.Phase.PAUSE ? ">" : "", ARGENT);
        if (c.phase != Chasse.Phase.PAUSE) {
            pe.rect(ox + 108 * k, oy + 5 * k, ox + 110 * k, oy + 12 * k, ARGENT);
            pe.rect(ox + 112 * k, oy + 5 * k, ox + 114 * k, oy + 12 * k, ARGENT);
        }

        // Écrans par-dessus.
        float cx = ox + Chasse.W / 2 * k;
        switch (c.phase) {
            case ACCUEIL: {
                voile(pe, ox, oy, k);
                Police.centre(pe, "CHASSE", cx, oy + 52 * k, 3 * k, ORANGE, ENCRE);
                Police.centre(pe, "AUX BUGS", cx, oy + 72 * k, 3 * k, BLEU, ENCRE);
                for (int i = 0; i < 3; i++)
                    if (!hd(pe, ID_BUGS[i], ox + (40 + i * 16) * k, oy + 96 * k, k / 2, t))
                        Police.motif(pe, BUGS[i][image], ox + (40 + i * 16) * k, oy + 96 * k, k,
                                new int[]{0, i == 0 ? ORANGE : i == 1 ? BLEU : ARGENT, ENCRE, BLANC});
                Police.centre(pe, "30   20   10", cx, oy + 106 * k, k, GRIS, 0);
                Police.centre(pe, "GLISSE POUR BOUGER", cx, oy + 122 * k, k, BLANC, 0);
                Police.centre(pe, "PILOU TIRE TOUT SEUL", cx, oy + 129 * k, k, BLANC, 0);
                Police.motif(pe, CAFE, ox + 30 * k, oy + 140 * k, k, new int[]{0, ORANGE, ARGENT, ORANGE_CLAIR});
                Police.ecrire(pe, "TIR RAPIDE", ox + 39 * k, oy + 141 * k, k, ORANGE_CLAIR);
                Police.motif(pe, TESTS, ox + 30 * k, oy + 149 * k, k, new int[]{0, BLEU, 0, 0});
                Police.ecrire(pe, "TESTS OK : BOUCLIER", ox + 39 * k, oy + 150 * k, k, BLEU_CLAIR);
                if ((t / 500) % 2 == 0) Police.centre(pe, "TOUCHE POUR JOUER", cx, oy + 170 * k, k, ORANGE, 0);
                break;
            }
            case PAUSE:
                voile(pe, ox, oy, k);
                Police.centre(pe, "PAUSE", cx, oy + 80 * k, 3 * k, BLEU, ENCRE);
                Police.centre(pe, "TOUCHE POUR REPRENDRE", cx, oy + 104 * k, k, BLANC, 0);
                break;
            case ENTRE_VAGUES:
                Police.centre(pe, Chasse.vagueDeBoss(c.vague + 1) ? "ATTENTION : BUG DE PROD" : "VAGUE " + (c.vague + 1),
                        cx, oy + 90 * k, 2 * k, Chasse.vagueDeBoss(c.vague + 1) ? ORANGE : BLEU_CLAIR, ENCRE);
                Police.centre(pe, "+" + 50 * c.vague + " BONUS", cx, oy + 106 * k, k, ORANGE_CLAIR, 0);
                break;
            case FIN: {
                voile(pe, ox, oy, k);
                Police.centre(pe, "PARTIE", cx, oy + 50 * k, 3 * k, ORANGE, ENCRE);
                Police.centre(pe, "TERMINEE", cx, oy + 68 * k, 3 * k, ORANGE, ENCRE);
                Police.centre(pe, c.fin, cx, oy + 88 * k, k, ARGENT, 0);
                Police.centre(pe, "SCORE " + c.score, cx, oy + 100 * k, 2 * k, BLANC, ENCRE);
                Police.centre(pe, c.score >= meilleur && c.score > 0 ? "NOUVEAU RECORD !" : "RECORD " + meilleur, cx, oy + 114 * k, k,
                        c.score >= meilleur && c.score > 0 ? ORANGE : GRIS, 0);
                Police.centre(pe, "+" + c.xp() + " XP POUR PILOU", cx, oy + 123 * k, k, BLEU_CLAIR, 0);
                bouton(pe, ox, oy, k, REJOUER, "REJOUER", ORANGE);
                bouton(pe, ox, oy, k, QUITTER, "QUITTER", ARGENT);
                break;
            }
            default:
                break;
        }
    }

    private static void voile(Dessin.Peintre pe, float ox, float oy, float k) {
        pe.rect(ox, oy + 15 * k, ox + Chasse.W * k, oy + Chasse.H * k, VOILE);
    }

    private static void bouton(Dessin.Peintre pe, float ox, float oy, float k, float[] z, String texte, int couleur) {
        float x = ox + z[0] * k, y = oy + z[1] * k, d = x + z[2] * k, b = y + z[3] * k;
        pe.rect(x, y, d, b, couleur);
        pe.rect(x + k, y + k, d - k, b - k, ENCRE);
        if (!texte.isEmpty()) Police.centre(pe, texte, (x + d) / 2, y + (z[3] - 5) / 2 * k, k, couleur, 0);
    }

    public static boolean dans(float[] z, float x, float y) {
        return x >= z[0] && x <= z[0] + z[2] && y >= z[1] && y <= z[1] + z[3];
    }
}
