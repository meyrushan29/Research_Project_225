// lib/screens/fitness/result_screen.dart
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:video_player/video_player.dart';
import 'package:flutter_application_1/services/api_service.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'fitness_xai_widget.dart';

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

  void _loadVideo(String? url) async {
    if (url == null) return;

    // 1. Remove the old controller from the UI immediately to prevent using a disposed controller
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
      debugPrint("Video initialization failed: $e");
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Failed to play video: $e"), backgroundColor: Colors.red)
         );
      }
    }
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
            icon: const Icon(Icons.download, color: Colors.purpleAccent),
            onPressed: () => _downloadVideo(),
          ),
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
                  // FIX: Show low-confidence warning banner
                  if (_isLowConfidence()) _buildConfidenceWarning(),
                  // FIX: Show accuracy warning for new users
                  if (widget.analysisResult.containsKey('accuracy_warning') && widget.analysisResult['accuracy_warning'] != null)
                    _buildAccuracyWarning(widget.analysisResult['accuracy_warning']),
                  _buildVideoSection(),
                  const SizedBox(height: 12),
                  if (widget.analysisResult.containsKey('lighting_message') && widget.analysisResult['lighting_message'] != null)
                    _buildLightingMessage(widget.analysisResult['lighting_message']),
                  const SizedBox(height: 24),
                  _buildQuickStats(),
                  const SizedBox(height: 24),
                  _buildDetailedAnalysis(),
                  const SizedBox(height: 24),
                  // XAI Form Analysis Section
                  FitnessXaiWidget(
                    xaiExplanation: widget.analysisResult['xai_explanation'] as Map<String, dynamic>?,
                    jointImportance: (widget.analysisResult['joint_importance'] as Map?)?.cast<String, dynamic>(),
                    perRepTimeline: widget.analysisResult['per_rep_timeline'] as List?,
                  ),
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
            // ProcessingScreen used pushReplacement, so we only need to pop once to go back to Home
            Navigator.of(context).pop(); 
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

  Future<void> _downloadVideo() async {
    final url = _heatmapEnabled ? _heatmapVideoUrl : _normalVideoUrl;
    if (url == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No video available to download.')),
      );
      return;
    }

    try {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Downloading video...'), duration: Duration(seconds: 1)),
      );

      // Find the appropriate directory to save
      Directory? directory;
      if (Platform.isAndroid) {
        directory = Directory('/storage/emulated/0/Download');
        if (!await directory.exists()) {
          directory = await getExternalStorageDirectory();
        }
      } else {
        directory = await getApplicationDocumentsDirectory();
      }

      if (directory == null) throw Exception("Could not access storage directory.");

      final String timeStamp = DateTime.now().millisecondsSinceEpoch.toString();
      final String savePath = '${directory.path}/workout_analysis_$timeStamp.mp4';

      final dio = Dio();
      await dio.download(url, savePath);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Video saved to Downloads!\n$savePath', style: const TextStyle(fontSize: 12)),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to download: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  // FIX: Check if confidence is low
  bool _isLowConfidence() {
    final level = widget.analysisResult['confidence_level'] ?? '';
    final confidence = (widget.analysisResult['confidence'] as num?)?.toDouble() ?? 0;
    return level == 'low' || confidence < 45;
  }

  // FIX: Format exercise name nicely (e.g. "barbell_biceps_curl" -> "Barbell Biceps Curl")
  String _formatExerciseName(String? name) {
    if (name == null || name.isEmpty || name == 'unknown') return 'Unknown';
    // Strip accidental _correct / _wrong suffix if full label slipped through
    String cleaned = name;
    if (cleaned.endsWith('_correct')) cleaned = cleaned.substring(0, cleaned.length - 8);
    if (cleaned.endsWith('_wrong'))   cleaned = cleaned.substring(0, cleaned.length - 6);
    return cleaned
        .split('_')
        .map((word) => word.isNotEmpty ? '${word[0].toUpperCase()}${word.substring(1)}' : '')
        .join(' ');
  }

  // FIX: Format form label nicely  
  String _formatFormLabel(String? form) {
    if (form == null || form.isEmpty || form == 'unknown') return 'N/A';
    if (form == 'correct') return 'Good Form';
    if (form == 'wrong') return 'Needs Work';
    return form[0].toUpperCase() + form.substring(1);
  }

  // FIX: Get form color
  Color _getFormColor(String? form) {
    if (form == 'correct') return Colors.greenAccent;
    if (form == 'wrong') return Colors.redAccent;
    return Colors.orangeAccent;
  }

  Widget _buildAccuracyWarning(String message) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.purpleAccent.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.purpleAccent.withValues(alpha: 0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline_rounded, color: Colors.purpleAccent, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Analysis Warning',
                  style: GoogleFonts.orbitron(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Colors.purpleAccent,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: GoogleFonts.exo2(
                    fontSize: 12,
                    color: Colors.white70,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLightingMessage(String message) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.cyanAccent.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.wb_sunny_rounded, color: Colors.cyanAccent, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Lighting Enhanced',
                  style: GoogleFonts.orbitron(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Colors.cyanAccent,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  message,
                  style: GoogleFonts.exo2(
                    fontSize: 12,
                    color: Colors.white70,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConfidenceWarning() {
    final confidence = (widget.analysisResult['confidence'] as num?)?.toDouble() ?? 0;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.orangeAccent.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.orangeAccent.withValues(alpha: 0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.orangeAccent, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Low Confidence (${confidence.toStringAsFixed(1)}%)',
                  style: GoogleFonts.orbitron(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Colors.orangeAccent,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'The AI had difficulty analyzing this video. Try better lighting, a clearer angle, or a steadier camera for more accurate results.',
                  style: GoogleFonts.exo2(
                    fontSize: 12,
                    color: Colors.white70,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
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
                              activeThumbColor: Colors.purpleAccent,
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
                  const Icon(Icons.video_library, color: Colors.cyanAccent, size: 20),
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
    final form = widget.analysisResult['form'] as String? ?? 'unknown';
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          Expanded(
            child: _buildStatCard(
              icon: Icons.accessibility_new_rounded,
              label: 'EXERCISE',
              value: _formatExerciseName(widget.analysisResult['exercise'] as String?),
              color: Colors.cyanAccent,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: _buildStatCard(
              icon: form == 'correct' ? Icons.check_circle : 
                    form == 'wrong' ? Icons.cancel : Icons.help_outline,
              label: 'FORM SCORE',
              value: _formatFormLabel(form),
              color: _getFormColor(form),
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
    final repsCorrect = widget.analysisResult['reps_correct'] ?? 0;
    final repsWrong = widget.analysisResult['reps_wrong'] ?? 0;
    final totalReps = (widget.analysisResult['reps'] ?? 0);
    
    // Calculate percentage if reps exist
    double correctPct = 0;
    if (repsCorrect + repsWrong > 0) {
       correctPct = (repsCorrect / (repsCorrect + repsWrong)) * 100;
    } else if (totalReps > 0) {
       // Fallback if detailed stats missing but reps exist
       correctPct = widget.analysisResult['form'] == 'correct' ? 100 : 0;
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
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
              // Past Results Button
              TextButton.icon(
                onPressed: () {
                   // TODO: Navigate to full history page
                   ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Past Video Results Page coming soon!', style: GoogleFonts.exo2(color: Colors.white)),
                        backgroundColor: Colors.purpleAccent.withValues(alpha: 0.5),
                      )
                   );
                },
                icon: const Icon(Icons.history, color: Colors.purpleAccent, size: 16),
                label: Text("HISTORY", style: GoogleFonts.orbitron(color: Colors.purpleAccent, fontSize: 12)),
              )
            ],
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
                  '$totalReps',
                  Icons.repeat,
                  Colors.greenAccent,
                ),
                // Show breakdown if available
                if (repsCorrect > 0 || repsWrong > 0) ...[
                   Divider(color: Colors.white.withValues(alpha: 0.1)),
                   Row(
                     children: [
                       Expanded(child: _buildMetricRow('Correct Reps', '$repsCorrect', Icons.check_circle_outline, Colors.green)),
                       Container(width: 1, height: 40, color: Colors.white10),
                       Expanded(child: _buildMetricRow('Wrong Reps', '$repsWrong', Icons.cancel_outlined, Colors.red)),
                     ],
                   )
                ],
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
          
          _buildAnalysisTable(correctPct),
        ],
      ),
    );
  }

  Widget _buildAnalysisTable(double correctPct) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'PERFORMANCE ANALYSIS',
          style: GoogleFonts.orbitron(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
            letterSpacing: 1
          ),
        ),
        const SizedBox(height: 16),
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
          ),
          child: Table(
            columnWidths: const {
              0: FlexColumnWidth(2), 
              1: FlexColumnWidth(1), 
              2: FlexColumnWidth(1),
              3: FlexColumnWidth(1.2)
            },
            defaultVerticalAlignment: TableCellVerticalAlignment.middle,
            children: [
              // Header
              TableRow(
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.05)),
                children: [
                  _buildTableHeader("Metric"),
                  _buildTableHeader("Value"),
                  _buildTableHeader("Trend"),
                  _buildTableHeader("Status"),
                ]
              ),
              // Correct %
              _buildTableRow(
                "Accuracy", 
                "${correctPct.toStringAsFixed(0)}%", 
                Icons.trending_up, 
                Colors.greenAccent,
                correctPct > 80 ? "Excellent" : (correctPct > 50 ? "Good" : "Poor")
              ),
              // Wrong %
              _buildTableRow(
                "Error Rate", 
                "${(100 - correctPct).toStringAsFixed(0)}%", 
                Icons.trending_down, 
                Colors.redAccent,
                (100 - correctPct) < 20 ? "Low" : "High"
              ),
              // Intensity (Mock)
              _buildTableRow(
                "Intensity", 
                "High", 
                Icons.bolt, 
                Colors.orangeAccent,
                "Optimal"
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTableHeader(String text) {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Text(text, style: GoogleFonts.exo2(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }

  TableRow _buildTableRow(String metric, String value, IconData trendIcon, Color color, String status) {
    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Text(metric, style: GoogleFonts.exo2(color: Colors.white, fontWeight: FontWeight.w500)),
        ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Text(value, style: GoogleFonts.orbitron(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Icon(trendIcon, color: color, size: 18),
        ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: Container(
             padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
             decoration: BoxDecoration(
               color: color.withValues(alpha: 0.2),
               borderRadius: BorderRadius.circular(8),
               border: Border.all(color: color.withValues(alpha: 0.5), width: 0.5)
             ),
             child: Text(status, 
               textAlign: TextAlign.center,
               style: GoogleFonts.exo2(color: color, fontSize: 10, fontWeight: FontWeight.bold)
             ),
          ),
        ),
      ]
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
    
    // Check for personalized body part recommendation
    final String? specificRec = widget.analysisResult['recommendation'];
    if (specificRec != null && specificRec.isNotEmpty) {
       // Insert at the top
       recommendations.insert(0, specificRec);
    } else {
       // Check inside details/advanced_metrics if not at root
       final details = widget.analysisResult['advanced_metrics'];
       if (details is Map && details['recommendation'] != null) {
          recommendations.insert(0, details['recommendation'].toString());
       }
    }
    
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
               const Icon(Icons.lightbulb_outline, color: Colors.yellowAccent, size: 20),
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