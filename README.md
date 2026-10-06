# Mera Brand Pakistan – Exhibition app (Android)

Native Android app (Kotlin + Jetpack Compose) for the Mera Brand Pakistan exhibition.

## What it does
**Welcome screen** → choose how to sign in.

**Exhibitors** (no sign-up – accounts are created by the organisers)
- Log in with Exhibitor ID + PIN
- Dashboard: pending / accepted / declined counts and upcoming meetings
- Meeting requests: accept or decline visitor requests
- View their product list and profile (hall + booth)

**Visitors** (register or log in)
- Browse and search exhibitors and products
- See each exhibitor's hall and booth, and browse by hall
- Request a meeting (pick a time slot, add a message) and track its status

## Demo mode
The app currently runs on **sample data** stored on the device, so it works without a server:
- Exhibitor login: `EXH001` … `EXH008`, PIN `1234`
- Visitors can register any email and password (stored locally on the phone)
- Meeting requests are shared between visitor and exhibitor accounts **on the same phone only**

## Connecting your real server
All data goes through the `EventRepository` interface (`data/EventRepository.kt`).
`DemoRepository` is the demo implementation. To go live, write a second implementation that calls
your API (exhibitor login, visitor register/login, exhibitors, products, halls, meeting requests)
and replace `DemoRepository(...)` in `EventViewModel.kt`. The screens don't need to change.
Remove the "Demo mode" hint in `ui/AuthScreens.kt` at the same time.

## Build
Requires JDK 17 and the Android SDK (or Android Studio).

```sh
./gradlew assembleDebug      # APK in app/build/outputs/apk/debug/
```

GitHub Actions (`.github/workflows/android.yml`) builds the APK on every push and publishes it
under **Releases → latest-debug** as `MeraBrandPakistan.apk`.

## Customising
| What | Where |
|---|---|
| Brand colors | `ui/theme/Theme.kt` and `res/values/colors.xml` |
| Logo / launcher icon | `res/mipmap-*/ic_launcher_foreground.png`, `res/drawable-nodpi/logo.png` |
| Sample exhibitors, products, halls, time slots | `data/DemoData.kt` |
| App name | `res/values/strings.xml` |
| Package name | `applicationId` / `namespace` in `app/build.gradle.kts` |

## Releasing to Google Play
Create a signing key, configure `signingConfigs` for the `release` build type, then run
`./gradlew bundleRelease` to get an `.aab` for upload. Never commit the keystore.
