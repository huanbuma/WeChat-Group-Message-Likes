# 微信自动化工具 (WeChat Automation Tool)

一个基于 Python 和 PyQt5 的微信自动化工具，支持朋友圈点赞、群发消息等功能。

## ✨ 功能特性

### 🎯 朋友圈功能
- **智能点赞**：自动识别指定用户的朋友圈动态并进行点赞
- **批量点赞**：支持多个用户的批量点赞操作
- **智能滚动**：自动滚动朋友圈寻找目标用户
- **重复检测**：避免重复点赞已点赞的内容

### 💬 消息功能
- **群发消息**：支持向多个联系人或群聊发送消息
- **智能搜索**：自动搜索并定位目标联系人
- **批量操作**：支持批量发送，提高效率

### 🔧 技术特性
- **OCR 识别**：基于 RapidOCR 的文字识别技术
- **智能路径查找**：自动检测微信安装路径
- **现代化 GUI**：基于 PyQt5 的美观用户界面
- **多线程处理**：避免界面卡顿，提升用户体验

## 🚀 快速开始

### 环境要求

- Windows 10/11
- Python 3.8+
- 微信 PC 版

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/your-username/wechat-automation-tool.git
   cd wechat-automation-tool
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python wechat_automation_gui.py
   ```

### 使用方法

#### 朋友圈点赞
1. 启动程序后，切换到「朋友圈点赞」标签页
2. 在「目标用户」框中输入要点赞的用户昵称（支持多个用户，用逗号分隔）
3. 设置等待时间和滚动参数
4. 点击「开始点赞」按钮
5. 程序会自动打开微信朋友圈并执行点赞操作

#### 群发消息
1. 切换到「群发消息」标签页
2. 在「发送目标」中输入联系人或群聊名称（每行一个）
3. 在「消息内容」中输入要发送的消息
4. 点击「开始群发」按钮
5. 程序会自动搜索联系人并发送消息

## 📁 项目结构

```
wechat-automation-tool/
├── wechat_automation_gui.py    # 主程序 GUI 界面
├── wechat_core_engine.py       # 核心自动化引擎
├── wechat_launcher.py          # 微信启动器
├── rapid_ocr_engine.py         # OCR 识别引擎
├── build.py                    # 打包构建脚本
├── run_gui.py                  # 程序启动入口
├── requirements.txt            # 依赖包列表
├── README.md                   # 项目说明文档
├── LICENSE                     # 开源许可证
└── assets/                     # 资源文件
    ├── *.png                   # 图标文件
    └── *.svg                   # 矢量图标
```

## 🔧 配置说明

### 微信路径配置
程序会自动检测微信安装路径，检测顺序：
1. 配置文件中的路径
2. 常见安装路径
3. 注册表查询
4. 运行进程检测
5. 全盘搜索
6. 手动选择

### OCR 引擎配置
- 使用 RapidOCR 进行文字识别
- 支持中文文字识别
- 自动优化识别精度

## ⚠️ 注意事项

1. **使用前请确保**：
   - 微信 PC 版已安装并可正常使用
   - 屏幕分辨率设置合适（推荐 1920x1080）
   - 微信界面语言为中文

2. **使用限制**：
   - 请遵守微信使用规范，避免频繁操作
   - 建议设置合理的等待时间间隔
   - 不要用于商业推广等违规用途

3. **安全提醒**：
   - 本工具仅供学习和个人使用
   - 使用时请确保网络环境安全
   - 定期更新程序以获得最佳体验

## 🛠️ 开发指南

### 构建可执行文件

```bash
python build.py
```

生成的可执行文件位于 `dist/` 目录下。

### 代码结构说明

- `wechat_automation_gui.py`：主 GUI 界面，负责用户交互
- `wechat_core_engine.py`：核心自动化逻辑，包含所有自动化操作
- `wechat_launcher.py`：微信启动和路径管理
- `rapid_ocr_engine.py`：OCR 文字识别功能

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PyQt5](https://pypi.org/project/PyQt5/) - GUI 框架
- [RapidOCR](https://github.com/RapidAI/RapidOCR) - OCR 识别引擎
- [PyAutoGUI](https://pypi.org/project/PyAutoGUI/) - 自动化操作库

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-username/wechat-automation-tool/issues)
- 发送邮件至：your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！