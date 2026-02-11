/// Utilities for parsing APDU responses from Thai ID cards.
library;

import 'date_converter.dart';
import 'encoding_utils.dart';

class ApduParser {
  /// Parse Citizen ID (CID) from response
  ///
  /// CID is 13 ASCII digits
  static String parseCid(String response) {
    if (response.length < 26) return ''; // 13 bytes = 26 hex chars

    final cidHex = response.substring(0, 26);
    final cidBytes = _hexToAscii(cidHex);
    return cidBytes;
  }

  /// Format CID with dashes: X-XXXX-XXXXX-XX-X
  static String formatCid(String cid) {
    if (cid.length != 13) return cid;
    return '${cid[0]}-${cid.substring(1, 5)}-'
        '${cid.substring(5, 10)}-${cid.substring(10, 12)}-${cid[12]}';
  }

  /// Validate CID checksum
  ///
  /// Thai CID uses mod-11 checksum algorithm
  static bool validateCid(String cid) {
    if (cid.length != 13 || !RegExp(r'^\d+$').hasMatch(cid)) {
      return false;
    }

    int checksum = 0;
    for (int i = 0; i < 12; i++) {
      checksum += int.parse(cid[i]) * (13 - i);
    }
    checksum = (11 - (checksum % 11)) % 10;

    return checksum == int.parse(cid[12]);
  }

  /// Parse Thai text (name, address, etc.) from TIS-620 encoded response
  static String parseThaiText(String response) {
    return EncodingUtils.tis620ToUtf8(response);
  }

  /// Parse English text (ASCII) from response
  static String parseEnglishText(String response) {
    return _hexToAscii(response).trim();
  }

  /// Parse date from Buddhist Era format (YYYYMMDD)
  static DateTime? parseDate(String response) {
    if (response.length < 16) return null; // 8 bytes = 16 hex chars

    final dateHex = response.substring(0, 16);
    final dateStr = _hexToAscii(dateHex);
    return DateConverter.parseBuddhistDate(dateStr);
  }

  /// Parse gender (1=Male, 2=Female)
  static String parseGender(String response) {
    if (response.length < 2) return '';

    final genderHex = response.substring(0, 2);
    final genderCode = _hexToAscii(genderHex);

    if (genderCode == '1') return 'Male';
    if (genderCode == '2') return 'Female';
    return 'Unknown';
  }

  /// Convert hex string to ASCII string
  static String _hexToAscii(String hex) {
    final cleanHex = hex.replaceAll(' ', '').replaceAll(':', '');
    final buffer = StringBuffer();

    for (int i = 0; i < cleanHex.length; i += 2) {
      if (i + 2 <= cleanHex.length) {
        final byteString = cleanHex.substring(i, i + 2);
        final byte = int.parse(byteString, radix: 16);
        if (byte >= 32 && byte <= 126) { // Printable ASCII
          buffer.write(String.fromCharCode(byte));
        }
      }
    }

    return buffer.toString();
  }

  /// Extract photo bytes from hex responses
  ///
  /// Photo is stored as 20 parts of 255 bytes each (5,100 bytes total JPEG)
  static List<int> assemblePhoto(List<String> photoResponses) {
    final photoBytes = <int>[];

    for (final response in photoResponses) {
      // Remove status bytes (last 4 hex chars = 2 bytes)
      final dataHex = response.substring(0, response.length - 4);
      final bytes = _hexToByteList(dataHex);
      photoBytes.addAll(bytes);
    }

    return photoBytes;
  }

  /// Convert hex string to byte list
  static List<int> _hexToByteList(String hex) {
    final cleanHex = hex.replaceAll(' ', '').replaceAll(':', '');
    final bytes = <int>[];

    for (int i = 0; i < cleanHex.length; i += 2) {
      if (i + 2 <= cleanHex.length) {
        final byteString = cleanHex.substring(i, i + 2);
        bytes.add(int.parse(byteString, radix: 16));
      }
    }

    return bytes;
  }
}
