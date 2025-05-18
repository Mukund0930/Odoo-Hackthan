// src/store/notification.js
import { defineStore } from 'pinia';

let nextId = 1;

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [], // { id, message, type: 'success'|'error'|'info', duration? }
  }),
  actions: {
    addNotification({ message, type = 'info', duration = 5000 }) {
      const id = nextId++;
      this.notifications.push({ id, message, type, duration });

      if (duration) {
        setTimeout(() => {
          this.removeNotification(id);
        }, duration);
      }
    },
    removeNotification(id) {
      this.notifications = this.notifications.filter(n => n.id !== id);
    },
    clearAllNotifications() {
      this.notifications = [];
    }
  },
  getters: {
    activeNotifications: (state) => state.notifications,
  },
});