import 'dart:convert';

import 'package:flutter/foundation.dart'; // kIsWeb
import 'package:http/http.dart' as http;
import 'package:flutter_application_1/services/auth_service.dart';
import 'package:image_picker/image_picker.dart'; // Use XFile

class ApiService {
  // Unified Deployment URL
  // Uses AuthService.baseUrl for unified configuration
  static String get baseUrl => AuthService.baseUrl;

  // =====================================================
  // FORM-BASED HYDRATION PREDICTION
  // =====================================================
  static Future<Map<String, dynamic>> predictHydration(
    Map<String, dynamic> data,
  ) async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final res = await http.post(
      Uri.parse("$baseUrl/predict/form"),
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
      body: jsonEncode(data),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Error ${res.statusCode}: ${res.body}");
    }
  }

  // =====================================================
  // GET USER PROFILE
  // =====================================================
  static Future<Map<String, dynamic>> getProfile() async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final res = await http.get(
      Uri.parse("$baseUrl/auth/profile"),
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Failed to load profile");
    }
  }

  // =====================================================
  // GET DAILY DASHBOARD
  // =====================================================
  static Future<Map<String, dynamic>> getDailyDashboard() async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final res = await http.get(
      Uri.parse("$baseUrl/tracker/dashboard"),
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Failed to load dashboard: ${res.body}");
    }
  }

  // =====================================================
  // GET TRENDS (WEEKLY/MONTHLY)
  // =====================================================
  static Future<Map<String, dynamic>> getTrends() async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final res = await http.get(
      Uri.parse("$baseUrl/history/trends"),
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Failed to load trends: ${res.body}");
    }
  }

  // =====================================================
  // GET CURRENT WEATHER
  // =====================================================
  static Future<Map<String, dynamic>> getWeather(double lat, double lon) async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final res = await http.get(
      Uri.parse("$baseUrl/weather/current?lat=$lat&lon=$lon"),
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Failed to fetch weather: ${res.body}");
    }
  }

  // =====================================================
  // LIP IMAGE PREDICTION (AUTO PLATFORM)
  // =====================================================
  static Future<Map<String, dynamic>> predictLip({
    XFile? imageFile, // Mobile/Web abstract
    Uint8List? webImage, // Web bytes
  }) async {
    if (kIsWeb) {
      if (webImage == null) {
        throw Exception("Web image bytes missing");
      }
      return _predictLipWeb(webImage);
    } else {
      if (imageFile == null) {
        throw Exception("Image file missing");
      }
      return _predictLipMobile(imageFile);
    }
  }

  // =====================================================
  // MOBILE (MULTIPART)
  // =====================================================
  // =====================================================
  // MOBILE (BASE64 JSON - UNIFIED)
  // =====================================================
  static Future<Map<String, dynamic>> _predictLipMobile(XFile image) async {
    final token = await AuthService.getToken();
    final bytes = await image.readAsBytes();
    final base64Image = base64Encode(bytes);

    return _sendLipRequest(token, base64Image);
  }

  // =====================================================
  // WEB (BASE64 JSON - UNIFIED)
  // =====================================================
  static Future<Map<String, dynamic>> _predictLipWeb(
    Uint8List imageBytes,
  ) async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final base64Image = base64Encode(imageBytes);
    return _sendLipRequest(token, base64Image);
  }

  // Shared Request Logic
  static Future<Map<String, dynamic>> _sendLipRequest(String? token, String base64Image) async {
    final res = await http.post(
      Uri.parse("$baseUrl/predict/lip"),
      headers: {
        "Content-Type": "application/json",
        if (token != null) "Authorization": "Bearer $token",
      },
      body: jsonEncode({"image_base64": base64Image}),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Lip prediction failed (${res.statusCode}): ${res.body}");
    }
  }

  // =====================================================
  // FITNESS VIDEO ANALYSIS
  // =====================================================
  static Future<Map<String, dynamic>> predictFitnessVideo(
    String videoIdentifier, {
    Uint8List? webBytes,
  }) async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final uri = Uri.parse("$baseUrl/predict/fitness/video");
    final request = http.MultipartRequest("POST", uri);
    
    request.headers["Authorization"] = "Bearer $token";
    
    if (kIsWeb && webBytes != null) {
       // Web Upload via Bytes
       request.files.add(http.MultipartFile.fromBytes(
         'video',
         webBytes,
         filename: videoIdentifier, // passed as name
       ));
    } else {
       // Mobile/Desktop Upload via Path
       request.files.add(await http.MultipartFile.fromPath(
        'video',
        videoIdentifier, // passed as path
      ));
    }

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception("Fitness analysis failed (${response.statusCode}): ${response.body}");
    }
  }

  // =====================================================
  // LIP ANALYSIS TRENDS
  // =====================================================
  static Future<Map<String, dynamic>> getLipTrends() async {
    final token = await AuthService.getToken();
    if (token == null) throw Exception("Please login first");

    final res = await http.get(
      Uri.parse("$baseUrl/history/lip-trends"),
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer $token",
      },
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Failed to load lip trends: ${res.body}");
    }
  }
}
