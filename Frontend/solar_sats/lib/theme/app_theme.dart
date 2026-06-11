import 'package:flutter/material.dart';

class AppTheme {
  static const Color bitcoinOrange = Color(0xFFF7931A);
  static const Color solarYellow = Color(0xFFFFD700);
  static const Color darkBackground = Color(0xFF1A1A2E);

  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    primaryColor: bitcoinOrange,
    colorScheme: const ColorScheme.light(
      primary: bitcoinOrange,
      secondary: solarYellow,
    ),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
    ),
    
  );

  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    primaryColor: bitcoinOrange,
    colorScheme: const ColorScheme.dark(
      primary: bitcoinOrange,
      secondary: solarYellow,
      surface: darkBackground,
    ),
    scaffoldBackgroundColor: darkBackground,
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
      backgroundColor: darkBackground,
    ),
  
  );
}