export interface WSMessage {
  type: string
  id?: string
  payload: Record<string, any>
}

export interface APICallInfo {
  action: string
  params: Record<string, any>
}

export interface TimelineEntry {
  type: 'inject' | 'api_call' | 'settle'
  timestamp: number
  action?: string
  eventType?: string
  data?: Record<string, any>
  params?: Record<string, any>
  apiCalls?: readonly APICallInfo[]
  durationMs?: number
}

export const MsgType = {
  SESSION_CREATE: 'session.create',
  SESSION_DESTROY: 'session.destroy',
  EVENT_INJECT: 'event.inject',
  SESSION_SETTLE: 'session.settle',
  RECORDING_START: 'recording.start',
  RECORDING_STOP: 'recording.stop',
  RECORDING_EXPORT: 'recording.export',
  SESSION_CREATED: 'session.created',
  API_CALLED: 'api.called',
  SETTLE_DONE: 'settle.done',
  RECORDING_EXPORTED: 'recording.exported',
  ERROR: 'error',
} as const
