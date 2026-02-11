import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:ccid/ccid.dart';

import 'constants/thai_id_commands.dart';
import 'models/thai_id_card.dart';
import 'utils/apdu_parser.dart';
import 'utils/date_converter.dart';
import 'widgets/debug_section.dart';
import 'widgets/debug_log_entry.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Thai ID Card Reader - Debug Interface',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const ThaiIDReaderDebugPage(),
    );
  }
}

class ThaiIDReaderDebugPage extends StatefulWidget {
  const ThaiIDReaderDebugPage({super.key});

  @override
  State<ThaiIDReaderDebugPage> createState() => _ThaiIDReaderDebugPageState();
}

class _ThaiIDReaderDebugPageState extends State<ThaiIDReaderDebugPage> {
  final _ccid = Ccid();

  // State
  List<String> _readers = [];
  String? _selectedReader;
  CcidCard? _card;
  String? _atr;
  ThaiIDCard _cardData = ThaiIDCard();
  final List<DebugLog> _logs = [];
  bool _isConnected = false;
  bool _isAppletSelected = false;
  double _photoProgress = 0.0;
  final List<String> _photoResponses = [];

  @override
  void initState() {
    super.initState();
    _refreshReaders();
  }

  // Logging
  void _addLog(String message, LogLevel level) {
    setState(() {
      _logs.insert(0, DebugLog(message: message, level: level));
      if (_logs.length > 100) _logs.removeLast();
    });
  }

  void _clearLogs() {
    setState(() {
      _logs.clear();
    });
  }

