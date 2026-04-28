import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '@/views/DashboardView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';
import ProfileView from '@/views/ProfileView.vue';
import UpdateProfileView from '@/views/UpdateProfileView.vue';
import UserManagementView from '@/views/UserManagementView.vue';
import ReportsView from '@/views/ReportsView.vue';
import NotificationsView from '@/views/NotificationsView.vue';
import ActivityLogView from '@/views/ActivityLogView.vue';
import ConnectDeviceView from '@/views/ConnectDeviceView.vue';
import ThresholdsView from '@/views/Admin/ThresholdsView.vue';
import { authService, firebaseAuthReadyPromise } from '@/services/auth';
import { authStore } from '@/store/auth';
import { firebaseService } from '@/services/firebase';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/VerifyEmailView.vue'),
    meta: { requiresAuth: true, allowUnverified: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/update-profile',
    name: 'UpdateProfile',
    component: UpdateProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: UserManagementView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/activity-logs',
    name: 'ActivityLogs',
    component: ActivityLogView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/thresholds',
    name: 'AdminThresholds',
    component: ThresholdsView,
    meta: { requiresAuth: true, roles: ['admin', 'officer'] },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: ReportsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: NotificationsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/connect-device',
    name: 'ConnectDevice',
    component: ConnectDeviceView,
    meta: { requiresAuth: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'), // Lazy load for efficiency
  },
  {
    path: '/delete-account-confirm',
    name: 'DeleteAccountConfirm',
    component: () => import('@/views/DeleteAccountConfirmView.vue'), // Lazy load
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // Wait for Firebase auth state to initialize to avoid false unverified redirects.
  await firebaseAuthReadyPromise;

  const requiresAuth = to.meta.requiresAuth;
  const isAuthenticated = authService.isAuthenticated();
  const currentUser = firebaseService.auth?.currentUser || null;
  const isEmailVerified = !!currentUser?.emailVerified;
  const allowUnverified = !!to.meta.allowUnverified;

  if (requiresAuth && !isAuthenticated) {
    // If the route requires auth and the user is not authenticated, redirect to login
    next('/login');
  } else if (to.name === 'VerifyEmail' && isAuthenticated && isEmailVerified) {
    next('/dashboard');
  } else if (requiresAuth && isAuthenticated && !isEmailVerified && !allowUnverified) {
    next({ name: 'VerifyEmail', query: { email: currentUser?.email || '' } });
  } else if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
    // If the user is authenticated and tries to access login or register, redirect to dashboard
    if (!isEmailVerified) {
      next({ name: 'VerifyEmail', query: { email: currentUser?.email || '' } });
    } else {
      next('/dashboard');
    }
  } else if (requiresAuth && isAuthenticated) {
    const requiredRoles = to.meta.roles;
    if (requiredRoles && requiredRoles.length > 0 && !requiredRoles.includes(authStore.user?.role)) {
      // If the route requires a specific role and the user does not have it, redirect to the dashboard
      next('/dashboard');
    } else {
      next();
    }
  }
  else {
    // Otherwise, allow navigation
    next();
  }
});

export default router;
