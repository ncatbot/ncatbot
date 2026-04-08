<script setup lang="ts">
import { ref } from 'vue'
import type { TimelineEntry } from '../../types/protocol'
import StructuredView from './StructuredView.vue'
import MockView from './MockView.vue'

defineProps<{
  entries: readonly TimelineEntry[]
}>()

const viewMode = ref<'structured' | 'mock'>('structured')
</script>

<template>
  <div class="result-panel">
    <div class="view-tabs">
      <button :class="{ active: viewMode === 'structured' }" @click="viewMode = 'structured'">
        结构化
      </button>
      <button :class="{ active: viewMode === 'mock' }" @click="viewMode = 'mock'">
        仿真
      </button>
    </div>
    <div class="view-content">
      <StructuredView v-if="viewMode === 'structured'" :entries="entries" />
      <MockView v-else :entries="entries" />
    </div>
  </div>
</template>

<style scoped>
.result-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.view-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.view-tabs button {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
}

.view-tabs button.active {
  background: white;
  border-bottom: 2px solid #1677ff;
  font-weight: 600;
}

.view-content {
  flex: 1;
  overflow-y: auto;
}
</style>
