<template>
  <div>
    <h1>Admin Dashboard</h1>
    <p>Welcome, Administrator!</p>
    <p>From here you can manage various aspects of the Community Pulse platform.</p>
    <div class="admin-links">
      <router-link to="/admin/pending-events" class="button admin-link">
        Manage Pending Events ({{ pendingCount }})
      </router-link>
      <router-link to="/admin/users" class="button admin-link">
        Manage Users
      </router-link>
      <!-- Add more links as admin features grow -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { adminService } from '../services/api'; // Assuming you have this
import { useNotificationStore } from '../store/notification';

const pendingCount = ref(0);
const notificationStore = useNotificationStore();

onMounted(async () => {
  try {
    // Fetch count for quick display, actual list is on pending events page
    const response = await adminService.getPendingEvents();
    pendingCount.value = response.data.length;
  } catch (error) {
    console.error("Failed to fetch pending events count:", error);
    notificationStore.addNotification({
      message: "Could not fetch pending events count.",
      type: 'error'
    });
  }
});
</script>

<style scoped>
.admin-links {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  align-items: flex-start;
}
.admin-link {
  padding: 12px 20px;
  font-size: 1.1em;
}
</style>