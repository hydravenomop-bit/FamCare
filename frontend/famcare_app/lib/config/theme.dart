import 'package:flutter/material.dart';

class AppTheme {
  AppTheme._();

  static const Color _primaryColor = Colors.black;
  static const Color _secondaryColor = Colors.black87;
  static const Color _errorColor = Color(0xFFD32F2F);
  static const Color _successColor = Color(0xFF388E3C);
  static const Color _surfaceColor = Colors.white;
  static const Color _cardColor = Colors.white;
  static const Color _borderColor = Color(0xFFE0E0E0);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: _surfaceColor,
      colorScheme: const ColorScheme.light(
        primary: _primaryColor,
        secondary: _secondaryColor,
        error: _errorColor,
        surface: _surfaceColor,
      ),
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: _surfaceColor,
        foregroundColor: _primaryColor,
        iconTheme: IconThemeData(color: _primaryColor),
        scrolledUnderElevation: 0,
        titleTextStyle: TextStyle(
          color: _primaryColor,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: _cardColor,
        elevation: 0,
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: const BorderRadius.all(Radius.circular(12)),
          side: BorderSide(color: _borderColor, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: _primaryColor,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.2,
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: _surfaceColor,
        selectedColor: _primaryColor,
        labelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: _borderColor),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: _borderColor,
        thickness: 1,
        space: 1,
      ),
    );
  }

  static const Color _darkPrimaryColor = Colors.white;
  static const Color _darkSecondaryColor = Colors.white70;
  static const Color _darkSurfaceColor = Color(0xFF121212);
  static const Color _darkCardColor = Color(0xFF1E1E1E);
  static const Color _darkBorderColor = Color(0xFF333333);

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: _darkSurfaceColor,
      colorScheme: const ColorScheme.dark(
        primary: _darkPrimaryColor,
        secondary: _darkSecondaryColor,
        error: _errorColor,
        surface: _darkSurfaceColor,
      ),
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: _darkSurfaceColor,
        foregroundColor: _darkPrimaryColor,
        iconTheme: IconThemeData(color: _darkPrimaryColor),
        scrolledUnderElevation: 0,
        titleTextStyle: TextStyle(
          color: _darkPrimaryColor,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: _darkCardColor,
        elevation: 0,
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: const BorderRadius.all(Radius.circular(12)),
          side: BorderSide(color: _darkBorderColor, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: _darkPrimaryColor,
          foregroundColor: Colors.black,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.2,
          ),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: _darkSurfaceColor,
        selectedColor: _darkPrimaryColor,
        labelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Colors.white),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: _darkBorderColor),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: _darkBorderColor,
        thickness: 1,
        space: 1,
      ),
    );
  }

  static const Color success = _successColor;
  static const Color error = _errorColor;
  static const Color primary = _primaryColor;
  static const Color secondary = _secondaryColor;
}
