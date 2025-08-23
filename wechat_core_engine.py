#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信朋友圈搜索工具 - 精简版
只包含两个核心功能：
1. 搜索联系人
2. 朋友圈功能（查找指定用户并点赞）
"""

import pyautogui
import time
import numpy as np
import win32gui
import win32con
import win32process
import os
from PIL import Image

# 导入微信启动器
try:
    from wechat_launcher import WeChatLauncher
    wechat_launcher = WeChatLauncher()
except ImportError:
    wechat_launcher = None



# 导入OCR引擎
try:
    from rapid_ocr_engine import get_ocr_engine
    ocr_engine = get_ocr_engine()
    RAPID_OCR_AVAILABLE = ocr_engine and ocr_engine.is_available()
    if RAPID_OCR_AVAILABLE:
        print("✅ RapidOCR核心引擎已加载")
    else:
        print("❌ RapidOCR核心引擎加载失败")
except ImportError as e:
    print(f"❌ RapidOCR引擎导入失败: {e}")
    ocr_engine = None
    RAPID_OCR_AVAILABLE = False

# 只使用RapidOCR，不再导入其他OCR模块

# 配置pyautogui
#pyautogui.FAILSAFE = True
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.5

# 自动化配置已从 wechat_automation 模块导入

# ==================== 核心工具函数 ====================

# 微信启动和激活功能已从 wechat_automation 模块导入

def find_wechat_main_window():
    """统一的微信主窗口查找函数"""
    windows = []
    def enum_windows_callback(hwnd, windows):
        try:
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                # 查找微信主窗口（不是朋友圈窗口）
                if "微信" in window_text and "朋友圈" not in window_text:
                    # 验证窗口句柄是否有效
                    if win32gui.IsWindow(hwnd):
                        windows.append((hwnd, window_text))
        except:
            # 忽略无效窗口
            pass
        return True
    
    win32gui.EnumWindows(enum_windows_callback, windows)
    return windows

def is_wechat_in_foreground():
    """检测微信窗口是否已在前台"""
    try:
        # 获取当前前台窗口
        foreground_hwnd = win32gui.GetForegroundWindow()
        if not foreground_hwnd:
            return False
        
        # 获取前台窗口标题
        foreground_title = win32gui.GetWindowText(foreground_hwnd)
        
        # 检查是否是微信窗口（包含"微信"关键字）
        if "微信" in foreground_title:
            return True
        
        # 如果标题检查失败，尝试通过进程名检查
        try:
            import psutil
            pid = win32process.GetWindowThreadProcessId(foreground_hwnd)[1]
            process = psutil.Process(pid)
            if "wechat" in process.name().lower() or "weixin" in process.name().lower():
                return True
        except:
            pass
        
        return False
    except Exception as e:
        # 静默处理错误，避免过多输出
        return False

def ensure_wechat_is_active():
    """
    确保微信窗口处于活动状态的统一函数。
    优先使用subprocess.Popen避免系统托盘窗口失效问题，然后用win32gui验证效果。
    """
    print("🚀 正在确保微信处于活动状态...")

    # 1. 优先使用subprocess.Popen启动/唤醒微信（更可靠）
    print("🔄 使用subprocess.Popen启动/唤醒微信...")
    try:
        if launch_wechat_internal():
            # 等待微信响应
            time.sleep(2)
            
            # 使用win32gui验证窗口是否成功激活到前台
            if activate_wechat_window_internal():
                print("✅ (Popen -> win32gui) 微信已成功启动并激活")
                return True
            else:
                print("⚠️ (Popen) 微信已启动，尝试强制激活到前台...")
                # 再次尝试激活，有时需要多次尝试
                time.sleep(1)
                if activate_wechat_window_internal():
                    print("✅ (Popen -> win32gui) 微信已强制激活到前台")
                    return True
                else:
                    print("⚠️ (Popen) 微信已启动，但无法确保在前台")
                    return True  # 微信已启动，即使不在前台也可能可以使用
        else:
            print("❌ (Popen) 启动微信失败，尝试win32gui备用方案...")
    except Exception as e:
        print(f"⚠️ (Popen) 启动/唤醒微信时出错: {e}，尝试win32gui备用方案...")

    # 2. 如果subprocess.Popen失败，使用win32gui作为备用方案
    print("🔄 使用win32gui备用方案...")
    try:
        if activate_wechat_window_internal():
            print("✅ (win32gui) 微信窗口已成功激活")
            return True
        else:
            print("❌ (win32gui) 无法激活微信窗口")
            return False
    except Exception as e:
        print(f"❌ (win32gui) 激活失败: {e}")
        return False

def launch_wechat_internal():
    """内部函数：仅用于启动微信进程"""
    if wechat_launcher:
        wechat_path = wechat_launcher.find_wechat_path()
        if not wechat_path:
            print("  -> (Popen) 未找到微信安装路径")
            return False
    else:
        print("  -> (Popen) 微信启动器不可用")
        return False
    
    try:
        import subprocess
        process = subprocess.Popen([wechat_path])
        print(f"  -> (Popen) 微信进程已启动 (PID: {process.pid})")
        return True
    except Exception as e:
        print(f"  -> (Popen) 启动微信失败: {str(e)}")
        return False

def activate_wechat_window_internal():
    """内部函数：仅用于激活微信窗口"""
    wechat_windows = find_wechat_main_window()
    if not wechat_windows:
        print("  -> (win32gui) 未找到微信主窗口")
        return False

    hwnd, window_title = wechat_windows[0]
    try:
        if win32gui.IsWindow(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.2)
            win32gui.SetForegroundWindow(hwnd)
            print(f"  -> (win32gui) 正在激活窗口: {window_title}")
            time.sleep(0.5) # 等待窗口响应
            # 验证是否成功
            if win32gui.GetForegroundWindow() == hwnd:
                return True
    except Exception as e:
        print(f"  -> (win32gui) 激活窗口时出错: {e}")
    return False

def verify_search_input_with_ocr(search_term, stop_flag_func=None):
    """统一的OCR验证搜索输入函数"""
    print("🔍 使用OCR验证中文输入是否成功...")
    try:
        # 截取搜索框区域进行OCR识别
        screenshot = pyautogui.screenshot()
        
        # 获取搜索框精确位置（微信搜索框通常在顶部中央）
        screen_width, screen_height = pyautogui.size()
        search_box_region = (
            int(screen_width * 0.25),  # 左边界：屏幕宽度的25%
            int(screen_height * 0.08),  # 上边界：屏幕高度的8%
            int(screen_width * 0.5),   # 宽度：屏幕宽度的50%
            int(screen_height * 0.08)  # 高度：屏幕高度的8%（更小的高度，只包含搜索框）
        )
        
        # 裁剪搜索框区域
        search_box_screenshot = screenshot.crop(search_box_region)
        
        # 保存截图用于调试（可选）
        try:
            pass
            # 调试代码已移除
        except:
            pass
        
        # 使用全局OCR引擎识别搜索框内容
        if not RAPID_OCR_AVAILABLE or not ocr_engine:
            print("⚠️ OCR引擎不可用，跳过验证")
            return True
        
        # 将PIL图像转换为numpy数组
        import numpy as np
        img_array = np.array(search_box_screenshot)
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 收到停止信号，中断OCR验证")
            return True
            
        # 进行OCR识别
        ocr_results = ocr_engine.recognize_text(img_array)
        
        if ocr_results:
            # 提取识别到的文本
            recognized_text = ""
            for result in ocr_results:
                if len(result) >= 2:
                    recognized_text += result[1]
            
            print(f"🔍 OCR识别结果: '{recognized_text}'")
            
            # 检查识别结果是否包含搜索词
            if search_term in recognized_text or recognized_text in search_term:
                print("✅ OCR验证成功：输入内容正确显示在搜索框中")
                return True
            else:
                print(f"⚠️ OCR验证警告：搜索框显示内容与预期不符")
                print(f"   预期: '{search_term}'")
                print(f"   实际: '{recognized_text}'")
                
                # GUI模式下自动继续搜索
                return True
        else:
            # OCR未识别到内容，但程序会继续执行搜索结果识别
            return True
                        
    except Exception as ocr_error:
        print(f"⚠️ OCR验证失败: {ocr_error}")
        print("💡 将继续执行搜索...")
        return True

def create_color_filtered_image(image, target_color_rgb, tolerance=30):
    """创建基于颜色过滤的图像，保留目标颜色的文字"""
    if isinstance(image, Image.Image):
        image_array = np.array(image)
    else:
        image_array = image.copy()
    
    # 确保图像是RGB格式
    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
        # 如果是BGR格式，转换为RGB
        if hasattr(image, 'mode') and image.mode == 'RGB':
            pass  # 已经是RGB
        else:
            # 假设是BGR，转换为RGB
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    
    target_r, target_g, target_b = target_color_rgb
    
    # 使用更宽松的颜色匹配
    # 计算每个通道的差异
    r_diff = np.abs(image_array[:, :, 0].astype(np.int16) - target_r)
    g_diff = np.abs(image_array[:, :, 1].astype(np.int16) - target_g)
    b_diff = np.abs(image_array[:, :, 2].astype(np.int16) - target_b)
    
    # 创建掩码：所有通道都在容差范围内
    mask = (r_diff <= tolerance) & (g_diff <= tolerance) & (b_diff <= tolerance)
    
    # 创建过滤后的图像：白色背景，黑色文字
    filtered_image = np.ones_like(image_array) * 255  # 白色背景
    filtered_image[mask] = [0, 0, 0]  # 匹配的像素设为黑色（文字）
    
    # 保存调试图像
    try:
        # 调试代码已移除
        print(f"🎨 目标颜色: RGB{target_color_rgb}, 容差: {tolerance}")
        print(f"📊 匹配像素数量: {np.sum(mask)}")
    except:
        pass
    
    return filtered_image

def color_targeted_ocr_recognition(image, target_name, target_color_rgb=(87, 107, 149), tolerance=20, stop_flag_func=None):
    """使用颜色过滤进行OCR识别"""
    if not RAPID_OCR_AVAILABLE or not ocr_engine or not ocr_engine.is_available():
        return None
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 颜色OCR识别被停止")
        return None
    
    try:
        # 创建颜色过滤图像
        color_filtered_image = create_color_filtered_image(image, target_color_rgb, tolerance)
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 颜色OCR识别被停止")
            return None
        
        # 转换为PIL图像再转为numpy数组
        if isinstance(color_filtered_image, np.ndarray):
            filtered_pil = Image.fromarray(color_filtered_image.astype(np.uint8))
            filtered_array = np.array(filtered_pil)
        else:
            filtered_array = np.array(color_filtered_image)
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 颜色OCR识别被停止")
            return None
        
        # 使用RapidOCR识别
        result = ocr_engine.recognize_text(filtered_array)
        
        if result and len(result) > 0:
            for detection in result:
                # 检查停止标志
                if stop_flag_func and stop_flag_func():
                    print("⏹️ 颜色OCR识别被停止")
                    return None
                    
                if len(detection) >= 2:
                    text = detection[1]
                    if target_name in text:
                        bbox = detection[0]
                        center_x = int((bbox[0][0] + bbox[2][0]) / 2)
                        center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                        return (center_x, center_y)
        
        return None
        
    except Exception as e:
        print(f"❌ 颜色OCR识别失败: {e}")
        return None

def color_targeted_ocr_recognition_yesterday(image, target_name, target_color_rgb=(158, 158, 158), tolerance=40, stop_flag_func=None):
    """专门用于"昨天"标记检测的颜色过滤OCR识别，使用独立的调试文件名"""
    if not RAPID_OCR_AVAILABLE or not ocr_engine or not ocr_engine.is_available():
        return None
    
    try:
        # 创建颜色过滤图像
        image_array = np.array(image)
        target_r, target_g, target_b = target_color_rgb
        
        # 计算每个像素与目标颜色的差异
        r_diff = np.abs(image_array[:, :, 0].astype(np.int16) - target_r)
        g_diff = np.abs(image_array[:, :, 1].astype(np.int16) - target_g)
        b_diff = np.abs(image_array[:, :, 2].astype(np.int16) - target_b)
        
        # 创建掩码：所有通道都在容差范围内
        mask = (r_diff <= tolerance) & (g_diff <= tolerance) & (b_diff <= tolerance)
        
        # 创建过滤后的图像：白色背景，黑色文字
        filtered_image = np.ones_like(image_array) * 255  # 白色背景
        filtered_image[mask] = [0, 0, 0]  # 匹配的像素设为黑色（文字）
        
        # 保存专用的调试图像
        try:
            # 调试代码已移除
            print(f"🎨 目标颜色: RGB{target_color_rgb}, 容差: {tolerance}")
            print(f"📊 匹配像素数量: {np.sum(mask)}")
        except:
            pass
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 收到停止信号，中断OCR识别")
            return None
            
        # 使用RapidOCR识别
        result = ocr_engine.recognize_text(filtered_image.astype(np.uint8))
        
        # 打印OCR识别结果用于调试
        print(f"🔍 OCR识别结果: {result}")
        
        if result and len(result) > 0:
            print(f"📝 识别到 {len(result)} 个文本区域:")
            for i, detection in enumerate(result):
                if len(detection) >= 2:
                    text = detection[1]
                    confidence = detection[2] if len(detection) > 2 else "未知"
                    print(f"   {i+1}. 文本: '{text}', 置信度: {confidence}")
                    # 检查是否匹配"昨天"或其OCR识别变体
                    yesterday_variants = ["昨天", "咋天", "作天", "昨夭", "咋夭", "作夭"]
                    if any(variant in text for variant in yesterday_variants):
                        bbox = detection[0]
                        center_x = int((bbox[0][0] + bbox[2][0]) / 2)
                        center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                        print(f"✅ 找到'昨天'标记变体 '{text}' (匹配目标: {target_name})")
                        return (center_x, center_y)
        else:
            print("📝 OCR未识别到任何文本")
        
        return None
        
    except Exception as e:
        print(f"❌ '昨天'标记颜色OCR识别失败: {e}")
        return None

def smart_ocr_recognition(image, target_name, stop_flag_func=None):
    """智能OCR识别函数，专门识别颜色#576b95的文字（朋友圈用户名颜色）"""
    if not RAPID_OCR_AVAILABLE or not ocr_engine or not ocr_engine.is_available():
        print("⚠️ RapidOCR引擎不可用")
        return None
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 智能OCR识别被停止")
        return None
    
    try:
        # 将PIL图像转换为numpy数组
        if hasattr(image, 'save'):  # PIL Image
            img_array = np.array(image)
        else:
            img_array = image
        
        # 朋友圈用户名的颜色 #576b95 转换为RGB
        target_color_rgb = (87, 107, 149)  # #576b95
        tolerance = 40  # 增加颜色容差
        
        print(f"\n🎨 使用颜色过滤OCR识别朋友圈用户名 (目标颜色: RGB{target_color_rgb}, 容差: {tolerance})")
        
        # 使用颜色过滤进行OCR识别
        result = color_targeted_ocr_recognition(image, target_name, target_color_rgb, tolerance, stop_flag_func)
        
        if result:
            print(f"✅ 找到目标用户名: '{target_name}' 在位置 {result}")
            return result
        else:
            print(f"❌ 未找到目标用户名: '{target_name}'")
            
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 智能OCR识别被停止")
                return None
            
            # 如果颜色过滤失败，尝试使用普通OCR识别并打印蓝色文字
            print("🔍 颜色过滤未找到目标，尝试普通OCR识别...")
            normal_result = ocr_engine.recognize_text(img_array)
            
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 智能OCR识别被停止")
                return None
            
            if normal_result and len(normal_result) > 0:
                print(f"\n📋 朋友圈OCR识别到的蓝色文字 (共{len(normal_result)}条):")
                print("=" * 60)
                
                target_found = False
                target_position = None
                blue_text_count = 0
                
                for i, detection in enumerate(normal_result):
                    # 检查停止标志
                    if stop_flag_func and stop_flag_func():
                        print("⏹️ 智能OCR识别被停止")
                        return None
                        
                    if len(detection) >= 3:
                        bbox = detection[0]
                        text = detection[1]
                        confidence = detection[2]
                        
                        # 计算文字位置
                        try:
                            center_x = int(sum([point[0] for point in bbox]) / 4)
                            center_y = int(sum([point[1] for point in bbox]) / 4)
                            position_str = f"({center_x}, {center_y})"
                        except:
                            position_str = "位置计算失败"
                        
                        # 检查文字颜色是否接近蓝色（简单的启发式判断）
                        # 这里我们假设短文字且置信度较高的可能是用户名
                        if len(text.strip()) <= 20 and confidence > 0.8:
                            blue_text_count += 1
                            print(f"{blue_text_count:2d}. 可能的用户名: '{text}' | 置信度: {confidence:.3f} | 位置: {position_str}")
                            
                            # 检查是否找到目标文字
                            if target_name in text and not target_found:
                                target_found = True
                                try:
                                    target_position = (center_x, center_y)
                                    print(f"    ✅ 找到目标用户名: '{target_name}' 在位置 {target_position}")
                                except:
                                    print(f"    ✅ 找到目标用户名: '{target_name}' 但位置计算失败")
                
                print("=" * 60)
                
                if target_found and target_position:
                    print(f"🎯 目标用户名 '{target_name}' 定位成功: {target_position}")
                    return target_position
                else:
                    print(f"❌ 在可能的用户名中未找到目标: '{target_name}'")
                    return None
            else:
                print("📋 普通OCR识别结果也为空")
                return None
        
    except Exception as e:
        print(f"❌ 智能OCR识别失败: {e}")
        return None

