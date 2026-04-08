<script setup lang="ts">
import { reactive } from 'vue'

interface FieldDef {
  key: string
  label: string
  type: 'text' | 'select'
  default: string
  options?: { value: string; label: string }[]
}

const props = defineProps<{
  title: string
  eventType: string
  fields: FieldDef[]
}>()

const emit = defineEmits<{
  submit: [eventType: string, data: Record<string, any>]
  cancel: []
}>()

const form = reactive<Record<string, string>>({})
for (const f of props.fields) {
  form[f.key] = f.default
}

function handleSubmit() {
  emit('submit', props.eventType, { ...form })
}
</script>

<template>
  <div class="event-form-overlay" @click.self="emit('cancel')">
    <div class="event-form">
      <h3>{{ title }}</h3>
      <div v-for="f in fields" :key="f.key" class="field">
        <label>{{ f.label }}</label>
        <select v-if="f.type === 'select'" v-model="form[f.key]">
          <option v-for="opt in f.options" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <input v-else v-model="form[f.key]" />
      </div>
      <div class="actions">
        <button class="btn-cancel" @click="emit('cancel')">取消</button>
        <button class="btn-submit" @click="handleSubmit">发送事件</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-form-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.event-form {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  min-width: 350px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.event-form h3 {
  margin-bottom: 1rem;
}

.field {
  margin-bottom: 0.75rem;
}

.field label {
  display: block;
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.field input,
.field select {
  width: 100%;
  padding: 0.4rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-cancel {
  padding: 0.4rem 1rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.btn-submit {
  padding: 0.4rem 1rem;
  background: #1677ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
