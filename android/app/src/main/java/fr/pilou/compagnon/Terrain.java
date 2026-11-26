package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * L'atelier de Pilou : une petite scène en pixels (96 × 64 cases) où il pêche, cuisine et joue.
 * Toucher le bouchon quand il plonge, remuer la marmite, attraper l'étoile, éclater les bulles,
 * taper dans la main, caresser Pilou. Les gains partent vers le PC par Gains.
 */
public final class Terrain extends View {
    private boolean possede(String id) {
        return Gains.possede(getContext(), id);
    }

    public interface Ecoute {
        void message(String texte);

        void change(); // niveau, stock, carnet : l'écran se met à jour

        int niveau();
    }

    private enum Mode {REPOS, LANCER, ATTENTE, MORD, PRISE, CUISINE, PLAT, ETOILE, BULLES, TAPE}

    static final int LG = 96, HT = 64;
    private static final int PX = 30, PY = 13;           // coin de Pilou (cases)
    private static final int BX = 12, BY = 51;           // bouchon
    private static final int MX = 73, MY = 44;           // marmite
    private static final int CIEL = 0xff22272e, SOL = 0xff2d333b, EAU = 0xff2f7ed8, EAU_CLAIRE = 0xff6cb6ff, ECUME = 0xffb4dbff,
            ENCRE = 0xff1c2128, ORANGE = 0xfff69d50, ORANGE_CLAIR = 0xffffd8b0, GRIS = 0xff768390, GRIS_CLAIR = 0xffadbac7,
            CREME = 0xfff6f8fa, BOIS = 0xffc97a28, ARGENT = 0xffb8c4d2, BLEU = 0xff6cb6ff;

    private final Ecoute ecoute;
    private final Random hasard = new Random();
    private final Paint pt = new Paint();
    private float s = 4, ox, oy;
    private Mode mode = Mode.REPOS;
    private long debut, mordA, finCaresse, derniereCaresse, debutSaut = -10_000;
    private boolean remue;
    private Butin.Prise prise;
    private Butin.Plat plat;
    private String humeur = "repos";
    private long finHumeur;
    private float etoileX, etoileY;
    private final List<float[]> bulles = new ArrayList<>(); // x, y, vitesse, éclatée (0/1)
    private int eclatees;
    private String couleur = "bleu", accessoire = "aucun";
    private long prochainClin = 2000, finClin;

    public Terrain(Context c, Ecoute e) {
        super(c);
        ecoute = e;
        pt.setAntiAlias(false);
    }

    public void tenue(String teinte, String acc) {
        couleur = teinte;
        accessoire = acc;
    }

    public boolean occupe() {
        return mode != Mode.REPOS;
    }

    @Override
    protected void onMeasure(int l, int h) {
        int w = MeasureSpec.getSize(l);
        setMeasuredDimension(w, w * HT / LG);
    }

    private long t() {
        return SystemClock.uptimeMillis();
    }

    // ---- Ce que proposent les boutons

    public void pecher() {
        if (occupe()) return;
        mode = Mode.LANCER;
        debut = t();
        mordA = debut + 700 + 3000 + (long) (hasard.nextDouble() * 12000);
        ecoute.message("Pilou lance sa ligne… touche le bouchon quand il plonge !");
    }

    public void cuisiner() {
        if (occupe()) return;
        if (!Butin.peutCuisiner(Gains.stock(getContext()))) {
            ecoute.message("Rien à cuisiner : il faut d'abord pêcher un poisson, une algue, un coquillage…");
            humeur("soulage", 1500);
            return;
        }
        mode = Mode.CUISINE;
        debut = t();
        remue = false;
        ecoute.message("Ça mijote… touche la marmite pour remuer (sinon, ça peut brûler).");
    }

    public void jouer() {
        jouer(hasard.nextInt(3));
    }

