import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/checkout_result.dart';
import '../services/api_service.dart';
import '../models/cart_item.dart';
import 'service_provider.dart';

class CheckoutState {
  final bool isLoading;
  final CheckoutResult? result;
  final String? error;

  const CheckoutState({
    this.isLoading = false,
    this.result,
    this.error,
  });

  const CheckoutState.initial()
      : isLoading = false,
        result = null,
        error = null;

  const CheckoutState.loading()
      : isLoading = true,
        result = null,
        error = null;

  CheckoutState.success(CheckoutResult r)
      : isLoading = false,
        result = r,
        error = null;

  CheckoutState.failure(String message)
      : isLoading = false,
        result = null,
        error = message;

  CheckoutState.conflict(CheckoutResult r)
      : isLoading = false,
        result = r,
        error = null;
}

class CheckoutNotifier extends StateNotifier<CheckoutState> {
  final ApiService _api;

  CheckoutNotifier(this._api) : super(const CheckoutState.initial());

  Future<void> checkout({
    required String patientId,
    required List<CartItem> items,
  }) async {
    state = const CheckoutState.loading();

    try {
      final result = await _api.checkout(
        patientId: patientId,
        items: items.map((i) => i.toCheckoutJson()).toList(),
      );

      if (result.success) {
        state = CheckoutState.success(result);
      } else {
        state = CheckoutState.conflict(result);
      }
    } catch (e) {
      state = CheckoutState.failure(
        'Checkout failed: ${e.toString()}',
      );
    }
  }

  void reset() {
    state = const CheckoutState.initial();
  }
}

final checkoutProvider =
    StateNotifierProvider<CheckoutNotifier, CheckoutState>((ref) {
  final api = ref.read(apiServiceProvider);
  return CheckoutNotifier(api);
});
