/// Utilities for converting Buddhist Era dates to Gregorian calendar.
library;

class DateConverter {
  /// Convert Buddhist Era date string to DateTime (Gregorian calendar)
  ///
  /// Thai ID cards store dates in Buddhist Era format (YYYYMMDD)
  /// where year = Gregorian year + 543
  ///
  /// Example: 25380220 = February 20, 1995 (2538 - 543 = 1995)
  static DateTime? parseBuddhistDate(String dateStr) {
    if (dateStr.isEmpty || dateStr.length != 8) {
      return null;
    }

    try {
      // Parse Buddhist Era year and convert to Gregorian
      final buddhistYear = int.parse(dateStr.substring(0, 4));
      final gregorianYear = buddhistYear - 543;
      final month = int.parse(dateStr.substring(4, 6));
      final day = int.parse(dateStr.substring(6, 8));

      return DateTime(gregorianYear, month, day);
    } catch (e) {
      return null;
    }
  }

  /// Format date to Thai Buddhist Era string
  static String formatToBuddhistEra(DateTime date) {
    final buddhistYear = date.year + 543;
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '$buddhistYear$month$day';
  }

  /// Format DateTime to readable string
  static String formatDate(DateTime date) {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return '${date.day} ${months[date.month - 1]} ${date.year}';
  }

  /// Calculate age from birth date
  static int calculateAge(DateTime birthDate) {
    final now = DateTime.now();
    int age = now.year - birthDate.year;

    if (now.month < birthDate.month ||
        (now.month == birthDate.month && now.day < birthDate.day)) {
      age--;
    }

    return age;
  }

  /// Check if date is expired
  static bool isExpired(DateTime expiryDate) {
    return DateTime.now().isAfter(expiryDate);
  }

  /// Days until expiry (negative if expired)
  static int daysUntilExpiry(DateTime expiryDate) {
    return expiryDate.difference(DateTime.now()).inDays;
  }
}
