# Code Changes Required for Play Store Launch

## 1. CHANGE PACKAGE NAME

### Step 1.1: Update build.gradle.kts
**File:** `flutter_application_1/android/app/build.gradle.kts`

**Change line 9:**
```kotlin
// FROM:
namespace = "com.example.flutter_application_1"

// TO:
namespace = "com.well360.healthanalyzer"
```

**Change line 25:**
```kotlin
// FROM:
applicationId = "com.example.flutter_application_1"

// TO:
applicationId = "com.well360.healthanalyzer"
```

### Step 1.2: Rename package directories
Rename directory structure in `android/app/src/main/kotlin/`:
```
FROM: com/example/flutter_application_1/
TO:   com/well360/healthanalyzer/
```

### Step 1.3: Update MainActivity.kt
**File:** `flutter_application_1/android/app/src/main/kotlin/.../MainActivity.kt`

Update package declaration:
```kotlin
// FROM:
package com.example.flutter_application_1

// TO:
package com.well360.healthanalyzer
```

---

## 2. CREATE SIGNING CONFIGURATION

### Step 2.1: Generate Keystore
Run this command in your terminal:
```bash
cd d:\PP2\Research_Project_225\Well360_FrontEnd_BackEnd\flutter_application_1\android\app

keytool -genkey -v -keystore well360-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias well360
```

You'll be prompted for:
- Keystore password (choose strong password, SAVE IT!)
- Key password (can be same as keystore password)
- Your name
- Organization unit (optional)
- Organization (e.g., "Well360")
- City
- State
- Country code (e.g., "US")

**⚠️ CRITICAL: Save the passwords! You cannot recover the keystore without them!**

### Step 2.2: Create key.properties
**File:** `flutter_application_1/android/key.properties` (NEW FILE)

```properties
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=well360
storeFile=well360-release-key.jks
```

### Step 2.3: Update .gitignore
**File:** `flutter_application_1/android/.gitignore`

Add these lines:
```
key.properties
*.jks
*.keystore
```

### Step 2.4: Configure Signing in build.gradle.kts
**File:** `flutter_application_1/android/app/build.gradle.kts`

**Add at the top (after plugins block):**
```kotlin
plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

// ADD THIS:
val keystorePropertiesFile = rootProject.file("key.properties")
val keystoreProperties = java.util.Properties()
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(java.io.FileInputStream(keystorePropertiesFile))
}

android {
    // ... existing config ...
```

**Update signingConfigs (add before buildTypes):**
```kotlin
android {
    // ... existing config ...

    // ADD THIS BLOCK:
    signingConfigs {
        create("release") {
            if (keystorePropertiesFile.exists()) {
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
                storeFile = file(keystoreProperties["storeFile"] as String)
                storePassword = keystoreProperties["storePassword"] as String
            }
        }
    }

    buildTypes {
        release {
            // CHANGE THIS LINE:
            // FROM: signingConfig = signingConfigs.getByName("debug")
            // TO:
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

---

## 3. SECURE NETWORK CONFIGURATION

### Option A: HTTPS Only (Recommended for Production)
**File:** `flutter_application_1/android/app/src/main/AndroidManifest.xml`

**Remove this line:**
```xml
android:usesCleartextTraffic="true"
```

### Option B: Restrict to Debug Builds Only
Keep cleartext traffic for development, disable for release:

**File:** `flutter_application_1/android/app/src/debug/AndroidManifest.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:usesCleartextTraffic="true">
    </application>
</manifest>
```

**File:** `flutter_application_1/android/app/src/main/AndroidManifest.xml`
```xml
<!-- REMOVE: android:usesCleartextTraffic="true" -->
```

---

## 4. UPDATE APP TO USE PRODUCTION BACKEND

### Step 4.1: Create Environment Configuration
**File:** `flutter_application_1/lib/config/app_config.dart` (NEW FILE)

```dart
class AppConfig {
  // Change this to your production backend URL after deployment
  static const String baseUrl = 'https://your-backend-domain.com';
  
  // For development, you can use:
  // static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator
  // static const String baseUrl = 'http://localhost:8000'; // iOS simulator
  
  static const bool isProduction = bool.fromEnvironment('dart.vm.product');
  
  static String get apiBaseUrl {
    if (isProduction) {
      return baseUrl;
    } else {
      // Use saved base URL from settings for development
      return baseUrl;
    }
  }
}
```

### Step 4.2: Update Auth Service
**File:** `flutter_application_1/lib/services/auth_service.dart`

Find where base URL is used and update to use AppConfig:
```dart
import 'package:flutter_application_1/config/app_config.dart';

