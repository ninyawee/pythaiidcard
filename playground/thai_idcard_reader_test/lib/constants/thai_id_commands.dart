/// APDU command constants for Thai National ID Card.
library;

class ThaiIDCommands {
  /// SELECT APPLET command
  static const selectApplet = '00A404000800';

  /// Thai ID Card applet identifier
  static const thaiIDApplet = 'A000000054480001';

  /// Full SELECT APPLET command with applet ID
  static String get fullSelectCommand => selectApplet + thaiIDApplet;

  /// Citizen ID (13 digits)
  static const cidCommand = '80B000040200000D';
  static const cidDescription = 'Citizen ID (13 digits)';

  /// Full name in Thai
  static const thaiFullnameCommand = '80B00011020064';
  static const thaiFullnameDescription = 'Full name in Thai';

  /// Full name in English
  static const englishFullnameCommand = '80B00075020064';
  static const englishFullnameDescription = 'Full name in English';

  /// Date of birth (YYYYMMDD in Buddhist Era)
  static const dateOfBirthCommand = '80B000D9020008';
  static const dateOfBirthDescription = 'Date of birth (YYYYMMDD in Buddhist Era)';

  /// Gender (1=Male, 2=Female)
  static const genderCommand = '80B000E1020001';
  static const genderDescription = 'Gender (1=Male, 2=Female)';

  /// Card issuing organization
  static const cardIssuerCommand = '80B000F6020064';
  static const cardIssuerDescription = 'Card issuing organization';

  /// Card issue date (YYYYMMDD in Buddhist Era)
  static const issueDateCommand = '80B00167020008';
  static const issueDateDescription = 'Card issue date (YYYYMMDD in Buddhist Era)';

  /// Card expiry date (YYYYMMDD in Buddhist Era)
  static const expireDateCommand = '80B0016F020008';
  static const expireDateDescription = 'Card expiry date (YYYYMMDD in Buddhist Era)';

  /// Registered address
  static const addressCommand = '80B01579020064';
  static const addressDescription = 'Registered address';

  /// Photo commands (20 parts, 255 bytes each = 5,100 bytes total JPEG)
  static const photoCommands = [
    '80B0017B0200FF', // Part 1/20
    '80B0027A0200FF', // Part 2/20
    '80B003790200FF', // Part 3/20
    '80B004780200FF', // Part 4/20
    '80B005770200FF', // Part 5/20
    '80B006760200FF', // Part 6/20
    '80B007750200FF', // Part 7/20
    '80B008740200FF', // Part 8/20
    '80B009730200FF', // Part 9/20
    '80B00A720200FF', // Part 10/20
    '80B00B710200FF', // Part 11/20
    '80B00C700200FF', // Part 12/20
    '80B00D6F0200FF', // Part 13/20
    '80B00E6E0200FF', // Part 14/20
    '80B00F6D0200FF', // Part 15/20
    '80B0106C0200FF', // Part 16/20
    '80B0116B0200FF', // Part 17/20
    '80B0126A0200FF', // Part 18/20
    '80B013690200FF', // Part 19/20
    '80B014680200FF', // Part 20/20
  ];

  /// Get the appropriate GET RESPONSE command based on ATR
  ///
  /// Different readers return different ATR values:
  /// - ATR starting with 3B67 uses: 00 C0 00 01
  /// - All others use: 00 C0 00 00
  static String getReadRequestCommand(String atr) {
    if (atr.toUpperCase().startsWith('3B67')) {
      return '00C00001';
    }
    return '00C00000';
  }
}

class ResponseStatus {
  /// Check if response indicates success
  ///
  /// Returns true for:
  /// - 90 00: Success
  /// - 61 XX: Success with more data available
  static bool isSuccess(String response) {
    if (response.length < 4) return false;

    final statusBytes = response.substring(response.length - 4).toUpperCase();

    // Success: 90 00
    if (statusBytes == '9000') return true;

    // Success with more data: 61 XX
    if (statusBytes.startsWith('61')) return true;

    return false;
  }

  /// Check if more data is available (61 XX)
  static bool hasMoreData(String response) {
    if (response.length < 4) return false;
    final statusBytes = response.substring(response.length - 4).toUpperCase();
    return statusBytes.startsWith('61');
  }

  /// Get status code description
  static String getStatusDescription(String response) {
    if (response.length < 4) return 'Invalid response';

    final statusBytes = response.substring(response.length - 4).toUpperCase();

    if (statusBytes == '9000') return 'Success';
    if (statusBytes.startsWith('61')) {
      final length = int.parse(statusBytes.substring(2), radix: 16);
      return 'Success ($length bytes available)';
    }
    if (statusBytes.startsWith('6C')) return 'Wrong length';
    if (statusBytes == '6986') return 'Command not allowed';
    if (statusBytes == '6A86') return 'Wrong parameters';
    if (statusBytes == '6A82') return 'File not found';

    return 'Unknown status: $statusBytes';
  }

  /// Remove status bytes from response data
  static String removeStatusBytes(String response) {
    if (response.length < 4) return response;
    return response.substring(0, response.length - 4);
  }
}
