# -*- mode: python ; coding: utf-8 -*-
import os
import site

block_cipher = None

# 动态获取rapidocr_onnxruntime包的路径
def get_rapidocr_path():
    try:
        import rapidocr_onnxruntime
        rapidocr_path = os.path.dirname(rapidocr_onnxruntime.__file__)
        return rapidocr_path
    except ImportError:
        # 如果导入失败，尝试从site-packages中查找
        for site_path in site.getsitepackages():
            rapidocr_path = os.path.join(site_path, 'rapidocr_onnxruntime')
            if os.path.exists(rapidocr_path):
                return rapidocr_path
        return None

rapidocr_base_path = get_rapidocr_path()

# 构建数据文件列表
datas = [
    ('wechat_automation_gui.py', '.'),
    ('wechat_core_engine.py', '.'),
    ('requirements.txt', '.'),
    ('assets', 'assets'),  # 添加assets目录，包含朋友圈功能所需的图像文件
]

# 如果找到了rapidocr_onnxruntime路径，添加相关文件
if rapidocr_base_path and os.path.exists(rapidocr_base_path):
    rapidocr_files = [
        ('config.yaml', 'rapidocr_onnxruntime'),
        ('models', 'rapidocr_onnxruntime/models'),
        ('ch_ppocr_det', 'rapidocr_onnxruntime/ch_ppocr_det'),
        ('ch_ppocr_rec', 'rapidocr_onnxruntime/ch_ppocr_rec'),
        ('ch_ppocr_cls', 'rapidocr_onnxruntime/ch_ppocr_cls'),
        ('cal_rec_boxes', 'rapidocr_onnxruntime/cal_rec_boxes'),
        ('utils', 'rapidocr_onnxruntime/utils'),
    ]
    
    for src_file, dest_path in rapidocr_files:
        src_path = os.path.join(rapidocr_base_path, src_file)
        if os.path.exists(src_path):
            datas.append((src_path, dest_path))
        else:
            print(f"警告: 未找到 {src_path}")
else:
    print("警告: 未找到 rapidocr_onnxruntime 包，可能会影响OCR功能")

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'pyautogui',
        'pyperclip',
        'cv2',
        'numpy',
        'PIL',
        'rapidocr_onnxruntime',
        'sklearn',
        'win32gui',
        'win32con',
        'win32api'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='微信自动化工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
