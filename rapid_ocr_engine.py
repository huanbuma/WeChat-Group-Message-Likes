"""
RapidOCR 核心引擎模块
基于 RapidOCR 的轻量级 OCR 实现，无需安装额外软件
支持中文、英文等多语言识别
"""

import os
import sys
import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RapidOCREngine:
    """RapidOCR 核心引擎类"""
    
    def __init__(self):
        """初始化 RapidOCR 引擎"""
        self.engine = None
        self.available = False
        self._init_engine()
    
    def _init_engine(self):
        """初始化 OCR 引擎"""
        try:
            # 尝试导入 rapidocr
            from rapidocr_onnxruntime import RapidOCR
            self.engine = RapidOCR()
            self.available = True
            logger.info("✅ RapidOCR 引擎初始化成功")
        except ImportError as e:
            logger.warning(f"❌ RapidOCR 未安装 (rapidocr_onnxruntime): {e}")
            try:
                # 备选方案：尝试导入 rapidocr
                from rapidocr import RapidOCR
                self.engine = RapidOCR()
                self.available = True
                logger.info("✅ RapidOCR 引擎初始化成功 (备选导入)")
            except ImportError as e2:
                logger.warning(f"❌ RapidOCR 未安装 (rapidocr): {e2}")
                logger.warning("RapidOCR不可用，将使用基础模式")
                self.available = False
        except Exception as e:
            logger.error(f"❌ RapidOCR 引擎初始化失败: {e}")
            logger.warning("RapidOCR不可用，将使用基础模式")
            self.available = False
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return self.available and self.engine is not None
    
    def recognize_image(self, image: Union[str, np.ndarray], **kwargs) -> List[Tuple]:
        """
        识别图像中的文字
        
        Args:
            image: 图像路径或numpy数组
            **kwargs: 其他参数
            
        Returns:
            识别结果列表，每个元素为 (bbox, text, confidence)
        """
        if not self.is_available():
            logger.error("RapidOCR 引擎不可用")
            return []
        
        try:
            # 如果是文件路径，直接使用
            if isinstance(image, str):
                if not os.path.exists(image):
                    logger.error(f"图像文件不存在: {image}")
                    return []
                result = self.engine(image)
            else:
                # 如果是numpy数组，直接使用
                result = self.engine(image)
            
            if result is None or len(result) == 0:
                return []
            
            # RapidOCR返回格式: (识别结果列表, 时间统计)
            # 我们只需要第一个元素
            if isinstance(result, tuple) and len(result) > 0:
                ocr_data = result[0]  # 获取识别结果列表
            else:
                ocr_data = result
            
            if not ocr_data:
                return []
            
            # 解析结果
            ocr_results = []
            for item in ocr_data:
                if len(item) >= 3:
                    bbox = item[0]  # 边界框坐标
                    text = item[1]  # 识别的文字
                    confidence = item[2]  # 置信度
                    
                    # 确保置信度是数值类型
                    if isinstance(confidence, (list, tuple)):
                        confidence = float(confidence[0]) if len(confidence) > 0 else 0.0
                    else:
                        confidence = float(confidence)
                    
                    ocr_results.append((bbox, text, confidence))
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            return []
    
    def find_text_in_image(self, image: Union[str, np.ndarray], target_text: str, 
                          confidence_threshold: float = 0.7) -> List[Tuple[int, int, float]]:
        """
        在图像中查找指定文字的位置
        
        Args:
            image: 图像路径或numpy数组
            target_text: 要查找的文字
            confidence_threshold: 置信度阈值
            
        Returns:
            匹配结果列表，每个元素为 (x, y, confidence)
        """
        results = self.recognize_image(image)
        matches = []
        
        for bbox, text, confidence in results:
            if confidence >= confidence_threshold and target_text in text:
                # 计算边界框中心点
                if len(bbox) == 4:  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    try:
                        center_x = int(sum([point[0] for point in bbox]) / 4)
                        center_y = int(sum([point[1] for point in bbox]) / 4)
                        matches.append((center_x, center_y, confidence))
                    except (ZeroDivisionError, TypeError, IndexError) as e:
                        logger.warning(f"计算边界框中心点失败: {e}, bbox: {bbox}")
                        continue
        
        return matches
    
    def recognize_with_color_filter(self, image: np.ndarray, target_color: Tuple[int, int, int],
                                   color_tolerance: int = 30) -> List[Tuple]:
        """
        使用颜色过滤进行OCR识别
        
        Args:
            image: 输入图像
            target_color: 目标颜色 (R, G, B)
            color_tolerance: 颜色容差
            
        Returns:
            识别结果列表
        """
        try:
            # 创建颜色过滤图像
            filtered_image = self._create_color_filtered_image(image, target_color, color_tolerance)
            
            # 对过滤后的图像进行OCR识别
            return self.recognize_image(filtered_image)
            
        except Exception as e:
            logger.error(f"颜色过滤OCR识别失败: {e}")
            return []
    
    def _create_color_filtered_image(self, image: np.ndarray, target_color: Tuple[int, int, int],
                                   color_tolerance: int = 30) -> np.ndarray:
        """
        创建颜色过滤图像
        
        Args:
            image: 输入图像
            target_color: 目标颜色 (R, G, B)
            color_tolerance: 颜色容差
            
        Returns:
            过滤后的图像
        """
        # 转换为RGB格式（如果需要）
        if len(image.shape) == 3 and image.shape[2] == 3:
            # BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # 创建颜色掩码
        lower_bound = np.array([max(0, c - color_tolerance) for c in target_color])
        upper_bound = np.array([min(255, c + color_tolerance) for c in target_color])
        
        # 创建掩码
        mask = cv2.inRange(image_rgb, lower_bound, upper_bound)
        
        # 创建白色背景
        result = np.ones_like(image_rgb) * 255
        
        # 将匹配的像素设为黑色
        result[mask > 0] = [0, 0, 0]
        
        return result