# 已删除enhanced_ocr_with_umi函数，只使用RapidOCR进行识别

# ==================== 功能1：搜索联系人 ====================



def get_wechat_window_screenshot():
    """获取微信窗口的截图"""
    try:
        # 使用统一的窗口查找函数
        wechat_windows = find_wechat_main_window()
        if not wechat_windows:
            print("❌ 未找到微信窗口")
            return None, None
        
        hwnd, window_title = wechat_windows[0]
        print(f"✅ 找到微信窗口: {window_title}")
        
        # 确保窗口被正确激活和恢复
        try:
            # 先恢复窗口（如果被最小化）
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.5)
            
            # 设置为前台窗口
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            
            # 再次检查窗口状态，如果太小则最大化
            rect = win32gui.GetWindowRect(hwnd)
            x, y, right, bottom = rect
            width = right - x
            height = bottom - y
            
            # 如果窗口太小（可能是最小化状态），尝试最大化
            if width < 400 or height < 300:
                print(f"⚠️ 窗口尺寸过小 ({width}x{height})，尝试最大化...")
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                time.sleep(1)
                
                # 重新获取窗口位置和大小
                rect = win32gui.GetWindowRect(hwnd)
                x, y, right, bottom = rect
                width = right - x
                height = bottom - y
            
        except Exception as e:
            print(f"⚠️ 窗口激活过程中出现问题: {e}")
        
        print(f"📐 微信窗口位置: ({x}, {y}) 尺寸: {width}x{height}")
        
        # 截取微信窗口
        window_screenshot = pyautogui.screenshot(region=(x, y, width, height))
        
        return window_screenshot, (x, y, width, height)
        
    except Exception as e:
        print(f"❌ 获取微信窗口截图失败: {e}")
        return None, None

def find_contact_in_search_results(search_term):
    """使用OCR识别搜索结果，查找"联系人"标识并定位联系人"""
    try:
        # 获取微信窗口截图
        window_screenshot, window_rect = get_wechat_window_screenshot()
        window_screenshot_used = False  # 标记是否使用了窗口截图
        
        if window_screenshot is None:
            print("❌ 无法获取微信窗口截图，使用全屏截图作为备用方案")
            # 备用方案：使用全屏截图
            full_screenshot = pyautogui.screenshot()
            screen_width, screen_height = pyautogui.size()
            search_results_region = (
                20,  # 左边界：向右移动20像素
                int(screen_height * 0.15) - 10,  # 上边界：向上移动10像素
                int(screen_width * 0.4) - 20,    # 宽度：减少20像素
                int(screen_height * 0.7)    # 高度：屏幕高度的70%
            )
            screenshot = full_screenshot.crop(search_results_region)
            window_offset_x, window_offset_y = 0, 0
            window_screenshot_used = False
        else:
            # 使用微信窗口截图
            window_x, window_y, window_width, window_height = window_rect
            window_screenshot_used = True
            
            # 计算搜索结果区域（相对于微信窗口）
            # 微信搜索结果通常在窗口的左侧部分
            search_results_region = (
                0,  # 左边界：从窗口左边开始
                int(window_height * 0.1) - 10,  # 上边界：窗口高度的10% - 10像素（向上调整）
                int(window_width * 0.45),   # 宽度：窗口宽度的45%（搜索结果区域）
                int(window_height * 0.8) + 10    # 高度：窗口高度的80% + 10像素（补偿向上移动）
            )
            
            # 裁剪搜索结果区域
            screenshot = window_screenshot.crop(search_results_region)
            window_offset_x, window_offset_y = window_x, window_y
            
            print(f"📐 搜索结果区域（相对于微信窗口）: 左上角({search_results_region[0]}, {search_results_region[1]}) 尺寸({search_results_region[2]}x{search_results_region[3]})")
        
        # 保存搜索结果截图用于调试
        try:
            # 调试代码已移除
            print(f"📐 截图区域: 左上角({search_results_region[0]}, {search_results_region[1]}) 尺寸({search_results_region[2]}x{search_results_region[3]})")
        except:
            pass
        
        # 使用RapidOCR进行文字识别
        if RAPID_OCR_AVAILABLE and ocr_engine:
            print("🔍 使用RapidOCR识别搜索结果...")
            
            # 将PIL图像转换为numpy数组
            img_array = np.array(screenshot)
            
            # 使用OCR识别文字
            result = ocr_engine.recognize_text(img_array)
            
            if result and len(result) > 0:
                # 首先进行预检查，确认是否有搜索结果
                search_indicators = ["联系人", "搜索网络结果", "聊天记录", "文件", "公众号", "小程序"]
                found_indicators = []
                
                for line in result:
                    if len(line) >= 2:
                        text = line[1]
                        for indicator in search_indicators:
                            if indicator in text and indicator not in found_indicators:
                                found_indicators.append(indicator)
                
                if not found_indicators:
                    print("⚠️ 预检查未发现搜索结果指示器")
                    print("🔍 识别到的所有文字:")
                    for line in result[:10]:  # 只显示前10行
                        if len(line) >= 2:
                            text = line[1]
                            print(f"   - {text}")
                    print("❌ 没有识别到有效的搜索结果，停止搜索操作")
                    return False
                
                print(f"✅ 预检查发现搜索结果指示器: {', '.join(found_indicators)}")
                
                contact_section_found = False
                contact_y_position = None
                target_contact_position = None
                
                # 遍历OCR结果，查找"联系人"标识
                for line in result:
                    if len(line) >= 3:
                        bbox = line[0]  # 边界框坐标
                        text = line[1]  # 识别的文字
                        confidence = line[2]  # 置信度
                        
                        # 查找"联系人"标识
                        if "联系人" in text:
                            print(f"✅ 找到联系人标识: {text}")
                            contact_section_found = True
                            # 获取"联系人"标识的Y坐标
                            contact_y_position = bbox[0][1]  # 左上角Y坐标
                            continue
                        
                        # 如果已经找到"联系人"标识，查找目标联系人名称
                        if contact_section_found and search_term in text:
                            print(f"✅ 在联系人区域找到目标: {text}")
                            # 获取联系人的位置坐标
                            try:
                                if len(bbox) >= 3 and len(bbox[0]) >= 2 and len(bbox[2]) >= 2:
                                    # 计算相对于截图区域的中心点
                                    relative_center_x = (bbox[0][0] + bbox[2][0]) // 2
                                    relative_center_y = (bbox[0][1] + bbox[2][1]) // 2
                                    
                                    # 如果使用的是窗口截图，坐标需要转换为窗口坐标
                                    if window_screenshot_used:
                                        # 窗口截图中的坐标需要加上搜索结果区域在窗口中的偏移
                                        window_center_x = search_results_region[0] + relative_center_x
                                        window_center_y = search_results_region[1] + relative_center_y
                                        
                                        # 再转换为屏幕绝对坐标
                                        center_x = window_rect[0] + window_center_x
                                        center_y = window_rect[1] + window_center_y
                                    else:
                                        # 屏幕截图，直接加上区域偏移
                                        center_x = search_results_region[0] + relative_center_x
                                        center_y = search_results_region[1] + relative_center_y
                                    
                                    target_contact_position = (center_x, center_y)
                                    
                                    # 点击找到的联系人
                                    print(f"🎯 点击联系人位置: ({center_x}, {center_y})")
                                    pyautogui.click(center_x, center_y)
                                    time.sleep(1.5)
                                    return True
                                else:
                                    print(f"⚠️ 边界框格式异常: {bbox}")
                                    continue
                            except (IndexError, TypeError, ZeroDivisionError) as e:
                                print(f"⚠️ 计算联系人位置失败: {e}")
                                continue
                
                # 如果找到了"联系人"标识但没有找到具体的联系人名称
                if contact_section_found and not target_contact_position:
                    print("⚠️ 找到联系人区域，但未找到具体联系人，尝试点击第一个联系人结果")
                    # 查找"联系人"标识下方的第一个结果
                    for line in result:
                        if len(line) >= 3:
                            bbox = line[0]
                            text = line[1]
                            confidence = line[2]
                            
                            # 如果这个文字在"联系人"标识下方，且不是"联系人"本身
                            if (contact_y_position and bbox[0][1] > contact_y_position and 
                                "联系人" not in text and len(text.strip()) > 0):
                                try:
                                    if len(bbox) >= 3 and len(bbox[0]) >= 2 and len(bbox[2]) >= 2:
                                        # 计算相对于截图区域的中心点
                                        relative_center_x = (bbox[0][0] + bbox[2][0]) // 2
                                        relative_center_y = (bbox[0][1] + bbox[2][1]) // 2
                                        
                                        # 如果使用的是窗口截图，坐标需要转换为窗口坐标
                                        if window_screenshot_used:
                                            # 窗口截图中的坐标需要加上搜索结果区域在窗口中的偏移
                                            window_center_x = search_results_region[0] + relative_center_x
                                            window_center_y = search_results_region[1] + relative_center_y
                                            
                                            # 再转换为屏幕绝对坐标
                                            center_x = window_rect[0] + window_center_x
                                            center_y = window_rect[1] + window_center_y
                                        else:
                                            # 屏幕截图，直接加上区域偏移
                                            center_x = search_results_region[0] + relative_center_x
                                            center_y = search_results_region[1] + relative_center_y
                                        
                                        print(f"🎯 点击第一个联系人结果: {text} 位置: ({center_x}, {center_y})")
                                        pyautogui.click(center_x, center_y)
                                        time.sleep(1.5)
                                        return True
                                    else:
                                        print(f"⚠️ 边界框格式异常: {bbox}")
                                        continue
                                except (IndexError, TypeError, ZeroDivisionError) as e:
                                    print(f"⚠️ 计算第一个联系人位置失败: {e}")
                                    continue
                
                if not contact_section_found:
                    print("⚠️ 未找到'联系人'标识，可能没有联系人搜索结果")
                    # 打印所有识别到的文字，帮助调试
                    print("🔍 识别到的所有文字:")
                    for line in result:
                        if len(line) >= 3:
                            text = line[1]
                            confidence = line[2]
                            print(f"   - {text} (置信度: {confidence:.2f})")
                    print("❌ 没有识别到有效的联系人搜索结果，停止搜索操作")
                    return False
            else:
                print("❌ OCR识别结果为空，没有识别到任何搜索结果")
                print("❌ 没有识别到有效的搜索结果，停止搜索操作")
                return False
        
        # 备用方案：如果RapidOCR不可用
        else:
            print("⚠️ RapidOCR不可用，无法智能识别搜索结果")
            print("❌ 停止搜索操作")
            return False
            
    except Exception as e:
        print(f"❌ OCR识别搜索结果失败: {e}")
        return False

