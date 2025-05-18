<template>
  <div>
    <h2>My RSVP'd Events</h2>
    <div v-if="loading" class="loading-spinner"></div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="notificationStore.notifications.length > 0">
        <div v-for="notif in notificationStore.notifications" :key="notif.id"
             :class="`message ${notif.type}`">
            {{ notif.message }}
        </div>
    </div>

    <div v-if="!loading && rsvpdEvents.length === 0 && !error" class="info-message">
      You haven't RSVP'd to any upcoming events yet.
      <router-link to="/">Browse events</router-link>
    </div>

    <div class="event-list">
      <div v-for="event in rsvpdEvents" :key="event.id" class="event-card rsvp-card">
        <EventCard :event="event" />
        <button @click="promptCancelRsvp(event.id)" class="button danger small-button" :disabled="cancelLoading === event.id">
          {{ cancelLoading === event.id ? 'Cancelling...' : 'Cancel RSVP' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { eventService } from '../services/api';
import EventCard from '../components/EventCard.vue'; // Assuming EventCard is in components
import { useNotificationStore } from '../store/notification';

const rsvpdEvents = ref([]);
const loading = ref(true);
const error = ref(null);
const cancelLoading = ref(null); // Store ID of event being cancelled
const notificationStore = useNotificationStore();

const fetchMyRsvps = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await eventService.getMyRsvps();
    rsvpdEvents.value = response.data.filter(event => event.status === 'APPROVED' && new Date(event.start_datetime) > new Date()); // Show only upcoming, approved
  } catch (err) {
    console.error('Failed to load your RSVPs:', err);
    error.value = 'Failed to load your RSVPs. ' + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: error.value, type: 'error' });
  } finally {
    loading.value = false;
  }
};

const promptCancelRsvp = (eventId) => {
    if (confirm("Are you sure you want to cancel your RSVP for this event?")) {
        handleCancelRsvp(eventId);
    }
};

const handleCancelRsvp = async (eventId) => {
  cancelLoading.value = eventId;
  try {
    await eventService.cancelRsvp(eventId);
    notificationStore.addNotification({ message: 'RSVP cancelled successfully.', type: 'success' });
    // Refresh the list or remove the event locally
    rsvpdEvents.value = rsvpdEvents.value.filter(e => e.id !== eventId);
  } catch (err) {
    console.error('Failed to cancel RSVP:', err);
    const errorMessage = 'Failed to cancel RSVP. ' + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: errorMessage, type: 'error' });
  } finally {
    cancelLoading.value = null;
  }
};

onMounted(fetchMyRsvps);
</script>

<style scoped>
.rsvp-card {
  position: relative;
  padding-bottom: 60px; /* Space for the button */
}
.small-button {
  position: absolute;
  bottom: 15px;
  right: 15px;
  padding: 6px 10px;
  font-size: 0.9em;
}
.message { /* For notificationStore messages if not using global component */
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
}
.message.success { background-color: #dff0d8; color: #3c763d; border: 1px solid #d6e9c6;}
.message.error { background-color: #f2dede; color: #a94442; border: 1px solid #ebccd1;}
</style>