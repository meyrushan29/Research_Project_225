// lib/screens/fitness/fitness_progress_screen.dart
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_application_1/services/api_service.dart';
import 'package:flutter_application_1/widgets/grid_painter.dart';

class FitnessProgressScreen extends StatefulWidget {
  final String? exerciseFilter;

  const FitnessProgressScreen({super.key, this.exerciseFilter});

  @override
  State<FitnessProgressScreen> createState() => _FitnessProgressScreenState();
}

class _FitnessProgressScreenState extends State<FitnessProgressScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = true;
  Map<String, dynamic> _progressData = {};
  Map<String, dynamic> _radarData    = {};
  List<dynamic>        _radarHistory = [];
  String? _error;
  int? _viewingCycleNum; // null = current cycle

  late AnimationController _radarAnimCtrl;
  late Animation<double>   _radarAnim;

  @override
  void initState() {
    super.initState();
    _radarAnimCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
    _radarAnim = CurvedAnimation(
      parent: _radarAnimCtrl,
      curve: Curves.easeOutCubic,
    );
    _loadAll();
  }

  @override
  void dispose() {
    _radarAnimCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadAll() async {
    try {
      final results = await Future.wait([
        ApiService.getFitnessProgress(exercise: widget.exerciseFilter, limit: 15),
        ApiService.getBodyPartRadar(),
        ApiService.getMuscleRadarHistory(),
      ]);
      if (mounted) {
        setState(() {
          _progressData = results[0] as Map<String, dynamic>;
          _radarData    = results[1] as Map<String, dynamic>;
          _radarHistory = results[2] as List<dynamic>;
          _isLoading    = false;
          _viewingCycleNum = null;
        });
        _radarAnimCtrl.forward(from: 0.0);
      }
    } catch (e) {
      if (mounted) {
        setState(() { _error = e.toString(); _isLoading = false; });
      }
    }
  }

  Future<void> _loadCycleData(int cycleNum) async {
    setState(() => _isLoading = true);
    try {
      final results = await Future.wait([
        ApiService.getFitnessProgress(exercise: widget.exerciseFilter, limit: 30, cycleNumber: cycleNum),
      ]);
      if (mounted) {
        setState(() {
          _progressData = results[0] as Map<String, dynamic>;
          _isLoading    = false;
          _viewingCycleNum = cycleNum;
        });
        _radarAnimCtrl.forward(from: 0.0);
      }
    } catch (e) {
      if (mounted) {
        setState(() { _error = e.toString(); _isLoading = false; });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text('FITNESS PROGRESS',
            style: GoogleFonts.orbitron(
                fontWeight: FontWeight.bold, color: Colors.white,
                letterSpacing: 1.5)),
      ),
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter, end: Alignment.bottomCenter,
                colors: [Color(0xFF050505), Color(0xFF0a0a12)],
              ),
            ),
          ),
          Positioned.fill(
            child: Opacity(opacity: 0.08, child: CustomPaint(painter: GridPainter())),
          ),
          SafeArea(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
                : _error != null ? _buildError() : _buildContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
            const SizedBox(height: 16),
            Text(_error ?? "Error loading data",
                style: GoogleFonts.exo2(color: Colors.white70),
                textAlign: TextAlign.center),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                setState(() { _isLoading = true; _error = null; });
                _loadAll();
              },
              style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.cyanAccent.withOpacity(0.2)),
              child: Text("Retry", style: GoogleFonts.exo2(color: Colors.cyanAccent)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    final sessions      = _progressData['sessions'] as List? ?? [];
    final trends        = _progressData['trends'] as Map<String, dynamic>? ?? {};
    final aiSummary     = _progressData['ai_summary'] as String? ?? '';
    final metricsSummary = _progressData['metrics_summary'] as Map<String, dynamic>? ?? {};

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (aiSummary.isNotEmpty) ...[
            _buildAiSummaryCard(aiSummary),
            const SizedBox(height: 20),
          ],

          // ── MUSCLE FOCUS RADAR (current cycle) ─────────────────────
          _buildRadarCard(),
          const SizedBox(height: 16),

          // ── RADAR HISTORY ───────────────────────────────────────────
          if (_radarHistory.isNotEmpty) ...[
            _buildRadarHistory(),
            const SizedBox(height: 20),
          ],

          if (sessions.isNotEmpty) ...[
            _buildTrendCards(trends),
            const SizedBox(height: 20),
            _buildMetricsSummary(metricsSummary),
            const SizedBox(height: 24),
            Text("SESSION HISTORY",
                style: GoogleFonts.orbitron(
                    color: Colors.white, fontWeight: FontWeight.bold,
                    fontSize: 13)),
            const SizedBox(height: 12),
            _buildMetricChart("Range of Motion", sessions, 'avg_rom',
                Colors.cyanAccent, "%"),
            const SizedBox(height: 16),
            _buildMetricChart("Stability", sessions, 'avg_stability',
                Colors.purpleAccent, "/100"),
            const SizedBox(height: 16),
            _buildSessionSummaryList(sessions),
            const SizedBox(height: 30),
          ],
        ],
      ),
    );
  }

  // ════════════════════════════════════════════════════════════════════
  // RADAR CARD
  // ════════════════════════════════════════════════════════════════════

  static const List<String> _bodyParts = [
    'Arms', 'Chest', 'Back', 'Shoulders', 'Core', 'Legs'
  ];
  static const List<Color> _radarColors = [
    Color(0xFF00E5FF), Color(0xFFFF6D00), Color(0xFF00E676),
    Color(0xFFAA00FF), Color(0xFFFFD740), Color(0xFFFF4081),
  ];
  static const Map<String, IconData> _bodyPartIcons = {
    'Arms':      Icons.fitness_center,
    'Chest':     Icons.favorite,
    'Back':      Icons.airline_seat_flat,
    'Shoulders': Icons.accessibility_new,
    'Core':      Icons.circle,
    'Legs':      Icons.directions_run,
  };

  Widget _buildRadarCard() {
    final bool isHistory = _viewingCycleNum != null;
    final int currentSession = isHistory ? 30 : ((_radarData['current_session'] as num?)?.toInt() ?? 0);
    final int cycleSize      = isHistory ? 30 : ((_radarData['cycle_size'] as num?)?.toInt() ?? 30);
    final int cycleNumber    = isHistory ? _viewingCycleNum! : ((_radarData['cycle_number'] as num?)?.toInt() ?? 1);
    final int sessionsRemain = isHistory ? 0 : ((_radarData['sessions_remaining'] as num?)?.toInt() ?? 30);

    // Get values either from current radar data, or from the specific history item
    List<double> values = [];
    if (isHistory) {
      final historyItem = _radarHistory.firstWhere((h) => h['cycle_number'] == _viewingCycleNum, orElse: () => <String, dynamic>{});
      final radarMap = historyItem['radar_data'] as Map<String, dynamic>? ?? {};
      values = _bodyParts.map<double>((bp) => ((radarMap[bp] ?? 0) as num).toDouble()).toList();
    } else {
      values = _bodyParts.map<double>((bp) => ((_radarData[bp] ?? 0) as num).toDouble()).toList();
    }

    final progress = currentSession / cycleSize;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [
            Colors.cyanAccent.withOpacity(0.07),
            Colors.blueAccent.withOpacity(0.04),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.cyanAccent.withOpacity(0.22)),
        boxShadow: [
          BoxShadow(
            color: Colors.cyanAccent.withOpacity(0.05),
            blurRadius: 24, spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header row ──────────────────────────────────────────────
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.cyanAccent.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.radar, color: Colors.cyanAccent, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("MUSCLE FOCUS RADAR",
                        style: GoogleFonts.orbitron(
                            color: Colors.cyanAccent, fontSize: 13,
                            fontWeight: FontWeight.bold, letterSpacing: 1.0)),
                    const SizedBox(height: 3),
                    if (isHistory)
                       Text("Cycle $cycleNumber  ·  Historical Snapshot", style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10))
                    else
                       Text("Cycle $cycleNumber  ·  $sessionsRemain sessions until reset", style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10)),
                  ],
                ),
              ),
              if (isHistory)
                InkWell(
                  onTap: () => _loadAll(),
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: Colors.purpleAccent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.purpleAccent.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.refresh, color: Colors.purpleAccent, size: 10),
                        const SizedBox(width: 4),
                        Text("VIEW CURRENT",
                            style: GoogleFonts.orbitron(
                                color: Colors.purpleAccent, fontSize: 8,
                                fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: Colors.cyanAccent.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.cyanAccent.withOpacity(0.3)),
                  ),
                  child: Text("Cycle $cycleNumber",
                      style: GoogleFonts.orbitron(
                          color: Colors.cyanAccent, fontSize: 9,
                          fontWeight: FontWeight.bold)),
                ),
            ],
          ),
          const SizedBox(height: 14),

          // ── Progress bar ────────────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: Colors.white.withOpacity(0.08),
                    valueColor: const AlwaysStoppedAnimation<Color>(Colors.cyanAccent),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Text("$currentSession / $cycleSize",
                  style: GoogleFonts.orbitron(
                      color: Colors.cyanAccent, fontSize: 10,
                      fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 18),

          // ── Radar chart ─────────────────────────────────────────────
          if (currentSession == 0)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Column(
                  children: [
                    Icon(Icons.radar,
                        size: 48, color: Colors.white.withOpacity(0.1)),
                    const SizedBox(height: 12),
                    Text("Upload your first workout video\nto populate this radar",
                        style: GoogleFonts.exo2(color: Colors.white38, fontSize: 11),
                        textAlign: TextAlign.center),
                  ],
                ),
              ),
            )
          else
            AnimatedBuilder(
              animation: _radarAnim,
              builder: (_, __) => SizedBox(
                height: 260,
                child: CustomPaint(
                  size: const Size(double.infinity, 260),
                  painter: _RadarChartPainter(
                    values: values,
                    labels: _bodyParts,
                    colors: _radarColors,
                    animationValue: _radarAnim.value,
                  ),
                ),
              ),
            ),

          const SizedBox(height: 14),

          // ── Legend ──────────────────────────────────────────────────
          Wrap(
            spacing: 8, runSpacing: 8,
            children: List.generate(_bodyParts.length, (i) {
              final bp    = _bodyParts[i];
              final color = _radarColors[i];
              final score = values[i];
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: color.withOpacity(0.25)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(_bodyPartIcons[bp] ?? Icons.circle, color: color, size: 12),
                    const SizedBox(width: 5),
                    Text(bp,
                        style: GoogleFonts.exo2(
                            color: Colors.white70, fontSize: 10,
                            fontWeight: FontWeight.w600)),
                    const SizedBox(width: 4),
                    Text("${score.toStringAsFixed(0)}%",
                        style: GoogleFonts.orbitron(
                            color: color, fontSize: 9,
                            fontWeight: FontWeight.bold)),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  // ════════════════════════════════════════════════════════════════════
  // RADAR HISTORY
  // ════════════════════════════════════════════════════════════════════

  Widget _buildRadarHistory() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.history, color: Colors.white54, size: 16),
            const SizedBox(width: 8),
            Text("RADAR HISTORY",
                style: GoogleFonts.orbitron(
                    color: Colors.white, fontWeight: FontWeight.bold,
                    fontSize: 12)),
            const SizedBox(width: 8),
            Text("${_radarHistory.length} past cycle${_radarHistory.length != 1 ? 's' : ''}",
                style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10)),
          ],
        ),
        const SizedBox(height: 12),
        SizedBox(
          height: 180,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: _radarHistory.length,
            separatorBuilder: (_, __) => const SizedBox(width: 12),
            itemBuilder: (context, index) {
              final h         = _radarHistory[index] as Map<String, dynamic>;
              final cycleNum  = h['cycle_number'] as int? ?? index + 1;
              final radarMap  = h['radar_data']   as Map<String, dynamic>? ?? {};
              final completedAt = h['completed_at'] as String? ?? '';
              final dateStr   = completedAt.length >= 10
                  ? completedAt.substring(0, 10) : completedAt;

              final vals = _bodyParts
                  .map<double>((bp) => ((radarMap[bp] ?? 0) as num).toDouble())
                  .toList();
              
              final isSelected = _viewingCycleNum == cycleNum;

              return InkWell(
                onTap: () {
                  if (_viewingCycleNum != cycleNum) {
                    _loadCycleData(cycleNum);
                  }
                },
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  width: 150,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isSelected ? Colors.cyanAccent.withOpacity(0.1) : Colors.white.withOpacity(0.03),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: isSelected ? Colors.cyanAccent.withOpacity(0.6) : Colors.cyanAccent.withOpacity(0.15), width: isSelected ? 1.5 : 1),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text("Cycle $cycleNum",
                              style: GoogleFonts.orbitron(
                                  color: Colors.cyanAccent, fontSize: 9,
                                  fontWeight: FontWeight.bold)),
                          Text(dateStr,
                              style: GoogleFonts.exo2(
                                  color: Colors.white30, fontSize: 8)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Expanded(
                        child: CustomPaint(
                          painter: _RadarChartPainter(
                            values: vals,
                            labels: _bodyParts,
                            colors: _radarColors,
                            animationValue: 1.0,
                            compact: true,
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
                      // Top focused muscle
                      Builder(builder: (_) {
                        final sorted = _bodyParts
                            .map((bp) => MapEntry(bp, (radarMap[bp] ?? 0) as num))
                            .toList()
                          ..sort((a, b) => b.value.compareTo(a.value));
                        final top = sorted.first;
                        final topIdx = _bodyParts.indexOf(top.key);
                        final topColor = topIdx >= 0 ? _radarColors[topIdx] : Colors.cyanAccent;
                        return Row(
                          children: [
                            Icon(Icons.star, color: topColor, size: 11),
                            const SizedBox(width: 4),
                            Text(top.key,
                                style: GoogleFonts.exo2(
                                    color: topColor, fontSize: 9,
                                    fontWeight: FontWeight.bold)),
                            const SizedBox(width: 2),
                            Text("${top.value.toStringAsFixed(0)}%",
                                style: GoogleFonts.exo2(
                                    color: Colors.white38, fontSize: 9)),
                          ],
                        );
                      }),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  // ════════════════════════════════════════════════════════════════════
  // EXISTING WIDGETS
  // ════════════════════════════════════════════════════════════════════

  Widget _buildAiSummaryCard(String summary) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [
            Colors.deepPurpleAccent.withOpacity(0.15),
            Colors.blueAccent.withOpacity(0.08),
          ],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.deepPurpleAccent.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.auto_awesome, color: Colors.deepPurpleAccent, size: 20),
              const SizedBox(width: 8),
              Text("AI COACH SUMMARY",
                  style: GoogleFonts.orbitron(
                      color: Colors.deepPurpleAccent, fontSize: 12,
                      fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 12),
          Text(summary,
              style: GoogleFonts.exo2(
                  color: Colors.white, fontSize: 13,
                  height: 1.6, fontStyle: FontStyle.italic)),
        ],
      ),
    );
  }

  Widget _buildTrendCards(Map<String, dynamic> trends) {
    return Row(
      children: [
        Expanded(child: _buildTrendCard("ROM", trends['rom'] ?? 'neutral', Colors.cyanAccent)),
        const SizedBox(width: 10),
        Expanded(child: _buildTrendCard("Stability", trends['stability'] ?? 'neutral', Colors.purpleAccent)),
        const SizedBox(width: 10),
        Expanded(child: _buildTrendCard("Form", "${trends['form_accuracy'] ?? 0}%", Colors.greenAccent)),
      ],
    );
  }

  Widget _buildTrendCard(String label, String trend, Color color) {
    IconData icon; String displayText;
    switch (trend) {
      case 'improving': icon = Icons.trending_up;   displayText = "Improving"; break;
      case 'declining': icon = Icons.trending_down; displayText = "Declining"; break;
      case 'stable':    icon = Icons.trending_flat; displayText = "Stable";    break;
      default:          icon = Icons.analytics;     displayText = trend;
    }
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 6),
          Text(label, style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 9, fontWeight: FontWeight.bold)),
          const SizedBox(height: 2),
          Text(displayText, style: GoogleFonts.exo2(color: color, fontSize: 11, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
        ],
      ),
    );
  }

  Widget _buildMetricsSummary(Map<String, dynamic> metrics) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildAvgMetric("Avg ROM", metrics['avg_rom'] != null ? "${metrics['avg_rom']}%" : "—", Colors.cyanAccent),
          Container(width: 1, height: 40, color: Colors.white12),
          _buildAvgMetric("Avg Stability", metrics['avg_stability'] != null ? "${metrics['avg_stability']}" : "—", Colors.purpleAccent),
          Container(width: 1, height: 40, color: Colors.white12),
          _buildAvgMetric("Avg Tempo", metrics['avg_tempo'] != null ? "${metrics['avg_tempo']}s" : "—", Colors.orangeAccent),
        ],
      ),
    );
  }

  Widget _buildAvgMetric(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: GoogleFonts.orbitron(color: color, fontSize: 14, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(label, style: GoogleFonts.exo2(color: Colors.white38, fontSize: 10)),
      ],
    );
  }

  Widget _buildMetricChart(String label, List sessions, String key, Color color, String unit) {
    final values = sessions.where((s) => s[key] != null)
        .map<double>((s) => (s[key] as num).toDouble()).toList();
    if (values.isEmpty) return const SizedBox.shrink();
    final maxVal = values.reduce((a, b) => a > b ? a : b);
    final minVal = values.reduce((a, b) => a < b ? a : b);
    final range  = (maxVal - minVal).clamp(1.0, double.infinity);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: GoogleFonts.orbitron(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
              Text("${values.last.toStringAsFixed(0)}$unit", style: GoogleFonts.orbitron(color: Colors.white, fontSize: 11)),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 60,
            child: CustomPaint(
              size: const Size(double.infinity, 60),
              painter: _SparklinePainter(values: values, color: color, minVal: minVal, range: range),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionSummaryList(List sessions) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("SESSION BREAKDOWN",
              style: GoogleFonts.orbitron(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text("Each row shows one workout session",
              style: GoogleFonts.exo2(color: Colors.white30, fontSize: 10)),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.04), borderRadius: BorderRadius.circular(8)),
            child: Row(
              children: [
                SizedBox(width: 26, child: Text("#", style: GoogleFonts.orbitron(color: Colors.white38, fontSize: 9))),
                Expanded(flex: 3, child: Text("Exercise", style: GoogleFonts.orbitron(color: Colors.white38, fontSize: 9))),
                Expanded(flex: 2, child: Text("Form", style: GoogleFonts.orbitron(color: Colors.white38, fontSize: 9))),
                Expanded(flex: 1, child: Text("Reps", style: GoogleFonts.orbitron(color: Colors.white38, fontSize: 9), textAlign: TextAlign.center)),
                Expanded(flex: 1, child: Text("ROM", style: GoogleFonts.orbitron(color: Colors.white38, fontSize: 9), textAlign: TextAlign.right)),
              ],
            ),
          ),
          const SizedBox(height: 4),
          ...sessions.asMap().entries.map<Widget>((entry) {
            final idx = entry.key + 1; final s = entry.value;
            final exercise = (s['exercise'] ?? 'Unknown').toString().replaceAll('_', ' ');
            final form = s['form'] ?? 'unknown';
            final reps = s['reps_total'] ?? '-';
            final rom  = s['avg_rom'];
            final Color fc; final String fl; final IconData fi;
            if (form == 'correct') { fc = Colors.greenAccent; fl = "Correct"; fi = Icons.check_circle; }
            else if (form == 'wrong') { fc = Colors.redAccent; fl = "Wrong"; fi = Icons.cancel; }
            else { fc = Colors.white38; fl = "N/A"; fi = Icons.help_outline; }
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.04)))),
              child: Row(
                children: [
                  SizedBox(width: 26, child: Text("$idx", style: GoogleFonts.orbitron(color: Colors.white24, fontSize: 9))),
                  Expanded(flex: 3, child: Text(exercise, style: GoogleFonts.exo2(color: Colors.white70, fontSize: 11), maxLines: 1, overflow: TextOverflow.ellipsis)),
                  Expanded(flex: 2, child: Row(children: [Icon(fi, color: fc, size: 13), const SizedBox(width: 4), Text(fl, style: GoogleFonts.exo2(color: fc, fontSize: 10, fontWeight: FontWeight.w600))])),
                  Expanded(flex: 1, child: Text("$reps", style: GoogleFonts.orbitron(color: Colors.white54, fontSize: 10), textAlign: TextAlign.center)),
                  Expanded(flex: 1, child: Text(rom != null ? "${rom}%" : "-", style: GoogleFonts.orbitron(color: Colors.cyanAccent, fontSize: 10, fontWeight: FontWeight.bold), textAlign: TextAlign.right)),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// RADAR CHART PAINTER  (shared by live radar + history mini cards)
// ═══════════════════════════════════════════════════════════════════════════

class _RadarChartPainter extends CustomPainter {
  final List<double> values;
  final List<String> labels;
  final List<Color>  colors;
  final double       animationValue;
  final bool         compact; // true = mini card (no labels, smaller rings)

  _RadarChartPainter({
    required this.values,
    required this.labels,
    required this.colors,
    required this.animationValue,
    this.compact = false,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final n      = values.length;
    final cx     = size.width  / 2;
    final cy     = size.height / 2;
    final radius = min(cx, cy) - (compact ? 6 : 36);

    double angle(int i) => -pi / 2 + (2 * pi / n) * i;
    Offset point(int i, double r) =>
        Offset(cx + r * cos(angle(i)), cy + r * sin(angle(i)));

    // ── Guide rings ────────────────────────────────────────────────
    for (final pct in [0.25, 0.50, 0.75, 1.0]) {
      final path = Path();
      for (int i = 0; i < n; i++) {
        final p = point(i, radius * pct);
        i == 0 ? path.moveTo(p.dx, p.dy) : path.lineTo(p.dx, p.dy);
      }
      path.close();
      canvas.drawPath(path, Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = pct == 1.0 ? 0.8 : 0.5
        ..color = Colors.white.withOpacity(pct == 1.0 ? 0.12 : 0.05));
    }

    // ── Spokes ─────────────────────────────────────────────────────
    final spokePaint = Paint()
      ..color = Colors.white.withOpacity(0.06)
      ..strokeWidth = 0.7;
    for (int i = 0; i < n; i++) {
      canvas.drawLine(Offset(cx, cy), point(i, radius), spokePaint);
    }

    // ── Filled data polygon ─────────────────────────────────────────
    final animVals = values.map((v) => v * animationValue).toList();
    final fillPath = Path();
    for (int i = 0; i < n; i++) {
      final r = radius * (animVals[i] / 100.0);
      final p = point(i, r);
      i == 0 ? fillPath.moveTo(p.dx, p.dy) : fillPath.lineTo(p.dx, p.dy);
    }
    fillPath.close();

    // Gradient fill
    canvas.drawPath(fillPath, Paint()
      ..style = PaintingStyle.fill
      ..shader = RadialGradient(
        center: Alignment.center, radius: 1.0,
        colors: [
          Colors.cyanAccent.withOpacity(0.28 * animationValue),
          Colors.tealAccent.withOpacity(0.08 * animationValue),
        ],
      ).createShader(Rect.fromCircle(center: Offset(cx, cy), radius: radius)));

    // Glow stroke
    canvas.drawPath(fillPath, Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = compact ? 1.2 : 2.2
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4)
      ..color = Colors.cyanAccent.withOpacity(0.6 * animationValue));

    canvas.drawPath(fillPath, Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = compact ? 1.0 : 1.5
      ..color = Colors.cyanAccent.withOpacity(animationValue));

    // ── Data dots ─────────────────────────────────────────────────
    for (int i = 0; i < n; i++) {
      final r = radius * (animVals[i] / 100.0);
      final p = point(i, r);
      final c = colors[i];
      canvas.drawCircle(p, compact ? 2.5 : 8,
          Paint()..color = c.withOpacity(0.18 * animationValue)
                 ..maskFilter = MaskFilter.blur(BlurStyle.normal, compact ? 3 : 6));
      canvas.drawCircle(p, compact ? 2.0 : 4,
          Paint()..color = c.withOpacity(animationValue)..style = PaintingStyle.fill);
      canvas.drawCircle(p, compact ? 0.8 : 1.5,
          Paint()..color = Colors.white.withOpacity(animationValue)..style = PaintingStyle.fill);
    }

    // ── Labels (only for full-size chart) ──────────────────────────
    if (!compact) {
      for (int i = 0; i < n; i++) {
        final p  = point(i, radius + 22);
        final c  = colors[i];
        final tp = TextPainter(
          text: TextSpan(
            text: labels[i].toUpperCase(),
            style: TextStyle(
              color: c.withOpacity(0.9), fontSize: 9,
              fontWeight: FontWeight.bold, letterSpacing: 0.5,
              shadows: [Shadow(color: c.withOpacity(0.5), blurRadius: 6)],
            ),
          ),
          textDirection: TextDirection.ltr,
        )..layout();
        tp.paint(canvas, Offset(p.dx - tp.width / 2, p.dy - tp.height / 2));
      }
    }
  }

  @override
  bool shouldRepaint(covariant _RadarChartPainter old) =>
      old.animationValue != animationValue || old.values != values;
}

// ═══════════════════════════════════════════════════════════════════════════
// SPARKLINE PAINTER
// ═══════════════════════════════════════════════════════════════════════════

class _SparklinePainter extends CustomPainter {
  final List<double> values;
  final Color color; final double minVal; final double range;

  _SparklinePainter({required this.values, required this.color,
      required this.minVal, required this.range});

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final paint = Paint()..color = color..strokeWidth = 2
        ..style = PaintingStyle.stroke..strokeCap = StrokeCap.round;
    final fillPaint = Paint()..shader = LinearGradient(
      begin: Alignment.topCenter, end: Alignment.bottomCenter,
      colors: [color.withOpacity(0.3), color.withOpacity(0.0)],
    ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));

    final path = Path(); final fillPath = Path();
    for (int i = 0; i < values.length; i++) {
      final x = i / (values.length - 1) * size.width;
      final y = size.height - ((values[i] - minVal) / range * size.height);
      if (i == 0) { path.moveTo(x, y); fillPath.moveTo(x, size.height); fillPath.lineTo(x, y); }
      else         { path.lineTo(x, y); fillPath.lineTo(x, y); }
    }
    fillPath.lineTo(size.width, size.height); fillPath.close();
    canvas.drawPath(fillPath, fillPaint); canvas.drawPath(path, paint);
    final dot = Paint()..color = color..style = PaintingStyle.fill;
    for (int i = 0; i < values.length; i++) {
      final x = i / (values.length - 1) * size.width;
      final y = size.height - ((values[i] - minVal) / range * size.height);
      canvas.drawCircle(Offset(x, y), 3, dot);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => true;
}
