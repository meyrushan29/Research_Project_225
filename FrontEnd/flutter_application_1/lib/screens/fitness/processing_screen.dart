// lib/screens/fitness/processing_screen.dart
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'result_screen.dart';

class ProcessingScreen extends StatefulWidget {
  final PlatformFile videoFile;
  final String videoName;
  final String videoSource;
  
  const ProcessingScreen({
    super.key,
    required this.videoFile,
    required this.videoName,
    required this.videoSource,
  });

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen>
    with TickerProviderStateMixin {
  late AnimationController _progressController;
  late AnimationController _pulseController;
  late Animation<double> _progressAnimation;
  late Animation<double> _pulseAnimation;
  
  int currentStep = 0;
  final List<String> steps = [
    'Loading video...',
    'Detecting poses...',
    'Analyzing form...',
    'Counting reps...',
    'Generating insights...',
  ];

  @override
  void initState() {
    super.initState();
    
    _progressController = AnimationController(
      duration: const Duration(seconds: 5),
      vsync: this,
    );

    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    )..repeat(reverse: true);

    _progressAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _progressController, curve: Curves.easeInOut),
    );

    _pulseAnimation = Tween<double>(begin: 0.96, end: 1.04).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _startProcessing();
  }

  void _startProcessing() {
    _progressController.forward();
    
    for (int i = 0; i < steps.length; i++) {
      Future.delayed(Duration(milliseconds: 1000 * i), () {
        if (mounted) {
          setState(() {
            currentStep = i;
          });
        }
      });
    }

    Future.delayed(const Duration(seconds: 5), () {
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        PageRouteBuilder(
          pageBuilder: (context, animation, secondaryAnimation) =>
              ResultScreen(
                videoFile: widget.videoFile,
                videoName: widget.videoName,
                videoSource: widget.videoSource,
              ),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            const begin = Offset(1.0, 0.0);
            const end = Offset.zero;
            const curve = Curves.easeInOut;
            var tween = Tween(begin: begin, end: end).chain(
              CurveTween(curve: curve),
            );
            var offsetAnimation = animation.drive(tween);
            return SlideTransition(position: offsetAnimation, child: child);
          },
          transitionDuration: const Duration(milliseconds: 500),
        ),
      );
    });
  }

  @override
  void dispose() {
    _progressController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1D3A),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF1A1D3A), Color(0xFF2D3561)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ScaleTransition(
                  scale: _pulseAnimation,
                  child: Container(
                    padding: const EdgeInsets.all(50),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: [
                          const Color(0xFF6C5CE7).withOpacity(0.3),
                          const Color(0xFFA29BFE).withOpacity(0.2),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF6C5CE7).withOpacity(0.3),
                          blurRadius: 40,
                          spreadRadius: 10,
                        ),
                      ],
                    ),
                    child: Container(
                      padding: const EdgeInsets.all(30),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: [
                            const Color(0xFF6C5CE7).withOpacity(0.4),
                            const Color(0xFFA29BFE).withOpacity(0.3),
                          ],
                        ),
                      ),
                      child: const Icon(
                        Icons.psychology,
                        size: 90,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 50),

                const Text(
                  'Analyzing Your Workout',
                  style: TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: 0.5,
                  ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 16),

                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.2),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: widget.videoSource == 'camera' 
                              ? const Color(0xFFFF6B9D).withOpacity(0.3)
                              : const Color(0xFF00D9A5).withOpacity(0.3),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          widget.videoSource == 'camera' 
                              ? Icons.videocam 
                              : Icons.upload_file,
                          color: Colors.white,
                          size: 16,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Flexible(
                        child: Text(
                          widget.videoName,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.white,
                            fontWeight: FontWeight.w500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 60),

                AnimatedBuilder(
                  animation: _progressAnimation,
                  builder: (context, child) {
                    return Column(
                      children: [
                        Stack(
                          children: [
                            Container(
                              height: 14,
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(7),
                              ),
                            ),
                            FractionallySizedBox(
                              widthFactor: _progressAnimation.value,
                              child: Container(
                                height: 14,
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [Color(0xFF00D9A5), Color(0xFF00B4D8)],
                                  ),
                                  borderRadius: BorderRadius.circular(7),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFF00D9A5).withOpacity(0.5),
                                      blurRadius: 12,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 20),
                        ShaderMask(
                          shaderCallback: (bounds) => const LinearGradient(
                            colors: [Color(0xFF00D9A5), Color(0xFF00B4D8)],
                          ).createShader(bounds),
                          child: Text(
                            '${(_progressAnimation.value * 100).toInt()}%',
                            style: const TextStyle(
                              fontSize: 38,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),

                const SizedBox(height: 50),

                Container(
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.1),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    children: List.generate(
                      steps.length,
                      (index) => _buildStepItem(
                        steps[index],
                        index,
                        currentStep >= index,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 40),

                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [
                        const Color(0xFF00D9A5).withOpacity(0.2),
                        const Color(0xFF00B4D8).withOpacity(0.2),
                      ],
                    ),
                  ),
                  child: const Center(
                    child: SizedBox(
                      width: 28,
                      height: 28,
                      child: CircularProgressIndicator(
                        color: Color(0xFF00D9A5),
                        strokeWidth: 3,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepItem(String text, int index, bool isActive) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10.0),
      child: Row(
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              gradient: isActive
                  ? const LinearGradient(
                      colors: [Color(0xFF00D9A5), Color(0xFF00B4D8)],
                    )
                  : null,
              color: isActive ? null : Colors.white.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: isActive
                  ? const Icon(
                      Icons.check,
                      color: Colors.white,
                      size: 20,
                    )
                  : Text(
                      '${index + 1}',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.5),
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: AnimatedDefaultTextStyle(
              duration: const Duration(milliseconds: 300),
              style: TextStyle(
                fontSize: 16,
                color: isActive
                    ? Colors.white
                    : Colors.white.withOpacity(0.4),
                fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
              ),
              child: Text(text),
            ),
          ),
          if (currentStep == index)
            Container(
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF00D9A5).withOpacity(0.3),
                    const Color(0xFF00B4D8).withOpacity(0.3),
                  ],
                ),
              ),
              child: const Center(
                child: SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    color: Color(0xFF00D9A5),
                    strokeWidth: 2,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}