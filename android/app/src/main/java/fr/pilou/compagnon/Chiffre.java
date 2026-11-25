package fr.pilou.compagnon;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Base64;
import java.util.Locale;

import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/**
 * Même calcul que Telephone.cs côté PC : le code d'appairage donne le sujet ntfy et la clé AES-256-GCM.
 * Message : base64(nonce 12 octets ‖ chiffré ‖ étiquette 16 octets).
 */
public final class Chiffre {
    static final String ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";

    private Chiffre() {
    }

    public static String normaliser(String code) {
        StringBuilder b = new StringBuilder();
        for (char c : code.toUpperCase(Locale.ROOT).toCharArray())
            if (ALPHABET.indexOf(c) >= 0) b.append(c);
        return b.toString();
    }

    public static boolean valide(String code) {
        return code != null && normaliser(code).length() == 16;
    }

    public static String formater(String code) {
        String n = normaliser(code);
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < n.length(); i++) {
            if (i > 0 && i % 4 == 0) b.append('-');
            b.append(n.charAt(i));
        }
        return b.toString();
    }

    static byte[] hmac(String code, String usage) throws GeneralSecurityException {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(normaliser(code).getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return mac.doFinal(usage.getBytes(StandardCharsets.UTF_8));
    }

    public static String sujet(String code) throws GeneralSecurityException {
        byte[] h = hmac(code, "pilou-sujet-v1");
        StringBuilder b = new StringBuilder("pilou-");
        for (int i = 0; i < 12; i++) b.append(String.format(Locale.ROOT, "%02x", h[i]));
        return b.toString();
    }

    /** Deuxième sujet, tiré du même code : le téléphone y publie ses gains, le PC y lit. */
    public static String sujetRetour(String code) throws GeneralSecurityException {
        byte[] h = hmac(code, "pilou-retour-v1");
        StringBuilder b = new StringBuilder("pilou-");
        for (int i = 0; i < 12; i++) b.append(String.format(Locale.ROOT, "%02x", h[i]));
        return b.toString();
    }

    /** Sujet du groupe d'appareils (les PC y publient leur compteur d'XP) : même calcul que Groupe.Sujet côté PC. */
    public static String sujetGroupe(String code) throws GeneralSecurityException {
        byte[] h = hmac(code, "pilou-groupe-v1");
        StringBuilder b = new StringBuilder("pilou-");
        for (int i = 0; i < 12; i++) b.append(String.format(Locale.ROOT, "%02x", h[i]));
        return b.toString();
    }

    public static String chiffrer(String code, String texte) throws GeneralSecurityException {
        byte[] nonce = new byte[12];
        new java.security.SecureRandom().nextBytes(nonce);
        return chiffrer(code, texte, nonce);
    }

    /** base64(nonce ‖ chiffré ‖ étiquette), comme Telephone.Chiffrer côté PC. */
    public static String chiffrer(String code, String texte, byte[] nonce) throws GeneralSecurityException {
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(hmac(code, "pilou-cle-v1"), "AES"), new GCMParameterSpec(128, nonce));
        byte[] chiffre = c.doFinal(texte.getBytes(StandardCharsets.UTF_8));
        byte[] tout = new byte[12 + chiffre.length];
        System.arraycopy(nonce, 0, tout, 0, 12);
        System.arraycopy(chiffre, 0, tout, 12, chiffre.length);
        return Base64.getEncoder().encodeToString(tout);
    }

    public static String dechiffrer(String code, String message) throws GeneralSecurityException {
        byte[] tout = Base64.getDecoder().decode(message.trim());
        if (tout.length < 28) throw new GeneralSecurityException("message trop court");
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.DECRYPT_MODE, new SecretKeySpec(hmac(code, "pilou-cle-v1"), "AES"), new GCMParameterSpec(128, tout, 0, 12));
        return new String(c.doFinal(tout, 12, tout.length - 12), StandardCharsets.UTF_8);
    }
}
