App.vue<template>
  <div class="app-shell">
    <NavBar />
    <main class="page-container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
</script>
