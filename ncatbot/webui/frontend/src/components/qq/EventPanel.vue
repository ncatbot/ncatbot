<script setup lang="ts">
import { ref } from 'vue'
import EventForm from './EventForm.vue'

const emit = defineEmits<{
  event: [eventType: string, data: Record<string, any>]
}>()

const activeEvent = ref<string | null>(null)

const eventButtons = [
  { category: '通知', events: [
    { type: 'notice.poke', label: '戳一戳', fields: [
      { key: 'user_id', label: '发起者 ID', type: 'text' as const, default: '99999' },
      { key: 'target_id', label: '目标 ID', type: 'text' as const, default: '10001' },
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
    ]},
    { type: 'notice.group_increase', label: '群成员增加', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'sub_type', label: '类型', type: 'select' as const, default: 'approve', options: [
        { value: 'approve', label: '管理员同意' },
        { value: 'invite', label: '被邀请' },
      ]},
    ]},
    { type: 'notice.group_decrease', label: '群成员减少', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'sub_type', label: '类型', type: 'select' as const, default: 'leave', options: [
        { value: 'leave', label: '主动退出' },
        { value: 'kick', label: '被踢出' },
      ]},
    ]},
    { type: 'notice.group_ban', label: '群禁言', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'duration', label: '时长(秒)', type: 'text' as const, default: '600' },
    ]},
    { type: 'notice.group_recall', label: '消息撤回', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '操作者 ID', type: 'text' as const, default: '99999' },
      { key: 'message_id', label: '消息 ID', type: 'text' as const, default: 'msg_001' },
    ]},
  ]},
  { category: '请求', events: [
    { type: 'request.friend', label: '加好友请求', fields: [
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'comment', label: '验证消息', type: 'text' as const, default: '请求加好友' },
    ]},
    { type: 'request.group', label: '加群请求', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'sub_type', label: '类型', type: 'select' as const, default: 'add', options: [
        { value: 'add', label: '申请加群' },
        { value: 'invite', label: '被邀请' },
      ]},
    ]},
  ]},
]

function onSubmit(eventType: string, data: Record<string, any>) {
  emit('event', eventType, data)
  activeEvent.value = null
}
</script>

<template>
  <div class="event-panel">
    <details open>
      <summary>事件面板</summary>
      <div v-for="cat in eventButtons" :key="cat.category" class="category">
        <span class="cat-label">{{ cat.category }}</span>
        <button
          v-for="ev in cat.events"
          :key="ev.type"
          @click="activeEvent = ev.type"
          class="event-btn"
        >
          {{ ev.label }}
        </button>
      </div>
    </details>
    <EventForm
      v-if="activeEvent"
      :title="eventButtons.flatMap(c => c.events).find(e => e.type === activeEvent)!.label"
      :event-type="activeEvent"
      :fields="eventButtons.flatMap(c => c.events).find(e => e.type === activeEvent)!.fields"
      @submit="onSubmit"
      @cancel="activeEvent = null"
    />
  </div>
</template>

<style scoped>
.event-panel {
  padding: 0.5rem;
}

details summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #555;
}

.category {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

.cat-label {
  font-size: 0.8rem;
  color: #999;
  width: 3rem;
}

.event-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.event-btn:hover {
  background: #e0e0e0;
}
</style>