    /** 0 étoile filante, 1 bulles, 2 tape m'en cinq. */
    public void jouer(int j) {
        if (occupe()) return;
        debut = t();
        if (j == 0) {
            mode = Mode.ETOILE;
            ecoute.message("Une étoile filante ! Attrape-la.");
        } else if (j == 1) {
            mode = Mode.BULLES;
            bulles.clear();
            eclatees = 0;
            for (int i = 0; i < 3; i++)
                bulles.add(new float[]{12 + hasard.nextInt(72), HT + i * 6, 5 + hasard.nextFloat() * 3, 0});
            ecoute.message("Trois bulles : éclate-les toutes !");
        } else {
            mode = Mode.TAPE;
            ecoute.message("Tape m'en cinq !");
        }
    }

    private void humeur(String h, long ms) {
        humeur = h;
        finHumeur = t() + ms;
        if (h.equals("fete") || h.equals("caresse") || h.equals("inquiet")) debutSaut = t();
    }

    // ---- Fin des activités

    private void finPeche(Butin.Prise x, boolean seul) {
        prise = x;
        mode = Mode.PRISE;
        debut = t();
        if (x == null) {
            ecoute.message(seul ? "Pilou a ferré tout seul… raté. (Touche le bouchon quand il plonge !)" : "Trop tôt : le poisson a filé.");
            humeur("soulage", 1800);
            return;
        }
        boolean nouvelle = !Gains.carnet(getContext(), Prefs.etat(getContext())).contains(x.id);
        int xp = Gains.prise(getContext(), x, Butin.xpPrise(x, nouvelle));
        ecoute.message(Butin.nomPrise(x) + "  +" + xp + " xp" + (nouvelle ? "  · nouveau !" : "") + (seul ? "  (Pilou, tout seul)" : ""));
        humeur("fete", 2500);
        ecoute.change();
    }

    private void finCuisine() {
        Etat e = Prefs.etat(getContext());
        plat = Butin.cuisiner(hasard, ecoute.niveau(), Gains.stock(getContext()), Gains.plats(getContext(), e), remue, possede(Boutique.MARMITE_CUIVRE));
        mode = Mode.PLAT;
        debut = t();
        if (plat == null) {
            mode = Mode.REPOS;
            return;
        }
        int xp = Gains.plat(getContext(), plat);
        if (plat.rate) {
            ecoute.message("Oups, " + plat.nom + " a brûlé…  +" + xp + " xp");
            humeur("grimace", 2000);
        } else {
            ecoute.message(plat.nom + "  +" + xp + " xp" + (plat.decouverte ? "  · nouvelle recette !" : ""));
            humeur("fete", 2500);
        }
        ecoute.change();
    }

    private void gagner(int xpBrute, String texte) {
        int xp = Gains.jeu(getContext(), xpBrute);
        ecoute.message(texte + "  +" + xp + " xp");
        humeur("fete", 2000);
        ecoute.change();
    }

    // ---- Toucher

