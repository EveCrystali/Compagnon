package fr.pilou.compagnon;

import android.content.Context;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.view.View;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;

/**
 * Musiques et ambiances de l'Aventure (docs/SONS.md). Décrites dans assets/musiques.txt, synthétisées en entiers
 * exactement comme Musique.cs (PC) et outils/sons/sons.py : mêmes échantillons (outils/sons/musiques-reference.txt).
 * Lues par un AudioTrack en flux, seulement tant que la lecture d'une campagne est à l'écran.
 */
final class Musique {
    private Musique() {}

    static final int TAUX = Sons.TAUX;
    static final String[] NIVEAUX = {"aucune", "discrete", "normale"};
    static final String DEFAUT = "discrete";
    static final String[] TONS = {"prologue", "humour", "mystere", "emotion"};

    static final class Voix {
        final String onde;
        final int volume, attaque, relache, declin, tenue;
        final List<String> jetons = new ArrayList<>();

        Voix(String onde, int volume, int attaque, int relache, int declin, int tenue) {
            this.onde = onde;
            this.volume = volume;
            this.attaque = attaque;
            this.relache = relache;
            this.declin = declin;
            this.tenue = tenue;
        }
    }

    static final class Morceau {
        final int ms, pas, filtre;
        final boolean motif;
        final List<Voix> voix = new ArrayList<>();

        Morceau(int ms, int pas, int filtre, boolean motif) {
            this.ms = ms;
            this.pas = pas;
            this.filtre = filtre;
            this.motif = motif;
        }
    }

    static final class Catalogue {
        final Map<String, Morceau> morceaux = new LinkedHashMap<>();
        final Map<String, String> decors = new HashMap<>();
    }

    private static final long[] GAMME = {261626, 277183, 293665, 311127, 329628, 349228, 369994, 391995, 415305, 440000, 466164, 493883};
    private static final List<String> NOMS = Arrays.asList("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B");

    /** Jeton → milli-hertz : « A4 », « F#3 » ou un nombre de hertz (bruit). */
    static long frequence(String j) {
        if (Character.isDigit(j.charAt(0))) return Long.parseLong(j) * 1000;
        int octave = j.charAt(j.length() - 1) - '0';
        long f = GAMME[NOMS.indexOf(j.substring(0, j.length() - 1))];
        return octave >= 4 ? f << (octave - 4) : f >> (4 - octave);
    }

    static Catalogue lire(String texte) {
        Catalogue c = new Catalogue();
        Morceau courant = null;
        Voix voix = null;
        for (String brute : texte.split("\n")) {
            String l = brute.trim();
            if (l.isEmpty() || l.startsWith("#")) continue;
            String[] p = l.split("\\|");
            for (int i = 0; i < p.length; i++) p[i] = p[i].trim();
            String[] jetons = p[p.length - 1].isEmpty() ? new String[0] : p[p.length - 1].split("\\s+");
            switch (p[0]) {
                case "morceau":
                    courant = new Morceau(Integer.parseInt(p[2]), Integer.parseInt(p[3]), Integer.parseInt(p[4]), p.length > 5 && p[5].equals("motif"));
                    c.morceaux.put(p[1], courant);
                    break;
                case "voix":
                    voix = new Voix(p[1], Integer.parseInt(p[2]), Integer.parseInt(p[3]), Integer.parseInt(p[4]),
                            Integer.parseInt(p[5]), Integer.parseInt(p[6]));
                    voix.jetons.addAll(Arrays.asList(jetons));
                    courant.voix.add(voix);
                    break;
                case "+":
                    voix.jetons.addAll(Arrays.asList(jetons));
                    break;
                case "decors":
                    for (String d : jetons) c.decors.put(d, p[1]);
                    break;
                default:
                    break;
            }
        }
        return c;
    }

    /** {pas, longueur, f0, f1} par note ; la suite se répète ; dans une boucle, une note tenue au bout repart au début. */
    static List<long[]> notes(List<String> jetons, int pas, boolean boucle) {
        String[] e = new String[pas];
        for (int k = 0; k < pas; k++) e[k] = jetons.get(k % jetons.size());
        List<long[]> n = new ArrayList<>();
        for (int k = 0; k < pas; k++) {
            if (e[k].equals("-") || e[k].equals(".")) continue;
            int longueur = 1;
            while (longueur < pas && (boucle || k + longueur < pas) && e[(k + longueur) % pas].equals("-")) longueur++;
            String[] f = e[k].split(">");
            n.add(new long[]{k, longueur, frequence(f[0]), frequence(f[f.length - 1])});
        }
        return n;
    }

