// lib/screens/hydration/hydration_home_screen.dart
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'form_screen.dart';
import 'lip_image_screen.dart';
import 'package:flutter_application_1/screens/history/history_screen.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';
import '../../services/hydration_results_service.dart' as import_services;
import 'combined_result_screen.dart' as import_results;


import 'package:flutter_application_1/services/api_service.dart';
import '../../services/notification_service.dart';

class HydrationHomeScreen extends StatefulWidget {
  const HydrationHomeScreen({super.key});

  @override
  State<HydrationHomeScreen> createState() => _HydrationHomeScreenState();
}

class _HydrationHomeScreenState extends State<HydrationHomeScreen> {
  Map<String, dynamic>? _dashboardData;
  bool _isLoading = true;

  List<String> _skippedHours = [];

  @override
  void initState() {
    super.initState();
    // Initialize & Schedule Notifications
    NotificationService().init().then((_) {
      NotificationService().scheduleDailyHourlyReminders();
    });
    
    _fetchDashboard();
  }

  Future<void> _fetchDashboard() async {
    try {
      final data = await ApiService.getDailyDashboard();
      final trends = await ApiService.getTrends(); // Fetch hourly trends
      
      if (mounted) {
        setState(() {
          _dashboardData = data;
          _isLoading = false;
          _calculateSkippedHours(trends['hourly']);
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false; 
        });
      }
      print("Dashboard Error: $e");
    }
  }

