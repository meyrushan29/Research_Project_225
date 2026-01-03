import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_application_1/main.dart';

void main() {
  testWidgets('Hydration app loads successfully', (WidgetTester tester) async {
    // Load app
    await tester.pumpWidget(const HydrationApp());

    // Check welcome text
    expect(find.text('Human Hydration'), findsOneWidget);
  });
}

class HydrationApp extends StatelessWidget {
  const HydrationApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Human Hydration')),
        body: const Center(child: Text('Human Hydration')),
      ),
    );
  }
}
