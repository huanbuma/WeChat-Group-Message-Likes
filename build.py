#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信自动化工具打包脚本
自动化exe打包过程
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理之前的构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 清理目录: {dir_name}")
            shutil.rmtree(dir_name)

def build_exe():
    """构建exe文件"""
    print("🚀 开始构建exe文件...")
    print("=" * 50)
    
    # 清理构建目录
    clean_build_dirs()
    
    try:
        # 使用PyInstaller构建
        cmd = ['pyinstaller', '--clean', 'build_exe.spec']
        print(f"📦 执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 构建成功!")
            
            # 检查生成的exe文件
            exe_path = Path('dist/微信自动化工具.exe')
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📁 生成的exe文件: {exe_path}")
                print(f"📏 文件大小: {size_mb:.1f} MB")
                return True
            else:
                print("❌ 未找到生成的exe文件")
                return False
        else:
            print("❌ 构建失败!")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def main():
    """主函数"""
    print("🔧 微信自动化工具 - exe打包器")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists('run_gui.py'):
        print("❌ 未找到run_gui.py文件，请在项目根目录运行此脚本")
        return False
    
    # 检查PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        print("✅ PyInstaller 已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller 未安装，请先安装: pip install pyinstaller")
        return False
    
    # 开始构建
    success = build_exe()
    
    if success:
        print("\n🎉 打包完成!")
        print("📁 exe文件位置: dist/微信自动化工具.exe")
        print("\n💡 使用提示:")
        print("   - 可以直接双击运行exe文件")
        print("   - 首次运行可能需要一些时间初始化")
        print("   - 建议将exe文件复制到独立文件夹中使用")
    else:
        print("\n❌ 打包失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    main()
    # 命令行入口点已移除input()调用，适配自动化构建