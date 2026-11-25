package fr.pilou.compagnon;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.provider.Settings;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Écoute le relais ntfy (flux JSON, une ligne par message), déchiffre l'état publié par le PC et le
 * montre aux trois niveaux : notification permanente, widget, Pilou flottant.
 */
public final class Veille extends Service {
    static final String CANAL_STATUT = "statut", CANAL_ATTENTE = "attente", CANAL_FIN = "fin";
    private static final int NOTIF_STATUT = 1;

    private final Handler principal = new Handler(Looper.getMainLooper());
    private final Set<String> prevenus = new HashSet<>();
    private volatile boolean actif;
    private volatile HttpURLConnection connexion;
    private Thread ecoute;
    private Etat etat = Etat.vide();
    private Bulle bulle;
    private int image;
    private String codeEcoute = "";

    public static void demarrer(Context c) {
        if (!Chiffre.valide(Prefs.code(c))) return;
        c.startForegroundService(new Intent(c, Veille.class));
    }

    public static void arreter(Context c) {
        c.stopService(new Intent(c, Veille.class));
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        Journal.installer(this);
        NotificationManager nm = getSystemService(NotificationManager.class);
        NotificationChannel statut = new NotificationChannel(CANAL_STATUT, "Statut des sessions", NotificationManager.IMPORTANCE_LOW);
        statut.setShowBadge(false);
        nm.createNotificationChannel(statut);
        nm.createNotificationChannel(new NotificationChannel(CANAL_ATTENTE, "Une IA t'attend", NotificationManager.IMPORTANCE_HIGH));
        nm.createNotificationChannel(new NotificationChannel(CANAL_FIN, "Une session a fini", NotificationManager.IMPORTANCE_DEFAULT));
        etat = Prefs.etat(this);
        // Les alertes déjà affichées avant un redémarrage ne repartent pas.
        for (Etat.Session s : etat.sessions) prevenus.add(s.id + "|" + s.etat + "|" + s.depuis);
        Notification n = statut(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT >= 34) startForeground(NOTIF_STATUT, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        else startForeground(NOTIF_STATUT, n);
        principal.postDelayed(this::battre, 30_000);
        // Mise à jour de l'app : une minute après le démarrage, puis une fois par jour (MiseAJour décide).
        principal.postDelayed(this::verifierMise, 60_000);
        principal.postDelayed(this::envoyerGains, 20_000);
    }

    private void verifierMise() {
        new Thread(() -> MiseAJour.peutEtre(this), "pilou-maj").start();
        principal.postDelayed(this::verifierMise, 3600_000L);
    }

    // Gains de l'atelier vers le PC : toutes les minutes, ce qui attend part (chiffré).
    private void envoyerGains() {
        new Thread(() -> Gains.envoyer(this), "pilou-gains").start();
        principal.postDelayed(this::envoyerGains, 60_000);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? null : intent.getAction();
        if (ACTION_CACHER.equals(action)) Prefs.de(this).edit().putLong("cacheJusque", System.currentTimeMillis() + 10 * 60_000L).apply();
        else if (ACTION_MONTRER.equals(action)) {
            Prefs.de(this).edit().remove("cacheJusque").apply();
            ramener = true;
        }
        String code = Prefs.code(this);
        if (!Chiffre.valide(code)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (!code.equals(codeEcoute)) {
            codeEcoute = code;
            couper();
            actif = true;
            ecoute = new Thread(this::ecouter, "pilou-relais");
            ecoute.start();
        }
        reglerBulle();
        afficher();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        couper();
        principal.removeCallbacksAndMessages(null);
        if (bulle != null) bulle.cacher();
        super.onDestroy();
    }

    private void couper() {
        actif = false;
        HttpURLConnection c = connexion;
        if (c != null) c.disconnect();
        if (ecoute != null) ecoute.interrupt();
    }

    static final String ACTION_CACHER = "fr.pilou.compagnon.CACHER", ACTION_MONTRER = "fr.pilou.compagnon.MONTRER";

    private boolean ramener;

    private boolean cache() {
        return cache(this);
    }

    /** Pilou flottant caché (10 min) ? */
    static boolean cache(android.content.Context c) {
        return System.currentTimeMillis() < Prefs.de(c).getLong("cacheJusque", 0);
    }

    /** Cacher Pilou 10 min, ou le montrer tout de suite (depuis l'app). */
    static void cacher(android.content.Context c, boolean oui) {
        if (!Chiffre.valide(Prefs.code(c))) {
            if (oui) Prefs.de(c).edit().putLong("cacheJusque", System.currentTimeMillis() + 10 * 60_000L).apply();
            else Prefs.de(c).edit().remove("cacheJusque").apply();
            return;
        }
        c.startForegroundService(new Intent(c, Veille.class).setAction(oui ? ACTION_CACHER : ACTION_MONTRER));
    }

    private void reglerBulle() {
        boolean veut = Prefs.bulle(this) && Settings.canDrawOverlays(this) && !cache();
        if (veut && bulle != null) bulle.reglerTaille();
        if (veut && bulle == null) {
            bulle = new Bulle(this);
            bulle.montrer();
        }
        if (veut && ramener) {
            ramener = false;
            bulle.ramener();
        } else if (!veut && bulle != null) {
            bulle.cacher();
            bulle = null;
        }
    }

    // ---- Relais

    private void ecouter() {
        long attente = 2000;
        while (actif) {
            try {
                String code = codeEcoute;
                String depuis = Prefs.de(this).getString("dernierId", "");
                URL url = new URL(Prefs.relais(this).replaceAll("/+$", "") + "/" + Chiffre.sujet(code) + "/json?since="
                        + (depuis.isEmpty() ? "latest" : depuis));
                HttpURLConnection c = (HttpURLConnection) url.openConnection();
                connexion = c;
                c.setConnectTimeout(15_000);
                c.setReadTimeout(120_000); // ntfy envoie un « keepalive » toutes les 45 s
                c.setRequestProperty("User-Agent", "pilou-android");
                try (BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8))) {
                    attente = 2000;
                    String ligne;
                    while (actif && (ligne = r.readLine()) != null) {
                        if (ligne.isEmpty()) continue;
                        JSONObject ev = new JSONObject(ligne);
                        if (!"message".equals(ev.optString("event"))) continue;
                        String id = ev.optString("id");
                        String message = ev.optString("message");
                        // Message trop long pour ntfy (> 4 096 octets) : il arrive en pièce jointe, à télécharger.
                        JSONObject pj = ev.optJSONObject("attachment");
                        if (pj != null && !pj.optString("url").isEmpty()) {
                            try {
                                message = MiseAJour.telecharger(pj.optString("url"));
                            } catch (Exception perdu) {
                                // pièce jointe expirée : le prochain message suffira
                            }
                        }
                        long recu = System.currentTimeMillis();
                        try {
                            String json = completer(Chiffre.dechiffrer(code, message));
                            Etat e = Etat.lire(json, recu);
                            Prefs.de(this).edit().putString("etat", json).putLong("recu", recu).putString("dernierId", id).apply();
                            principal.post(() -> recevoir(e));
                        } catch (Exception illisible) {
                            // pas pour nous (autre code, message altéré) : ignoré
                            Prefs.de(this).edit().putString("dernierId", id).apply();
                        }
                    }
                } finally {
                    c.disconnect();
                }
            } catch (Exception e) {
                // hors ligne, relais indisponible : on réessaie, de plus en plus lentement
            }
            if (!actif) break;
            try {
                Thread.sleep(attente);
            } catch (InterruptedException e) {
                break;
            }
            attente = Math.min(60_000, attente * 2);
        }
    }

