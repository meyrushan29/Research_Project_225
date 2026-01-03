import 'package:flutter/material.dart';
import 'screens/home_screen_comman.dart';

void main() {
  runApp(const HealthAnalyzerApp());
}

class HealthAnalyzerApp extends StatelessWidget {
  const HealthAnalyzerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'AI Health Analyzer',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const HomeScreen(),
    );
  }
}
