package xyz.ncatbot.java.sdk;

/**
 * NcatBot Java 插件入口接口。
 */
public interface NcatBotPlugin {
    /**
     * 插件加载时调用。
     */
    default void onLoad(NcatBotContext context) throws Exception {
    }

    /**
     * 收到 NcatBot 事件时调用。
     */
    void onEvent(NcatBotEvent event) throws Exception;

    /**
     * 插件卸载或进程退出时调用。
     */
    default void onUnload() throws Exception {
    }
}
