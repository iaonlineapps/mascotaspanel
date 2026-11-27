package io.github.iaonlineapps.mascotaspanel;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.text.SpannableStringBuilder;
import android.text.Spanned;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.graphics.Typeface;
import android.util.TypedValue;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Version de la app, lista de novedades (res/raw/novedades.md) y aviso de versiones nuevas.
 * Las versiones de la app se publican en las Releases del repo publico con etiquetas
 * "android-v1.2" (las del servidor usan "v1.2.3", asi que no se mezclan).
 */
final class Novedades {

    static final String RELEASES_PAGE = "https://github.com/iaonlineapps/mascotaspanel#app-para-android";
    private static final String RELEASES_API = "https://api.github.com/repos/iaonlineapps/mascotaspanel/releases?per_page=30";
    private static final String TAG_PREFIX = "android-v";
    private static final String KEY_LAST_CHECK = "update_last_check";
    private static final String KEY_SKIPPED = "update_skipped";
    private static final String KEY_SEEN_VERSION = "novedades_seen_version";
    private static final long CHECK_EVERY_MS = 12L * 60 * 60 * 1000;

    private Novedades() { }

    static String version(Activity a) {
        try {
            return a.getPackageManager().getPackageInfo(a.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "?";
        }
    }

    // ------------------------------------------------------------------ Novedades

    /** Muestra las novedades una vez, la primera vez que se abre una version nueva (no en la primera instalacion). */
    static void showIfUpdated(Activity a, SharedPreferences prefs, boolean firstInstall) {
        String v = version(a);
        String seen = prefs.getString(KEY_SEEN_VERSION, null);
        prefs.edit().putString(KEY_SEEN_VERSION, v).apply();
        if (!firstInstall && !v.equals(seen)) show(a, prefs, L.t("Novedades de la versión ", "What's new in version ") + v);
    }

    static void show(final Activity a, final SharedPreferences prefs, String title) {
        TextView t = new TextView(a);
        t.setText(format(readChangelog(a)));
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        t.setTextColor(0xFF1F1F1F);
        t.setTextIsSelectable(true);
        int p = (int) (20 * a.getResources().getDisplayMetrics().density);
        t.setPadding(p, p / 2, p, 0);
        ScrollView sv = new ScrollView(a);
        sv.addView(t);
        new AlertDialog.Builder(a)
                .setTitle(title != null ? title : "MascotasPanel " + version(a))
                .setView(sv)
                .setPositiveButton(L.t("Cerrar", "Close"), null)
                .setNeutralButton(L.t("Buscar actualizaciones", "Check for updates"), new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int w) { check(a, prefs, true); }
                })
                .show();
    }

    private static String readChangelog(Activity a) {
        try {
            InputStream in = a.getResources().openRawResource(L.en() ? R.raw.novedades_en : R.raw.novedades);
            String s = readAll(in);
            in.close();
            return s;
        } catch (Exception e) {
            return "";
        }
    }

    /** Markdown sencillo -> texto con titulos en negrita. */
    static CharSequence format(String md) {
        SpannableStringBuilder b = new SpannableStringBuilder();
        for (String line : md.split("\n")) {
            String l = line.trim();
            if (l.startsWith(">")) l = l.substring(1).trim();
            if (l.startsWith("# ")) continue; // Titulo del archivo
            if (l.startsWith("<!--")) continue;
            if (l.startsWith("## ")) {
                if (b.length() > 0) b.append("\n");
                int s = b.length();
                b.append(l.substring(3).replace("**", ""));
                b.setSpan(new StyleSpan(Typeface.BOLD), s, b.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                b.setSpan(new RelativeSizeSpan(1.1f), s, b.length(), Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
                b.append("\n");
            } else if (l.startsWith("- ") || l.startsWith("* ")) {
                b.append("•  ").append(l.substring(2).replace("**", "").replace("`", "")).append("\n");
            } else if (!l.isEmpty()) {
                b.append(l.replace("**", "").replace("`", "")).append("\n");
            }
        }
        return b;
    }

    // ------------------------------------------------------------------ Actualizaciones

    /** Comprueba en GitHub si hay una version nueva. manual=true: avisa tambien si no la hay. */
    static void check(final Activity a, final SharedPreferences prefs, final boolean manual) {
        long now = System.currentTimeMillis();
        if (!manual && now - prefs.getLong(KEY_LAST_CHECK, 0) < CHECK_EVERY_MS) return;
        prefs.edit().putLong(KEY_LAST_CHECK, now).apply();
        if (manual) Toast.makeText(a, L.t("Buscando actualizaciones…", "Checking for updates…"), Toast.LENGTH_SHORT).show();
        final String current = version(a);
        final Handler main = new Handler(Looper.getMainLooper());
        new Thread(new Runnable() { @Override public void run() {
            Release r = null;
            boolean failed = false;
            try {
                r = latest();
            } catch (Exception e) {
                failed = true;
            }
            final Release fr = r;
            final boolean ff = failed;
            main.post(new Runnable() { @Override public void run() {
                if (a.isFinishing()) return;
                if (fr != null && compare(fr.version, current) > 0) {
                    if (!manual && fr.version.equals(prefs.getString(KEY_SKIPPED, null))) return;
                    offer(a, prefs, fr);
                } else if (manual) {
                    Toast.makeText(a, ff ? L.t("No se ha podido comprobar. ¿Tienes Internet?", "Could not check. Are you online?")
                            : L.t("Ya tienes la última versión (", "You already have the latest version (") + current + ")", Toast.LENGTH_LONG).show();
                }
            } });
        } }).start();
    }

    private static void offer(final Activity a, final SharedPreferences prefs, final Release r) {
        String msg = L.en() ? "You have " + version(a) + ". Version " + r.version + " is now available."
                : "Tienes la " + version(a) + ". Ya está disponible la " + r.version + ".";
        if (r.notes != null && !r.notes.trim().isEmpty()) msg += "\n\n" + format(r.notes);
        msg += L.t("\n\nAl descargarla, ábrela y toca Instalar: se instala encima y no pierdes nada.", "\n\nOnce downloaded, open it and tap Install: it installs over the old one and you lose nothing.");
        new AlertDialog.Builder(a)
                .setTitle(L.t("Hay una versión nueva", "A new version is available"))
                .setMessage(msg)
                .setPositiveButton(L.t("Descargar", "Download"), new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int w) {
                        open(a, r.apkUrl != null ? r.apkUrl : r.pageUrl);
                    }
                })
                .setNegativeButton(L.t("Más tarde", "Later"), null)
                .setNeutralButton(L.t("Saltar esta versión", "Skip this version"), new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int w) {
                        prefs.edit().putString(KEY_SKIPPED, r.version).apply();
                    }
                })
                .show();
    }

    static void open(Activity a, String url) {
        try {
            a.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (ActivityNotFoundException e) {
            Toast.makeText(a, L.t("No hay navegador para abrir ", "No browser to open ") + url, Toast.LENGTH_LONG).show();
        }
    }

    static final class Release {
        String version, notes, apkUrl, pageUrl;
    }

    /** Si no hay Releases en GitHub, la versión nueva se anuncia en android/dist/version.json del repo público. */
    private static final String RAW_VERSION = "https://raw.githubusercontent.com/iaonlineapps/mascotaspanel/main/android/dist/version.json";

    private static Release latest() throws Exception {
        Release r = null;
        try { r = fromReleases(); } catch (Exception ignored) { }
        Release raw = null;
        try { raw = fromRaw(); } catch (Exception e) { if (r == null) throw e; }
        if (raw != null && (r == null || compare(raw.version, r.version) > 0)) r = raw;
        return r;
    }

    private static Release fromRaw() throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(RAW_VERSION).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(10000);
        try {
            if (c.getResponseCode() != 200) throw new Exception("HTTP " + c.getResponseCode());
            JSONObject o = new JSONObject(readAll(c.getInputStream()));
            Release r = new Release();
            r.version = o.optString("version", "0");
            r.notes = o.optString(L.en() ? "notes_en" : "notes", "");
            r.apkUrl = o.optString("apk", "");
            r.pageUrl = o.optString("page", RELEASES_PAGE);
            return r;
        } finally {
            c.disconnect();
        }
    }

    private static Release fromReleases() throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(RELEASES_API).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(10000);
        c.setRequestProperty("Accept", "application/vnd.github+json");
        try {
            if (c.getResponseCode() != 200) throw new Exception("HTTP " + c.getResponseCode());
            JSONArray arr = new JSONArray(readAll(c.getInputStream()));
            Release best = null;
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                String tag = o.optString("tag_name", "");
                if (o.optBoolean("draft") || o.optBoolean("prerelease") || !tag.startsWith(TAG_PREFIX)) continue;
                Release r = new Release();
                r.version = tag.substring(TAG_PREFIX.length());
                r.notes = o.optString("body", "");
                r.pageUrl = o.optString("html_url", RELEASES_PAGE);
                JSONArray assets = o.optJSONArray("assets");
                if (assets != null) {
                    for (int j = 0; j < assets.length(); j++) {
                        String u = assets.getJSONObject(j).optString("browser_download_url", "");
                        if (u.endsWith(".apk")) { r.apkUrl = u; break; }
                    }
                }
                if (best == null || compare(r.version, best.version) > 0) best = r;
            }
            return best;
        } finally {
            c.disconnect();
        }
    }

    /** Compara "1.10" con "1.9" por numeros. */
    static int compare(String x, String y) {
        String[] a = x.split("[^0-9]+"), b = y.split("[^0-9]+");
        for (int i = 0; i < Math.max(a.length, b.length); i++) {
            int p = i < a.length && !a[i].isEmpty() ? Integer.parseInt(a[i]) : 0;
            int q = i < b.length && !b[i].isEmpty() ? Integer.parseInt(b[i]) : 0;
            if (p != q) return p < q ? -1 : 1;
        }
        return 0;
    }

    private static String readAll(InputStream in) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        return out.toString("UTF-8");
    }
}
