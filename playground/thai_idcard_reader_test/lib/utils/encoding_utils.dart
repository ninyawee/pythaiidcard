/// Utilities for handling Thai TIS-620 encoding.
library;

import 'dart:convert';
import 'dart:typed_data';

class EncodingUtils {
  /// Convert TIS-620 encoded hex string to UTF-8 string
  ///
  /// TIS-620 is the Thai character encoding used in Thai ID cards.
  /// This function converts TIS-620 bytes to Unicode/UTF-8.
  ///
  /// Note: Dart doesn't have built-in TIS-620 support, so this uses
  /// a mapping table for Thai characters (0xA0-0xFF range)
  static String tis620ToUtf8(String hexString) {
    if (hexString.isEmpty) return '';

    try {
      // Remove spaces and convert hex string to bytes
      final cleanHex = hexString.replaceAll(' ', '').replaceAll(':', '');
      final bytes = _hexToBytes(cleanHex);

      // Convert TIS-620 bytes to Unicode string
      final result = StringBuffer();
      for (final byte in bytes) {
        if (byte == 0x23) { // '#' character used as padding/filler
          result.write(' ');
        } else if (byte < 0x80) {
          // ASCII range (0x00-0x7F) - direct mapping
          result.write(String.fromCharCode(byte));
        } else if (byte >= 0xA0 && byte <= 0xFF) {
          // Thai character range - map to Unicode
          final unicodeChar = _tis620ToUnicode(byte);
          result.write(String.fromCharCode(unicodeChar));
        }
      }

      return result.toString().trim();
    } catch (e) {
      return hexString;
    }
  }

  /// Convert hex string to bytes
  static Uint8List _hexToBytes(String hex) {
    final length = hex.length;
    final bytes = Uint8List(length ~/ 2);

    for (int i = 0; i < length; i += 2) {
      final byteString = hex.substring(i, i + 2);
      bytes[i ~/ 2] = int.parse(byteString, radix: 16);
    }

    return bytes;
  }

  /// Map TIS-620 byte to Unicode code point
  ///
  /// TIS-620 Thai characters (0xA0-0xFF) map to Unicode range 0x0E00-0x0E5F
  /// Offset calculation: Unicode = TIS-620 - 0xA0 + 0x0E00
  static int _tis620ToUnicode(int tis620Byte) {
    if (tis620Byte < 0xA0 || tis620Byte > 0xFF) {
      return tis620Byte;
    }

    // TIS-620 to Unicode Thai mapping
    // Thai Unicode block starts at 0x0E00
    // TIS-620 Thai characters start at 0xA0
    return tis620Byte - 0xA0 + 0x0E00;
  }

  /// Clean and format text (remove excessive spaces, etc.)
  static String cleanText(String text) {
    return text
        .replaceAll('#', ' ')
        .split(RegExp(r'\s+'))
        .where((s) => s.isNotEmpty)
        .join(' ')
        .trim();
  }

  /// Format hex string for display (add spaces every 2 characters)
  static String formatHex(String hex) {
    final cleanHex = hex.replaceAll(' ', '').replaceAll(':', '');
    final formatted = StringBuffer();

    for (int i = 0; i < cleanHex.length; i += 2) {
      if (i > 0) formatted.write(' ');
      formatted.write(cleanHex.substring(i, i + 2));
    }

    return formatted.toString().toUpperCase();
  }

  /// Convert bytes to hex string
  static String bytesToHex(List<int> bytes) {
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join('').toUpperCase();
  }
}
