import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';
import 'combined_result_screen.dart';

class LipImageScreen extends StatefulWidget {
  const LipImageScreen({super.key});

  @override
  State<LipImageScreen> createState() => _LipImageScreenState();
}

class _LipImageScreenState extends State<LipImageScreen> {
  File? image;
  Uint8List? webImage;
  bool loading = false;

  // --------------------------------------------------
  // Pick Image (All Platforms)
  // --------------------------------------------------
  Future<void> pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: source);

    if (picked == null) return;

    if (kIsWeb) {
      webImage = await picked.readAsBytes();
      image = null;
    } else {
      image = File(picked.path);
      webImage = null;
    }

    setState(() {});
  }

  // --------------------------------------------------
  // Submit Image (Web + Mobile)
  // --------------------------------------------------
  Future<void> submit() async {
    if (!kIsWeb && image == null) return;
    if (kIsWeb && webImage == null) return;

    setState(() => loading = true);

    try {
      final result = await ApiService.predictLip(
        imageFile: image,
        webImage: webImage,
      );

      setState(() => loading = false);

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) =>
              CombinedResultScreen(formResult: {}, lipResult: result),
        ),
      );
    } catch (e) {
      setState(() => loading = false);
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Prediction failed: $e"),
          backgroundColor: Colors.red.shade600,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  // --------------------------------------------------
  // UI
  // --------------------------------------------------
  @override
  Widget build(BuildContext context) {
    final hasImage = (kIsWeb && webImage != null) || (!kIsWeb && image != null);

    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text("Lip Analysis"),
        elevation: 0,
        backgroundColor: Colors.teal.shade600,
        foregroundColor: Colors.white,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
              decoration: BoxDecoration(
                color: Colors.teal.shade600,
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(30),
                  bottomRight: Radius.circular(30),
                ),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.camera_alt_outlined,
                    size: 48,
                    color: Colors.white.withOpacity(0.9),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Lip Hydration Analysis',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Upload a clear photo of your lips for AI-powered hydration assessment',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Content Section
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  // Image Preview Card
                  Container(
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.05),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(20),
                      child: hasImage
                          ? _buildImagePreview()
                          : _buildPlaceholder(),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Instructions Card
                  if (!hasImage) _buildInstructionsCard(),

                  const SizedBox(height: 24),

                  // Action Buttons
                  if (!hasImage) _buildImageSourceButtons(),

                  // Analyze Button (shown when image is selected)
                  if (hasImage) ...[
                    _buildAnalyzeButton(),
                    const SizedBox(height: 16),
                    _buildRetakeButton(),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // --------------------------------------------------
  // UI Components
  // --------------------------------------------------

  Widget _buildImagePreview() {
    return Stack(
      children: [
        Container(
          height: 320,
          width: double.infinity,
          child: kIsWeb
              ? Image.memory(webImage!, fit: BoxFit.cover)
              : Image.file(image!, fit: BoxFit.cover),
        ),
        Positioned(
          top: 12,
          right: 12,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.green.shade500,
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.check_circle, color: Colors.white, size: 16),
                SizedBox(width: 6),
                Text(
                  'Image Ready',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      height: 320,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.add_photo_alternate_outlined,
            size: 80,
            color: Colors.grey.shade300,
          ),
          const SizedBox(height: 16),
          Text(
            'No Image Selected',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Choose a method below to get started',
            style: TextStyle(fontSize: 14, color: Colors.grey.shade500),
          ),
        ],
      ),
    );
  }

  Widget _buildInstructionsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.teal.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.teal.shade100),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb_outline, color: Colors.teal.shade700),
              const SizedBox(width: 8),
              Text(
                'Tips for Best Results',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.teal.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildTipItem('Good lighting - avoid shadows'),
          _buildTipItem('Close-up of lips only'),
          _buildTipItem('Natural expression, no smile'),
          _buildTipItem('Remove lipstick or gloss'),
        ],
      ),
    );
  }

  Widget _buildTipItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(Icons.check_circle, size: 16, color: Colors.teal.shade600),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: 14, color: Colors.grey.shade700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildImageSourceButtons() {
    return Column(
      children: [
        // Camera Button
        if (!kIsWeb)
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton.icon(
              onPressed: () => pickImage(ImageSource.camera),
              icon: const Icon(Icons.camera_alt, size: 24),
              label: const Text(
                'Take Photo',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.teal.shade600,
                foregroundColor: Colors.white,
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
          ),
        if (!kIsWeb) const SizedBox(height: 12),
        // Gallery Button
        SizedBox(
          width: double.infinity,
          height: 56,
          child: ElevatedButton.icon(
            onPressed: () => pickImage(ImageSource.gallery),
            icon: const Icon(Icons.photo_library, size: 24),
            label: const Text(
              'Choose from Gallery',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: Colors.teal.shade600,
              elevation: 2,
              side: BorderSide(color: Colors.teal.shade600, width: 2),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAnalyzeButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: loading ? null : submit,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.teal.shade600,
          foregroundColor: Colors.white,
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          disabledBackgroundColor: Colors.grey.shade300,
        ),
        child: loading
            ? const SizedBox(
                height: 24,
                width: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.analytics_outlined, size: 24),
                  SizedBox(width: 12),
                  Text(
                    'Analyze Hydration',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildRetakeButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: OutlinedButton.icon(
        onPressed: loading ? null : () => pickImage(ImageSource.gallery),
        icon: const Icon(Icons.refresh, size: 24),
        label: const Text(
          'Choose Different Image',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.teal.shade600,
          side: BorderSide(color: Colors.teal.shade300, width: 2),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
    );
  }
}
