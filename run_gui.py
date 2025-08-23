#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信自动化工具 - GUI启动器
快速启动图形界面版本
"""

import sys
import os

def safe_print(message):
    """安全的打印函数，在无控制台模式下不会崩溃"""
    try:
        print(message)
    except:
        pass

def main():
    """主启动函数"""
    safe_print("🚀 正在启动微信自动化工具 GUI界面...")
    safe_print("=" * 50)
    
    try:
        # 检查PyQt5是否已安装
        import PyQt5
        safe_print("✅ PyQt5 已安装")
    except ImportError:
        safe_print("❌ PyQt5 未安装，正在尝试安装...")
        os.system("pip install PyQt5==5.15.10")
        safe_print("✅ PyQt5 安装完成")
    
    try:
        # 导入并启动GUI
        from wechat_automation_gui import main as gui_main
        safe_print("✅ 正在启动GUI界面...")
        gui_main()
    except ImportError as e:
        safe_print(f"❌ 导入GUI模块失败: {e}")
        safe_print("请确保 wechat_automation_gui.py 文件存在")
    except Exception as e:
        safe_print(f"❌ 启动GUI失败: {e}")
        # GUI模式下不需要用户交互，直接退出
        pass

if __name__ == "__main__":
    main()