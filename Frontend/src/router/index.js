import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import EventDetailView from '../views/EventDetailView.vue';
import CreateEventView from '../views/CreateEventView.vue';
import EditEventView from '../views/EditEventView.vue';
import MyOrganizedEventsView from '../views/MyOrganizedEventsView.vue';
import MyRsvpsView from '../views/MyRsvpsView.vue';
import AdminDashboardView from '../views/AdminDashboardView.vue';
import AdminPendingEventsView from '../views/AdminPendingEventsView.vue';
import AdminUsersView from '../views/AdminUsersView.vue';
import NotFoundView from '../views/NotFoundView.vue';

import { useAuthStore } from '../store/auth';

const routes = [
    { path: '/', name: 'Home', component: HomeView },
    { path: '/login', name: 'Login', component: LoginView, meta: { guestOnly: true } },
    { path: '/register', name: 'Register', component: RegisterView, meta: { guestOnly: true } },
    { path: '/event/new', name: 'CreateEvent', component: CreateEventView, meta: { requiresAuth: true } },
    { path: '/event/:id', name: 'EventDetail', component: EventDetailView, props: true },
    { path: '/event/:id/edit', name: 'EditEvent', component: EditEventView, props: true, meta: { requiresAuth: true } }, // Add organizer check in component
    { path: '/my-events', name: 'MyOrganizedEvents', component: MyOrganizedEventsView, meta: { requiresAuth: true } },
    { path: '/my-rsvps', name: 'MyRsvps', component: MyRsvpsView, meta: { requiresAuth: true } },
    // Admin Routes
    {
        path: '/admin',
        name: 'AdminDashboard',
        component: AdminDashboardView,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/pending-events',
        name: 'AdminPendingEvents',
        component: AdminPendingEventsView,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/admin/users',
        name: 'AdminUsers',
        component: AdminUsersView,
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFoundView },
];

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
});

router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore();

    // Fetch user details if token exists but user object is null (e.g., on page refresh)
    if (authStore.token && !authStore.user) {
        await authStore.fetchUser();
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next({ name: 'Login', query: { redirect: to.fullPath } });
    } else if (to.meta.guestOnly && authStore.isAuthenticated) {
        next({ name: 'Home' });
    } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
        next({ name: 'Home' }); // Or a specific 'Unauthorized' page
    }
    else {
        next();
    }
});

export default router;