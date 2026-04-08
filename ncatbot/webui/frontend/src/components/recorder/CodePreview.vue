<script setup lang="ts">
const props = defineProps<{
  code: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function copyToClipboard() {
  navigator.clipboard.writeText(props.code)
}
</script>

<template>
  <div v-if="visible" class="code-overlay" @click.self="emit('close')">
    <div class="code-modal">
      <div class="modal-header">
        <h3>生成的测试代码</h3>
        <div class="actions">
          <button @click="copyToClipboard">复制</button>
          <button @click="emit('close')">关闭</button>
        </div>
      </div>
      <pre class="code-block"><code>{{ code }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.code-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.code-modal {
  background: white;
  border-radius: 8px;
  width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.actions button {
  padding: 0.3rem 0.8rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.code-block {
  flex: 1;
  overflow: auto;
  padding: 1rem 1.5rem;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  background: #f7f7f7;
  margin: 0;
  white-space: pre;
}
</style>
