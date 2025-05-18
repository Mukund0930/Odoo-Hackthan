<template>
  <div v-if="loading" class="loading-spinner"></div>
  <div v-if="error" class="error-message">{{ error }}</div>

  <div v-if="event" class="event-detail">
    <h1>{{ event.title }}</h1>
    <p><strong>Category:</strong> {{ event.category }}</p>
    <p><strong>Starts:</strong> {{ formatDate(event.start_datetime) }}</p>
    <p v-if="event.end_datetime"><strong>Ends:</strong> {{ formatDate(event.end_datetime) }}</p>
    <p><strong>Location:</strong> {{ event.location_address }}</p>
    <p><strong>Description:</strong></p>
    <div v-html="formattedDescription"></div>
    <p><strong>Organizer:</strong> {{ event.organizer_username }}</p>
    <p><strong>Status:</strong> <span :class="`status-${event.status?.toLowerCase()}`">{{ event.status }}</span></p>
    <p><strong>Attending:</strong> {{ event.attendees_count || 0 }} people</p>

    <div class="actions" v-if="event.status === 'APPROVED'">
      <button v-if="!isRsvpd" @click="handleRsvp" :disabled="rsvpLoading">RSVP</button>
      <button v-else @click="handleCancelRsvp" :disabled="rsvpLoading" class="danger">Cancel RSVP</button>
      <p v-if="rsvpMessage" :class="rsvpError ? 'error-message' : 'success-message'">{{ rsvpMessage }}</p>
    </div>

    <div v-if="authStore.isAuthenticated && (isOrganizer || authStore.isAdmin)" class="organizer-actions">
      <hr>
      <h4>Organizer/Admin Actions:</h4>
      <router-link :to="{ name: 'EditEvent', params: { id: event.id } }" class="button">Edit Event</router-link>
      <button @click="handleDeleteEvent" class="button danger" :disabled="deleteLoading">
        {{ deleteLoading ? 'Deleting...' : 'Delete Event' }}
      </button>
      <button @click="fetchAttendees" class="button">View Attendees</button>
      <div v-if="authStore.isAdmin && event.status === 'PENDING'" style="margin-top:10px;">
        <button @click="adminApprove" class="button">Approve Event</button>
        <button @click="adminReject" class="button danger" style="margin-left: 10px;">Reject Event</button>
      </div>
      <div v-if="authStore.isAdmin && event.status !== 'CANCELLED' && event.status !== 'REJECTED'" style="margin-top:10px;">
        <button @click="adminCancel" class="button danger">Admin: Cancel Event</button>
      </div>
      <p v-if="adminActionMessage" :class="adminActionError ? 'error-message' : 'success-message'">{{ adminActionMessage }}</p>
    </div>
  </div>

  <!-- RSVP Modal -->
  <div v-if="showRsvpModal" class="modal-overlay">
    <div class="modal">
      <h3>RSVP for {{ event?.title }}</h3>
      <form @submit.prevent="submitRsvpForm">
        <label for="rsvpName">Full Name:</label>
        <input id="rsvpName" v-model="rsvpForm.name" required />

        <label for="rsvpEmail">Email Address:</label>
        <input id="rsvpEmail" v-model="rsvpForm.email" type="email" required />

        <label for="rsvpPhone">Phone Number (optional):</label>
        <input id="rsvpPhone" v-model="rsvpForm.phone" />

        <label for="rsvpNumPeople">Number of People Attending:</label>
        <input
          id="rsvpNumPeople"
          v-model.number="rsvpForm.num_people"
          type="number"
          min="1"
          required
        />

        <div class="modal-actions">
          <button type="submit" :disabled="rsvpLoading">Confirm RSVP</button>
          <button type="button" @click="showRsvpModal = false">Cancel</button>
        </div>
      </form>
      <p v-if="rsvpMessage" :class="rsvpError ? 'error-message' : 'success-message'">{{ rsvpMessage }}</p>
    </div>
  </div>
  <!-- Attendees Modal -->
<div v-if="showAttendeesModal" class="modal-overlay">
  <div class="modal">
    <h3>Attendees for {{ event?.title }}</h3>
    <table class="attendee-table">
      <thead>
        <tr>
          <th>Name</th><th>Email</th><th>Phone</th><th># People</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rsvp in attendeeList" :key="rsvp.id">
          <td>{{ rsvp.guest_name || rsvp.user?.name || 'N/A' }}</td>
          <td>{{ rsvp.guest_email || rsvp.user?.email || 'N/A' }}</td>
          <td>{{ rsvp.guest_phone || 'N/A' }}</td>
          <td>{{ rsvp.num_people }}</td>
        </tr>
      </tbody>
    </table>
    <div class="modal-actions">
      <button @click="showAttendeesModal = false">Close</button>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { eventService, adminService } from '../services/api';
import { useAuthStore } from '../store/auth';

const showAttendeesModal = ref(false);
const attendeeList = ref([]);

const fetchAttendees = async () => {
  try {
    let token = localStorage.getItem('token');

    // Debug: Show raw token from storage
    console.log('Raw token from localStorage:', token);

    if (!token) {
      throw new Error('You must be logged in to view attendees.');
    }

    // Strip double quotes if present (token was stored as stringified JSON)
    token = token.replace(/^"(.*)"$/, '$1');

    // Debug: Show cleaned token
    console.log('Cleaned token to be sent:', token);

    // Final check: should look like 'eyJ...<3 parts>'
    if (!token.split('.').length === 3) {
      throw new Error('Invalid JWT format');
    }

    const response = await fetch(`/events/${props.id}/rsvps`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.message || 'Failed to fetch attendees');
    }

    const data = await response.json();
    attendeeList.value = data;
    showAttendeesModal.value = true;

  } catch (err) {
    console.error('Fetch error:', err); // Debug
    alert('Failed to fetch attendee list: ' + err.message);
  }
};

