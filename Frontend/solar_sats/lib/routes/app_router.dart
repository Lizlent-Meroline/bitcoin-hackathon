import 'package:go_router/go_router.dart';
import 'package:solar_sats/features/auth/screen/welcome_screen.dart';
import 'package:solar_sats/features/wallet/screen/wallet_dashboard.dart';

class AppRouter {
  static final router = GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        name: 'welcome',
        builder: (context, state) => const WelcomeScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        name: 'dashboard',
        builder: (context, state) => const WalletDashboard(),
      ),
    ],
  );
}
