<template>
  <div>
    <h2>Edit Event</h2>
    <div v-if="loading && !eventData.title" class="loading-spinner">Loading event data...</div>
    <div v-if="pageError" class="error-message">{{ pageError }}</div>
    <div v-if="!canEdit && !loading" class="error-message">
      You do not have permission to edit this event.
    </div>

    <form v-if="eventData.title && canEdit" @submit.prevent="handleSubmit">
      <div v-if="submitError" class="error-message">{{ submitError }}</div>
      <div class="form-group">
        <label for="title">Title:</label>
        <input type="text" id="title" v-model="eventData.title" required>
      </div>
      <div class="form-group">
        <label for="description">Description:</label>
        <textarea id="description" v-model="eventData.description"></textarea>
      </div>
      <div class="form-group">
        <label for="category">Category:</label>
        <select id="category" v-model="eventData.category" required>
          <option disabled value="">Please select one</option>
          <option>Garage Sales</option>
          <option>Sports Matches</option>
          <option>Community Classes</option>
          <option>Volunteer Opportunities</option>
          <option>Exhibitions</option>
          <option>Small Festivals</option>
          <option>Celebrations</option>
        </select>
      </div>
      <div class="form-group">
        <label for="start_datetime">Start Date & Time:</label>
        <input type="datetime-local" id="start_datetime" v-model="eventData.start_datetime" required>
      </div>
      <div class="form-group">
        <label for="end_datetime">End Date & Time (Optional):</label>
        <input type="datetime-local" id="end_datetime" v-model="eventData.end_datetime">
      </div>
      <div class="form-group">
        <label for="location_address">Location Address:</label>
        <input type="text" id="location_address" v-model="eventData.location_address" required>
      </div>
      <button type="submit" :disabled="submitLoading">
        {{ submitLoading ? 'Saving...' : 'Save Changes' }}
      </button>
       <router-link :to="{ name: 'EventDetail', params: { id: props.id } }" class="button secondary" style="margin-left: 10px;">
        Cancel
      </router-link>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
// Corrected paths:
import { eventService } from '../services/api';
import { useAuthStore } from '../store/auth';
import { useNotificationStore } from '../store/notification'; // For global notifications

const props = defineProps({
  id: { type: String, required: true }
});

const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();

const eventData = reactive({
  title: '',
  description: '',
  category: '',
  start_datetime: '',
  end_datetime: '',
  location_address: '',
  organizer_id: null, // To store original organizer for permission check
});

const loading = ref(true); // Page loading state
const submitLoading = ref(false); // Form submission loading state
const pageError = ref(null);
const submitError = ref(null);

// Function to format ISO string to datetime-local input format
const formatToDateTimeLocal = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  // Adjust for timezone offset to display correctly in local time input
  const timezoneOffset = date.getTimezoneOffset() * 60000; //offset in milliseconds
  const localISOTime = new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16);
  return localISOTime;
};


const canEdit = computed(() => {
  if (!authStore.isAuthenticated || !eventData.organizer_id) return false;
  return authStore.isAdmin || authStore.currentUser?.id === eventData.organizer_id;
});

onMounted(async () => {
  try {
    const response = await eventService.getEventById(props.id);
    const fetchedEvent = response.data;
    eventData.title = fetchedEvent.title;
    eventData.description = fetchedEvent.description;
    eventData.category = fetchedEvent.category;
    eventData.start_datetime = formatToDateTimeLocal(fetchedEvent.start_datetime);
    eventData.end_datetime = formatToDateTimeLocal(fetchedEvent.end_datetime);
    eventData.location_address = fetchedEvent.location_address;
    eventData.organizer_id = fetchedEvent.organizer_id;

    if (!canEdit.value && authStore.isAuthenticated) { // Check after data is loaded
        pageError.value = "You do not have permission to edit this event.";
        notificationStore.addNotification({ message: pageError.value, type: 'error' });
    }

  } catch (err) {
    console.error('Failed to fetch event for editing:', err);
    pageError.value = 'Failed to load event data. ' + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: pageError.value, type: 'error' });
  } finally {
    loading.value = false;
  }
});

const handleSubmit = async () => {
  if (!canEdit.value) {
    submitError.value = "Permission denied.";
    notificationStore.addNotification({ message: submitError.value, type: 'error' });
    return;
  }

  submitLoading.value = true;
  submitError.value = null;

  const payload = {
    title: eventData.title,
    description: eventData.description,
    category: eventData.category,
    start_datetime: eventData.start_datetime ? new Date(eventData.start_datetime).toISOString() : null,
    end_datetime: eventData.end_datetime ? new Date(eventData.end_datetime).toISOString() : null,
    location_address: eventData.location_address,
  };

  if (!payload.start_datetime) {
      submitError.value = "Start date and time are required.";
      notificationStore.addNotification({ message: submitError.value, type: 'error' });
      submitLoading.value = false;
      return;
  }
  if (payload.end_datetime && payload.end_datetime < payload.start_datetime) {
    submitError.value = "End date cannot be before start date.";
    notificationStore.addNotification({ message: submitError.value, type: 'error' });
    submitLoading.value = false;
    return;
  }

  try {
    await eventService.updateEvent(props.id, payload);
    notificationStore.addNotification({ message: 'Event updated successfully!', type: 'success' });
    router.push({ name: 'EventDetail', params: { id: props.id } });
  } catch (err) {
    console.error('Failed to update event:', err);
    submitError.value = 'Failed to update event. ' + (err.response?.data?.message || err.message);
    notificationStore.addNotification({ message: submitError.value, type: 'error' });
  } finally {
    submitLoading.value = false;
  }
};
</script>