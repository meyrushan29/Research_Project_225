import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
// For DebugPrints
import 'dart:io'; // For SocketException
import 'dart:async'; // For Timeout

class AuthService {
  static String? _customBaseUrl;
  static const String _baseUrlKey = 'custom_base_url';

  // Load configured URL at startup; fix platform-mismatched URLs (web vs emulator)
  static Future<void> loadBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    String? url = prefs.getString(_baseUrlKey);
    // Web: prefer 127.0.0.1 over localhost (avoids "Failed to fetch" in some browsers)
    if (kIsWeb && url != null && url.contains('localhost') && url.contains('8000')) {
      url = "http://127.0.0.1:8000";
      await prefs.setString(_baseUrlKey, url);
    }
    // Android: 127.0.0.1/localhost point to the device, not your PC — use emulator host
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      final u = (url ?? "").trim().toLowerCase();
      if (u.contains('127.0.0.1') || u.contains('localhost')) {
        url = "http://10.0.2.2:8000";
        await prefs.setString(_baseUrlKey, url);
      }
    }
    _customBaseUrl = url;
  }

  // Set and persist new URL
  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    if (url.isEmpty) {
      await prefs.remove(_baseUrlKey);
      _customBaseUrl = null;
    } else {
      await prefs.setString(_baseUrlKey, url);
      _customBaseUrl = url;
    }
  }

  // Unified Deployment URL (platform-aware defaults)
  static String get baseUrl {
    String url;
    if (_customBaseUrl != null && _customBaseUrl!.isNotEmpty) {
      url = _customBaseUrl!.trim();
    } else if (kIsWeb) {
      url = "http://127.0.0.1:8000";
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      url = "http://10.0.2.2:8000";
    } else {
      url = "http://localhost:8000";
    }
    // On web, localhost often causes "Failed to fetch" – use 127.0.0.1
    if (kIsWeb && url.contains('localhost') && url.contains('8000')) {
      return "http://127.0.0.1:8000";
    }
    return url;
  }

  /// Hint for connection errors: which URL to use for current platform
  static String get connectionHint {
    if (kIsWeb) {
      return "Use http://127.0.0.1:8000 and start backend with: python run.py (or uvicorn main:app --reload --host 0.0.0.0).";
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return "Use http://10.0.2.2:8000 for Emulator. For physical device use your PC's IP (e.g. http://192.168.1.x:8000). Start backend with: python run.py.";
    }
    return "Start backend with: python run.py from Final_Backend folder.";
  }

  // Login
  static Future<String?> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/auth/login-json"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "email": email,
          "password": password,
        }),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        String token = data["access_token"];
        
        // Save Token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        await prefs.setString('user_email', email);
        return null; // Success (no error)
      } else {
        // Try to parse error detail
        try {
          final body = jsonDecode(response.body);
          return body["detail"] ?? "Login Failed: ${response.statusCode}";
        } catch (_) {
          return "Login Failed: ${response.statusCode} ${response.reasonPhrase}";
        }
      }
    } on SocketException catch (_) {
      return "Connection Refused.\n\nCheck: \n1. Correct IP in Settings?\n2. Backend running?\n3. Phone/PC on same WiFi?";
    } on TimeoutException catch (_) {
      return "Connection Timed Out.\n\nCheck Firewall or IP reachability.";
    } catch (e) {
      debugPrint("Login Error: $e");
      return "Error: $e";
    }
  }

  // Register
  static Future<String?> register(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/auth/register"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "email": email,
          "password": password,
        }),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return null; // Success
      } else {
        final body = jsonDecode(response.body);
        return body["detail"] ?? "Registration Failed: ${response.statusCode}";
      }
    } on SocketException catch (_) {
      return "Connection Refused. Check Server IP.";
    } catch (e) {
      return "Error: $e";
    }
  }

  // Get Token
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  // Logout
  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    await prefs.remove('user_email');
  }

  static Future<String?> getUserEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('user_email');
  }

  // Google Login (Backend Verify)
  static Future<String?> googleLoginBackend(String idToken) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/auth/google"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "id_token": idToken,
        }),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        String token = data["access_token"];
        String email = data["email"];
        
        // Save Token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('auth_token', token);
        await prefs.setString('user_email', email);
        
        return null; // Success
      } else {
         try {
          final body = jsonDecode(response.body);
          return body["detail"] ?? "Google Login Failed: ${response.statusCode}";
        } catch (_) {
          return "Google Login Failed: ${response.statusCode}";
        }
      }
    } catch (e) {
      return "Error: $e";
    }
  }

  // Diagnostic: Test Connection
  static Future<String> testConnection() async {
    try {
      final response = await http.get(Uri.parse("$baseUrl/api-status")).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        return "SUCCESS: Connected to Backend!";
      } else {
        return "FAILED: Server returned ${response.statusCode}";
      }
    } catch (e) {
      return "FAILED: $e";
    }
  }
}