    /** Échantillons 16 bits de la boucle au réglage « normale » ; le dernier enchaîne sur le premier. */
    static short[] synthetiser(Morceau m) {
        int pasEch = TAUX * m.ms / 1000, total = pasEch * m.pas + (m.motif ? TAUX * 20 / 1000 : 0);
        long[] acc = new long[total];
        for (Voix v : m.voix) {
            for (long[] note : notes(v.jetons, m.pas, !m.motif)) {
                int s0 = (int) note[0] * pasEch, n = (int) note[1] * pasEch;
                long f0 = note[2], f1 = note[3];
                if (v.tenue > 0) n = Math.min(n, TAUX * v.tenue / 1000);
                int a = Math.min(n / 2, TAUX * v.attaque / 1000), r = Math.min(n / 2, TAUX * v.relache / 1000);
                long phase = 0;
                int lfsr = 1;
                for (int i = 0; i < n; i++) {
                    long fm = (f0 * (n - i) + f1 * i) / n;
                    long inc = fm * 4294967296L / (TAUX * 1000L);
                    long avant = phase;
                    phase = (phase + inc) & 0xFFFFFFFFL;
                    int p = (int) (phase >> 16);
                    long x;
                    if (v.onde.equals("tri")) {
                        int t = p < 32768 ? p : 65535 - p;
                        x = ((t >> 11) * 2 - 15) * 2184L;
                    } else if (v.onde.equals("puls")) {
                        x = p < 16384 ? 24000 : -8000;
                    } else {
                        if (phase < avant) {
                            int b = (lfsr ^ (lfsr >> 1)) & 1;
                            lfsr = (lfsr >> 1) | (b << 14);
                        }
                        x = (lfsr & 1) != 0 ? 20000 : -20000;
                    }
                    long e = 4096;
                    if (i < a) e = 4096L * i / a;
                    if (r > 0 && i >= n - r) {
                        long q = n - i;
                        e = Math.min(e, 4096L * q * q / ((long) r * r));
                    }
                    e = e * (4096 - (long) v.declin * i / n) / 4096;
                    acc[(s0 + i) % total] += (x * e * v.volume * 10) >> 24;
                }
            }
        }
        // Passe-bas en anneau : un tour pour mettre le filtre en régime, le second donne la sortie.
        short[] sortie = new short[total];
        long y1 = 0, y2 = 0;
        for (int tour = 0; tour < (m.motif ? 1 : 2); tour++) {
            for (int i = 0; i < total; i++) {
                y1 += (((acc[i] << 8) - y1) * m.filtre) >> 8;
                y2 += ((y1 - y2) * m.filtre) >> 8;
                if (tour == 1 || m.motif) sortie[i] = (short) Math.max(-32767, Math.min(32767, y2 >> 8));
            }
        }
        if (m.motif) {
            int q = TAUX * 8 / 1000;
            for (int i = total - q; i < total; i++) {
                long g = ((long) (total - 1 - i) << 16) / q;
                sortie[i] = (short) ((sortie[i] * g) >> 16);
            }
        }
        return sortie;
    }

    /** Le prologue a sa musique, les autres campagnes celle de leur ton. */
    static String pour(String campagne, String ton) {
        return pour(campagne, ton, null);
    }

    /**
     * Le champ facultatif « musique » d'une scène ou d'un nœud ({@code demande}) nomme un morceau, ou « calme » /
     * « tension », la variante de la boucle du moment ; sans champ, la boucle du prologue ou du ton (comme Musique.Pour).
     */
    static String pour(String campagne, String ton, String demande) {
        String base = "prologue".equals(campagne) ? "prologue"
                : "humour".equals(ton) || "mystere".equals(ton) || "emotion".equals(ton) ? ton : null;
        if (demande == null || demande.isEmpty()) return base;
        Map<String, Morceau> c = catalogue().morceaux;
        if (c.containsKey(demande)) return demande;
        return base != null && c.containsKey(base + "-" + demande) ? base + "-" + demande : base;
    }

