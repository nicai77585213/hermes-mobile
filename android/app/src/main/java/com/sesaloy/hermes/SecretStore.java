package com.sesaloy.hermes;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import android.util.Log;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * 密钥安全存储：Android Keystore AES/GCM 加密后落盘 SharedPreferences。
 * 磁盘上只有密文，明文只在内存中短暂存在。用于替代明文保存 API 密钥。
 */
public class SecretStore {

    private static final String TAG = "HermesSecretStore";
    private static final String ANDROID_KEYSTORE = "AndroidKeyStore";
    private static final String KEY_ALIAS = "hermes_mobile_secret_key";
    private static final String PREFS_NAME = "hermes_secure_secrets";
    private static final String IV_SEPARATOR = ":";
    private static final int GCM_TAG_BITS = 128;

    private final SharedPreferences prefs;
    private final Object lock = new Object();

    public SecretStore(Context context) {
        this.prefs = context.getApplicationContext()
                .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    /** 加密并存储一个密钥/敏感值，返回是否成功。 */
    public boolean store(String key, String plaintext) {
        if (key == null || plaintext == null) {
            return false;
        }
        synchronized (lock) {
            try {
                String encrypted = encrypt(plaintext);
                if (encrypted == null) {
                    return false;
                }
                prefs.edit().putString(key, encrypted).apply();
                return true;
            } catch (Exception e) {
                Log.w(TAG, "store failed", e);
                return false;
            }
        }
    }

    /** 读取并解密，返回明文；不存在或解密失败返回 null。 */
    public String load(String key) {
        if (key == null) {
            return null;
        }
        synchronized (lock) {
            String encrypted = prefs.getString(key, null);
            if (encrypted == null || encrypted.isEmpty()) {
                return null;
            }
            try {
                return decrypt(encrypted);
            } catch (Exception e) {
                Log.w(TAG, "load failed", e);
                return null;
            }
        }
    }

    /** 判断某个密钥是否存在。 */
    public boolean has(String key) {
        return key != null && prefs.contains(key);
    }

    /** 删除某个密钥。 */
    public void delete(String key) {
        if (key != null) {
            prefs.edit().remove(key).apply();
        }
    }

    private SecretKey getOrCreateKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance(ANDROID_KEYSTORE);
        keyStore.load(null);
        KeyStore.SecretKeyEntry entry =
                (KeyStore.SecretKeyEntry) keyStore.getEntry(KEY_ALIAS, null);
        if (entry != null) {
            return entry.getSecretKey();
        }
        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE);
        generator.init(new KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build());
        return generator.generateKey();
    }

    private String encrypt(String plaintext) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey());
        byte[] iv = cipher.getIV();
        byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));
        return Base64.encodeToString(iv, Base64.NO_WRAP)
                + IV_SEPARATOR
                + Base64.encodeToString(ciphertext, Base64.NO_WRAP);
    }

    private String decrypt(String stored) throws Exception {
        String[] parts = stored.split(IV_SEPARATOR, 2);
        if (parts.length != 2) {
            return null;
        }
        byte[] iv = Base64.decode(parts[0], Base64.NO_WRAP);
        byte[] ciphertext = Base64.decode(parts[1], Base64.NO_WRAP);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), new GCMParameterSpec(GCM_TAG_BITS, iv));
        byte[] plaintext = cipher.doFinal(ciphertext);
        return new String(plaintext, StandardCharsets.UTF_8);
    }
}
