# 🐾 Claw-GA 桌面宠物

基于 PyQt6 的 AI 桌面宠物，带有像素精灵动画和 GenericAgent 智能对话功能。

## 功能特性

- 🎨 **透明像素宠物** - 支持透明背景的像素精灵动画
- 💬 **AI 对话** - 集成 GenericAgent，支持智能对话
- 🎮 **多状态动画** - idle、walk、run、slide、work_sleep 等动画状态
- 🖱️ **拖拽移动** - 左键点击拖拽移动宠物位置
- 📦 **收缩模式** - 双击宠物隐藏/显示聊天框

## 项目结构

```
claw-ga/
├── pet_clean.py          # 主程序
├── cut_sprites.py        # 精灵图裁剪工具
├── sprites_yoffset3/     # 像素精灵图
│   ├── idle_front/
│   ├── walk_front/
│   ├── walk_left/
│   ├── walk_right/
│   ├── run/
│   ├── slide/
│   ├── work_sleep/
│   └── jump/
└── GenericAgent/         # AI 对话引擎
```

## 运行方式

```bash
# 安装依赖
pip install PyQt6 requests

# 运行宠物
python pet_clean.py
```

## 环境要求

- Python 3.11+
- PyQt6
- requests

## 预览

宠物会在桌面显示，支持对话交互。
双击收缩/展开聊天面板，左键拖拽移动位置。