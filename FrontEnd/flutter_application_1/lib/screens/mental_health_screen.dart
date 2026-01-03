import 'package:flutter/material.dart';

class MentalHealthScreen extends StatelessWidget {
  const MentalHealthScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mental Health Assessment")),
      body: const Center(
        child: Text("Mental health module (Under development)"),
      ),
    );
  }
}
