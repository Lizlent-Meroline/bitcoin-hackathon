import 'package:flutter/material.dart';
import 'package:solar_sats/routes/app_router.dart';
import 'package:solar_sats/theme/app_theme.dart';

class SolarSatsApp extends StatelessWidget {
  const SolarSatsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router( 
      title: 'Solar Bitcoin Platform',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      routerConfig: AppRouter.router,
      debugShowCheckedModeBanner: false,
    );
  }
}
