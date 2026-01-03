import 'package:flutter/material.dart';

class SummaryTile extends StatelessWidget {
  final String title;
  final String value;

  const SummaryTile({
    super.key,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(title),
      trailing: Text(
        value,
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
  }
}