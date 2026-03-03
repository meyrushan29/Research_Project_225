import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:video_player/video_player.dart';
import 'package:flutter_application_1/services/api_service.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';
import 'package:intl/intl.dart';
import 'fitness_xai_widget.dart';

class FitnessSessionDetailScreen extends StatefulWidget {
  final Map<String, dynamic> sessionData;

  const FitnessSessionDetailScreen({
    super.key,
    required this.sessionData,
  });

  @override
  State<FitnessSessionDetailScreen> createState() => _FitnessSessionDetailScreenState();
}

class _FitnessSessionDetailScreenState extends State<FitnessSessionDetailScreen> {
  VideoPlayerController? _videoController;
  bool _heatmapEnabled = false;
  String? _normalVideoUrl;
  String? _heatmapVideoUrl;

  @override
  void initState() {
    super.initState();
    _initVideo();
  }

  void _initVideo() {
    // History endpoint returns "video_path_normal", not "video_url_normal" (DB columns)
    // But result dict had "video_url_normal".
    // Let's check what I saved in backend:
    // video_url_normal = f"/fitness_videos/{result['video_filename_normal']}"
    // video_path_normal=video_url_normal (in DB)
    
    // So DB keys are video_path_normal
    if (widget.sessionData['video_path_normal'] != null) {
      _normalVideoUrl = "${ApiService.baseUrl}${widget.sessionData['video_path_normal']}";
    }
    
    if (widget.sessionData['video_path_heatmap'] != null) {
      _heatmapVideoUrl = "${ApiService.baseUrl}${widget.sessionData['video_path_heatmap']}";
    }
    
    _loadVideo(_normalVideoUrl);
  }

