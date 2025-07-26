import json
import time
import asyncio
from pathlib import Path

from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
from astrbot import logger

data_dir = Path("data/plugin_data/astrbot_plugin_auto_handler")
data_dir.mkdir(parents=True, exist_ok=True)
muted_groups_file = data_dir / "muted_groups.json"

def load_muted_groups():
    if not muted_groups_file.exists():
        return {}
    try:
        with open(muted_groups_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_muted_groups(data):
    with open(muted_groups_file, 'w') as f:
        json.dump(data, f, indent=4)

@register(
    "astrbot_plugin_auto_handler",
    "Lumine",
    "自动处理好友和群邀请，最终稳定版",
    "3.5.22-final-stable",
    "https://github.com/Lumine-Inc/AstrBot-Python"
)
class AutoHandler(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.admins_id: list[str] = context.get_config().get("admins", [])
        self.port_instance = None
        
        # --- 由于旧版本兼容性问题，暂时禁用定时任务功能 ---
        # self.scheduler_job = None
        # try:
        #     # 这一行在旧版本中会报错 ModuleNotFoundError
        #     from astrbot.core.scheduler import get_scheduler
        #     scheduler = get_scheduler()
        #     self.scheduler_job = scheduler.add_job(self.check_muted_status, 'interval', minutes=10)
        #     logger.info("[AutoHandler] 插件已加载，定时任务已启动。")
        # except ImportError:
        #     logger.warning("[AutoHandler] 插件已加载，但定时任务功能因版本不兼容已禁用。")
        logger.info("[AutoHandler] 插件已加载。")

    
    async def destroy(self):
        # if self.scheduler_job:
        #     self.scheduler_job.remove()
        #     logger.info("[AutoHandler] 插件已卸载，定时任务已停止。")
        pass

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    async def event_handler(self, event: AiocqhttpMessageEvent):
        if self.port_instance is None:
            self.port_instance = event.bot
            logger.info("[AutoHandler] 成功获取并保存机器人实例。")

        raw_message = getattr(event.message_obj, "raw_message", None)
        if not isinstance(raw_message, dict):
            return
        
        post_type = raw_message.get("post_type")
        if post_type == "request":
            await self.handle_request(event, raw_message)
        elif post_type == "notice":
            await self.handle_notice(event, raw_message)

    async def handle_request(self, event: AiocqhttpMessageEvent, raw: dict):
        request_type = raw.get("request_type")
        user_id = str(raw.get("user_id"))
        comment = raw.get('comment', '')
        flag = raw.get("flag")
        port = event.bot

        if request_type == "friend":
            await self.handle_friend_request(port, user_id, comment, flag)
        elif request_type == "group" and raw.get("sub_type") == 'invite':
            group_id = raw.get("group_id")
            await self.handle_group_invite(port, user_id, group_id, flag)

    async def handle_friend_request(self, port, user_id, comment, flag):
        mode = self.config.get("friend_request_mode")
        if str(user_id) in self.admins_id:
            try: await port.set_friend_add_request(flag=flag, approve=True)
            except Exception as e: logger.error(f"[AutoHandler] 同意好友失败: {e}")
        elif mode == "accept":
            try: await port.set_friend_add_request(flag=flag, approve=True)
            except Exception as e: logger.error(f"[AutoHandler] 同意好友失败: {e}")
        elif mode == "reject":
            try: await port.set_friend_add_request(flag=flag, approve=False)
            except Exception as e: logger.error(f"[AutoHandler] 拒绝好友失败: {e}")

    async def handle_group_invite(self, port, user_id, group_id, flag):
        if str(user_id) in self.admins_id:
            await port.set_group_add_request(flag=flag, sub_type="invite", approve=True)
            return
        
        if self.config.get("group_blacklist_enabled") and str(user_id) in self.config.get("group_blacklist_user_ids", []):
            await port.set_group_add_request(flag=flag, sub_type="invite", approve=False, reason=self.config.get("group_blacklist_rejection_message"))
            return

        if self.config.get("exclusive_members_enabled"):
            try:
                group_members = await port.get_group_member_list(group_id=group_id)
                member_ids = {str(m['user_id']) for m in group_members}
                exclusive_ids = set(self.config.get("exclusive_members_user_ids", []))
                if not member_ids.isdisjoint(exclusive_ids):
                    await port.set_group_add_request(flag=flag, sub_type="invite", approve=False, reason=self.config.get("exclusive_members_exit_message"))
                    return
            except Exception: pass

        if self.config.get("min_group_size_enabled"):
            try:
                group_info = await port.get_group_info(group_id=group_id)
                if group_info['member_count'] < self.config.get("min_group_size_count"):
                    await port.set_group_add_request(flag=flag, sub_type="invite", approve=False, reason=self.config.get("min_group_size_rejection_message"))
                    return
            except Exception: pass

        mode = self.config.get("group_invite_mode")
        if mode == "accept":
            await port.set_group_add_request(flag=flag, sub_type="invite", approve=True)
            if self.config.get("welcome_message_enabled"):
                await asyncio.sleep(2)
                await port.send_group_msg(group_id=group_id, message=self.config.get("welcome_message_message"))
        elif mode == "reject":
            await port.set_group_add_request(flag=flag, sub_type="invite", approve=False)

    async def handle_notice(self, event: AiocqhttpMessageEvent, raw: dict):
        notice_type = raw.get("notice_type")
        
        if notice_type == 'group_decrease' and raw.get("sub_type") == 'kick_me':
            if self.config.get("group_blacklist_enabled"):
                operator_id = str(raw.get("operator_id"))
                current_blacklist = self.config.get("group_blacklist_user_ids", [])
                if operator_id not in current_blacklist:
                    current_blacklist.append(operator_id)
                    self.config.set("group_blacklist_user_ids", current_blacklist)
                    self.config.save_config()

        # --- 由于定时任务禁用，此部分代码不会被 check_muted_status 调用，但保留事件监听逻辑 ---
        if notice_type == 'group_ban' and self.config.get("auto_leave_if_muted_enabled"):
            if raw.get("user_id") == raw.get("self_id") and raw.get("duration") > 0:
                group_id = str(raw.get("group_id"))
                muted_groups = load_muted_groups()
                muted_groups[group_id] = time.time() + raw.get("duration")
                save_muted_groups(muted_groups)

    # --- 由于旧版本兼容性问题，暂时禁用此功能 ---
    # async def check_muted_status(self):
    #     if not self.config.get("auto_leave_if_muted_enabled"):
    #         return
    #     
    #     if self.port_instance is None:
    #         logger.warning("[AutoHandler] 尚未收到任何事件，无法获取机器人实例，本次定时任务跳过。")
    #         return
    #     
    #     port = self.port_instance
    #     muted_groups = load_muted_groups()
    #     current_time = time.time()
    #     groups_to_leave = []
    #     
    #     for group_id, unmute_time in list(muted_groups.items()):
    #         if current_time > unmute_time:
    #             del muted_groups[group_id]
    #         elif (unmute_time - current_time) / 3600 > self.config.get("auto_leave_if_muted_duration_hours"):
    #             groups_to_leave.append(group_id)
    #     
    #     if groups_to_leave:
    #         try:
    #             for group_id in groups_to_leave:
    #                 await port.set_group_leave(group_id=int(group_id))
    #                 del muted_groups[group_id]
    #         except Exception as e:
    #             logger.error(f"[AutoHandler] 定时退群失败: {e}")
    #
    #     save_muted_groups(muted_groups)
