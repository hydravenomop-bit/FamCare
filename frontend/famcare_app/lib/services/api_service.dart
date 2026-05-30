import 'package:dio/dio.dart';

import '../config/constants.dart';
import '../models/service.dart';
import '../models/slot.dart';
import '../models/checkout_result.dart';

class ApiService {
  late final Dio _dio;

  ApiService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 10),
        headers: {'Content-Type': 'application/json'},
      ),
    );
  }


  Future<List<Service>> getServices() async {
    final response = await _dio.get('/services');
    return (response.data as List)
        .map((s) => Service.fromJson(s as Map<String, dynamic>))
        .toList();
  }


  Future<SlotAvailability> getAvailableSlots({
    required String serviceId,
    required String date,
  }) async {
    final response = await _dio.get(
      '/slots/available',
      queryParameters: {'service_id': serviceId, 'date': date},
    );
    return SlotAvailability.fromJson(response.data as Map<String, dynamic>);
  }


  Future<CheckoutResult> checkout({
    required String patientId,
    required List<Map<String, dynamic>> items,
  }) async {
    try {
      final response = await _dio.post(
        '/cart/checkout',
        data: {
          'patient_id': patientId,
          'items': items,
        },
      );
      return CheckoutResult.fromSuccessJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      if (e.response?.statusCode == 409) {
        return CheckoutResult.fromErrorJson(
          e.response!.data as Map<String, dynamic>,
        );
      }
      rethrow;
    }
  }
}
