<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [text: string]
}>()

const text = ref('')

function handleSend() {
  const trimmed = text.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  text.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="message-input">
    <textarea
      v-model="text"
      placeholder="输入消息..."
      rows="2"
      @keydown="handleKeydown"
    />
    <button @click="handleSend" :disabled="!text.trim()">发送</button>
  </div>
</template>

<style scoped>
.message-input {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  border-top: 1px solid #e0e0e0;
}

textarea {
  flex: 1;
  resize: none;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
}

button {
  padding: 0.5rem 1rem;
  background: #1677ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

button:disabled {
  background: #bbb;
  cursor: not-allowed;
}
</style>
