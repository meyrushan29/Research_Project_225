
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:ui';
import 'package:flutter_application_1/widgets/grid_painter.dart';
import 'package:flutter_application_1/services/api_service.dart';

class CompareResultsScreen extends StatefulWidget {
  const CompareResultsScreen({super.key});

  @override
  State<CompareResultsScreen> createState() => _CompareResultsScreenState();
}

class _CompareResultsScreenState extends State<CompareResultsScreen> {
  List<dynamic> _videoHistory = [];
  List<dynamic> _audioHistory = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadComparisonData();
  }

  Future<void> _loadComparisonData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final videoData = await ApiService.getEmotionHistory(source: 'video', limit: 20);
      final audioData = await ApiService.getEmotionHistory(source: 'audio', limit: 20);

      if (mounted) {
        setState(() {
          _videoHistory = (videoData['history'] as List<dynamic>?) ?? [];
          _audioHistory = (audioData['history'] as List<dynamic>?) ?? [];
          // Normalize lists to same length for comparison if needed, or just plot indices
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  double _getSentimentScore(String emotion) {
    switch (emotion.toLowerCase()) {
      case 'happy':
      case 'surprise':
        return 90.0; // Positive
      case 'neutral':
        return 50.0; // Neutral
      case 'calm':
        return 60.0;
      case 'sad':
      case 'fear':
      case 'disgust':
      case 'angry':
        return 20.0; // Negative
      default:
        return 50.0;
    }
  }

  List<FlSpot> _buildSpots(List<dynamic> history) {
    List<FlSpot> spots = [];
    for (int i = 0; i < history.length; i++) {
      final item = history[i];
      final emotion = item['emotion'] as String? ?? 'neutral';
      final score = _getSentimentScore(emotion);
      spots.add(FlSpot(i.toDouble(), score));
    }
    // Reverse to show chronological order (oldest to newest) if backend returns newest first
    // Usually backend returns newest first (index 0). So we should reverse for graph (left to right = time)
    // But let's check index. If index is not provided, we assume index 0 is latest.
    // To plot time: 0 is oldest.
    // If list is [Newest, ..., Oldest], we reverse it.
    // Let's assume standard API behavior: List is usually [Latest...Oldest].
    // So we need to reverse the spots or iterate backwards.
    return spots.reversed.toList().asMap().entries.map((e) {
      return FlSpot(e.key.toDouble(), e.value.y);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text('RESULT COMPARISON', style: GoogleFonts.orbitron(fontWeight: FontWeight.bold, fontSize: 20, letterSpacing: 1, color: Colors.white)),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white70),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white70),
            onPressed: _loadComparisonData,
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
            child: _isLoading
                ? _buildLoading()
                : _errorMessage != null
                    ? _buildError()
                    : _buildContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildLoading() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(color: Colors.cyanAccent),
          const SizedBox(height: 20),
          Text(
            'Comparing biometric data...',
            style: GoogleFonts.exo2(color: Colors.white60, fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.orangeAccent.withValues(alpha: 0.1),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.orangeAccent.withValues(alpha: 0.5)),
              ),
              child: const Icon(Icons.compare_arrows, size: 48, color: Colors.orangeAccent),
            ),
            const SizedBox(height: 24),
            Text(
              'Comparison Failed',
              style: GoogleFonts.orbitron(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, letterSpacing: 1),
            ),
            const SizedBox(height: 12),
            Text(
              _errorMessage ?? 'Unable to fetch data.',
              textAlign: TextAlign.center,
              style: GoogleFonts.exo2(fontSize: 14, color: Colors.white60),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: _loadComparisonData,
              icon: const Icon(Icons.refresh),
              label: Text('RETRY', style: GoogleFonts.orbitron(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.cyanAccent,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    final videoSpots = _buildSpots(_videoHistory);
    final audioSpots = _buildSpots(_audioHistory);

    if (videoSpots.isEmpty && audioSpots.isEmpty) {
        return Center(
            child: Text(
              'No history data available for comparison.',
              style: GoogleFonts.exo2(color: Colors.white60),
            ),
        );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
            ),
            child: Column(
              children: [
                 Text(
                   'TONE CONSISTENCY',
                   style: GoogleFonts.orbitron(
                     fontSize: 14,
                     fontWeight: FontWeight.bold,
                     color: Colors.white,
                     letterSpacing: 1
                   ),
                 ),
                 const SizedBox(height: 20),
                 SizedBox(
                   height: 300,
                   child: LineChart(
                     LineChartData(
                       gridData: FlGridData(
                         show: true,
                         drawVerticalLine: true,
                         getDrawingHorizontalLine: (value) => FlLine(
                           color: Colors.white.withValues(alpha: 0.05),
                           strokeWidth: 1,
                         ),
                         getDrawingVerticalLine: (value) => FlLine(
                           color: Colors.white.withValues(alpha: 0.05),
                           strokeWidth: 1,
                         ),
                       ),
                       titlesData: FlTitlesData(
                         show: true,
                         bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                         topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                         rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                         leftTitles: AxisTitles(
                           sideTitles: SideTitles(
                             showTitles: true,
                             reservedSize: 40,
                             interval: 20,
                             getTitlesWidget: (value, meta) {
                               if (value == 20) return Text('Neg', style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10));
                               if (value == 50) return Text('Neu', style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10));
                               if (value == 90) return Text('Pos', style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10));
                               return const SizedBox();
                             },
                           ),
                         ),
                       ),
                       borderData: FlBorderData(show: false),
                       minY: 0,
                       maxY: 100,
                       lineBarsData: [
                         // Visual Line
                         LineChartBarData(
                           spots: videoSpots,
                           isCurved: true,
                           color: Colors.cyanAccent,
                           barWidth: 3,
                           isStrokeCapRound: true,
                           dotData: const FlDotData(show: false),
                           belowBarData: BarAreaData(
                             show: true,
                             color: Colors.cyanAccent.withValues(alpha: 0.1),
                           ),
                         ),
                         // Audio Line
                         LineChartBarData(
                           spots: audioSpots,
                           isCurved: true,
                           color: Colors.purpleAccent,
                           barWidth: 3,
                           isStrokeCapRound: true,
                           dotData: const FlDotData(show: false),
                           belowBarData: BarAreaData(
                             show: true,
                             color: Colors.purpleAccent.withValues(alpha: 0.1),
                           ),
                         ),
                       ],
                     ),
                   ),
                 ),
                 const SizedBox(height: 20),
                 Row(
                   mainAxisAlignment: MainAxisAlignment.center,
                   children: [
                     _buildLegendItem('Visual Analysis', Colors.cyanAccent),
                     const SizedBox(width: 20),
                     _buildLegendItem('Audio Analysis', Colors.purpleAccent),
                   ],
                 ),
              ],
            ),
          ),
          
          const SizedBox(height: 30),
          
          Text(
            'INSIGHTS',
            style: GoogleFonts.orbitron(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.white,
              letterSpacing: 1
            ),
          ),
          const SizedBox(height: 16),
          _buildInsightCard(
             Icons.insights,
             'Overall Consistency',
             'Comparing your visual expressions with your vocal tone helps identify suppressed emotions.',
             Colors.blueAccent 
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: GoogleFonts.exo2(color: Colors.white70, fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildInsightCard(IconData icon, String title, String desc, Color color) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: GoogleFonts.orbitron(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  desc,
                  style: GoogleFonts.exo2(color: Colors.white60, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