class AuthService {
  static Future<void> loadBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString('base_url') ?? AppConfig.apiBaseUrl;
  }
  
  // ... rest of code
}
```

---

## 5. ADD PRIVACY & LEGAL SCREENS

### Step 5.1: Create Privacy Policy Screen
**File:** `flutter_application_1/lib/screens/settings/privacy_policy_screen.dart` (NEW FILE)

```dart
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

  static const String privacyPolicyUrl = 'https://your-domain.com/privacy-policy';

  Future<void> _launchPrivacyPolicy() async {
    final uri = Uri.parse(privacyPolicyUrl);
    if (!await launchUrl(uri, mode: LaunchMode.externalBrowser)) {
      throw Exception('Could not launch $privacyPolicyUrl');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Privacy Policy'),
      ),
      body: Center(
        child: ElevatedButton(
          onPressed: _launchPrivacyPolicy,
          child: const Text('View Privacy Policy'),
        ),
      ),
    );
  }
}
```

### Step 5.2: Add url_launcher Package
**File:** `flutter_application_1/pubspec.yaml`

Add to dependencies:
```yaml
dependencies:
  flutter:
    sdk: flutter
  # ... existing dependencies ...
  url_launcher: ^6.2.0  # ADD THIS
```

Run: `flutter pub get`

### Step 5.3: Create About Screen
**File:** `flutter_application_1/lib/screens/settings/about_screen.dart` (NEW FILE)

```dart
import 'package:flutter/material.dart';
import 'package:flutter_application_1/screens/settings/privacy_policy_screen.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('About'),
      ),
      body: ListView(
        children: [
          const ListTile(
            title: Text('Well360'),
            subtitle: Text('AI Health Analyzer'),
          ),
          const ListTile(
            title: Text('Version'),
            subtitle: Text('1.0.0'),
          ),
          ListTile(
            title: const Text('Privacy Policy'),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const PrivacyPolicyScreen(),
                ),
              );
            },
          ),
          ListTile(
            title: const Text('Terms of Service'),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: () {
              // Navigate to terms of service
            },
          ),
          const Divider(),
          const ListTile(
            title: Text('Medical Disclaimer'),
            subtitle: Text(
              'This app is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.',
            ),
          ),
          const ListTile(
            title: Text('Contact'),
            subtitle: Text('support@well360.com'),
          ),
        ],
      ),
    );
  }
}
```

---

## 6. BUILD RELEASE AAB

### Step 6.1: Clean and Build
```bash
cd d:\PP2\Research_Project_225\Well360_FrontEnd_BackEnd\flutter_application_1

# Clean build cache
flutter clean

# Get dependencies
flutter pub get

# Build release AAB
flutter build appbundle --release
```

### Step 6.2: Locate the AAB file
The file will be at:
```
flutter_application_1\build\app\outputs\bundle\release\app-release.aab
```

This is the file you'll upload to Google Play Console.

---

## 7. TEST RELEASE BUILD

### Install release build on device:
```bash
# Build APK for testing (AAB is for Play Store only)
flutter build apk --release

# Install on connected device
adb install build\app\outputs\flutter-apk\app-release.apk
```

### Test checklist:
- [ ] App launches successfully
- [ ] Login works
- [ ] All modules load (Hydration, Fitness, Mental Health)
- [ ] Camera permission works
- [ ] Location permission works
- [ ] Backend connectivity works (must use production backend!)
- [ ] Notifications work
- [ ] No crashes during normal use
- [ ] Settings screens accessible
- [ ] Privacy policy link works

---

## 8. COMMON ISSUES & FIXES

### Issue: "Keystore tampered with or password incorrect"
**Fix:** Double-check password in key.properties matches what you entered during keystore creation

### Issue: "Release APK much larger than debug"
**Fix:** This is normal. AAB will be smaller due to Play Store optimization

### Issue: "Cleartext HTTP traffic not permitted"
**Fix:** Ensure backend uses HTTPS or configure network_security_config.xml properly

### Issue: "App crashes on release but not debug"
**Fix:** Usually related to ProGuard/R8 obfuscation. Check specific errors in crash logs

---

## PRIORITY ORDER

1. **FIRST:** Change package name ✅ Most critical
2. **SECOND:** Create signing key ✅ Required for release
3. **THIRD:** Deploy backend with HTTPS ✅ App won't work without it
4. **FOURTH:** Add privacy policy screen ✅ Play Store requirement
5. **FIFTH:** Build and test release AAB ✅ Validate everything works

---

## BACKUP YOUR KEYSTORE!

⚠️⚠️⚠️ **EXTREMELY IMPORTANT** ⚠️⚠️⚠️

**Make multiple backups of:**
- `well360-release-key.jks`
- The passwords you chose

**Store in:**
- Secure cloud storage (Google Drive, Dropbox, etc.)
- External hard drive
- Password manager (for passwords)

**Why:** If you lose the keystore, you can NEVER update your app on Play Store. You'll have to publish as a new app with a new package name, losing all users and reviews.

---

*Document Version: 1.0*  
*Last Updated: February 11, 2026*