const props = defineProps({
  id: { type: String, required: true }
});

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const event = ref(null);
const loading = ref(true);
const error = ref(null);
const rsvpLoading = ref(false);
const rsvpMessage = ref('');
const rsvpError = ref(false);
const userRsvps = ref([]);
const isRsvpd = ref(false);
const deleteLoading = ref(false);
const adminActionMessage = ref('');
const adminActionError = ref(false);

const showRsvpModal = ref(false);
const rsvpForm = ref({
  name: '',
  email: '',
  phone: '',
  num_people: 1,
});

const formatDate = (datetimeString) => {
  if (!datetimeString) return 'N/A';
  const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return new Date(datetimeString).toLocaleDateString(undefined, options);
};

const formattedDescription = computed(() => {
  return event.value?.description?.replace(/\n/g, '<br>') || '';
});

const isOrganizer = computed(() => {
  return authStore.isAuthenticated && event.value && authStore.currentUser?.id === event.value.organizer_id;
});

const fetchEventData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await eventService.getEventById(props.id);
    event.value = response.data;
    if (authStore.isAuthenticated) {
      await checkIfRsvpd();
    }
  } catch (err) {
    error.value = 'Event created waiting for approval.' ;
  } finally {
    loading.value = false;
  }
};

const checkIfRsvpd = async () => {
  try {
    const rsvpResponse = await eventService.getMyRsvps();
    userRsvps.value = rsvpResponse.data;
    isRsvpd.value = userRsvps.value.some(e => e.id === event.value.id);
  } catch (err) {
    console.error("Could not fetch user's RSVPs to check status:", err);
  }
};

const handleRsvp = () => {
  rsvpMessage.value = '';
  rsvpError.value = false;
  showRsvpModal.value = true;
};

const submitRsvpForm = async () => {
  rsvpLoading.value = true;
  rsvpMessage.value = '';
  rsvpError.value = false;

  try {
    const payload = {
      name: rsvpForm.value.name,
      email: rsvpForm.value.email,
      phone: rsvpForm.value.phone,
      num_people: rsvpForm.value.num_people,
    };

    if (!payload.name || !payload.email || !payload.num_people) {
      rsvpError.value = true;
      rsvpMessage.value = 'Please fill in all required RSVP fields.';
      rsvpLoading.value = false;
      return;
    }

    await eventService.rsvpToEvent(props.id, payload);
    rsvpMessage.value = 'Successfully RSVPd!';
    isRsvpd.value = true;
    event.value.attendees_count = (event.value.attendees_count || 0) + payload.num_people;
    showRsvpModal.value = false;
  } catch (err) {
    rsvpError.value = true;
    rsvpMessage.value = 'Failed to RSVP. ' + (err.response?.data?.message || err.message);
  } finally {
    rsvpLoading.value = false;
  }
};

const handleCancelRsvp = async () => {
  rsvpLoading.value = true;
  rsvpMessage.value = '';
  rsvpError.value = false;
  try {
    await eventService.cancelRsvp(props.id);
    rsvpMessage.value = 'RSVP Cancelled.';
    isRsvpd.value = false;
    event.value.attendees_count = Math.max(0, (event.value.attendees_count || 1) - 1);
  } catch (err) {
    rsvpError.value = true;
    rsvpMessage.value = 'Failed to cancel RSVP. ' + (err.response?.data?.message || err.message);
  } finally {
    rsvpLoading.value = false;
  }
};

const handleDeleteEvent = async () => {
  if (confirm('Are you sure you want to delete this event?')) {
    deleteLoading.value = true;
    try {
      await eventService.deleteEvent(props.id);
      router.push('/');
    } catch (err) {
      alert('Failed to delete event: ' + (err.response?.data?.message || err.message));
      deleteLoading.value = false;
    }
  }
};

const adminApprove = async () => {
  adminActionMessage.value = ''; adminActionError.value = false;
  try {
    const res = await adminService.approveEvent(props.id);
    event.value = res.data;
    adminActionMessage.value = "Event approved successfully!";
  } catch (err) {
    adminActionError.value = true;
    adminActionMessage.value = "Failed to approve event: " + (err.response?.data?.message || err.message);
  }
};

const adminReject = async () => {
  adminActionMessage.value = ''; adminActionError.value = false;
  try {
    const res = await adminService.rejectEvent(props.id);
    event.value = res.data;
    adminActionMessage.value = "Event rejected successfully!";
  } catch (err) {
    adminActionError.value = true;
    adminActionMessage.value = "Failed to reject event: " + (err.response?.data?.message || err.message);
  }
};

const adminCancel = async () => {
  adminActionMessage.value = ''; adminActionError.value = false;
  if (confirm("Are you sure you want to cancel this event?")) {
    try {
      const res = await adminService.cancelEventByAdmin(props.id);
      event.value = res.data;
      adminActionMessage.value = "Event cancelled by admin!";
    } catch (err) {
      adminActionError.value = true;
      adminActionMessage.value = "Failed to cancel event: " + (err.response?.data?.message || err.message);
    }
  }
};

onMounted(fetchEventData);
</script>

<style scoped>
.event-detail {
  line-height: 1.6;
}
.actions {
  margin-top: 20px;
}
.organizer-actions .button {
  margin-right: 10px;
}
.status-approved { color: green; font-weight: bold; }
.status-pending { color: orange; font-weight: bold; }
.status-rejected { color: red; font-weight: bold; }
.status-cancelled { color: grey; font-weight: bold; text-decoration: line-through; }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 400px;
  width: 100%;
}

.modal-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: space-between;
}

.modal input {
  width: 100%;
  margin-bottom: 0.5rem;
  padding: 0.4rem;
}
</style>