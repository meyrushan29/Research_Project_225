// lib/screens/hydration/combined_result_screen.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';

class CombinedResultScreen extends StatelessWidget {
  final Map<String, dynamic> formResult;
  final Map<String, dynamic>? lipResult;
  final String userName;

  const CombinedResultScreen({
    super.key,
    this.formResult = const {},
    this.lipResult,
    this.userName = "Merus",
  });

  @override
  Widget build(BuildContext context) {
    // ---------------- Data Extraction ----------------
    final bool hasForm = formResult.isNotEmpty;
    final bool hasLip = lipResult != null && lipResult!.isNotEmpty;

    // 1. Water Need (Form)
    double waterNeed = 0.0;
    if (hasForm && formResult.containsKey('recommended_total_water_liters')) {
      final val = formResult['recommended_total_water_liters'];
      if (val is num) {
        waterNeed = val.toDouble();
      } else if (val is String) {
        waterNeed = double.tryParse(val) ?? 0.0;
      }
    }
    
    // 2. Lip Score (Image)
    int lipScore = 0;
    String lipStatus = "N/A";
    
    if (hasLip) {
      if (lipResult!.containsKey('hydration_score')) {
         final val = lipResult!['hydration_score'];
         if (val is num) {
           lipScore = val.toInt();
         } else if (val is String) {
           lipScore = int.tryParse(val) ?? 0;
         }
      }
      lipStatus = lipResult!['prediction']?.toString() ?? "Unknown";
    }

    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: Stack(
        children: [
          // Background
           Container(
             decoration: const BoxDecoration(
               gradient: LinearGradient(
                 begin: Alignment.topCenter,
                 end: Alignment.bottomCenter,
                 colors: [Color(0xFF050505), Color(0xFF101015)],
               ),
             ),
          ),
          Positioned.fill(
            child: Opacity(
              opacity: 0.1,
              child: CustomPaint(painter: GridPainter()),
            ),
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 20),
                  
                  // Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      IconButton(
                        onPressed: () => Navigator.pop(context), 
                        icon: const Icon(Icons.close, color: Colors.white70)
                      ),
                      Text(
                        "ANALYSIS RESULT",
                        style: GoogleFonts.orbitron(
                          color: Colors.white, 
                          fontSize: 16, 
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2
                        ),
                      ),
                      const SizedBox(width: 40), // Balance
                    ],
                  ),

                  const SizedBox(height: 40),

                  Text(
                    "Here is your hydration breakdown.",
                    style: GoogleFonts.exo2(color: Colors.white60, fontSize: 16),
                    textAlign: TextAlign.center,
                  ),

                  const SizedBox(height: 40),

                  // ===============================
                  // METRIC 1: WATER NEED (FORM)
                  // ===============================
                  if (hasForm)
                    _buildBigMetricCard(
                      title: "NEXT 4 HOURS NEED",
                      value: "${waterNeed.toStringAsFixed(1)} L",
                      subtitle: "Based on your body metrics & activity",
                      icon: Icons.water_drop,
                      color: Colors.cyanAccent,
                    )
                  else
                    _buildMissingDataCard("Water Need Data Missing", Colors.cyanAccent),

                  const SizedBox(height: 24),

                  // ===============================
                  // METRIC 2: LIP SCORE (IMAGE)
                  // ===============================
                  if (hasLip)
                    _buildBigMetricCard(
                      title: "LIP HYDRATION SCORE",
                      value: "$lipScore / 100",
                      subtitle: "Status: $lipStatus",
                      icon: Icons.face_retouching_natural,
                      color: lipScore > 75 ? Colors.greenAccent : Colors.orangeAccent,
                    )
                  else
                    _buildMissingDataCard("Lip Scan Data Missing", Colors.orangeAccent),

                  const SizedBox(height: 50),

                  // Action Button
                  Container(
                    decoration: BoxDecoration(
                      boxShadow: [BoxShadow(color: Colors.white.withValues(alpha: 0.1), blurRadius: 20, spreadRadius: 0)]
                    ),
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(vertical: 20),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        elevation: 0
                      ),
                      child: Text(
                        "DONE", 
                        style: GoogleFonts.orbitron(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1)
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 40),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildBigMetricCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: color.withValues(alpha: 0.3)),
        boxShadow: [
          BoxShadow(color: color.withValues(alpha: 0.05), blurRadius: 30, spreadRadius: 5)
        ]
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 40),
          ),
          const SizedBox(height: 20),
          Text(
            title,
            style: GoogleFonts.orbitron(color: Colors.white60, fontSize: 12, letterSpacing: 1, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Text(
            value,
            style: GoogleFonts.orbitron(color: Colors.white, fontSize: 40, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 10),
          Text(
            subtitle,
            style: GoogleFonts.exo2(color: Colors.white70, fontSize: 14),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildMissingDataCard(String text, Color color) {
    return Container(
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      ),
      child: Column(
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.white24, size: 40),
           const SizedBox(height: 10),
          Text(text, style: GoogleFonts.exo2(color: Colors.white24)),
        ],
      ),
    );
  }
}
