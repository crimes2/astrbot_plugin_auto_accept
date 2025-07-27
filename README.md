<div align="center">
 
![:name](https://count.getloli.com/@astrbot_plugin_auto_handler?name=astrbot_plugin_auto_handler&theme=morden-num&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)
 
# astrbot_plugin_auto_handler
 
_✨ 智能自动化管家 & 高级手动管理平台 ✨_  
 
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.5%2B-orange.svg)](https://github.com/AstrBotDevs/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-crimes2-blue)](https://github.com/crimes2)
 
</div>
 
## 💡 介绍
 
`astrbot_plugin_auto_handler` 不仅仅是一个自动化请求处理器，它是一个功能完备的 **Bot 智能管家**。它将强大的 **7x24 小时自动化规则引擎** 与一套完善的 **管理员手动工具** 相结合，让您既能解放双手，又能随时随地精准掌控 Bot 的一举一动。
 
---
 
### **核心功能一览**
 
#### 🤖 **自动化核心**
- **全自动请求处理**: 可配置好友请求和群聊邀请为“全部同意”、“全部拒绝”或“转交管理员”模式。
- **多层规则过滤**:
    - **管理员优先**: 自动同意所有来自管理员的邀请。
    - **黑名单系统**: 自动拒绝来自邀请者黑名单或群聊黑名单的邀请，并向邀请者发送拒绝说明。
    - **条件性退群**:
        - **互斥成员**: Bot 加入群聊后若发现互斥成员，将自动退群并通知邀请者。
        - **人数上限**: Bot 所在群聊超过设定人数后自动退群。
        - **禁言惩罚**: Bot 被禁言超过设定时长后自动退群。
- **智能入群观察**: Bot 被拉入新群后，可配置延迟一段时间（如10分钟）后，自动抽查群内近期消息并汇报给管理员。
 
#### 🛠️ **手动管理工具**
- **信息查询**: 通过简单指令，随时查看 Bot 的好友与群聊列表。
- **关系管理**: 管理员可随时通过指令让 Bot 删除指定好友或退出指定群聊。
- **全能消息抽查**: 强大的`/抽查`指令，不仅能抽查**群聊**，还能抽查与**好友**的私聊记录，并可指定抽查条数，是您监控和追溯问题的利器。
 
---
 
## 📦 安装
 
- **推荐**: 在 AstrBot 的插件市场搜索 `astrbot_plugin_auto_handler`，点击安装即可。
- **手动安装**:
```bash
# 进入 AstrBot 插件目录
cd /opt/AstrBot/data/plugins
# 克隆仓库
git clone https://github.com/Lumine-Inc/astrbot-plugin-auto-handler
# 重启 AstrBot 服务
systemctl restart astrbot
```

⚙️ 配置
所有功能均可通过 AstrBot 的 WebUI 面板进行配置，路径：插件管理 -> astrbot_plugin_auto_handler -> 操作 -> 插件配置。

配置项	类型	默认值	说明
friend_request_mode	string	manual	好友请求模式 (accept:同意, reject:拒绝, manual:转交管理员)。
group_invite_mode	string	manual	群邀请基础模式 (同上，但特殊规则优先)。
group_inviter_blacklist	list	[]	邀请者黑名单: 拒绝此列表用户的邀请 (填QQ号)。
group_blacklist	list	[]	群聊黑名单: 拒绝加入或立刻退出此列表的群 (填群号)。
exclusive_members	list	[]	互斥成员列表: 入群后若发现他们，则自动退群 (填QQ号)。
max_group_capacity	int	100	最大群容量: Bot 总群数超过此值后，会拒绝新邀请。
max_ban_duration	int	86400	禁言退群阈值(秒): 被禁言超过此时长后自动退群。0为禁用。
welcome_message	string	''	入群欢迎语: 成功入群后发送的消息，留空则不发。
new_group_check_delay	int	600	新群延迟抽查(秒): Bot 加入新群后，等待多少秒再自动抽查。
default_check_count	int	20	默认抽查条数: /抽查指令不指定数量时的默认值。
max_check_count	int	100	最大抽查条数: 单次/抽查可获取的最大消息数。
⌨️ 使用说明与指令
本插件的自动化功能在配置完成后即刻生效。管理员可通过以下指令与 Bot 交互：

指令	别名	参数	说明
/好友列表			查看所有好友的QQ号与昵称。
/群列表			查看所有已加入群聊的群号与群名。
/删除好友	/删了	<QQ号 或 @成员>	删除指定好友。
/退群		<群号>	让 Bot 退出指定群聊。
/抽查		<QQ号或群号> [数量]	核心功能: 抽查与某人或某群的聊天记录，并以合并转发形式发送。
🤝 TODO
 自动处理好友与群聊请求
 实现了基于管理员、黑名单、互斥成员、群容量、禁言时长的多重自动化规则
 实现了被踢后自动拉黑群聊
 实现了新群延迟自动抽查
 实现了可抽查私聊和群聊的/抽查指令
 完善管理员通过回复消息直接审批请求的流程
 增加邀请者白名单模式 (与黑名单互斥)
👥 贡献指南
我们欢迎任何形式的贡献和建议，让这个插件变得更好！

🌟 Star 这个项目！
🐛 通过 Issues 提交 Bug报告。
💡 通过 Issues 提出 新功能建议。
🔧 提交 Pull Request 帮助我们改进代码。