def find_group_in_search_results(search_term):
    """使用OCR识别搜索结果，查找"群聊"标识并定位群聊"""
    try:
        # 获取微信窗口截图
        window_screenshot, window_rect = get_wechat_window_screenshot()
        window_screenshot_used = False  # 标记是否使用了窗口截图
        
        if window_screenshot is None:
            print("❌ 无法获取微信窗口截图，使用全屏截图作为备用方案")
            # 备用方案：使用全屏截图
            full_screenshot = pyautogui.screenshot()
            screen_width, screen_height = pyautogui.size()
            search_results_region = (
                20,  # 左边界：向右移动20像素
                int(screen_height * 0.15) - 10,  # 上边界：向上移动10像素
                int(screen_width * 0.4) - 20,    # 宽度：减少20像素
                int(screen_height * 0.7)    # 高度：屏幕高度的70%
            )
            screenshot = full_screenshot.crop(search_results_region)
            window_offset_x, window_offset_y = 0, 0
            window_screenshot_used = False
        else:
            # 使用微信窗口截图
            window_x, window_y, window_width, window_height = window_rect
            window_screenshot_used = True
            
            # 计算搜索结果区域（相对于微信窗口）
            # 微信搜索结果通常在窗口的左侧部分
            search_results_region = (
                0,  # 左边界：从窗口左边开始
                int(window_height * 0.1) - 10,  # 上边界：窗口高度的10% - 10像素（向上调整）
                int(window_width * 0.45),   # 宽度：窗口宽度的45%（搜索结果区域）
                int(window_height * 0.8) + 10    # 高度：窗口高度的80% + 10像素（补偿向上移动）
            )
            
            # 裁剪搜索结果区域
            screenshot = window_screenshot.crop(search_results_region)
            window_offset_x, window_offset_y = window_x, window_y
            
            print(f"📐 搜索结果区域（相对于微信窗口）: 左上角({search_results_region[0]}, {search_results_region[1]}) 尺寸({search_results_region[2]}x{search_results_region[3]})")
        
        # 保存搜索结果截图用于调试
        try:
            # 调试代码已移除
            print(f"📐 截图区域: 左上角({search_results_region[0]}, {search_results_region[1]}) 尺寸({search_results_region[2]}x{search_results_region[3]})")
        except:
            pass
        
        # 使用RapidOCR进行文字识别
        if RAPID_OCR_AVAILABLE and ocr_engine:
            print("🔍 使用RapidOCR识别群聊搜索结果...")
            
            # 将PIL图像转换为numpy数组
            img_array = np.array(screenshot)
            
            # 使用OCR识别文字
            result = ocr_engine.recognize_text(img_array)
            
            if result and len(result) > 0:
                # 首先进行预检查，确认是否有搜索结果
                search_indicators = ["群聊", "联系人", "搜索网络结果", "聊天记录", "文件", "公众号", "小程序"]
                found_indicators = []
                
                for line in result:
                    if len(line) >= 2:
                        text = line[1]
                        for indicator in search_indicators:
                            if indicator in text and indicator not in found_indicators:
                                found_indicators.append(indicator)
                
                if not found_indicators:
                    print("⚠️ 预检查未发现搜索结果指示器")
                    print("🔍 识别到的所有文字:")
                    for line in result[:10]:  # 只显示前10行
                        if len(line) >= 2:
                            text = line[1]
                            print(f"   - {text}")
                    print("❌ 没有识别到有效的搜索结果，停止搜索操作")
                    return False
                
                print(f"✅ 预检查发现搜索结果指示器: {', '.join(found_indicators)}")
                
                group_section_found = False
                group_y_position = None
                target_group_position = None
                
                # 遍历OCR结果，查找"群聊"标识
                for line in result:
                    if len(line) >= 3:
                        bbox = line[0]  # 边界框坐标
                        text = line[1]  # 识别的文字
                        confidence = line[2]  # 置信度
                        
                        # 查找"群聊"标识
                        if "群聊" in text:
                            print(f"✅ 找到群聊标识: {text}")
                            group_section_found = True
                            # 获取"群聊"标识的Y坐标
                            group_y_position = bbox[0][1]  # 左上角Y坐标
                            continue
                        
                        # 如果已经找到"群聊"标识，查找目标群聊名称
                        if group_section_found and search_term in text:
                            print(f"✅ 在群聊区域找到目标: {text}")
                            # 获取群聊的位置坐标
                            try:
                                if len(bbox) >= 3 and len(bbox[0]) >= 2 and len(bbox[2]) >= 2:
                                    # 计算相对于截图区域的中心点
                                    relative_center_x = (bbox[0][0] + bbox[2][0]) // 2
                                    relative_center_y = (bbox[0][1] + bbox[2][1]) // 2
                                    
                                    # 如果使用的是窗口截图，坐标需要转换为窗口坐标
                                    if window_screenshot_used:
                                        # 窗口截图中的坐标需要加上搜索结果区域在窗口中的偏移
                                        window_center_x = search_results_region[0] + relative_center_x
                                        window_center_y = search_results_region[1] + relative_center_y
                                        
                                        # 再转换为屏幕绝对坐标
                                        center_x = window_rect[0] + window_center_x
                                        center_y = window_rect[1] + window_center_y
                                    else:
                                        # 屏幕截图，直接加上区域偏移
                                        center_x = search_results_region[0] + relative_center_x
                                        center_y = search_results_region[1] + relative_center_y
                                    
                                    target_group_position = (center_x, center_y)
                                    
                                    # 点击找到的群聊
                                    print(f"🎯 点击群聊位置: ({center_x}, {center_y})")
                                    pyautogui.click(center_x, center_y)
                                    time.sleep(1.5)
                                    return True
                                else:
                                    print(f"⚠️ 边界框格式异常: {bbox}")
                                    continue
                            except (IndexError, TypeError, ZeroDivisionError) as e:
                                print(f"⚠️ 计算群聊位置失败: {e}")
                                continue
                
                # 如果找到了"群聊"标识但没有找到具体的群聊名称
                if group_section_found and not target_group_position:
                    print("⚠️ 找到群聊区域，但未找到具体群聊，尝试点击第一个群聊结果")
                    # 查找"群聊"标识下方的第一个结果
                    for line in result:
                        if len(line) >= 3:
                            bbox = line[0]
                            text = line[1]
                            confidence = line[2]
                            
                            # 如果这个文字在"群聊"标识下方，且不是"群聊"本身
                            if (group_y_position and bbox[0][1] > group_y_position and 
                                "群聊" not in text and len(text.strip()) > 0):
                                try:
                                    if len(bbox) >= 3 and len(bbox[0]) >= 2 and len(bbox[2]) >= 2:
                                        # 计算相对于截图区域的中心点
                                        relative_center_x = (bbox[0][0] + bbox[2][0]) // 2
                                        relative_center_y = (bbox[0][1] + bbox[2][1]) // 2
                                        
                                        # 如果使用的是窗口截图，坐标需要转换为窗口坐标
                                        if window_screenshot_used:
                                            # 窗口截图中的坐标需要加上搜索结果区域在窗口中的偏移
                                            window_center_x = search_results_region[0] + relative_center_x
                                            window_center_y = search_results_region[1] + relative_center_y
                                            
                                            # 再转换为屏幕绝对坐标
                                            center_x = window_rect[0] + window_center_x
                                            center_y = window_rect[1] + window_center_y
                                        else:
                                            # 屏幕截图，直接加上区域偏移
                                            center_x = search_results_region[0] + relative_center_x
                                            center_y = search_results_region[1] + relative_center_y
                                        
                                        print(f"🎯 点击第一个群聊结果: {text} 位置: ({center_x}, {center_y})")
                                        pyautogui.click(center_x, center_y)
                                        time.sleep(1.5)
                                        return True
                                    else:
                                        print(f"⚠️ 边界框格式异常: {bbox}")
                                        continue
                                except (IndexError, TypeError, ZeroDivisionError) as e:
                                    print(f"⚠️ 计算第一个群聊位置失败: {e}")
                                    continue
                
                if not group_section_found:
                    print("⚠️ 未找到'群聊'标识，可能没有群聊搜索结果")
                    # 打印所有识别到的文字，帮助调试
                    print("🔍 识别到的所有文字:")
                    for line in result:
                        if len(line) >= 3:
                            text = line[1]
                            confidence = line[2]
                            print(f"   - {text} (置信度: {confidence:.2f})")
                    print("❌ 没有识别到有效的群聊搜索结果，停止搜索操作")
                    return False
            else:
                print("❌ OCR识别结果为空，没有识别到任何搜索结果")
                print("❌ 没有识别到有效的搜索结果，停止搜索操作")
                return False
        
        # 备用方案：如果RapidOCR不可用
        else:
            print("⚠️ RapidOCR不可用，无法智能识别搜索结果")
            print("❌ 停止搜索操作")
            return False
            
    except Exception as e:
        print(f"❌ OCR识别群聊搜索结果失败: {e}")
        return False