  void _calculateSkippedHours(List<dynamic>? hourlyData) {
    if (hourlyData == null) return;
    
    final now = DateTime.now();
    final currentHour = now.hour;
    List<String> skippedSlots = [];
    
    // Define time slots
    final slots = [
      {"name": "Midnight-4 AM", "start": 0, "end": 3},
      {"name": "4 AM-8 AM", "start": 4, "end": 7},
      {"name": "8 AM-12 PM", "start": 8, "end": 11},
      {"name": "12 PM-4 PM", "start": 12, "end": 15},
      {"name": "4 PM-8 PM", "start": 16, "end": 19},
      {"name": "8 PM-Midnight", "start": 20, "end": 23},
    ];
    
    // Check each time slot
    for (var slot in slots) {
      int start = slot["start"] as int;
      int end = slot["end"] as int;
      String slotName = slot["name"] as String;
      
      // Only check slots that have already passed
      // Skip if the current time hasn't reached the end of this slot
      if (currentHour < end) continue;
      
      // Check if ALL hours in this slot have zero intake
      bool allZero = true;
      for (int h = start; h <= end; h++) {
        final hourStr = "${h.toString().padLeft(2, '0')}:00";
        final entry = hourlyData.firstWhere(
          (e) => e['hour'] == hourStr, 
          orElse: () => null
        );
        
        double intake = 0.0;
        if (entry != null) {
          intake = (entry['liters'] is num) ? entry['liters'].toDouble() : 0.0;
        }
        
        if (intake > 0) {
          allZero = false;
          break;
        }
      }
      
      // If entire slot has zero intake, mark it as skipped
      if (allZero) {
        skippedSlots.add(slotName);
      }
    }
    
    _skippedHours = skippedSlots;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      extendBodyBehindAppBar: true,
      body: Stack(
        children: [
          // 1. Base Background
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
                   const SizedBox(height: 10),
                   
                   Text(
                    'HYDRATION\nMONITOR',
                    style: GoogleFonts.orbitron(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      letterSpacing: 2,
                      height: 1.1
                    ),
                    textAlign: TextAlign.center,
                  ),

                  const SizedBox(height: 20),

                  // ==========================
                  // NEW GOAL DASHBOARD CARD
                  // ==========================
                  _buildDashboardCard(),

                  const SizedBox(height: 20),

                  // ==========================
                  // SKIPPED HOURS WIDGET
                  // ==========================
                  if (_skippedHours.isNotEmpty)
                    _buildSkippedHoursCard(),

                  const SizedBox(height: 30),
                  
                  // Cards
                  const SizedBox(height: 20),

                  _buildMenuCard(
                    context,
                    title: "QUICK FORM LOG",
                    subtitle: "Record water intake & vitals",
                    icon: Icons.assignment_outlined,
                    color: Colors.cyanAccent,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const FormScreen()),
                    ).then((_) => _fetchDashboard()), // Refresh on return
                  ),
                   const SizedBox(height: 20),
                  _buildMenuCard(
                    context,
                    title: "LIP SCAN ONLY",
                    subtitle: "AI dehydration detection",
                    icon: Icons.face_retouching_natural,
                    color: Colors.blueAccent,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const LipImageScreen()),
                    ).then((_) => _fetchDashboard()), // Refresh on return
                  ),

                  const SizedBox(height: 20),
                  
                  const SizedBox(height: 20),
                  
                  _buildLatestResultButton(context),

                  const SizedBox(height: 20),

                  _buildMenuCard(
                    context,
                    title: "HISTORY & TRENDS",
                    subtitle: "View logs and analysis",
                    icon: Icons.history,
                    color: Colors.purpleAccent,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const HistoryScreen()),
                    ),
                  ),
                  
                  const SizedBox(height: 40),                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  // ... _buildDashboardCard

  Widget _buildSkippedHoursCard() {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: Colors.redAccent.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.redAccent.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: Colors.orangeAccent, size: 20),
              const SizedBox(width: 10),
              Text(
                "MISSED TIME SLOTS",
                style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _skippedHours.map((h) => 
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.red.withValues(alpha: 0.3))
                ),
                child: Text(h, style: GoogleFonts.exo2(color: Colors.white, fontWeight: FontWeight.bold)),
              )
            ).toList(),
          )
        ],
      ),
    );
  }

  // ... rest of class


  Widget _buildDashboardCard() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Colors.cyanAccent));
    }
    
    // Default values if data is missing or error
    double total = _dashboardData?['total_water_intake_today_liters'] ?? 0.0;
    double goal = _dashboardData?['daily_goal_liters'] ?? 3.0;
    double percent = _dashboardData?['percentage_completed'] ?? 0.0;
    String status = _dashboardData?['goal_status'] ?? "Track to see status";
    var lipStatus = _dashboardData?['current_lip_status'];

    // Clamp percent for UI (0 to 1)
    double progressValue = (percent / 100).clamp(0.0, 1.0);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(30),
        gradient: LinearGradient(
          colors: [Colors.blueAccent.withValues(alpha: 0.2), Colors.cyanAccent.withValues(alpha: 0.1)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight
        ),
        border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("DAILY GOAL", style: GoogleFonts.orbitron(color: Colors.white70, fontSize: 14)),
              Text("$total / $goal L", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 15),
          LinearProgressIndicator(
            value: progressValue,
            backgroundColor: Colors.white10,
            color: progressValue >= 1.0 ? Colors.greenAccent : Colors.cyanAccent,
            minHeight: 10,
            borderRadius: BorderRadius.circular(5),
          ),
          const SizedBox(height: 15),
          Text(status, style: GoogleFonts.exo2(color: Colors.white, fontSize: 16)),
          
          if (lipStatus != null && lipStatus['status'] != "Unknown") ...[
            const Divider(color: Colors.white24, height: 30),
             Row(
              children: [
                const Icon(Icons.face, color: Colors.orangeAccent, size: 20),
                const SizedBox(width: 10),
                Text("Lip Status: ", style: GoogleFonts.exo2(color: Colors.white70)),
                Text(
                  "${lipStatus['status']} (${lipStatus['score']})",
                  style: GoogleFonts.orbitron(color: Colors.orangeAccent, fontWeight: FontWeight.bold)
                ),
              ],
            )
          ]
        ],
      ),
    );
  }

  Widget _buildMenuCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(24),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: color.withValues(alpha: 0.3)),
                boxShadow: [
                  BoxShadow(color: color.withValues(alpha: 0.05), blurRadius: 20, offset: const Offset(0, 10))
                ]
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.1),
                      shape: BoxShape.circle,
                      boxShadow: [BoxShadow(color: color.withValues(alpha: 0.2), blurRadius: 10)]
                    ),
                    child: Icon(icon, color: color, size: 32),
                  ),
                  const SizedBox(width: 20),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: GoogleFonts.orbitron(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 1
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          subtitle,
                          style: GoogleFonts.exo2(
                            fontSize: 13,
                            color: Colors.white60,
                            ),
                        ),
                      ],
                    ),
                  ),
                  Icon(Icons.arrow_forward_ios_rounded, color: color.withValues(alpha: 0.5), size: 16),
                ],
              ),
            ),
          ),
        ),
      );
  }

  Widget _buildLatestResultButton(BuildContext context) {
    // Quick check:
    final service = import_services.HydrationResultsService();
    // if (!service.hasFormResult && !service.hasLipResult) return const SizedBox.shrink(); // Always show now

    return _buildMenuCard(
      context,
      title: "VIEW COMPARISON",
      subtitle: "See latest analysis results",
      icon: Icons.analytics_outlined,
      color: Colors.greenAccent,
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => import_results.CombinedResultScreen(
              formResult: service.formResult,
              lipResult: service.lipResult,
              userName: service.userName,
            ),
          ),
        );
      },
    );
  }
}
