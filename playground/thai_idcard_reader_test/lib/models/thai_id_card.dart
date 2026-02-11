/// Data model for Thai National ID Card information.
library;

class ThaiIDCard {
  String? cid;
  String? thaiFullname;
  String? englishFullname;
  DateTime? dateOfBirth;
  String? gender;
  String? cardIssuer;
  DateTime? issueDate;
  DateTime? expiryDate;
  String? address;
  List<int>? photoBytes;

  ThaiIDCard({
    this.cid,
    this.thaiFullname,
    this.englishFullname,
    this.dateOfBirth,
    this.gender,
    this.cardIssuer,
    this.issueDate,
    this.expiryDate,
    this.address,
    this.photoBytes,
  });

  /// Format CID with dashes: X-XXXX-XXXXX-XX-X
  String? get formattedCid {
    if (cid == null || cid!.length != 13) return cid;
    return '${cid!.substring(0, 1)}-${cid!.substring(1, 5)}-'
        '${cid!.substring(5, 10)}-${cid!.substring(10, 12)}-${cid!.substring(12, 13)}';
  }

  /// Get gender text
  String? get genderText {
    if (gender == null) return null;
    return gender == '1' ? 'Male' : 'Female';
  }

  /// Check if card is expired
  bool get isExpired {
    if (expiryDate == null) return false;
    return DateTime.now().isAfter(expiryDate!);
  }

  /// Days until expiry (negative if expired)
  int? get daysUntilExpiry {
    if (expiryDate == null) return null;
    return expiryDate!.difference(DateTime.now()).inDays;
  }

  /// Calculate age from date of birth
  int? get age {
    if (dateOfBirth == null) return null;
    final now = DateTime.now();
    int age = now.year - dateOfBirth!.year;
    if (now.month < dateOfBirth!.month ||
        (now.month == dateOfBirth!.month && now.day < dateOfBirth!.day)) {
      age--;
    }
    return age;
  }

  /// Check if all required fields are present
  bool get isComplete {
    return cid != null &&
        thaiFullname != null &&
        englishFullname != null &&
        dateOfBirth != null &&
        gender != null &&
        address != null;
  }

  /// Copy with method for updating individual fields
  ThaiIDCard copyWith({
    String? cid,
    String? thaiFullname,
    String? englishFullname,
    DateTime? dateOfBirth,
    String? gender,
    String? cardIssuer,
    DateTime? issueDate,
    DateTime? expiryDate,
    String? address,
    List<int>? photoBytes,
  }) {
    return ThaiIDCard(
      cid: cid ?? this.cid,
      thaiFullname: thaiFullname ?? this.thaiFullname,
      englishFullname: englishFullname ?? this.englishFullname,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      gender: gender ?? this.gender,
      cardIssuer: cardIssuer ?? this.cardIssuer,
      issueDate: issueDate ?? this.issueDate,
      expiryDate: expiryDate ?? this.expiryDate,
      address: address ?? this.address,
      photoBytes: photoBytes ?? this.photoBytes,
    );
  }

  @override
  String toString() {
    return 'ThaiIDCard(\n'
        '  CID: ${formattedCid ?? "Not set"}\n'
        '  Thai Name: ${thaiFullname ?? "Not set"}\n'
        '  English Name: ${englishFullname ?? "Not set"}\n'
        '  Date of Birth: ${dateOfBirth?.toString() ?? "Not set"}\n'
        '  Age: ${age?.toString() ?? "Not set"}\n'
        '  Gender: ${genderText ?? "Not set"}\n'
        '  Card Issuer: ${cardIssuer ?? "Not set"}\n'
        '  Issue Date: ${issueDate?.toString() ?? "Not set"}\n'
        '  Expiry Date: ${expiryDate?.toString() ?? "Not set"}\n'
        '  Address: ${address ?? "Not set"}\n'
        '  Photo: ${photoBytes != null ? "${photoBytes!.length} bytes" : "Not set"}\n'
        ')';
  }
}