def search_group(search_term=None, ensure_active=True, message=None, stop_flag_func=None):
    """搜索群聊功能 - 在微信主界面搜索群聊"""
    print("🔍 开始搜索群聊...")
    
    try:
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索群聊操作被停止")
            return False
            
        # GUI模式下必须提供搜索内容
        if search_term is None or not search_term:
            print("❌ 未提供搜索内容")
            return False
        
        print(f"📝 准备搜索群聊: {search_term}")
        
        # 根据参数决定是否激活微信窗口
        if ensure_active and not ensure_wechat_is_active():
            return False
            
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索群聊操作被停止")
            return False
        
        # 再次确保微信窗口处于活动状态
        print("🔄 再次确认微信窗口激活状态...")
        pyautogui.click(pyautogui.size().width // 2, pyautogui.size().height // 2)  # 点击屏幕中央确保焦点
        time.sleep(0.5)
        
        # 使用快捷键打开搜索框
        print("⌨️ 在微信界面使用快捷键 Ctrl+F 打开搜索...")
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(2)  # 等待搜索框出现
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索联系人操作被停止")
            return False
        
        # 使用剪贴板方式输入中文（解决中文输入问题）
        print(f"📝 在微信搜索框中输入: {search_term}")
        input_success = False
        
        try:
            import pyperclip
            # 将搜索内容复制到剪贴板
            pyperclip.copy(search_term)
            time.sleep(0.3)
            
            # 使用Ctrl+V粘贴
            pyautogui.hotkey('ctrl', 'v')
            print("✅ 使用剪贴板成功输入中文")
            time.sleep(1)
            input_success = True
            
        except ImportError:
            print("⚠️ pyperclip模块未安装，尝试直接输入...")
            # 备用方案：检查是否包含中文字符
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in search_term)
            
            if has_chinese:
                print("🔤 检测到中文字符，建议安装pyperclip模块以支持中文输入")
                print("💡 安装命令: pip install pyperclip")
                # 尝试逐字符输入，但可能不支持中文
                for char in search_term:
                    if '\u4e00' <= char <= '\u9fff':  # 中文字符
                        print(f"⚠️ 跳过中文字符: {char}")
                        continue
                    pyautogui.typewrite(char)
                    time.sleep(0.15)
            else:
                # 纯英文或数字，直接输入
                for char in search_term:
                    pyautogui.typewrite(char)
                    time.sleep(0.15)
            
            time.sleep(1)
        
        except Exception as e:
            print(f"⚠️ 剪贴板输入失败，尝试直接输入: {e}")
            # 备用方案：直接输入
            for char in search_term:
                pyautogui.typewrite(char)
                time.sleep(0.15)
            time.sleep(1)
        
        # 如果使用了剪贴板输入中文，进行OCR验证
        if input_success and any('\u4e00' <= char <= '\u9fff' for char in search_term):
            if not verify_search_input_with_ocr(search_term, stop_flag_func):
                return False
        
        # 微信会自动显示搜索结果，无需按回车
        print("🔍 等待微信自动显示搜索结果...")
        time.sleep(1)  # 等待搜索结果自动显示
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索群聊操作被停止")
            return False
        
        # 使用OCR识别搜索结果，查找"群聊"标识（包含预检查功能）
        print("🔍 使用OCR识别搜索结果，查找群聊...")
        group_found = find_group_in_search_results(search_term)
        
        if group_found:
            print(f"✅ 在微信中搜索群聊 '{search_term}' 完成")
            print("💡 程序将自动进入群聊界面并发送自定义消息")
            
            # 直接进入发送消息流程
            print("\n" + "="*50)
            print("🎯 搜索完成！准备自动进入群聊界面...")
            print("="*50)
            
            # 直接调用发送消息功能
            return send_message_to_contact(search_term, message, stop_flag_func)  # 复用联系人的发送消息功能
        else:
            print(f"❌ 未找到群聊 '{search_term}'，请检查群聊名称是否正确")
            return False
        
    except Exception as e:
        print(f"❌ 搜索群聊失败: {e}")
        return False

def search_contact(search_term=None, ensure_active=True, message=None, stop_flag_func=None):
    """搜索联系人功能 - 在微信主界面搜索"""
    print("🔍 开始搜索联系人...")
    
    try:
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索联系人操作被停止")
            return False
            
        # GUI模式下必须提供搜索内容
        if search_term is None or not search_term:
            print("❌ 未提供搜索内容")
            return False
        
        print(f"📝 准备搜索: {search_term}")
        
        # 根据参数决定是否激活微信窗口
        if ensure_active and not ensure_wechat_is_active():
            return False
            
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索联系人操作被停止")
            return False
        
        # 使用快捷键打开搜索框
        print("⌨️ 在微信界面使用快捷键 Ctrl+F 打开搜索...")
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(2)  # 等待搜索框出现
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索群聊操作被停止")
            return False
        
        # 使用剪贴板方式输入中文（解决中文输入问题）
        print(f"📝 在微信搜索框中输入: {search_term}")
        input_success = False
        
        try:
            import pyperclip
            # 将搜索内容复制到剪贴板
            pyperclip.copy(search_term)
            time.sleep(0.3)
            
            # 使用Ctrl+V粘贴
            pyautogui.hotkey('ctrl', 'v')
            print("✅ 使用剪贴板成功输入中文")
            time.sleep(1)
            input_success = True
            
        except ImportError:
            print("⚠️ pyperclip模块未安装，尝试直接输入...")
            # 备用方案：检查是否包含中文字符
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in search_term)
            
            if has_chinese:
                print("🔤 检测到中文字符，建议安装pyperclip模块以支持中文输入")
                print("💡 安装命令: pip install pyperclip")
                # 尝试逐字符输入，但可能不支持中文
                for char in search_term:
                    if '\u4e00' <= char <= '\u9fff':  # 中文字符
                        print(f"⚠️ 跳过中文字符: {char}")
                        continue
                    pyautogui.typewrite(char)
                    time.sleep(0.15)
            else:
                # 纯英文或数字，直接输入
                for char in search_term:
                    pyautogui.typewrite(char)
                    time.sleep(0.15)
            
            time.sleep(1)
        
        except Exception as e:
            print(f"⚠️ 剪贴板输入失败，尝试直接输入: {e}")
            # 备用方案：直接输入
            for char in search_term:
                pyautogui.typewrite(char)
                time.sleep(0.15)
            time.sleep(1)
        
        # 如果使用了剪贴板输入中文，进行OCR验证
        if input_success and any('\u4e00' <= char <= '\u9fff' for char in search_term):
            if not verify_search_input_with_ocr(search_term, stop_flag_func):
                return False
        
        # 微信会自动显示搜索结果，无需按回车
        print("🔍 等待微信自动显示搜索结果...")
        time.sleep(1)  # 等待搜索结果自动显示
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 搜索联系人操作被停止")
            return False
        
        # 使用OCR识别搜索结果，查找"联系人"标识（包含预检查功能）
        print("🔍 使用OCR识别搜索结果，查找联系人...")
        contact_found = find_contact_in_search_results(search_term)
        
        if contact_found:
            print(f"✅ 在微信中搜索联系人 '{search_term}' 完成")
            print("💡 程序将自动进入聊天界面并发送自定义消息")
            
            # 直接进入发送消息流程
            print("\n" + "="*50)
            print("🎯 搜索完成！准备自动进入聊天界面...")
            print("="*50)
            
            # 直接调用发送消息功能
            return send_message_to_contact(search_term, message, stop_flag_func)
        else:
            print(f"❌ 未找到联系人 '{search_term}'，请检查联系人名称是否正确")
            return False
        
    except Exception as e:
        print(f"❌ 搜索联系人失败: {e}")
        return False

def send_message_to_contact(contact_name, message=None, stop_flag_func=None):
    """点击第一个搜索结果并发送消息"""
    print(f"💬 准备向 '{contact_name}' 发送消息...")
    
    try:
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 发送消息操作被停止")
            return False
            
        # 等待搜索结果显示
        time.sleep(1.5)
        
        # 检查微信是否在前台，如果不在才激活
        if not is_wechat_in_foreground():
            print("🔄 微信不在前台，正在激活...")
            if not ensure_wechat_is_active():
                return False
        else:
            print("✅ 微信已在前台，无需重复激活")
        
        
        print("✅ 已自动进入聊天界面")
        
        # 再次确保微信窗口处于最前面（聊天界面可能是新窗口）
        #activate_wechat_window()
        
        # GUI模式下必须提供消息内容
        if message is None or not message:
            print("❌ 未提供消息内容")
            return False
        
        print(f"📝 准备发送消息: {message}")
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 发送消息操作被停止")
            return False
        
        # 获取微信窗口位置，在窗口内点击输入框
        wechat_windows = find_wechat_main_window()
        if wechat_windows:
            # 获取第一个微信窗口的句柄
            wechat_hwnd, window_title = wechat_windows[0]
            
            # 获取微信窗口的位置和大小
            rect = win32gui.GetWindowRect(wechat_hwnd)
            window_left, window_top, window_right, window_bottom = rect
            window_width = window_right - window_left
            window_height = window_bottom - window_top
            
            # 在微信窗口内的输入框位置点击（窗口下方中央）
            input_box_x = window_left + window_width // 2
            input_box_y = window_top + int(window_height * 0.88)
            pyautogui.click(input_box_x, input_box_y)
            time.sleep(0.5)
        else:
            # 备用方案：使用屏幕位置
            screen_width, screen_height = pyautogui.size()
            input_box_x = screen_width // 2
            input_box_y = int(screen_height * 0.88)
            pyautogui.click(input_box_x, input_box_y)
            time.sleep(0.5)
        
        # 清空输入框（防止有残留内容）
        pyautogui.hotkey('ctrl', 'a')  # 全选
        time.sleep(0.2)
        pyautogui.press('delete')  # 删除
        time.sleep(0.3)
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 发送消息操作被停止")
            return False
            
        # 发送消息（使用剪贴板方式支持中文）
        print("📝 输入消息内容...")
        
        time.sleep(0.3)
        message_input_success = False
        
        try:
            import pyperclip
            # 将消息复制到剪贴板
            pyperclip.copy(message)
            time.sleep(0.3)
            
            # 使用Ctrl+V粘贴
            pyautogui.hotkey('ctrl', 'v')
            print("✅ 使用剪贴板成功输入消息")
            time.sleep(1)
            message_input_success = True
            
        except ImportError:
            print("⚠️ pyperclip模块未安装，尝试直接输入...")
            # 备用方案：逐字符输入
            for char in message:
                pyautogui.typewrite(char)
                time.sleep(0.1)
            time.sleep(0.8)
        
        # 消息输入完成，等待一下确保输入生效
        time.sleep(0.5)
        
        # 发送消息前最后确认微信在前台
        if not is_wechat_in_foreground():
            print("🔄 发送前确认：微信不在前台，正在激活...")
            ensure_wechat_is_active()
        # 如果微信在前台，直接发送（无需额外提示）
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 发送消息操作被停止")
            return False
            
        # 按回车发送消息
        print("📤 发送消息...")
        pyautogui.press('enter')
        time.sleep(1.5)
        
        print(f"✅ 消息已成功发送给 '{contact_name}': {message}")
        print("💡 提示：消息已发送，聊天界面保持打开状态")
        return True
        
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        return False



