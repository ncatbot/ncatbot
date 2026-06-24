package xyz.ncatbot.java.sdk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Collections;
import java.util.Map;

/**
 * 调用 Python 桥接插件 /api/call 的简单客户端。
 */
public class BotApi {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final HttpClient httpClient;
    private final String apiUrl;
    private final String token;

    public BotApi(String apiUrl, String token) {
        this.apiUrl = stripTrailingSlash(apiUrl);
        this.token = token == null ? "" : token;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public JsonNode call(String action, Map<String, ?> params) throws IOException, InterruptedException {
        ObjectNode body = MAPPER.createObjectNode();
        body.put("action", action);
        body.set("params", MAPPER.valueToTree(params == null ? Collections.emptyMap() : params));

        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl + "/api/call"))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(MAPPER.writeValueAsString(body)));
        if (!token.isBlank()) {
            builder.header("Authorization", "Bearer " + token);
            builder.header("X-NcatBot-Token", token);
        }

        HttpResponse<String> response = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofString());
        JsonNode json = response.body() == null || response.body().isBlank()
                ? MAPPER.createObjectNode()
                : MAPPER.readTree(response.body());
        if (response.statusCode() < 200 || response.statusCode() >= 300) {
            throw new IOException("NcatBot API 调用失败，HTTP " + response.statusCode() + ": " + json);
        }
        if (json.path("ok").isBoolean() && !json.path("ok").asBoolean()) {
            throw new IOException("NcatBot API 调用失败: " + json.path("error").asText(json.toString()));
        }
        return json.has("data") ? json.get("data") : json;
    }

    public JsonNode sendGroupText(long groupId, String text) throws IOException, InterruptedException {
        return call("post_group_msg", Map.of("group_id", groupId, "text", text));
    }

    public JsonNode sendPrivateText(long userId, String text) throws IOException, InterruptedException {
        return call("post_private_msg", Map.of("user_id", userId, "text", text));
    }

    public JsonNode deleteMsg(long messageId) throws IOException, InterruptedException {
        return call("delete_msg", Map.of("message_id", messageId));
    }

    public JsonNode setGroupBan(long groupId, long userId, long durationSeconds) throws IOException, InterruptedException {
        return call("set_group_ban", Map.of("group_id", groupId, "user_id", userId, "duration", durationSeconds));
    }

    public JsonNode setGroupKick(long groupId, long userId, boolean rejectAddRequest) throws IOException, InterruptedException {
        return call("set_group_kick", Map.of("group_id", groupId, "user_id", userId, "reject_add_request", rejectAddRequest));
    }

    public JsonNode getLoginInfo() throws IOException, InterruptedException {
        return call("get_login_info", Collections.emptyMap());
    }

    private String stripTrailingSlash(String value) {
        if (value == null || value.isBlank()) {
            return "http://127.0.0.1:8765";
        }
        String result = value;
        while (result.endsWith("/")) {
            result = result.substring(0, result.length() - 1);
        }
        return result;
    }
}
