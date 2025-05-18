<template>
  <div>
    <h2>Create New Event</h2>
    <div v-if="submitError" class="error-message">{{ submitError }}</div>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="title">Title:</label>
        <input type="text" id="title" v-model="eventData.title" required />
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
          <option value="Other">Other</option>
        </select>
      </div>

      <!-- Custom category input -->
      <div v-if="eventData.category === 'Other'" class="form-group">
        <label for="customCategory">Custom Category:</label>
        <input
          type="text"
          id="customCategory"
          v-model="customCategory"
          placeholder="Enter custom category"
          required
        />
      </div>

      <div class="form-group">
        <label for="start_datetime">Start Date & Time:</label>
        <input
          type="datetime-local"
          id="start_datetime"
          v-model="eventData.start_datetime"
          required
        />
      </div>

      <div class="form-group">
        <label for="end_datetime">End Date & Time (Optional):</label>
        <input
          type="datetime-local"
          id="end_datetime"
          v-model="eventData.end_datetime"
        />
      </div>

      <div class="form-group">
        <label for="pin_code">PIN Code:</label>
        <input
          type="text"
          id="pin_code"
          v-model="pinCode"
          @blur="fetchLocationFromPin"
          placeholder="Enter PIN code"
          maxlength="10"
          required
        />
      </div>

      <div class="form-group">
        <label for="location_address">Location Address:</label>
        <input
          type="text"
          id="location_address"
          v-model="eventData.location_address"
          required
        />
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Submitting...' : 'Create Event' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { eventService } from '../services/api';

const router = useRouter();
const loading = ref(false);
const submitError = ref(null);
const pinCode = ref('');
const customCategory = ref('');
const API_KEY = 'bc101e187819463d91ea4482d23afab6'; // 🔐 Replace with your actual OpenCage key

const eventData = reactive({
  title: '',
  description: '',
  category: '',
  start_datetime: '',
  end_datetime: '',
  location_address: '',
});

const fetchLocationFromPin = async () => {
  if (!pinCode.value) return;

  try {
    const response = await fetch(
      `https://api.opencagedata.com/geocode/v1/json?q=${encodeURIComponent(pinCode.value)}&key=${API_KEY}&countrycode=in`
    );
    const data = await response.json();

    if (data.results && data.results.length > 0) {
      const formatted = data.results[0].formatted;
      eventData.location_address = formatted;
    } else {
      submitError.value = 'No location found for the provided PIN code.';
    }
  } catch (error) {
    console.error('OpenCage API error:', error);
    submitError.value = 'Failed to fetch location. Please try again.';
  }
};

const handleSubmit = async () => {
  loading.value = true;
  submitError.value = null;

  const payload = {
    ...eventData,
    category: eventData.category === 'Other' ? customCategory.value : eventData.category,
    start_datetime: eventData.start_datetime
      ? new Date(eventData.start_datetime).toISOString()
      : null,
    end_datetime: eventData.end_datetime
      ? new Date(eventData.end_datetime).toISOString()
      : null,
  };

  if (!payload.start_datetime) {
    submitError.value = 'Start date and time are required.';
    loading.value = false;
    return;
  }

  if (payload.end_datetime && payload.end_datetime < payload.start_datetime) {
    submitError.value = 'End date cannot be before start date.';
    loading.value = false;
    return;
  }

  try {
    const response = await eventService.createEvent(payload);
    router.push({ name: 'EventDetail', params: { id: response.data.id } });
  } catch (err) {
    console.error('Failed to create event:', err);
    submitError.value =
      'Failed to create event. ' + (err.response?.data?.message || err.message);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.error-message {
  color: red;
  margin-bottom: 1rem;
}
.form-group {
  margin-bottom: 1rem;
}
</style>