<template>
  <div>
    <h2>Pending Event Approvals</h2>
    <div v-if="loading" class="loading-spinner"></div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="message" class="success-message">{{ message }}</div>

    <div v-if="!loading && events.length === 0 && !error" class="info-message">
      No events are currently pending approval.
    </div>

    <table v-if="events.length > 0">
      <thead>
        <tr>
          <th>Title</th>
          <th>Organizer</th>
          <th>Category</th>
          <th>Submitted</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="event in events" :key="event.id">
          <td><router-link :to="{name: 'EventDetail', params: {id: event.id}}">{{ event.title }}</router-link></td>
          <td>{{ event.organizer_username }}</td>
          <td>{{ event.category }}</td>
          <td>{{ formatDate(event.created_at) }}</td>
          <td>
            <button @click="approve(event.id)" class="small">Approve</button>
            <button @click="reject(event.id)" class="small danger">Reject</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { adminService } from '../services/api';

const events = ref([]);
const loading = ref(true);
const error = ref(null);
const message = ref('');

const fetchPendingEvents = async () => {
  loading.value = true;
  error.value = null;
  message.value = '';
  try {
    const response = await adminService.getPendingEvents();
    events.value = response.data;
  } catch (err) {
    error.value = 'Failed to load pending events. ' + (err.response?.data?.message || err.message);
  } finally {
    loading.value = false;
  }
};

const formatDate = (datetimeString) => {
  if (!datetimeString) return 'N/A';
  try {
    return new Date(datetimeString).toLocaleDateString();
  } catch (e) { return datetimeString; }
};

const approve = async (eventId) => {
  try {
    await adminService.approveEvent(eventId);
    message.value = 'Event approved successfully!';
    fetchPendingEvents(); // Refresh list
  } catch (err) {
    error.value = 'Failed to approve event: ' + (err.response?.data?.message || err.message);
  }
};

const reject = async (eventId) => {
  try {
    await adminService.rejectEvent(eventId);
    message.value = 'Event rejected successfully!';
    fetchPendingEvents(); // Refresh list
  } catch (err) {
    error.value = 'Failed to reject event: ' + (err.response?.data?.message || err.message);
  }
};

onMounted(fetchPendingEvents);
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
th {
  background-color: #f2f2f2;
}
button.small {
  padding: 5px 10px;
  font-size: 0.9em;
  margin-right: 5px;
}
</style>