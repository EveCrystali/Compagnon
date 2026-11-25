package fr.pilou.compagnon;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * « Chasse aux bugs » : la logique pure du jeu de tir (aucune dépendance Android, testée sur JVM).
 * Monde de 120 × 200 unités. Pilou, en bas, tire des étincelles sur des vagues de bugs qui descendent
 * en zigzag ; trois boucliers en accolades { } s'effritent ; un café accélère le tir, « ✓ tests verts »
 * protège d'un coup ; toutes les 5 vagues, le « Bug de prod ».
 */
public final class Chasse {
    public static final float W = 120, H = 200;
    public static final float JOUEUR_Y = 182, JOUEUR_L = 16;
    public static final float LIGNE_PROD = 154;                 // les bugs qui l'atteignent : partie perdue
    public static final float BOUCLIER_Y = 160, CASE = 2;
    public static final int XP_MAX = 30;
    static final float CADENCE = 0.42f, CADENCE_CAFE = 0.17f, DUREE_CAFE = 8, DUREE_TESTS = 7, INVULNERABLE = 1.6f;

    public enum Phase {ACCUEIL, JEU, ENTRE_VAGUES, PAUSE, FIN}

    public enum Evenement {TIR, TOUCHE, EXPLOSION, BONUS, BLESSE, BOUCLIER, VAGUE, BOSS, BOSS_TOUCHE, FIN}

    public static final class Bug {
        public float x, y;            // coin haut-gauche
        public final int type;        // 0 scarabée (30), 1 araignée (20), 2 ver (10)
        public final int col, rang;
        public boolean vivant = true;

        Bug(float x, float y, int type, int col, int rang) {
            this.x = x;
            this.y = y;
            this.type = type;
            this.col = col;
            this.rang = rang;
        }

        public static final float L = 9, HT = 7;

        public int points() {
            return type == 0 ? 30 : type == 1 ? 20 : 10;
        }
    }

    public static final class Boss {
        public float x, y = 30, t;
        public int pv;
        public final int pvMax;
        public static final float L = 36, HT = 20;

        Boss(int pv) {
            this.pv = pv;
            pvMax = pv;
            x = (W - L) / 2;
        }
    }

    public static final class Tir {
        public float x, y, vx, vy;
        public final boolean ami;

        Tir(float x, float y, float vx, float vy, boolean ami) {
            this.x = x;
            this.y = y;
            this.vx = vx;
            this.vy = vy;
            this.ami = ami;
        }
    }

    public static final class Bonus {
        public float x, y;
        public final boolean cafe;    // sinon « ✓ tests verts »

        Bonus(float x, float y, boolean cafe) {
            this.x = x;
            this.y = y;
            this.cafe = cafe;
        }
    }

    public static final class Eclat {
        public float x, y, vx, vy, vie;
        public final int couleur;

        Eclat(float x, float y, float vx, float vy, int couleur) {
            this.x = x;
            this.y = y;
            this.vx = vx;
            this.vy = vy;
            this.couleur = couleur;
            vie = 0.6f;
        }
    }

    /** Bouclier en accolades : 13 × 9 cases de 2 unités, 2 points de vie par case. */
    static final String[] ACCOLADES = {
            "0011000001100",
            "0110000000110",
            "0110000000110",
            "0110000000110",
            "1100000000011",
            "0110000000110",
            "0110000000110",
            "0110000000110",
            "0011000001100"};

    public final List<Bug> bugs = new ArrayList<>();
    public final List<Tir> tirs = new ArrayList<>();
    public final List<Bonus> bonus = new ArrayList<>();
    public final List<Eclat> eclats = new ArrayList<>();
    /** Boucliers : [n][ligne][colonne] = points de vie (0 : détruit). */
    public final int[][][] boucliers = new int[3][ACCOLADES.length][ACCOLADES[0].length()];
    public Boss boss;

    public Phase phase = Phase.ACCUEIL;
    public float joueurX = (W - JOUEUR_L) / 2, cibleX = joueurX;
    public int vies = 3, score, vague = 0, bugsTues;
    public float cafe, tests, invulnerable, temps, chrono, sens = 1;
    public String fin = "";
    /** Aperçu de la page Jouer : Pilou n'y perd jamais. */
    public boolean immortel;
    private float prochainTir, prochainTirBug, pauseVague;
    private final Random hasard;
    private final List<Evenement> evenements = new ArrayList<>();

