import { reactive, computed } from 'vue';
import { apiService } from '@/services/api';

export const authStore = reactive({
  user: null,
  token: localStorage.getItem('accessToken') || null,
});

export const isAuthenticated = computed(() => !!authStore.token);

export async function fetchUser() {
  if (authStore.token) {
    try {
      apiService.setToken(authStore.token);
      const user = await apiService.getMe();
      authStore.user = user;
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout(); // Clear invalid token
    }
  }
}

export function setUser(user, token) {
  authStore.user = user;
  authStore.token = token;
  localStorage.setItem('accessToken', token);
  apiService.setToken(token);
}

export function logout() {
  authStore.user = null;
  authStore.token = null;
  localStorage.removeItem('accessToken');
  apiService.removeToken();
}
