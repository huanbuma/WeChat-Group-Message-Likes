# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('wechat_automation_gui.py', '.'),
        ('wechat_core_engine.py', '.'),
        ('requirements.txt', '.'),
        ('assets', 'assets'),  # 添加assets目录，包含朋友圈功能所需的图像文件
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\config.yaml', 'rapidocr_onnxruntime'),
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\models', 'rapidocr_onnxruntime/models'),
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\ch_ppocr_det', 'rapidocr_onnxruntime/ch_ppocr_det'),
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\ch_ppocr_rec', 'rapidocr_onnxruntime/ch_ppocr_rec'),
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\ch_ppocr_cls', 'rapidocr_onnxruntime/ch_ppocr_cls'),
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\cal_rec_boxes', 'rapidocr_onnxruntime/cal_rec_boxes'),
        ('C:\\Users\\zhao\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\rapidocr_onnxruntime\\utils', 'rapidocr_onnxruntime/utils'),
    ],
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