class EnhancedOCREngine:
    """简化的OCR引擎，只使用RapidOCR"""
    
    def __init__(self):
        """初始化OCR引擎"""
        self.rapid_ocr = RapidOCREngine()
    
    def is_available(self) -> bool:
        """检查RapidOCR是否可用"""
        return self.rapid_ocr.is_available()
    
    def get_current_engine(self) -> str:
        """获取当前使用的OCR引擎"""
        if self.rapid_ocr.is_available():
            return "RapidOCR"
        else:
            return "None"
    
    def recognize_text(self, image: Union[str, np.ndarray], method: str = "rapid") -> List[Tuple]:
        """
        文字识别（只使用RapidOCR）
        
        Args:
            image: 图像路径或numpy数组
            method: 识别方法（只支持"rapid"）
            
        Returns:
            识别结果列表
        """
        if self.rapid_ocr.is_available():
            return self.rapid_ocr.recognize_image(image)
        else:
            logger.error("RapidOCR引擎不可用")
            return []
    
    def find_text_position(self, image: Union[str, np.ndarray], target_text: str,
                          target_color: Optional[Tuple[int, int, int]] = None,
                          confidence_threshold: float = 0.7) -> Optional[Tuple[int, int]]:
        """
        查找文字在图像中的位置
        
        Args:
            image: 图像路径或numpy数组
            target_text: 要查找的文字
            target_color: 目标颜色（可选）
            confidence_threshold: 置信度阈值
            
        Returns:
            文字位置 (x, y) 或 None
        """
        try:
            # 如果指定了颜色，使用颜色过滤
            if target_color and self.rapid_ocr.is_available():
                if isinstance(image, str):
                    image_array = cv2.imread(image)
                else:
                    image_array = image
                
                matches = self.rapid_ocr.recognize_with_color_filter(
                    image_array, target_color, color_tolerance=30
                )
                
                for bbox, text, confidence in matches:
                    if confidence >= confidence_threshold and target_text in text:
                        # 计算中心点
                        center_x = int(sum([point[0] for point in bbox]) / 4)
                        center_y = int(sum([point[1] for point in bbox]) / 4)
                        return (center_x, center_y)
            
            # 普通识别
            results = self.recognize_text(image)
            for bbox, text, confidence in results:
                if confidence >= confidence_threshold and target_text in text:
                    # 计算中心点
                    center_x = int(sum([point[0] for point in bbox]) / 4)
                    center_y = int(sum([point[1] for point in bbox]) / 4)
                    return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.error(f"查找文字位置失败: {e}")
            return None


# 全局实例
ocr_engine = EnhancedOCREngine()

def get_ocr_engine() -> EnhancedOCREngine:
    """获取OCR引擎实例"""
    return ocr_engine

def install_rapidocr():
    """安装RapidOCR依赖"""
    try:
        import subprocess
        import sys
        
        print("正在安装 RapidOCR...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rapidocr-onnxruntime"])
        print("✅ RapidOCR 安装成功！")
        return True
    except Exception as e:
        print(f"❌ RapidOCR 安装失败: {e}")
        return False

# 命令行测试代码已移除，此文件现在仅作为GUI的后端模块使用