 ```vue
 // src/App.vue
 <template>
   <div id="app-container">
     <Navbar />
     <GlobalNotifications />
     <main class="container">
       <router-view v-slot="{ Component }">
         <template v-if="Component">
           <Suspense>
             <component :is="Component"></component>
             <template #fallback>
               <div class="loading-spinner"></div>
               <p style="text-align: center;">Loading page...</p>
             </template>
           </Suspense>
         </template>
         <template v-else> <!-- Add this else block for debugging -->
           <p style="color: red; text-align: center; font-weight: bold;">
             Router-view has no component to render for the current route!
           </p>
         </template>
       </router-view>
     </main>
   </div>
 </template>

 <script setup>
 import Navbar from './components/Navbar.vue'; // Assuming alias
 import GlobalNotifications from './components/GlobalNotifications.vue'; // Assuming alias
 import { onMounted }
 from 'vue';
 import { useAuthStore } from './store/auth'; // Assuming alias

 console.log('App.vue script setup is running'); // <--- ADD THIS

 const authStore = useAuthStore();

 onMounted(async () => {
   console.log('App.vue onMounted hook'); // <--- ADD THIS
   if (authStore.token && !authStore.user) {
     await authStore.fetchUser();
   }
 });
 </script>
 ```