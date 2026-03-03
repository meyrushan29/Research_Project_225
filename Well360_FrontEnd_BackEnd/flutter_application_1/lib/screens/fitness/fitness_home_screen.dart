// lib/screens/fitness/fitness_home_screen.dart
import 'dart:ui';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_application_1/services/api_service.dart';
import 'processing_screen.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';
import '../profile/profile_screen.dart';
import 'fitness_history_screen.dart';
import 'fitness_notification_screen.dart';
import 'fitness_progress_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  PlatformFile? selectedVideoFile;
  String? videoName;
  String? videoSource;
  Map<String, dynamic>? _recommendation;
  bool _isLoadingRec = true;
  List<dynamic> _recentHistory = [];
  bool _isLoadingHistory = true;

  @override
  void initState() {
    super.initState();
    _fetchRecommendation();
    _fetchRecentHistory();
  }

  Future<void> _fetchRecommendation() async {
     try {
       final rec = await ApiService.getFitnessRecommendation();
       if (mounted) {
         setState(() {
           _recommendation = rec;
           _isLoadingRec = false;
         });
       }
     } catch (e) {
       debugPrint("Failed to load recommendation: $e");
       if (mounted) setState(() => _isLoadingRec = false);
     }
  }

  Future<void> _fetchRecentHistory() async {
    try {
      final history = await ApiService.getFitnessHistory(limit: 3);
      if (mounted) {
        setState(() {
          _recentHistory = history;
          _isLoadingHistory = false;
        });
      }
    } catch (e) {
      debugPrint("Failed to load history: $e");
      if (mounted) setState(() => _isLoadingHistory = false);
    }
  }

  Future<void> uploadVideo() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.video,
        allowMultiple: false,
        withData: kIsWeb,
      );
      
      if (result != null) {
        setState(() {
          selectedVideoFile = result.files.single;
          videoName = result.files.single.name;
          videoSource = 'upload';
        });
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Row(
                children: [
                  const Icon(Icons.check_circle, color: Colors.black),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text('Video selected: ${result.files.single.name}', style: const TextStyle(color: Colors.black)),
                  ),
                ],
              ),
              backgroundColor: Colors.cyanAccent,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              duration: const Duration(seconds: 2),
            ),
          );
        }
        navigateToProcessing();
      }
    } catch (e) {
      _showError('Failed to upload video: ${e.toString()}');
    }
  }

  Future<void> recordLiveVideo() async {
    if (kIsWeb) {
      _showError('Camera recording not supported on web. Please use mobile app.');
      return;
    }

    try {
      final ImagePicker picker = ImagePicker();
      final XFile? video = await picker.pickVideo(
        source: ImageSource.camera,
        maxDuration: const Duration(minutes: 5),
      );
      
      if (video != null) {
        setState(() {
          videoName = video.name;
          videoSource = 'camera';
          selectedVideoFile = PlatformFile(
            name: video.name,
            size: 0,
            path: video.path,
          );
        });
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Row(
                children: [
                   Icon(Icons.check_circle, color: Colors.black),
                   SizedBox(width: 8),
                  Expanded(
                    child: Text('Video recorded successfully!', style: TextStyle(color: Colors.black)),
                  ),
                ],
              ),
              backgroundColor: Colors.cyanAccent,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              duration: const Duration(seconds: 2),
            ),
          );
        }
        navigateToProcessing();
      }
    } catch (e) {
       _showError('Failed to record video: ${e.toString()}');
    }
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              const Icon(Icons.error, color: Colors.white),
              const SizedBox(width: 8),
              Expanded(child: Text(message)),
            ],
          ),
          backgroundColor: Colors.redAccent,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
    }
  }

  void navigateToProcessing() {
    if (selectedVideoFile == null) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ProcessingScreen(
          videoFile: selectedVideoFile!,
          videoName: videoName ?? 'workout.mp4',
          videoSource: videoSource ?? 'upload',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white70),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          'FITNESS',
          style: GoogleFonts.orbitron(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
            letterSpacing: 2,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline_rounded, color: Colors.cyanAccent, size: 22),
            tooltip: 'Profile',
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
          ),
        ],
      ),
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF050505), Color(0xFF101015)],
              ),
            ),
          ),
          Positioned.fill(
            child: Opacity(
              opacity: 0.15,
              child: CustomPaint(painter: GridPainter()),
            ),
          ),
          // Ambient glow
          Positioned(
            top: -80,
            right: -60,
            child: Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.cyanAccent.withValues(alpha: 0.06),
                boxShadow: [
                  BoxShadow(color: Colors.cyanAccent.withValues(alpha: 0.08), blurRadius: 80, spreadRadius: 40),
                ],
              ),
            ),
          ),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 8),
                  // ─── Welcome Banner ───
                  _buildWelcomeBanner(),
                  const SizedBox(height: 20),

                  // ─── Capabilities (at top) ───
                  _buildCapabilitiesRow(),
                  const SizedBox(height: 24),

                  // ─── Action Buttons (Upload / Record) ───
                  _buildSectionLabel("START WORKOUT ANALYSIS", Icons.play_circle_outline, Colors.cyanAccent),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(child: _buildActionButton(
                        icon: Icons.upload_file_rounded,
                        label: "UPLOAD",
                        subtitle: "From gallery",
                        color: Colors.cyanAccent,
                        onTap: uploadVideo,
                      )),
                      const SizedBox(width: 12),
                      Expanded(child: _buildActionButton(
                        icon: Icons.videocam_rounded,
                        label: "RECORD",
                        subtitle: "Live camera",
                        color: Colors.purpleAccent,
                        onTap: recordLiveVideo,
                      )),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // ─── Quick Nav Cards ───
                  _buildSectionLabel("EXPLORE", Icons.dashboard_rounded, Colors.white54),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(child: _buildNavCard(
                        icon: Icons.trending_up_rounded,
                        label: "Progress",
                        color: Colors.greenAccent,
                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FitnessProgressScreen())),
                      )),
                      const SizedBox(width: 10),
                      Expanded(child: _buildNavCard(
                        icon: Icons.history_rounded,
                        label: "History",
                        color: Colors.purpleAccent,
                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FitnessHistoryScreen())),
                      )),
                      const SizedBox(width: 10),
                      Expanded(child: _buildNavCard(
                        icon: Icons.analytics_rounded,
                        label: "Analyze",
                        color: Colors.orangeAccent,
                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FitnessNotificationScreen())),
                      )),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // ─── Recent Activity ───
                  if (_recentHistory.isNotEmpty) ...[
                    _buildSectionLabel("RECENT WORKOUTS", Icons.fitness_center_rounded, Colors.white54),
                    const SizedBox(height: 12),
                    ..._recentHistory.map((session) => _buildRecentSessionCard(session)),
                    const SizedBox(height: 24),
                  ],

                  const SizedBox(height: 30),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ═══════════════════════════════════════
  // WIDGETS
  // ═══════════════════════════════════════

  Widget _buildWelcomeBanner() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: LinearGradient(
          colors: [
            Colors.cyanAccent.withValues(alpha: 0.08),
            Colors.purpleAccent.withValues(alpha: 0.04),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "AI Form Analysis",
            style: GoogleFonts.orbitron(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            "Upload or record a workout video for AI-powered pose detection, form correction & rep counting.",
            style: GoogleFonts.exo2(
              fontSize: 14,
              color: Colors.white54,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionLabel(String text, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, color: color, size: 18),
        const SizedBox(width: 8),
        Text(
          text,
          style: GoogleFonts.orbitron(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: color,
            letterSpacing: 1.5,
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color.withValues(alpha: 0.25)),
            boxShadow: [
              BoxShadow(color: color.withValues(alpha: 0.05), blurRadius: 12, offset: const Offset(0, 4)),
            ],
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: color.withValues(alpha: 0.15), blurRadius: 10),
                  ],
                ),
                child: Icon(icon, size: 28, color: color),
              ),
              const SizedBox(height: 12),
              Text(
                label,
                style: GoogleFonts.orbitron(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: GoogleFonts.exo2(fontSize: 13, color: Colors.white38),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecommendationCard() {
    final String message = _recommendation!['message'] ?? "Keep it up!";
    final List<dynamic> suggested = _recommendation!['suggested_exercises'] ?? [];
    final String target = _recommendation!['target_part'] ?? "General";

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: _showRecommendationDialog,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.purpleAccent.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.purpleAccent.withValues(alpha: 0.2)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.purpleAccent.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.auto_awesome, color: Colors.purpleAccent, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          "AI RECOMMENDATION",
                          style: GoogleFonts.orbitron(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Colors.purpleAccent,
                            letterSpacing: 1,
                          ),
                        ),
                        const Icon(Icons.arrow_forward_ios, color: Colors.purpleAccent, size: 12),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      message,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.exo2(color: Colors.white70, fontSize: 12, height: 1.4),
                    ),
                    if (suggested.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: suggested.take(3).map((e) => Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.06),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            e.toString(),
                            style: GoogleFonts.exo2(color: Colors.white54, fontSize: 10),
                          ),
                        )).toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavCard({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: color.withValues(alpha: 0.15)),
          ),
          child: Column(
            children: [
              Icon(icon, color: color, size: 26),
              const SizedBox(height: 8),
              Text(
                label,
                style: GoogleFonts.exo2(
                  color: Colors.white70,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecentSessionCard(dynamic session) {
    final exercise = _formatExerciseName(session['exercise']);
    final form = session['form'] as String? ?? 'unknown';
    final reps = session['reps_total'] ?? 0;
    final confidence = session['confidence']?.toInt() ?? 0;
    
    final Color formColor;
    final IconData formIcon;
    if (form == 'correct') {
      formColor = Colors.greenAccent;
      formIcon = Icons.check_circle;
    } else if (form == 'wrong') {
      formColor = Colors.redAccent;
      formIcon = Icons.cancel;
    } else {
      formColor = Colors.orangeAccent;
      formIcon = Icons.help_outline;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
      ),
      child: Row(
        children: [
          Icon(formIcon, color: formColor, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              exercise,
              style: GoogleFonts.exo2(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "$reps reps",
                style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 12),
              ),
              const SizedBox(height: 2),
              Text(
                "$confidence%",
                style: GoogleFonts.orbitron(color: Colors.cyanAccent, fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCapabilitiesRow() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.02),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
      ),
      child: Column(
        children: [
          Text(
            "CAPABILITIES",
            style: GoogleFonts.orbitron(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.white38,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildCapabilityIcon(Icons.sports_gymnastics, "Exercise\nID", Colors.cyanAccent),
              _buildCapabilityIcon(Icons.check_circle, "Form\nCheck", Colors.purpleAccent),
              _buildCapabilityIcon(Icons.repeat, "Rep\nCount", Colors.blueAccent),
              _buildCapabilityIcon(Icons.whatshot, "Heatmap\nView", Colors.orangeAccent),
              _buildCapabilityIcon(Icons.psychology, "XAI\nAnalysis", Colors.deepPurpleAccent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCapabilityIcon(IconData icon, String label, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 22),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          textAlign: TextAlign.center,
          style: GoogleFonts.exo2(
            color: Colors.white38,
             fontSize: 11,
            height: 1.3,
          ),
        ),
      ],
    );
  }

  String _formatExerciseName(String? name) {
    if (name == null || name.isEmpty || name == 'unknown') return 'Unknown';
    String cleaned = name;
    if (cleaned.endsWith('_correct')) cleaned = cleaned.substring(0, cleaned.length - 8);
    if (cleaned.endsWith('_wrong'))   cleaned = cleaned.substring(0, cleaned.length - 6);
    return cleaned
        .split('_')
        .map((word) => word.isNotEmpty ? '${word[0].toUpperCase()}${word.substring(1)}' : '')
        .join(' ');
  }

  void _showRecommendationDialog() {
    if (_recommendation == null) {
      if (_isLoadingRec) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("No recommendations yet. Start working out!")));
      return;
    }

    final String message = _recommendation!['message'] ?? "Keep it up!";
    final List<dynamic> suggested = _recommendation!['suggested_exercises'] ?? [];
    final String target = _recommendation!['target_part'] ?? "General";

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E1E),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: Row(
          children: [
             Container(
               padding: const EdgeInsets.all(8),
               decoration: BoxDecoration(color: Colors.purpleAccent.withOpacity(0.2), shape: BoxShape.circle),
               child: const Icon(Icons.auto_awesome, color: Colors.purpleAccent),
             ),
             const SizedBox(width: 12),
             Expanded(child: Text('AI TRAINER', style: GoogleFonts.orbitron(color: Colors.white, fontSize: 18))),
          ],
        ),
        content: Column(
           mainAxisSize: MainAxisSize.min,
           crossAxisAlignment: CrossAxisAlignment.start,
           children: [
             Text(
               message,
               style: GoogleFonts.exo2(color: Colors.white70, fontSize: 15, height: 1.5),
             ),
             const SizedBox(height: 20),
             if (suggested.isNotEmpty) ...[
                Text("SUGGESTED WORKOUT (${target.toUpperCase()})", style: GoogleFonts.orbitron(color: Colors.cyanAccent, fontSize: 12, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: suggested.map((e) => Chip(
                    label: Text(e.toString(), style: GoogleFonts.exo2(color: Colors.white, fontSize: 12)),
                    backgroundColor: Colors.white.withOpacity(0.1),
                    side: BorderSide.none,
                  )).toList(),
                )
             ]
           ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('GOT IT', style: TextStyle(color: Colors.cyanAccent)),
          ),
        ],
      ),
    );
  }
}