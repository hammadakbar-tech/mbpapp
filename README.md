# Mera Brand Pakistan – Android app

A native Android (Kotlin) shell around [merabrandpakistan.com](https://merabrandpakistan.com).

## Features
- Splash screen and brand-colored status bar
- Full website in a WebView (JavaScript, cookies and logins persist)
- Pull-to-refresh, loading progress bar, back-button navigation
- Offline screen with a "Try again" button
- `tel:`, `mailto:`, WhatsApp and other non-web links open in the right app
- File uploads and downloads
- `https://merabrandpakistan.com/...` links open in the app
- HTTPS only (cleartext traffic and mixed content are blocked)

## Build
Requires JDK 17 and the Android SDK (or just Android Studio).

```sh
./gradlew assembleDebug      # APK in app/build/outputs/apk/debug/
```

Or open the folder in Android Studio and press Run. The GitHub Actions workflow
(`.github/workflows/android.yml`) also builds the debug APK on every push.

## Customising
| What | Where |
|---|---|
| Site URL | `START_URL` in `app/build.gradle.kts` (and the hosts in `AndroidManifest.xml`) |
| Brand colors | `app/src/main/res/values/colors.xml` |
| App name | `app/src/main/res/values/strings.xml` |
| Logo / launcher icon | `res/drawable/ic_launcher_foreground.xml` (currently a placeholder "M") |
| Package name | `applicationId` / `namespace` in `app/build.gradle.kts` |

The WebView appends `MBPApp/<version>` to the user agent, so the site can detect the app.

## Releasing to Google Play
Create a signing key, configure `signingConfigs` for the `release` build type, then run
`./gradlew bundleRelease` to get an `.aab` for upload. Never commit the keystore.

## Notes
All `http(s)` navigation stays inside the WebView so that payment-gateway redirects
(JazzCash, Easypaisa, card 3-D Secure, etc.) return to the app. If you would rather open
other domains in the browser, change `shouldOverrideUrlLoading` in `MainActivity.kt`.
