<script setup lang="ts">
import { ref } from 'vue'
import MessageInput from './MessageInput.vue'
import EventPanel from './EventPanel.vue'

const emit = defineEmits<{
  inject: [eventType: string, data: Record<string, any>]
}>()

const chatMode = ref<'group' | 'private'>('group')
const groupId = ref('100200')
const userId = ref('99999')

function handleSendMessage(text: string) {
  if (chatMode.value === 'group') {
    emit('inject', 'message.group', {
      text,
      group_id: groupId.value,
      user_id: userId.value,
    })
  } else {
    emit('inject', 'message.private', {
      text,
      user_id: userId.value,
    })
  }
}

function handleEvent(eventType: string, data: Record<string, any>) {
  emit('inject', eventType, data)
}
</script>

<template>
  <div class="qq-simulator">
    <div class="mode-tabs">
      <button :class="{ active: chatMode === 'group' }" @click="chatMode = 'group'">群聊</button>
      <button :class="{ active: chatMode === 'private' }" @click="chatMode = 'private'">私聊</button>
    </div>

    <div class="context-bar">
      <template v-if="chatMode === 'group'">
        <label>群号</label>
        <input v-model="groupId" size="8" />
      </template>
      <label>用户 ID</label>
      <input v-model="userId" size="8" />
    </div>

    <div class="message-area">
      <p class="placeholder-text">在下方输入消息或使用事件面板发送模拟事件</p>
    </div>

    <MessageInput @send="handleSendMessage" />
    <EventPanel @event="handleEvent" />
  </div>
</template>

<style scoped>
.qq-simulator {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mode-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
}

.mode-tabs button {
  flex: 1;
  padding: 0.5rem;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
}

.mode-tabs button.active {
  background: white;
  border-bottom: 2px solid #1677ff;
  font-weight: 600;
}

.context-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9f9f9;
  font-size: 0.85rem;
}

.context-bar input {
  padding: 0.2rem 0.4rem;
  border: 1px solid #ddd;
  border-radius: 3px;
}

.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.placeholder-text {
  color: #999;
  text-align: center;
  margin-top: 2rem;
}
</style>
