class Caregiver {
  final String id;
  final String name;

  const Caregiver({
    required this.id,
    required this.name,
  });

  factory Caregiver.fromJson(Map<String, dynamic> json) {
    return Caregiver(
      id: json['id'] as String,
      name: json['name'] as String,
    );
  }
}
