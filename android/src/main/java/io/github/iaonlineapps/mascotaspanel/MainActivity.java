package io.github.iaonlineapps.mascotaspanel;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentValues;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * App de MascotasPanel: el panel de tu propio servidor dentro de una app.
 * Se guardan dos direcciones: la principal (normalmente tu dominio con https) y,
 * si quieres, la de casa (IP de la wifi). Si una no responde, se prueba la otra sola.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "mascotaspanel";
    private static final String KEY_URL = "server_url";
    private static final String KEY_ALT = "server_alt";
    private static final String ACTION_CHANGE_SERVER = "io.github.iaonlineapps.mascotaspanel.CHANGE_SERVER";
    private static final String ACTION_NOVEDADES = "io.github.iaonlineapps.mascotaspanel.NOVEDADES";
    private static final String INSTALL_URL = "https://github.com/iaonlineapps/mascotaspanel#2-instalar";
    private static final int REQ_FILES = 1;
    private static final int REQ_STORAGE = 2;
    private static final int REQ_CAMERA = 3;
    private static final int REQ_GEO = 4;
    private static final int RED = 0xFFEA580C;
    private static final int INK = 0xFF111111;
    private static final int GREY = 0xFF6B6B6B;

    private SharedPreferences prefs;
    private FrameLayout root;
    private WebView web;
    private ProgressBar progress;
    private ValueCallback<Uri[]> fileCallback;
    private String base;            // direccion que se esta usando ahora
    private boolean triedOther;     // ya se probo la otra direccion tras un fallo
    private boolean errorShown;
    private String[] pendingDownload;
    private Uri photoUri;
    private GeolocationPermissions.Callback geoCb;
    private String geoOrigin;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        L.init(this);
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);
        setContentView(root);

        String url = prefs.getString(KEY_URL, null);
        if (url == null || isAction(getIntent(), ACTION_CHANGE_SERVER)) {
            showSetup(null);
        } else {
            showWeb(url, state);
        }
        if (state == null) Novedades.showIfUpdated(this, prefs, url == null);
        if (isAction(getIntent(), ACTION_NOVEDADES)) Novedades.show(this, prefs, null);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (isAction(intent, ACTION_CHANGE_SERVER)) showSetup(null);
        else if (isAction(intent, ACTION_NOVEDADES)) Novedades.show(this, prefs, null);
    }

    private static boolean isAction(Intent i, String action) {
        return i != null && action.equals(i.getAction());
    }

    // ------------------------------------------------------------------ Pantalla de conexion

    private void showSetup(String message) {
        if (web != null) {
            web.destroy();
            web = null;
        }
        root.removeAllViews();

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_HORIZONTAL);
        box.setPadding(dp(28), dp(44), dp(28), dp(28));
        scroll.addView(box);

        android.widget.ImageView logo = new android.widget.ImageView(this);
        logo.setImageResource(R.mipmap.ic_launcher);
        box.addView(logo, new LinearLayout.LayoutParams(dp(84), dp(84)));

        TextView title = new TextView(this);
        title.setText("MascotasPanel");
        title.setTextSize(30);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(INK);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(10), 0, dp(4));
        box.addView(title);

        TextView info = text(L.t("Conecta la app con tu servidor MascotasPanel. Escribe la misma dirección que usas en el navegador.", "Connect the app to your MascotasPanel server. Type the same address you use in the browser."), 15, 0xFF333333);
        info.setPadding(0, dp(4), 0, dp(16));
        box.addView(info);

        TextView need = text(L.t("Importante: necesitas tu propio servidor MascotasPanel ya instalado ", "Important: you need your own MascotasPanel server already installed ")
                + L.t("(en una Raspberry Pi o un ordenador con Linux y Docker). Sin servidor la app no funciona.\n", "(on a Raspberry Pi or a Linux computer with Docker). Without a server the app does not work.\n")
                + L.t("¿Aún no lo tienes? Toca aquí para ver cómo instalarlo.", "Don't have one yet? Tap here to see how to install it."), 14, 0xFF7A1F00);
        need.setPadding(dp(14), dp(12), dp(14), dp(12));
        GradientDrawable nbg = new GradientDrawable();
        nbg.setColor(0xFFFFF1F2);
        nbg.setCornerRadius(dp(10));
        need.setBackground(nbg);
        need.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) {
            Novedades.open(MainActivity.this, INSTALL_URL);
        } });
        LinearLayout.LayoutParams nlp = matchWrap();
        nlp.setMargins(0, 0, 0, dp(18));
        box.addView(need, nlp);

        box.addView(label(L.t("Dirección de tu servidor", "Your server address")));
        box.addView(text(L.t("Lo normal es tu dominio, que funciona desde cualquier sitio: ", "Usually your domain, which works from anywhere: ")
                + L.t("por ejemplo mascotas.midominio.com", "for example pets.mydomain.com"), 13, GREY));
        final EditText main = input("mascotas.midominio.com", prefs.getString(KEY_URL, ""));
        box.addView(main, matchWrap());

        box.addView(label(L.t("Dirección en casa (opcional)", "Home address (optional)")));
        box.addView(text(L.t("La IP de tu servidor en la wifi de casa y el puerto, por ejemplo 192.168.1.x:8093. ", "Your server IP on your home wifi and the port, for example 192.168.1.x:8093. ")
                + L.t("Si pones las dos, la app usa sola la que funcione.", "If you enter both, the app uses whichever works."), 13, GREY));
        final EditText alt = input("192.168.1.x:8093", prefs.getString(KEY_ALT, ""));
        alt.setImeOptions(EditorInfo.IME_ACTION_GO);
        box.addView(alt, matchWrap());

        final TextView status = text(message != null ? message : "", 14, RED);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0, dp(12), 0, dp(12));
        box.addView(status);

        final Button connect = new Button(this);
        connect.setText(L.t("Conectar", "Connect"));
        connect.setTextColor(Color.WHITE);
        connect.setAllCaps(false);
        connect.setTextSize(16);
        GradientDrawable cbg = new GradientDrawable();
        cbg.setColor(INK);
        cbg.setCornerRadius(dp(10));
        connect.setBackground(cbg);
        box.addView(connect, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        final Runnable go = new Runnable() { @Override public void run() {
            final String u1 = normalize(main.getText().toString());
            final String u2 = alt.getText().toString().trim().isEmpty() ? "" : normalize(alt.getText().toString());
            if (u1 == null && (u2 == null || u2.isEmpty())) {
                status.setText(L.t("Escribe al menos una dirección válida.", "Enter at least one valid address."));
                return;
            }
            if (u2 == null) {
                status.setText(L.t("La dirección de casa no parece válida.", "The home address doesn't look valid."));
                return;
            }
            final String first = u1 != null ? u1 : u2;
            final String second = u1 != null ? u2 : "";
            connect.setEnabled(false);
            status.setTextColor(GREY);
            status.setText(L.t("Comprobando ", "Checking ") + first + " …");
            checkServer(first, new CheckResult() { @Override public void done(boolean ok, String error) {
                if (ok) { connect.setEnabled(true); saveAndOpen(first, second); return; }
                if (!second.isEmpty()) {
                    status.setText(L.t("Comprobando ", "Checking ") + second + " …");
                    checkServer(second, new CheckResult() { @Override public void done(boolean ok2, String error2) {
                        connect.setEnabled(true);
                        if (ok2) {
                            toast(L.t("Ahora entras por la dirección de casa. Fuera de casa se usará ", "You are now connected through the home address. Away from home it will use ") + first);
                            saveAndOpen(second, first);
                            return;
                        }
                        fail(status, first, second, error);
                    } });
                    return;
                }
                connect.setEnabled(true);
                fail(status, first, second, error);
            } });
        } };
        connect.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { go.run(); } });
        alt.setOnEditorActionListener(new TextView.OnEditorActionListener() { @Override public boolean onEditorAction(TextView v, int actionId, KeyEvent event) {
            if (actionId == EditorInfo.IME_ACTION_GO
                    || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER && event.getAction() == KeyEvent.ACTION_DOWN)) {
                go.run();
                return true;
            }
            return false;
        } });

        TextView help = text(L.t("\nSi tu dominio no usa https, escribe la dirección completa con http://\n", "\nIf your domain doesn't use https, type the full address with http://\n")
                + L.t("Puedes cambiar las direcciones cuando quieras: mantén pulsado el icono de MascotasPanel ", "You can change the addresses at any time: long-press the MascotasPanel icon ")
                + L.t("y elige «Cambiar servidor», o pulsa Atrás dentro de la app.", "and choose \"Change server\", or press Back inside the app."), 13, GREY);
        help.setGravity(Gravity.CENTER);
        box.addView(help);

        TextView ver = text(L.t("\nVersión ", "\nVersion ") + Novedades.version(this) + L.t(" · Ver novedades", " · What's new"), 13, RED);
        ver.setGravity(Gravity.CENTER);
        ver.setPadding(0, dp(8), 0, dp(8));
        ver.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { Novedades.show(MainActivity.this, prefs, null); } });
        box.addView(ver);

        root.addView(scroll);
    }

    private void fail(TextView status, final String first, final String second, String error) {
        status.setTextColor(RED);
        status.setText(error);
        new AlertDialog.Builder(this)
                .setTitle(L.t("No se ha podido comprobar", "Could not check"))
                .setMessage(error + L.t("\n\n¿Quieres guardar estas direcciones de todas formas?", "\n\nDo you want to save these addresses anyway?"))
                .setPositiveButton(L.t("Guardar", "Save"), new DialogInterface.OnClickListener() { @Override public void onClick(DialogInterface d, int w) { saveAndOpen(first, second); } })
                .setNegativeButton(L.t("Corregir", "Fix"), null)
                .show();
    }

    private TextView text(String s, int sp, int color) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        return t;
    }

    private TextView label(String s) {
        TextView t = text(s, 15, INK);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding(0, dp(10), 0, dp(2));
        t.setLayoutParams(matchWrap());
        return t;
    }

    private EditText input(String hint, String value) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setSingleLine(true);
        e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        e.setImeOptions(EditorInfo.IME_ACTION_NEXT);
        e.setText(value);
        return e;
    }

    private static LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    /**
     * Convierte lo que escribe la persona en una direccion completa, o null si no vale.
     * Sin http(s):// delante: una IP de casa o un nombre .local van con http://;
     * un dominio va con https://, que es lo normal en Internet.
     */
    static String normalize(String s) {
        if (s == null) return null;
        s = s.trim();
        if (s.isEmpty() || s.contains(" ")) return null;
        if (!s.matches("(?i)^https?://.*")) {
            String host = s.split("[:/]")[0].toLowerCase();
            boolean local = host.matches("^\\d{1,3}(\\.\\d{1,3}){3}$") || host.equals("localhost")
                    || host.endsWith(".local") || host.endsWith(".lan") || !host.contains(".");
            s = (local ? "http://" : "https://") + s;
        }
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        if (s.toLowerCase().endsWith("/panel")) s = s.substring(0, s.length() - 6);
        Uri u = Uri.parse(s);
        if (u.getHost() == null || u.getHost().isEmpty()) return null;
        return s;
    }

    private interface CheckResult { void done(boolean ok, String error); }

    /** Pide el manifest de la web para comprobar que al otro lado hay un MascotasPanel. */
    private void checkServer(final String url, final CheckResult cb) {
        final Handler main = new Handler(Looper.getMainLooper());
        new Thread(new Runnable() { @Override public void run() {
            boolean ok = false;
            String error;
            HttpURLConnection c = null;
            try {
                c = (HttpURLConnection) new URL(url + "/static/manifest.webmanifest").openConnection();
                c.setConnectTimeout(7000);
                c.setReadTimeout(7000);
                int code = c.getResponseCode();
                if (code == 200) {
                    InputStream in = c.getInputStream();
                    byte[] buf = new byte[4096];
                    int n = in.read(buf);
                    String body = n > 0 ? new String(buf, 0, n, "UTF-8") : "";
                    in.close();
                    ok = body.contains("MascotasPanel");
                    error = ok ? null : L.t("Esa dirección responde, pero no parece un servidor MascotasPanel.", "That address responds, but it doesn't look like an MascotasPanel server.");
                } else {
                    error = L.t("El servidor ha respondido con un error (", "The server responded with an error (") + code + ").";
                }
            } catch (javax.net.ssl.SSLException e) {
                error = L.t("Problema con el certificado https del servidor. Si tu servidor no usa https, escribe la dirección con http://", "Problem with the server's https certificate. If your server doesn't use https, type the address with http://");
            } catch (java.net.UnknownHostException e) {
                error = L.t("No se encuentra esa dirección. Revisa que esté bien escrita.", "That address can't be found. Check that it is typed correctly.");
            } catch (java.net.SocketTimeoutException e) {
                error = L.t("El servidor no contesta. Si has puesto la IP de casa, comprueba que estás conectado a la wifi de casa.", "The server doesn't answer. If you entered the home IP, check that you are on your home wifi.");
            } catch (Exception e) {
                error = L.t("No se puede conectar. Si has puesto la IP de casa, comprueba que estás conectado a la wifi de casa.", "Cannot connect. If you entered the home IP, check that you are on your home wifi.");
            } finally {
                if (c != null) c.disconnect();
            }
            final boolean fOk = ok;
            final String fErr = error;
            main.post(new Runnable() { @Override public void run() { cb.done(fOk, fErr); } });
        } }).start();
    }

    private void saveAndOpen(String url, String alt) {
        prefs.edit().putString(KEY_URL, url).putString(KEY_ALT, alt == null ? "" : alt).apply();
        showWeb(url, null);
    }

    // ------------------------------------------------------------------ La web

    private void showWeb(final String url, Bundle state) {
        root.removeAllViews();
        base = url;
        errorShown = false;
        web = new WebView(this);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.addView(progress, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(3)));

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setSupportMultipleWindows(false); // el registro público y los pipicanes se abren dentro de la app
        s.setGeolocationEnabled(true);      // «Estoy aquí» en los mapas
        s.setUserAgentString(s.getUserAgentString() + " MascotasPanelAndroid/" + Novedades.version(this));

        CookieManager cm = CookieManager.getInstance();
        cm.setAcceptCookie(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri u = req.getUrl();
                String scheme = u.getScheme();
                if (("http".equals(scheme) || "https".equals(scheme)) && isOurHost(u)) {
                            return false;
                }
                openOutside(u);
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) connectionFailed();
            }

            @Override
            public void onPageFinished(WebView view, String u) {
                CookieManager.getInstance().flush();
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int p) {
                progress.setProgress(p);
                progress.setVisibility(p >= 100 ? View.GONE : View.VISIBLE);
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = cb;
                if (!has(Manifest.permission.CAMERA) && !prefs.getBoolean("camera_asked", false)) {
                    // La primera vez se pide la cámara para poder hacer la foto desde aquí; si dice que no, solo galería
                    prefs.edit().putBoolean("camera_asked", true).apply();
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
                    return true;
                }
                openChooser();
                return true;
            }

            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                if (has(Manifest.permission.ACCESS_FINE_LOCATION) || has(Manifest.permission.ACCESS_COARSE_LOCATION)) { cb.invoke(origin, true, false); return; }
                geoCb = cb; geoOrigin = origin;
                requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_GEO);
            }
        });

        web.addJavascriptInterface(new Bridge(this), "MascotasPanelAndroid");

        web.setDownloadListener(new android.webkit.DownloadListener() { @Override public void onDownloadStart(String u, String userAgent, String disposition, String mime, long length) {
            download(new String[]{u, userAgent, disposition, mime});
        } });

        Novedades.check(this, prefs, false);
        if (state != null && web.restoreState(state) != null) return;
        web.loadUrl(base + "/panel");
    }

    private boolean isOurHost(Uri u) {
        String h = u.getHost();
        if (h == null) return false;
        for (String b : new String[]{prefs.getString(KEY_URL, ""), prefs.getString(KEY_ALT, "")}) {
            if (b != null && !b.isEmpty() && h.equalsIgnoreCase(Uri.parse(b).getHost())) return true;
        }
        return false;
    }

    private void openOutside(Uri u) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, u));
        } catch (ActivityNotFoundException e) {
            toast(L.t("No hay ninguna app para abrir este enlace", "No app available to open this link"));
        }
    }

    /** La direccion actual no responde: se prueba la otra (casa o dominio) antes de avisar. */
    private void connectionFailed() {
        String alt = prefs.getString(KEY_ALT, "");
        if (!triedOther && alt != null && !alt.isEmpty() && !alt.equals(base)) {
            triedOther = true;
            final String other = alt;
            checkServer(other, new CheckResult() { @Override public void done(boolean ok, String error) {
                if (ok) {
                    String cur = base;
                    prefs.edit().putString(KEY_URL, other).putString(KEY_ALT, cur).apply();
                    toast(L.t("Conectado por ", "Connected through ") + other);
                    showWeb(other, null);
                } else {
                    showConnectionError();
                }
            } });
            return;
        }
        showConnectionError();
    }

    private void showConnectionError() {
        if (errorShown || isFinishing()) return;
        errorShown = true;
        new AlertDialog.Builder(this)
                .setTitle(L.t("No se puede conectar", "Cannot connect"))
                .setMessage(L.t("Tu servidor MascotasPanel no responde (", "Your MascotasPanel server is not responding (") + base + ").\n\n"
                        + L.t("Si usas la IP de casa, comprueba que estás en la wifi de casa. ", "If you use the home IP, check that you are on your home wifi. ")
                        + L.t("Fuera de casa necesitas la dirección con tu dominio.", "Away from home you need the address with your domain."))
                .setPositiveButton(L.t("Reintentar", "Retry"), new DialogInterface.OnClickListener() { @Override public void onClick(DialogInterface d, int w) {
                    errorShown = false;
                    triedOther = false;
                    if (web != null) web.loadUrl(base + "/panel");
                } })
                .setNegativeButton(L.t("Cambiar servidor", "Change server"), new DialogInterface.OnClickListener() { @Override public void onClick(DialogInterface d, int w) { showSetup(null); } })
                .setCancelable(false)
                .show();
    }

    // ------------------------------------------------------------------ Descargas (QR, tus datos)

    private void download(String[] d) {
        if (Build.VERSION.SDK_INT <= 28 && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            pendingDownload = d;
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
            return;
        }
        try {
            String name = URLUtil.guessFileName(d[0], d[2], d[3]);
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(d[0]));
            String cookie = CookieManager.getInstance().getCookie(d[0]);
            if (cookie != null) r.addRequestHeader("Cookie", cookie);
            r.addRequestHeader("User-Agent", d[1]);
            r.setTitle(name);
            r.setMimeType(d[3]);
            r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
            ((DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE)).enqueue(r);
            toast(L.t("Descargando ", "Downloading ") + name + L.t(" en la carpeta Descargas", " to the Downloads folder"));
        } catch (Exception e) {
            toast(L.t("No se ha podido descargar", "Could not download"));
        }
    }

    private boolean has(String perm) { return checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED; }

    /** Galería y, si hay permiso, también la cámara para hacer la foto en el momento. */
    private void openChooser() {
        Intent pick = new Intent(Intent.ACTION_GET_CONTENT);
        pick.addCategory(Intent.CATEGORY_OPENABLE);
        pick.setType("image/*");
        Intent chooser = Intent.createChooser(pick, L.t("Elegir o hacer una foto", "Choose or take a photo"));
        photoUri = null;
        if (has(Manifest.permission.CAMERA)) {
            try {
                ContentValues cv = new ContentValues();
                cv.put(MediaStore.Images.Media.DISPLAY_NAME, "mascotaspanel-" + System.currentTimeMillis() + ".jpg");
                cv.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                if (Build.VERSION.SDK_INT >= 29) cv.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/MascotasPanel");
                photoUri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv);
                Intent cam = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                cam.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
                chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{cam});
            } catch (Exception e) { photoUri = null; }
        }
        try {
            startActivityForResult(chooser, REQ_FILES);
        } catch (ActivityNotFoundException e) {
            if (fileCallback != null) fileCallback.onReceiveValue(null);
            fileCallback = null;
            toast(L.t("No hay ninguna app para elegir fotos", "No app available to pick photos"));
        }
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        boolean ok = results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED;
        if (code == REQ_CAMERA) { if (fileCallback != null) openChooser(); return; }
        if (code == REQ_GEO && geoCb != null) {
            boolean any = ok || (results.length > 1 && results[1] == PackageManager.PERMISSION_GRANTED);
            geoCb.invoke(geoOrigin, any, false); geoCb = null; return;
        }
        if (code == REQ_STORAGE && pendingDownload != null) {
            String[] d = pendingDownload;
            pendingDownload = null;
            if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) download(d);
            else toast(L.t("Sin permiso no se puede guardar la descarga", "Without permission the download can't be saved"));
        }
    }

    @Override
    protected void onActivityResult(int req, int result, Intent data) {
        if (req == REQ_FILES && fileCallback != null) {
            Uri[] res = null;
            if (result == RESULT_OK && data != null && data.getData() != null) res = new Uri[]{data.getData()};
            else if (result == RESULT_OK && photoUri != null) res = new Uri[]{photoUri};
            else if (photoUri != null) { try { getContentResolver().delete(photoUri, null, null); } catch (Exception ignored) { } }
            fileCallback.onReceiveValue(res);
            fileCallback = null;
            return;
        }
        super.onActivityResult(req, result, data);
    }

    // ------------------------------------------------------------------ Puente con la web

    /** La web lo usa para compartir, copiar y guardar archivos (ver app.js). */
    public static final class Bridge {
        private final MainActivity a;
        Bridge(MainActivity a) { this.a = a; }

        @JavascriptInterface
        public void share(final String url, final String title) {
            a.runOnUiThread(new Runnable() { @Override public void run() {
                Intent i = new Intent(Intent.ACTION_SEND);
                i.setType("text/plain");
                i.putExtra(Intent.EXTRA_TEXT, url);
                if (title != null) i.putExtra(Intent.EXTRA_SUBJECT, title);
                a.startActivity(Intent.createChooser(i, L.t("Compartir", "Share")));
            } });
        }

        @JavascriptInterface
        public void copy(final String text) {
            a.runOnUiThread(new Runnable() { @Override public void run() {
                ClipboardManager cm = (ClipboardManager) a.getSystemService(Context.CLIPBOARD_SERVICE);
                cm.setPrimaryClip(ClipData.newPlainText("MascotasPanel", text));
                a.toast(L.t("Enlace copiado", "Link copied"));
            } });
        }

        @JavascriptInterface
        public String version() { return Novedades.version(a); }

        /** Guarda en Descargas/MascotasPanel un archivo hecho en la web (el cartel en PDF o imagen, el código…). */
        @JavascriptInterface
        public void saveFile(final String b64, final String name, final String mime) {
            final byte[] data = Base64.decode(b64, Base64.DEFAULT);
            a.runOnUiThread(new Runnable() { @Override public void run() { a.saveBytes(data, clean(name), mime); } });
        }

        /** Comparte un archivo (por ejemplo, el cartel) con WhatsApp, Telegram, correo… */
        @JavascriptInterface
        public void shareFile(final String b64, final String name, final String mime, final String text) {
            final byte[] data = Base64.decode(b64, Base64.DEFAULT);
            a.runOnUiThread(new Runnable() { @Override public void run() { a.shareBytes(data, clean(name), mime, text); } });
        }

        /** Novedades de la app (la web tiene las suyas). */
        @JavascriptInterface
        public void news() {
            a.runOnUiThread(new Runnable() { @Override public void run() { Novedades.show(a, a.prefs, null); } });
        }

        /** El panel avisa del idioma elegido (es/en) para que la app use el mismo. */
        @JavascriptInterface
        public void setLang(String l) { L.set(a, l); }

        /** Mira ahora si hay una versión nueva de la app en GitHub. */
        @JavascriptInterface
        public void checkUpdate() {
            a.runOnUiThread(new Runnable() { @Override public void run() { Novedades.check(a, a.prefs, true); } });
        }
    }

    static String clean(String n) {
        n = n == null ? "" : n.replaceAll("[^A-Za-z0-9._ -]", "_");
        return n.isEmpty() ? "mascotaspanel" : n;
    }

    private void saveBytes(final byte[] data, final String name, final String mime) {
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues cv = new ContentValues();
                cv.put(MediaStore.Downloads.DISPLAY_NAME, name);
                cv.put(MediaStore.Downloads.MIME_TYPE, mime);
                cv.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/MascotasPanel");
                Uri u = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv);
                OutputStream o = getContentResolver().openOutputStream(u);
                o.write(data);
                o.close();
            } else {
                if (!has(Manifest.permission.WRITE_EXTERNAL_STORAGE)) {
                    requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
                    toast(L.t("Da permiso y vuelve a pulsar Descargar.", "Allow it and tap Download again."));
                    return;
                }
                File d = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "MascotasPanel");
                d.mkdirs();
                FileOutputStream o = new FileOutputStream(new File(d, name));
                o.write(data);
                o.close();
            }
            toast(L.t("Guardado en Descargas/MascotasPanel: ", "Saved in Downloads/MascotasPanel: ") + name);
        } catch (Exception e) {
            toast(L.t("No se pudo guardar el archivo", "Could not save the file"));
        }
    }

    private void shareBytes(byte[] data, String name, String mime, String text) {
        try {
            File d = Archivos.dir(this);
            File[] old = d.listFiles();
            if (old != null) for (File f : old) if (System.currentTimeMillis() - f.lastModified() > 3600_000L) f.delete();
            File f = new File(d, name);
            FileOutputStream o = new FileOutputStream(f);
            o.write(data);
            o.close();
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType(mime);
            i.putExtra(Intent.EXTRA_STREAM, Archivos.uri(f));
            if (text != null && !text.isEmpty()) i.putExtra(Intent.EXTRA_TEXT, text);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(i, L.t("Compartir", "Share")));
        } catch (Exception e) {
            toast(L.t("No se pudo compartir", "Could not share"));
        }
    }

    // ------------------------------------------------------------------ Atrás y ciclo de vida

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
            return;
        }
        if (web == null) {
            if (prefs.getString(KEY_URL, null) != null) showWeb(prefs.getString(KEY_URL, null), null);
            else super.onBackPressed();
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle("MascotasPanel")
                .setItems(new CharSequence[]{L.t("Salir", "Exit"), L.t("Cambiar servidor", "Change server"), L.t("Recargar", "Reload"),
                        L.t("Novedades (versión ", "What's new (version ") + Novedades.version(this) + ")"}, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) {
                        if (which == 0) finish();
                        else if (which == 1) showSetup(null);
                        else if (which == 2) { triedOther = false; errorShown = false; web.reload(); }
                        else Novedades.show(MainActivity.this, prefs, null);
                    }
                })
                .show();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        if (web != null) web.saveState(out);
    }

    @Override
    protected void onPause() {
        super.onPause();
        CookieManager.getInstance().flush();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (web != null) web.destroy();
        super.onDestroy();
    }

    void toast(String msg) {
        Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }
}
