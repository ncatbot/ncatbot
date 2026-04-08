<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import QQSimulator from '../components/qq/QQSimulator.vue'
import ResultPanel from '../components/results/ResultPanel.vue'
import RecorderBar from '../components/recorder/RecorderBar.vue'
import CodePreview from '../components/recorder/CodePreview.vue'
import { useWebSocket } from '../composables/useWebSocket'

const ws = useWebSocket()
const initialized = ref(false)
const isRecording = ref(false)
const showCodePreview = ref(false)

onMounted(async () => {
  ws.connect()
  const waitForConnection = setInterval(async () => {
    if (ws.connected.value && !initialized.value) {
      clearInterval(waitForConnection)
      await ws.createSession('qq')
      initialized.value = true
    }
  }, 200)
})

onUnmounted(() => {
  ws.disconnect()
})

async function handleInject(eventType: string, data: Record<string, any>) {
  ws.injectEvent(eventType, data)
  await ws.settle()
}

function handleStartRecording() {
  ws.startRecording()
  isRecording.value = true
}

function handleStopRecording() {
  ws.stopRecording()
  isRecording.value = false
}

async function handleExport() {
  await ws.exportRecording()
  showCodePreview.value = true
}
</script>

<template>
  <div class="playground-container">
    <div class="playground">
      <div class="left-panel">
        <QQSimulator @inject="handleInject" />
      </div>
      <div class="right-panel">
        <div class="connection-status">
          <span :class="ws.connected.value ? 'online' : 'offline'">
            {{ ws.connected.value ? '● 已连接' : '○ 断开' }}
          </span>
          <span v-if="ws.sessionId.value" class="session-id">
            Session: {{ ws.sessionId.value }}
          </span>
        </div>
        <ResultPanel :entries="ws.timeline.value" />
      </div>
    </div>
    <RecorderBar
      :recording="isRecording"
      @start="handleStartRecording"
      @stop="handleStopRecording"
      @export="handleExport"
    />
    <CodePreview
      :code="ws.recordingCode.value"
      :visible="showCodePreview"
      @close="showCodePreview = false"
    />
  </div>
</template>

<style scoped>
.playground-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.playground {
  display: flex;
  flex: 1;
  min-height: 0;
}

.left-panel {
  flex: 1;
  border-right: 1px solid #ddd;
  background: white;
}

.right-panel {
  flex: 1;
  padding: 1rem;
  background: #fafafa;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.online { color: #52c41a; }
.offline { color: #ff4d4f; }

.session-id {
  color: #999;
  font-family: monospace;
}
</style>
