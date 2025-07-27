import asyncio
from typing import Dict, Optional
from aiocqhttp import CQHttp

from astrbot.api.event import filter
import astrbot.api.message_components as Comp
from astrbot.api.star import Context, Star, register
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
from astrbot.core.star.filter.platform_adapter_type import PlatformAdapterType
from astrbot.core.star.filter.permission import PermissionType
from astrbot import logger

@register(
    "astrbot_plugin_auto_handler",
    "Lumine & Zhalslar",
    "智能自动化管家, 集成高级监控与手动管理工具",
    "2.1.0",
    "https://github.com/Lumine-Inc/astrbot-plugin-auto-handler"
)
class AutoHandler(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.admins_id: list[str] = list(set(context.get_config().get("admins", [])))
        
        self.new_group_check_delay: int = config.get("new_group_check_delay", 600)
        self.default_check_count: int = config.get("default_check_count", 20)
        self.max_check_count: int = config.get("max_check_count", 100)
        self.scheduled_checks: Dict[str, asyncio.Task] = {}
        
        logger.info("[AutoHandler] 插件已加载，当前为 v2.1.0 最终版。")

    @staticmethod
    def convert_duration_advanced(duration: int) -> str:
        if duration <= 0: return "0秒"
        days, rem = divmod(duration, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = []
        if days > 0: parts.append(f"{days}天")
        if hours > 0: parts.append(f"{hours}小时")
        if minutes > 0: parts.append(f"{minutes}分钟")
        if seconds > 0: parts.append(f"{seconds}秒")
        return "".join(parts) if parts else "0秒"

    async def _send_to_admins(self, client: CQHttp, message: str):
        for admin_id in self.admins_id:
            if admin_id.isdigit():
                try:
                    await client.send_private_msg(user_id=int(admin_id), message=message)
                except Exception as e:
                    logger.error(f"向管理员({admin_id})发送消息失败: {e}")

    # ===== 自动化核心（请求处理） =====
    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP)
    async def on_request(self, event: AiocqhttpMessageEvent):
        raw_message = getattr(event.message_obj, "raw_message", None)
        if not isinstance(raw_message, dict) or raw_message.get("post_type") != "request": return

        client = event.bot
        request_type = raw_message.get("request_type")
        user_id = str(raw_message["user_id"])
        comment = raw_message.get("comment", "无")
        flag = raw_message["flag"]

        # --- 1. 好友请求处理 ---
        if request_type == "friend":
            mode = self.config.get("friend_request_mode", "manual")
            if user_id in self.admins_id or mode == "accept":
                await client.set_friend_add_request(flag=flag, approve=True)
            elif mode == "reject":
                await client.set_friend_add_request(flag=flag, approve=False)
            elif mode == "manual":
                nickname = (await client.get_stranger_info(user_id=int(user_id))).get("nickname", "未知")
                notice = (
                    f"【收到好友申请】请回复审批\n"
                    f"昵称：{nickname}\n"
                    f"QQ号：{user_id}\n"
                    f"flag：{flag}\n"
                    f"验证信息：{comment}"
                )
                await self._send_to_admins(client, notice)

        # --- 2. 群邀请处理 (集成黑白名单) ---
        elif request_type == "group" and raw_message.get("sub_type") == "invite":
            group_id = str(raw_message["group_id"])
            nickname = (await client.get_stranger_info(user_id=int(user_id))).get("nickname", "未知")

            if user_id in self.admins_id:
                await client.set_group_add_request(flag=flag, sub_type='invite', approve=True)
                return

            if group_id in self.config.get("group_blacklist", []):
                await client.set_group_add_request(flag=flag, sub_type='invite', approve=False, reason="该群在黑名单中")
                return

            filter_mode = self.config.get("inviter_filter_mode", "none")
            inviter_blacklist = self.config.get("inviter_blacklist", [])
            inviter_whitelist = self.config.get("inviter_whitelist", [])
            if filter_mode == "blacklist" and user_id in inviter_blacklist:
                await client.set_group_add_request(flag=flag, sub_type='invite', approve=False, reason="邀请者在黑名单中")
                return
            elif filter_mode == "whitelist" and user_id not in inviter_whitelist:
                await client.set_group_add_request(flag=flag, sub_type='invite', approve=False, reason="邀请者不在白名单中")
                return

            mode = self.config.get("group_invite_mode", "manual")
            if mode == "accept":
                await client.set_group_add_request(flag=flag, sub_type='invite', approve=True)
            elif mode == "reject":
                await client.set_group_add_request(flag=flag, sub_type='invite', approve=False)
            elif mode == "manual":
                group_name = (await client.get_group_info(group_id=int(group_id))).get("group_name", "未知")
                notice = (
                    f"【收到群邀请】请回复审批\n"
                    f"邀请人：{nickname}\n"
                    f"邀请人QQ：{user_id}\n"
                    f"群名称：{group_name}\n"
                    f"群号：{group_id}\n"
                    f"flag：{flag}\n"
                    f"验证信息：{comment}"
                )
                await self._send_to_admins(client, notice)
        
        event.stop_event()

    # --- 自动化核心（通知事件处理）---
    @filter.platform_adapter_type(PlatformAdapterType.AIOCQHTTP)
    async def on_notice(self, event: AiocqhttpMessageEvent):
        raw_message = getattr(event.message_obj, "raw_message", None)
        self_id = str(event.get_self_id())
        if not isinstance(raw_message, dict) or raw_message.get("post_type") != "notice": return
        
        notice_type = raw_message.get("notice_type")
        client = event.bot
        group_id_str = str(raw_message.get("group_id"))

        def _cancel_scheduled_task(gid: str):
            if gid in self.scheduled_checks:
                task = self.scheduled_checks.pop(gid)
                task.cancel()
                logger.info(f"机器人离开群 {gid}，已取消为其安排的延迟抽查任务。")

        # 机器人被踢
        if notice_type == "group_decrease" and raw_message.get("sub_type") == "kick_me" and str(raw_message.get("user_id")) == self_id:
            _cancel_scheduled_task(group_id_str)
            group_blacklist = self.config.get("group_blacklist", [])
            if group_id_str not in group_blacklist:
                group_blacklist.append(group_id_str)
                self.config.set("group_blacklist", group_blacklist)
                self.config.save_config()
                logger.info(f"群聊 {group_id_str} 因被踢出已被加入黑名单。")

        # 机器人被禁言
        elif notice_type == "group_ban" and str(raw_message.get("user_id")) == self_id:
            duration = raw_message.get("duration", 0)
            max_ban_duration = self.config.get("max_ban_duration", 0)
            if max_ban_duration > 0 and duration > max_ban_duration:
                _cancel_scheduled_task(group_id_str)
                await self._send_to_admins(client, f"在群 {group_id_str} 中被禁言时间超过 {self.convert_duration_advanced(max_ban_duration)}，将自动退群。")
                await client.set_group_leave(group_id=int(group_id_str))

        # 机器人被邀请入群（成功加入后触发）
        elif notice_type == "group_increase" and str(raw_message.get("user_id")) == self_id:
            # 入群后检查
            await self._post_join_checks(event)
            event.stop_event()

    async def _post_join_checks(self, event: AiocqhttpMessageEvent):
        client = event.bot
        group_id = int(event.get_group_id())
        group_name = (await client.get_group_info(group_id=group_id)).get("group_name", str(group_id))

        # 检查1: 群黑名单
        if str(group_id) in self.config.get("group_blacklist", []):
            await client.set_group_leave(group_id=group_id)
            return

        # 检查2：总群数
        group_list = await client.get_group_list()
        max_capacity = self.config.get("max_group_capacity", 0)
        if max_capacity > 0 and len(group_list) > max_capacity:
            await client.set_group_leave(group_id=group_id)
            return
            
        # 检查3: 互斥成员
        exclusive_members = set(self.config.get("exclusive_members", []))
        if exclusive_members:
            member_list = await client.get_group_member_list(group_id=group_id)
            member_ids = {str(member["user_id"]) for member in member_list}
            if not exclusive_members.isdisjoint(member_ids):
                await client.set_group_leave(group_id=group_id)
                return
        
        # 所有检查通过, 发送欢迎语并安排延迟抽查
        welcome_msg = self.config.get("welcome_message", "")
        if welcome_msg:
            await event.reply(welcome_msg)
            
        group_id_str = str(group_id)
        if self.new_group_check_delay >= 0 and group_id_str not in self.scheduled_checks:
            async def _delayed_check():
                await asyncio.sleep(self.new_group_check_delay)
                if group_id_str not in self.scheduled_checks: return
                try:
                    current_groups = await client.get_group_list()
                    if any(str(g['group_id']) == group_id_str for g in current_groups):
                        await self.check_messages(client=client, target_id=group_id_str, is_automated=True)
                except Exception as e:
                    logger.error(f"对新群 {group_id_str} 的延迟抽查失败: {e}")
                finally:
                    self.scheduled_checks.pop(group_id_str, None)
            
            task = asyncio.create_task(_delayed_check())
            self.scheduled_checks[group_id_str] = task
            logger.info(f"已为新群 {group_id_str} 安排 {self.new_group_check_delay} 秒后的延迟抽查。")

    # ===== 管理员手动工具 =====
    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("同意", alias={"agree"})
    async def agree_request(self, event: AiocqhttpMessageEvent, extra: str = ""):
        reply = await self._process_approval_reply(event, approve=True, extra=extra)
        if reply: await event.reply(reply)

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("拒绝", alias={"refuse"})
    async def refuse_request(self, event: AiocqhttpMessageEvent, extra: str = ""):
        reply = await self._process_approval_reply(event, approve=False, extra=extra)
        if reply: await event.reply(reply)

    async def _process_approval_reply(self, event: AiocqhttpMessageEvent, approve: bool, extra: str) -> str:
        chain = event.get_messages(); reply_seg = next((seg for seg in chain if isinstance(seg, Comp.Reply)), None)
        if not (reply_seg and reply_seg.chain): return ""
        text = "".join(seg.text for seg in reply_seg.chain if isinstance(seg, Comp.Plain))
        lines = text.split("\n")
        client = event.bot
        try:
            flag = next(line.split("：", 1)[1] for line in lines if line.startswith("flag："))
            if "【收到好友申请】" in text:
                nickname = next(line.split("：", 1)[1] for line in lines if line.startswith("昵称："))
                await client.set_friend_add_request(flag=flag, approve=approve, remark=extra)
                return f"已{'同意' if approve else '拒绝'}好友【{nickname}】的申请。"
            elif "【收到群邀请】" in text:
                group_name = next(line.split("：", 1)[1] for line in lines if line.startswith("群名称："))
                await client.set_group_add_request(flag=flag, sub_type="invite", approve=approve, reason=extra)
                return f"已{'同意' if approve else '拒绝'}加入群聊【{group_name}】。"
        except Exception:
            return "审批失败，请求可能已过期或格式不正确。"
        return ""

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("好友列表")
    async def show_friends_info(self, event: AiocqhttpMessageEvent):
        client = event.bot; friend_list = await client.get_friend_list()
        info = "\n".join(f"{i+1}. {f['user_id']}: {f['nickname']}" for i, f in enumerate(friend_list))
        await event.reply(f"【好友列表】共{len(friend_list)}位好友：\n{info}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("群列表")
    async def show_groups_info(self, event: AiocqhttpMessageEvent):
        client = event.bot; group_list = await client.get_group_list()
        info = "\n".join(f"{i+1}. {g['group_id']}: {g['group_name']}" for i, g in enumerate(group_list))
        await event.reply(f"【群列表】共加入{len(group_list)}个群：\n{info}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("删除好友", alias={"删了"})
    async def delete_friend(self, event: AiocqhttpMessageEvent, user_id_str: str = ""):
        target_id = 0
        at_seg = next((seg for seg in event.get_messages() if isinstance(seg, Comp.At)), None)
        if at_seg: target_id = int(at_seg.qq)
        elif user_id_str.isdigit(): target_id = int(user_id_str)
        if not target_id: return await event.reply("请 @ 要删除的好友或提供其QQ号。")
        try:
            await event.bot.delete_friend(user_id=target_id)
            await event.reply(f"已删除好友：{target_id}")
        except Exception as e:
            await event.reply(f"删除好友 {target_id} 失败: {e}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("退群")
    async def set_group_leave(self, event: AiocqhttpMessageEvent, group_id_str: str = ""):
        if not group_id_str.isdigit(): return await event.reply("请提供正确的群号。")
        try:
            await event.bot.set_group_leave(group_id=int(group_id_str))
            await event.reply(f"已退出群聊：{group_id_str}")
        except Exception as e:
            await event.reply(f"退出群聊 {group_id_str} 失败: {e}")

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("抽查")
    async def check_messages_handle(self, event: AiocqhttpMessageEvent, target_id: str, count_str: str = ""):
        try:
            count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else self.default_check_count
            count = min(count, self.max_check_count)
            is_group = any(str(g['group_id']) == target_id for g in await event.bot.get_group_list())
            is_friend = any(str(f['user_id']) == target_id for f in await event.bot.get_friend_list())
            
            if not (is_group or is_friend):
                return await event.reply(f"错误：ID {target_id} 既不是我所在的群聊，也不是我的好友。")

            await self.check_messages(client=event.bot, target_id=target_id, count=count, 
                                      reply_to_group=int(event.get_group_id()) if event.get_group_id() else None,
                                      reply_to_user=event.get_sender_id())
        except Exception as e:
            logger.exception(e)
            await event.reply(f"抽查ID({target_id})消息失败: {e}")

    async def check_messages(self, client: CQHttp, target_id: str, count: int, is_automated: bool = False, 
                             reply_to_group: Optional[int] = None, reply_to_user: Optional[str] = None):
        result = None
        try:
            if any(str(g['group_id']) == target_id for g in await client.get_group_list()):
                result = await client.get_group_msg_history(group_id=int(target_id), count=count)
            elif any(str(f['user_id']) == target_id for f in await client.get_friend_list()):
                result = await client.get_friend_msg_history(user_id=int(target_id), count=count)
        except Exception as e:
            logger.error(f"获取 {target_id} 历史消息失败: {e}")
            if not is_automated: await self._send_to_admins(client, f"获取 {target_id} 历史消息失败: {e}")
            return

        if not result or not result.get("messages"):
            if not is_automated: await self._send_to_admins(client, f"未能获取到 {target_id} 的任何消息。")
            return

        nodes = [{"type": "node", "data": {"name": m["sender"]["nickname"], "uin": m["sender"]["user_id"], "content": m["message"]}} for m in result["messages"]]
        
        # 确定发送目标
        if reply_to_group:
            await client.send_group_forward_msg(group_id=reply_to_group, messages=nodes)
        elif reply_to_user:
            await client.send_private_forward_msg(user_id=int(reply_to_user), messages=nodes)
        else: # 自动抽查，发给所有管理员
            for admin_id in self.admins_id:
                if admin_id.isdigit():
                    await client.send_private_forward_msg(user_id=int(admin_id), messages=nodes)
