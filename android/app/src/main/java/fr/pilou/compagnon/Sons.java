package fr.pilou.compagnon;

import android.app.NotificationManager;
import android.content.Context;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Petits sons rétro synthétisés en code : aucun fichier, aucun droit d'auteur. Deux familles :
 * les sons de Chasse aux bugs (instance, réglage « son ») et les sons de Pilou (docs/SONS.md), décrits dans
 * /sons.txt (assets/ du dépôt) et synthétisés en entiers exactement comme Sons.cs sur le PC et outils/sons/sons.py
 * (empreintes : outils/sons/sons-reference.txt), réglage « sons » : aucun (par défaut), discrets, normaux.
 * Un AudioTrack statique par son ; rejouer = rembobiner.
 */
final class Sons {
    static final int TAUX = 22050;
    private final Map<Chasse.Evenement, AudioTrack> pistes = new EnumMap<>(Chasse.Evenement.class);
    private boolean actif;

    Sons(boolean actif) {
        this.actif = actif;
        if (!actif) return;
        try {
            pistes.put(Chasse.Evenement.TIR, piste(balayage(1100, 700, 0.05, 0.07, true)));
            pistes.put(Chasse.Evenement.TOUCHE, piste(bruit(0.09, 0.18)));
            pistes.put(Chasse.Evenement.EXPLOSION, piste(bruit(0.45, 0.28)));
            pistes.put(Chasse.Evenement.BONUS, piste(notes(new double[]{660, 880, 1320}, 0.06, 0.16)));
            pistes.put(Chasse.Evenement.BLESSE, piste(balayage(440, 110, 0.28, 0.2, true)));
            pistes.put(Chasse.Evenement.BOUCLIER, piste(balayage(300, 260, 0.04, 0.09, false)));
            pistes.put(Chasse.Evenement.VAGUE, piste(notes(new double[]{523, 784}, 0.09, 0.14)));
            pistes.put(Chasse.Evenement.BOSS, piste(notes(new double[]{110, 98, 110, 98}, 0.12, 0.2)));
            pistes.put(Chasse.Evenement.BOSS_TOUCHE, piste(balayage(220, 180, 0.04, 0.12, true)));
            pistes.put(Chasse.Evenement.FIN, piste(notes(new double[]{523, 440, 349, 262}, 0.14, 0.18)));
        } catch (RuntimeException e) {
            this.actif = false; // pas de sortie audio : silence, noté pour le diagnostic
            Journal.son("chasse", "pistes non créées : " + e.getClass().getSimpleName());
        }
    }

    void jouer(Chasse.Evenement e) {
        if (!actif) return;
        AudioTrack t = pistes.get(e);
        if (t == null) return;
        try {
            String r = lancer(t);
            if (!r.isEmpty()) Journal.son("chasse " + e.name().toLowerCase(java.util.Locale.ROOT), r);
        } catch (IllegalStateException x) {
            Journal.son("chasse " + e.name().toLowerCase(java.util.Locale.ROOT), "piste libérée ou occupée");
        }
    }

    /** Rembobine et lance une piste statique ; "" si elle joue, sinon la raison (pour le diagnostic). */
    static String lancer(AudioTrack t) {
        if (t == null) return "son absent du catalogue";
        if (t.getState() != AudioTrack.STATE_INITIALIZED) return "piste non prête (état " + t.getState() + ")";
        if (t.getPlayState() == AudioTrack.PLAYSTATE_PLAYING) t.stop();
        int r = t.reloadStaticData();
        if (r != AudioTrack.SUCCESS) return "rembobinage refusé (" + r + ")";
        t.play();
        return t.getPlayState() == AudioTrack.PLAYSTATE_PLAYING ? "" : "lecture refusée par le système";
    }

    void liberer() {
        for (AudioTrack t : pistes.values()) t.release();
        pistes.clear();
    }

