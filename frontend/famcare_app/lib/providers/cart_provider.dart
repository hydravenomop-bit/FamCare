import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/cart_item.dart';

class CartNotifier extends StateNotifier<List<CartItem>> {
  CartNotifier() : super([]);

  void addItem(CartItem item) {
    if (state.any((i) => i.uniqueKey == item.uniqueKey)) {
      return; // Already in cart
    }
    state = [...state, item];
  }

  void removeItem(String uniqueKey) {
    state = state.where((i) => i.uniqueKey != uniqueKey).toList();
  }

  void clear() {
    state = [];
  }

  double get totalPrice =>
      state.fold(0.0, (sum, item) => sum + item.price);
}

final cartProvider =
    StateNotifierProvider<CartNotifier, List<CartItem>>((ref) {
  return CartNotifier();
});

final cartTotalProvider = Provider<double>((ref) {
  final items = ref.watch(cartProvider);
  return items.fold(0.0, (sum, item) => sum + item.price);
});

final cartCountProvider = Provider<int>((ref) {
  return ref.watch(cartProvider).length;
});
