// lib/screens/hydration/camera_screen.dart
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:google_fonts/google_fonts.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  List<CameraDescription> _cameras = [];
  bool _isInit = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras.isEmpty) {
        setState(() => _error = "No cameras found");
        return;
      }

      // Use the first camera (usually front/webcam on laptop)
      // Prefer front camera if available
      final frontCam = _cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => _cameras.first,
      );

      _controller = CameraController(
        frontCam, 
        ResolutionPreset.medium, 
        enableAudio: false
      );

      await _controller!.initialize();
      if (!mounted) return;
      setState(() => _isInit = true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = "Camera Error: $e");
    }
  }

  Future<void> _takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    try {
      final XFile rawFile = await _controller!.takePicture();
      
      // Load image
      final bytes = await rawFile.readAsBytes();
      img.Image? originalImage = img.decodeImage(bytes);
      
      if (originalImage != null) {
        // Correct orientation for front camera
        // (Usually front cams are rotated, but we'll assume basic crop logic for now)
        // Crop Center Area (Simulating the UI Overlay)
        
        final int w = originalImage.width;
        final int h = originalImage.height;
        
        // Target: Center 60% Width, 20% Height
        final int cropW = (w * 0.6).toInt();
        final int cropH = (cropW * 0.5).toInt(); // 2:1 Aspect Ratio
        final int cropX = (w - cropW) ~/ 2;
        final int cropY = (h - cropH) ~/ 2;
        
        final cropped = img.copyCrop(originalImage, x: cropX, y: cropY, width: cropW, height: cropH);
        final jpg = img.encodeJpg(cropped);
        
        // Save to temp file
        final String newPath = '${rawFile.path}_cropped.jpg';
        if (!kIsWeb) {
           await File(newPath).writeAsBytes(jpg);
           if (!mounted) return;
           Navigator.pop(context, XFile(newPath));
           return;
        } else {
           // For Web, constructing XFile from bytes is tricky, but we can pass bytes back if needed
           final croppedFile = XFile.fromData(Uint8List.fromList(jpg), mimeType: 'image/jpeg', name: 'cropped.jpg');
           if (!mounted) return;
           Navigator.pop(context, croppedFile);
           return;
        }
      }

      if (!mounted) return;
      Navigator.pop(context, rawFile); // Fallback
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Capture failed: $e", style: GoogleFonts.exo2())));
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(title: Text("CAMERA ERROR", style: GoogleFonts.orbitron()), backgroundColor: Colors.transparent),
        body: Center(child: Text(_error!, style: GoogleFonts.exo2(color: Colors.redAccent))),
      );
    }

    if (!_isInit || _controller == null) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Colors.cyanAccent)),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        alignment: Alignment.bottomCenter,
        children: [
          // Camera Feed
          Center(child: CameraPreview(_controller!)),
          
          // Overlay UI Matches Dark Future Theme
          Positioned(
            bottom: 40,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                FloatingActionButton(
                  heroTag: "cancel",
                  backgroundColor: Colors.white10,
                  onPressed: () => Navigator.pop(context),
                  child: const Icon(Icons.close, color: Colors.white),
                ),
                const SizedBox(width: 40),
                FloatingActionButton.large(
                  heroTag: "capture",
                  backgroundColor: Colors.white,
                  onPressed: _takePicture,
                  child: Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.cyanAccent, width: 2)
                    ),
                    child: const Icon(Icons.camera, color: Colors.black, size: 40),
                  ),
                ),
                const SizedBox(width: 40),
                 const SizedBox(width: 56), 
              ],
            ),
          ),
          
          // Animated Lip Scan Overlay
          Positioned.fill(
             child: IgnorePointer(
               child: Stack(
                 children: [
                   // Darken outer area
                   ColorFiltered(
                     colorFilter: ColorFilter.mode(Colors.black.withValues(alpha: 0.7), BlendMode.srcOut),
                     child: Stack(
                       children: [
                         Container(
                           decoration: const BoxDecoration(
                             color: Colors.black,
                             backgroundBlendMode: BlendMode.dstOut,
                           ), 
                         ),
                         // The "Hole"
                         Center(
                           child: Container(
                             width: 300,
                             height: 140,
                             decoration: BoxDecoration(
                               color: Colors.white,
                               borderRadius: BorderRadius.circular(70),
                             ),
                           ),
                         ),
                       ],
                     ),
                   ),
                   
                   // Scanning Mesh Points
                   const Center(
                     child: _LipMeshAnimation(),
                   ),
                   
                   // Border guideline
                   Center(
                     child: Container(
                       width: 320,
                       height: 160,
                       decoration: BoxDecoration(
                         borderRadius: BorderRadius.circular(80),
                         border: Border.all(color: Colors.cyanAccent.withValues(alpha: 0.5), width: 2),
                         boxShadow: [
                           BoxShadow(color: Colors.cyanAccent.withValues(alpha: 0.2), blurRadius: 20)
                         ]
                       ),
                     ),
                   ),
                   
                   // Scan Line Animation
                   const Center(
                     child: _ScanLine(),
                   ),
                 ],
               ),
             ),
          ),
          
          Positioned(
            top: 60,
            child: Column(
              children: [
                Text(
                  "ALIGN LIPS",
                  style: GoogleFonts.orbitron(
                    color: Colors.white, 
                    fontSize: 24, 
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                    shadows: [const Shadow(blurRadius: 10, color: Colors.cyanAccent)]
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    "Ensure good lighting & keep camera close",
                    style: GoogleFonts.exo2(
                      color: Colors.white70,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}

class _LipMeshAnimation extends StatefulWidget {
  const _LipMeshAnimation();

  @override
  State<_LipMeshAnimation> createState() => _LipMeshAnimationState();
}

class _LipMeshAnimationState extends State<_LipMeshAnimation> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
       duration: const Duration(seconds: 2),
       vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: const Size(300, 140),
          painter: _MeshPainter(_controller.value),
        );
      },
    );
  }
}

class _MeshPainter extends CustomPainter {
  final double progress;
  _MeshPainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.cyanAccent.withValues(alpha: 0.4 + (progress * 0.4))
      ..style = PaintingStyle.fill;
    
    final points = [
      const Offset(0.1, 0.4), const Offset(0.3, 0.3), const Offset(0.5, 0.35), 
      const Offset(0.7, 0.3), const Offset(0.9, 0.4),
      const Offset(0.2, 0.6), const Offset(0.4, 0.7), const Offset(0.6, 0.7), 
      const Offset(0.8, 0.6),
    ];
    
    for (var p in points) {
      canvas.drawCircle(
        Offset(p.dx * size.width, p.dy * size.height), 
        3.0 + (progress * 1.5), 
        paint
      );
    }
  }
  
  @override
  bool shouldRepaint(_MeshPainter oldDelegate) => true;
}

class _ScanLine extends StatefulWidget {
  const _ScanLine();

  @override
  State<_ScanLine> createState() => _ScanLineState();
}

class _ScanLineState extends State<_ScanLine> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
       duration: const Duration(seconds: 3),
       vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, -70 + (_controller.value * 140)),
          child: Container(
            width: 280,
            height: 2,
            decoration: BoxDecoration(
              color: Colors.purpleAccent.withValues(alpha: 0.8), // Purple scan line for contrast
              boxShadow: [
                BoxShadow(
                  color: Colors.purpleAccent.withValues(alpha: 0.5),
                  blurRadius: 10,
                  spreadRadius: 2,
                )
              ],
            ),
          ),
        );
      },
    );
  }
}