    @Override
    public boolean onTouchEvent(MotionEvent ev) {
        if (ev.getActionMasked() != MotionEvent.ACTION_DOWN) return true;
        float x = (ev.getX() - ox) / s, y = (ev.getY() - oy) / s;
        long t = t();
        switch (mode) {
            case ATTENTE:
                if (pres(x, y, BX + 1, BY, 9)) finPeche(null, false);
                return true;
            case MORD:
                if (pres(x, y, BX + 1, BY + 2, 10)) finPeche(Butin.tirer(hasard, ecoute.niveau(), false, possede(Boutique.CANNE_DOREE)), false);
                return true;
            case CUISINE:
                if (x >= MX - 3 && x <= MX + 16 && y >= MY - 6 && y <= MY + 12 && !remue) {
                    remue = true;
                    ecoute.message("Tu remues la marmite : rien ne brûlera.");
                }
                return true;
            case ETOILE:
                if (pres(x, y, etoileX, etoileY, 9)) {
                    mode = Mode.REPOS;
                    gagner(10, "Étoile attrapée !");
                }
                return true;
            case BULLES:
                for (float[] b : bulles)
                    if (b[3] == 0 && pres(x, y, b[0] + 3, b[1] + 3, 7)) {
                        b[3] = 1;
                        eclatees++;
                        if (eclatees == bulles.size()) {
                            mode = Mode.REPOS;
                            gagner(20, "Trois bulles éclatées (bonus compris) !");
                        } else ecoute.message("Pop ! Encore " + (bulles.size() - eclatees) + ".");
                        break;
                    }
                return true;
            case TAPE:
                if (x >= 66 && x <= 82 && y >= 24 && y <= 42) {
                    mode = Mode.REPOS;
                    gagner(10, "Tape m'en cinq !");
                }
                return true;
            default:
                break;
        }
        // Pilou lui-même : une caresse (comptée au plus toutes les 3 s).
        if (x >= PX + 4 && x <= PX + 32 && y >= PY + 8 && y <= PY + 40) {
            finCaresse = t + 2400;
            humeur("caresse", 2400);
            if (t - derniereCaresse > 3000) {
                derniereCaresse = t;
                Gains.caresse(getContext());
                ecoute.change();
            }
            ecoute.message("Pilou ronronne.");
        }
        return true;
    }

