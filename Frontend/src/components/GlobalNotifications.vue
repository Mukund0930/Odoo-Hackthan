<template>
  <div class="notifications-container">
    <transition-group name="notification-fade" tag="div">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="['notification', `notification-${notification.type}`]"
        @click="removeNotification(notification.id)"
      >
        {{ notification.message }}
        <button class="close-btn" @click.stop="removeNotification(notification.id)">×</button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useNotificationStore } from '../store/notification';

const notificationStore = useNotificationStore();
const notifications = computed(() => notificationStore.activeNotifications);

const removeNotification = (id) => {
  notificationStore.removeNotification(id);
};
</script>

<style scoped>
.notifications-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  width: 300px; /* Adjust as needed */
}

.notification {
  background-color: #f0f0f0;
  color: #333;
  padding: 12px 15px;
  margin-bottom: 10px;
  border-radius: 5px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-success {
  background-color: #d4edda;
  color: #155724;
  border-left: 5px solid #28a745;
}

.notification-error {
  background-color: #f8d7da;
  color: #721c24;
  border-left: 5px solid #dc3545;
}

.notification-info {
  background-color: #cce5ff;
  color: #004085;
  border-left: 5px solid #007bff;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2em;
  color: inherit;
  cursor: pointer;
  margin-left: 10px;
  padding: 0 5px;
}

/* Transition animations */
.notification-fade-enter-active,
.notification-fade-leave-active {
  transition: all 0.5s ease;
}
.notification-fade-enter-from,
.notification-fade-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>