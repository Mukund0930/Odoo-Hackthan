// Frontend/src/views/AdminUsersView.vue
<template>
  <div>
    <h2>Manage Users</h2>
    <div v-if="loading" class="loading-spinner"></div>
    <div v-if="pageError" class="error-message">{{ pageError }}</div>

    <table v-if="users.length > 0">
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Email</th>
          <th>Admin?</th>
          <th>Verified Org?</th>
          <th>Banned?</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.is_admin ? 'Yes' : 'No' }}</td>
          <td>{{ user.is_verified_organizer ? 'Yes' : 'No' }}</td>
          <td :class="{'banned-text': user.is_banned}">{{ user.is_banned ? 'Yes' : 'No' }}</td>
          <td>
            <button @click="toggleVerified(user)" class="button small" :disabled="actionLoading === user.id">
              {{ user.is_verified_organizer ? 'Revoke Verify' : 'Verify Org' }}
            </button>
            <button @click="toggleBan(user)"
                    :class="['button small', user.is_banned ? 'secondary' : 'danger']"
                    :disabled="actionLoading === user.id || user.is_admin"> <!-- Prevent banning self/other admins easily -->
              {{ user.is_banned ? 'Unban' : 'Ban' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading">No users found.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
// Correct paths for AdminUsersView.vue located in src/views/
import { adminService } from '../services/api';         // Correct: ../services/api
import { useNotificationStore } from '../store/notification'; // Correct: ../store/notification
import { useAuthStore } from '../store/auth';             // Correct: ../store/auth


const users = ref([]);
const loading = ref(true);
const pageError = ref(null);
const actionLoading = ref(null);
const notificationStore = useNotificationStore();
const authStore = useAuthStore();


const fetchUsers = async () => {
  loading.value = true;
  pageError.value = null;
  try {
    const response = await adminService.getUsers();
    users.value = response.data;
  } catch (err) {
    console.error('Failed to load users:', err);
    pageError.value = 'Failed to load users. ' + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: pageError.value, type: 'error' });
  } finally {
    loading.value = false;
  }
};

const toggleVerified = async (user) => {
  actionLoading.value = user.id;
  try {
    const response = await adminService.toggleVerifiedOrganizer(user.id);
    const updatedUserIndex = users.value.findIndex(u => u.id === user.id);
    if (updatedUserIndex !== -1) {
      users.value[updatedUserIndex] = response.data;
    }
    notificationStore.addNotification({ message: `User ${user.username}'s verified status updated.`, type: 'success' });
  } catch (err) {
    const msg = `Failed to update verified status for ${user.username}. ` + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: msg, type: 'error' });
  } finally {
    actionLoading.value = null;
  }
};

const toggleBan = async (user) => {
  if (user.id === authStore.currentUser?.id) {
    notificationStore.addNotification({ message: "You cannot ban yourself.", type: 'error' });
    return;
  }
   if (user.is_admin) {
    notificationStore.addNotification({ message: "Admins cannot be banned through this interface.", type: 'error' });
    return;
  }
  actionLoading.value = user.id;
  try {
    const response = await adminService.toggleBanUser(user.id);
    const updatedUserIndex = users.value.findIndex(u => u.id === user.id);
    if (updatedUserIndex !== -1) {
      users.value[updatedUserIndex] = response.data;
    }
    notificationStore.addNotification({ message: `User ${user.username}'s ban status updated.`, type: 'success' });
  } catch (err)
{
    const msg = `Failed to update ban status for ${user.username}. ` + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: msg, type: 'error' });
  } finally {
    actionLoading.value = null;
  }
};

onMounted(fetchUsers);
</script>

<style scoped>
/* ... styles ... */
</style>