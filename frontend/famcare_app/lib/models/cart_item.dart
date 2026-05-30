class CartItem {
  final String serviceId;
  final String serviceName;
  final String caregiverId;
  final String caregiverName;
  final String date;
  final String startTime;
  final String endTime;
  final int durationMinutes;
  final double price;

  const CartItem({
    required this.serviceId,
    required this.serviceName,
    required this.caregiverId,
    required this.caregiverName,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.durationMinutes,
    required this.price,
  });

  String get uniqueKey => '$serviceId-$caregiverId-$date-$startTime';

  Map<String, dynamic> toCheckoutJson() {
    return {
      'service_id': serviceId,
      'caregiver_id': caregiverId,
      'start_time': startTime,
      'date': date,
    };
  }
}
