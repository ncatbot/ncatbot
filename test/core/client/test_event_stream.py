"""
ClientEventStream / BotClient.events 测试
"""

import asyncio

import pytest

from ncatbot.core import BotClient, EventType, NcatBotEvent


@pytest.fixture(autouse=True)
def reset_bot_client_singleton():
    """每个测试前重置 BotClient 单例状态。"""

    BotClient._initialized = False
    yield
    BotClient._initialized = False


class TestClientEventStream:
    """测试 BotClient 事件流接口。"""

    @pytest.mark.asyncio
    async def test_events_yield_all_ncatbot_events(self, mock_adapter):
        """默认事件流应接收全部 ncatbot.* 事件。"""

        client = BotClient(adapter=mock_adapter)
        stream = client.events()
        iterator = stream.__aiter__()

        payload = {"raw_message": "hello"}
        publish_task = asyncio.create_task(
            client.event_bus.publish(NcatBotEvent("ncatbot.message_event", payload))
        )

        event = await asyncio.wait_for(anext(iterator), timeout=1.0)
        await publish_task
        await iterator.aclose()

        assert event.type == "ncatbot.message_event"
        assert event.data == payload

    @pytest.mark.asyncio
    async def test_events_filter_by_event_type_enum(self, mock_adapter):
        """EventType 应映射到带 ncatbot 前缀的真实事件名。"""

        client = BotClient(adapter=mock_adapter)

        async with client.events(EventType.MESSAGE) as stream:
            iterator = stream.__aiter__()

            await client.event_bus.publish(
                NcatBotEvent("ncatbot.notice_event", {"notice": True})
            )
            await client.event_bus.publish(
                NcatBotEvent("ncatbot.message_event", {"raw_message": "ping"})
            )

            event = await asyncio.wait_for(anext(iterator), timeout=1.0)

        assert event.type == "ncatbot.message_event"
        assert event.data["raw_message"] == "ping"

    @pytest.mark.asyncio
    async def test_each_events_call_creates_independent_subscription(self, mock_adapter):
        """不同事件流订阅应各自收到完整事件。"""

        client = BotClient(adapter=mock_adapter)

        async with client.events(EventType.MESSAGE) as stream1:
            async with client.events(EventType.MESSAGE) as stream2:
                iterator1 = stream1.__aiter__()
                iterator2 = stream2.__aiter__()

                await client.event_bus.publish(
                    NcatBotEvent("ncatbot.message_event", {"raw_message": "fanout"})
                )

                event1, event2 = await asyncio.wait_for(
                    asyncio.gather(anext(iterator1), anext(iterator2)),
                    timeout=1.0,
                )

        assert event1.data["raw_message"] == "fanout"
        assert event2.data["raw_message"] == "fanout"

    @pytest.mark.asyncio
    async def test_events_aclose_unsubscribes_handler(self, mock_adapter):
        """显式关闭事件流后应从 EventBus 退订。"""

        client = BotClient(adapter=mock_adapter)
        stream = client.events(EventType.MESSAGE)

        assert "ncatbot.message_event" not in client.event_bus._exact

        await stream.__aenter__()
        assert len(client.event_bus._exact["ncatbot.message_event"]) == 1

        await stream.aclose()

        assert "ncatbot.message_event" not in client.event_bus._exact
        assert stream.closed is True

    @pytest.mark.asyncio
    async def test_bot_is_async_iterable(self, mock_adapter):
        """BotClient 本身应支持直接 async for 取事件。"""

        client = BotClient(adapter=mock_adapter)
        iterator = client.__aiter__()

        publish_task = asyncio.create_task(
            client.event_bus.publish(NcatBotEvent("ncatbot.meta_event", {"ok": True}))
        )

        event = await asyncio.wait_for(anext(iterator), timeout=1.0)
        await publish_task
        await iterator.aclose()

        assert event.type == "ncatbot.meta_event"
        assert event.data == {"ok": True}

    @pytest.mark.asyncio
    async def test_async_with_break_releases_subscription(self, mock_adapter):
        """在 async with 中 break 退出后，应确定性地释放订阅。"""

        client = BotClient(adapter=mock_adapter)

        async def producer():
            await asyncio.sleep(0)
            await client.event_bus.publish(
                NcatBotEvent("ncatbot.message_event", {"raw_message": "once"})
            )

        async with client.events(EventType.MESSAGE) as stream:
            task = asyncio.create_task(producer())

            async for event in stream:
                assert event.data["raw_message"] == "once"
                break

        await task
        await asyncio.sleep(0)

        assert "ncatbot.message_event" not in client.event_bus._exact
