<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_auto_handler?name=astrbot_plugin_auto_handler&theme=morden-num&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_auto_handler

_✨ 智能好友与群聊自动化管家 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.5%2B-orange.svg)](https://github.com/AstrBotDevs/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-crimes2-blue)](https://github.com/crimes2)

</div>

## 💡 介绍

`astrbot_plugin_auto_handler` 是一个为 AstrBot 设计的强大且高度可配置的自动化请求处理器。它能让您的 Bot 7x24 小时全自动处理好友请求和群聊邀请，无需任何人工干预。插件内置了丰富的规则引擎，可以根据您的设定，智能地决定接受或拒绝，极大解放您的双手。

**核心功能：**
- **自动处理好友请求**：可设置为全部同意、全部拒绝或忽略。
- **智能处理群聊邀请**：基于多重规则进行判断，包括：
    - **管理员优先**：自动同意所有来自管理员的邀请。
    - **邀请者黑名单**：自动拒绝黑名单用户的邀请。
    - **互斥成员检查**：如果群内已有指定成员，则拒绝加入，避免冲突。
    - **最小群规模限制**：拒绝加入人数过少的群聊。
    - **自动拉黑**：当 Bot 被从群里踢出时，自动将操作者加入黑名单。

## 📦 安装

- **推荐**：在 AstrBot 的插件市场搜索 `astrbot_plugin_auto_handler`，点击安装即可。
- **手动安装**：克隆本仓库到您的插件文件夹：

```bash
# 进入 AstrBot 插件目录
cd /opt/AstrBot/data/plugins

# 克隆仓库 (请注意，这是一个示例链接，未来可能会建立正式仓库)
git clone https://github.com/Lumine-Inc/astrbot-plugin-auto-handler

# 重启 AstrBot 服务
systemctl restart astrbot
```

## ⚙️ 配置

所有功能均可通过 AstrBot 的 WebUI 面板进行配置，路径：`插件管理` -> `astrbot_plugin_auto_handler` -> `操作` -> `插件配置`。

**配置项说明：**

| 配置项 | 类型 | 默认值 | 说明 |
| :--- | :---: | :---: | :--- |
| `friend_request_mode` | `string` | `ignore` | 好友请求处理模式 (accept: 同意, reject: 拒绝, ignore: 忽略)。 |
| `group_invite_mode` | `string` | `ignore` | 群邀请处理模式 (除特殊规则外)。 |
| `group_blacklist_enabled` | `bool` | `true` | 是否启用邀请者黑名单功能。 |
| `group_blacklist_user_ids`| `list` | `[]` | 黑名单QQ号列表。 |
| `group_blacklist_rejection_message` | `string` | `...` | 拒绝黑名单邀请时的理由。 |
| `exclusive_members_enabled` | `bool` | `true` | 是否启用互斥成员检查。 |
| `exclusive_members_user_ids`| `list` | `[]` | 互斥成员QQ号列表。 |
| `exclusive_members_exit_message` | `string` | `...` | 检测到互斥成员时的退群/拒绝理由。 |
| `min_group_size_enabled`| `bool` | `false` | 是否启用最小群人数检查。 |
| `min_group_size_count` | `int` | `10` | 允许加入的最小群成员数。 |
| `min_group_size_rejection_message` | `string` | `...` | 因群太小而拒绝邀请的理由。 |
| `welcome_message_enabled` | `bool` | `true` | 是否在同意入群后发送欢迎语。 |
| `welcome_message_message` | `string` | `大家好...` | 入群欢迎语的具体内容。 |
| `auto_leave_if_muted_enabled` | `bool` | `true` | **(当前版本因兼容性暂未生效)** 是否启用被禁言自动退群。 |
| `auto_leave_if_muted_duration_hours` | `int` | `24` | **(当前版本因兼容性暂未生效)** 被禁言超过多少小时后退群。 |


## ⌨️ 使用说明

本插件**无任何指令**，所有功能均为全自动后台运行。您只需在配置面板中完成设置，插件便会根据您的规则忠实地执行任务。

## 🤝 TODO

- [x] 自动处理好友请求
- [x] 基于多重规则（管理员、黑名单、互斥成员、群规模）自动处理群邀请
- [x] 自动将被踢操作者加入黑名单
- [ ] 重新启用并优化“被禁言自动退群”功能（待 AstrBot 核心版本更新支持）
- [ ] 增加邀请者白名单模式
- [ ] 增加指令用于临时开启/关闭/切换处理模式
- [ ] 为所有自动化操作增加详细的日志推送，方便主人监控

## 👥 贡献指南

我们欢迎任何形式的贡献和建议，让这个插件变得更好！
- 🌟 **Star** 这个项目！
- 🐛 通过 [Issues](https://github.com/Lumine-Inc/astrbot-plugin-auto-handler/issues) 提交 **Bug报告**。
- 💡 通过 [Issues](https://github.com/Lumine-Inc/astrbot-plugin-auto-handler/issues) 提出 **新功能建议**。
- 🔧 提交 **Pull Request** 帮助我们改进代码。

## 📌 注意事项
- 如有任何问题，欢迎通过 GitHub Issues 进行反馈。
