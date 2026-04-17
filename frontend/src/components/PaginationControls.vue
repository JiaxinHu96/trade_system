<template>
  <div class="pagination-bar" v-if="count > 0">
    <div class="pagination-meta">
      Page {{ currentPage }} / {{ totalPages }} · {{ count }} records
    </div>
    <div class="pagination-actions">
      <button class="secondary" @click="$emit('change', currentPage - 1)" :disabled="currentPage <= 1">Previous</button>
      <button @click="$emit('change', currentPage + 1)" :disabled="currentPage >= totalPages">Next</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  count: { type: Number, default: 0 },
  pageSize: { type: Number, default: 20 },
  currentPage: { type: Number, default: 1 },
})

const totalPages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)))
</script>
