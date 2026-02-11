/// Debug log entry widget with timestamp and color coding.
library;

import 'package:flutter/material.dart';

enum LogLevel { info, success, error, warning }

class DebugLogEntry extends StatelessWidget {
  final DateTime timestamp;
  final String message;
  final LogLevel level;

  const DebugLogEntry({
    super.key,
    required this.timestamp,
    required this.message,
    required this.level,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildIcon(),
          const SizedBox(width: 8),
          Text(
            _formatTimestamp(),
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade600,
              fontFamily: 'monospace',
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                fontSize: 13,
                color: _getTextColor(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIcon() {
    IconData iconData;
    Color iconColor;

    switch (level) {
      case LogLevel.success:
        iconData = Icons.check_circle;
        iconColor = Colors.green;
        break;
      case LogLevel.error:
        iconData = Icons.error;
        iconColor = Colors.red;
        break;
      case LogLevel.warning:
        iconData = Icons.warning;
        iconColor = Colors.orange;
        break;
      case LogLevel.info:
      default:
        iconData = Icons.info;
        iconColor = Colors.blue;
        break;
    }

    return Icon(iconData, size: 16, color: iconColor);
  }

  Color _getTextColor() {
    switch (level) {
      case LogLevel.success:
        return Colors.green.shade700;
      case LogLevel.error:
        return Colors.red.shade700;
      case LogLevel.warning:
        return Colors.orange.shade700;
      case LogLevel.info:
      default:
        return Colors.black87;
    }
  }

  String _formatTimestamp() {
    final hour = timestamp.hour.toString().padLeft(2, '0');
    final minute = timestamp.minute.toString().padLeft(2, '0');
    final second = timestamp.second.toString().padLeft(2, '0');
    final millisecond = timestamp.millisecond.toString().padLeft(3, '0');
    return '$hour:$minute:$second.$millisecond';
  }
}

class DebugLog {
  final DateTime timestamp;
  final String message;
  final LogLevel level;

  DebugLog({
    required this.message,
    required this.level,
  }) : timestamp = DateTime.now();
}