    // Un message allégé (sans carnet ni recettes) garde les listes du message précédent.
    private String completer(String json) {
        try {
            JSONObject n = new JSONObject(json);
            String avant = Prefs.de(this).getString("etat", "");
            if (avant.isEmpty()) return json;
            JSONObject a = new JSONObject(avant);
            boolean change = false;
            for (String cle : new String[]{"carnet", "plats"})
                if (!n.has(cle) && a.has(cle)) {
                    n.put(cle, a.get(cle));
                    change = true;
                }
            return change ? n.toString() : json;
        } catch (org.json.JSONException e) {
            return json;
        }
    }

    private void recevoir(Etat e) {
        etat = e;
        Gains.accuser(this, e);
        afficher();
        prevenir();
    }

    // Toutes les 30 s : durées à jour, « le PC dort » s'il se tait.
    private void battre() {
        reglerBulle();
        afficher();
        principal.postDelayed(this::battre, 30_000);
    }

    private void afficher() {
        long maintenant = System.currentTimeMillis();
        image++;
        getSystemService(NotificationManager.class).notify(NOTIF_STATUT, statut(maintenant));
        Widget.maj(this, etat, maintenant);
        if (bulle != null) bulle.maj(etat, maintenant);
    }

    // ---- Niveau 1 : notification permanente

