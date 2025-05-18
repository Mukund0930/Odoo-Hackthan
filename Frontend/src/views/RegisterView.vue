<template>
  <div>
    <h2>Register</h2>
    <form @submit.prevent="handleRegister">
      <div v-if="authStore.error" class="error-message">{{ authStore.error }}</div>
      <div class="form-group">
        <label for="username">Username:</label>
        <input type="text" id="username" v-model="userData.username" required>
      </div>
      <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" v-model="userData.email" required>
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="userData.password" required>
      </div>
      <div class="form-group">
        <label for="phone_number">Phone Number (Optional):</label>
        <input type="text" id="phone_number" v-model="userData.phone_number">
      </div>
      <button type="submit" :disabled="authStore.loading">
        {{ authStore.loading ? 'Registering...' : 'Register' }}
      </button>
    </form>
    <p>Already have an account? <router-link to="/login">Login here</router-link></p>
  </div>
</template>

<script setup>
import { reactive, onUnmounted } from 'vue';
import { useAuthStore } from '../store/auth';

const authStore = useAuthStore();
const userData = reactive({
  username: '',
  email: '',
  password: '',
  phone_number: '',
});

const handleRegister = async () => {
  await authStore.register(userData);
  // Navigation is handled by the store action
};

// Clear errors when component is left
onUnmounted(() => {
  authStore.clearError();
});
</script>