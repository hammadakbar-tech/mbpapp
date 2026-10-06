package com.merabrandpakistan.app

import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.webkit.CookieManager
import android.webkit.URLUtil
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.button.MaterialButton

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private lateinit var offlineView: View

    private var fileCallback: ValueCallback<Array<Uri>>? = null

    private val fileChooser =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val uris = WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
            fileCallback?.onReceiveValue(uris)
            fileCallback = null
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        progressBar = findViewById(R.id.progressBar)
        offlineView = findViewById(R.id.offlineView)

        configureWebView()

        swipeRefresh.setColorSchemeResources(R.color.brand_primary)
        swipeRefresh.setOnRefreshListener { webView.reload() }
        // Only allow pull-to-refresh when the page is scrolled to the top.
        swipeRefresh.setOnChildScrollUpCallback { _, _ -> webView.scrollY > 0 }

        findViewById<MaterialButton>(R.id.retryButton).setOnClickListener { loadStartPage() }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            // Deep link (https://merabrandpakistan.com/...) or the home page.
            loadUrl(intent?.data?.toString() ?: BuildConfig.START_URL)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            builtInZoomControls = false
            setSupportZoom(false)
            mediaPlaybackRequiresUserGesture = true
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            allowFileAccess = false
            allowContentAccess = false
            // Lets the site tell app visitors apart from browser visitors.
            userAgentString = "$userAgentString MBPApp/${BuildConfig.VERSION_NAME}"
        }
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true)

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                return when (uri.scheme) {
                    // Web pages stay in the app. This also keeps payment-gateway redirects working.
                    "http", "https" -> false
                    else -> {
                        openExternally(uri)
                        true
                    }
                }
            }

            override fun onPageStarted(view: WebView, url: String, favicon: Bitmap?) {
                offlineView.visibility = View.GONE
            }

            override fun onPageFinished(view: WebView, url: String) {
                swipeRefresh.isRefreshing = false
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError,
            ) {
                // Only react to failures of the page itself, not images/scripts.
                if (request.isForMainFrame) {
                    swipeRefresh.isRefreshing = false
                    progressBar.visibility = View.GONE
                    offlineView.visibility = View.VISIBLE
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, newProgress: Int) {
                progressBar.progress = newProgress
                progressBar.visibility = if (newProgress in 1..99) View.VISIBLE else View.GONE
            }

            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: ValueCallback<Array<Uri>>,
                fileChooserParams: FileChooserParams,
            ): Boolean {
                fileCallback?.onReceiveValue(null)
                fileCallback = filePathCallback
                return try {
                    fileChooser.launch(fileChooserParams.createIntent())
                    true
                } catch (e: ActivityNotFoundException) {
                    fileCallback = null
                    false
                }
            }
        }

        webView.setDownloadListener { url, userAgent, contentDisposition, mimeType, _ ->
            val request = DownloadManager.Request(Uri.parse(url)).apply {
                setMimeType(mimeType)
                addRequestHeader("User-Agent", userAgent)
                CookieManager.getInstance().getCookie(url)?.let { addRequestHeader("Cookie", it) }
                setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                setDestinationInExternalFilesDir(
                    this@MainActivity,
                    Environment.DIRECTORY_DOWNLOADS,
                    URLUtil.guessFileName(url, contentDisposition, mimeType),
                )
            }
            (getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager).enqueue(request)
            Toast.makeText(this, R.string.download_started, Toast.LENGTH_SHORT).show()
        }
    }

    private fun loadStartPage() = loadUrl(BuildConfig.START_URL)

    private fun loadUrl(url: String) {
        if (!isOnline()) {
            offlineView.visibility = View.VISIBLE
            return
        }
        offlineView.visibility = View.GONE
        webView.loadUrl(url)
    }

    private fun isOnline(): Boolean {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val caps = cm.getNetworkCapabilities(cm.activeNetwork) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    /** tel:, mailto:, whatsapp:, intent: and other non-web links open in the matching app. */
    private fun openExternally(uri: Uri) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, uri))
        } catch (e: ActivityNotFoundException) {
            Toast.makeText(this, R.string.cannot_open_link, Toast.LENGTH_SHORT).show()
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        intent.data?.let { loadUrl(it.toString()) }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onPause() {
        CookieManager.getInstance().flush()
        webView.onPause()
        super.onPause()
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}
