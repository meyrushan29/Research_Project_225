import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';
import 'combined_result_screen.dart';

class FormScreen extends StatefulWidget {
  const FormScreen({super.key});

  @override
  State<FormScreen> createState() => _FormScreenState();
}

class _FormScreenState extends State<FormScreen> {
  final _formKey = GlobalKey<FormState>();

  // ---------------- Controllers ----------------
  final ageController = TextEditingController();
  final weightController = TextEditingController();
  final heightController = TextEditingController();
  final waterController = TextEditingController();
  final exerciseController = TextEditingController();

  // ---------------- Dropdown values ----------------
  String gender = "Male";
  String activity = "Moderate";
  String urinated = "Yes";
  int urineColor = 4;
  String thirsty = "No";
  String dizziness = "No";
  String fatigue = "No";
  String headache = "No";
  String sweating = "Moderate";

  bool loading = false;

  // ---------------- Submit ----------------
  Future<void> submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => loading = true);

    try {
      final position = await LocationService.getLocation();

      final payload = {
        "Age": int.parse(ageController.text),
        "Gender": gender,
        "Weight": double.parse(weightController.text),
        "Height": double.parse(heightController.text),
        "Water_Intake_Last_4_Hours": double.parse(waterController.text),
        "Exercise_Time_Last_4_Hours": double.parse(exerciseController.text),
        "Physical_Activity_Level": activity,
        "Urinated_Last_4_Hours": urinated,
        "Urine_Color": urineColor,
        "Thirsty": thirsty,
        "Dizziness": dizziness,
        "Fatigue": fatigue,
        "Headache": headache,
        "Sweating_Level": sweating,
        "Latitude": position.latitude,
        "Longitude": position.longitude,
      };

      final result = await ApiService.predictHydration(payload);

      if (!mounted) return;

      setState(() => loading = false);

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => CombinedResultScreen(formResult: result),
        ),
      );
    } catch (e) {
      setState(() => loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Prediction failed: $e"),
          backgroundColor: Colors.red.shade600,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  // ---------------- UI ----------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      appBar: AppBar(
        title: const Text("Hydration Assessment"),
        elevation: 0,
        backgroundColor: Colors.blue.shade600,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
              decoration: BoxDecoration(
                color: Colors.blue.shade600,
                borderRadius: const BorderRadius.only(
                  bottomLeft: Radius.circular(30),
                  bottomRight: Radius.circular(30),
                ),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.water_drop_outlined,
                    size: 48,
                    color: Colors.white.withOpacity(0.9),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Complete Your Health Profile',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Fill in the details below to check your hydration status',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                ],
              ),
            ),

            // Form Section
            Padding(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    // Personal Information Section
                    _buildSection(
                      title: "Personal Information",
                      icon: Icons.person_outline,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: _numberField(
                                ageController,
                                "Age",
                                Icons.cake,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _dropdown(
                                "Gender",
                                gender,
                                ["Male", "Female"],
                                (v) => setState(() => gender = v),
                                Icons.people_outline,
                              ),
                            ),
                          ],
                        ),
                        Row(
                          children: [
                            Expanded(
                              child: _numberField(
                                weightController,
                                "Weight (kg)",
                                Icons.monitor_weight_outlined,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _numberField(
                                heightController,
                                "Height (cm)",
                                Icons.height,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // Activity Information Section
                    _buildSection(
                      title: "Activity & Intake",
                      icon: Icons.directions_run,
                      children: [
                        _numberField(
                          waterController,
                          "Water intake last 4h (L)",
                          Icons.local_drink,
                        ),
                        _numberField(
                          exerciseController,
                          "Exercise minutes",
                          Icons.fitness_center,
                        ),
                        _dropdown(
                          "Physical Activity Level",
                          activity,
                          [
                            "Sedentary",
                            "Light",
                            "Moderate",
                            "Heavy",
                            "Very Heavy",
                          ],
                          (v) => setState(() => activity = v),
                          Icons.trending_up,
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // Urination & Symptoms Section
                    _buildSection(
                      title: "Current Symptoms",
                      icon: Icons.health_and_safety_outlined,
                      children: [
                        _dropdown(
                          "Urinated in last 4 hours",
                          urinated,
                          ["Yes", "No"],
                          (v) => setState(() => urinated = v),
                          Icons.wc,
                        ),
                        _urineColorPicker(),
                        _dropdown(
                          "Feeling Thirsty",
                          thirsty,
                          ["Yes", "No"],
                          (v) => setState(() => thirsty = v),
                          Icons.water_drop,
                        ),
                        _dropdown(
                          "Sweating Level",
                          sweating,
                          ["None", "Light", "Moderate", "Heavy", "Very Heavy"],
                          (v) => setState(() => sweating = v),
                          Icons.thermostat,
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // Health Indicators Section
                    _buildSection(
                      title: "Health Indicators",
                      icon: Icons.monitor_heart_outlined,
                      children: [
                        _yesNoChip(
                          "Dizziness",
                          dizziness,
                          (v) => setState(() => dizziness = v),
                        ),
                        _yesNoChip(
                          "Fatigue",
                          fatigue,
                          (v) => setState(() => fatigue = v),
                        ),
                        _yesNoChip(
                          "Headache",
                          headache,
                          (v) => setState(() => headache = v),
                        ),
                      ],
                    ),

                    const SizedBox(height: 32),

                    // Submit Button
                    loading
                        ? Container(
                            padding: const EdgeInsets.all(20),
                            child: const CircularProgressIndicator(),
                          )
                        : SizedBox(
                            width: double.infinity,
                            height: 56,
                            child: ElevatedButton(
                              onPressed: submit,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.blue.shade600,
                                foregroundColor: Colors.white,
                                elevation: 2,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16),
                                ),
                              ),
                              child: const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.analytics_outlined, size: 24),
                                  SizedBox(width: 12),
                                  Text(
                                    "Analyze Hydration",
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------- Widgets ----------------
  Widget _buildSection({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: Colors.blue.shade600, size: 20),
                ),
                const SizedBox(width: 12),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey.shade800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _numberField(
    TextEditingController controller,
    String label,
    IconData icon,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: Colors.blue.shade600),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.blue.shade600, width: 2),
          ),
          filled: true,
          fillColor: Colors.grey.shade50,
        ),
        validator: (v) {
          if (v == null || v.trim().isEmpty) return "Required";
          if (double.tryParse(v) == null) return "Invalid number";
          return null;
        },
      ),
    );
  }

  Widget _dropdown(
    String label,
    String value,
    List<String> items,
    ValueChanged<String> onChanged,
    IconData icon,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: DropdownButtonFormField<String>(
        value: value,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: Colors.blue.shade600),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.blue.shade600, width: 2),
          ),
          filled: true,
          fillColor: Colors.grey.shade50,
        ),
        items: items
            .map((e) => DropdownMenuItem<String>(value: e, child: Text(e)))
            .toList(),
        onChanged: (v) => onChanged(v!),
      ),
    );
  }

  Widget _urineColorPicker() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.palette, color: Colors.blue.shade600, size: 20),
              const SizedBox(width: 8),
              const Text(
                "Urine Color (1 = Light, 8 = Dark)",
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(8, (i) {
                    final color = i + 1;
                    return GestureDetector(
                      onTap: () => setState(() => urineColor = color),
                      child: Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: _getUrineColor(color),
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: urineColor == color
                                ? Colors.blue.shade600
                                : Colors.grey.shade300,
                            width: urineColor == color ? 3 : 1,
                          ),
                        ),
                        child: urineColor == color
                            ? const Icon(
                                Icons.check,
                                color: Colors.white,
                                size: 20,
                              )
                            : Center(
                                child: Text(
                                  "$color",
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                      ),
                    );
                  }),
                ),
                const SizedBox(height: 8),
                Text(
                  "Selected: Level $urineColor",
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.grey.shade600,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getUrineColor(int level) {
    final colors = [
      const Color(0xFFFFF9C4),
      const Color(0xFFFFF59D),
      const Color(0xFFFFEE58),
      const Color(0xFFFFD54F),
      const Color(0xFFFFB74D),
      const Color(0xFFFF9800),
      const Color(0xFFF57C00),
      const Color(0xFFE65100),
    ];
    return colors[level - 1];
  }

  Widget _yesNoChip(
    String label,
    String value,
    ValueChanged<String> onChanged,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
            ),
          ),
          Row(
            children: ["No", "Yes"].map((option) {
              final isSelected = value == option;
              return Padding(
                padding: const EdgeInsets.only(left: 8),
                child: ChoiceChip(
                  label: Text(option),
                  selected: isSelected,
                  onSelected: (_) => onChanged(option),
                  selectedColor: Colors.blue.shade100,
                  backgroundColor: Colors.grey.shade100,
                  labelStyle: TextStyle(
                    color: isSelected
                        ? Colors.blue.shade700
                        : Colors.grey.shade700,
                    fontWeight: isSelected
                        ? FontWeight.bold
                        : FontWeight.normal,
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  // ---------------- Dispose ----------------
  @override
  void dispose() {
    ageController.dispose();
    weightController.dispose();
    heightController.dispose();
    waterController.dispose();
    exerciseController.dispose();
    super.dispose();
  }
}
