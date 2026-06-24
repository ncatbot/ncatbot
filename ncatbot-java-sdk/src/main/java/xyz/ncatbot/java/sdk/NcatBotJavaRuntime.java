package xyz.ncatbot.java.sdk;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.ServiceLoader;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;

/**
 * Java 插件运行时：加载插件、启动 HTTP 服务、接收 Python 桥接插件转发的事件。
 */
public class NcatBotJavaRuntime {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    public static void run(String[] args) throws Exception {
        List<NcatBotPlugin> plugins = new ArrayList<>();
        ServiceLoader.load(NcatBotPlugin.class).forEach(plugins::add);
        if (plugins.isEmpty()) {
            throw new IllegalStateException("未通过 ServiceLoader 找到 NcatBotPlugin 实现");
        }
        run(plugins, args);
    }

    public static void run(NcatBotPlugin plugin, String[] args) throws Exception {
        run(List.of(plugin), args);
    }

    public static void run(List<NcatBotPlugin> plugins, String[] args) throws Exception {
        RuntimeOptions options = RuntimeOptions.parse(args);
        BotApi botApi = new BotApi(options.apiUrl, options.token);
        NcatBotContext context = new NcatBotContext(botApi, options.pluginName, options.workDir);

        for (NcatBotPlugin plugin : plugins) {
            plugin.onLoad(context);
        }

        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", options.port), 0);
        server.createContext("/health", exchange -> writeJson(exchange, 200, okJson("ok")));
        server.createContext("/ncatbot/event", exchange -> handleEvent(exchange, plugins, context));
        server.setExecutor(Executors.newCachedThreadPool());

        CountDownLatch shutdownLatch = new CountDownLatch(1);
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            for (NcatBotPlugin plugin : plugins) {
                try {
                    plugin.onUnload();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
            server.stop(0);
            shutdownLatch.countDown();
        }));

        server.start();
        System.out.println("NcatBot Java 插件运行中，监听端口 " + options.port);
        shutdownLatch.await();
    }

    private static void handleEvent(HttpExchange exchange, List<NcatBotPlugin> plugins, NcatBotContext context) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            writeJson(exchange, 405, errorJson("仅支持 POST"));
            return;
        }
        try (InputStream inputStream = exchange.getRequestBody()) {
            JsonNode raw = MAPPER.readTree(inputStream);
            String type = raw.path("type").asText(raw.path("post_type").asText(""));
            String platform = raw.path("platform").asText("ncatbot");
            JsonNode data = raw.has("data") ? raw.get("data") : raw;
            NcatBotEvent event = new NcatBotEvent(type, platform, data, raw, context);
            for (NcatBotPlugin plugin : plugins) {
                plugin.onEvent(event);
            }
            writeJson(exchange, 200, okJson("event accepted"));
        } catch (Exception e) {
            e.printStackTrace();
            writeJson(exchange, 500, errorJson(e.getMessage() == null ? e.getClass().getName() : e.getMessage()));
        }
    }

    private static ObjectNode okJson(String message) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("ok", true);
        node.put("message", message);
        return node;
    }

    private static ObjectNode errorJson(String error) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("ok", false);
        node.put("error", error);
        return node;
    }

    private static void writeJson(HttpExchange exchange, int status, JsonNode json) throws IOException {
        byte[] bytes = MAPPER.writeValueAsBytes(json);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream outputStream = exchange.getResponseBody()) {
            outputStream.write(bytes);
        }
    }

    private static class RuntimeOptions {
        private int port = 0;
        private String apiUrl = "http://127.0.0.1:8765";
        private String token = "";
        private String pluginName = "java-plugin";
        private Path workDir = Path.of(".").toAbsolutePath().normalize();

        private static RuntimeOptions parse(String[] args) {
            RuntimeOptions options = new RuntimeOptions();
            for (int i = 0; i < args.length; i++) {
                String arg = args[i];
                String value = null;
                int eq = arg.indexOf('=');
                if (eq > 0) {
                    value = arg.substring(eq + 1);
                    arg = arg.substring(0, eq);
                } else if (i + 1 < args.length) {
                    value = args[++i];
                }

                if ("--ncatbot-plugin-port".equals(arg)) {
                    options.port = Integer.parseInt(requireValue(arg, value));
                } else if ("--ncatbot-api-url".equals(arg)) {
                    options.apiUrl = requireValue(arg, value);
                } else if ("--ncatbot-token".equals(arg)) {
                    options.token = requireValue(arg, value);
                } else if ("--ncatbot-plugin-name".equals(arg)) {
                    options.pluginName = requireValue(arg, value);
                } else if ("--ncatbot-work-dir".equals(arg)) {
                    options.workDir = Path.of(requireValue(arg, value)).toAbsolutePath().normalize();
                }
            }
            if (options.port <= 0) {
                throw new IllegalArgumentException("缺少启动参数 --ncatbot-plugin-port");
            }
            return options;
        }

        private static String requireValue(String name, String value) {
            if (value == null || value.isBlank()) {
                throw new IllegalArgumentException("参数 " + name + " 需要值");
            }
            return value;
        }
    }
}
