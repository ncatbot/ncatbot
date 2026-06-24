package xyz.ncatbot.java.example;

import xyz.ncatbot.java.sdk.NcatBotContext;
import xyz.ncatbot.java.sdk.NcatBotEvent;
import xyz.ncatbot.java.sdk.NcatBotPlugin;

/**
 * 示例插件：收到 hello 后回复 hi from java。
 */
public class HelloPlugin implements NcatBotPlugin {
    private NcatBotContext context;

    @Override
    public void onLoad(NcatBotContext context) {
        this.context = context;
        System.out.println("HelloPlugin 已加载: " + context.getPluginName());
    }

    @Override
    public void onEvent(NcatBotEvent event) throws Exception {
        if (!"hello".equalsIgnoreCase(event.getText().trim())) {
            return;
        }

        Long groupId = event.getGroupId();
        Long userId = event.getUserId();
        if (groupId != null) {
            context.getBotApi().sendGroupText(groupId, "hi from java");
        } else if (userId != null) {
            context.getBotApi().sendPrivateText(userId, "hi from java");
        }
    }
}
