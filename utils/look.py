import base64
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QBuffer, QByteArray, QIODevice

def capture_screen_base64():
    """捕获全屏并返回base64编码的PNG图片"""
    try:
        # 确保QApplication实例存在
        app = QApplication.instance()
        if not app:
            raise RuntimeError("QApplication 未初始化")
            
        screen = QApplication.primaryScreen()
        if not screen:
            raise RuntimeError("无法获取主屏幕")
            
        screenshot = screen.grabWindow(0)
        if screenshot.isNull():
            raise RuntimeError("截图失败")
        
        # 使用QBuffer而不是io.BytesIO
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        
        if not screenshot.save(buffer, "PNG"):
            raise RuntimeError("保存截图到缓冲区失败")
            
        buffer.close()
        
        # 编码为base64
        base64_data = base64.b64encode(byte_array).decode('utf-8')
        
        if not base64_data:
            raise RuntimeError("base64编码失败")
            
        return base64_data
        
    except Exception as e:
        # 打印详细错误信息到控制台
        print(f"截图错误详情: {type(e).__name__}: {str(e)}")
        raise  # 重新抛出异常，让调用者处理