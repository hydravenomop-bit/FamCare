import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/slot.dart';
import '../services/api_service.dart';
import 'service_provider.dart';

class SlotQuery {
  final String serviceId;
  final String date;

  const SlotQuery({required this.serviceId, required this.date});

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is SlotQuery &&
          runtimeType == other.runtimeType &&
          serviceId == other.serviceId &&
          date == other.date;

  @override
  int get hashCode => serviceId.hashCode ^ date.hashCode;
}

final slotAvailabilityProvider =
    FutureProvider.family<SlotAvailability, SlotQuery>((ref, query) async {
  final api = ref.read(apiServiceProvider);
  return api.getAvailableSlots(
    serviceId: query.serviceId,
    date: query.date,
  );
});
