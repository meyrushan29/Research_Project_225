import 'package:flutter/material.dart';
import 'hydration_home_screen.dart';
import 'fitness_screen.dart';
import 'mental_health_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AI-Driven Health Analyzer"),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _card(
              "Hydration Management",
              Icons.water_drop,
              Colors.blue,
              () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const HydrationHomeScreen()),
              ),
            ),
            _card(
              "Fitness Optimization",
              Icons.fitness_center,
              Colors.green,
              () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const FitnessScreen()),
              ),
            ),
            _card(
              "Mental Health Assessment",
              Icons.psychology,
              Colors.purple,
              () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const MentalHealthScreen()),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _card(String title, IconData icon, Color color, VoidCallback onTap) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 10),
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(title),
        trailing: const Icon(Icons.arrow_forward_ios),
        onTap: onTap,
      ),
    );
  }
}