# ==================== 功能2：朋友圈功能 ====================

def find_and_click_pengyouquan(stop_flag_func=None):
    """查找并点击朋友圈图标"""
    print("🔍 查找朋友圈图标...")
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 查找朋友圈操作被停止")
        return False
    
    try:
        # 尝试使用图像识别找到朋友圈图标
        pengyouquan_icon = pyautogui.locateOnScreen('assets/pengyouquan.png', confidence=0.8)
        if pengyouquan_icon:
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 查找朋友圈操作被停止")
                return False
            pyautogui.click(pengyouquan_icon)
            print("✅ 通过图像识别找到并点击了朋友圈图标")
            return True
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 查找朋友圈操作被停止")
            return False
        
        # 备用方案：使用RapidOCR查找"朋友圈"文字
        if RAPID_OCR_AVAILABLE and ocr_engine:
            screenshot = pyautogui.screenshot()
            result = smart_ocr_recognition(screenshot, "朋友圈", stop_flag_func)
            if result:
                # 检查停止标志
                if stop_flag_func and stop_flag_func():
                    print("⏹️ 查找朋友圈操作被停止")
                    return False
                pyautogui.click(result[0], result[1])
                print("✅ 通过RapidOCR找到并点击了朋友圈")
                return True
        
        print("❌ 未找到朋友圈图标")
        return False
        
    except Exception as e:
        print(f"❌ 查找朋友圈图标失败: {e}")
        return False

def check_and_perform_dianzan(dianzan_position, enable_comment=False, comment_text="", stop_flag_func=None):
    """检测点赞状态并执行点赞操作 - 返回操作结果"""
    print("🔍 检测点赞状态...")
    
    try:
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 收到停止信号，中断点赞操作")
            return False
            
        # 点击点赞按钮弹出界面
        pyautogui.click(dianzan_position[0], dianzan_position[1])
        print("✅ 已点击点赞按钮，等待界面弹出...")
        time.sleep(1.5)  # 等待界面弹出
        
        # 检测已点赞状态 (yizan.png)
        print("🔍 正在识别已点赞状态图标 (yizan.png)...")
        try:
            yizan_icon = pyautogui.locateOnScreen('assets/yizan.png', confidence=0.8)
            if yizan_icon:
                print(f"✅ 检测到已点赞状态，位置: {yizan_icon}，无需重复点赞")
                
                # 即使已点赞，如果启用评论功能，仍然执行评论操作
                if enable_comment and comment_text.strip():
                    print("💬 检测到已点赞状态，但仍需执行评论操作...")
                    success = perform_comment_action(comment_text, dianzan_position, stop_flag_func)
                    if success:
                        print("✅ 评论操作完成")
                    else:
                        print("⚠️ 评论操作失败")
                

                return True  # 已点赞，操作成功
            else:
                print("❌ 未找到已点赞状态图标")
        except Exception as e:
            print(f"❌ 识别已点赞状态时出错: {e}")
        
        # 检测未点赞状态 (nozan.png)
        print("🔍 正在识别未点赞状态图标 (nozan.png)...")
        try:
            nozan_icon = pyautogui.locateOnScreen('assets/nozan.png', confidence=0.8)
            if nozan_icon:
                print(f"✅ 检测到未点赞状态，位置: {nozan_icon}，执行点赞操作")
                # 点击点赞图标进行点赞
                pyautogui.click(nozan_icon)
                time.sleep(1)  # 等待点赞完成
                print("👍 点赞操作完成")
                
                # 如果启用评论功能，尝试点击评论
                if enable_comment and comment_text.strip():
                    print("💬 开始执行评论操作...")
                    success = perform_comment_action(comment_text, dianzan_position, stop_flag_func)
                    if success:
                        print("✅ 评论操作完成")
                    else:
                        print("⚠️ 评论操作失败")
                
                return True  # 点赞成功
            else:
                print("❌ 未找到未点赞状态图标")
        except Exception as e:
            print(f"❌ 识别未点赞状态时出错: {e}")
        
        # 如果都没检测到，尝试通用点赞操作
        print("⚠️ 无法确定点赞状态，尝试通用点赞操作")
        # 在弹出界面中查找可能的点赞按钮
        try:
            # 尝试查找并点击点赞相关的图标
            dianzan_in_popup = pyautogui.locateOnScreen('assets/dianzan.png', confidence=0.7)
            if dianzan_in_popup:
                pyautogui.click(dianzan_in_popup)
                time.sleep(1)
                print("👍 通用点赞操作完成")
                
                # 如果启用评论功能，尝试点击评论
                if enable_comment and comment_text.strip():
                    print("💬 开始执行评论操作...")
                    success = perform_comment_action(comment_text, dianzan_position, stop_flag_func)
                    if success:
                        print("✅ 评论操作完成")
                    else:
                        print("⚠️ 评论操作失败")
                
                return True
        except:
            pass
        

        print("⚠️ 无法执行点赞操作")
        return False
        
    except Exception as e:
        print(f"❌ 检测点赞状态失败: {e}")
        return False

def perform_comment_action(comment_text, dianzan_position=None, stop_flag_func=None):
    """执行评论操作"""
    try:
        print("🔍 开始执行评论操作...")
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 收到停止信号，中断评论操作")
            return False
        
        # 处理多条评论，随机选择一条
        import random
        if ',' in comment_text:
            comment_list = [comment.strip() for comment in comment_text.split(',') if comment.strip()]
            if comment_list:
                selected_comment = random.choice(comment_list)
                print(f"💬 从 {len(comment_list)} 条评论中随机选择: {selected_comment}")
            else:
                print("❌ 评论内容为空")
                return False
        else:
            selected_comment = comment_text.strip()
            print(f"💬 使用评论内容: {selected_comment}")
        
        if not selected_comment:
            print("❌ 评论内容为空")
            return False
        
        # 首先点击点赞按钮重新弹出界面
        if dianzan_position:
            print(f"🔍 点击点赞按钮重新弹出界面，位置: {dianzan_position}")
            try:
                pyautogui.click(dianzan_position[0], dianzan_position[1])
                time.sleep(1.5)  # 等待界面弹出
                print("✅ 已重新弹出点赞界面")
            except Exception as e:
                print(f"❌ 点击点赞按钮时出错: {e}，尝试继续查找评论图标")
        else:
            print("⚠️ 未提供点赞按钮位置，尝试查找点赞图标...")
            try:
                dianzan_icon = pyautogui.locateOnScreen('assets/dianzan.png', confidence=0.8)
                if dianzan_icon:
                    print(f"✅ 找到点赞图标，位置: {dianzan_icon}")
                    pyautogui.click(dianzan_icon)
                    time.sleep(1.5)  # 等待界面弹出
                    print("✅ 已重新弹出点赞界面")
                else:
                    print("❌ 未找到点赞图标，尝试继续查找评论图标")
            except Exception as e:
                print(f"❌ 查找点赞图标时出错: {e}，尝试继续查找评论图标")
        
        # 查找评论图标
        print("🔍 正在查找评论图标 (pinglun.png)...")
        try:
            pinglun_icon = pyautogui.locateOnScreen('assets/pinglun.png', confidence=0.8)
            if pinglun_icon:
                print(f"✅ 找到评论图标，位置: {pinglun_icon}")
                # 点击评论图标
                pyautogui.click(pinglun_icon)
                time.sleep(1.5)  # 等待评论输入框出现
                
                print("💬 开始输入评论内容...")
                print(f"💡 输入内容: {selected_comment}")
                
                # 使用剪贴板方式输入评论内容（支持中文）
                try:
                    import pyperclip
                    # 将评论内容复制到剪贴板
                    pyperclip.copy(selected_comment)
                    time.sleep(0.3)
                    
                    # 使用Ctrl+V粘贴
                    pyautogui.hotkey('ctrl', 'v')
                    print("✅ 使用剪贴板成功输入评论内容")
                    time.sleep(0.8)
                    
                except ImportError:
                    print("⚠️ pyperclip模块未安装，尝试直接输入...")
                    # 备用方案：直接输入（可能不支持中文）
                    pyautogui.typewrite(selected_comment, interval=0.05)
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"⚠️ 剪贴板输入失败，尝试直接输入: {e}")
                    # 备用方案：直接输入
                    pyautogui.typewrite(selected_comment, interval=0.05)
                    time.sleep(0.5)
                
                print("📤 查找发送按钮 (fasong.png)...")
                # 查找并点击发送按钮，尝试不同置信度
                fasong_found = False
                confidence_levels = [0.8, 0.7, 0.6, 0.5]
                
                for confidence in confidence_levels:
                    try:
                        print(f"🔍 尝试置信度 {confidence} 查找发送按钮...")
                        fasong_icon = pyautogui.locateOnScreen('assets/fasong.png', confidence=confidence)
                        if fasong_icon:
                            print(f"✅ 找到发送按钮，位置: {fasong_icon} (置信度: {confidence})")
                            pyautogui.click(fasong_icon)
                            time.sleep(1)  # 等待发送完成
                            print("✅ 评论发送成功")
                            fasong_found = True
                            break
                    except Exception as e:
                        print(f"❌ 置信度 {confidence} 检测出错: {e}")
                        continue
                
                if not fasong_found:
                    print("❌ 所有置信度都未找到发送按钮，尝试使用回车键发送")
                    pyautogui.press('enter')
                    time.sleep(1)
                    print("✅ 评论发送完成（使用回车键）")
                
                return True
            else:
                print("❌ 未找到评论图标")
                return False
        except Exception as e:
            print(f"❌ 查找评论图标时出错: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 评论操作失败: {e}")
        return False