    public Chasse(long graine) {
        hasard = new Random(graine);
    }

    // ---- Commandes

    public void commencer() {
        bugs.clear();
        tirs.clear();
        bonus.clear();
        eclats.clear();
        boss = null;
        vies = 3;
        score = 0;
        vague = 0;
        bugsTues = 0;
        cafe = tests = invulnerable = 0;
        fin = "";
        joueurX = cibleX = (W - JOUEUR_L) / 2;
        for (int[][] b : boucliers)
            for (int r = 0; r < ACCOLADES.length; r++)
                for (int k = 0; k < ACCOLADES[r].length(); k++) b[r][k] = ACCOLADES[r].charAt(k) == '1' ? 2 : 0;
        phase = Phase.JEU;
        vagueSuivante();
    }

    public void viser(float x) {
        cibleX = Math.max(0, Math.min(W - JOUEUR_L, x - JOUEUR_L / 2));
    }

    public void pause(boolean oui) {
        if (oui && (phase == Phase.JEU || phase == Phase.ENTRE_VAGUES)) phase = Phase.PAUSE;
        else if (!oui && phase == Phase.PAUSE) phase = boss == null && vivants() == 0 ? Phase.ENTRE_VAGUES : Phase.JEU;
    }

    /** Ce qui s'est passé depuis le dernier appel (sons, vibrations) ; la liste est vidée. */
    public List<Evenement> evenements() {
        List<Evenement> e = new ArrayList<>(evenements);
        evenements.clear();
        return e;
    }

    /** XP de la partie : score / 150 + 2 par vague franchie, au plus 30. */
    public int xp() {
        if (score <= 0) return 0;
        return Math.max(1, Math.min(XP_MAX, score / 150 + Math.max(0, vague - 1) * 2));
    }

    public int vivants() {
        int n = 0;
        for (Bug b : bugs) if (b.vivant) n++;
        return n;
    }

    public static boolean vagueDeBoss(int v) {
        return v > 0 && v % 5 == 0;
    }

    // ---- Vagues

    void vagueSuivante() {
        vague++;
        bugs.clear();
        tirs.clear();
        sens = 1;
        if (vagueDeBoss(vague)) {
            boss = new Boss(25 + 5 * vague);
            evenements.add(Evenement.BOSS);
        } else {
            boss = null;
            int rangs = Math.min(5, 3 + vague / 3), cols = 7;
            float x0 = (W - (cols - 1) * 14 - Bug.L) / 2;
            for (int r = 0; r < rangs; r++)
                for (int k = 0; k < cols; k++) {
                    int type = r == 0 ? 0 : r <= 2 ? 1 : 2;
                    bugs.add(new Bug(x0 + k * 14, 26 + r * 12, type, k, r));
                }
            evenements.add(Evenement.VAGUE);
        }
        prochainTirBug = 1.2f;
        phase = Phase.JEU;
    }

    float vitesse() {
        float base = 8 + 2.5f * vague;
        int restants = vivants(), total = Math.max(1, bugs.size());
        return base * (1 + 1.5f * (1 - restants / (float) total)); // plus ils sont rares, plus ils filent
    }

    // ---- Le temps passe

