package fr.pilou.compagnon;

import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioTrack;

import java.util.EnumMap;
import java.util.Map;

/**
 * Petits sons rétro synthétisés en code (ondes carrées et bruit) : aucun fichier, aucun droit d'auteur.
 * Un AudioTrack statique par son ; rejouer = rembobiner.
 */
final class Sons {
    private static final int TAUX = 22050;
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
            this.actif = false; // pas de sortie audio : silence
        }
    }

    void jouer(Chasse.Evenement e) {
        if (!actif) return;
        AudioTrack t = pistes.get(e);
        if (t == null) return;
        try {
            if (t.getPlayState() == AudioTrack.PLAYSTATE_PLAYING) t.stop();
            t.reloadStaticData();
            t.play();
        } catch (IllegalStateException ignore) {
            // piste libérée ou occupée : son perdu
        }
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
}
