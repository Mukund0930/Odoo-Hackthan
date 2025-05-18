<template>
  <div>
    <h1>Upcoming Community Events</h1>
    <div class="filters">
      <input
        type="text"
        v-model="filters.category"
        placeholder="Filter by category (e.g., Sports)"
        @input="debouncedFetchEvents"
      />
      <input
        type="text"
        v-model="filters.location"
        placeholder="Filter by location"
        @input="debouncedFetchEvents"
      />
      <!-- <input
        type="text"
        v-model="filters.organizer_username"
        placeholder="Search by user"
        @input="debouncedFetchEvents"
      /> -->
      <input
        type="date"
        v-model="filters.date_from"
        @input="debouncedFetchEvents"
      />
      <input
        type="date"
        v-model="filters.date_to"
        @input="debouncedFetchEvents"
      />
    </div>

    <div v-if="loading" class="loading-spinner"></div>
    <div v-if="error" class="error-message">{{ error }}</div>

    <div v-if="!loading && events.length === 0 && !error" class="info-message">
      No events found matching your criteria.
    </div>

    <div class="event-list">
      <EventCard v-for="event in events" :key="event.id" :event="event" />
    </div>

    <div class="pagination" v-if="totalPages > 1">
      <button @click="prevPage" :disabled="currentPage === 1">Previous</button>
      <span>Page {{ currentPage }} of {{ totalPages }}</span>
      <button @click="nextPage" :disabled="currentPage === totalPages">Next</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { eventService } from '../services/api';
import EventCard from '../components/EventCard.vue';

const events = ref([]);
const loading = ref(true);
const error = ref(null);

const filters = reactive({
  category: '',
  location: '',
organizer_username: '',  // Corrected: use organizer here
  date_from: '',
  date_to: '',
});

const currentPage = ref(1);
const perPage = ref(10);
const totalPages = ref(1);

let debounceTimer;

const fetchEvents = async () => {
  loading.value = true;
  error.value = null;
  try {
    const params = {
      page: currentPage.value,
      per_page: perPage.value,
    };

    if (filters.category) params.category = filters.category;
    if (filters.location) params.location = filters.location;
    if (filters.organizer_username) params.organizer_username = filters.organizer_username;  // Correct param name here
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;

    const response = await eventService.getEvents(params);
    events.value = response.data;

    if (response.data.length < perPage.value) {
      totalPages.value = currentPage.value;
    } else {
      totalPages.value = currentPage.value + 1;
    }
  } catch (err) {
    console.error('Failed to fetch events:', err);
    error.value = 'Failed to load events. ' + (err.response?.data?.message || err.message);
  } finally {
    loading.value = false;
  }
};

const debouncedFetchEvents = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    currentPage.value = 1; // Reset to first page on filter change
    fetchEvents();
  }, 500);
};

const nextPage = () => {
  if (!loading.value && currentPage.value < totalPages.value) {
    currentPage.value++;
    fetchEvents();
  }
};

const prevPage = () => {
  if (currentPage.value > 1 && !loading.value) {
    currentPage.value--;
    fetchEvents();
  }
};

onMounted(fetchEvents);
</script>

<style scoped>
.filters {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.filters input {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  min-width: 150px;
}
.event-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.pagination {
  margin-top: 20px;
  text-align: center;
}
.pagination button {
  margin: 0 10px;
}
.info-message {
  text-align: center;
  padding: 20px;
  background-color: #eef;
  border-radius: 4px;
}
</style>