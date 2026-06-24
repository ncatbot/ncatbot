package xyz.ncatbot.java.sdk;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * NcatBot 事件包装类，保留原始 JSON 并提供常用字段读取方法。
 */
public class NcatBotEvent {
    private final String type;
    private final String platform;
    private final JsonNode data;
    private final JsonNode raw;
    private final NcatBotContext context;

    public NcatBotEvent(String type, String platform, JsonNode data, JsonNode raw, NcatBotContext context) {
        this.type = type == null ? "" : type;
        this.platform = platform == null ? "" : platform;
        this.data = data;
        this.raw = raw;
        this.context = context;
    }

    public String getType() {
        return type;
    }

    public String getPlatform() {
        return platform;
    }

    public JsonNode getData() {
        return data;
    }

    public JsonNode getRaw() {
        return raw;
    }

    public NcatBotContext getContext() {
        return context;
    }

    public BotApi getBotApi() {
        return context.getBotApi();
    }

    public String getText() {
        String direct = firstText("text", "raw_message", "content", "msg");
        if (!direct.isBlank()) {
            return direct;
        }
        JsonNode message = findField("message");
        if (message != null && message.isTextual()) {
            return message.asText();
        }
        if (message != null && message.isArray()) {
            StringBuilder builder = new StringBuilder();
            for (JsonNode segment : message) {
                String type = segment.path("type").asText("");
                if ("text".equals(type)) {
                    builder.append(segment.path("data").path("text").asText(""));
                }
            }
            return builder.toString();
        }
        return "";
    }

    public Long getGroupId() {
        return firstLong("group_id", "groupId", "group");
    }

    public Long getUserId() {
        return firstLong("user_id", "userId", "sender_id", "senderId", "operator_id", "operatorId");
    }

    public Long getMessageId() {
        return firstLong("message_id", "messageId", "msg_id", "msgId");
    }

    public boolean isGroupMessage() {
        return getGroupId() != null || type.toLowerCase().contains("group");
    }

    public boolean isPrivateMessage() {
        return getGroupId() == null && (getUserId() != null || type.toLowerCase().contains("private"));
    }

    private String firstText(String... names) {
        for (String name : names) {
            JsonNode node = findField(name);
            if (node != null && !node.isNull()) {
                if (node.isTextual()) {
                    return node.asText();
                }
                if (node.isValueNode()) {
                    return node.asText();
                }
            }
        }
        return "";
    }

    private Long firstLong(String... names) {
        for (String name : names) {
            JsonNode node = findField(name);
            if (node != null && !node.isNull()) {
                if (node.canConvertToLong()) {
                    return node.asLong();
                }
                if (node.isTextual()) {
                    try {
                        return Long.parseLong(node.asText());
                    } catch (NumberFormatException ignored) {
                        // 忽略无法转为数字的字段，继续尝试其他名称。
                    }
                }
            }
        }
        return null;
    }

    private JsonNode findField(String name) {
        JsonNode node = getField(data, name);
        if (node != null) {
            return node;
        }
        return getField(raw, name);
    }

    private JsonNode getField(JsonNode root, String name) {
        if (root == null || root.isNull()) {
            return null;
        }
        JsonNode direct = root.get(name);
        if (direct != null) {
            return direct;
        }
        JsonNode eventData = root.get("data");
        if (eventData != null) {
            direct = eventData.get(name);
            if (direct != null) {
                return direct;
            }
        }
        JsonNode sender = root.get("sender");
        if (sender != null) {
            direct = sender.get(name);
            if (direct != null) {
                return direct;
            }
        }
        return null;
    }
}