    private PendingIntent ouvrir() {
        return PendingIntent.getActivity(this, 0, new Intent(this, Principale.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    private Notification statut(long maintenant) {
        List<Etat.Ligne> lignes = etat.lignes(maintenant, image);
        Notification.InboxStyle style = new Notification.InboxStyle();
        for (int i = 0; i < Math.min(6, lignes.size()); i++) style.addLine(lignes.get(i).toString());
        String titre = etat.resume(maintenant);
        Notification.Builder b = new Notification.Builder(this, CANAL_STATUT)
                .setSmallIcon(R.drawable.ic_stat_pilou)
                .setLargeIcon(Dessin.image(etat.expression(maintenant), etat.couleur, etat.accessoire, 4))
                .setContentTitle(titre)
                .setContentText(lignes.isEmpty() ? etat.nom + " · niveau " + etat.niveau : lignes.get(0).toString())
                .setStyle(style)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .setShowWhen(false)
                .setContentIntent(ouvrir());
        // Pilou flottant : le cacher 10 min ou le rappeler, depuis la notification.
        if (Prefs.bulle(this) && Settings.canDrawOverlays(this)) {
            boolean cache = cache();
            Intent i = new Intent(this, Veille.class).setAction(cache ? ACTION_MONTRER : ACTION_CACHER);
            b.addAction(new Notification.Action.Builder(null, cache ? "Montrer Pilou" : "Cacher Pilou 10 min",
                    PendingIntent.getForegroundService(this, cache ? 11 : 10, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT)).build());
            if (cache) b.setSubText("Pilou caché");
            else b.addAction(new Notification.Action.Builder(null, "Ramener Pilou",
                    PendingIntent.getForegroundService(this, 12, new Intent(this, Veille.class).setAction(ACTION_MONTRER),
                            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT)).build());
        }
        return b.build();
    }

    // Une IA attend, ou une session vient de finir : une alerte, une fois.
    private void prevenir() {
        long maintenant = System.currentTimeMillis();
        NotificationManager nm = getSystemService(NotificationManager.class);
        for (Etat.Session s : etat.sessions) {
            String cle = s.id + "|" + s.etat + "|" + s.depuis;
            if (prevenus.contains(cle)) continue;
            String canal, texte;
            if (s.attend() && Prefs.alerteAttente(this)) {
                canal = CANAL_ATTENTE;
                texte = s.etat.equals("question") ? "te pose une question" : "attend ton autorisation";
                if (bulle != null) bulle.alerter();
            } else if ((s.etat.equals("fini") || s.etat.equals("erreur")) && maintenant - s.depuis < 5 * 60_000L && Prefs.alerteFin(this)) {
                canal = CANAL_FIN;
                texte = s.etat.equals("fini") ? "a fini" : "s'est arrêtée sur une erreur";
            } else {
                prevenus.add(cle);
                continue;
            }
            prevenus.add(cle);
            nm.notify(cle.hashCode(), new Notification.Builder(this, canal)
                    .setSmallIcon(R.drawable.ic_stat_pilou)
                    .setContentTitle(s.nom())
                    .setContentText(texte)
                    .setAutoCancel(true)
                    .setContentIntent(ouvrir())
                    .build());
        }
    }
}
