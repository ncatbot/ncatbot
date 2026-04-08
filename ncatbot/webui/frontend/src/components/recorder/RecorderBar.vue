<script setup lang="ts">
defineProps<{
  recording: boolean
}>()

const emit = defineEmits<{
  start: []
  stop: []
  export: []
}>()
</script>

<template>
  <div :class="['recorder-bar', { recording }]">
    <div class="left">
      <template v-if="recording">
        <span class="rec-indicator">🔴 录制中</span>
        <button @click="emit('stop')">停止</button>
      </template>
      <template v-else>
        <button @click="emit('start')">开始录制</button>
      </template>
    </div>
    <div class="right">
      <button @click="emit('export')" :disabled="recording">导出代码</button>
    </div>
  </div>
</template>

<style scoped>
.recorder-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #fafafa;
  border-top: 1px solid #e0e0e0;
}

.recorder-bar.recording {
  background: #fff2f0;
  border-top-color: #ff4d4f;
}

.left, .right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rec-indicator {
  font-size: 0.85rem;
  font-weight: 600;
}

button {
  padding: 0.3rem 0.8rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

button:hover { background: #e0e0e0; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
