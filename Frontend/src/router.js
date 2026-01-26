import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '@/views/DashboardView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';
import ProfileView from '@/views/ProfileView.vue';
import UpdateProfileView from '@/views/UpdateProfileView.vue';
import UserManagementView from '@/views/UserManagementView.vue';
import ReportsView from '@/views/ReportsView.vue';
import { authService } from '@/services/auth';
import { authStore } from '@/store/auth';

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
    meta: { requiresAuth: true, role: 'admin' },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: ReportsView,
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
  // Removed await authReady; as it's no longer managed by firebaseConfig.js
  const requiresAuth = to.meta.requiresAuth;
  const isAuthenticated = authService.isAuthenticated();

  if (requiresAuth && !isAuthenticated) {
    // If the route requires auth and the user is not authenticated, redirect to login
    next('/login');
  } else if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
    // If the user is authenticated and tries to access login or register, redirect to dashboard
    next('/dashboard');
  } else if (requiresAuth && isAuthenticated) {
    const requiredRole = to.meta.role;
    if (requiredRole && authStore.user?.role !== requiredRole) {
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