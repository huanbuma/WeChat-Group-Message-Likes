#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信智能启动器
实现多种方式自动查找和启动微信
"""

import os
import json
import subprocess
import winreg
import psutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import time

class WeChatLauncher:
    def __init__(self):
        self.config_file = "wechat_config.json"
        self.common_paths = [
            r"C:\Program Files\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files\Tencent\Weixin\Weixin.exe",
            r"C:\Program Files (x86)\Tencent\Weixin\Weixin.exe",
            r"D:\Program Files\Tencent\WeChat\WeChat.exe",
            r"D:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"D:\Program Files\Tencent\Weixin\Weixin.exe",
            r"D:\Program Files (x86)\Tencent\Weixin\Weixin.exe",
            r"E:\Program Files\Tencent\WeChat\WeChat.exe",
            r"E:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"F:\Program Files\Tencent\WeChat\WeChat.exe",
            r"F:\Program Files (x86)\Tencent\WeChat\WeChat.exe"
        ]
        
    def load_config(self):
        """加载配置文件中的微信路径"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    wechat_path = config.get('wechat_path')
                    if wechat_path and os.path.exists(wechat_path):
                        print(f"从配置文件加载微信路径: {wechat_path}")
                        return wechat_path
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        return None
    
    def save_config(self, wechat_path):
        """保存微信路径到配置文件"""
        try:
            config = {'wechat_path': wechat_path}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"微信路径已保存到配置文件: {wechat_path}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def try_common_paths(self):
        """尝试常见的微信安装路径"""
        print("正在尝试常见安装路径...")
        for path in self.common_paths:
            if os.path.exists(path):
                print(f"找到微信路径: {path}")
                return path
        return None
    
    def query_registry(self):
        """查询注册表获取微信安装路径"""
        print("正在查询注册表...")
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Tencent\WeChat"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WeChat")
        ]
        
        for hkey, subkey in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    # 尝试不同的值名称
                    value_names = ['InstallPath', 'InstallLocation', 'DisplayIcon', 'UninstallString']
                    for value_name in value_names:
                        try:
                            value, _ = winreg.QueryValueEx(key, value_name)
                            if value:
                                # 处理不同格式的路径
                                if value_name == 'DisplayIcon' and value.endswith('.exe'):
                                    wechat_path = value
                                elif value_name == 'UninstallString':
                                    # 从卸载字符串中提取路径
                                    if 'WeChat.exe' in value or 'Weixin.exe' in value:
                                        parts = value.split('"')
                                        for part in parts:
                                            if part.endswith('.exe') and ('WeChat' in part or 'Weixin' in part):
                                                wechat_path = part
                                                break
                                        else:
                                            continue
                                    else:
                                        continue
                                else:
                                    # InstallPath或InstallLocation
                                    possible_exes = [os.path.join(value, 'WeChat.exe'), os.path.join(value, 'Weixin.exe')]
                                    for exe_path in possible_exes:
                                        if os.path.exists(exe_path):
                                            wechat_path = exe_path
                                            break
                                    else:
                                        continue
                                
                                if os.path.exists(wechat_path):
                                    print(f"从注册表找到微信路径: {wechat_path}")
                                    return wechat_path
                        except FileNotFoundError:
                            continue
            except Exception as e:
                continue
        return None
    
    def detect_running_process(self):
        """检测运行中的微信进程"""
        print("正在检测运行中的微信进程...")
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() in ['wechat.exe', 'weixin.exe']:
                        exe_path = proc.info['exe']
                        if exe_path and os.path.exists(exe_path):
                            print(f"从运行进程找到微信路径: {exe_path}")
                            return exe_path
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"检测进程失败: {e}")
        return None
    
    def search_all_drives(self):
        """全盘搜索微信可执行文件（最后手段）"""
        print("正在进行全盘搜索（这可能需要一些时间）...")
        drives = [f"{chr(i)}:\\" for i in range(ord('C'), ord('Z')+1) if os.path.exists(f"{chr(i)}:\\")]
        
        search_patterns = ['WeChat.exe', 'Weixin.exe']
        common_folders = ['Program Files', 'Program Files (x86)', 'Tencent']
        
        for drive in drives:
            print(f"搜索驱动器: {drive}")
            # 优先搜索常见文件夹
            for folder in common_folders:
                folder_path = os.path.join(drive, folder)
                if os.path.exists(folder_path):
                    for pattern in search_patterns:
                        for root, dirs, files in os.walk(folder_path):
                            if pattern in files:
                                full_path = os.path.join(root, pattern)
                                if 'Tencent' in root and ('WeChat' in root or 'Weixin' in root):
                                    print(f"全盘搜索找到微信路径: {full_path}")
                                    return full_path
        return None
    
    def manual_select_path(self):
        """提示用户手动选择微信路径"""
        print("请手动选择微信可执行文件...")
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        file_path = filedialog.askopenfilename(
            title="请选择微信可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            initialdir="C:\\Program Files"
        )
        
        root.destroy()
        
        if file_path and os.path.exists(file_path):
            print(f"用户选择的微信路径: {file_path}")
            return file_path
        return None
    
    def find_wechat_path(self):
        """按优先级查找微信路径"""
        methods = [
            ("配置文件", self.load_config),
            ("常见路径", self.try_common_paths),
            ("注册表", self.query_registry),
            ("运行进程", self.detect_running_process),
            ("全盘搜索", self.search_all_drives),
            ("手动选择", self.manual_select_path)
        ]
        
        for method_name, method in methods:
            print(f"\n尝试方法: {method_name}")
            try:
                path = method()
                if path:
                    # 保存找到的路径到配置文件（除非是从配置文件加载的）
                    if method_name != "配置文件":
                        self.save_config(path)
                    return path
            except Exception as e:
                print(f"{method_name}方法失败: {e}")
                continue
        
        return None
    
    def launch_wechat(self, wechat_path=None):
        """启动微信"""
        if not wechat_path:
            wechat_path = self.find_wechat_path()
        
        if not wechat_path:
            print("错误: 无法找到微信可执行文件")
            return False
        
        try:
            print(f"正在启动微信: {wechat_path}")
            subprocess.Popen([wechat_path], shell=True)
            print("微信启动成功")
            return True
        except Exception as e:
            print(f"启动微信失败: {e}")
            return False
    
    def is_wechat_running(self):
        """检查微信是否正在运行"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() in ['wechat.exe', 'weixin.exe']:
                    return True
        except Exception:
            pass
        return False

# 命令行入口点已移除，此文件现在仅作为GUI的后端模块使用
# 所有功能通过GUI界面调用，不再支持独立的命令行运行