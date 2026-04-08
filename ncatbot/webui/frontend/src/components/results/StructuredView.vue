<script setup lang="ts">
import type { TimelineEntry } from '../../types/protocol'

defineProps<{
  entries: readonly TimelineEntry[]
}>()

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour12: false })
}

function formatParams(params: Record<string, any>): string {
  const msg = params?.message
  if (Array.isArray(msg)) {
    const texts = msg
      .filter((s: any) => s.type === 'text')
      .map((s: any) => s.data?.text || '')
    if (texts.length) return texts.join('')
  }
  return JSON.stringify(params).slice(0, 100)
}
</script>

<template>
  <div class="structured-view">
    <div v-for="(entry, i) in entries" :key="i" :class="['entry', entry.type]">
      <span class="time">{{ formatTime(entry.timestamp) }}</span>
      <template v-if="entry.type === 'inject'">
        <span class="arrow">←</span>
        <span class="label">inject:</span>
        <span class="detail">{{ entry.eventType }} {{ JSON.stringify(entry.data) }}</span>
      </template>
      <template v-else-if="entry.type === 'api_call'">
        <span class="arrow">→</span>
        <span class="label">api:</span>
        <span class="action">{{ entry.action }}</span>
        <span class="detail">{{ formatParams(entry.params || {}) }}</span>
      </template>
      <template v-else-if="entry.type === 'settle'">
        <span class="arrow">✓</span>
        <span class="label">settle:</span>
        <span class="detail">
          {{ entry.apiCalls?.length || 0 }} call(s)
          <template v-if="entry.durationMs">, {{ entry.durationMs }}ms</template>
        </span>
      </template>
    </div>
    <div v-if="entries.length === 0" class="empty">
      等待事件注入...
    </div>
  </div>
</template>

<style scoped>
.structured-view {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
}

.entry {
  display: flex;
  gap: 0.5rem;
  padding: 0.2rem 0;
  border-bottom: 1px solid #f0f0f0;
  align-items: baseline;
}

.time { color: #999; min-width: 5rem; }
.arrow { font-weight: bold; min-width: 1rem; text-align: center; }
.label { color: #666; }
.action { color: #1677ff; font-weight: 600; }
.detail { color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.entry.inject .arrow { color: #faad14; }
.entry.api_call .arrow { color: #1677ff; }
.entry.settle .arrow { color: #52c41a; }

.empty {
  color: #999;
  text-align: center;
  padding: 2rem;
}
</style>