def find_and_click_dianzan(target_name, name_position=None, max_scroll_attempts=3, enable_comment=False, comment_text="", stop_flag_func=None):
    """查找并点击点赞按钮 - 持续滚动查找下方最近的点赞按钮，并检测点赞状态"""
    print("👍 查找点赞按钮...")
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 点赞操作被停止")
        return False
    
    def try_find_dianzan_icon_with_name_position(current_name_position):
        """基于当前用户名位置尝试查找点赞图标的内部函数"""
        if not current_name_position:
            return None
            
        # 使用图像识别找到点赞图标
        dianzan_icons = list(pyautogui.locateAllOnScreen('assets/dianzan.png', confidence=0.8))
        if dianzan_icons:
            # 找到用户名下方最近的点赞按钮
            name_x, name_y = current_name_position
            closest_dianzan = None
            min_distance = float('inf')
            
            for icon in dianzan_icons:
                icon_x = icon.left + icon.width // 2
                icon_y = icon.top + icon.height // 2
                
                # 只考虑在用户名下方的点赞按钮
                if icon_y > name_y:
                    distance = abs(icon_x - name_x) + (icon_y - name_y)
                    if distance < min_distance:
                        min_distance = distance
                        closest_dianzan = (icon_x, icon_y)
            
            if closest_dianzan:
                return closest_dianzan
        
        return None
    
    try:
        # 如果没有提供初始位置，先进行OCR识别
        current_name_position = name_position
        if not current_name_position:
            current_name_position = enhanced_recognition_in_current_view(target_name, stop_flag_func)
            if not current_name_position:
                print(f"❌ 无法识别用户名 '{target_name}' 的位置")
                return False
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 点赞操作被停止")
            return False
            
        # 第一次尝试查找点赞图标
        dianzan_position = try_find_dianzan_icon_with_name_position(current_name_position)
        
        if dianzan_position:
            # 检测点赞状态并执行相应操作
            result = check_and_perform_dianzan(dianzan_position, enable_comment, comment_text, stop_flag_func)
            if result:
                print("✅ 找到并完成了用户名下方的点赞操作")
                return True
            else:
                print("❌ 点赞操作失败")
                return False
        
        # 如果没有找到点赞图标，继续下键滚动查找
        print("⚠️ 未找到点赞图标，开始下键滚动查找下方最近的点赞按钮...")
        
        for scroll_attempt in range(max_scroll_attempts):
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 点赞操作被停止")
                return False
                
            print(f"🔄 第 {scroll_attempt + 1}/{max_scroll_attempts} 次滚动查找点赞按钮")
            
            # 按下键滚动
            pyautogui.press('down')
            print("⬇️ 已按下键滚动")
            
            # 等待滚动动画完成
            time.sleep(0.8)
            
            # 重新识别用户名位置
            print(f"🔍 重新识别用户名 '{target_name}' 的位置...")
            current_name_position = enhanced_recognition_in_current_view(target_name, stop_flag_func)
            
            if not current_name_position:
                print(f"⚠️ 第 {scroll_attempt + 1} 次滚动后无法识别用户名位置，继续滚动...")
                continue
            
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 点赞操作被停止")
                return False
                
            # 基于新的用户名位置查找点赞图标
            dianzan_position = try_find_dianzan_icon_with_name_position(current_name_position)
            
            if dianzan_position:
                # 检测点赞状态并执行相应操作
                result = check_and_perform_dianzan(dianzan_position, enable_comment, comment_text, stop_flag_func)
                if result:
                    print(f"✅ 在第 {scroll_attempt + 1} 次滚动后找到并完成了点赞操作")
                    return True
                else:
                    print(f"❌ 在第 {scroll_attempt + 1} 次滚动后点赞操作失败")
                    return False
            else:
                print(f"❌ 第 {scroll_attempt + 1} 次滚动后仍未找到点赞按钮，继续滚动...")
        
        # 如果滚动多次后还是找不到，直接放弃点赞
        print(f"❌ 滚动 {max_scroll_attempts} 次后仍未找到点赞图标，放弃点赞操作")
        return False
        
    except Exception as e:
        print(f"❌ 查找点赞按钮失败: {e}")
        return False

def get_pengyouquan_window_region(stop_flag_func=None):
    """获取朋友圈窗口的区域坐标 - 使用健壮的窗口查找机制
    
    Args:
        stop_flag_func: 停止标志检查函数
    """
    try:
        def find_pengyouquan_window():
            windows = []
            def enum_windows_callback(hwnd, windows):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        # 查找朋友圈窗口
                        if "朋友圈" in window_text:
                            # 验证窗口句柄是否有效
                            if win32gui.IsWindow(hwnd):
                                windows.append((hwnd, window_text))
                except:
                    # 忽略无效窗口
                    pass
                return True
            
            win32gui.EnumWindows(enum_windows_callback, windows)
            return windows
        
        # 尝试多次查找和激活朋友圈窗口
        success = False
        rect = None
        
        for attempt in range(3):  # 最多尝试3次
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 获取朋友圈窗口区域操作被停止")
                return None
                
            print(f"🔄 第 {attempt + 1} 次尝试查找朋友圈窗口...")
            pengyouquan_windows = find_pengyouquan_window()
            
            if pengyouquan_windows:
                hwnd, window_title = pengyouquan_windows[0]
                try:
                    # 验证窗口句柄仍然有效
                    if win32gui.IsWindow(hwnd):
                        # 确保窗口不是最小化状态
                        if win32gui.IsIconic(hwnd):
                            print("⚠️ 朋友圈窗口被最小化，正在恢复...")
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            time.sleep(1)  # 等待窗口恢复
                        
                        # 先尝试显示窗口
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        time.sleep(0.5)
                        
                        # 再尝试设置前台窗口
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(0.5)
                        
                        # 获取窗口区域
                        rect = win32gui.GetWindowRect(hwnd)
                        left, top, right, bottom = rect
                        
                        # 验证坐标是否有效（排除最小化窗口的异常坐标）
                        if left < -10000 or top < -10000 or (right - left) < 100 or (bottom - top) < 100:
                            print(f"⚠️ 检测到异常朋友圈窗口坐标: {rect}")
                            if attempt < 2:  # 不是最后一次尝试
                                time.sleep(1)
                                continue
                            else:
                                return None
                        
                        print(f"✅ 获取朋友圈窗口区域: {rect}")
                        success = True
                        break
                    else:
                        print(f"⚠️ 朋友圈窗口句柄已失效，重试...")
                        time.sleep(0.5)
                        continue
                except Exception as e:
                    print(f"⚠️ 第 {attempt + 1} 次激活朋友圈窗口失败: {e}")
                    if attempt < 2:  # 不是最后一次尝试
                        time.sleep(1)
                        continue
                    else:
                        print("❌ 多次尝试后仍无法激活朋友圈窗口")
                        return None
            else:
                print(f"⚠️ 第 {attempt + 1} 次未找到朋友圈窗口")
                if attempt < 2:
                    time.sleep(1)
                    continue
        
        if success and rect:
            return rect  # (left, top, right, bottom)
        else:
            print("❌ 未能成功获取朋友圈窗口区域")
            return None
            
    except Exception as e:
        print(f"❌ 获取朋友圈窗口区域失败: {e}")
        return None

def check_yesterday_marker(stop_flag_func=None):
    """检查当前视图中是否有灰色的'昨天'文字标记"""
    if not ocr_engine or not ocr_engine.is_available():
        return False
    
    try:
        # 获取朋友圈窗口区域
        pengyouquan_region = get_pengyouquan_window_region(stop_flag_func)
        
        if pengyouquan_region:
            # 只截取朋友圈窗口区域
            left, top, right, bottom = pengyouquan_region
            width, height = right - left, bottom - top
            
            # 确保坐标和尺寸都是正数
            if width > 0 and height > 0 and left >= 0 and top >= 0:
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
            else:
                screenshot = pyautogui.screenshot()
        else:
            screenshot = pyautogui.screenshot()
        
        # 使用专用的颜色过滤识别"昨天"文字（颜色 #9e9e9e = RGB(158, 158, 158)）
        target_color_rgb = (158, 158, 158)
        result = color_targeted_ocr_recognition_yesterday(screenshot, "昨天", target_color_rgb, tolerance=30, stop_flag_func=stop_flag_func)
        
        if result:
            print(f"✅ 检测到'昨天'标记: {result}")
            return True
        else:
            print("❌ 未检测到'昨天'标记")
            return False
        
    except Exception as e:
        print(f"❌ 检查'昨天'标记失败: {e}")
        return False

def common_countdown_wait(wait_seconds, status_callback=None, next_user="无", stop_flag_func=None):
    """通用倒计时等待函数
    
    Args:
        wait_seconds: 等待秒数
        status_callback: 状态回调函数
        next_user: 下一个用户名称
        stop_flag_func: 停止标志检查函数
    """
    if wait_seconds <= 0:
        return
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 倒计时等待被停止")
        return
    
    wait_minutes = wait_seconds // 60
    wait_secs = wait_seconds % 60
    if wait_minutes > 0:
        time_str = f"{wait_minutes}分{wait_secs:02d}秒"
    else:
        time_str = f"{wait_secs}秒"
    print(f"⏳ 等待 {time_str} 后继续下一个用户...")
    
    # 如果有回调函数，执行倒计时
    if status_callback:
        for remaining_seconds in range(wait_seconds, 0, -1):
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 倒计时等待被停止")
                return
                
            remaining_minutes = remaining_seconds // 60
            remaining_secs = remaining_seconds % 60
            if remaining_minutes > 0:
                countdown_str = f"{remaining_minutes}分{remaining_secs:02d}秒"
            else:
                countdown_str = f"{remaining_secs}秒"
            
            status_callback(f"⏳ 倒计时: {countdown_str} (下一个: {next_user})")
            time.sleep(1)
    else:
        # 分段等待，每秒检查一次停止标志
        for _ in range(wait_seconds):
            if stop_flag_func and stop_flag_func():
                print("⏹️ 倒计时等待被停止")
                return
            time.sleep(1)

def common_ocr_recognition(target_names, is_multi_target=False, stop_flag_func=None):
    """通用OCR识别接口
    
    Args:
        target_names: 目标名称，可以是字符串（单目标）或列表（多目标）
        is_multi_target: 是否为多目标识别模式
    
    Returns:
        单目标模式：返回位置坐标或None
        多目标模式：返回字典 {name: position}
    """
    # 统一处理输入参数
    if isinstance(target_names, str):
        target_list = [target_names]
        is_multi_target = False
    else:
        target_list = target_names
        is_multi_target = True
    
    print(f"🔍 在当前视图中使用RapidOCR识别查找: {', '.join(target_list)}")
    
    if not ocr_engine or not ocr_engine.is_available():
        print("⚠️ RapidOCR不可用")
        return {} if is_multi_target else None
    
    try:
        # 获取朋友圈窗口区域
        pengyouquan_region = get_pengyouquan_window_region(stop_flag_func)
        
        if pengyouquan_region:
            # 只截取朋友圈窗口区域
            left, top, right, bottom = pengyouquan_region
            width, height = right - left, bottom - top
            print(f"📸 准备截取朋友圈窗口区域: left={left}, top={top}, width={width}, height={height}")
            
            # 确保坐标和尺寸都是正数
            if width > 0 and height > 0 and left >= 0 and top >= 0:
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                print(f"✅ 成功截取朋友圈窗口区域")
            else:
                print(f"⚠️ 朋友圈窗口区域参数异常，使用全屏截图")
                screenshot = pyautogui.screenshot()
        else:
            # 如果获取朋友圈窗口区域失败，使用全屏截图
            screenshot = pyautogui.screenshot()
            print("📸 使用全屏截图（获取朋友圈窗口区域失败）")
        
        # 保存当前截图（固定文件名，每次覆盖）- 已注释避免生成文件
        # import os
        # screenshot_filename = "current_screenshot.png"
        
        # try:
        #     screenshot.save(screenshot_filename)
        #     # 验证文件是否真的保存了
        #     if os.path.exists(screenshot_filename):
        #         file_size = os.path.getsize(screenshot_filename)
        #         print(f"✅ 已保存当前截图: {screenshot_filename} (大小: {file_size} 字节)")
        #     else:
        #         print(f"❌ 截图保存失败: 文件不存在")
        # except Exception as save_error:
        #     print(f"❌ 截图保存异常: {save_error}")
        
        # 执行OCR识别
        found_results = {}
        
        if is_multi_target:
            # 多目标识别模式
            print(f"🔍 执行一次OCR识别，然后查找所有目标用户...")
            
            # 朋友圈用户名的颜色 #576b95 转换为RGB
            target_color_rgb = (87, 107, 149)  # #576b95
            tolerance = 40  # 增加颜色容差
            
            print(f"🎨 使用颜色过滤OCR识别朋友圈用户名 (目标颜色: RGB{target_color_rgb}, 容差: {tolerance})")
            
            # 首先尝试颜色过滤识别
            color_found_any = False
            for target_name in target_list:
                result = color_targeted_ocr_recognition(screenshot, target_name, target_color_rgb, tolerance, stop_flag_func)
                if result:
                    print(f"✅ 颜色过滤找到目标: {target_name}")
                    found_results[target_name] = result
                    color_found_any = True
            
            # 如果颜色过滤没有找到任何目标，使用普通OCR识别
            if not color_found_any:
                print("🔍 颜色过滤未找到任何目标，使用普通OCR识别...")
                
                try:
                    img_array = np.array(screenshot)
                    ocr_results = ocr_engine.recognize_text(img_array)
                    
                    if ocr_results and len(ocr_results) > 0:
                        print(f"📋 OCR识别到 {len(ocr_results)} 条文字，开始查找目标用户...")
                        
                        # 在OCR结果中查找所有目标用户
                        for target_name in target_list:
                            target_found = False
                            
                            for detection in ocr_results:
                                if len(detection) >= 3:
                                    bbox = detection[0]
                                    text = detection[1]
                                    confidence = detection[2]
                                    
                                    # 检查是否找到目标文字
                                    if target_name in text and confidence > 0.8:
                                        try:
                                            center_x = int(sum([point[0] for point in bbox]) / 4)
                                            center_y = int(sum([point[1] for point in bbox]) / 4)
                                            target_position = (center_x, center_y)
                                            
                                            print(f"✅ OCR找到目标: {target_name} 位置: {target_position}")
                                            found_results[target_name] = target_position
                                            target_found = True
                                            break
                                        except:
                                            continue
                            
                            if not target_found:
                                print(f"❌ OCR未找到目标: {target_name}")
                    else:
                        print("📋 OCR识别结果为空")
                        for target_name in target_list:
                            print(f"❌ OCR未找到目标: {target_name}")
                            
                except Exception as e:
                    print(f"❌ OCR识别失败: {e}")
                    for target_name in target_list:
                        print(f"❌ OCR未找到目标: {target_name}")
            else:
                # 对于颜色过滤没找到的用户，标记为未找到
                for target_name in target_list:
                    if target_name not in found_results:
                        print(f"❌ 颜色过滤未找到目标: {target_name}")
        else:
            # 单目标识别模式
            target_name = target_list[0]
            result = smart_ocr_recognition(screenshot, target_name, stop_flag_func)
            if result:
                print(f"✅ RapidOCR成功找到目标: {target_name}")
                return result
            else:
                print("❌ RapidOCR未找到目标")
                return None
        
        return found_results if is_multi_target else (found_results.get(target_list[0]) if found_results else None)
        
    except Exception as e:
        print(f"❌ RapidOCR识别失败: {e}")
        return {} if is_multi_target else None