    public void avancer(float dt) {
        dt = Math.min(dt, 0.05f);
        for (Eclat e : eclats) {
            e.x += e.vx * dt;
            e.y += e.vy * dt;
            e.vie -= dt;
        }
        eclats.removeIf(e -> e.vie <= 0);
        if (phase == Phase.PAUSE || phase == Phase.ACCUEIL || phase == Phase.FIN) return;
        temps += dt;
        chrono += dt;
        if (phase == Phase.ENTRE_VAGUES) {
            pauseVague -= dt;
            if (pauseVague <= 0) vagueSuivante();
            bougerJoueur(dt);
            return;
        }
        bougerJoueur(dt);
        cafe = Math.max(0, cafe - dt);
        tests = Math.max(0, tests - dt);
        invulnerable = Math.max(0, invulnerable - dt);

        // Tir automatique.
        prochainTir -= dt;
        if (prochainTir <= 0) {
            prochainTir = cafe > 0 ? CADENCE_CAFE : CADENCE;
            tirs.add(new Tir(joueurX + JOUEUR_L / 2, JOUEUR_Y - 2, 0, -190, true));
            evenements.add(Evenement.TIR);
        }

        bougerBugs(dt);
        if (boss != null) bougerBoss(dt);
        tirerBugs(dt);

        for (Tir t : tirs) {
            t.x += t.vx * dt;
            t.y += t.vy * dt;
        }
        for (Bonus b : bonus) b.y += 38 * dt;
        collisions();
        tirs.removeIf(t -> t.y < -6 || t.y > H + 6 || t.x < -6 || t.x > W + 6);
        bonus.removeIf(b -> b.y > H);

        if (phase == Phase.JEU && boss == null && vivants() == 0) {
            phase = Phase.ENTRE_VAGUES;
            pauseVague = 1.6f;
            score += 50 * vague;
        }
    }

    private void bougerJoueur(float dt) {
        float d = cibleX - joueurX, pas = 150 * dt;
        joueurX += Math.abs(d) <= pas ? d : Math.signum(d) * pas;
    }

    private void bougerBugs(float dt) {
        if (vivants() == 0) return;
        float dx = sens * vitesse() * dt, gauche = Float.MAX_VALUE, droite = -Float.MAX_VALUE;
        for (Bug b : bugs)
            if (b.vivant) {
                gauche = Math.min(gauche, b.x + dx);
                droite = Math.max(droite, b.x + dx + Bug.L);
            }
        boolean bord = gauche < 2 || droite > W - 2;
        for (Bug b : bugs) {
            if (!b.vivant) continue;
            if (bord) b.y += 6;
            else b.x += dx;
            if (b.y + Bug.HT >= LIGNE_PROD && phase == Phase.JEU) terminer("Les bugs ont atteint la prod !");
        }
        if (bord) sens = -sens;
    }

    private void bougerBoss(float dt) {
        boss.t += dt;
        boss.x = (W - Boss.L) / 2 + (float) Math.sin(boss.t * (0.9 + vague * 0.02)) * (W - Boss.L - 8) / 2;
        boss.y = 30 + (float) Math.sin(boss.t * 2.1) * 3;
    }

    private void tirerBugs(float dt) {
        prochainTirBug -= dt;
        if (prochainTirBug > 0) return;
        if (boss != null) {
            prochainTirBug = Math.max(0.55f, 1.2f - vague * 0.02f);
            float cx = boss.x + Boss.L / 2, cy = boss.y + Boss.HT;
            for (int i = -1; i <= 1; i++) tirs.add(new Tir(cx, cy, i * 22, 80, false));
            return;
        }
        prochainTirBug = 1 / (0.6f + 0.15f * vague) * (0.6f + hasard.nextFloat() * 0.8f);
        // Un bug du bas d'une colonne au hasard.
        List<Bug> bas = new ArrayList<>();
        for (Bug b : bugs) {
            if (!b.vivant) continue;
            boolean dessous = false;
            for (Bug o : bugs) if (o.vivant && o.col == b.col && o.rang > b.rang) dessous = true;
            if (!dessous) bas.add(b);
        }
        if (bas.isEmpty()) return;
        Bug b = bas.get(hasard.nextInt(bas.size()));
        tirs.add(new Tir(b.x + Bug.L / 2, b.y + Bug.HT, 0, 70 + 4 * vague, false));
    }

    // ---- Collisions

