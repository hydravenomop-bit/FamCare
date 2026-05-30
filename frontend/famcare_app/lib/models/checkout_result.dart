class CheckoutResult {
  final bool success;
  final String? bookingId;
  final double? totalPrice;
  final List<CheckoutItem>? items;
  final String? errorMessage;
  final List<FailedItem>? failedItems;

  const CheckoutResult.success({
    required this.bookingId,
    required this.totalPrice,
    required this.items,
  })  : success = true,
        errorMessage = null,
        failedItems = null;

  const CheckoutResult.failure({
    required this.errorMessage,
    required this.failedItems,
  })  : success = false,
        bookingId = null,
        totalPrice = null,
        items = null;

  factory CheckoutResult.fromSuccessJson(Map<String, dynamic> json) {
    return CheckoutResult.success(
      bookingId: json['booking_id'] as String,
      totalPrice: (json['total_price'] as num).toDouble(),
      items: (json['items'] as List)
          .map((i) => CheckoutItem.fromJson(i as Map<String, dynamic>))
          .toList(),
    );
  }

  factory CheckoutResult.fromErrorJson(Map<String, dynamic> json) {
    return CheckoutResult.failure(
      errorMessage: json['message'] as String? ?? 'Checkout failed',
      failedItems: (json['failed_items'] as List?)
              ?.map((i) => FailedItem.fromJson(i as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class CheckoutItem {
  final String serviceName;
  final String caregiverName;
  final String date;
  final String startTime;
  final String endTime;
  final int durationMinutes;
  final double price;

  const CheckoutItem({
    required this.serviceName,
    required this.caregiverName,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.durationMinutes,
    required this.price,
  });

  factory CheckoutItem.fromJson(Map<String, dynamic> json) {
    return CheckoutItem(
      serviceName: json['service_name'] as String,
      caregiverName: json['caregiver_name'] as String,
      date: json['date'] as String,
      startTime: json['start_time'] as String,
      endTime: json['end_time'] as String,
      durationMinutes: json['duration_minutes'] as int,
      price: (json['price'] as num).toDouble(),
    );
  }
}

class FailedItem {
  final int index;
  final String reason;
  final String slotDate;
  final String startTime;

  const FailedItem({
    required this.index,
    required this.reason,
    required this.slotDate,
    required this.startTime,
  });

  factory FailedItem.fromJson(Map<String, dynamic> json) {
    return FailedItem(
      index: json['index'] as int,
      reason: json['reason'] as String,
      slotDate: json['slot_date'] as String,
      startTime: json['start_time'] as String,
    );
  }
}
