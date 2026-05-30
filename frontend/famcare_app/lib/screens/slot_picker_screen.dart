import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../config/theme.dart';
import '../models/service.dart';
import '../models/cart_item.dart';
import '../models/slot.dart';
import '../providers/slot_provider.dart';
import '../providers/cart_provider.dart';

class SlotPickerScreen extends ConsumerStatefulWidget {
  final Service service;

  const SlotPickerScreen({super.key, required this.service});

  @override
  ConsumerState<SlotPickerScreen> createState() => _SlotPickerScreenState();
}

class _SlotPickerScreenState extends ConsumerState<SlotPickerScreen> {
  late DateTime _selectedDate;
  final ScrollController _dateScrollController = ScrollController();
  late List<DateTime> _availableDates;

  @override
  void initState() {
    super.initState();
    _availableDates = List.generate(
      14, 
      (i) => DateTime.now().add(Duration(days: i + 1))
    );
    _selectedDate = _availableDates[0];
  }

  String get _dateString => DateFormat('yyyy-MM-dd').format(_selectedDate);

  SlotQuery get _currentQuery => SlotQuery(
        serviceId: widget.service.id,
        date: _dateString,
      );

  void _showCaregiverSheet(AvailableSlot slot) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _CaregiverBottomSheet(
        service: widget.service,
        dateString: _dateString,
        slot: slot,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final slotsAsync = ref.watch(slotAvailabilityProvider(_currentQuery));
    final cartCount = ref.watch(cartCountProvider);

    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primaryColor = Theme.of(context).colorScheme.primary;
    
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.service.name),
        actions: [
          if (cartCount > 0)
            Padding(
              padding: const EdgeInsets.only(right: 8.0),
              child: TextButton.icon(
                onPressed: () => Navigator.pushNamed(context, '/cart'),
                icon: Icon(Icons.shopping_cart, color: primaryColor),
                label: Text(
                  '$cartCount',
                  style: TextStyle(color: primaryColor, fontWeight: FontWeight.bold),
                ),
                style: TextButton.styleFrom(
                  backgroundColor: isDark ? Colors.white12 : Colors.grey[200],
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
              ),
            ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            color: Theme.of(context).cardColor,
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isDark ? Colors.white10 : Colors.grey[100],
                    shape: BoxShape.circle,
                  ),
                  child: Icon(Icons.schedule, size: 20, color: Theme.of(context).colorScheme.secondary),
                ),
                const SizedBox(width: 12),
                Text(
                  '${widget.service.durationMinutes} min',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: primaryColor),
                ),
                const Spacer(),
                Text(
                  '₹${widget.service.price.toStringAsFixed(0)}',
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: -0.5),
                ),
              ],
            ),
          ),
          
          Divider(height: 1, color: Theme.of(context).dividerColor),

          Container(
            color: Theme.of(context).cardColor,
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Text(
                    'Select Date',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Theme.of(context).colorScheme.secondary),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 72,
                  child: ListView.builder(
                    controller: _dateScrollController,
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    itemCount: _availableDates.length,
                    itemBuilder: (context, index) {
                      final date = _availableDates[index];
                      final isSelected = date.day == _selectedDate.day && date.month == _selectedDate.month;
                      
                      return GestureDetector(
                        onTap: () {
                          setState(() {
                            _selectedDate = date;
                          });
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          width: 60,
                          margin: const EdgeInsets.symmetric(horizontal: 4),
                          decoration: BoxDecoration(
                            color: isSelected ? primaryColor : Theme.of(context).cardColor,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: isSelected ? primaryColor : (isDark ? Colors.white12 : Colors.grey[300]!),
                              width: 1,
                            ),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                DateFormat('E').format(date).toUpperCase(),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: isSelected ? Theme.of(context).colorScheme.surface.withValues(alpha: 0.7) : Theme.of(context).colorScheme.secondary,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${date.day}',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: isSelected ? Theme.of(context).colorScheme.surface : primaryColor,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
          
          Expanded(
            child: slotsAsync.when(
              loading: () => Center(
                child: CircularProgressIndicator(color: primaryColor, strokeWidth: 2),
              ),
              error: (error, _) => Center(
                child: Text('Error loading slots', style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ),
              data: (availability) {
                if (availability.slots.isEmpty) {
                  return Center(
                    child: Text(
                      'No slots available',
                      style: TextStyle(fontSize: 16, color: Theme.of(context).colorScheme.secondary),
                    ),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.all(24),
                  itemCount: availability.slots.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final slot = availability.slots[index];
                    return GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onTap: () => _showCaregiverSheet(slot),
                      child: Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF181818) : Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: isDark ? Colors.white10 : Colors.grey[300]!,
                            width: 1,
                          ),
                        ),
                        child: Row(
                          children: [
                            Text(
                              '${slot.startTime} – ${slot.endTime}',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: isDark ? Colors.white : Colors.black87,
                              ),
                            ),
                            const Spacer(),
                            Text(
                              '${slot.availableCaregivers.length} available',
                              style: TextStyle(
                                fontSize: 14,
                                color: Theme.of(context).colorScheme.secondary,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Icon(
                              Icons.arrow_forward_ios,
                              size: 14,
                              color: Theme.of(context).colorScheme.secondary,
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _CaregiverBottomSheet extends ConsumerStatefulWidget {
  final Service service;
  final String dateString;
  final AvailableSlot slot;

  const _CaregiverBottomSheet({
    required this.service,
    required this.dateString,
    required this.slot,
  });

  @override
  ConsumerState<_CaregiverBottomSheet> createState() => _CaregiverBottomSheetState();
}

class _CaregiverBottomSheetState extends ConsumerState<_CaregiverBottomSheet> {
  String? _selectedCaregiverId;
  String? _selectedCaregiverName;

  void _addToCart() {
    if (_selectedCaregiverId == null) return;

    final parts = widget.slot.startTime.split(':');
    final startMinutes = int.parse(parts[0]) * 60 + int.parse(parts[1]);
    final endMinutes = startMinutes + widget.service.durationMinutes;
    final endTime =
        '${(endMinutes ~/ 60).toString().padLeft(2, '0')}:${(endMinutes % 60).toString().padLeft(2, '0')}';

    final item = CartItem(
      serviceId: widget.service.id,
      serviceName: widget.service.name,
      caregiverId: _selectedCaregiverId!,
      caregiverName: _selectedCaregiverName!,
      date: widget.dateString,
      startTime: widget.slot.startTime,
      endTime: endTime,
      durationMinutes: widget.service.durationMinutes,
      price: widget.service.price,
    );

    ref.read(cartProvider.notifier).addItem(item);
    Navigator.pop(context);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Added to cart successfully'),
        backgroundColor: AppTheme.success,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primaryColor = Theme.of(context).colorScheme.primary;
    final surfaceColor = Theme.of(context).colorScheme.surface;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: isDark ? Colors.white24 : Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Select a Specialist',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: isDark ? Colors.white : Colors.black,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'For ${widget.slot.startTime} – ${widget.slot.endTime}',
              style: TextStyle(
                fontSize: 14,
                color: Theme.of(context).colorScheme.secondary,
              ),
            ),
            const SizedBox(height: 24),
            ...widget.slot.availableCaregivers.map((cg) {
              final isSelected = _selectedCaregiverId == cg.id;
              return GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () {
                  setState(() {
                    _selectedCaregiverId = cg.id;
                    _selectedCaregiverName = cg.name;
                  });
                },
                child: Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isSelected ? primaryColor : (isDark ? const Color(0xFF181818) : Colors.white),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isSelected ? primaryColor : (isDark ? Colors.white10 : Colors.grey[300]!),
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: isSelected ? surfaceColor.withValues(alpha: 0.2) : (isDark ? Colors.white10 : Colors.grey[100]),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.person,
                          color: isSelected ? surfaceColor : Theme.of(context).colorScheme.secondary,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Text(
                        cg.name,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                          color: isSelected ? surfaceColor : (isDark ? Colors.white : Colors.black87),
                        ),
                      ),
                      const Spacer(),
                      if (isSelected)
                        Icon(Icons.check_circle, color: surfaceColor)
                    ],
                  ),
                ),
              );
            }),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _selectedCaregiverId != null ? _addToCart : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: primaryColor,
                  foregroundColor: surfaceColor,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 0,
                  disabledBackgroundColor: isDark ? Colors.white10 : Colors.grey[200],
                  disabledForegroundColor: Theme.of(context).colorScheme.secondary,
                ),
                child: const Text(
                  'Confirm Selection',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
