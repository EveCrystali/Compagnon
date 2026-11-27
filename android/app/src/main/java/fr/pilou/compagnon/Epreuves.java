package fr.pilou.compagnon;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Random;
import java.util.function.Consumer;

/**
 * Les épreuves des campagnes, en vues natives (10 à 25 s, difficulté 1 à 3, jouables d'une main) : réflexe (le curseur
 * dans la zone), mémoire (refaire la suite de signes), rythme (toucher quand la note passe la ligne), visée (toucher les
 * cibles), et les dés (le tirage du moteur, animé, avec sa chance). Toujours une porte de sortie : « laisser faire les
 * dés ». Retours visuels nets (signe ✓ / ✕ en plus de la couleur), vibration légère si les vibrations sont permises.
 */
final class Epreuves {
    private Epreuves() {
    }

    /** L'écran d'une épreuve, par-dessus la lecture. */
    static final class Ecran extends FrameLayout {
        private final Consumer<Boolean> fin;
        private final Jeu jeu;
        private final TextView statut;
        private final LinearLayout colonne;
        private boolean decide;

        Ecran(Context c, String nom, int difficulte, int chance, int tirage, String ton, Consumer<Boolean> fin, Runnable annuler) {
            super(c);
            this.fin = fin;
            setBackgroundColor(Vitrine.NUIT);
            setClickable(true);
            colonne = Ui.pile(c);
            colonne.setPadding(Ui.dp(c, 16), Ui.dp(c, 8), Ui.dp(c, 16), Ui.dp(c, 16));
            addView(colonne, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

            LinearLayout haut = Ui.rangee(c);
            TextView fermer = Ui.texte(c, "‹", 26, Vitrine.ARGENT_CLAIR, true);
            fermer.setGravity(Gravity.CENTER);
            fermer.setContentDescription("Revenir à la lecture sans jouer");
            fermer.setBackground(Ui.touchable(c, Ui.arrondi(c, Vitrine.NUIT2, 24, 0), 24));
            fermer.setOnClickListener(v -> annuler.run());
            haut.addView(fermer, new LinearLayout.LayoutParams(Ui.dp(c, 48), Ui.dp(c, 48)));
            LinearLayout titres = Ui.pile(c);
            titres.setPadding(Ui.dp(c, 12), 0, 0, 0);
            titres.addView(new Vitrine.Pixel(c, nom.equals("des") ? "LES DES" : "EPREUVE", 2.2f, Vitrine.ORANGE, Vitrine.VIOLET_FONCE, false));
            TextView sous = Ui.texte(c, Aventure.nomJeu(nom) + "  ·  " + Aventure.difficulte(difficulte), Ui.T_DETAIL, Vitrine.ARGENT, true);
            sous.setPadding(0, Ui.dp(c, 6), 0, 0);
            titres.addView(sous);
            haut.addView(titres, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
            colonne.addView(haut, Ui.large());

            TextView consigne = Ui.texte(c, nom.equals("des") ? "Les dés décident pour Pilou : " + chance + " % de chance de réussir."
                    : Aventure.consigneJeu(nom), Ui.T_CORPS, Vitrine.ARGENT_CLAIR, false);
            consigne.setPadding(0, Ui.dp(c, 12), 0, Ui.dp(c, 12));
            colonne.addView(consigne, Ui.large());

            switch (nom) {
                case "reflexe": jeu = new Reflexe(c, difficulte); break;
                case "memoire": jeu = new Memoire(c, difficulte); break;
                case "rythme": jeu = new Rythme(c, difficulte); break;
                case "visee": jeu = new Visee(c, difficulte); break;
                default: jeu = new Des(c, chance, tirage); break;
            }
            jeu.ecran = this;
            jeu.setBackground(Ui.arrondi(c, Vitrine.NUIT2, 16, Vitrine.VIOLET_FONCE));
            colonne.addView(jeu, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

            statut = Ui.texte(c, "", Ui.T_CORPS, Vitrine.ARGENT_CLAIR, true);
            statut.setGravity(Gravity.CENTER);
            statut.setPadding(0, Ui.dp(c, 12), 0, Ui.dp(c, 4));
            statut.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
            colonne.addView(statut, Ui.large());
            if (!nom.equals("des")) {
                TextView des = Ui.texte(c, "Laisser faire les dés · " + chance + " %", Ui.T_CORPS, Vitrine.BLEU, true);
                des.setGravity(Gravity.CENTER);
                des.setMinHeight(Ui.dp(c, 48));
                des.setBackground(Ui.touchable(c, Ui.arrondi(c, 0x00000000, 12, 0), 12));
                des.setOnClickListener(v -> {
                    if (decide) return;
                    jeu.arreter();
                    resultat(tirage < chance, true);
                });
                colonne.addView(des, Ui.large());
            }
            statut(jeu.depart());
        }

        void statut(String s) {
            statut.setText(s);
        }

        /** Le jeu est fini : le résultat s'affiche, avec Pilou qui réagit ; « Continuer » rend la main au récit. */
        void resultat(boolean ok, boolean auxDes) {
            if (decide) return;
            decide = true;
            Context c = getContext();
            Ui.vibrer(c, ok ? 18 : 40);
            FrameLayout voile = new FrameLayout(c);
            voile.setBackgroundColor(0xcc0d1117);
            voile.setClickable(true);
            LinearLayout carte = Ui.pile(c);
            carte.setGravity(Gravity.CENTER_HORIZONTAL);
            android.graphics.drawable.GradientDrawable g = new android.graphics.drawable.GradientDrawable();
            g.setColor(Vitrine.NUIT);
            g.setStroke(Ui.dp(c, 3), ok ? Vitrine.ORANGE : Vitrine.ARGENT);
            g.setCornerRadius(Ui.dp(c, 10));
            carte.setBackground(g);
            carte.setPadding(Ui.dp(c, 20), Ui.dp(c, 18), Ui.dp(c, 20), Ui.dp(c, 18));
            carte.addView(new Vitrine.Pixel(c, ok ? "REUSSI !" : "RATE...", 4, ok ? Vitrine.ORANGE : Vitrine.ARGENT_CLAIR, Vitrine.VIOLET_FONCE, false));
            PilouVue p = new PilouVue(c, Aventure.pixelPour(c, 96), true);
            p.montrer(ok ? "joie" : "triste", Prefs.etat(c).couleur);
            if (ok) p.jouer("fete", 1800);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.topMargin = Ui.dp(c, 10);
            carte.addView(p, lp);
            TextView t = Ui.texte(c, (ok ? "✓  " : "✕  ") + (auxDes ? (ok ? "Les dés sont avec Pilou." : "Les dés n'ont pas voulu.")
                    : ok ? "Pilou s'en sort haut la main !" : "Pilou rate son coup… l'histoire continue quand même."), Ui.T_CORPS, Vitrine.ARGENT_CLAIR, true);
            t.setGravity(Gravity.CENTER);
            t.setPadding(0, Ui.dp(c, 10), 0, Ui.dp(c, 14));
            carte.addView(t, Ui.large());
            android.widget.Button b = Ui.bouton(c, "Continuer", true, v -> fin.accept(ok));
            b.setBackground(Ui.touchable(c, Ui.arrondi(c, Vitrine.ORANGE, 8, 0), 8));
            b.setTextColor(Vitrine.ENCRE);
            carte.addView(b, Ui.large());
            LayoutParams lc = new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);
            lc.leftMargin = lc.rightMargin = Ui.dp(c, 24);
            voile.addView(carte, lc);
            addView(voile, new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            if (ok) voile.addView(new Aventure.Etincelles(c, new int[]{Vitrine.ORANGE, Vitrine.BLEU_CLAIR, Aventure.CREME}),
                    new LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            if (Vitrine.anime(c)) {
                carte.setScaleX(0.85f);
                carte.setScaleY(0.85f);
                carte.setAlpha(0);
                carte.animate().scaleX(1).scaleY(1).alpha(1).setDuration(240)
                        .setInterpolator(new android.view.animation.OvershootInterpolator(1.6f)).start();
            }
            statut.setText("");
        }

        /** Pour les tests : le jeu finit tout de suite, comme si on l'avait joué. */
        void forcer(boolean ok) {
            jeu.arreter();
            resultat(ok, false);
        }

        Jeu jeu() {
            return jeu;
        }

        boolean decide() {
            return decide;
        }
    }

    // ---- Le socle d'un jeu

    abstract static class Jeu extends View {
        Ecran ecran;
        final int diff;
        final Paint pt = new Paint();
        final float b;
        long debut = -1;
        boolean fini;
        final Random r = new Random(SystemClock.uptimeMillis());
        /** Durée maximale (ms) : au-delà, ce qui reste compte comme raté. */
        long limite = 22_000;

        Jeu(Context c, int difficulte) {
            super(c);
            diff = Math.max(1, Math.min(3, difficulte));
            pt.setAntiAlias(false);
            b = Math.max(2, Math.round(Ui.dp(c, 4)));
            setContentDescription("Zone de jeu : touche pour commencer");
        }

        /** Le texte du statut avant de commencer. */
        String depart() {
            return "Touche la zone de jeu pour commencer";
        }

        long t() {
            return debut < 0 ? 0 : SystemClock.uptimeMillis() - debut;
        }

        abstract void commencer();

        abstract void toucher(float x, float y);

        abstract void dessiner(Canvas cv, long t);

        void arreter() {
            fini = true;
        }

        void terminer(boolean ok) {
            if (fini) return;
            fini = true;
            postDelayed(() -> ecran.resultat(ok, false), 450);
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            if (e.getActionMasked() != MotionEvent.ACTION_DOWN || fini) return true;
            if (debut < 0) {
                debut = SystemClock.uptimeMillis();
                commencer();
            } else toucher(e.getX(), e.getY());
            invalidate();
            return true;
        }

        @Override
        protected void onDraw(Canvas cv) {
            long t = t();
            if (debut >= 0 && !fini && t > limite) temps();
            dessiner(cv, t);
            if (debut >= 0 && limite < Long.MAX_VALUE && !fini) {
                // Le temps qui reste : un fil orange en haut de la zone.
                float part = Math.max(0, 1 - t / (float) limite);
                pt.setColor(Vitrine.ORANGE);
                cv.drawRect(b * 2, b, b * 2 + (getWidth() - b * 4) * part, b * 2, pt);
            }
            if (debut < 0) {
                pt.setColor(Vitrine.ARGENT_CLAIR);
                Dessin.Peintre pe = (g, h, d, bb, col) -> {
                    pt.setColor(col);
                    cv.drawRect(g, h, d, bb, pt);
                };
                float px = Math.max(2, b * 0.75f);
                Police.centre(pe, "TOUCHE POUR COMMENCER", getWidth() / 2f, getHeight() - px * 10, px, Vitrine.ARGENT_CLAIR, Vitrine.VIOLET_FONCE);
            }
            if (!fini && isShown()) postInvalidateDelayed(16);
        }

        /** Le temps est écoulé. */
        void temps() {
            terminer(false);
        }

        void carre(Canvas cv, float x, float y, float cote, int couleur) {
            pt.setColor(couleur);
            cv.drawRect(Math.round(x), Math.round(y), Math.round(x + cote), Math.round(y + cote), pt);
        }

        void texte(Canvas cv, String s, float cx, float y, float px, int couleur) {
            Dessin.Peintre pe = (g, h, d, bb, col) -> {
                pt.setColor(col);
                cv.drawRect(g, h, d, bb, pt);
            };
            Police.centre(pe, s, cx, y, px, couleur, Vitrine.NUIT);
        }
    }

    // ---- Réflexe : le curseur passe et repasse ; toucher quand il est dans la zone orange.

    static final class Reflexe extends Jeu {
        private final int tours = 3, requis = 2;
        private int tour, reussis, rates;
        private float centre, largeur;
        private long pause = -1;
        private String signe = "";
        private boolean dernierOk;

        Reflexe(Context c, int d) {
            super(c, d);
            largeur = d == 1 ? 0.28f : d == 2 ? 0.2f : 0.14f;
            limite = 20_000;
            nouvelleZone();
        }

        private void nouvelleZone() {
            centre = 0.22f + r.nextFloat() * 0.56f;
        }

        private float vitesse() {
            return (diff == 1 ? 0.55f : diff == 2 ? 0.75f : 0.95f) + tour * 0.08f;
        }

        private float position(long t) {
            float k = (t / 1000f * vitesse()) % 2f;
            return k < 1 ? k : 2 - k;
        }

        @Override
        String depart() {
            return "Deux sur trois : 0 / " + requis;
        }

        @Override
        void commencer() {
            ecran.statut("Réussis : 0 / " + requis);
        }

        @Override
        void toucher(float x, float y) {
            if (pause >= 0) return;
            float pos = position(t());
            boolean ok = Math.abs(pos - centre) <= largeur / 2;
            if (ok) reussis++;
            else rates++;
            dernierOk = ok;
            signe = ok ? "✓" : "✕";
            Ui.vibrer(getContext(), ok ? 10 : 22);
            pause = t();
            tour++;
            ecran.statut("Réussis : " + reussis + " / " + requis);
            if (reussis >= requis) terminer(true);
            else if (rates > tours - requis) terminer(false);
        }

        @Override
        void dessiner(Canvas cv, long t) {
            float w = getWidth(), h = getHeight(), x0 = w * 0.08f, x1 = w * 0.92f, y = h * 0.55f, hb = b * 6;
            if (pause >= 0 && t - pause > 700) {
                pause = -1;
                nouvelleZone();
            }
            // La barre, la zone, le curseur.
            pt.setColor(Vitrine.NUIT3);
            cv.drawRect(x0, y, x1, y + hb, pt);
            float zx = x0 + (centre - largeur / 2) * (x1 - x0), zw = largeur * (x1 - x0);
            pt.setColor(Vitrine.ORANGE);
            cv.drawRect(zx, y, zx + zw, y + hb, pt);
            pt.setColor(Vitrine.ORANGE_CLAIR);
            cv.drawRect(zx, y, zx + zw, y + b, pt);
            float pos = pause >= 0 ? position(pause) : position(t);
            float cx = x0 + pos * (x1 - x0);
            int cc = pause >= 0 ? (dernierOk ? Vitrine.BLEU_CLAIR : Vitrine.ARGENT) : Aventure.CREME;
            pt.setColor(cc);
            cv.drawRect(cx - b / 2, y - b * 3, cx + b / 2, y + hb + b * 3, pt);
            for (int i = 0; i < 3; i++) cv.drawRect(cx - b * (1.5f - i * 0.5f) - b / 2, y - b * (6 - i), cx + b * (1.5f - i * 0.5f) + b / 2, y - b * (5 - i), pt);
            // Les tours : cases pleines (réussi), barrées (raté), vides (à venir).
            for (int i = 0; i < tours; i++) {
                float bx = w / 2 + (i - 1) * b * 6 - b * 2, by = h * 0.2f;
                int col = i < reussis + rates ? (i < histo.length() && histo.charAt(i) == '1' ? Vitrine.BLEU : Vitrine.ARGENT) : Vitrine.NUIT3;
                carre(cv, bx, by, b * 4, col);
            }
            if (pause >= 0 && !signe.isEmpty()) {
                pt.setColor(dernierOk ? Vitrine.BLEU_CLAIR : Vitrine.ARGENT_CLAIR);
                pt.setTextSize(b * 9);
                pt.setTextAlign(Paint.Align.CENTER);
                pt.setAntiAlias(true);
                cv.drawText(signe, w / 2, h * 0.45f, pt);
                pt.setAntiAlias(false);
            }
        }

        /** L'historique des tours (pour les cases) : '1' réussi, '0' raté. */
        private final StringBuilder histo = new StringBuilder();

        @Override

        public boolean onTouchEvent(MotionEvent e) {
            int avant = reussis + rates;
            boolean r2 = super.onTouchEvent(e);
            if (reussis + rates > avant) histo.append(dernierOk ? '1' : '0');
            return r2;
        }
    }

    // ---- Mémoire : quatre signes s'allument dans un ordre ; le refaire.

    static final class Memoire extends Jeu {
        private static final int[] COULEURS = {Vitrine.BLEU, Vitrine.ORANGE, Vitrine.VIOLET, Aventure.CREME};
        private static final String[][] FORMES = {
                {"0011100", "0111110", "1111111", "1111111", "1111111", "0111110", "0011100"},
                {"0001000", "0011100", "0011100", "0111110", "0111110", "1111111", "1111111"},
                {"1111111", "1111111", "1111111", "1111111", "1111111", "1111111", "1111111"},
                {"0001000", "0011100", "0111110", "1111111", "0111110", "0011100", "0001000"}};
        private final int[] suite;
        private int saisis, vies = 2;
        private long montreDepuis = -1;
        private int allume = -1;
        private long allumeJusque;
        private boolean montre;
        private final long pas;

        Memoire(Context c, int d) {
            super(c, d);
            suite = new int[2 + d];
            for (int i = 0; i < suite.length; i++) suite[i] = r.nextInt(4);
            pas = d == 1 ? 700 : d == 2 ? 600 : 520;
            limite = 25_000;
        }

        @Override
        String depart() {
            return "Une suite de " + suite.length + " signes";
        }

        @Override
        void commencer() {
            montrer();
        }

        private void montrer() {
            montre = true;
            montreDepuis = t() + 400;
            saisis = 0;
            ecran.statut("Regarde bien…");
        }

        private int case_(float x, float y) {
            float w = getWidth(), h = getHeight(), cote = Math.min(w, h) * 0.38f, gx = w / 2 - cote - b * 2, gy = h / 2 - cote - b * 2;
            for (int i = 0; i < 4; i++) {
                float cx = gx + (i % 2) * (cote + b * 4), cy = gy + (i / 2) * (cote + b * 4);
                if (x >= cx && x <= cx + cote && y >= cy && y <= cy + cote) return i;
            }
            return -1;
        }

        @Override
        void toucher(float x, float y) {
            if (montre) return;
            int k = case_(x, y);
            if (k < 0) return;
            allume = k;
            allumeJusque = t() + 220;
            if (suite[saisis] == k) {
                saisis++;
                Ui.vibrer(getContext(), 8);
                ecran.statut("À toi : " + saisis + " / " + suite.length);
                if (saisis == suite.length) terminer(true);
            } else {
                vies--;
                Ui.vibrer(getContext(), 30);
                if (vies <= 0) terminer(false);
                else {
                    ecran.statut("✕  Raté — encore une chance, regarde à nouveau");
                    postDelayed(this::montrer, 700);
                }
            }
        }

        @Override
        void dessiner(Canvas cv, long t) {
            float w = getWidth(), h = getHeight(), cote = Math.min(w, h) * 0.38f, gx = w / 2 - cote - b * 2, gy = h / 2 - cote - b * 2;
            int actif = -1;
            if (montre && montreDepuis >= 0 && t >= montreDepuis) {
                long k = (t - montreDepuis) / pas;
                if (k >= suite.length) {
                    montre = false;
                    ecran.statut("À toi : 0 / " + suite.length);
                } else if ((t - montreDepuis) % pas < pas * 0.7f) actif = suite[(int) k];
            }
            if (!montre && t < allumeJusque) actif = allume;
            for (int i = 0; i < 4; i++) {
                float cx = gx + (i % 2) * (cote + b * 4), cy = gy + (i / 2) * (cote + b * 4);
                boolean on = i == actif;
                pt.setColor(on ? COULEURS[i] : Vitrine.NUIT3);
                cv.drawRect(cx, cy, cx + cote, cy + cote, pt);
                float px = Math.max(2, Math.round(cote / 12f));
                Police.motif((g, hh, d, bb, col) -> {
                    pt.setColor(col);
                    cv.drawRect(g, hh, d, bb, pt);
                }, FORMES[i], cx + cote / 2 - px * 3.5f, cy + cote / 2 - px * 3.5f, px, new int[]{0, on ? Vitrine.NUIT : COULEURS[i]});
            }
        }
    }

    // ---- Rythme : les notes arrivent sur la ligne ; toucher au bon moment.

    static final class Rythme extends Jeu {
        private final long[] notes = new long[8];
        private final int[] juge = new int[8]; // 0 à venir, 1 réussie, 2 ratée
        private final long tolerance, intervalle;
        private final int requis;
        private int reussies, ratees;
        private long eclair = -1;

        Rythme(Context c, int d) {
            super(c, d);
            intervalle = d == 1 ? 720 : d == 2 ? 620 : 540;
            tolerance = d == 1 ? 190 : d == 2 ? 150 : 115;
            requis = d == 1 ? 5 : 6;
            for (int i = 0; i < notes.length; i++) notes[i] = 1600 + i * intervalle + (i % 4 == 3 ? intervalle / 2 : 0);
            limite = notes[notes.length - 1] + 1200;
        }

        @Override
        String depart() {
            return "Au moins " + requis + " notes sur 8";
        }

        @Override
        void commencer() {
            ecran.statut("Notes : 0 / " + requis);
        }

        @Override
        void toucher(float x, float y) {
            long t = t();
            int meilleure = -1;
            long ecart = Long.MAX_VALUE;
            for (int i = 0; i < notes.length; i++)
                if (juge[i] == 0 && Math.abs(notes[i] - t) < ecart) {
                    ecart = Math.abs(notes[i] - t);
                    meilleure = i;
                }
            if (meilleure < 0 || ecart > 320) return;
            if (ecart <= tolerance) {
                juge[meilleure] = 1;
                reussies++;
                eclair = t;
                Ui.vibrer(getContext(), 8);
            } else {
                juge[meilleure] = 2;
                ratees++;
            }
            bilan();
        }

        private void bilan() {
            ecran.statut("Notes : " + reussies + " / " + requis);
            if (reussies >= requis) terminer(true);
            else if (ratees > notes.length - requis) terminer(false);
        }

        @Override
        void temps() {
            terminer(reussies >= requis);
        }

        @Override
        void dessiner(Canvas cv, long t) {
            float w = getWidth(), h = getHeight(), y = h / 2, ligne = w * 0.2f;
            for (int i = 0; i < notes.length; i++)
                if (juge[i] == 0 && t - notes[i] > tolerance) {
                    juge[i] = 2;
                    ratees++;
                    bilan();
                }
            // La piste et la ligne.
            pt.setColor(Vitrine.NUIT3);
            cv.drawRect(0, y - b * 5, w, y + b * 5, pt);
            boolean bat = debut >= 0 && t - eclair < 180;
            pt.setColor(bat ? Vitrine.BLEU_CLAIR : Vitrine.VIOLET);
            cv.drawRect(ligne - b, y - b * 8, ligne + b, y + b * 8, pt);
            float vitesse = (w * 0.8f) / 1500f; // px par ms
            for (int i = 0; i < notes.length; i++) {
                float x = ligne + (notes[i] - t) * vitesse;
                if (x < -b * 4 || x > w + b * 4) continue;
                int col = juge[i] == 1 ? Vitrine.BLEU_CLAIR : juge[i] == 2 ? Vitrine.ARGENT : Vitrine.ORANGE;
                // Une croche pixel : tête, hampe, drapeau.
                carre(cv, x - b * 2, y, b * 3, col);
                pt.setColor(col);
                cv.drawRect(x + b, y - b * 5, x + b * 1.8f, y + b, pt);
                cv.drawRect(x + b, y - b * 5, x + b * 3, y - b * 4, pt);
                if (juge[i] == 2) {
                    pt.setColor(Vitrine.NUIT);
                    cv.drawRect(x - b * 2, y + b, x + b, y + b * 1.6f, pt);
                }
            }
            // Les notes passées : ✓ ou ✕ en petit, au-dessus.
            float px = Math.max(2, b * 0.6f);
            texte(cv, reussies + " / " + requis, w / 2, h * 0.18f, px * 2, Vitrine.ARGENT_CLAIR);
        }
    }

    // ---- Visée : des cibles apparaissent et filent ; les toucher.

    static final class Visee extends Jeu {
        private final int total = 6, requis;
        private int vues, touchees;
        private float cx, cy, vx, vy, rayon;
        private long nee = -1, vie;
        private long eclat = -1;
        private float ex, ey;

        Visee(Context c, int d) {
            super(c, d);
            requis = d == 3 ? 5 : 4;
            vie = d == 1 ? 1700 : d == 2 ? 1350 : 1050;
            rayon = Ui.dp(c, d == 1 ? 34 : d == 2 ? 30 : 26);
            limite = Long.MAX_VALUE;
        }

        @Override
        String depart() {
            return "Touche " + requis + " cibles sur " + total;
        }

        @Override
        void commencer() {
            ecran.statut("Cibles : 0 / " + requis);
            nouvelle(t() + 500);
        }

        private void nouvelle(long quand) {
            if (vues >= total) {
                terminer(touchees >= requis);
                return;
            }
            float w = Math.max(1, getWidth()), h = Math.max(1, getHeight());
            cx = rayon + r.nextFloat() * (w - 2 * rayon);
            cy = rayon * 1.5f + r.nextFloat() * (h - 3 * rayon);
            double a = r.nextDouble() * Math.PI * 2;
            float v = Ui.dp(getContext(), 40 + diff * 25) / 1000f;
            vx = (float) Math.cos(a) * v;
            vy = (float) Math.sin(a) * v;
            nee = quand;
            vues++;
        }

        @Override
        void toucher(float x, float y) {
            long t = t();
            if (nee < 0 || t < nee) return;
            float[] p = position(t);
            if (Math.hypot(x - p[0], y - p[1]) <= rayon * 1.3f) {
                touchees++;
                eclat = t;
                ex = p[0];
                ey = p[1];
                Ui.vibrer(getContext(), 8);
                ecran.statut("Cibles : " + touchees + " / " + requis);
                if (touchees >= requis) {
                    terminer(true);
                    return;
                }
                nee = -1;
                postDelayed(() -> nouvelle(t() + 250), 150);
            }
        }

        private final float[] pos = new float[2];

        private float[] position(long t) {
            float dt = t - nee, w = getWidth(), h = getHeight();
            float x = cx + vx * dt, y = cy + vy * dt;
            // Rebond sur les bords.
            float lw = Math.max(1, w - 2 * rayon), lh = Math.max(1, h - 2 * rayon);
            x = rayon + rebond(x - rayon, lw);
            y = rayon + rebond(y - rayon, lh);
            pos[0] = x;
            pos[1] = y;
            return pos;
        }

        private static float rebond(float v, float l) {
            float k = ((v % (2 * l)) + 2 * l) % (2 * l);
            return k < l ? k : 2 * l - k;
        }

        @Override
        void dessiner(Canvas cv, long t) {
            if (nee >= 0 && t >= nee) {
                if (t - nee > vie) {
                    nee = -1;
                    if (touchees + (total - vues) < requis) terminer(false);
                    else postDelayed(() -> nouvelle(t() + 200), 50);
                } else {
                    float[] p = position(t);
                    float k = 1 - (t - nee) / (float) vie; // la cible pâlit en filant
                    for (int i = 3; i >= 0; i--) {
                        float rr = rayon * (i + 1) / 4f;
                        pt.setColor(i % 2 == 0 ? Vitrine.ORANGE : Aventure.CREME);
                        pt.setAlpha((int) (120 + 135 * k));
                        float s = Math.round(rr / b) * b;
                        cv.drawRect(Math.round((p[0] - s) / b) * b, Math.round((p[1] - s) / b) * b, Math.round((p[0] + s) / b) * b, Math.round((p[1] + s) / b) * b, pt);
                    }
                    pt.setAlpha(255);
                }
            }
            if (eclat >= 0 && t - eclat < 350) {
                float e = (t - eclat) / 350f * rayon * 1.6f;
                pt.setColor(Vitrine.BLEU_CLAIR);
                for (int i = 0; i < 8; i++) {
                    double a = i * Math.PI / 4;
                    carre(cv, ex + (float) Math.cos(a) * e - b / 2, ey + (float) Math.sin(a) * e - b / 2, b, Vitrine.BLEU_CLAIR);
                }
            }
            // Les cibles : touchées (pleines), manquées (barrées), à venir (vides).
            for (int i = 0; i < total; i++) {
                float x = getWidth() / 2f + (i - total / 2f) * b * 5, y = getHeight() - b * 6;
                carre(cv, x, y, b * 3, i < touchees ? Vitrine.BLEU : i < vues - (nee >= 0 ? 1 : 0) ? Vitrine.ARGENT : Vitrine.NUIT3);
            }
        }
    }

    // ---- Les dés : le tirage du moteur, animé.

    static final class Des extends Jeu {
        private final int chance, tirage;
        private final long duree = 2400;

        Des(Context c, int chance, int tirage) {
            super(c, 1);
            this.chance = chance;
            this.tirage = tirage;
            limite = Long.MAX_VALUE;
            setContentDescription("Les dés roulent : " + chance + " pour cent de chance");
        }

        @Override
        String depart() {
            return "Les dés roulent…";
        }

        @Override
        protected void onAttachedToWindow() {
            super.onAttachedToWindow();
            debut = SystemClock.uptimeMillis();
            if (!Vitrine.anime(getContext())) debut -= duree;
        }

        @Override
        void commencer() {
        }

        @Override
        void toucher(float x, float y) {
            debut -= duree; // impatient : le dé s'arrête tout de suite
        }

        private int valeur(long t) {
            if (t >= duree) return tirage;
            // Le dé ralentit : il change de moins en moins souvent, puis tombe sur le tirage.
            float k = t / (float) duree;
            long pas = (long) (40 + 260 * k * k);
            return new Random(t / pas * 31 + 7).nextInt(100);
        }

        @Override
        void dessiner(Canvas cv, long t) {
            float w = getWidth(), h = getHeight(), x0 = w * 0.08f, x1 = w * 0.92f, y = h * 0.62f, hb = b * 5;
            int v = valeur(t);
            // La jauge : la part qui réussit (bleue) et le reste (argent sombre).
            float xc = x0 + chance / 100f * (x1 - x0);
            pt.setColor(Vitrine.BLEU);
            cv.drawRect(x0, y, xc, y + hb, pt);
            pt.setColor(Vitrine.FERME);
            cv.drawRect(xc, y, x1, y + hb, pt);
            float xv = x0 + (v + 0.5f) / 100f * (x1 - x0);
            pt.setColor(Aventure.CREME);
            cv.drawRect(xv - b / 2, y - b * 3, xv + b / 2, y + hb + b * 2, pt);
            float px = Math.max(3, b * 1.6f);
            boolean fin = t >= duree;
            int col = !fin ? Aventure.CREME : v < chance ? Vitrine.BLEU_CLAIR : Vitrine.ARGENT;
            texte(cv, String.format(java.util.Locale.ROOT, "%02d", v), w / 2, h * 0.22f, px * 2, col);
            texte(cv, "REUSSIR SOUS " + chance, w / 2, y + hb + b * 5, Math.max(2, b * 0.6f), Vitrine.ARGENT);
            if (fin && !fini) {
                fini = true;
                boolean ok = v < chance;
                postDelayed(() -> ecran.resultat(ok, true), 500);
            }
        }
    }
}