    void collisions() {
        for (Tir t : tirs) {
            if (t.y < -100) continue;
            if (toucheBouclier(t)) {
                t.y = -1000;
                continue;
            }
            if (t.ami) {
                if (boss != null && t.x >= boss.x && t.x <= boss.x + Boss.L && t.y >= boss.y && t.y <= boss.y + Boss.HT) {
                    float tx = t.x;
                    t.y = -1000;
                    boss.pv--;
                    evenements.add(Evenement.BOSS_TOUCHE);
                    eclater(tx, boss.y + Boss.HT, 0xfff69d50, 3);
                    if (boss.pv <= 0) {
                        score += 250 + 50 * vague;
                        eclater(boss.x + Boss.L / 2, boss.y + Boss.HT / 2, 0xfff69d50, 24);
                        evenements.add(Evenement.EXPLOSION);
                        bonus.add(new Bonus(boss.x + Boss.L / 2 - 3, boss.y + Boss.HT, hasard.nextBoolean()));
                        boss = null;
                    }
                    continue;
                }
                for (Bug b : bugs) {
                    if (!b.vivant || t.x < b.x || t.x > b.x + Bug.L || t.y < b.y || t.y > b.y + Bug.HT) continue;
                    b.vivant = false;
                    t.y = -1000;
                    score += b.points();
                    bugsTues++;
                    evenements.add(Evenement.TOUCHE);
                    eclater(b.x + Bug.L / 2, b.y + Bug.HT / 2, b.type == 0 ? 0xfff69d50 : b.type == 1 ? 0xff6cb6ff : 0xffb8c4d2, 8);
                    if (hasard.nextFloat() < 0.07f) bonus.add(new Bonus(b.x + 1, b.y, hasard.nextBoolean()));
                    break;
                }
            } else if (t.x >= joueurX + 1 && t.x <= joueurX + JOUEUR_L - 1 && t.y >= JOUEUR_Y - 4 && t.y <= JOUEUR_Y + 12) {
                t.y = -1000;
                blesser();
            }
        }
        for (Bonus b : bonus) {
            if (b.y < 0) continue;
            if (b.x + 6 >= joueurX && b.x <= joueurX + JOUEUR_L && b.y + 6 >= JOUEUR_Y - 4 && b.y <= JOUEUR_Y + 12) {
                if (b.cafe) cafe = DUREE_CAFE;
                else tests = DUREE_TESTS;
                score += 25;
                b.y = H + 100;
                evenements.add(Evenement.BONUS);
            }
        }
    }

    void blesser() {
        if (immortel || invulnerable > 0 || phase != Phase.JEU) return;
        if (tests > 0) {
            tests = 0;
            invulnerable = 0.8f;
            evenements.add(Evenement.BOUCLIER);
            return;
        }
        vies--;
        invulnerable = INVULNERABLE;
        evenements.add(Evenement.BLESSE);
        eclater(joueurX + JOUEUR_L / 2, JOUEUR_Y + 4, 0xff6cb6ff, 10);
        if (vies <= 0) terminer("Plus de vies…");
    }

    private boolean toucheBouclier(Tir t) {
        for (int n = 0; n < 3; n++) {
            float bx = boucliersX(n);
            int k = (int) Math.floor((t.x - bx) / CASE), r = (int) Math.floor((t.y - BOUCLIER_Y) / CASE);
            if (r < 0 || r >= ACCOLADES.length || k < 0 || k >= ACCOLADES[0].length()) continue;
            if (boucliers[n][r][k] > 0) {
                boucliers[n][r][k]--;
                evenements.add(Evenement.BOUCLIER);
                return true;
            }
        }
        return false;
    }

    /** Abscisse du bouclier n (0..2). */
    public static float boucliersX(int n) {
        float l = ACCOLADES[0].length() * CASE, ecart = (W - 3 * l) / 4;
        return ecart + n * (l + ecart);
    }

    private void eclater(float x, float y, int couleur, int n) {
        for (int i = 0; i < n; i++) {
            double a = hasard.nextDouble() * Math.PI * 2;
            float v = 20 + hasard.nextFloat() * 40;
            eclats.add(new Eclat(x, y, (float) Math.cos(a) * v, (float) Math.sin(a) * v, couleur));
        }
    }

    void terminer(String raison) {
        if (phase == Phase.FIN) return;
        phase = Phase.FIN;
        fin = raison;
        evenements.add(Evenement.FIN);
    }

    // ---- Pour les tests

    void tirAmi(float x, float y) {
        tirs.add(new Tir(x, y, 0, -190, true));
    }

    void tirEnnemi(float x, float y) {
        tirs.add(new Tir(x, y, 0, 70, false));
    }

    void poserBonus(float x, float y, boolean estCafe) {
        bonus.add(new Bonus(x, y, estCafe));
    }

    void sauterA(int v) {
        vague = v - 1;
        vagueSuivante();
    }
}
