import 'package:flutter/foundation.dart';

import 'dart:io' show Platform;

class AppConstants {
  static String get apiBaseUrl {
    if (kIsWeb) return 'http://localhost:8000/api/v1';
    if (!kIsWeb && (Platform.isMacOS || Platform.isWindows || Platform.isLinux)) return 'http://localhost:8000/api/v1';
    return 'http://10.0.2.2:8000/api/v1';
  }

  static const String defaultPatientId =
      'pt-john0-0001-0001-000000000001';
}
