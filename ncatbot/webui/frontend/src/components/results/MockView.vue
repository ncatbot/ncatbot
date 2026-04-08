<script setup lang="ts">
import type { TimelineEntry } from '../../types/protocol'

defineProps<{
  entries: readonly TimelineEntry[]
}>()

function extractBubbles(entries: readonly TimelineEntry[]) {
  const bubbles: Array<{
    side: 'user' | 'bot' | 'system'
    text: string
    ts: number
  }> = []

  for (const entry of entries) {
    if (entry.type === 'inject' && entry.eventType?.startsWith('message.')) {
      bubbles.push({
        side: 'user',
        text: entry.data?.text || JSON.stringify(entry.data),
        ts: entry.timestamp,
      })
    } else if (entry.type === 'api_call') {
      const params = entry.params || {}
      const msg = params.message
      if (Array.isArray(msg)) {
        const texts = msg
          .filter((s: any) => s.type === 'text')
          .map((s: any) => s.data?.text || '')
        if (texts.length) {
          bubbles.push({ side: 'bot', text: texts.join(''), ts: entry.timestamp })
        }
        const images = msg.filter((s: any) => s.type === 'image')
        for (const img of images) {
          bubbles.push({
            side: 'bot',
            text: `[图片] ${img.data?.url || img.data?.file || ''}`,
            ts: entry.timestamp,
          })
        }
      } else if (entry.action && !entry.action.startsWith('send_')) {
        bubbles.push({
          side: 'system',
          text: `${entry.action}(${JSON.stringify(params).slice(0, 80)})`,
          ts: entry.timestamp,
        })
      }
    } else if (entry.type === 'inject' && entry.eventType?.startsWith('notice.')) {
      bubbles.push({
        side: 'system',
        text: `[${entry.eventType}] ${JSON.stringify(entry.data)}`,
        ts: entry.timestamp,
      })
    }
  }
  return bubbles
}
</script>

<template>
  <div class="mock-view">
    <div
      v-for="(b, i) in extractBubbles(entries)"
      :key="i"
      :class="['bubble-row', b.side]"
    >
      <div class="bubble">{{ b.text }}</div>
    </div>
    <div v-if="entries.length === 0" class="empty">
      等待消息...
    </div>
  </div>
</template>

<style scoped>
.mock-view {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bubble-row {
  display: flex;
}

.bubble-row.user { justify-content: flex-end; }
.bubble-row.bot { justify-content: flex-start; }
.bubble-row.system { justify-content: center; }

.bubble {
  max-width: 70%;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  word-break: break-word;
}

.user .bubble {
  background: #1677ff;
  color: white;
  border-bottom-right-radius: 2px;
}

.bot .bubble {
  background: white;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 2px;
}

.system .bubble {
  background: transparent;
  color: #999;
  font-size: 0.75rem;
}

.empty {
  color: #999;
  text-align: center;
  padding: 2rem;
}
</style>
