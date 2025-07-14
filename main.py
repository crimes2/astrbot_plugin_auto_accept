# astrbot_plugin_auto_accept/main.py

from astrbot.api.star import Context, Star, register
# 导入 filter, AstrMessageEvent, MessageChain 
from astrbot.api.event import filter, AstrMessageEvent, MessageChain 
from astrbot.api.message_components import Plain 
from astrbot.api import logger
from types import SimpleNamespace
from enum import Enum
import asyncio


# 配置中将使用的枚举类型
class ActionType(Enum):
    IGNORE = "ignore"
    ACCEPT = "accept"
    REJECT = "reject"


@register(
    "astrbot_plugin_auto_approve",
    "你的名字",
    "自动处理NapCat平台的好友请求和入群邀请",
    "1.0.0",
    "你的插件仓库URL或其他信息"
)
class AutoApprovePlugin(Star):
    def __init__(self, context: Context, config: SimpleNamespace):
        super().__init__(context)
        self.context = context 
        self.config = config

        self.friend_request_enabled = self.config.friend_request.enabled
        self.friend_request_action = ActionType(self.config.friend_request.action)
        self.group_invite_enabled = self.config.group_invite.enabled
        self.group_invite_action = ActionType(self.config.group_invite.action)

        self.admin_qq_id = getattr(self.config, 'admin_qq', None) 
        if self.admin_qq_id:
            logger.info(f"将向管理员QQ ({self.admin_qq_id}) 发送通知。")
        else:
            logger.warning("未配置管理员QQ号，将无法发送处理结果通知。")

        logger.info(f"插件 [自动审批] 初始化完成。")
        logger.info(f"好友请求自动处理: {'启用' if self.friend_request_enabled else '禁用'}, 方式: {self.friend_request_action.value}")
        logger.info(f"入群邀请自动处理: {'启用' if self.group_invite_enabled else '禁用'}, 方式: {self.group_invite_action.value}")

    # 使用 @filter.event_message_type(filter.EventMessageType.ALL) 来捕获所有事件
    # 根据最新的错误，现在我们将函数参数明确为 Context
    @filter.event_message_type(filter.EventMessageType.ALL, priority=100)
    async def handle_all_events(self, ctx: Context): # 将参数名改为 ctx 并指定类型为 Context
        # 尝试从 Context 中获取实际的事件对象或原始数据
        # 这里的访问方式是推测，目的是为了兼容多种可能的内部实现
        raw_data = None
        event_obj_for_stop = None # 用于调用 stop_event() 的实际事件对象

        # 优先级：
        # 1. 直接从 ctx.event 获取 AstrMessageEvent 及其 raw_message
        if hasattr(ctx, 'event') and isinstance(ctx.event, AstrMessageEvent) and hasattr(ctx.event, 'raw_message'):
            event_obj_for_stop = ctx.event
            raw_data = event_obj_for_stop.raw_message
        # 2. 如果 ctx.event 不是 AstrMessageEvent，或者没有 raw_message，尝试 ctx.raw_event
        elif hasattr(ctx, 'raw_event'): # 假设 Context 直接持有原始事件字典
            raw_data = ctx.raw_event
        # 3. 这种情况下，如果 EventMessageType.ALL 收到的确实是 Context，但原始事件数据不在以上位置，则跳过
        
        if raw_data is None:
            # 如果无法获取原始数据，可能是非预期的事件类型，跳过处理
            logger.debug(f"无法从 Context 中获取原始事件数据。Context 属性: {dir(ctx)}")
            return # 跳过，不再处理

        # 确保 raw_data 是字典
        if not isinstance(raw_data, dict):
            # 如果 raw_data 不是字典，但可能是某种包含原始数据的对象（例如 SimpleNamespace），尝试转换
            if hasattr(raw_data, '__dict__'):
                raw_data = raw_data.__dict__
            else:
                logger.warning(f"获取到的原始事件数据不是字典类型，跳过：{type(raw_data)}")
                return
        
        if 'post_type' not in raw_data:
            # logger.debug(f"Received non-Go-CQHttp event or incomplete data: {raw_data}") # 更加详细的日志
            return # 不是预期的 Go-CQHttp 事件格式，跳过

        post_type = raw_data.get('post_type')
        request_type = raw_data.get('request_type')

        handled = False
        if post_type == 'request':
            if request_type == 'friend':
                logger.info(f"触发好友请求事件：{raw_data}")
                # 将 ctx 和 raw_data 传递给处理函数
                await self._handle_friend_request(ctx, raw_data) 
                handled = True
            elif request_type == 'group':
                sub_type = raw_data.get('sub_type')
                if sub_type == 'add':
                     logger.info(f"触发入群申请事件：{raw_data}")
                     await self._handle_group_add_request(ctx, raw_data)
                     handled = True
                elif sub_type == 'invite':
                    logger.info(f"触发入群邀请事件：{raw_data}")
                    await self._handle_group_invite_request(ctx, raw_data)
                    handled = True
        
        if handled:
            # 停止事件传播
            if event_obj_for_stop and hasattr(event_obj_for_stop, 'stop_event'):
                event_obj_for_stop.stop_event()
            elif hasattr(ctx, 'stop_event'): # 如果 Context 也提供了 stop_event 方法
                ctx.stop_event()
            else:
                logger.warning("无法停止事件传播，可能已处理的事件会继续传递。")


    async def _send_admin_notification(self, message: str):
        """向配置的管理员QQ发送私聊通知"""
        if self.admin_qq_id:
            try:
                await self.context.send_private_message(self.admin_qq_id, MessageChain([Plain(message)]))
            except Exception as e:
                logger.error(f"向管理员 ({self.admin_qq_id}) 发送通知失败: {e}")

    # 将参数 event_or_ctx 更改为 ctx，因为我们现在明确它是一个 Context 对象
    async def _handle_friend_request(self, ctx: Context, raw_data: dict):
        # 从 Context 获取 bot 实例
        bot_instance = ctx.bot
        if bot_instance is None:
            logger.error("无法获取 Bot 实例来处理好友请求。")
            return

        if not self.friend_request_enabled:
            logger.info(f"好友请求自动处理未启用，忽略来自 {raw_data.get('user_id')} 的请求。")
            return

        user_id = raw_data.get('user_id')
        flag = raw_data.get('flag') 
        comment = raw_data.get('comment', '无')

        log_prefix = f"好友请求 (用户: {user_id}, 申请: '{comment}')"

        if self.friend_request_action == ActionType.ACCEPT:
            try:
                await bot_instance.set_friend_add_request(flag=flag, approve=True)
                logger.info(f"{log_prefix}：已自动同意。")
                await self._send_admin_notification(f"✅ 已自动同意来自 {user_id} 的好友请求：{comment}")
            except Exception as e:
                logger.error(f"{log_prefix}：自动同意失败，错误: {e}")
                await self._send_admin_notification(f"❌ 自动同意来自 {user_id} 的好友请求失败：{e}")
        elif self.friend_request_action == ActionType.REJECT:
            try:
                await bot_instance.set_friend_add_request(flag=flag, approve=False, remark='插件自动拒绝。')
                logger.info(f"{log_prefix}：已自动拒绝。")
                await self._send_admin_notification(f"🚫 已自动拒绝来自 {user_id} 的好友请求：{comment}")
            except Exception as e:
                logger.error(f"{log_prefix}：自动拒绝失败，错误: {e}")
                await self._send_admin_notification(f"❌ 自动拒绝来自 {user_id} 的好友请求失败：{e}")
        else: # IGNORE
            logger.info(f"{log_prefix}：处理方式为 '无操作'，不进行处理。")

    # Group add request and invite use similar logic
    async def _handle_group_add_request(self, ctx: Context, raw_data: dict):
        bot_instance = ctx.bot
        if bot_instance is None:
            logger.error("无法获取 Bot 实例来处理入群请求。")
            return

        if not self.group_invite_enabled:
            logger.info(f"入群申请/邀请自动处理未启用，忽略来自 {raw_data.get('user_id')} 加入群 {raw_data.get('group_id')} 的请求。")
            return

        group_id = raw_data.get('group_id')
        user_id = raw_data.get('user_id')
        flag = raw_data.get('flag')
        sub_type = raw_data.get('sub_type')
        comment = raw_data.get('comment', '无')

        log_prefix = f"入群申请/邀请 (群: {group_id}, 用户: {user_id}, 理由: '{comment}')"

        if self.group_invite_action == ActionType.ACCEPT:
            try:
                await bot_instance.set_group_add_request(
                    flag=flag,
                    sub_type=sub_type,
                    approve=True
                )
                logger.info(f"{log_prefix}：已自动同意。")
                await self._send_admin_notification(f"✅ 已自动同意用户 {user_id} 加入群 {group_id} 的请求：{comment}")
            except Exception as e:
                logger.error(f"{log_prefix}：自动同意失败，错误: {e}")
                await self._send_admin_notification(f"❌ 自动同意用户 {user_id} 加入群 {group_id} 失败：{e}")
        elif self.group_invite_action == ActionType.REJECT:
            try:
                await bot_instance.set_group_add_request(
                    flag=flag,
                    sub_type=sub_type,
                    approve=False,
                    reason=f'插件自动拒绝: {comment}'
                )
                logger.info(f"{log_prefix}：已自动拒绝。")
                await self._send_admin_notification(f"🚫 已自动拒绝用户 {user_id} 加入群 {group_id} 的请求：{comment}")
            except Exception as e:
                logger.error(f"{log_prefix}：自动拒绝失败，错误: {e}")
                await self._send_admin_notification(f"❌ 自动拒绝用户 {user_id} 加入群 {group_id} 失败：{e}")
        else: # IGNORE
            logger.info(f"{log_prefix}：处理方式为 '无操作'，不进行处理。")

    async def _handle_group_invite_request(self, ctx: Context, raw_data: dict):
        await self._handle_group_add_request(ctx, raw_data)

