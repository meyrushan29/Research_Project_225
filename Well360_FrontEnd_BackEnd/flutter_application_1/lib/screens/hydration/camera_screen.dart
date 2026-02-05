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
  CameraDescription? _selectedCamera;

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

      // Default to Front
      final initialCamera = _cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => _cameras.first,
      );

      await _startCamera(initialCamera);
      
      if (!mounted) return;
      setState(() => _isInit = true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = "Camera Error: $e");
    }
  }

  Future<void> _startCamera(CameraDescription camera) async {
    if (_controller != null) {
      await _controller!.dispose();
    }
    
    _selectedCamera = camera;

    _controller = CameraController(
      camera, 
      ResolutionPreset.max, 
      enableAudio: false,
      imageFormatGroup: Platform.isAndroid ? ImageFormatGroup.jpeg : ImageFormatGroup.bgra8888,
    );

    try {
      await _controller!.initialize();
      try {
        await _controller!.setFocusMode(FocusMode.auto);
        await _controller!.setExposureMode(ExposureMode.auto);
      } catch (_) {}
    } catch (e) {
      print("Camera Start Error: $e");
    }
  }

  void _switchCamera() async {
    if (_cameras.length < 2) return;
    
    if (_selectedCamera != null) {
       final lensDirection = _selectedCamera!.lensDirection;
       CameraDescription newCamera;
       
       if (lensDirection == CameraLensDirection.front) {
         newCamera = _cameras.firstWhere((c) => c.lensDirection == CameraLensDirection.back, orElse: () => _cameras.first);
       } else {
         newCamera = _cameras.firstWhere((c) => c.lensDirection == CameraLensDirection.front, orElse: () => _cameras.first);
       }
       
       setState(() => _isInit = false); 
       await _startCamera(newCamera);
       setState(() => _isInit = true);
    }
  }

  Future<void> _takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    try {
      // Simple, direct capture
      final XFile rawFile = await _controller!.takePicture();
      await _processCenterCrop(rawFile);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Capture failed: $e", style: GoogleFonts.exo2())));
    }
  }

  Future<void> _processCenterCrop(XFile rawFile) async {
    final bytes = await rawFile.readAsBytes();
    img.Image? originalImage = img.decodeImage(bytes);
    
    if (originalImage != null) {
      // Fix rotation
      originalImage = img.bakeOrientation(originalImage);
      
      final int w = originalImage.width;
      final int h = originalImage.height;
      
      // Calculate Crop to match the UI Overlay (80% width, 0.45 aspect ratio)
      final double overlayWidthFactor = 0.8; 
      
      final int cropW = (w * overlayWidthFactor).toInt();
      final int cropH = (cropW * 0.45).toInt(); 
      
      final int cropX = (w - cropW) ~/ 2;
      final int cropY = (h - cropH) ~/ 2;
      
      // Perform Crop
      final cropped = img.copyCrop(originalImage, x: cropX, y: cropY, width: cropW, height: cropH);
      final jpg = img.encodeJpg(cropped);
      
      final String newPath = '${rawFile.path}_processed.jpg';
      await File(newPath).writeAsBytes(jpg);
      
      if (!mounted) return;
      Navigator.pop(context, XFile(newPath));
    } else {
      if (!mounted) return;
      Navigator.pop(context, rawFile);
    }
  }

  void _onTapFocus(TapUpDetails details, BoxConstraints constraints) {
    if (_controller == null || !_controller!.value.isInitialized) return;
    
    final offset = Offset(
      details.localPosition.dx / constraints.maxWidth,
      details.localPosition.dy / constraints.maxHeight,
    );
    
    try {
      _controller!.setFocusPoint(offset);
      _controller!.setExposurePoint(offset);
    } catch (_) {}
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
    
    final screenWidth = MediaQuery.of(context).size.width;
    final overlayWidth = screenWidth * 0.8;
    final overlayHeight = overlayWidth * 0.45;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        alignment: Alignment.bottomCenter,
        children: [
          // 1. Camera Feed with Tap to Focus
          LayoutBuilder(
            builder: (context, constraints) {
              return GestureDetector(
                onTapUp: (details) => _onTapFocus(details, constraints),
                behavior: HitTestBehavior.opaque,
                child: SizedBox.expand(
                  child: Center(
                    child: CameraPreview(_controller!),
                  ),
                ),
              );
            }
          ),
          
          // 2. Simple Static Overlay (Guide)
          Positioned.fill(
             child: IgnorePointer(
               child: Stack(
                 children: [
                   // Dark Mask
                   ColorFiltered(
                     colorFilter: ColorFilter.mode(Colors.black.withOpacity(0.7), BlendMode.srcOut),
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
                             width: overlayWidth,
                             height: overlayHeight,
                             decoration: BoxDecoration(
                               color: Colors.white,
                               borderRadius: BorderRadius.circular(overlayHeight / 2),
                             ),
                           ),
                         ),
                       ],
                     ),
                   ),
                   // Simple Border (No animations)
                   Center(
                     child: Container(
                       width: overlayWidth + 20,
                       height: overlayHeight + 20,
                       decoration: BoxDecoration(
                         borderRadius: BorderRadius.circular(overlayHeight),
                         border: Border.all(color: Colors.cyanAccent.withOpacity(0.5), width: 2),
                       ),
                     ),
                   ),
                ],
              ),
            ),
          ),
          
          // 3. UI Controls
          Positioned(
            bottom: 40,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // Close
                FloatingActionButton(
                  heroTag: "cancel",
                  backgroundColor: Colors.white10,
                  onPressed: () => Navigator.pop(context),
                  child: const Icon(Icons.close, color: Colors.white),
                ),
                const SizedBox(width: 40),
                // Capture
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
                // Switch Camera
                 FloatingActionButton(
                  heroTag: "switch_cam",
                  backgroundColor: Colors.white10,
                  onPressed: _switchCamera,
                  child: const Icon(Icons.cameraswitch, color: Colors.white),
                ), 
              ],
            ),
          ),
          
          // 4. Instruction Text
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
              ],
            ),
          )
        ],
      ),
    );
  }
}
