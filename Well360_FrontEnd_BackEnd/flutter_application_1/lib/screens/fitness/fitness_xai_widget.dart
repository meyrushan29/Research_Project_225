// lib/screens/fitness/fitness_xai_widget.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// XAI Explanation Widget for Fitness Analysis
/// Shows natural language form explanations, joint importance, and per-rep timeline
class FitnessXaiWidget extends StatefulWidget {
  final Map<String, dynamic>? xaiExplanation;
  final Map<String, dynamic>? jointImportance;
  final List<dynamic>? perRepTimeline;

  const FitnessXaiWidget({
    super.key,
    this.xaiExplanation,
    this.jointImportance,
    this.perRepTimeline,
  });

  @override
  State<FitnessXaiWidget> createState() => _FitnessXaiWidgetState();
}

class _FitnessXaiWidgetState extends State<FitnessXaiWidget> {
  bool _showJointDetails = false;
  bool _showRepTimeline = false;

  @override
  Widget build(BuildContext context) {
    final hasXai = widget.xaiExplanation != null &&
        (widget.xaiExplanation!['insights'] as List?)?.isNotEmpty == true;
    final hasJoints = widget.jointImportance != null && widget.jointImportance!.isNotEmpty;
    final hasReps = widget.perRepTimeline != null && widget.perRepTimeline!.isNotEmpty;

    if (!hasXai && !hasJoints && !hasReps) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ─── XAI Header ───
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.deepPurpleAccent.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.psychology, color: Colors.deepPurpleAccent, size: 20),
              ),
              const SizedBox(width: 12),
              Text(
                "AI FORM ANALYSIS",
                style: GoogleFonts.orbitron(
                  color: Colors.deepPurpleAccent,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  letterSpacing: 1.5,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.deepPurpleAccent.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  "XAI",
                  style: GoogleFonts.orbitron(
                    color: Colors.deepPurpleAccent,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // ─── AI Summary ───
        if (hasXai && widget.xaiExplanation!['summary'] != null)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Colors.deepPurpleAccent.withOpacity(0.12),
                    Colors.blueAccent.withOpacity(0.06),
                  ],
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.deepPurpleAccent.withOpacity(0.25)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.auto_awesome, color: Colors.deepPurpleAccent, size: 18),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      widget.xaiExplanation!['summary'],
                      style: GoogleFonts.exo2(
                        color: Colors.white,
                        fontSize: 13,
                        height: 1.5,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        const SizedBox(height: 16),

        // ─── Insights List ───
        if (hasXai)
          ..._buildInsights(widget.xaiExplanation!['insights'] as List),

        // ─── Joint Importance ───
        if (hasJoints) ...[
          const SizedBox(height: 16),
          _buildJointImportanceSection(),
        ],

        // ─── Per-Rep Timeline ───
        if (hasReps) ...[
          const SizedBox(height: 16),
          _buildRepTimelineSection(),
        ],
      ],
    );
  }

  List<Widget> _buildInsights(List insights) {
    return insights.map<Widget>((insight) {
      final severity = insight['severity'] ?? 'info';
      final Color color;
      final Color bgColor;

      switch (severity) {
        case 'good':
          color = Colors.greenAccent;
          bgColor = Colors.greenAccent.withOpacity(0.08);
          break;
        case 'warning':
          color = Colors.orangeAccent;
          bgColor = Colors.orangeAccent.withOpacity(0.08);
          break;
        case 'critical':
          color = Colors.redAccent;
          bgColor = Colors.redAccent.withOpacity(0.08);
          break;
        default:
          color = Colors.cyanAccent;
          bgColor = Colors.cyanAccent.withOpacity(0.08);
      }

      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: color.withOpacity(0.25)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(_getIconData(insight['icon']), color: color, size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      insight['title'] ?? '',
                      style: GoogleFonts.orbitron(
                        color: color,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      insight['message'] ?? '',
                      style: GoogleFonts.exo2(
                        color: Colors.white70,
                        fontSize: 12,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }).toList();
  }

  Widget _buildJointImportanceSection() {
    final joints = widget.jointImportance!;
    // Sort by importance
    final sorted = joints.entries.toList()
      ..sort((a, b) => (b.value as num).compareTo(a.value as num));
    final top5 = sorted.take(5).toList();

    if (top5.isEmpty) return const SizedBox.shrink();

    final maxVal = (top5.first.value as num).toDouble();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.cyanAccent.withOpacity(0.15)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            InkWell(
              onTap: () => setState(() => _showJointDetails = !_showJointDetails),
              child: Row(
                children: [
                  const Icon(Icons.accessibility_new, color: Colors.cyanAccent, size: 18),
                  const SizedBox(width: 8),
                  Text(
                    "AI FOCUS POINTS",
                    style: GoogleFonts.orbitron(
                      color: Colors.cyanAccent,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  Icon(
                    _showJointDetails ? Icons.expand_less : Icons.expand_more,
                    color: Colors.cyanAccent,
                    size: 20,
                  ),
                ],
              ),
            ),
            if (_showJointDetails) ...[
              const SizedBox(height: 14),
              Text(
                "These body joints had the most influence on the AI's decision:",
                style: GoogleFonts.exo2(color: Colors.white54, fontSize: 11),
              ),
              const SizedBox(height: 12),
              ...top5.map((entry) => _buildJointBar(
                entry.key,
                (entry.value as num).toDouble(),
                maxVal,
              )),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildJointBar(String name, double value, double maxVal) {
    final ratio = maxVal > 0 ? value / maxVal : 0.0;
    final Color barColor;
    if (ratio > 0.7) {
      barColor = Colors.redAccent;
    } else if (ratio > 0.4) {
      barColor = Colors.orangeAccent;
    } else {
      barColor = Colors.cyanAccent;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                name,
                style: GoogleFonts.exo2(color: Colors.white70, fontSize: 11),
              ),
              Text(
                "${(ratio * 100).toStringAsFixed(0)}%",
                style: GoogleFonts.orbitron(
                  color: barColor,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: ratio.clamp(0.0, 1.0),
              minHeight: 6,
              backgroundColor: Colors.white.withOpacity(0.08),
              valueColor: AlwaysStoppedAnimation(barColor),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRepTimelineSection() {
    final reps = widget.perRepTimeline!;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.purpleAccent.withOpacity(0.15)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            InkWell(
              onTap: () => setState(() => _showRepTimeline = !_showRepTimeline),
              child: Row(
                children: [
                  const Icon(Icons.timeline, color: Colors.purpleAccent, size: 18),
                  const SizedBox(width: 8),
                  Text(
                    "PER-REP BREAKDOWN",
                    style: GoogleFonts.orbitron(
                      color: Colors.purpleAccent,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  Icon(
                    _showRepTimeline ? Icons.expand_less : Icons.expand_more,
                    color: Colors.purpleAccent,
                    size: 20,
                  ),
                ],
              ),
            ),
            if (_showRepTimeline) ...[
              const SizedBox(height: 14),
              ...reps.map<Widget>((rep) => _buildRepCard(rep)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRepCard(dynamic rep) {
    final repNum = rep['rep_number'] ?? 0;
    final romPct = rep['rom_pct'];
    final duration = rep['duration'];
    final quality = rep['quality'] ?? 'unknown';

    final Color qualityColor;
    final IconData qualityIcon;
    switch (quality) {
      case 'good':
        qualityColor = Colors.greenAccent;
        qualityIcon = Icons.check_circle;
        break;
      case 'fair':
        qualityColor = Colors.orangeAccent;
        qualityIcon = Icons.warning_amber;
        break;
      case 'poor':
        qualityColor = Colors.redAccent;
        qualityIcon = Icons.cancel;
        break;
      default:
        qualityColor = Colors.white38;
        qualityIcon = Icons.help_outline;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: qualityColor.withOpacity(0.06),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: qualityColor.withOpacity(0.15)),
      ),
      child: Row(
        children: [
          Icon(qualityIcon, color: qualityColor, size: 16),
          const SizedBox(width: 8),
          Text(
            "Rep $repNum",
            style: GoogleFonts.orbitron(
              color: Colors.white,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          if (romPct != null)
            _buildRepMetric("ROM", "${romPct.toStringAsFixed(0)}%", qualityColor),
          if (duration != null) ...[
            const SizedBox(width: 12),
            _buildRepMetric("Time", "${duration.toStringAsFixed(1)}s", Colors.white54),
          ],
        ],
      ),
    );
  }

  Widget _buildRepMetric(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          label,
          style: GoogleFonts.exo2(color: Colors.white38, fontSize: 9),
        ),
        Text(
          value,
          style: GoogleFonts.orbitron(
            color: color,
            fontSize: 10,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  IconData _getIconData(String? iconName) {
    switch (iconName) {
      case 'check_circle': return Icons.check_circle;
      case 'error': return Icons.error;
      case 'help': return Icons.help;
      case 'straighten': return Icons.straighten;
      case 'balance': return Icons.balance;
      case 'speed': return Icons.speed;
      case 'emoji_events': return Icons.emoji_events;
      case 'trending_up': return Icons.trending_up;
      case 'trending_down': return Icons.trending_down;
      case 'psychology': return Icons.psychology;
      case 'verified': return Icons.verified;
      default: return Icons.info_outline;
    }
  }
}