def enhanced_recognition_in_current_view(target_name, stop_flag_func=None):
    """在当前视图中使用RapidOCR识别策略查找目标用户名"""
    print(f"🔍 在当前视图中使用RapidOCR识别查找: {target_name}")
    
    # 直接使用RapidOCR识别
    if ocr_engine and ocr_engine.is_available():
        print("📋 使用RapidOCR识别...")
        try:
            # 获取朋友圈窗口区域
            pengyouquan_region = get_pengyouquan_window_region(stop_flag_func)
            
            if pengyouquan_region:
                # 只截取朋友圈窗口区域
                left, top, right, bottom = pengyouquan_region
                width, height = right - left, bottom - top
                print(f"📸 准备截取朋友圈窗口区域: left={left}, top={top}, width={width}, height={height}")
                
                # 确保坐标和尺寸都是正数
                if width > 0 and height > 0 and left >= 0 and top >= 0:
                    screenshot = pyautogui.screenshot(region=(left, top, width, height))
                    print(f"✅ 成功截取朋友圈窗口区域")
                else:
                    print(f"⚠️ 朋友圈窗口区域参数异常，使用全屏截图")
                    screenshot = pyautogui.screenshot()
            else:
                # 如果获取朋友圈窗口区域失败，使用全屏截图
                screenshot = pyautogui.screenshot()
                print("📸 使用全屏截图（获取朋友圈窗口区域失败）")
            
            # 保存当前截图（固定文件名，每次覆盖）- 已注释避免生成文件
            # import os
            # screenshot_filename = "current_screenshot.png"
            
            # try:
            #     screenshot.save(screenshot_filename)
            #     # 验证文件是否真的保存了
            #     if os.path.exists(screenshot_filename):
            #         file_size = os.path.getsize(screenshot_filename)
            #         print(f"✅ 已保存当前截图: {screenshot_filename} (大小: {file_size} 字节)")
            #     else:
            #         print(f"❌ 截图保存失败: 文件不存在")
            # except Exception as save_error:
            #     print(f"❌ 截图保存异常: {save_error}")
            
            # 使用RapidOCR进行识别
            result = smart_ocr_recognition(screenshot, target_name, stop_flag_func)
            if result:
                print(f"✅ RapidOCR成功找到目标: {target_name}")
                return result
            else:
                print("❌ RapidOCR未找到目标")
                return None
        except Exception as e:
            print(f"❌ RapidOCR识别失败: {e}")
            return None
    else:
        print("⚠️ RapidOCR不可用")
        return None

def common_scroll_controller(ocr_callback, stop_condition_callback=None, scroll_description="滚动查找", stop_flag_func=None):
    """通用滚动控制器
    
    Args:
        ocr_callback: OCR识别回调函数，返回识别结果或None
        stop_condition_callback: 停止条件回调函数，返回True时停止滚动
        scroll_description: 滚动描述信息
        stop_flag_func: 停止标志检查函数
    
    Returns:
        OCR识别结果或None
    """
    print(f"🔄 开始{scroll_description}")
    print(f"📋 滚动策略: 持续滚动直到检测到'昨天'标记")
    
    scroll_count = 0
    while True:
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 滚动操作被停止")
            return None
            
        scroll_count += 1
        print(f"\n🔄 第 {scroll_count} 次滚动")
        
        # 按一次下键
        pyautogui.press('down')
        print("⬇️ 已按下键滚动")
        
        # 等待滚动动画完成和内容加载
        print("⏳ 等待滚动动画完成...")
        time.sleep(0.8)  # 增加等待时间，确保动画完成
        
        # 再等待一下确保内容完全加载
        print("⏳ 等待内容加载...")
        time.sleep(0.5)
        
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 滚动操作被停止")
            return None
        
        # 检查是否识别到"昨天"文字（停止条件）
        print("🔍 检查是否到达'昨天'标记...")
        if check_yesterday_marker(stop_flag_func):
            print("🛑 识别到'昨天'标记，停止滚动")
            return None
        
        # 检查自定义停止条件
        if stop_condition_callback and stop_condition_callback():
            print("🛑 满足自定义停止条件，停止滚动")
            return None
        
        print("📸 开始OCR识别...")
        # 执行OCR识别回调
        result = ocr_callback(scroll_count)
        
        if result:
            return result
        else:
            print(f"❌ 第 {scroll_count} 次滚动未找到目标，继续滚动...")

def enhanced_scroll_and_find_name(target_name, stop_flag_func=None):
    """增强滚动查找功能，每按一次下键就进行一次OCR识别，直到找到昨天标记为止"""
    def ocr_callback(scroll_count):
        """OCR识别回调函数"""
        result = common_ocr_recognition(target_name, is_multi_target=False, stop_flag_func=stop_flag_func)
        if result:
            print(f"✅ 在第 {scroll_count} 次滚动后找到目标: {target_name}")
        return result
    
    # 使用通用滚动控制器
    result = common_scroll_controller(
        ocr_callback=ocr_callback,
        scroll_description=f"增强滚动查找: {target_name}",
        stop_flag_func=stop_flag_func
    )
    
    if not result:
        print(f"❌ 已到达'昨天'标记仍未找到目标: {target_name}")
    
    return result

def pengyouquan_dianzan_action(target_name, enable_comment=False, comment_text="", stop_flag_func=None):
    """在朋友圈中查找指定名字并点赞"""
    print(f"👍 开始查找并点赞: {target_name}")
    if enable_comment and comment_text:
        print(f"💬 同时启用评论功能: {comment_text}")
    print("🚀 使用RapidOCR识别策略 + 滚动查找")
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 朋友圈点赞操作被停止")
        return False
    
    # 等待朋友圈加载完成
    print("⏳ 等待朋友圈加载 (5秒)...")
    #time.sleep(5)
    
    # 首先使用通用OCR检查当前页面
    print(f"📋 使用通用OCR检查当前页面是否有: {target_name}")
    name_position = common_ocr_recognition(target_name, is_multi_target=False, stop_flag_func=stop_flag_func)
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 朋友圈点赞操作被停止")
        return False
    
    # 如果当前页面没有找到，开始滚动查找
    if not name_position:
        print(f"❌ 当前页面未找到 '{target_name}'，开始滚动查找...")
        name_position = enhanced_scroll_and_find_name(target_name, stop_flag_func)
    
    if name_position:
        print(f"✅ 找到目标名字: {target_name} 位置: {name_position}")
        
        # 直接查找并点击点赞按钮，不点击用户名
        if find_and_click_dianzan(target_name, name_position, enable_comment=enable_comment, comment_text=comment_text, stop_flag_func=stop_flag_func):
            print(f"👍 成功给 {target_name} 点赞!")
            return True
        else:
            print(f"❌ 未能找到点赞按钮")
            return False
    else:
        print(f"❌ 未找到目标名字: {target_name}")
        return False

def enhanced_multi_recognition_in_current_view(target_names, stop_flag_func=None):
    """在当前视图中同时查找多个目标名字"""
    print(f"🔍 在当前视图中使用RapidOCR同时识别查找: {', '.join(target_names)}")
    
    if not ocr_engine:
        print("⚠️ RapidOCR不可用")
        return {}
    
    try:
        # 获取朋友圈窗口区域
        pengyouquan_region = get_pengyouquan_window_region(stop_flag_func)
        
        if pengyouquan_region:
            # 只截取朋友圈窗口区域
            left, top, right, bottom = pengyouquan_region
            width, height = right - left, bottom - top
            print(f"📸 准备截取朋友圈窗口区域: left={left}, top={top}, width={width}, height={height}")
            
            # 确保坐标和尺寸都是正数
            if width > 0 and height > 0 and left >= 0 and top >= 0:
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                print(f"✅ 成功截取朋友圈窗口区域")
            else:
                print(f"⚠️ 朋友圈窗口区域参数异常，使用全屏截图")
                screenshot = pyautogui.screenshot()
        else:
            # 如果获取朋友圈窗口区域失败，使用全屏截图
            screenshot = pyautogui.screenshot()
            print("📸 使用全屏截图（获取朋友圈窗口区域失败）")
        
        # 保存当前截图（固定文件名，每次覆盖）- 已注释避免生成文件
        # import os
        # screenshot_filename = "current_screenshot.png"
        
        # try:
        #     screenshot.save(screenshot_filename)
        #     # 验证文件是否真的保存了
        #     if os.path.exists(screenshot_filename):
        #         file_size = os.path.getsize(screenshot_filename)
        #         print(f"✅ 已保存当前截图: {screenshot_filename} (大小: {file_size} 字节)")
        #     else:
        #         print(f"❌ 截图保存失败: 文件不存在")
        # except Exception as save_error:
        #     print(f"❌ 截图保存异常: {save_error}")
        
        # 使用RapidOCR进行一次识别，然后在结果中查找所有目标
        found_results = {}
        
        # 一次性OCR识别获取所有文字
        print(f"🔍 执行一次OCR识别，然后查找所有目标用户...")
        
        # 将PIL图像转换为numpy数组
        if hasattr(screenshot, 'save'):  # PIL Image
            img_array = np.array(screenshot)
        else:
            img_array = screenshot
        
        # 朋友圈用户名的颜色 #576b95 转换为RGB
        target_color_rgb = (87, 107, 149)  # #576b95
        tolerance = 40  # 增加颜色容差
        
        print(f"🎨 使用颜色过滤OCR识别朋友圈用户名 (目标颜色: RGB{target_color_rgb}, 容差: {tolerance})")
        
        # 首先尝试颜色过滤识别
        color_found_any = False
        for target_name in target_names:
            result = color_targeted_ocr_recognition(screenshot, target_name, target_color_rgb, tolerance, stop_flag_func)
            if result:
                print(f"✅ 颜色过滤找到目标: {target_name}")
                found_results[target_name] = result
                color_found_any = True
        
        # 如果颜色过滤没有找到任何目标，使用普通OCR识别
        if not color_found_any:
            print("🔍 颜色过滤未找到任何目标，使用普通OCR识别...")
            
            try:
                ocr_results = ocr_engine.recognize_text(img_array)
                
                if ocr_results and len(ocr_results) > 0:
                    print(f"📋 OCR识别到 {len(ocr_results)} 条文字，开始查找目标用户...")
                    
                    # 在OCR结果中查找所有目标用户
                    for target_name in target_names:
                        target_found = False
                        
                        for detection in ocr_results:
                            if len(detection) >= 3:
                                bbox = detection[0]
                                text = detection[1]
                                confidence = detection[2]
                                
                                # 检查是否找到目标文字
                                if target_name in text and confidence > 0.8:
                                    try:
                                        center_x = int(sum([point[0] for point in bbox]) / 4)
                                        center_y = int(sum([point[1] for point in bbox]) / 4)
                                        target_position = (center_x, center_y)
                                        
                                        print(f"✅ OCR找到目标: {target_name} 位置: {target_position}")
                                        found_results[target_name] = target_position
                                        target_found = True
                                        break
                                    except:
                                        continue
                        
                        if not target_found:
                            print(f"❌ OCR未找到目标: {target_name}")
                else:
                    print("📋 OCR识别结果为空")
                    for target_name in target_names:
                        print(f"❌ OCR未找到目标: {target_name}")
                        
            except Exception as e:
                print(f"❌ OCR识别失败: {e}")
                for target_name in target_names:
                    print(f"❌ OCR未找到目标: {target_name}")
        else:
            # 对于颜色过滤没找到的用户，标记为未找到
            for target_name in target_names:
                if target_name not in found_results:
                    print(f"❌ 颜色过滤未找到目标: {target_name}")
        
        return found_results
    except Exception as e:
        print(f"❌ RapidOCR识别失败: {e}")
        return {}

