// src/store/auth.js
import { defineStore } from 'pinia';
import { authService }
from '../services/api';
import router from '../router'; // To redirect after login/logout

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || null,
        user: JSON.parse(localStorage.getItem('user')) || null, // Store basic user info
        error: null,
        loading: false,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
        currentUser: (state) => state.user,
        isAdmin: (state) => state.user && state.user.is_admin,
        isVerifiedOrganizer: (state) => state.user && state.user.is_verified_organizer,
    },
    actions: {
        async login(credentials) {
            this.loading = true;
            this.error = null;
            try {
                const response = await authService.login(credentials);
                this.token = response.data.access_token;
                localStorage.setItem('token', this.token);
                await this.fetchUser(); // Fetch user details after login
                router.push('/'); // Redirect to home
            } catch (error) {
                this.error = error.response?.data?.message || 'Login failed. Please try again.';
                console.error('Login error:', error);
            } finally {
                this.loading = false;
            }
        },
        async register(userData) {
            this.loading = true;
            this.error = null;
            try {
                const response = await authService.register(userData);
                this.token = response.data.access_token;
                localStorage.setItem('token', this.token);
                await this.fetchUser(); // Fetch user details after registration
                router.push('/'); // Redirect to home
            } catch (error) {
                this.error = error.response?.data?.message || 'Registration failed. Please try again.';
                console.error('Registration error:', error);
            } finally {
                this.loading = false;
            }
        },
        async fetchUser() {
            if (!this.token) return;
            this.loading = true;
            try {
                const response = await authService.getMe();
                this.user = response.data;
                localStorage.setItem('user', JSON.stringify(this.user));
            } catch (error) {
                console.error('Failed to fetch user:', error);
                // Potentially logout if fetching user fails (e.g., token invalid)
                if (error.response && error.response.status === 401) {
                    this.logout();
                }
                this.error = 'Could not fetch user details.';
            } finally {
                this.loading = false;
            }
        },
        logout() {
            this.token = null;
            this.user = null;
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            router.push('/login'); // Redirect to login page
        },
        clearError() {
            this.error = null;
        }
    },
});