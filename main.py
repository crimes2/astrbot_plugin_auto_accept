# astrbot_plugin_auto_approve/main.py

from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.message_components import Plain, MessageChain
from astrbot.api import logger
from types import SimpleNamespace
from enum import Enum
import asyncio # 用于可能的异步操作

# 配置中将使用的枚举类型
class ActionType(Enum):
    IGNORE = "ignore"
    ACCEPT = "accept"
    REJECT = "reject"


@register(
    "astrbot_plugin_auto_approve",
    "你的名字",
    "自动处理好友请求和入群邀请",
    "1.0.0",
    "你的插件仓库URL"
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
        # 确保事件来自 NapCat (理论上对于特定平台适配器，此钩子可能更具针对性)
        # 例如，检查 event.adapter.name 或其他标识符
        # 这里假设 `raw_message` 包含所有原始事件数据
        raw_data = event.raw_message
        post_type = raw_data.get('post_type')
        request_type = raw_data.get('request_type')

        if post_type == 'request':
            if request_type == 'friend':
                logger.info(f"收到好友请求事件：{raw_data}")
                await self._handle_friend_request(event, raw_data)
                event.stop_event() # 停止事件传播，防止其他插件或LLM处理 [<sup data-citation='{&quot;id&quot;:1,&quot;url&quot;:&quot;https://www.kunkunyu.com/links&quot;,&quot;title&quot;:&quot;众星 - 回忆航线&quot;,&quot;content&quot;:&quot;推荐 张洪Heo 分享设计与科技生活 24小时内检测到电波 分享设计与科技生活 杜老师说 杜老师说 距离4光年 杜老师说 新·都在 只想专心玩NAS 该星球距离检测中 只想专心玩NAS 风记星辰 热爱你来过的每度温暖 距离1光年 热爱你来过的每度温暖 满心记 追求让人充实，分享让人快乐 该星球距离检测中 追求让人充实，分享让人快乐 又见梅林 与其诅咒黑暗，不如点燃一支蜡烛 距离5光年 与其诅咒黑暗&quot;}'>1</sup>](https://www.kunkunyu.com/links)
            elif request_type == 'group':
                sub_type = raw_data.get('sub_type')
                if sub_type == 'add': # 管理员邀请入群 (如果是主动申请入群，sub_type可能是invite)
                     logger.info(f"收到入群申请/邀请事件：{raw_data}")
                     await self._handle_group_add_request(event, raw_data)
                     event.stop_event() # 停止事件传播 [<sup data-citation='{&quot;id&quot;:1,&quot;url&quot;:&quot;https://www.kunkunyu.com/links&quot;,&quot;title&quot;:&quot;众星 - 回忆航线&quot;,&quot;content&quot;:&quot;推荐 张洪Heo 分享设计与科技生活 24小时内检测到电波 分享设计与科技生活 杜老师说 杜老师说 距离4光年 杜老师说 新·都在 只想专心玩NAS 该星球距离检测中 只想专心玩NAS 风记星辰 热爱你来过的每度温暖 距离1光年 热爱你来过的每度温暖 满心记 追求让人充实，分享让人快乐 该星球距离检测中 追求让人充实，分享让人快乐 又见梅林 与其诅咒黑暗，不如点燃一支蜡烛 距离5光年 与其诅咒黑暗&quot;}'>1</sup>](https://www.kunkunyu.com/links)
                elif sub_type == 'invite': # 机器人收到邀请入群
                    logger.info(f"收到入群邀请事件：{raw_data}")
                    await self._handle_group_invite_request(event, raw_data)
                    event.stop_event() # 停止事件传播 [<sup data-citation='{&quot;id&quot;:1,&quot;url&quot;:&quot;https://www.kunkunyu.com/links&quot;,&quot;title&quot;:&quot;众星 - 回忆航线&quot;,&quot;content&quot;:&quot;推荐 张洪Heo 分享设计与科技生活 24小时内检测到电波 分享设计与科技生活 杜老师说 杜老师说 距离4光年 杜老师说 新·都在 只想专心玩NAS 该星球距离检测中 只想专心玩NAS 风记星辰 热爱你来过的每度温暖 距离1光年 热爱你来过的每度温暖 满心记 追求让人充实，分享让人快乐 该星球距离检测中 追求让人充实，分享让人快乐 又见梅林 与其诅咒黑暗，不如点燃一支蜡烛 距离5光年 与其诅咒黑暗&quot;}'>1</sup>](https://www.kunkunyu.com/links)
        # 如果是其他您不关心的raw_event类型，则跳过

    async def _handle_friend_request(self, event: AstrMessageEvent, raw_data: dict):
        if not self.friend_request_enabled:
            logger.info("好友请求自动处理未启用，忽略。")
            return

        user_id = raw_data.get('user_id')
        flag = raw_data.get('flag') # go-cqhttp 的请求标识符

        if self.friend_request_action == ActionType.ACCEPT:
            try:
                # 调用 NapCat/go-cqhttp 的 API 来同意好友请求
                # 这是最关键的部分，需要 AstrBot 适配器公开相应的方法
                # 理论上 `event.bot` 应该持有当前平台适配器的客户端实例
                # 具体的API调用可能如下：
                await event.bot.set_friend_add_request(flag=flag, approve=True) # go-cqhttp API
                logger.info(f"已自动同意来自 {user_id} 的好友请求。")
                # 可以选择发送一条提示消息给到机器人主人的私人会话
                await self.context.send_message(
                    event.unified_msg_origin, # 根据实际情况，可能需要获取管理员的UID进行发送
                    MessageChain([Plain(f"已自动同意来自 {user_id} 的好友请求。")])
                )
            except Exception as e:
                logger.error(f"自动同意好友请求失败 (用户ID: {user_id})：{e}")
                # 也可以发送失败提示给管理员
        elif self.friend_request_action == ActionType.REJECT:
            try:
                await event.bot.set_friend_add_request(flag=flag, approve=False, remark='抱歉，暂时不添加好友。') # go-cqhttp API
                logger.info(f"已自动拒绝来自 {user_id} 的好友请求。")
                # 可选择发送拒绝提示
            except Exception as e:
                logger.error(f"自动拒绝好友请求失败 (用户ID: {user_id})：{e}")
        else: # IGNORE
            logger.info(f"好友请求处理方式为 '无操作'，不进行处理。")

    async def _handle_group_add_request(self, event: AstrMessageEvent, raw_data: dict):
        # 处理用户申请入群或邀请入群的请求
        if not self.group_invite_enabled:
            logger.info("入群申请/邀请自动处理未启用，忽略。")
            return

        group_id = raw_data.get('group_id')
        user_id = raw_data.get('user_id')
        flag = raw_data.get('flag')
        sub_type = raw_data.get('sub_type') # 'add' (加群申请) 或 'invite' (群邀请)
        comment = raw_data.get('comment', '无') # 申请理由

        if self.group_invite_action == ActionType.ACCEPT:
            try:
                # 调用 NapCat/go-cqhttp 的 API 来同意入群请求/邀请
                await event.bot.set_group_add_request(
                    flag=flag,
                    sub_type=sub_type,
                    approve=True
                ) # go-cqhttp API
                logger.info(f"已自动同意用户 {user_id} 加入群 {group_id} 的请求/邀请。")
                await self.context.send_message(
                    event.unified_msg_origin,
                    MessageChain([Plain(f"已自动同意用户 {user_id} 加入群 {group_id} 的请求/邀请。")])
                )
            except Exception as e:
                logger.error(f"自动同意入群请求失败 (用户ID: {user_id}, 群ID: {group_id})：{e}")
        elif self.group_invite_action == ActionType.REJECT:
            try:
                await event.bot.set_group_add_request(
                    flag=flag,
                    sub_type=sub_type,
                    approve=False,
                    reason=f'插件自动拒绝: {comment}' # 拒绝理由
                ) # go-cqhttp API
                logger.info(f"已自动拒绝用户 {user_id} 加入群 {group_id} 的请求/邀请。")
                # 可选择发送拒绝提示
            except Exception as e:
                logger.error(f"自动拒绝入群请求失败 (用户ID: {user_id}, 群ID: {group_id})：{e}")
        else: # IGNORE
            logger.info(f"入群申请/邀请处理方式为 '无操作'，不进行处理。")

    async def _handle_group_invite_request(self, event: AstrMessageEvent, raw_data: dict):
        # 专门处理机器人被邀请入群的情况 (sub_type='invite')
        # 在go-cqhttp中，机器人被邀请入群也属于request/group但可能需要不同的处理参数
        # 确保这里传入的approve方法能够正确处理
        # 逻辑与 _handle_group_add_request 类似，但侧重的是机器人被邀请
        await self._handle_group_add_request(event, raw_data) # 复用逻辑，因为底层API可能相同
