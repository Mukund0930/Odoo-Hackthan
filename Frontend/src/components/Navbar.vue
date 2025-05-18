<template>
  <nav>
    <ul>
      <li><router-link to="/">Community Pulse</router-link></li>
      <li><router-link to="/">Browse Events</router-link></li>
      <template v-if="authStore.isAuthenticated">
        <li><router-link to="/event/new">Create Event</router-link></li>
        <li><router-link to="/my-events">My Events</router-link></li>
        <li><router-link to="/my-rsvps">My RSVPs</router-link></li>
        <template v-if="authStore.isAdmin">
          <li class="dropdown">
            <a href="#" @click.prevent="toggleAdminMenu">Admin ▾</a>
            <ul v-if="showAdminMenu" class="dropdown-menu">
              <li><router-link to="/admin">Dashboard</router-link></li>
              <li><router-link to="/admin/pending-events">Pending Events</router-link></li>
              <li><router-link to="/admin/users">Manage Users</router-link></li>
            </ul>
          </li>
        </template>
        <li style="margin-left: auto;">Welcome, {{ authStore.currentUser?.username }}!</li>
        <li><button @click="handleLogout">Logout</button></li>
      </template>
      <template v-else>
        <li style="margin-left: auto;"><router-link to="/login">Login</router-link></li>
        <li><router-link to="/register">Register</router-link></li>
      </template>
    </ul>
  </nav>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const showAdminMenu = ref(false);

const handleLogout = () => {
  authStore.logout();
  // Router push is handled in store
};

const toggleAdminMenu = () => {
  showAdminMenu.value = !showAdminMenu.value;
};
</script>

<style scoped>
nav ul {
  display: flex;
  align-items: center;
}
nav ul li {
  position: relative; /* For dropdown positioning */
}
.dropdown-menu {
  display: block; /* Managed by v-if */
  position: absolute;
  background-color: #4a2f7c;
  list-style-type: none;
  padding: 10px 0;
  margin: 5px 0 0 0;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  z-index: 100;
  min-width: 180px; /* Adjust as needed */
}
.dropdown-menu li {
  padding: 0;
  margin: 0; /* Reset margin for dropdown items */
}
.dropdown-menu li a {
  display: block;
  padding: 8px 15px;
  color: white;
  text-decoration: none;
  white-space: nowrap;
}
.dropdown-menu li a:hover {
  background-color: #5a3e8d;
}
</style>