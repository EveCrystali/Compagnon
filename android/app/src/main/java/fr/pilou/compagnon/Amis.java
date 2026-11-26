package fr.pilou.compagnon;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.util.Locale;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * Amis de Pilou : mêmes dérivations qu'Amis.cs côté PC (vecteur commun dans AmisTest et AmisTests.cs).
 * Le téléphone n'échange pas encore avec les amis (il montre ce que le PC lui en dit) ; ces calculs sont là
 * pour qu'il puisse un jour recevoir une visite sans réinventer le protocole.
 */
public final class Amis {
    static final int LONGUEUR = 12;

    private Amis() {
    }

    /** « pilou-7f3k 9qxa-m2ht » → « 7F3K9QXAM2HT » (le préfixe PILOU est retiré avant le filtre). */
    public static String normaliser(String code) {
        String s = code == null ? "" : code.toUpperCase(Locale.ROOT).trim();
        if (s.startsWith("PILOU")) s = s.substring(5);
        return Chiffre.normaliser(s);
    }

    public static boolean valide(String code) {
        return normaliser(code).length() == LONGUEUR;
    }

    static byte[] hmac(byte[] cle, String usage) throws GeneralSecurityException {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(cle, "HmacSHA256"));
        return mac.doFinal(usage.getBytes(StandardCharsets.UTF_8));
    }

    static String hex(byte[] h, int n) {
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < n; i++) b.append(String.format(Locale.ROOT, "%02x", h[i]));
        return b.toString();
    }

    /** Boîte d'un code : où l'on dépose une demande d'ami. */
    public static String sujetBoite(String code) throws GeneralSecurityException {
        return "pilou-" + hex(hmac(normaliser(code).getBytes(StandardCharsets.UTF_8), "pilou-ami-boite-v1"), 12);
    }

    public static byte[] cleBoite(String code) throws GeneralSecurityException {
        return hmac(normaliser(code).getBytes(StandardCharsets.UTF_8), "pilou-ami-cle-v1");
    }

    private static String lien(String codeA, String codeB) {
        String a = normaliser(codeA), b = normaliser(codeB);
        return a.compareTo(b) <= 0 ? a + "|" + b : b + "|" + a;
    }

    /** Sujet de la paire, à partir du secret ECDH P-256 (coordonnée x, 32 octets). */
    public static String sujetPaire(byte[] secret, String codeA, String codeB) throws GeneralSecurityException {
        return "pilou-" + hex(hmac(secret, "pilou-paire-sujet-v1|" + lien(codeA, codeB)), 12);
    }

    public static byte[] clePaire(byte[] secret, String codeA, String codeB) throws GeneralSecurityException {
        return hmac(secret, "pilou-paire-cle-v1|" + lien(codeA, codeB));
    }

    /** Code ami = empreinte de la clé publique (SubjectPublicKeyInfo) : un octet du SHA-256 → un signe. */
    public static String empreinte(byte[] publique) throws GeneralSecurityException {
        byte[] h = MessageDigest.getInstance("SHA-256").digest(publique);
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < LONGUEUR; i++) b.append(Chiffre.ALPHABET.charAt((h[i] & 0xff) % Chiffre.ALPHABET.length()));
        return b.toString();
    }
}