def enhanced_multi_scroll_and_find_names(target_names, stop_flag_func=None):
    """增强多目标滚动查找功能，每按一次下键就进行一次OCR识别查找多个目标，直到找到昨天标记为止"""
    found_results = {}
    remaining_targets = target_names.copy()
    
    def ocr_callback(scroll_count):
        """多目标OCR识别回调函数"""
        nonlocal found_results, remaining_targets
        
        print(f"🎯 剩余待查找目标: {', '.join(remaining_targets)}")
        current_results = common_ocr_recognition(remaining_targets, is_multi_target=True, stop_flag_func=stop_flag_func)
        
        # 处理找到的结果
        for target_name, result in current_results.items():
            print(f"✅ 在第 {scroll_count} 次滚动后找到目标: {target_name}")
            found_results[target_name] = result
            remaining_targets.remove(target_name)
        
        if current_results:
            print(f"📊 本次滚动找到 {len(current_results)} 个目标")
        
        # 返回None继续滚动，直到所有目标找到或遇到昨天标记
        return None
    
    def stop_condition():
        """停止条件：所有目标都找到了"""
        if not remaining_targets:
            print("🎉 所有目标都已找到，提前结束滚动")
            return True
        return False
    
    # 使用通用滚动控制器
    common_scroll_controller(
        ocr_callback=ocr_callback,
        stop_condition_callback=stop_condition,
        scroll_description=f"增强多目标滚动查找: {', '.join(target_names)}",
        stop_flag_func=stop_flag_func
    )
    
    if remaining_targets:
        print(f"❌ 已到达'昨天'标记仍未找到的目标: {', '.join(remaining_targets)}")
    
    print(f"📊 多目标查找完成，共找到 {len(found_results)} 个目标")
    return found_results

def pengyouquan_multi_dianzan_action(target_names, wait_seconds=0, status_callback=None, enable_comment=False, comment_text="", stop_flag_func=None):
    """在朋友圈中查找多个名字并立即点赞（找到一个点赞一个）"""
    print(f"👍 开始多目标查找并点赞: {', '.join(target_names)}")
    if wait_seconds > 0:
        wait_minutes = wait_seconds // 60
        wait_secs = wait_seconds % 60
        if wait_minutes > 0:
            time_str = f"{wait_minutes}分{wait_secs:02d}秒"
        else:
            time_str = f"{wait_secs}秒"
        print(f"🚀 使用RapidOCR多目标识别策略 + 即时点赞 (间隔: {time_str})")
    else:
        print("🚀 使用RapidOCR多目标识别策略 + 即时点赞")
    
    # 检查停止标志
    if stop_flag_func and stop_flag_func():
        print("⏹️ 朋友圈多目标点赞操作被停止")
        return None
    
    # 等待朋友圈加载完成
    print("⏳ 等待朋友圈加载 (5秒)...")
    #time.sleep(5)
    
    # 统计结果
    success_count = 0
    failed_count = 0
    failed_names = []
    found_users = []
    not_found_users = []
    
    # 首先检查当前页面
    print(f"📋 使用通用OCR检查当前页面是否有目标用户")
    current_results = common_ocr_recognition(target_names, is_multi_target=True, stop_flag_func=stop_flag_func)
    
    # 对当前页面找到的用户立即点赞
    total_processed = 0
    for target_name, name_position in current_results.items():
        # 检查停止标志
        if stop_flag_func and stop_flag_func():
            print("⏹️ 朋友圈多目标点赞操作被停止")
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'failed_names': failed_names,
                'found_users': found_users,
                'not_found_users': not_found_users
            }
            
        print(f"\n👍 正在给 {target_name} 点赞...")
        print(f"✅ 目标位置: {name_position}")
        
        if find_and_click_dianzan(target_name, name_position, enable_comment=enable_comment, comment_text=comment_text, stop_flag_func=stop_flag_func):
            print(f"👍 成功给 {target_name} 点赞!")
            success_count += 1
            found_users.append(target_name)
            total_processed += 1
            
            # 如果设置了等待时间且不是最后一个用户，则等待
            if wait_seconds > 0 and total_processed < len(target_names):
                # 找到下一个要处理的用户
                remaining_names = [name for name in target_names if name not in found_users]
                next_user = remaining_names[0] if remaining_names else '无'
                common_countdown_wait(wait_seconds, status_callback, next_user, stop_flag_func)
            else:
                time.sleep(1)  # 点赞后稍等一下
        else:
            print(f"❌ 未能找到 {target_name} 的点赞按钮")
            failed_count += 1
            failed_names.append(target_name)
            total_processed += 1
    
    # 计算剩余需要查找的目标
    remaining_targets = [name for name in target_names if name not in current_results]
    
    # 如果还有剩余目标，开始滚动查找并立即点赞
    if remaining_targets:
        print(f"\n❌ 当前页面未找到的目标: {', '.join(remaining_targets)}")
        print(f"🔄 开始RapidOCR滚动查找并立即点赞...")
        
        scroll_count = 0
        while True:
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 朋友圈多目标点赞操作被停止")
                # 将剩余目标标记为未找到
                for name in remaining_targets:
                    failed_count += 1
                    failed_names.append(name)
                    not_found_users.append(name)
                break
                
            scroll_count += 1
            if not remaining_targets:  # 如果所有目标都找到了，提前结束
                print("🎉 所有目标都已找到，提前结束滚动")
                break
                
            print(f"\n🔄 第 {scroll_count} 次滚动")
            print(f"🎯 剩余待查找目标: {', '.join(remaining_targets)}")
            
            # 按一次下键
            pyautogui.press('down')
            print("⬇️ 已按下键滚动")
            
            # 等待滚动动画完成和内容加载
            print("⏳ 等待滚动动画完成...")
            time.sleep(0.8)
            print("⏳ 等待内容加载...")
            time.sleep(0.5)
            
            # 检查停止标志
            if stop_flag_func and stop_flag_func():
                print("⏹️ 朋友圈多目标点赞操作被停止")
                # 将剩余目标标记为未找到
                for name in remaining_targets:
                    failed_count += 1
                    failed_names.append(name)
                    not_found_users.append(name)
                break
            
            # 检查是否识别到"昨天"文字（停止条件）
            print("🔍 检查是否到达'昨天'标记...")
            if check_yesterday_marker(stop_flag_func):
                print("🛑 识别到'昨天'标记，停止滚动")
                # 通过状态回调通知GUI
                if status_callback:
                    status_callback("🛑 识别到'昨天'标记，停止滚动")
                # 将剩余目标标记为未找到
                if remaining_targets:
                    print(f"❌ 已到达'昨天'标记仍未找到的目标: {', '.join(remaining_targets)}")
                    for name in remaining_targets:
                        print(f"❌ 未找到用户: {name}")
                        failed_count += 1
                        failed_names.append(name)
                # 清空剩余目标
                remaining_targets.clear()
                break
            
            print("📸 开始多目标OCR识别...")
            # 进行多目标OCR识别
            scroll_results = common_ocr_recognition(remaining_targets, is_multi_target=True, stop_flag_func=stop_flag_func)
            
            # 对找到的用户立即点赞
            for target_name, name_position in scroll_results.items():
                # 检查停止标志
                if stop_flag_func and stop_flag_func():
                    print("⏹️ 朋友圈多目标点赞操作被停止")
                    # 将剩余目标标记为未找到
                    for name in remaining_targets:
                        failed_count += 1
                        failed_names.append(name)
                        not_found_users.append(name)
                    return {
                        'success_count': success_count,
                        'failed_count': failed_count,
                        'failed_names': failed_names,
                        'found_users': found_users,
                        'not_found_users': not_found_users
                    }
                    
                print(f"✅ 在第 {scroll_count} 次滚动后找到目标: {target_name}")
                print(f"\n👍 立即给 {target_name} 点赞...")
                print(f"✅ 目标位置: {name_position}")
                
                if find_and_click_dianzan(target_name, name_position, enable_comment=enable_comment, comment_text=comment_text, stop_flag_func=stop_flag_func):
                    print(f"👍 成功给 {target_name} 点赞!")
                    success_count += 1
                    found_users.append(target_name)
                    total_processed += 1
                    
                    # 如果设置了等待时间且不是最后一个用户，则等待
                    if wait_seconds > 0 and total_processed < len(target_names):
                        # 找到下一个要处理的用户
                        remaining_names = [name for name in target_names if name not in found_users]
                        next_user = remaining_names[0] if remaining_names else '无'
                        common_countdown_wait(wait_seconds, status_callback, next_user, stop_flag_func)
                    else:
                        time.sleep(1)  # 点赞后稍等一下
                else:
                    print(f"❌ 未能找到 {target_name} 的点赞按钮")
                    failed_count += 1
                    failed_names.append(target_name)
                    total_processed += 1
                
                # 从剩余目标中移除已处理的用户
                remaining_targets.remove(target_name)
            
            if scroll_results:
                print(f"📊 本次滚动找到并处理 {len(scroll_results)} 个目标")
            else:
                print(f"❌ 第 {scroll_count} 次滚动未找到任何目标，继续滚动...")
    
    # 返回详细结果
    result = {
        'success_count': success_count,
        'failed_count': failed_count,
        'failed_names': failed_names,
        'found_users': found_users,
        'not_found_users': not_found_users
    }
    
    print(f"\n📊 多目标点赞完成!")
    print(f"   成功点赞: {success_count} 个")
    print(f"   失败: {failed_count} 个")
    if failed_names:
        print(f"   失败用户: {', '.join(failed_names)}")
    
    return result

def find_and_click_pengyouquan_with_dianzan(target_name=None, stop_flag_func=None):
    """完整的朋友圈功能：打开朋友圈并查找指定用户点赞"""
    print("👥💖 开始执行朋友圈完整功能...")
    
    # 将微信窗口置于最前
    if not ensure_wechat_is_active():
        print("❌ 无法激活微信窗口")
        return False
    
    # 查找并点击朋友圈
    if not find_and_click_pengyouquan(stop_flag_func):
        print("❌ 无法打开朋友圈")
        return False
    
    print("✅ 朋友圈已打开")
    time.sleep(3)  # 等待朋友圈加载
    
    # GUI模式下必须提供目标用户名
    if target_name is None or not target_name:
        print("❌ 未提供目标用户名")
        return False
    
    # 执行点赞操作
    return pengyouquan_dianzan_action(target_name, stop_flag_func=stop_flag_func)

# ==================== 主程序 ====================

# 命令行入口点已移除，此文件现在仅作为GUI的后端模块使用
# 所有功能通过GUI界面调用，不再支持独立的命令行运行