    private static AudioTrack piste(short[] pcm) {
        AudioTrack t = new AudioTrack.Builder()
                .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
                .setAudioFormat(new AudioFormat.Builder().setEncoding(AudioFormat.ENCODING_PCM_16BIT).setSampleRate(TAUX)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
                .setTransferMode(AudioTrack.MODE_STATIC)
                .setBufferSizeInBytes(pcm.length * 2)
                .build();
        t.write(pcm, 0, pcm.length);
        return t;
    }

    // Onde carrée (ou triangle) qui glisse d'une fréquence à l'autre, avec décroissance.
    static short[] balayage(double de, double a, double duree, double volume, boolean carre) {
        int n = (int) (TAUX * duree);
        short[] s = new short[n];
        double phase = 0;
        for (int i = 0; i < n; i++) {
            double f = de + (a - de) * i / n;
            phase += f / TAUX;
            double x = phase % 1, v = carre ? (x < 0.5 ? 1 : -1) : 4 * Math.abs(x - 0.5) - 1;
            s[i] = (short) (v * volume * (1 - i / (double) n) * Short.MAX_VALUE);
        }
        return s;
    }

    static short[] bruit(double duree, double volume) {
        int n = (int) (TAUX * duree);
        short[] s = new short[n];
        java.util.Random r = new java.util.Random(7);
        double v = 0;
        for (int i = 0; i < n; i++) {
            if (i % 3 == 0) v = r.nextDouble() * 2 - 1; // bruit « 8 bits » un peu grave
            double env = Math.pow(1 - i / (double) n, 2);
            s[i] = (short) (v * volume * env * Short.MAX_VALUE);
        }
        return s;
    }

    static short[] notes(double[] freqs, double duree, double volume) {
        int n = (int) (TAUX * duree);
        short[] s = new short[n * freqs.length];
        for (int k = 0; k < freqs.length; k++) {
            short[] u = balayage(freqs[k], freqs[k], duree, volume, true);
            System.arraycopy(u, 0, s, k * n, n);
        }
        return s;
    }

    // ---- Sons de Pilou (docs/SONS.md) ----

    static final String CARESSE = "caresse", MOT = "mot", AVENTURE = "aventure", CHOIX = "choix", ACHAT = "achat",
            PECHE = "peche", EXPEDITION = "expedition", CAMPAGNE = "campagne", PALIER = "palier", SUCCES = "succes";
    static final String[] NIVEAUX = {"aucun", "discrets", "normaux"};
    private static final int ATTAQUE_MS = 4, RELACHE_MS = 60, QUEUE_MS = 20, FONDU_MS = 8, FILTRE = 120, DISCRET = 3;

    static final class Note {
        final int debut, duree, f0, f1, volume;
        final String onde;

        Note(int debut, int duree, int f0, int f1, String onde, int volume) {
            this.debut = debut;
            this.duree = duree;
            this.f0 = f0;
            this.f1 = f1;
            this.onde = onde;
            this.volume = volume;
        }
    }

    static Map<String, List<Note>> lire(String texte) {
        Map<String, List<Note>> sons = new LinkedHashMap<>();
        for (String brute : texte.split("\n")) {
            String l = brute.trim();
            if (l.isEmpty() || l.startsWith("#")) continue;
            String[] p = l.split("\\|");
            if (p.length != 6) continue;
            for (int k = 0; k < p.length; k++) p[k] = p[k].trim();
            String[] f = p[3].split(">");
            Note n = new Note(Integer.parseInt(p[1]), Integer.parseInt(p[2]), Integer.parseInt(f[0]),
                    Integer.parseInt(f[f.length - 1]), p[4], Integer.parseInt(p[5]));
            List<Note> liste = sons.get(p[0]);
            if (liste == null) sons.put(p[0], liste = new ArrayList<>());
            liste.add(n);
        }
        return sons;
    }

    /** Échantillons 16 bits au réglage « normaux ». Tout en entiers, comme Sons.cs et sons.py (même ordre, mêmes décalages). */
    static short[] synthetiser(List<Note> notes) {
        int fin = 0;
        for (Note n : notes) fin = Math.max(fin, TAUX * n.debut / 1000 + TAUX * n.duree / 1000);
        fin += TAUX * QUEUE_MS / 1000;
        long[] acc = new long[fin];
        int a = TAUX * ATTAQUE_MS / 1000;
        for (Note note : notes) {
            int s0 = TAUX * note.debut / 1000, n = TAUX * note.duree / 1000;
            int r = Math.min(n / 2, TAUX * RELACHE_MS / 1000);
            long phase = 0;
            int lfsr = 1;
            for (int i = 0; i < n; i++) {
                long fm = ((long) note.f0 * 1000 * (n - i) + (long) note.f1 * 1000 * i) / n;
                long inc = fm * 4294967296L / (TAUX * 1000L);
                long avant = phase;
                phase = (phase + inc) & 0xFFFFFFFFL;
                int p = (int) (phase >> 16);
                long v;
                if (note.onde.equals("tri")) {
                    int t = p < 32768 ? p : 65535 - p;
                    v = ((t >> 11) * 2 - 15) * 2184L;
                } else if (note.onde.equals("puls")) {
                    v = p < 16384 ? 24000 : -8000;
                } else {
                    if (phase < avant) {
                        int b = (lfsr ^ (lfsr >> 1)) & 1;
                        lfsr = (lfsr >> 1) | (b << 14);
                    }
                    v = (lfsr & 1) != 0 ? 20000 : -20000;
                }
                long e = 4096;
                if (i < a) e = 4096L * i / a;
                if (i >= n - r) {
                    long k = n - i;
                    e = Math.min(e, 4096L * k * k / ((long) r * r));
                }
                e = e * (4096 - 1024L * i / n) / 4096;
                acc[s0 + i] += (v * e * note.volume * 10) >> 22;
            }
        }
        short[] sortie = new short[fin];
        long y1 = 0, y2 = 0;
        for (int i = 0; i < fin; i++) {
            long x = acc[i] << 8;
            y1 += ((x - y1) * FILTRE) >> 8;
            y2 += ((y1 - y2) * FILTRE) >> 8;
            sortie[i] = (short) Math.max(-32767, Math.min(32767, y2 >> 8));
        }
        int f = TAUX * FONDU_MS / 1000;
        for (int i = fin - f; i < fin; i++) {
            long g = ((long) (fin - 1 - i) << 16) / f;
            sortie[i] = (short) ((sortie[i] * g) >> 16);
        }
        return sortie;
    }

    /** « Discrets » : environ -14 dB, vraiment bas. */
    static short[] adoucir(short[] s) {
        short[] d = new short[s.length];
        for (int i = 0; i < s.length; i++) d[i] = (short) ((s[i] * DISCRET) >> 4);
        return d;
    }

    static String empreinte(short[] s) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] o = new byte[s.length * 2];
            for (int i = 0; i < s.length; i++) {
                o[i * 2] = (byte) s[i];
                o[i * 2 + 1] = (byte) (s[i] >> 8);
            }
            StringBuilder b = new StringBuilder();
            for (byte x : md.digest(o)) b.append(String.format("%02x", x));
            return b.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    /** Quand un son a le droit de partir : même règle que GardeSons sur le PC. */
    static final class Garde {
        static final long ESPACEMENT = 1200, MEME_SON = 4000;
        static final int SPONTANES_PAR_HEURE = 6;
        private long dernier = Long.MIN_VALUE / 2;
        private final Map<String, Long> parSon = new HashMap<>();
        private final ArrayDeque<Long> spontanes = new ArrayDeque<>();

