package xyz.ncatbot.java.sdk;

import java.nio.file.Path;

/**
 * 插件运行上下文，提供 API、插件名和工作目录。
 */
public class NcatBotContext {
    private final BotApi botApi;
    private final String pluginName;
    private final Path workDir;

    public NcatBotContext(BotApi botApi, String pluginName, Path workDir) {
        this.botApi = botApi;
        this.pluginName = pluginName;
        this.workDir = workDir;
    }

    public BotApi getBotApi() {
        return botApi;
    }

    public String getPluginName() {
        return pluginName;
    }

    public Path getWorkDir() {
        return workDir;
    }
}
