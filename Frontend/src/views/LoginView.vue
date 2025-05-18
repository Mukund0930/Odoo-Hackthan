<template>
  <div>
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <div v-if="authStore.error" class="error-message">{{ authStore.error }}</div>
      <div class="form-group">
        <label for="email_or_username">Email or Username:</label>
        <input type="text" id="email_or_username" v-model="credentials.email_or_username" required>
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="credentials.password" required>
      </div>
      <button type="submit" :disabled="authStore.loading">
        {{ authStore.loading ? 'Logging in...' : 'Login' }}
      </button>
    </form>
    <p>Don't have an account? <router-link to="/register">Register here</router-link></p>
  </div>
</template>

<script setup>
import { reactive, onUnmounted } from 'vue';
import { useAuthStore } from '../store/auth';

const authStore = useAuthStore();
const credentials = reactive({
  email_or_username: '',
  password: '',
});

const handleLogin = async () => {
  await authStore.login(credentials);
  // Navigation is handled by the store action
};

// Clear errors when component is left
onUnmounted(() => {
  authStore.clearError();
});
</script>