    static boolean estMotif(String id) {
        Morceau m = catalogue().morceaux.get(id);
        return m != null && m.motif;
    }

    static String ambiance(String decor) {
        return decor == null ? null : catalogue().decors.get(decor);
    }

    /** Gain sur 65536 : « discrète » = × 3 / 8 (environ -8,5 dB). */
    static int gain(String niveau) {
        return "normale".equals(niveau) ? 65536 : "discrete".equals(niveau) ? 65536 * 3 / 8 : 0;
    }

    static String niveau(Context c) {
        return Prefs.de(c).getString("musique", DEFAUT);
    }

    // ---- Table de mixage (sans audio : testable), comme Melangeur sur le PC ----

    static final class Melangeur {
        static final int ENTREE = TAUX * 3 / 2, SORTIE = TAUX;

        interface Boucles {
            short[] boucle(String id);
        }

        interface Motifs {
            boolean motif(String id);
        }

        private static final class Couche {
            String id;
            boolean musique, unique;
            short[] s;
            int pos, gain, cible;
        }

        private final Boucles boucles;
        private final Motifs motifs;
        private final List<Couche> couches = new ArrayList<>();
        private String dernierMotif;

        Melangeur(Boucles boucles) {
            this(boucles, id -> false);
        }

        /** Un motif (une fin) part tout de suite, joue une fois et laisse le silence ; il rejoue après un autre morceau. */
        Melangeur(Boucles boucles, Motifs motifs) {
            this.boucles = boucles;
            this.motifs = motifs;
        }

        synchronized boolean silencieux() {
            return couches.isEmpty();
        }

        synchronized void viser(String musique, String ambiance, int gain) {
            regler(true, musique, gain);
            regler(false, ambiance, gain);
        }

        private void regler(boolean musique, String id, int gain) {
            boolean present = false;
            for (Couche c : couches) {
                if (c.musique != musique) continue;
                boolean garde = c.id.equals(id) && gain > 0;
                c.cible = garde ? gain : 0;
                present |= garde;
            }
            boolean motif = id != null && musique && motifs.motif(id);
            if (musique && !motif && id != null) dernierMotif = null;
            if (present || id == null || gain <= 0 || (motif && id.equals(dernierMotif))) return;
            short[] s = boucles.boucle(id);
            if (s == null || s.length == 0) return;
            Couche c = new Couche();
            c.id = id;
            c.musique = musique;
            c.s = s;
            c.cible = gain;
            c.unique = motif;
            c.gain = motif ? gain : 0;
            couches.add(c);
            if (motif) dernierMotif = id;
        }

        synchronized void remplir(short[] bloc) {
            long[] somme = new long[bloc.length];
            for (Couche c : couches) {
                int monte = Math.max(1, (c.cible + ENTREE - 1) / ENTREE), descend = (65536 + SORTIE - 1) / SORTIE;
                for (int i = 0; i < bloc.length; i++) {
                    if (c.gain < c.cible) c.gain = Math.min(c.cible, c.gain + monte);
                    else if (c.gain > c.cible) c.gain = Math.max(c.cible, c.gain - descend);
                    somme[i] += ((long) c.s[c.pos] * c.gain) >> 16;
                    if (++c.pos < c.s.length) continue;
                    c.pos = 0;
                    if (!c.unique) continue;
                    c.gain = 0;
                    c.cible = 0;
                    break;
                }
            }
            for (int i = 0; i < bloc.length; i++) bloc[i] = (short) Math.max(-32767, Math.min(32767, somme[i]));
            for (Iterator<Couche> it = couches.iterator(); it.hasNext(); ) {
                Couche c = it.next();
                if (c.gain == 0 && c.cible == 0) it.remove();
            }
        }
    }

    // ---- Lecture ----

    private static Catalogue catalogue;
    private static final Map<String, short[]> BOUCLES = new HashMap<>();
    private static final Set<String> EN_CALCUL = new HashSet<>();
    private static final Melangeur TABLE = new Melangeur(Musique::boucle, Musique::estMotif);
    private static Thread fil;

