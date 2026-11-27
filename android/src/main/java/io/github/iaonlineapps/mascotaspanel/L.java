package io.github.iaonlineapps.mascotaspanel;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.Locale;

/**
 * Idioma de la app: el que elijas en el panel (Cuenta → Idioma) o, si no, el del móvil.
 * L.t("texto en español", "text in English").
 */
final class L {
    static final String KEY = "lang";
    private static String lang;

    static void init(Context c) {
        SharedPreferences p = c.getSharedPreferences("mascotaspanel", Context.MODE_PRIVATE);
        String l = p.getString(KEY, null);
        lang = (l != null) ? l : ("es".equals(Locale.getDefault().getLanguage()) ? "es" : "en");
    }

    static void set(Context c, String l) {
        if (!"es".equals(l) && !"en".equals(l)) return;
        lang = l;
        c.getSharedPreferences("mascotaspanel", Context.MODE_PRIVATE).edit().putString(KEY, l).apply();
    }

    static boolean en() { return "en".equals(lang); }

    static String t(String es, String en) { return en() ? en : es; }
}
