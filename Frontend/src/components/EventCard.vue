<template>
  <div class="event-card">
    <h3>
      <router-link :to="{ name: 'EventDetail', params: { id: event.id } }">
        {{ event.title }}
      </router-link>
    </h3>
    <p><strong>Category:</strong> {{ event.category }}</p>
    <p><strong>When:</strong> {{ formatDate(event.start_datetime) }}</p>
    <p><strong>Where:</strong> {{ event.location_address }}</p>
    <p><strong>Organizer:</strong> {{ event.organizer_username || 'N/A' }}</p>
    <p><strong>Attendees:</strong> {{ event.attendees_count || 0 }}</p>
    <router-link :to="{ name: 'EventDetail', params: { id: event.id } }" class="button secondary">
      View Details
    </router-link>
  </div>
</template>

<script setup>
defineProps({
  event: {
    type: Object,
    required: true,
  },
});

const formatDate = (datetimeString) => {
  if (!datetimeString) return 'N/A';
  try {
    const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(datetimeString).toLocaleDateString(undefined, options);
  } catch (e) {
    return datetimeString; // Fallback if date is invalid
  }
};
</script>

<style scoped>


.event-card h3 a {
  color: inherit;
  text-decoration: none;
}
.event-card h3 a:hover {
  text-decoration: underline;
}
</style>