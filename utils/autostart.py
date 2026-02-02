import os
import sys
import winreg

def _get_program_path():
    """获取程序启动路径"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        return f'"{pythonw}" "{os.path.abspath(sys.argv[0])}"'

def set_autostart(enable):
    """
    设置开机自启动
    enable: True开启, False关闭
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "AI_Desk_Pet"
    
    try:
        if enable:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, _get_program_path())
        else:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, app_name)
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        print(f"设置开机自启动失败: {e}")
        return False

def is_autostart_enabled():
    """检查是否已开启开机自启动"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "AI_Desk_Pet"
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, app_name)
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False