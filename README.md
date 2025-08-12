
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_record_converter?name=astrbot_plugin_record_converter&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_record_converter

_✨ [astrbot](https://github.com/AstrBotDevs/AstrBot)语音转化插件 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Zhalslar-blue)](https://github.com/Zhalslar)

</div>

## 🤝 介绍

QQ语音转化插件，包括语音转文件，文件转语音，克服了QQ语音无法转发的问题

## 📦 安装

- 直接在astrbot的插件市场搜索astrbot_plugin_record_converter，点击安装，等待完成即可

- 也可以克隆源码到插件文件夹：

```bash
# 克隆仓库到插件目录
cd /AstrBot/data/plugins
git clone https://github.com/Zhalslar/astrbot_plugin_record_converter

# 控制台重启AstrBot
```

## ⌨️ 配置

请前往插件配置面板进行配置

| 配置项       | 说明 | 取值范围 / 选项 |
| ------------ | ---- | --------------- |
| `format`     | 转化后的语音格式 | `mp3`, `amr`, `wma`, `m4a`, `spx`, `ogg`, `wav`, `flac` |
| `send_private`  | 语音转文件时是否仅私发给用户，避免在群聊中显示以保护隐私 | `true` / `false` |

## 🤝 使用说明

### 命令表

| 命令     | 说明                       |  使用方法                       |
| -------- | ------------------------- | ------------------------------ | 
| 转格式   | 语音消息<->音频文件  | 需要引用要传化的语音消息或音频文件；可私发文件（根据配置项 `send_private`） |

### 效果图

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561（不点star不给进）
