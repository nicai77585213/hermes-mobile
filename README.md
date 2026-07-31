# Hermes Mobile

Hermes Mobile packages the Hermes Agent runtime, local Dashboard, Node/TUI runtime, and an Android mobile interface into a self-contained Android application.

> Current status: version 1.1 (`versionCode 2`) is under active development. The published source builds an ARM64 debug APK and is not yet a production-signed release.

## Features

- Runs Hermes Agent locally on Android without requiring Termux or a remote server.
- Bundles Python, Dashboard assets, Node/TUI runtime, and required ARM64 native libraries.
- Provides mobile chat, session persistence, file access, automation, integrations, remote instance status, memory, Skills Hub, themes, and model settings.
- Provides an in-app Wireless Debugging page and an `android_debug` Agent tool for paired-device diagnostics without Termux.
- Shows streaming reasoning and tool execution as collapsible, stateful mobile cards.
- Uses a mobile drawer and settings-oriented navigation designed for phones.

## Repository Layout

- `android/` — Android and Gradle project.
- `android/app/src/main/python/` — bundled Hermes Agent Python source.
- `android/app/src/main/assets/` — Dashboard, Node, and TUI assets.
- `android/app/src/main/jniLibs/arm64-v8a/` — Android ARM64 runtime binaries.
- `www/` — mobile WebView shell.
- `Hermes.md` — sanitized public project handoff memory and current development state.

## Build

Prerequisites:

- JDK compatible with the configured Android Gradle Plugin.
- Android SDK with the required build tools and platform installed.
- Node.js and npm for Capacitor dependency management.
- The local Python/Chaquopy build requirements referenced by the Android project.

```powershell
npm install
cd android
./gradlew assembleDebug --console=plain
```

The debug APK is generated under `android/app/build/outputs/apk/debug/`. APK files and local build configuration are intentionally excluded from Git.

The bundled development ADB host binary is derived from LADB and must be replaced with an independently built AOSP binary before any Google Play publication. See `THIRD_PARTY_NOTICES.md`.

## Platform Support

- Android `arm64-v8a` only.
- Physical ARM64 Android devices are the primary test target.
- Release signing, upgrade migration, and production release validation are not complete.

## Security and Privacy

Do not commit API keys, access tokens, signing keys, local configuration, databases, session dumps, device backups, logs, or personal device information. See `SECURITY.md` for responsible reporting.

## Project Memory

Read `Hermes.md` before continuing development. It records the current architecture, validated features, known limitations, technical constraints, and next steps. The public copy is sanitized and must remain free of private environment information.

## License

This repository is distributed under the MIT License. The bundled Hermes Agent source retains the original Nous Research copyright and license notice. See `LICENSE` and `android/app/src/main/python/LICENSE`.