  Future<void> _loadVideo(String? url) async {
    if (url == null) return;

    // 1. Remove the old controller from the UI immediately
    final oldController = _videoController;
    if (mounted) {
      setState(() {
        _videoController = null;
      });
    }

    // 2. Dispose previous controller safely
    if (oldController != null) {
      await oldController.dispose();
    }

    if (!mounted) return;

    // 3. Initialize new controller
    final newController = VideoPlayerController.networkUrl(Uri.parse(url));
    try {
      await newController.initialize();
      if (mounted) {
        setState(() {
          _videoController = newController;
        });
        await _videoController?.play();
        await _videoController?.setLooping(true);
      } else {
        await newController.dispose();
      }
    } catch (e) {
      debugPrint("Video error: $e");
    }
  }

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final timestamp = DateTime.parse(widget.sessionData['timestamp']).toLocal();
    final dateStr = DateFormat('MMM d, y • h:mm a').format(timestamp);

    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Column(
          children: [
            Text(
              'SESSION DETAILS',
              style: GoogleFonts.orbitron(
                fontWeight: FontWeight.bold,
                color: Colors.white,
                letterSpacing: 1.5,
                fontSize: 16
              ),
            ),
            Text(
              dateStr,
              style: GoogleFonts.exo2(
                color: Colors.white54,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
      body: Stack(
        children: [
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
              padding: const EdgeInsets.only(bottom: 50),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 10),
                  _buildVideoSection(),
                  const SizedBox(height: 24),
                  _buildQuickStats(),
                  const SizedBox(height: 24),
                  _buildDetailedMetrics(),
                  const SizedBox(height: 24),
                  // XAI Form Analysis from stored session data
                  _buildXaiSection(),
                  const SizedBox(height: 24),
                  _buildRecommendations(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVideoSection() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      // ... decoration ...
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
        boxShadow: [
          BoxShadow(color: Colors.cyanAccent.withOpacity(0.1), blurRadius: 20, spreadRadius: 1)
        ]
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: AspectRatio(
          aspectRatio: (_videoController != null && _videoController!.value.isInitialized)
              ? _videoController!.value.aspectRatio 
              : 16 / 9,
          child: Stack(
            alignment: Alignment.center,
            children: [
              if (_videoController != null && _videoController!.value.isInitialized)
                VideoPlayer(_videoController!)
              else
                Container(
                  color: Colors.black,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                       if (_normalVideoUrl == null) ...[
                         const Icon(Icons.videocam_off, color: Colors.white24, size: 40),
                         const SizedBox(height: 10),
                         Text("Video expired or not saved", style: GoogleFonts.exo2(color: Colors.white54))
                       ] else 
                         const CircularProgressIndicator(color: Colors.cyanAccent),
                    ],
                  ),
                ),
                
              if (_heatmapVideoUrl != null)
                Positioned(
                  top: 10,
                  right: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: _heatmapEnabled ? Colors.purpleAccent : Colors.white24),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                         Text(
                          "HEATMAP",
                          style: GoogleFonts.orbitron(fontSize: 10, color: Colors.white),
                        ),
                        Switch(
                          value: _heatmapEnabled,
                          onChanged: (val) {
                            setState(() {
                              _heatmapEnabled = val;
                              _loadVideo(_heatmapEnabled ? _heatmapVideoUrl : _normalVideoUrl);
                            });
                          },
                          activeColor: Colors.purpleAccent,
                        ),
                      ],
                    ),
                  ),
                )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildQuickStats() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          Expanded(
            child: _buildStatCard(
              "EXERCISE",
              _formatExerciseName(widget.sessionData['exercise']),
              Icons.fitness_center,
              Colors.cyanAccent,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: _buildStatCard(
              "SCORE",
              "${widget.sessionData['confidence']?.toInt() ?? 0}%",
              Icons.analytics,
              Colors.purpleAccent,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 8),
          Text(label, style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 10)),
          const SizedBox(height: 4),
          Text(value, style: GoogleFonts.exo2(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildDetailedMetrics() {
    final repsTotal = widget.sessionData['reps_total'] ?? 0;
    final repsCorrect = widget.sessionData['reps_correct'] ?? 0;
    final repsWrong = widget.sessionData['reps_wrong'] ?? 0;
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("SESSION METRICS", style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          _buildMetricRow("Total Reps", "$repsTotal", Icons.repeat),
          Divider(color: Colors.white.withValues(alpha: 0.1)),
          _buildMetricRow("Correct Reps", "$repsCorrect", Icons.check_circle, color: Colors.greenAccent),
          Divider(color: Colors.white.withValues(alpha: 0.1)),
          _buildMetricRow("Wrong Reps", "$repsWrong", Icons.cancel, color: Colors.redAccent),
          Divider(color: Colors.white.withValues(alpha: 0.1)),
          _buildMetricRow("Hold Time", "${widget.sessionData['hold_time'] ?? 0}s", Icons.timer),
        ],
      ),
    );
  }
  
  Widget _buildMetricRow(String label, String value, IconData icon, {Color color = Colors.white70}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 16),
          Expanded(child: Text(label, style: GoogleFonts.exo2(color: Colors.white70))),
          Text(value, style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildRecommendations() {
    final details = widget.sessionData['details'];
    if (details == null || details is! Map) return const SizedBox.shrink();
    
    final String? aiRec = details['recommendation'];
    
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (aiRec != null && aiRec.isNotEmpty) ...[
             Row(
               children: [
                 const Icon(Icons.auto_awesome, color: Colors.purpleAccent, size: 20),
                 const SizedBox(width: 8),
                 Text("AI TRAINER INSIGHT", style: GoogleFonts.orbitron(color: Colors.purpleAccent, fontWeight: FontWeight.bold)),
               ],
             ),
             const SizedBox(height: 12),
             Container(
               padding: const EdgeInsets.all(16),
               decoration: BoxDecoration(
                 color: Colors.purpleAccent.withOpacity(0.1),
                 borderRadius: BorderRadius.circular(16),
                 border: Border.all(color: Colors.purpleAccent.withOpacity(0.3)),
               ),
               child: Row(
                 crossAxisAlignment: CrossAxisAlignment.start,
                 children: [
                   const Icon(Icons.format_quote, color: Colors.purpleAccent, size: 20),
                   const SizedBox(width: 10),
                   Expanded(
                     child: Text(
                       aiRec, 
                       style: GoogleFonts.exo2(
                         color: Colors.white, 
                         fontSize: 14,
                         height: 1.5,
                         fontStyle: FontStyle.italic
                       )
                     ),
                   ),
                 ],
               ),
             ),
             const SizedBox(height: 24),
          ],
          
          if (details['avg_rom'] != null || details['avg_tempo'] != null || details['avg_stability'] != null) ...[
              Text("ADVANCED ANALYTICS", style: GoogleFonts.orbitron(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              if (details['avg_rom'] != null)
                 _buildMetricRow("Avg ROM", "${details['avg_rom']}%", Icons.straighten, color: Colors.blueAccent),
              if (details['avg_tempo'] != null)
                 _buildMetricRow("Avg Tempo", "${details['avg_tempo']}s/rep", Icons.speed, color: Colors.orangeAccent),
              if (details['avg_stability'] != null)
                 _buildMetricRow("Stability Score", "${details['avg_stability']}/100", Icons.balance, color: Colors.purpleAccent),
          ]
        ],
      ),
    );
  }

  String _formatExerciseName(String? name) {
    if (name == null || name.isEmpty) return "Unknown";
    String cleaned = name;
    if (cleaned.endsWith('_correct')) cleaned = cleaned.substring(0, cleaned.length - 8);
    if (cleaned.endsWith('_wrong'))   cleaned = cleaned.substring(0, cleaned.length - 6);
    return cleaned.split('_').map((w) => w.isNotEmpty ? "${w[0].toUpperCase()}${w.substring(1)}" : "").join(" ");
  }

  Widget _buildXaiSection() {
    final details = widget.sessionData['details'];
    if (details == null || details is! Map) return const SizedBox.shrink();
    
    final xaiExplanation = details['xai_explanation'] as Map<String, dynamic>?;
    final jointImportance = (details['joint_importance'] as Map?)?.cast<String, dynamic>();
    final perRepTimeline = details['per_rep_timeline'] as List?;
    
    return FitnessXaiWidget(
      xaiExplanation: xaiExplanation,
      jointImportance: jointImportance,
      perRepTimeline: perRepTimeline,
    );
  }
}
