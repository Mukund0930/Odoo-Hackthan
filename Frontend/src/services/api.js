import axios from 'axios';
import { useAuthStore } from '../store/auth'; // Adjust path if store is elsewhere

const API_URL = 'http://127.0.0.1:5000/api/v1'; // Your Flask backend URL

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add JWT token to headers
apiClient.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore();
        const token = authStore.token;
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor (optional, e.g., for handling 401 globally)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const authStore = useAuthStore();
        if (error.response && error.response.status === 401) {
            // Token might be expired or invalid
            authStore.logout(); // Clear token and user data
            // Optionally redirect to login page
            // router.push('/login'); // You'd need to import router here or handle in components
            console.error('Unauthorized or token expired, logging out.');
        }
        return Promise.reject(error);
    }
);


// --- Auth Service ---
export const authService = {
    login(credentials) { // { email_or_username, password }
        return apiClient.post('/auth/login', credentials);
    },
    register(userData) { // { username, email, password, phone_number? }
        return apiClient.post('/auth/register', userData);
    },
    getMe() {
        return apiClient.get('/auth/me');
    }
};

// --- Event Service ---
export const eventService = {
    getEvents(params) { // { category, location, date_from, date_to, page, per_page }
        return apiClient.get('/events', { params });
    },
    getEventById(eventId) {
        return apiClient.get(`/events/${eventId}`);
    },
    createEvent(eventData) {
        return apiClient.post('/events', eventData);
    },
    updateEvent(eventId, eventData) {
        return apiClient.put(`/events/${eventId}`, eventData);
    },
    deleteEvent(eventId) {
        return apiClient.delete(`/events/${eventId}`);
    },
    rsvpToEvent(eventId, rsvpData) { // { name?, email?, phone?, num_people }
        return apiClient.post(`/events/${eventId}/rsvp`, rsvpData);
    },
    cancelRsvp(eventId, guestEmail = null) {
        let params = {};
        if (guestEmail) {
            params.guest_email = guestEmail;
        }
        return apiClient.delete(`/events/${eventId}/rsvp`, { params });
    },
    getEventRsvps(eventId) { // Organizer/Admin only
        return apiClient.get(`/events/${eventId}/rsvps`);
    },
    getMyOrganizedEvents() {
        return apiClient.get('/events/my-organized-events');
    },
    getMyRsvps() {
        return apiClient.get('/events/my-rsvps');
    }
};

// --- Admin Service ---
export const adminService = {
    getPendingEvents() {
        return apiClient.get('/admin/events/pending');
    },
    approveEvent(eventId) {
        return apiClient.put(`/admin/events/${eventId}/approve`);
    },
    rejectEvent(eventId) {
        return apiClient.put(`/admin/events/${eventId}/reject`);
    },
    cancelEventByAdmin(eventId) {
        return apiClient.put(`/admin/events/${eventId}/cancel`);
    },
    getUsers() {
        return apiClient.get('/admin/users');
    },
    toggleVerifiedOrganizer(userId) {
        return apiClient.put(`/admin/users/${userId}/verify-organizer`);
    },
    toggleBanUser(userId) {
        return apiClient.put(`/admin/users/${userId}/ban`);
    }
};

export default apiClient; // Export the configured client if needed directly