  // Copy to Clipboard
  Future<void> _copyToClipboard(String text, String fieldName) async {
    await Clipboard.setData(ClipboardData(text: text));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$fieldName copied to clipboard'),
          duration: const Duration(seconds: 2),
          behavior: SnackBarBehavior.floating,
          width: 300,
        ),
      );
    }
    _addLog('Copied $fieldName to clipboard', LogLevel.info);
  }

  String _generateAllDataText() {
    final buffer = StringBuffer();
    buffer.writeln('=== Thai National ID Card Data ===\n');

    if (_cardData.formattedCid != null) {
      buffer.writeln('Citizen ID: ${_cardData.formattedCid}');
    }
    if (_cardData.thaiFullname != null) {
      buffer.writeln('Thai Name: ${_cardData.thaiFullname}');
    }
    if (_cardData.englishFullname != null) {
      buffer.writeln('English Name: ${_cardData.englishFullname}');
    }
    if (_cardData.dateOfBirth != null) {
      buffer.writeln('Date of Birth: ${DateConverter.formatDate(_cardData.dateOfBirth!)} (Age: ${_cardData.age})');
    }
    if (_cardData.genderText != null) {
      buffer.writeln('Gender: ${_cardData.genderText}');
    }
    if (_cardData.cardIssuer != null) {
      buffer.writeln('Card Issuer: ${_cardData.cardIssuer}');
    }
    if (_cardData.issueDate != null) {
      buffer.writeln('Issue Date: ${DateConverter.formatDate(_cardData.issueDate!)}');
    }
    if (_cardData.expiryDate != null) {
      final expired = _cardData.isExpired;
      final days = _cardData.daysUntilExpiry;
      buffer.writeln('Expiry Date: ${DateConverter.formatDate(_cardData.expiryDate!)} ${expired ? "(EXPIRED)" : "($days days remaining)"}');
    }
    if (_cardData.address != null) {
      buffer.writeln('Address: ${_cardData.address}');
    }
    if (_cardData.photoBytes != null) {
      buffer.writeln('\nPhoto: ${_cardData.photoBytes!.length} bytes (JPEG)');
    }

    buffer.writeln('\n=== End of Card Data ===');
    return buffer.toString();
  }

  Future<void> _copyAllData() async {
    final allData = _generateAllDataText();
    await _copyToClipboard(allData, 'All card data');
  }

  // Reader Detection
  Future<void> _refreshReaders() async {
    try {
      _addLog('Scanning for smartcard readers...', LogLevel.info);
      final readers = await _ccid.listReaders();

      setState(() {
        _readers = readers;
        _selectedReader = readers.isNotEmpty ? readers[0] : null;
      });

      if (readers.isEmpty) {
        _addLog('No readers found. Please connect a smartcard reader.', LogLevel.warning);
      } else {
        _addLog('Found ${readers.length} reader(s): ${readers.join(", ")}', LogLevel.success);
      }
    } catch (e) {
      _addLog('Error scanning readers: $e', LogLevel.error);
    }
  }

  // Card Connection
  Future<void> _connectCard() async {
    if (_selectedReader == null) {
      _addLog('No reader selected', LogLevel.error);
      return;
    }

    try {
      _addLog('Connecting to card in reader: $_selectedReader', LogLevel.info);
      final card = await _ccid.connect(_selectedReader!);

      // Get ATR
      final atr = card.atr;

      setState(() {
        _card = card;
        _atr = atr;
        _isConnected = true;
      });

      _addLog('Card connected successfully', LogLevel.success);
      _addLog('ATR: $atr', LogLevel.info);

      // Parse ATR info
      if (atr != null) {
        final atrUpper = atr.toUpperCase();
        if (atrUpper.startsWith('3B67')) {
          _addLog('ATR type: 3B67 variant (will use GET RESPONSE 00 C0 00 01)', LogLevel.info);
        } else {
          _addLog('ATR type: Standard (will use GET RESPONSE 00 C0 00 00)', LogLevel.info);
        }
      }
    } catch (e) {
      _addLog('Error connecting to card: $e', LogLevel.error);
    }
  }

  Future<void> _disconnectCard() async {
    if (_card != null) {
      try {
        await _card!.disconnect();
        setState(() {
          _card = null;
          _atr = null;
          _isConnected = false;
          _isAppletSelected = false;
          _cardData = ThaiIDCard();
        });
        _addLog('Card disconnected', LogLevel.info);
      } catch (e) {
        _addLog('Error disconnecting: $e', LogLevel.error);
      }
    }
  }

  // Select Thai ID Applet
  Future<void> _selectApplet() async {
    if (_card == null) {
      _addLog('Card not connected', LogLevel.error);
      return;
    }

    try {
      _addLog('Sending SELECT APPLET command...', LogLevel.info);
      final command = ThaiIDCommands.fullSelectCommand;
      _addLog('Command: $command', LogLevel.info);

      final response = await _card!.transceive(command);

      if (response == null) {
        _addLog('No response from card', LogLevel.error);
        return;
      }

      _addLog('Response: $response', LogLevel.info);

      if (ResponseStatus.isSuccess(response)) {
        setState(() {
          _isAppletSelected = true;
        });
        final statusDesc = ResponseStatus.getStatusDescription(response);
        _addLog('Applet selected successfully: $statusDesc', LogLevel.success);
      } else {
        _addLog('Failed to select applet: ${ResponseStatus.getStatusDescription(response)}', LogLevel.error);
      }
    } catch (e) {
      _addLog('Error selecting applet: $e', LogLevel.error);
    }
  }

  // Read Individual Fields
  Future<void> _readCid() async {
    await _readField(
      command: ThaiIDCommands.cidCommand,
      fieldName: 'CID',
      parser: (response) {
        final cid = ApduParser.parseCid(ResponseStatus.removeStatusBytes(response));
        _cardData = _cardData.copyWith(cid: cid);
        return ApduParser.formatCid(cid);
      },
    );
  }

  Future<void> _readThaiName() async {
    await _readField(
      command: ThaiIDCommands.thaiFullnameCommand,
      fieldName: 'Thai Name',
      parser: (response) {
        final name = ApduParser.parseThaiText(ResponseStatus.removeStatusBytes(response));
        _cardData = _cardData.copyWith(thaiFullname: name);
        return name;
      },
    );
  }

  Future<void> _readEnglishName() async {
    await _readField(
      command: ThaiIDCommands.englishFullnameCommand,
      fieldName: 'English Name',
      parser: (response) {
        final name = ApduParser.parseEnglishText(ResponseStatus.removeStatusBytes(response));
        _cardData = _cardData.copyWith(englishFullname: name);
        return name;
      },
    );
  }

  Future<void> _readDateOfBirth() async {
    await _readField(
      command: ThaiIDCommands.dateOfBirthCommand,
      fieldName: 'Date of Birth',
      parser: (response) {
        final date = ApduParser.parseDate(ResponseStatus.removeStatusBytes(response));
        if (date != null) {
          _cardData = _cardData.copyWith(dateOfBirth: date);
          return '${DateConverter.formatDate(date)} (Age: ${DateConverter.calculateAge(date)})';
        }
        return 'Invalid date';
      },
    );
  }

  Future<void> _readGender() async {
    await _readField(
      command: ThaiIDCommands.genderCommand,
      fieldName: 'Gender',
      parser: (response) {
        final gender = ApduParser.parseGender(ResponseStatus.removeStatusBytes(response));
        _cardData = _cardData.copyWith(gender: gender == 'Male' ? '1' : '2');
        return gender;
      },
    );
  }

  Future<void> _readCardIssuer() async {
    await _readField(
      command: ThaiIDCommands.cardIssuerCommand,
      fieldName: 'Card Issuer',
      parser: (response) {
        final issuer = ApduParser.parseThaiText(ResponseStatus.removeStatusBytes(response));
        _cardData = _cardData.copyWith(cardIssuer: issuer);
        return issuer;
      },
    );
  }

  Future<void> _readIssueDate() async {
    await _readField(
      command: ThaiIDCommands.issueDateCommand,
      fieldName: 'Issue Date',
      parser: (response) {
        final date = ApduParser.parseDate(ResponseStatus.removeStatusBytes(response));
        if (date != null) {
          _cardData = _cardData.copyWith(issueDate: date);
          return DateConverter.formatDate(date);
        }
        return 'Invalid date';
      },
    );
  }

  Future<void> _readExpiryDate() async {
    await _readField(
      command: ThaiIDCommands.expireDateCommand,
      fieldName: 'Expiry Date',
      parser: (response) {
        final date = ApduParser.parseDate(ResponseStatus.removeStatusBytes(response));
        if (date != null) {
          _cardData = _cardData.copyWith(expiryDate: date);
          final days = DateConverter.daysUntilExpiry(date);
          final expired = DateConverter.isExpired(date);
          return '${DateConverter.formatDate(date)} (${expired ? "EXPIRED" : "$days days remaining"})';
        }
        return 'Invalid date';
      },
    );
  }

  Future<void> _readAddress() async {
    await _readField(
      command: ThaiIDCommands.addressCommand,
      fieldName: 'Address',
      parser: (response) {
        final address = ApduParser.parseThaiText(ResponseStatus.removeStatusBytes(response));
        _cardData = _cardData.copyWith(address: address);
        return address;
      },
    );
  }

  Future<void> _readField({
    required String command,
    required String fieldName,
    required String Function(String) parser,
  }) async {
    if (_card == null || !_isAppletSelected) {
      _addLog('Card not ready. Connect and select applet first.', LogLevel.error);
      return;
    }

    try {
      _addLog('Reading $fieldName...', LogLevel.info);
      final response = await _card!.transceive(command);

      if (response == null) {
        _addLog('No response for $fieldName', LogLevel.error);
        return;
      }

      if (ResponseStatus.isSuccess(response)) {
        // May need GET RESPONSE for more data
        String finalResponse = response;

        if (ResponseStatus.hasMoreData(response)) {
          final getResponseCmd = ThaiIDCommands.getReadRequestCommand(_atr ?? '');
          final moreData = await _card!.transceive(getResponseCmd);
          if (moreData != null) {
            finalResponse = moreData;
          }
        }

        final parsedValue = parser(finalResponse);
        _addLog('$fieldName: $parsedValue', LogLevel.success);
        setState(() {});
      } else {
        _addLog('Failed to read $fieldName: ${ResponseStatus.getStatusDescription(response)}', LogLevel.error);
      }
    } catch (e) {
      _addLog('Error reading $fieldName: $e', LogLevel.error);
    }
  }

  // Read Photo
  Future<void> _readPhoto() async {
    if (_card == null || !_isAppletSelected) {
      _addLog('Card not ready. Connect and select applet first.', LogLevel.error);
      return;
    }

    try {
      _addLog('Starting photo read (20 parts)...', LogLevel.info);
      setState(() {
        _photoProgress = 0.0;
        _photoResponses.clear();
      });

      for (int i = 0; i < ThaiIDCommands.photoCommands.length; i++) {
        final command = ThaiIDCommands.photoCommands[i];
        _addLog('Reading photo part ${i + 1}/20...', LogLevel.info);

        final response = await _card!.transceive(command);

        if (response == null || !ResponseStatus.isSuccess(response)) {
          _addLog('Failed to read photo part ${i + 1}', LogLevel.error);
          return;
        }

        // May need GET RESPONSE
        String finalResponse = response;
        if (ResponseStatus.hasMoreData(response)) {
          final getResponseCmd = ThaiIDCommands.getReadRequestCommand(_atr ?? '');
          final moreData = await _card!.transceive(getResponseCmd);
          if (moreData != null) {
            finalResponse = moreData;
          }
        }

        _photoResponses.add(finalResponse);

        setState(() {
          _photoProgress = (i + 1) / ThaiIDCommands.photoCommands.length;
        });
      }

      // Assemble photo
      final photoBytes = ApduParser.assemblePhoto(_photoResponses);
      _cardData = _cardData.copyWith(photoBytes: photoBytes);

      _addLog('Photo read complete! ${photoBytes.length} bytes', LogLevel.success);
      setState(() {});
    } catch (e) {
      _addLog('Error reading photo: $e', LogLevel.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Thai ID Card Reader - Debug Interface'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Reader Detection Section
            _buildReaderSection(),

            // Card Connection Section
            _buildConnectionSection(),

            // Applet Selection Section
            _buildAppletSection(),

            // Data Reading Section
            _buildDataReadingSection(),

            // Photo Section
            _buildPhotoSection(),

            // Debug Log Section
            _buildDebugLogSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildReaderSection() {
    return DebugSection(
      title: '1. Reader Detection',
      headerColor: Colors.blue.shade50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ElevatedButton.icon(
                onPressed: _refreshReaders,
                icon: const Icon(Icons.refresh),
                label: const Text('Refresh Readers'),
              ),
              const SizedBox(width: 16),
              Text(
                _readers.isEmpty ? 'No readers found' : '${_readers.length} reader(s) found',
                style: TextStyle(
                  color: _readers.isEmpty ? Colors.red : Colors.green,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          if (_readers.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text('Select Reader:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButton<String>(
              value: _selectedReader,
              isExpanded: true,
              items: _readers.map((reader) {
                return DropdownMenuItem(value: reader, child: Text(reader));
              }).toList(),
              onChanged: (value) {
                setState(() {
                  _selectedReader = value;
                });
                _addLog('Selected reader: $value', LogLevel.info);
              },
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildConnectionSection() {
    return DebugSection(
      title: '2. Card Connection',
      headerColor: Colors.green.shade50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ElevatedButton.icon(
                onPressed: _isConnected ? null : _connectCard,
                icon: const Icon(Icons.credit_card),
                label: const Text('Connect to Card'),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: _isConnected ? _disconnectCard : null,
                icon: const Icon(Icons.cancel),
                label: const Text('Disconnect'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red.shade100,
                ),
              ),
              const SizedBox(width: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _isConnected ? Colors.green.shade100 : Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _isConnected ? Icons.check_circle : Icons.cancel,
                      size: 16,
                      color: _isConnected ? Colors.green : Colors.grey,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      _isConnected ? 'Connected' : 'Disconnected',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (_atr != null) ...[
            const SizedBox(height: 12),
            const Text('ATR (Answer To Reset):', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            SelectableText(
              _atr!,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAppletSection() {
    return DebugSection(
      title: '3. Thai ID Applet Selection',
      headerColor: Colors.orange.shade50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ElevatedButton.icon(
                onPressed: _isConnected && !_isAppletSelected ? _selectApplet : null,
                icon: const Icon(Icons.app_registration),
                label: const Text('Select Thai ID Applet'),
              ),
              const SizedBox(width: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _isAppletSelected ? Colors.green.shade100 : Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      _isAppletSelected ? Icons.check_circle : Icons.pending,
                      size: 16,
                      color: _isAppletSelected ? Colors.green : Colors.grey,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      _isAppletSelected ? 'Applet Selected' : 'Not Selected',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Applet ID: ${ThaiIDCommands.thaiIDApplet}',
            style: const TextStyle(fontFamily: 'monospace', fontSize: 11, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildDataReadingSection() {
    return DebugSection(
      title: '4. Data Reading',
      headerColor: Colors.purple.shade50,
      initiallyExpanded: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Copy All Data Button
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: ElevatedButton.icon(
              onPressed: _cardData.isComplete ? _copyAllData : null,
              icon: const Icon(Icons.copy_all),
              label: const Text('Copy All Data'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade100,
                foregroundColor: Colors.blue.shade900,
              ),
            ),
          ),
          const Divider(),
          const SizedBox(height: 8),
          _buildFieldReadButton('Read CID', _readCid, _cardData.formattedCid, 'CID'),
          _buildFieldReadButton('Read Thai Name', _readThaiName, _cardData.thaiFullname, 'Thai Name'),
          _buildFieldReadButton('Read English Name', _readEnglishName, _cardData.englishFullname, 'English Name'),
          _buildFieldReadButton(
            'Read Date of Birth',
            _readDateOfBirth,
            _cardData.dateOfBirth != null
                ? '${DateConverter.formatDate(_cardData.dateOfBirth!)} (Age: ${_cardData.age})'
                : null,
            'Date of Birth',
          ),
          _buildFieldReadButton('Read Gender', _readGender, _cardData.genderText, 'Gender'),
          _buildFieldReadButton('Read Card Issuer', _readCardIssuer, _cardData.cardIssuer, 'Card Issuer'),
          _buildFieldReadButton(
            'Read Issue Date',
            _readIssueDate,
            _cardData.issueDate != null ? DateConverter.formatDate(_cardData.issueDate!) : null,
            'Issue Date',
          ),
          _buildFieldReadButton(
            'Read Expiry Date',
            _readExpiryDate,
            _cardData.expiryDate != null
                ? '${DateConverter.formatDate(_cardData.expiryDate!)} ${_cardData.isExpired ? "(EXPIRED)" : "(${_cardData.daysUntilExpiry} days)"}'
                : null,
            'Expiry Date',
          ),
          _buildFieldReadButton('Read Address', _readAddress, _cardData.address, 'Address'),
        ],
      ),
    );
  }

  Widget _buildFieldReadButton(String label, VoidCallback onPressed, String? value, String fieldName) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 180,
            child: ElevatedButton(
              onPressed: _isAppletSelected ? onPressed : null,
              child: Text(label),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: value != null
                ? SelectableText(
                    value,
                    style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green),
                  )
                : const Text('—', style: TextStyle(color: Colors.grey)),
          ),
          const SizedBox(width: 8),
          IconButton(
            onPressed: value != null ? () => _copyToClipboard(value, fieldName) : null,
            icon: const Icon(Icons.copy, size: 18),
            tooltip: 'Copy $fieldName',
            visualDensity: VisualDensity.compact,
            iconSize: 18,
            padding: const EdgeInsets.all(4),
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
          ),
        ],
      ),
    );
  }

  Widget _buildPhotoSection() {
    return DebugSection(
      title: '5. Photo Reading',
      headerColor: Colors.teal.shade50,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ElevatedButton.icon(
            onPressed: _isAppletSelected ? _readPhoto : null,
            icon: const Icon(Icons.photo_camera),
            label: const Text('Read Photo (20 parts)'),
          ),
          if (_photoProgress > 0) ...[
            const SizedBox(height: 12),
            LinearProgressIndicator(value: _photoProgress),
            const SizedBox(height: 4),
            Text('Progress: ${(_photoProgress * 100).toStringAsFixed(0)}%'),
          ],
          if (_cardData.photoBytes != null && _cardData.photoBytes!.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Photo: ${_cardData.photoBytes!.length} bytes'),
            const SizedBox(height: 8),
            Image.memory(
              Uint8List.fromList(_cardData.photoBytes!),
              width: 200,
              height: 250,
              fit: BoxFit.cover,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDebugLogSection() {
    return DebugSection(
      title: '6. Debug Log',
      headerColor: Colors.grey.shade200,
      initiallyExpanded: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('${_logs.length} log entries', style: const TextStyle(fontWeight: FontWeight.bold)),
              TextButton.icon(
                onPressed: _clearLogs,
                icon: const Icon(Icons.clear_all, size: 18),
                label: const Text('Clear Log'),
              ),
            ],
          ),
          const Divider(),
          Container(
            height: 300,
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: Colors.grey.shade300),
            ),
            child: _logs.isEmpty
                ? const Center(child: Text('No logs yet', style: TextStyle(color: Colors.grey)))
                : ListView.builder(
                    reverse: false,
                    itemCount: _logs.length,
                    itemBuilder: (context, index) {
                      final log = _logs[index];
                      return DebugLogEntry(
                        timestamp: log.timestamp,
                        message: log.message,
                        level: log.level,
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
