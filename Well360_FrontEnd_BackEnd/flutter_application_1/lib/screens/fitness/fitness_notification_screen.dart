import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_application_1/services/api_service.dart';

class FitnessNotificationScreen extends StatefulWidget {
  const FitnessNotificationScreen({super.key});

  @override
  State<FitnessNotificationScreen> createState() => _FitnessNotificationScreenState();
}

class _FitnessNotificationScreenState extends State<FitnessNotificationScreen> {
  bool _isLoading = true;
  bool _isAnalyzing = false;
  List<dynamic> _notifications = [];

  @override
  void initState() {
    super.initState();
    _fetchNotifications();
  }

  Future<void> _fetchNotifications() async {
    setState(() => _isLoading = true);
    try {
      final notifs = await ApiService.getFitnessNotifications();
      setState(() {
        _notifications = notifs;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading notifications: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _analyzeFitness() async {
    setState(() => _isAnalyzing = true);
    try {
      await ApiService.analyzeFitness();
      await _fetchNotifications();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to analyze: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isAnalyzing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          'FITNESS ANALYSIS',
          style: GoogleFonts.orbitron(color: Colors.cyanAccent, fontWeight: FontWeight.bold),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white70),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: InkWell(
              onTap: _isAnalyzing ? null : _analyzeFitness,
              borderRadius: BorderRadius.circular(16),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.purpleAccent.withOpacity(0.3),
                      Colors.cyanAccent.withOpacity(0.3)
                    ],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.cyanAccent.withOpacity(0.5)),
                  boxShadow: [
                    BoxShadow(color: Colors.cyanAccent.withOpacity(0.1), blurRadius: 10)
                  ]
                ),
                child: Center(
                  child: _isAnalyzing 
                      ? const SizedBox(
                          width: 24, height: 24,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)
                        )
                      : Text(
                          "ANALYZE MY FITNESS",
                          style: GoogleFonts.orbitron(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 2
                          ),
                        ),
                ),
              ),
            ),
          ),
          Expanded(
            child: _isLoading 
                ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
                : _notifications.isEmpty 
                    ? Center(
                        child: Text(
                          "No analysis history yet.\nClick above to analyze your recent workouts.",
                          textAlign: TextAlign.center,
                          style: GoogleFonts.exo2(color: Colors.white54, fontSize: 16),
                        ),
                      )
                    : ListView.builder(
                        itemCount: _notifications.length,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        itemBuilder: (context, index) {
                          final notif = _notifications[index];
                          final exercises = List<String>.from(notif['exercises_analyzed'] ?? []);
                          final mappedExercises = exercises.isEmpty ? ["None"] : exercises;

                          return Container(
                            margin: const EdgeInsets.only(bottom: 16),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: Colors.white.withOpacity(0.1)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.analytics, color: Colors.purpleAccent),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        "SMART ANALYSIS",
                                        style: GoogleFonts.orbitron(
                                          color: Colors.cyanAccent,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    Text(
                                      _formatDate(notif['timestamp']),
                                      style: GoogleFonts.exo2(color: Colors.white54, fontSize: 12),
                                    )
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  notif['message'] ?? '',
                                  style: GoogleFonts.exo2(color: Colors.white, fontSize: 15, height: 1.5),
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  "ANALYZED EXERCISES:",
                                  style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 12),
                                ),
                                const SizedBox(height: 8),
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 8,
                                  children: mappedExercises.map((e) => Chip(
                                    label: Text(e.toUpperCase(), style: GoogleFonts.exo2(color: Colors.white, fontSize: 11)),
                                    backgroundColor: Colors.purpleAccent.withOpacity(0.2),
                                    side: BorderSide.none,
                                  )).toList(),
                                )
                              ],
                            ),
                          );
                        },
                      ),
          )
        ],
      )
    );
  }

  String _formatDate(String? isoString) {
    if (isoString == null) return "";
    try {
      final date = DateTime.parse(isoString).toLocal();
      return "${date.month}/${date.day} ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}";
    } catch (_) {
      return "";
    }
  }
}
