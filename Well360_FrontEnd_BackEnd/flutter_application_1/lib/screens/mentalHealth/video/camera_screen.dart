// lib/screens/mentalHealth/video/camera_screen.dart
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:ui';
import 'package:google_fonts/google_fonts.dart';
import 'stress_graph_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> with SingleTickerProviderStateMixin {
  CameraController? _controller;
  bool _isCameraInitialized = false;
  String? _errorMessage;
  String _detectedEmotion = '';
  double _confidence = 0.0;
  
  Timer? _analysisTimer;
  late AnimationController _scanController;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _scanController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  void _startAnalysis() {
    _analysisTimer = Timer.periodic(const Duration(seconds: 3), (timer) {
      if (mounted) {
        setState(() {
          final emotions = ['Happy', 'Neutral', 'Focused', 'Calm', 'Surprised'];
          _detectedEmotion = emotions[timer.tick % emotions.length];
          _confidence = 0.75 + (timer.tick % 5) * 0.05;
        });
      }
    });
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() {
          _errorMessage = 'No cameras found on this device';
        });
        return;
      }

      final camera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _controller = CameraController(
        camera,
        ResolutionPreset.veryHigh,
        enableAudio: false,
      );

      await _controller!.initialize();
      if (mounted) {
        setState(() {
          _isCameraInitialized = true;
        });
        _startAnalysis();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Failed to initialize camera: ${e.toString()}';
        });
      }
    }
  }

  @override
  void dispose() {
    _analysisTimer?.cancel();
    _controller?.dispose();
    _scanController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage != null) {
      return _buildErrorScreen();
    }

    if (!_isCameraInitialized) {
      return _buildLoadingScreen();
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Camera Preview
          CameraPreview(_controller!),
          
          // Face Mesh Overlay Simulation
          Positioned.fill(
             child: CustomPaint(
               painter: _FaceScannerPainter(_scanController),
             ),
          ),

          // Top Bar Overlay
          _buildTopBar(),

          // Emotion Result Display
          if (_detectedEmotion.isNotEmpty) _buildEmotionDisplay(),

          // Bottom Controls
          _buildBottomControls(),
        ],
      ),
    );
  }

  Widget _buildErrorScreen() {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.redAccent.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.redAccent.withValues(alpha: 0.5))
                ),
                child: const Icon(Icons.error_outline, size: 60, color: Colors.redAccent),
              ),
              const SizedBox(height: 32),
              Text(
                'CAMERA ERROR',
                style: GoogleFonts.orbitron(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 2),
              ),
              const SizedBox(height: 16),
              Text(
                _errorMessage ?? 'Unknown error occurred',
                textAlign: TextAlign.center,
                style: GoogleFonts.exo2(fontSize: 16, color: Colors.white70),
              ),
              const SizedBox(height: 48),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: Text(
                    'GO BACK',
                    style: GoogleFonts.orbitron(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLoadingScreen() {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.cyanAccent.withValues(alpha: 0.1),
                shape: BoxShape.circle,
                boxShadow: [BoxShadow(color: Colors.cyanAccent.withValues(alpha: 0.2), blurRadius: 30)],
                border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.5))
              ),
              child: const Icon(Icons.videocam, size: 50, color: Colors.cyanAccent),
            ),
            const SizedBox(height: 32),
            Text(
              'INITIALIZING...',
              style: GoogleFonts.orbitron(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 2),
            ),
            const SizedBox(height: 24),
            const CircularProgressIndicator(color: Colors.cyanAccent),
          ],
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: Container(
        padding: EdgeInsets.only(
          top: MediaQuery.of(context).padding.top + 16,
          left: 20,
          right: 20,
          bottom: 16,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.black.withValues(alpha: 0.8), Colors.transparent],
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.white24)
              ),
              child: Row(
                children: [
                  const Icon(Icons.videocam, color: Colors.redAccent, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    'LIVE ANALYSIS',
                    style: GoogleFonts.orbitron(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 40), // Spacer
          ],
        ),
      ),
    );
  }

  Widget _buildEmotionDisplay() {
    return Positioned(
      top: MediaQuery.of(context).padding.top + 80,
      left: 0,
      right: 0,
      child: Center(
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                color: Colors.black45,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.3)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.emoji_emotions_outlined, color: Colors.cyanAccent, size: 24),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _detectedEmotion.toUpperCase(),
                        style: GoogleFonts.orbitron(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1),
                      ),
                      Text(
                        '${(_confidence * 100).toStringAsFixed(0)}% CONFIDENCE',
                        style: GoogleFonts.exo2(fontSize: 10, color: Colors.cyanAccent),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBottomControls() {
    return Positioned(
      bottom: 0,
      left: 0,
      right: 0,
      child: Container(
        padding: EdgeInsets.only(
          left: 24,
          right: 24,
          bottom: MediaQuery.of(context).padding.bottom + 24,
          top: 40,
        ),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.bottomCenter,
            end: Alignment.topCenter,
            colors: [Colors.black.withValues(alpha: 0.9), Colors.transparent],
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _buildControlButton(
              icon: Icons.close,
              label: 'QUIT',
              color: Colors.redAccent,
              onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
            ),
            _buildControlButton(
              icon: Icons.analytics_outlined,
              label: 'STATS',
              color: Colors.purpleAccent,
              onPressed: () {
                Navigator.push(context, MaterialPageRoute(builder: (_) => const StressGraphScreen()));
              },
            ),
            _buildControlButton(
              icon: Icons.map,
              label: 'MAP',
              color: Colors.greenAccent,
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Map View coming soon!', style: GoogleFonts.exo2()), backgroundColor: Colors.black87));
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildControlButton({required IconData icon, required String label, required Color color, required VoidCallback onPressed}) {
    return GestureDetector(
      onTap: onPressed,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.2),
              shape: BoxShape.circle,
              border: Border.all(color: color.withValues(alpha: 0.5))
            ),
            child: Icon(icon, color: color, size: 28),
          ),
          const SizedBox(height: 8),
          Text(label, style: GoogleFonts.exo2(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _FaceScannerPainter extends CustomPainter {
  final Animation<double> animation;
  _FaceScannerPainter(this.animation) : super(repaint: animation);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.cyanAccent.withValues(alpha: 0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.35 + (animation.value * 10);
    
    // Draw scanning circle
    canvas.drawCircle(center, radius, paint);
    
    // Draw corners
    final cornerPaint = Paint()
      ..color = Colors.cyanAccent.withValues(alpha: 0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
      
    double cornerSize = 40;
    double offset = radius + 20;

    // TL
    canvas.drawPath(
      Path()
        ..moveTo(center.dx - offset, center.dy - offset + cornerSize)
        ..lineTo(center.dx - offset, center.dy - offset)
        ..lineTo(center.dx - offset + cornerSize, center.dy - offset),
      cornerPaint
    );
    
    // TR
    canvas.drawPath(
        Path()
          ..moveTo(center.dx + offset - cornerSize, center.dy - offset)
          ..lineTo(center.dx + offset, center.dy - offset)
          ..lineTo(center.dx + offset, center.dy - offset + cornerSize),
        cornerPaint
    );
    
    // BL
    canvas.drawPath(
        Path()
          ..moveTo(center.dx - offset, center.dy + offset - cornerSize)
          ..lineTo(center.dx - offset, center.dy + offset)
          ..lineTo(center.dx - offset + cornerSize, center.dy + offset),
        cornerPaint
    );

    // BR
    canvas.drawPath(
        Path()
          ..moveTo(center.dx + offset - cornerSize, center.dy + offset)
          ..lineTo(center.dx + offset, center.dy + offset)
          ..lineTo(center.dx + offset, center.dy + offset - cornerSize),
        cornerPaint
    );
  }
  
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}