    private static synchronized Catalogue catalogue() {
        if (catalogue == null) catalogue = lire(Sons.ressource("/musiques.txt"));
        return catalogue;
    }

    /** La boucle si elle est prête ; sinon son calcul part à côté et le prochain tour la prend. */
    private static short[] boucle(String id) {
        Morceau m = catalogue().morceaux.get(id);
        synchronized (BOUCLES) {
            short[] s = BOUCLES.get(id);
            if (s != null || m == null || !EN_CALCUL.add(id)) return s;
        }
        new Thread(() -> {
            short[] b = synthetiser(m);
            synchronized (BOUCLES) {
                BOUCLES.put(id, b);
                EN_CALCUL.remove(id);
            }
        }, "Musique de Pilou (calcul)").start();
        return null;
    }

    /**
     * Une ligne dans la lecture d'une campagne : la musique suit la campagne, l'ambiance suit le décor, tant que la
     * vue est à l'écran et que sa fenêtre a le premier plan. Silence pendant un appel ou une visio et en silencieux.
     */
    static void suivre(View v, Supplier<String> campagne, Supplier<String> ton, Supplier<String> decor) {
        suivre(v, campagne, ton, decor, () -> null);
    }

    /** {@code demande} : le champ facultatif « musique » de la scène ou du nœud en cours (voir pour). */
    static void suivre(View v, Supplier<String> campagne, Supplier<String> ton, Supplier<String> decor, Supplier<String> demande) {
        Runnable[] tour = new Runnable[1];
        tour[0] = () -> {
            try {
                Context c = v.getContext();
                AudioManager am = (AudioManager) c.getSystemService(Context.AUDIO_SERVICE);
                boolean cache = am == null || am.getMode() != AudioManager.MODE_NORMAL
                        || am.getRingerMode() != AudioManager.RINGER_MODE_NORMAL;
                int g = gain(niveau(c));
                boolean actif = g > 0 && v.isAttachedToWindow() && v.isShown() && v.hasWindowFocus() && !cache;
                viser(actif ? pour(campagne.get(), ton.get(), demande.get()) : null, actif ? ambiance(decor.get()) : null, g);
            } catch (RuntimeException e) {
                viser(null, null, 0);
            }
            if (v.isAttachedToWindow()) v.postDelayed(tour[0], 250);
        };
        v.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener() {
            @Override public void onViewAttachedToWindow(View x) {
                x.removeCallbacks(tour[0]);
                x.post(tour[0]);
            }

            @Override public void onViewDetachedFromWindow(View x) {
                x.removeCallbacks(tour[0]);
                viser(null, null, 0);
            }
        });
        if (v.isAttachedToWindow()) v.post(tour[0]);
    }

    private static void viser(String musique, String ambiance, int gain) {
        TABLE.viser(musique, ambiance, gain);
        synchronized (TABLE) {
            if (TABLE.silencieux() || fil != null) return;
            fil = new Thread(Musique::jouer, "Musique de Pilou");
            fil.start();
        }
    }

    /** Écrit des blocs de 100 ms dans un AudioTrack en flux ; s'arrête (et rend la sortie audio) une fois tout éteint. */
    private static void jouer() {
        AudioTrack t = null;
        try {
            int taille = TAUX / 10;
            int min = AudioTrack.getMinBufferSize(TAUX, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT);
            t = new AudioTrack.Builder()
                    .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME)
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
                    .setAudioFormat(new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(TAUX)
                            .setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .setBufferSizeInBytes(Math.max(min, taille * 4))
                    .build();
            t.play();
            short[] bloc = new short[taille];
            while (true) {
                synchronized (TABLE) {
                    if (TABLE.silencieux()) {
                        fil = null;
                        break;
                    }
                }
                TABLE.remplir(bloc);
                t.write(bloc, 0, bloc.length);
            }
        } catch (RuntimeException e) {
            // pas de sortie audio : silence
        } finally {
            if (t != null) {
                try {
                    t.stop();
                } catch (IllegalStateException ignore) {
                    // déjà arrêté
                }
                t.release();
            }
            synchronized (TABLE) {
                if (fil == Thread.currentThread()) fil = null;
            }
        }
    }
}