        static boolean spontane(String id) {
            return id.equals(MOT) || id.equals(EXPEDITION) || id.equals(CAMPAGNE) || id.equals(PALIER) || id.equals(SUCCES);
        }

        synchronized boolean peut(String id, long t, String niveau, boolean cache, boolean saisie) {
            if (!(niveau.equals("discrets") || niveau.equals("normaux")) || cache) return false;
            boolean sp = spontane(id);
            if (sp && saisie) return false;
            if (t - dernier < ESPACEMENT) return false;
            Long d = parSon.get(id);
            if (d != null && t - d < MEME_SON) return false;
            while (!spontanes.isEmpty() && t - spontanes.peekFirst() >= 3_600_000) spontanes.pollFirst();
            if (sp && spontanes.size() >= SPONTANES_PAR_HEURE) return false;
            dernier = t;
            parSon.put(id, t);
            if (sp) spontanes.addLast(t);
            return true;
        }
    }

    private static final Garde GARDE = new Garde();
    private static final Map<String, AudioTrack> PILOU = new HashMap<>();
    private static Map<String, List<Note>> catalogue;

    static final String DEFAUT = "normaux";

    static String niveau(Context c) {
        return Prefs.de(c).getString("sons", DEFAUT);
    }

    /**
     * Pourquoi un son ne peut pas sortir maintenant ("" : rien ne l'en empêche). Un son qui répond à un geste du joueur
     * passe par le volume multimédia quel que soit le mode de sonnerie, comme dans n'importe quel jeu ; un son
     * spontané ({@link Garde#spontane}) respecte silencieux et vibreur. Toujours le silence pendant un appel ou une visio.
     */
    static String empechement(int mode, int sonnerie, int volume, boolean silenceTotal, boolean spontane) {
        if (mode != AudioManager.MODE_NORMAL) return "téléphone en appel ou en visio";
        if (spontane && sonnerie == AudioManager.RINGER_MODE_SILENT) return "téléphone en silencieux";
        if (spontane && sonnerie == AudioManager.RINGER_MODE_VIBRATE) return "téléphone en vibreur";
        if (silenceTotal) return "« Ne pas déranger » en silence total";
        if (volume <= 0) return "volume multimédia à zéro";
        return "";
    }

