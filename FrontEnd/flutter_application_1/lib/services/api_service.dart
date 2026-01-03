import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart'; // kIsWeb
import 'package:http/http.dart' as http;

class ApiService {
  // 🔴 CHANGE IP IF NEEDED
  static const String baseUrl = "http://172.20.10.2:8000";

  // =====================================================
  // FORM-BASED HYDRATION PREDICTION
  // =====================================================
  static Future<Map<String, dynamic>> predictHydration(
    Map<String, dynamic> data,
  ) async {
    final res = await http.post(
      Uri.parse("$baseUrl/predict/form"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(data),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Hydration prediction failed (${res.statusCode})");
    }
  }

  // =====================================================
  // LIP IMAGE PREDICTION (AUTO PLATFORM)
  // =====================================================
  static Future<Map<String, dynamic>> predictLip({
    File? imageFile, // Mobile
    Uint8List? webImage, // Web
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
  static Future<Map<String, dynamic>> _predictLipMobile(File image) async {
    final request = http.MultipartRequest(
      "POST",
      Uri.parse("$baseUrl/predict/lip/mobile"),
    );

    request.files.add(await http.MultipartFile.fromPath("file", image.path));

    final response = await request.send();
    final body = await response.stream.bytesToString();

    if (response.statusCode == 200) {
      return jsonDecode(body);
    } else {
      throw Exception("Lip prediction failed (${response.statusCode})");
    }
  }

  // =====================================================
  // WEB (BASE64 JSON)
  // =====================================================
  static Future<Map<String, dynamic>> _predictLipWeb(
    Uint8List imageBytes,
  ) async {
    final base64Image = base64Encode(imageBytes);

    final res = await http.post(
      Uri.parse("$baseUrl/predict/lip/web"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"image_base64": base64Image}),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    } else {
      throw Exception("Lip prediction failed (${res.statusCode})");
    }
  }
}
