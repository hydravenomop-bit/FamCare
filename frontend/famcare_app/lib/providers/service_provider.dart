import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/api_service.dart';
import '../models/service.dart';

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());

final servicesProvider = FutureProvider<List<Service>>((ref) async {
  final api = ref.read(apiServiceProvider);
  return api.getServices();
});
