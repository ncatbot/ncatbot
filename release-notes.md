## 🐛 修复
- **dispatcher**: `_consume` 改为并发分发，解决长 handler（如私聊交互菜单）阻塞事件管线导致群命令无响应 (8c4e2dbf)

## ✅ 测试
- 新增 H-12/H-13: 慢 handler 不阻塞后续事件分发 + stop() 清理 dispatch task (8c4e2dbf)
