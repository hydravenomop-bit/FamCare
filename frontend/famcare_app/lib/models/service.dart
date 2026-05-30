class Service {
  final String id;
  final String name;
  final int durationMinutes;
  final double price;
  final String? description;

  const Service({
    required this.id,
    required this.name,
    required this.durationMinutes,
    required this.price,
    this.description,
  });

  factory Service.fromJson(Map<String, dynamic> json) {
    return Service(
      id: json['id'] as String,
      name: json['name'] as String,
      durationMinutes: json['duration_minutes'] as int,
      price: (json['price'] as num).toDouble(),
      description: json['description'] as String?,
    );
  }
}
