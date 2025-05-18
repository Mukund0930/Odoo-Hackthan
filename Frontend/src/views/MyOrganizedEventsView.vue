<template>
  <div>
    <h2>My Organized Events</h2>
    <div v-if="loading" class="loading-spinner"></div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="!loading && events.length === 0 && !error" class="info-message">
      You haven't organized any events yet. <router-link to="/event/new">Create one!</router-link>
    </div>
    <div class="event-list">
      <EventCard v-for="event in events" :key="event.id" :event="event" />
      <!-- Optionally add quick edit/delete links or status indicators here -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { eventService } from '../services/api';
import EventCard from '../components/EventCard.vue';

const events = ref([]);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const response = await eventService.getMyOrganizedEvents();
    events.value = response.data;
  } catch (err) {
    error.value = 'Failed to load your events. ' + (err.response?.data?.message || err.message);
  } finally {
    loading.value = false;
  }
});
</script>