    static String empechement(Context c, boolean spontane) {
        AudioManager am = c.getSystemService(AudioManager.class);
        if (am == null) return "pas de sortie audio";
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        boolean total = nm != null && nm.getCurrentInterruptionFilter() == NotificationManager.INTERRUPTION_FILTER_NONE;
        return empechement(am.getMode(), am.getRingerMode(), am.getStreamVolume(AudioManager.STREAM_MUSIC), total, spontane);
    }

    /** Joue un son de Pilou si le réglage le permet (voir empechement) ; un silence imprévu est noté pour le diagnostic. */
    static void jouer(Context c, String id) {
        jouer(c, id, false);
    }

    /**
     * {@code essai} : le bouton « Essayer » des Réglages, qui passe la garde d'espacement et joue même au réglage
     * « Aucun » (au niveau normal). Renvoie "" si le son est parti, sinon la raison en clair.
     */
    static String jouer(Context c, String id, boolean essai) {
        String raison;
        try {
            String niveau = niveau(c);
            boolean permis = niveau.equals("discrets") || niveau.equals("normaux");
            if (!permis && !essai) return "réglage « Aucun »";
            raison = empechement(c, Garde.spontane(id));
            if (raison.isEmpty() && !essai && !GARDE.peut(id, android.os.SystemClock.uptimeMillis(), niveau, false, false))
                raison = Garde.spontane(id) ? "garde (espacement ou six par heure)" : "garde (trop près du précédent)";
            if (raison.isEmpty()) raison = lancer(pret(id, niveau.equals("discrets")));
        } catch (RuntimeException e) {
            raison = "erreur " + e.getClass().getSimpleName();
        }
        if (!raison.isEmpty()) Journal.son(id, raison);
        return raison;
    }

    private static synchronized AudioTrack pret(String id, boolean discret) {
        String cle = id + (discret ? "-discret" : "");
        AudioTrack t = PILOU.get(cle);
        if (t != null) return t;
        if (catalogue == null || catalogue.isEmpty()) catalogue = lire(ressource("/sons.txt"));
        List<Note> notes = catalogue.get(id);
        if (notes == null) return null;
        short[] s = synthetiser(notes);
        t = piste(discret ? adoucir(s) : s);
        PILOU.put(cle, t);
        return t;
    }

    static String ressource(String nom) {
        try (InputStream in = Sons.class.getResourceAsStream(nom)) {
            if (in == null) return "";
            ByteArrayOutputStream o = new ByteArrayOutputStream();
            byte[] b = new byte[4096];
            for (int k; (k = in.read(b)) > 0; ) o.write(b, 0, k);
            return new String(o.toByteArray(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            return "";
        }
    }
}
