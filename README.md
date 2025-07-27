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
 
`astrbot_plugin_auto_handler` 是一个功能完备的 **Bot 智能管家**。它将强大的 **7x24 小时自动化规则引擎** 与一套完善的 **管理员手动工具** 相结合，让您既能解放双手，又能随时随地精准掌控 Bot 的一举一动。
 
---
 
### **核心功能一览**
 
#### 🤖 **自动化核心**
- **全自动请求处理**: 可配置好友请求和群聊邀请为“全部同意”、“全部拒绝”或“转交管理员审批”。
- **多层规则过滤**:
    - **管理员优先**: 自动同意所有来自管理员的邀请。
	- **邀请者过滤器(新!)**: 可在 `黑名单` (拒绝特定用户) 和 `白名单` (仅接受特定用户) 模式间切换。
    - **群聊黑名单**: 自动拒绝加入黑名单中的群聊。
    - **条件性退群**: 包括互斥成员、群容量超限、被禁言超长等多种自动退群机制。
- **智能入群观察**: Bot 被拉入新群后，可配置延迟一段时间后，自动抽查群内近期消息并汇报给管理员。
 
#### 🛠️ **手动管理工具**
- **回复审批(新!)**: 管理员收到请求通知后，可直接**回复**该消息并输入`同意`或`拒绝`来完成审批，高效便捷。
- **信息查询**: 通过简单指令，随时查看 Bot 的好友与群聊列表。
- **关系管理**: 管理员可随时通过指令让 Bot 删除指定好友或退出指定群聊。
- **全能消息抽查**: 强大的`/抽查`指令，支持抽查群聊和好友的私聊记录。
 
---
 
## 📦 安装
 
```bash
# 进入 AstrBot 插件目录
cd /opt/AstrBot/data/plugins
# 克隆仓库
git clone https://github.com/Lumine-Inc/astrbot-plugin-auto-handler
# 重启 AstrBot 服务
systemctl restart astrbot
```

---

## ⚙️ 配置

所有功能均可通过 AstrBot 的 WebUI 面板配置：`插件管理` -> `astrbot_plugin_auto_handler` -> `插件配置`。

| 配置项 | 说明 |
| :--- | :--- |
| `friend_request_mode` | 好友请求模式 (accept:同意, reject:拒绝, manual:转交审批)。 |
| `group_invite_mode` | 群邀请基础模式 (同上，但特殊规则优先)。 |
| `inviter_filter_mode` | **[新]** 邀请者过滤模式 (none:不过滤, blacklist:黑名单, whitelist:白名单)。|
| `inviter_blacklist`| 邀请者黑名单QQ号列表。 |
| `inviter_whitelist`| **[新]** 邀请者白名单QQ号列表。 |
| `group_blacklist`| 群聊黑名单群号列表。 |
| `exclusive_members`| 互斥成员QQ号列表。 |
| `max_group_capacity` | Bot允许加入的最大总群数。 |
| `max_ban_duration` | 被禁言自动退群的秒数阈值。 |
| `welcome_message` | 入群欢迎语，留空不发。 |
| `new_group_check_delay`| 新群延迟抽查的秒数。 |
| `default_check_count` | `/抽查`指令的默认消息条数。 |
| `max_check_count` | `/抽查`指令的最大消息条数。 |

---

## ⌨️ 使用说明与指令

| 指令 | 别名 | 参数 | 说明 |
| :--- | :---: | :---: | :--- |
| `同意` | `agree` | `[理由/备注]` | **[新]** **回复**请求通知以同意申请。 |
| `拒绝` | `refuse`| `[理由]`| **[新]** **回复**请求通知以拒绝申请。 |
| `/好友列表` | | | 查看所有好友。 |
| `/群列表` | | | 查看所有群聊。 |
| `/删除好友` | `/删了` | `<QQ号 或 @成员>` | 删除指定好友。 |
| `/退群` | | `<群号>` | 让 Bot 退出指定群聊。 |
| `/抽查` | | `<ID> [数量]` | 抽查与某人或某群的聊天记录。 |

---

## 🤝 TODO

- [x] 自动处理好友与群聊请求
- [x] 实现了完整的自动化规则引擎
- [x] 实现了新群延迟自动抽查
- [x] 实现了可抽查私聊和群聊的`/抽查`指令
- [x] **完成: 完善管理员通过回复消息直接审批请求的流程**
- [x] **完成: 增加邀请者白名单模式**
- [ ] 后续可考虑增加“临时审批”功能，如同意某次黑名单邀请而不将其移出黑名单。

---

## 👥 贡献指南

我们欢迎任何形式的贡献和建议！
- 🌟 **Star** 这个项目！
- 🐛 通过 **Issues** 提交 **Bug报告**。
- 💡 通过 **Issues** 提出 **新功能建议**。
- 🔧 提交 **Pull Request** 帮助我们改进代码。
