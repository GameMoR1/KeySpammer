import threading
import time
import win32api
import win32con
import win32gui

class KeySpammer:
    def __init__(self):
        self.is_spamming = False
        self.spam_thread = None
        self.current_key = None
        self.current_speed = 10
        self.target_hwnd = None
        self.mode = 1  # 1 = по нажатию, 2 = включение/выключение
        self.key_pressed = False
        self.spam_active = False  # Для режима включения/выключения

    def set_profile(self, key, speed, mode, target_hwnd=None):
        self.current_key = key
        self.current_speed = speed
        self.mode = mode
        self.target_hwnd = target_hwnd
        self.key_pressed = False
        self.spam_active = False

    def start_spam(self):
        if not self.current_key:
            return
        self.is_spamming = True
        delay = 1.0 / self.current_speed
        key_code = self._get_key_code(self.current_key)

        def spam():
            prev_pressed = False
            while self.is_spamming:
                current_pressed = win32api.GetAsyncKeyState(key_code) & 0x8000
                if self.mode == 1:
                    # Режим "по нажатию": спам только если клавиша зажата
                    if not current_pressed:
                        time.sleep(0.01)
                        continue
                elif self.mode == 2:
                    # Режим "включение/выключение": спам по нажатию клавиши
                    if current_pressed and not prev_pressed:
                        self.spam_active = not self.spam_active
                    prev_pressed = current_pressed
                    if not self.spam_active:
                        time.sleep(0.01)
                        continue
                # Отправка клавиши
                if self.target_hwnd:
                    win32gui.SetForegroundWindow(self.target_hwnd)
                win32api.keybd_event(key_code, 0, 0, 0)
                win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(delay)

        self.spam_thread = threading.Thread(target=spam)
        self.spam_thread.daemon = True
        self.spam_thread.start()

    def stop_spam(self):
        self.is_spamming = False
        self.spam_active = False
        if self.spam_thread:
            self.spam_thread.join(timeout=0.1)
        self.spam_thread = None

    def _get_key_code(self, key_name):
        if len(key_name) == 1:
            return ord(key_name.upper())
        special_keys = {
            'space': win32con.VK_SPACE,
            'enter': win32con.VK_RETURN,
            'esc': win32con.VK_ESCAPE,
            'tab': win32con.VK_TAB,
            'page up': win32con.VK_PRIOR,
            'page down': win32con.VK_NEXT,
            'end': win32con.VK_END,
            'home': win32con.VK_HOME,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'insert': win32con.VK_INSERT,
            'delete': win32con.VK_DELETE,
        }
        return special_keys.get(key_name.lower(), win32con.VK_SPACE)
