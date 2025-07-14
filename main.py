# astrbot_plugin_auto_approve/main.py

from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent, MessageChain # <-- MessageChain 从这里导入 [1]
from astrbot.api.message_components import Plain # Plain 等消息组件从这里导入 [1]
from astrbot.api import logger
from types import SimpleNamespace
from enum import Enum
import asyncio # 通常不需要直接使用，但保留以防万一未来有异步需求

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
        self.config = config

        self.friend_request_enabled = self.config.friend_request.enabled
        self.friend_request_action = ActionType(self.config.friend_request.action)
        self.group_invite_enabled = self.config.group_invite.enabled
        self.group_invite_action = ActionType(self.config.group_invite.action)

        logger.info(f"插件 [自动审批] 初始化完成。")
        logger.info(f"好友请求自动处理: {'启用' if self.friend_request_enabled else '禁用'}, 方式: {self.friend_request_action.value}")
        logger.info(f"入群邀请自动处理: {'启用' if self.group_invite_enabled else '禁用'}, 方式: {self.group_invite_action.value}")

    # 使用 on_platform_raw_event 钩子监听原始的平台事件
    # 这是处理 go-cqhttp (NapCat) 特有请求事件的常见方式
    @filter.on_platform_raw_event
    async def handle_raw_event(self, event: AstrMessageEvent):
        # 确保事件来自 NapCat (go-cqhttp 协议)
        # 实际检查取决于 AstrBot 如何封装适配器，raw_message是通用方法
        raw_data = event.raw_message # 这是一个字典，包含原始的go-cqhttp事件数据
        post_type = raw_data.get('post_type')
        request_type = raw_data.get('request_type')

        if post_type == 'request':
            if request_type == 'friend':
                logger.info(f"触发好友请求事件：{raw_data}") # 打印原始数据用于调试
                await self._handle_friend_request(event, raw_data)
                event.stop_event() # 停止事件传播，防止其他插件或LLM处理 [1]
            elif request_type == 'group':
                sub_type = raw_data.get('sub_type')
                if sub_type == 'add': # 用户主动申请入群 (bot作为管理员可以审批)
                     logger.info(f"触发入群申请事件：{raw_data}")
                     await self._handle_group_add_request(event, raw_data)
                     event.stop_event() # 停止事件传播 [1]
                elif sub_type == 'invite': # 机器人收到邀请入群 (robot自身被邀请)
                    logger.info(f"触发入群邀请事件：{raw_data}")
                    await self._handle_group_invite_request(event, raw_data)
                    event.stop_event() # 停止事件传播 [1]
        # 如果是其他您不关心的raw_event类型，则跳过

    async def _handle_friend_request(self, event: AstrMessageEvent, raw_data: dict):
        if not self.friend_request_enabled:
            logger.info(f"好友请求自动处理未启用，忽略来自 {raw_data.get('user_id')} 的请求。")
            return

        user_id = raw_data.get('user_id')
        flag = raw_data.get('flag') # go-cqhttp 的请求标识符，用于API调用
        comment = raw_data.get('comment', '无') # 申请消息

        log_prefix = f"好友请求 (用户: {user_id}, 申请: '{comment}')"

        if self.friend_request_action == ActionType.ACCEPT:
            try:
                # 调用 NapCat/go-cqhttp 的 API 来同意好友请求
                # event.bot 提供了与当前平台的交互接口
                await event.bot.set_friend_add_request(flag=flag, approve=True)
                logger.info(f"{log_prefix}：已自动同意。")
                # 可选：向管理员发送私聊通知，需要您在_conf_schema.json中配置管理员UID
                # 例如：await self.context.send_private_message(self.config.admin_qq_id, MessageChain([Plain(f"已自动同意来自 {user_id} 的好友请求。")]))
            except Exception as e:
                logger.error(f"{log_prefix}：自动同意失败，错误: {e}")
        elif self.friend_request_action == ActionType.REJECT:
            try:
                await event.bot.set_friend_add_request(flag=flag, approve=False, remark='插件自动拒绝。')
                logger.info(f"{log_prefix}：已自动拒绝。")
            except Exception as e:
                logger.error(f"{log_prefix}：自动拒绝失败，错误: {e}")
        else: # IGNORE
            logger.info(f"{log_prefix}：处理方式为 '无操作'，不进行处理。")

    async def _handle_group_add_request(self, event: AstrMessageEvent, raw_data: dict):
        # 处理用户申请入群 (sub_type='add')
        if not self.group_invite_enabled:
            logger.info(f"入群申请/邀请自动处理未启用，忽略来自 {raw_data.get('user_id')} 加入群 {raw_data.get('group_id')} 的请求。")
            return

        group_id = raw_data.get('group_id')
        user_id = raw_data.get('user_id')
        flag = raw_data.get('flag')
        sub_type = raw_data.get('sub_type') # 'add' 或 'invite' (虽然这里主要处理add)
        comment = raw_data.get('comment', '无') # 申请理由

        log_prefix = f"入群申请/邀请 (群: {group_id}, 用户: {user_id}, 理由: '{comment}')"

        if self.group_invite_action == ActionType.ACCEPT:
            try:
                await event.bot.set_group_add_request(
                    flag=flag,
                    sub_type=sub_type, # go-cqhttp 需要这个 sub_type
                    approve=True
                )
                logger.info(f"{log_prefix}：已自动同意。")
                # 可选：向管理员发送私聊通知
            except Exception as e:
                logger.error(f"{log_prefix}：自动同意失败，错误: {e}")
        elif self.group_invite_action == ActionType.REJECT:
            try:
                await event.bot.set_group_add_request(
                    flag=flag,
                    sub_type=sub_type,
                    approve=False,
                    reason=f'插件自动拒绝: {comment}'
                )
                logger.info(f"{log_prefix}：已自动拒绝。")
            except Exception as e:
                logger.error(f"{log_prefix}：自动拒绝失败，错误: {e}")
        else: # IGNORE
            logger.info(f"{log_prefix}：处理方式为 '无操作'，不进行处理。")

    async def _handle_group_invite_request(self, event: AstrMessageEvent, raw_data: dict):
        # 专门处理机器人被邀请入群的情况 (sub_type='invite')
        # 在go-cqhttp中，机器人被邀请入群也属于request/group但可能需要不同的处理参数
        # 这里的逻辑与 _handle_group_add_request 类似，因为底层API (set_group_add_request) 相同，
        # 只是 sub_type 会是 'invite'
        await self._handle_group_add_request(event, raw_data)


