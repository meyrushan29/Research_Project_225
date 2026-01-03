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
      theme: ThemeData(
        useMaterial3: true,
        primaryColor: const Color(0xFF1E88E5),
        scaffoldBackgroundColor: const Color(0xFFF5F7FA),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1E88E5),
          foregroundColor: Colors.white,
          centerTitle: true,
        ),
      ),
      home: const HomeScreenCommon(),
    );
  }
}
