import 'package:flutter/material.dart';
import 'form_screen.dart';
import 'lip_image_screen.dart';

class HydrationHomeScreen extends StatelessWidget {
  const HydrationHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFE3F2FD), Color(0xFFE0F7FA), Color(0xFFE0F2F1)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              const SizedBox(height: 60),
              const Icon(Icons.water_drop, size: 80, color: Colors.blue),
              const SizedBox(height: 16),
              const Text(
                'Hydration Checker',
                style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 40),
                child: Text(
                  'Monitor hydration and maintain optimal health',
                  textAlign: TextAlign.center,
                ),
              ),
              const Spacer(),
              _button(
                context,
                "Hydration Form",
                Icons.assignment,
                () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const FormScreen()),
                ),
              ),
              const SizedBox(height: 20),
              _button(
                context,
                "Lip Image Prediction",
                Icons.camera_alt,
                () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const LipImageScreen()),
                ),
              ),
              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _button(
    BuildContext context,
    String text,
    IconData icon,
    VoidCallback onTap,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: ElevatedButton.icon(
        icon: Icon(icon),
        label: Text(text),
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(double.infinity, 56),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        onPressed: onTap,
      ),
    );
  }
}
