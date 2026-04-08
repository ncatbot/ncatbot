import { ref, readonly } from 'vue'
import type { TimelineEntry, WSMessage } from '../types/protocol'
import { MsgType } from '../types/protocol'

export function useWebSocket() {
  const connected = ref(false)
  const sessionId = ref<string | null>(null)
  const timeline = ref<TimelineEntry[]>([])
  const recordingCode = ref<string>('')

  let ws: WebSocket | null = null
  let reconnectDelay = 3000
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  const pendingCallbacks = new Map<string, (resp: WSMessage) => void>()

  function connect(url?: string) {
    const wsUrl = url || `ws://${location.host}/ws`
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connected.value = true
      reconnectDelay = 3000
    }

    ws.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      connected.value = false
    }

    ws.onmessage = (event: MessageEvent) => {
      const msg: WSMessage = JSON.parse(event.data)
      handleMessage(msg)
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws?.close()
    ws = null
    connected.value = false
  }

  function scheduleReconnect() {
    reconnectTimer = setTimeout(() => {
      connect()
      reconnectDelay = Math.min(reconnectDelay * 2, 30000)
    }, reconnectDelay)
  }

  function send(type: string, payload: Record<string, any>): string {
    const id = crypto.randomUUID()
    ws?.send(JSON.stringify({ type, id, payload }))
    return id
  }

  function sendAndWait(type: string, payload: Record<string, any>): Promise<WSMessage> {
    return new Promise((resolve) => {
      const id = send(type, payload)
      pendingCallbacks.set(id, resolve)
    })
  }

  function handleMessage(msg: WSMessage) {
    if (msg.id && pendingCallbacks.has(msg.id)) {
      const cb = pendingCallbacks.get(msg.id)!
      pendingCallbacks.delete(msg.id)
      cb(msg)
    }

    switch (msg.type) {
      case MsgType.SESSION_CREATED:
        sessionId.value = msg.payload.session_id
        break

      case MsgType.API_CALLED:
        timeline.value.push({
          type: 'api_call',
          timestamp: Date.now(),
          action: msg.payload.action,
          params: msg.payload.params,
        })
        break

      case MsgType.SETTLE_DONE:
        timeline.value.push({
          type: 'settle',
          timestamp: Date.now(),
          apiCalls: msg.payload.api_calls,
        })
        break

      case MsgType.RECORDING_EXPORTED:
        recordingCode.value = msg.payload.code
        break

      case MsgType.ERROR:
        console.error('[WebUI]', msg.payload.message)
        break
    }
  }

  async function createSession(platform = 'qq', plugins?: string[]) {
    const resp = await sendAndWait(MsgType.SESSION_CREATE, { platform, plugins })
    sessionId.value = resp.payload.session_id
    return resp.payload.session_id
  }

  function injectEvent(eventType: string, data: Record<string, any>) {
    timeline.value.push({
      type: 'inject',
      timestamp: Date.now(),
      eventType,
      data,
    })
    send(MsgType.EVENT_INJECT, {
      session_id: sessionId.value,
      event_type: eventType,
      data,
    })
  }

  async function settle() {
    const t0 = Date.now()
    const resp = await sendAndWait(MsgType.SESSION_SETTLE, {
      session_id: sessionId.value,
    })
    const lastSettle = [...timeline.value].reverse().find((e) => e.type === 'settle')
    if (lastSettle) {
      lastSettle.durationMs = Date.now() - t0
    }
    return resp.payload.api_calls
  }

  function startRecording() {
    send(MsgType.RECORDING_START, { session_id: sessionId.value })
  }

  function stopRecording() {
    send(MsgType.RECORDING_STOP, { session_id: sessionId.value })
  }

  async function exportRecording() {
    const resp = await sendAndWait(MsgType.RECORDING_EXPORT, {
      session_id: sessionId.value,
      format: 'scenario_dsl',
    })
    recordingCode.value = resp.payload.code
    return resp.payload.code
  }

  function clearTimeline() {
    timeline.value = []
  }

  return {
    connected: readonly(connected),
    sessionId: readonly(sessionId),
    timeline: readonly(timeline),
    recordingCode: readonly(recordingCode),
    connect,
    disconnect,
    createSession,
    injectEvent,
    settle,
    startRecording,
    stopRecording,
    exportRecording,
    clearTimeline,
  }
}