    private static boolean pres(float x, float y, float cx, float cy, float r) {
        return (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r;
    }

    // ---- Dessin

    private void c(float x, float y, float w, float h, int couleur) {
        pt.setColor(couleur);
        canvas.drawRect(ox + x * s, oy + y * s, ox + (x + w) * s, oy + (y + h) * s, pt);
    }

    private Canvas canvas;

    private void motif(String[] m, int x, int y, int[] pal, boolean contour) {
        int h = m.length, w = m[0].length();
        if (contour)
            for (int r = -1; r <= h; r++)
                for (int k = -1; k <= w; k++) {
                    if (plein(m, r, k)) continue;
                    if (plein(m, r - 1, k) || plein(m, r + 1, k) || plein(m, r, k - 1) || plein(m, r, k + 1)) c(x + k, y + r, 1, 1, ENCRE);
                }
        for (int r = 0; r < h; r++)
            for (int k = 0; k < w; k++) {
                int v = m[r].charAt(k) - '0';
                if (v > 0 && v < pal.length && pal[v] != 0) c(x + k, y + r, 1, 1, pal[v]);
            }
    }

    private static boolean plein(String[] m, int r, int k) {
        return r >= 0 && r < m.length && k >= 0 && k < m[r].length() && m[r].charAt(k) != '0';
    }

    private void ligne(int x0, int y0, int x1, int y1, int couleur) {
        int dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1, err = dx + dy;
        while (true) {
            c(x0, y0, 1, 1, couleur);
            if (x0 == x1 && y0 == y1) break;
            int e2 = 2 * err;
            if (e2 >= dy) { err += dy; x0 += sx; }
            if (e2 <= dx) { err += dx; y0 += sy; }
        }
    }

    @Override
    protected void onDraw(Canvas cv) {
        canvas = cv;
        s = Math.min(getWidth() / (float) LG, getHeight() / (float) HT);
        ox = (getWidth() - LG * s) / 2;
        oy = (getHeight() - HT * s) / 2;
        long t = t();
        avancer(t);

        c(0, 0, LG, HT, CIEL);
        for (int i = 0; i < 14; i++) c((i * 37 + 11) % LG, (i * 23 + 5) % 30, 1, 1, (t / 700 + i) % 5 == 0 ? GRIS_CLAIR : GRIS);
        c(0, 55, LG, 9, SOL);
        for (int x = 0; x < LG; x += 3) c(x, 55, 2, 1, GRIS);

        // L'eau, à gauche, qui ondule.
        c(1, 50, 26, 12, EAU);
        for (int x = 1; x < 27; x++) {
            int y = 50 + (int) Math.round(Math.sin(t / 380.0 + x * 0.7));
            c(x, y, 1, 1, EAU_CLAIRE);
            if ((x + t / 300) % 9 == 0) c(x, 56, 1, 1, ECUME);
        }

        // La marmite, à droite.
        boolean cuisine = mode == Mode.CUISINE;
        hd("marmite", MX - 1, MY - 4, cuisine ? t : 0);
        if (cuisine || (mode == Mode.PLAT && t - debut < 800)) {
            hd("feu", MX, MY + 7, t);
            for (int i = 0; i < 3; i++) {
                float k = ((t - debut) / 900f + i / 3f) % 1f;
                motif(new String[]{"0110", "1111", "0110"}, MX + 2 + i * 3 + (int) (Math.sin(k * 6) * 1.5), (int) (MY - 2 - k * 12),
                        new int[]{0, remue || !cuisine ? GRIS_CLAIR : CREME}, false);
            }
        }
        if (mode == Mode.PLAT && plat != null && plat.rate)
            for (int i = 0; i < 4; i++) {
                float k = ((t - debut) / 1100f + i / 4f) % 1f;
                motif(new String[]{"0110", "1111", "1111", "0110"}, MX + 1 + i * 3, (int) (MY - 3 - k * 16), new int[]{0, 0xff1c2128}, false);
            }

        // La canne, la ligne et le bouchon.
        boolean peche = mode == Mode.LANCER || mode == Mode.ATTENTE || mode == Mode.MORD || (mode == Mode.PRISE && t - debut < 600);
        if (peche) {
            ligne(PX + 6, PY + 30, PX - 5, PY + 15, BOIS);
            c(PX + 4, PY + 28, 2, 2, GRIS);
            boolean lance = mode != Mode.LANCER || t - debut > 600;
            if (lance) {
                boolean mord = mode == Mode.MORD;
                int by = BY + (mord ? 2 + (int) ((t / 90) % 2) : (int) Math.round(Math.sin(t / 500.0)));
                ligne(PX - 5, PY + 15, BX + 1, by, GRIS_CLAIR);
                hd("bouchon", BX - 1, by - 1, mord ? t : 0);
                if (mord) {
                    motif(new String[]{"1", "1", "1", "0", "1"}, BX + 1, by - 8, new int[]{0, ORANGE}, false);
                    for (int i = 0; i < 6; i++) {
                        double a = i * Math.PI / 3 + t / 200.0;
                        c(BX + 1 + (int) Math.round(Math.cos(a) * 4), by + 2 + (int) Math.round(Math.sin(a) * 2), 1, 1, ECUME);
                    }
                }
            }
        }

        // Pilou.
        if (t > prochainClin) {
            finClin = t + 140;
            prochainClin = t + 2500 + (long) (Math.random() * 3500);
        }
        String expr = t < finHumeur ? humeur : mode == Mode.MORD ? "attente" : mode == Mode.ATTENTE || mode == Mode.LANCER || cuisine ? "concentre" : "repos";
        long ds = t - debutSaut;
        float saut = ds < 600 ? (float) (Math.sin(Math.PI * ds / 600.0) * 3) : 0;
        // Même encombrement qu'avant (boîte de 36 cases) avec la grille fine de 48 × 56.
        Dessin.dessiner((g, h, d, b, col) -> {
            pt.setColor(col);
            cv.drawRect(g, h, d, b, pt);
        }, ox + PX * s, oy + PY * s, s * 36f / (Dessin.W + 2), expr, t, couleur, accessoire, t < finClin, saut);

        // Cœurs de caresse.
        if (t < finCaresse)
            for (int i = 0; i < 3; i++) {
                float k = ((2400 - (finCaresse - t)) / 2400f + i / 3f) % 1f;
                motif(new String[]{"0101", "1111", "0110"}, PX + 8 + i * 8, (int) (PY + 6 - k * 10), new int[]{0, ORANGE_CLAIR}, false);
            }

        // La prise ou le plat, au-dessus de Pilou, avec un cadre selon la rareté.
        if (mode == Mode.PRISE && prise != null) {
            if (Sprites.banque().get("prise-" + prise.id) != null) objetHd("prise-" + prise.id, PX + 18, 3, prise.rarete, t);
            else objet(sprite(prise.forme), PX + 18, 3, new int[]{0, ENCRE, prise.couleur, prise.clair, prise.detail}, prise.rarete);
        }
        if (mode == Mode.PLAT && plat != null && !plat.rate)
            objetHd(Sprites.banque().plat(plat.inventee ? "" : plat.id, false), PX + 18, 3, plat.decouverte ? Butin.RARE : Butin.COMMUN, t);

        // Jeux.
        if (mode == Mode.ETOILE) {
            for (int i = 1; i < 8; i++) c(etoileX + i * 1.5f, etoileY - i * 0.6f, 1, 1, i < 4 ? ORANGE_CLAIR : GRIS);
            hd("etoile", (int) etoileX - 4, (int) etoileY - 5, t);
        }
        if (mode == Mode.BULLES)
            for (float[] b : bulles)
                if (b[3] == 0) hd("bulle", (int) b[0] - 1, (int) b[1] - 1, t);
        if (mode == Mode.TAPE) hd("main", 69, 27 + (int) Math.round(Math.sin(t / 120.0)), t);

        postInvalidateDelayed(50);
    }

    // Sprite HD de la banque, deux fois plus fin que les cases du terrain (coin haut-gauche en cases).
    private void hd(String id, int x, int y, long t) {
        Sprites.dessiner((g, h, d, b, col) -> {
            pt.setColor(col);
            canvas.drawRect(g, h, d, b, pt);
        }, Sprites.banque().get(id), ox + x * s, oy + y * s, s / 2, t, false);
    }

    private void objetHd(String id, int centreX, int y, int rarete, long t) {
        Sprites.Sprite sp = Sprites.banque().get(id);
        if (sp == null) return;
        int w = (sp.w() + 1) / 2, h = (sp.h() + 1) / 2, x = centreX - w / 2;
        cadre(x, y, w, h, rarete);
        hd(id, x, y, t);
    }

    // Cadre de la prise : aucun (commun), coins (peu commun), trait (rare), double (épique), étoilé (légendaire).
    private void objet(String[] m, int centreX, int y, int[] pal, int rarete) {
        int w = m[0].length(), h = m.length, x = centreX - w / 2;
        cadre(x, y, w, h, rarete);
        motif(m, x, y, pal, true);
    }

    private void cadre(int x, int y, int w, int h, int rarete) {
        int g = x - 3, d = x + w + 2, haut = y - 3, bas = y + h + 2;
        int cadre = rarete >= Butin.EPIQUE ? ORANGE : rarete == Butin.RARE ? BLEU : ARGENT;
        if (rarete == Butin.PEU_COMMUN)
            for (int[] k : new int[][]{{g, haut}, {d - 1, haut}, {g, bas - 1}, {d - 1, bas - 1}}) {
                c(k[0], k[1], 2, 1, cadre);
                c(k[0], k[1], 1, 2, cadre);
            }
        if (rarete >= Butin.RARE) {
            c(g, haut, d - g, 1, cadre);
            c(g, bas - 1, d - g, 1, cadre);
            c(g, haut, 1, bas - haut, cadre);
            c(d - 1, haut, 1, bas - haut, cadre);
        }
        if (rarete >= Butin.EPIQUE) {
            c(g - 2, haut - 2, d - g + 4, 1, cadre);
            c(g - 2, bas + 1, d - g + 4, 1, cadre);
            c(g - 2, haut - 2, 1, bas - haut + 4, cadre);
            c(d + 1, haut - 2, 1, bas - haut + 4, cadre);
        }
        if (rarete == Butin.LEGENDAIRE)
            for (int[] k : new int[][]{{g - 3, haut - 3}, {d + 1, haut - 3}, {g - 3, bas + 1}, {d + 1, bas + 1}})
                motif(new String[]{"010", "111", "010"}, k[0], k[1], new int[]{0, ORANGE_CLAIR}, false);
    }

    static String[] sprite(String forme) {
        switch (forme) {
            case "poisson": return new String[]{"000022220000", "200223322200", "222232222420", "222222222220", "200222222200", "000022220000"};
            case "long": return new String[]{"00000000022220", "02220002222342", "22222222222220", "02200222200000"};
            case "plat": return new String[]{"0000220000", "0002332000", "0223332220", "2223342222", "0022222200", "0000220000", "0000020000"};
            case "coquillage": return new String[]{"00022000", "00233200", "02334320", "23343432", "23434332", "02333320", "00222200"};
            case "crabe": return new String[]{"20000000002", "22000000022", "02222222220", "22234243222", "02222222220", "20202020202"};
            case "algue": return new String[]{"002000", "020200", "002020", "020200", "002020", "020220", "202020", "022220"};
            case "botte": return new String[]{"0022220", "0023320", "0022220", "0022220", "0022220", "2222220", "2222222", "4444444"};
            case "bouteille": return new String[]{"00400", "00200", "02320", "23332", "23432", "23432", "23332", "23332", "02220"};
            case "caillou": return new String[]{"0022200", "0233322", "2232222", "0222220"};
            case "cle": return new String[]{"0220000000", "2002222222", "2002000202", "0220000202"};
            case "pieuvre": return new String[]{"002222200", "023333320", "024323420", "022222220", "022222220", "020202020", "202020202", "020002020"};
            case "hippocampe": return new String[]{"022200", "223420", "022220", "002220", "022320", "223200", "022200", "002200", "000220", "002200"};
            case "coffre": return new String[]{"022222220", "233333332", "222242222", "244424442", "222242222", "222222222", "244444442"};
            case "perle": return new String[]{"002200", "023320", "233332", "233342", "023420", "002200"};
            default: return new String[]{"00000000040000", "00000000404000", "00022222222000", "02233333222220", "22234222222222", "02222222222220", "00222000000000"};
        }
    }

    // Le temps passe : morsure, fin de cuisson, étoile qui file, bulles qui montent.
    private void avancer(long t) {
        switch (mode) {
            case LANCER:
                if (t - debut > 700) mode = Mode.ATTENTE;
                break;
            case ATTENTE:
                if (t >= mordA) mode = Mode.MORD;
                break;
            case MORD:
                if (t >= mordA + Butin.FENETRE_MORSURE) finPeche(Butin.tirer(hasard, ecoute.niveau(), true, possede(Boutique.CANNE_DOREE)), true);
                break;
            case PRISE:
            case PLAT:
                if (t - debut > 3000) mode = Mode.REPOS;
                break;
            case CUISINE:
                if (t - debut > 4500) finCuisine();
                break;
            case ETOILE: {
                float k = (t - debut) / 4000f;
                etoileX = LG + 4 - k * 70;
                etoileY = 2 + k * 30;
                if (k >= 1) {
                    mode = Mode.REPOS;
                    ecoute.message("L'étoile est passée…");
                }
                break;
            }
            case BULLES:
                for (float[] b : bulles) b[1] -= b[2] * 0.05f;
                boolean toutes = true;
                for (float[] b : bulles) toutes &= b[3] == 1 || b[1] < -8;
                if (toutes) {
                    mode = Mode.REPOS;
                    if (eclatees < bulles.size()) {
                        if (eclatees > 0) gagner(5 * eclatees, eclatees + " bulle" + (eclatees > 1 ? "s" : "") + " éclatée" + (eclatees > 1 ? "s" : ""));
                        else ecoute.message("Les bulles se sont envolées.");
                    }
                }
                break;
            case TAPE:
                if (t - debut > 2500) {
                    mode = Mode.REPOS;
                    ecoute.message("Raté… Pilou attendait ta main.");
                }
                break;
            default:
                break;
        }
    }
}
