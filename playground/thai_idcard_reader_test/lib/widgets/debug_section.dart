/// Reusable collapsible debug section widget.
library;

import 'package:flutter/material.dart';

class DebugSection extends StatefulWidget {
  final String title;
  final Widget child;
  final bool initiallyExpanded;
  final Color? headerColor;

  const DebugSection({
    super.key,
    required this.title,
    required this.child,
    this.initiallyExpanded = true,
    this.headerColor,
  });

  @override
  State<DebugSection> createState() => _DebugSectionState();
}

class _DebugSectionState extends State<DebugSection> {
  late bool _isExpanded;

  @override
  void initState() {
    super.initState();
    _isExpanded = widget.initiallyExpanded;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: () {
              setState(() {
                _isExpanded = !_isExpanded;
              });
            },
            child: Container(
              padding: const EdgeInsets.all(12),
              color: widget.headerColor ?? Colors.blue.shade50,
              child: Row(
                children: [
                  Icon(
                    _isExpanded
                        ? Icons.keyboard_arrow_down
                        : Icons.keyboard_arrow_right,
                    size: 24,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      widget.title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_isExpanded)
            Padding(
              padding: const EdgeInsets.all(12),
              child: widget.child,
            ),
        ],
      ),
    );
  }
}
