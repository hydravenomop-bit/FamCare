import 'caregiver.dart';

class AvailableSlot {
  final String startTime;
  final String endTime;
  final List<Caregiver> availableCaregivers;

  const AvailableSlot({
    required this.startTime,
    required this.endTime,
    required this.availableCaregivers,
  });

  factory AvailableSlot.fromJson(Map<String, dynamic> json) {
    return AvailableSlot(
      startTime: json['start_time'] as String,
      endTime: json['end_time'] as String,
      availableCaregivers: (json['available_caregivers'] as List)
          .map((c) => Caregiver.fromJson(c as Map<String, dynamic>))
          .toList(),
    );
  }
}

class SlotAvailability {
  final String serviceId;
  final String serviceName;
  final int durationMinutes;
  final String date;
  final List<AvailableSlot> slots;

  const SlotAvailability({
    required this.serviceId,
    required this.serviceName,
    required this.durationMinutes,
    required this.date,
    required this.slots,
  });

  factory SlotAvailability.fromJson(Map<String, dynamic> json) {
    return SlotAvailability(
      serviceId: json['service_id'] as String,
      serviceName: json['service_name'] as String,
      durationMinutes: json['duration_minutes'] as int,
      date: json['date'] as String,
      slots: (json['slots'] as List)
          .map((s) => AvailableSlot.fromJson(s as Map<String, dynamic>))
          .toList(),
    );
  }
}
