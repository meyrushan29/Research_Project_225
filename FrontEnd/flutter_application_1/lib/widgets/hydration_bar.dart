import 'package:flutter/material.dart';

class HydrationBar extends StatelessWidget {
  final int score;

  const HydrationBar({super.key, required this.score});

  @override
  Widget build(BuildContext context) {
    final hydrationData = _getHydrationData(score);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            hydrationData.color.withOpacity(0.1),
            hydrationData.color.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: hydrationData.color.withOpacity(0.3),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: hydrationData.color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      hydrationData.icon,
                      color: hydrationData.color,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Hydration Level',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: Colors.grey,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        hydrationData.label,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: hydrationData.color,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              // Score Badge
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: hydrationData.color,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: hydrationData.color.withOpacity(0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Text(
                  '$score',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Progress Bar with Scale
          Column(
            children: [
              // Scale Labels
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildScaleLabel('0', Colors.red.shade400),
                  _buildScaleLabel('40', Colors.orange.shade400),
                  _buildScaleLabel('70', Colors.green.shade400),
                  _buildScaleLabel('100', Colors.green.shade600),
                ],
              ),
              const SizedBox(height: 8),

              // Animated Progress Bar
              Stack(
                children: [
                  // Background bar with gradient zones
                  Container(
                    height: 16,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(10),
                      gradient: LinearGradient(
                        colors: [
                          Colors.red.shade300,
                          Colors.orange.shade300,
                          Colors.yellow.shade300,
                          Colors.green.shade300,
                          Colors.green.shade400,
                        ],
                        stops: const [0.0, 0.4, 0.5, 0.7, 1.0],
                      ),
                    ),
                  ),
                  // Foreground bar (filled portion)
                  FractionallySizedBox(
                    widthFactor: score / 100,
                    child: Container(
                      height: 16,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(10),
                        gradient: LinearGradient(
                          colors: [
                            hydrationData.color.withOpacity(0.8),
                            hydrationData.color,
                          ],
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: hydrationData.color.withOpacity(0.4),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                    ),
                  ),
                  // Score indicator
                  Positioned(
                    left:
                        (score / 100) *
                            MediaQuery.of(context).size.width *
                            0.85 -
                        12,
                    top: -8,
                    child: Container(
                      width: 24,
                      height: 32,
                      decoration: BoxDecoration(
                        color: hydrationData.color,
                        borderRadius: BorderRadius.circular(4),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.2),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.arrow_drop_down,
                        color: Colors.white,
                        size: 20,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Description
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.7),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(Icons.info_outline, size: 18, color: hydrationData.color),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    hydrationData.description,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey.shade700,
                      height: 1.3,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScaleLabel(String text, Color color) {
    return Column(
      children: [
        Container(
          width: 3,
          height: 8,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          text,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: color,
          ),
        ),
      ],
    );
  }

  _HydrationData _getHydrationData(int score) {
    if (score < 40) {
      return _HydrationData(
        color: Colors.red.shade600,
        label: 'Dehydrated',
        icon: Icons.warning_amber_rounded,
        description:
            'Your hydration level is low. Increase water intake immediately.',
      );
    } else if (score < 70) {
      return _HydrationData(
        color: Colors.orange.shade600,
        label: 'Moderate',
        icon: Icons.water_drop_outlined,
        description:
            'Fair hydration. Consider drinking more water throughout the day.',
      );
    } else {
      return _HydrationData(
        color: Colors.green.shade600,
        label: 'Well Hydrated',
        icon: Icons.check_circle,
        description: 'Excellent! Your hydration level is optimal. Keep it up!',
      );
    }
  }
}

class _HydrationData {
  final Color color;
  final String label;
  final IconData icon;
  final String description;

  _HydrationData({
    required this.color,
    required this.label,
    required this.icon,
    required this.description,
  });
}
