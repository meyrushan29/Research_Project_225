// lib/screens/fitness/result_screen.dart
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:video_player/video_player.dart';
import 'package:flutter_application_1/services/api_service.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';

class ResultScreen extends StatefulWidget {
  final PlatformFile videoFile;
  final String videoName;
  final String videoSource;
  final Map<String, dynamic> analysisResult;
  
  const ResultScreen({
    super.key,
    required this.videoFile,
    required this.videoName,
    required this.videoSource,
    required this.analysisResult,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
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
    // Parse URLs
    if (widget.analysisResult.containsKey('video_url_normal')) {
      _normalVideoUrl = "${ApiService.baseUrl}${widget.analysisResult['video_url_normal']}";
    } else if (widget.analysisResult.containsKey('video_url')) {
      // Fallback
      _normalVideoUrl = "${ApiService.baseUrl}${widget.analysisResult['video_url']}";
    }

    if (widget.analysisResult.containsKey('video_url_heatmap')) {
      _heatmapVideoUrl = "${ApiService.baseUrl}${widget.analysisResult['video_url_heatmap']}";
    }
    
    _loadVideo(_normalVideoUrl);
  }

  void _loadVideo(String? url) {
    if (url == null) return;

    final oldController = _videoController;
    if (oldController != null) {
      oldController.pause();
    }

    _videoController = VideoPlayerController.networkUrl(Uri.parse(url))
      ..initialize().then((_) {
        if (mounted) {
          setState(() {});
          _videoController?.play();
          _videoController?.setLooping(true);
          
          if (oldController != null && oldController.value.isInitialized) {
             _videoController?.seekTo(oldController.value.position);
          }
        }
      }).catchError((e) {
        debugPrint("Video initialization failed: $e");
      });
  }

  @override
  void dispose() {
    _videoController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
        title: Text(
          'ANALYSIS REPORT',
          style: GoogleFonts.orbitron(
            fontWeight: FontWeight.bold,
            color: Colors.white,
            letterSpacing: 1.5
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share, color: Colors.cyanAccent),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Share feature coming soon!', style: GoogleFonts.exo2(color: Colors.white)),
                  backgroundColor: Colors.cyanAccent.withValues(alpha: 0.2),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
        ],
      ),
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
              padding: const EdgeInsets.only(bottom: 100),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 10),
                  _buildVideoSection(),
                  const SizedBox(height: 24),
                  _buildQuickStats(),
                  const SizedBox(height: 24),
                  _buildDetailedAnalysis(),
                  const SizedBox(height: 24),
                  _buildRecommendations(),
                ],
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
             BoxShadow(color: Colors.cyanAccent.withValues(alpha: 0.3), blurRadius: 20, spreadRadius: 2)
          ]
        ),
        child: FloatingActionButton.extended(
          onPressed: () {
            Navigator.of(context).popUntil((route) => route.isFirst);
          },
          icon: const Icon(Icons.refresh, color: Colors.black),
          label: Text(
            'NEW ANALYSIS',
            style: GoogleFonts.orbitron(
              fontWeight: FontWeight.bold,
              color: Colors.black,
            ),
          ),
          backgroundColor: Colors.cyanAccent,
          elevation: 0,
        ),
      ),
    );
  }

  Widget _buildVideoSection() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        boxShadow: [
          BoxShadow(color: Colors.cyanAccent.withValues(alpha: 0.1), blurRadius: 20, spreadRadius: 1)
        ]
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Column(
          children: [
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  if (_videoController != null && _videoController!.value.isInitialized)
                    AspectRatio(
                      aspectRatio: _videoController!.value.aspectRatio,
                      child: VideoPlayer(_videoController!),
                    )
                  else
                    Container(
                      color: Colors.black,
                      child: const Center(child: CircularProgressIndicator(color: Colors.cyanAccent)),
                    ),
                  
                  // Heatmap Toggle Overlay
                  Positioned(
                    top: 10,
                    right: 10,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.black54,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: _heatmapEnabled ? Colors.purpleAccent : Colors.white24),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.whatshot, size: 16, color: _heatmapEnabled ? Colors.purpleAccent : Colors.white54),
                          const SizedBox(width: 8),
                          Text(
                            "HEATMAP",
                            style: GoogleFonts.orbitron(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(width: 8),
                          SizedBox(
                            width: 30,
                            height: 20,
                            child: Switch(
                              value: _heatmapEnabled,
                              onChanged: (val) {
                                if (_heatmapVideoUrl == null) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("No heatmap available yet.")));
                                  return;
                                }
                                setState(() {
                                  _heatmapEnabled = val;
                                  _loadVideo(_heatmapEnabled ? _heatmapVideoUrl : _normalVideoUrl);
                                });
                              },
                              activeColor: Colors.purpleAccent,
                              activeTrackColor: Colors.purpleAccent.withValues(alpha: 0.3),
                              inactiveThumbColor: Colors.grey,
                              inactiveTrackColor: Colors.grey[800],
                            ),
                          )
                        ],
                      ),
                    ),
                  )
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.all(16),
              color: Colors.white.withValues(alpha: 0.05),
              child: Row(
                children: [
                  Icon(Icons.video_library, color: Colors.cyanAccent, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      widget.videoName,
                      style: GoogleFonts.exo2(color: Colors.white70, fontSize: 14),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            )
          ],
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
              icon: Icons.fitness_center,
              label: 'EXERCISE',
              value: widget.analysisResult['exercise'] ?? 'Unknown',
              color: Colors.cyanAccent,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: _buildStatCard(
              icon: Icons.check_circle,
              label: 'FORM SCORE',
              value: widget.analysisResult['form'] ?? 'N/A',
              color: Colors.purpleAccent,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: color.withValues(alpha: 0.3)),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: color.withValues(alpha: 0.2), blurRadius: 10)],
                ),
                child: Icon(icon, color: color, size: 24),
              ),
              const SizedBox(height: 12),
              Text(
                label,
                style: GoogleFonts.orbitron(
                  fontSize: 10,
                  color: Colors.white54,
                  letterSpacing: 1
                ),
              ),
              const SizedBox(height: 6),
              FittedBox(
                child: Text(
                  value,
                  style: GoogleFonts.exo2(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailedAnalysis() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'DETAILED METRICS',
            style: GoogleFonts.orbitron(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.white,
              letterSpacing: 1
            ),
          ),
          const SizedBox(height: 16),
          _buildGlassContainer(
            child: Column(
              children: [
                _buildMetricRow(
                  'Confidence Score',
                  '${(widget.analysisResult['confidence'] as num?)?.toStringAsFixed(1) ?? 0}%',
                  Icons.psychology,
                  Colors.blueAccent,
                ),
                Divider(color: Colors.white.withValues(alpha: 0.1)),
                _buildMetricRow(
                  'Repetition Count',
                  '${widget.analysisResult['reps'] ?? 0}',
                  Icons.repeat,
                  Colors.greenAccent,
                ),
                Divider(color: Colors.white.withValues(alpha: 0.1)),
                _buildMetricRow(
                  'Hold Duration',
                  '${widget.analysisResult['hold_time'] ?? 0}s',
                  Icons.timer,
                  Colors.orangeAccent,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlassContainer({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
          ),
          child: child,
        ),
      ),
    );
  }

  Widget _buildMetricRow(String label, String value, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              label,
              style: GoogleFonts.exo2(
                fontSize: 14,
                color: Colors.white70,
              ),
            ),
          ),
          Text(
            value,
            style: GoogleFonts.orbitron(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendations() {
    final List<dynamic> rawRecs = widget.analysisResult['recommendations'] ?? [];
    final recommendations = rawRecs.map((e) => e.toString()).toList();
    
    if (recommendations.isEmpty) {
        recommendations.add("Great form! Keep executing consistently.");
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
               Icon(Icons.lightbulb_outline, color: Colors.yellowAccent, size: 20),
               const SizedBox(width: 10),
               Text(
                'AI INSIGHTS',
                style: GoogleFonts.orbitron(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                  letterSpacing: 1
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildGlassContainer(
            child: Column(
              children: recommendations
                  .asMap()
                  .entries
                  .map((entry) => _buildRecommendationItem(
                        entry.key + 1,
                        entry.value,
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendationItem(int number, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: Colors.cyanAccent.withValues(alpha: 0.1),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.5))
            ),
            child: Center(
              child: Text(
                '$number',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.cyanAccent,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              text,
              style: GoogleFonts.exo2(
                fontSize: 14,
                height: 1.5,
                color: Colors.white70,
              ),
            ),
          ),
        ],
      ),
    );
  }
}