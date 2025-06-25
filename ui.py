import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import keyboard
import ctypes
import ctypes.wintypes
from binder import KeySpammer
from profiles import load_profiles, add_or_update_profile, delete_profile, get_profile
import webbrowser

help_text_ru = '''
Добро пожаловать в KeySpammer!

Это приложение позволяет вам автоматически спамить заданной клавишей с выбранной скоростью и режимом.

Основные функции:

1. Профили: создавайте, сохраняйте и удаляйте профили с настройками клавиши, скорости, режима и выбранного окна.

2. Бинд клавиши: нажмите "Забиндить клавишу" и нажмите нужную клавишу на клавиатуре. Приложение учитывает раскладку (русская/английская).

3. Режимы спама:
   - Зажатие: спам идет только при зажатии клавиши.
   - Включение/Выключение: при нажатии клавиши спам запускается, при повторном нажатии — останавливается.

4. Выбор окна: выберите окно, в котором будет работать спам. Если окно не выбрано, спам идет глобально (или не работает =) ).

5. Переключение языка интерфейса: кнопка в правом верхнем углу позволяет переключать язык между русским и английским.

Как пользоваться:

- Забиндите клавишу.
- Выберите скорость спама (1-100 нажатий в секунду).
- Выберите режим спама.
- При необходимости выберите окно для спама.
- Создайте новый профиль, нажав "Добавить".
- Нажмите "Спам" для запуска/остановки спама.

Удачи!
'''

help_text_en = '''
Welcome to KeySpammer!

This application allows you to automatically spam a specified key with chosen speed and mode.

Main features:

1. Profiles: create, save, and delete profiles with key, speed, mode, and selected window settings.

2. Bind key: click "Bind key" and press the desired key on your keyboard. The app accounts for keyboard layout (Russian/English).

3. Spam modes:
   - Hold: spam works only while the key is held down.
   - Toggle: spam starts on key press and stops on next press.

4. Window selection: choose the window where spam will work. If no window is selected, spam is global (or will not work =) ).

5. Interface language switch: the button in the top right corner toggles between Russian and English.

How to use:

- Bind a key.
- Select spam speed (1-100 presses per second).
- Choose spam mode.
- Select a window for spam.
- Create a new profile by clicking "Add".
- Click "Spam" to start/stop spamming.

Good luck!
'''

def ru_to_en_key(rus_key):
    mapping = {
        'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
        'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k', 'д': 'l',
        'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm'
    }
    return mapping.get(rus_key.lower(), rus_key)

def enum_windows():
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    GetWindowText = user32.GetWindowTextW
    GetWindowTextLength = user32.GetWindowTextLengthW
    IsWindowVisible = user32.IsWindowVisible

    windows = []

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                windows.append((hwnd, buff.value))
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)
    return windows

class HelpDialog(ctk.CTkToplevel):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.title("Помощь" if lang == "ru" else "Help")
        self.geometry("600x500")
        self.resizable(False, False)
        self.textbox = ctk.CTkTextbox(self, wrap="word", width=580, height=420)
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", help_text_ru if lang == "ru" else help_text_en)
        self.textbox.configure(state="disabled")
        self.close_button = ctk.CTkButton(self, text="Закрыть" if lang == "ru" else "Close", command=self.destroy)
        self.close_button.pack(pady=10)

def show_help(parent, lang):
    dlg = HelpDialog(parent, lang)
    dlg.grab_set()
    dlg.focus_set()
    dlg.wait_window()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KeySpammer")
        self.geometry("750x380")
        self.spammer = KeySpammer()
        self.current_key = None
        self.current_profile_name = None
        self.target_hwnd = None
        self.target_title = None
        self.lang = "ru"  # ru/en
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Левая панель: профили
        self.profiles_frame = ctk.CTkFrame(self)
        self.profiles_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        self.profiles_label = ctk.CTkLabel(self.profiles_frame)
        self.profiles_label.pack(pady=10)
        self.profiles_listbox = tk.Listbox(self.profiles_frame, width=20, height=10)
        self.profiles_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.profiles_listbox.bind("<<ListboxSelect>>", self.on_profile_select)
        self.add_profile_button = ctk.CTkButton(self.profiles_frame, command=self.add_profile)
        self.add_profile_button.pack(pady=5)
        self.delete_profile_button = ctk.CTkButton(self.profiles_frame, command=self.delete_profile)
        self.delete_profile_button.pack(pady=5)
        self.update_profile_list()

        # Правая панель: настройки и управление
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # --- Кнопки языка и помощи в правом верхнем углу settings_frame ---
        self.lang_button = ctk.CTkButton(
            self.settings_frame,
            text="EN",
            width=50,
            command=self.toggle_language
        )
        self.lang_button.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)
        self.help_button = ctk.CTkButton(
            self.settings_frame,
            text="Помощь",
            width=70,
            command=self.on_help
        )
        self.help_button.place(relx=1.0, rely=0.0, anchor="ne", x=-80, y=10)
        # --------------------------------------------------------

        self.key_label = ctk.CTkLabel(self.settings_frame)
        self.key_label.pack(pady=5)
        self.bind_key_button = ctk.CTkButton(self.settings_frame, command=self.bind_key)
        self.bind_key_button.pack(pady=5)
        self.speed_label = ctk.CTkLabel(self.settings_frame)
        self.speed_label.pack(pady=5)
        self.speed_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=100, command=self.on_speed_change)
        self.speed_slider.pack(pady=5)
        self.speed_value = ctk.CTkLabel(self.settings_frame)
        self.speed_value.pack(pady=5)
        self.mode_var = ctk.IntVar(value=1)
        self.mode_frame = ctk.CTkFrame(self.settings_frame)
        self.mode_frame.pack(pady=10)
        self.mode_label = ctk.CTkLabel(self.mode_frame)
        self.mode_label.pack(side="left")
        self.mode_1 = ctk.CTkRadioButton(self.mode_frame, variable=self.mode_var, value=1)
        self.mode_1.pack(side="left", padx=5)
        self.mode_2 = ctk.CTkRadioButton(self.mode_frame, variable=self.mode_var, value=2)
        self.mode_2.pack(side="left", padx=5)
        self.select_window_button = ctk.CTkButton(self.settings_frame, command=self.select_window)
        self.select_window_button.pack(pady=5)
        self.window_label = ctk.CTkLabel(self.settings_frame)
        self.window_label.pack(pady=5)
        self.spam_button = ctk.CTkButton(self.settings_frame, command=self.toggle_spam)
        self.spam_button.pack(pady=10)

        # --- Кнопка и надпись "Мой бусти" в правом нижнем углу ---
        self.boosty_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.boosty_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  # x=-10, y=-10 — небольшой отступ от края
        self.boosty_label = ctk.CTkLabel(self.boosty_frame, text="Мой Boosty")
        self.boosty_label.pack(side="top", anchor="e")
        self.boosty_button = ctk.CTkButton(
            self.boosty_frame,
            text="Поддержать",
            width=120,
            command=lambda: webbrowser.open_new_tab("https://boosty.to/gamemor")
        )
        self.boosty_button.pack(side="top", anchor="e", pady=5)


        keyboard.hook(self.on_key_event)
        self.update_language()

    def on_help(self):
        show_help(self, self.lang)

    def update_language(self):
        if self.lang == "ru":
            self.profiles_label.configure(text="Профили")
            self.add_profile_button.configure(text="Добавить")
            self.delete_profile_button.configure(text="Удалить")
            self.key_label.configure(text=f"Клавиша: {'не выбрана' if not self.current_key else self.current_key}")
            self.bind_key_button.configure(text="Забиндить клавишу")
            self.speed_label.configure(text="Скорость спама (1-100):")
            self.mode_label.configure(text="Режим:")
            self.mode_1.configure(text="Зажатие")
            self.mode_2.configure(text="Включение/Выключение")
            self.select_window_button.configure(text="Выбрать окно")
            self.window_label.configure(text=f"Окно: {'не выбрано' if not self.target_title else self.target_title}")
            self.spam_button.configure(text="Спам" if not hasattr(self, "is_spamming") or not self.is_spamming else "Остановить")
            self.lang_button.configure(text="EN")
            self.help_button.configure(text="Помощь")
            self.boosty_label.configure(text="Мой бусти")
            self.boosty_button.configure(text="Поддержать")
        else:
            self.profiles_label.configure(text="Profiles")
            self.add_profile_button.configure(text="Add")
            self.delete_profile_button.configure(text="Delete")
            self.key_label.configure(text=f"Key: {'not selected' if not self.current_key else self.current_key}")
            self.bind_key_button.configure(text="Bind key")
            self.speed_label.configure(text="Spam speed (1-100):")
            self.mode_label.configure(text="Mode:")
            self.mode_1.configure(text="Hold")
            self.mode_2.configure(text="Toggle")
            self.select_window_button.configure(text="Select window")
            self.window_label.configure(text=f"Window: {'not selected' if not self.target_title else self.target_title}")
            self.spam_button.configure(text="Spam" if not hasattr(self, "is_spamming") or not self.is_spamming else "Stop")
            self.lang_button.configure(text="RU")
            self.help_button.configure(text="Help")
            self.boosty_label.configure(text="My Boosty")
            self.boosty_button.configure(text="Support")

    def toggle_language(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.update_language()

    def select_window(self):
        windows = enum_windows()
        self.select_window_window = ctk.CTkToplevel(self)
        self.select_window_window.title("Выберите окно для спама" if self.lang == "ru" else "Select window for spam")
        self.select_window_window.geometry("600x400")
        self.select_window_window.transient(self)
        self.select_window_window.grab_set()

        frame = ctk.CTkFrame(self.select_window_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        for idx, (hwnd, title) in enumerate(windows):
            btn = ctk.CTkButton(
                frame,
                text=f"{title}",
                command=lambda hwnd=hwnd, title=title: self.set_window(hwnd, title)
            )
            btn.pack(fill="x", padx=5, pady=2)

        cancel_btn = ctk.CTkButton(
            frame,
            text="Отмена" if self.lang == "ru" else "Cancel",
            command=self.select_window_window.destroy
        )
        cancel_btn.pack(fill="x", padx=5, pady=10)

    def set_window(self, hwnd, title):
        self.target_hwnd = hwnd
        self.target_title = title
        if self.lang == "ru":
            self.window_label.configure(text=f"Окно: {self.target_title}")
        else:
            self.window_label.configure(text=f"Window: {self.target_title}")
        self.select_window_window.destroy()

    def update_profile_list(self):
        profiles = load_profiles()
        self.profiles_listbox.delete(0, tk.END)
        for name in profiles:
            self.profiles_listbox.insert(tk.END, name)

    def on_profile_select(self, event):
        selected = self.profiles_listbox.curselection()
        if selected:
            name = self.profiles_listbox.get(selected[0])
            profile = get_profile(name)
            if profile:
                self.current_profile_name = name
                self.current_key = profile["key"]
                if self.lang == "ru":
                    self.key_label.configure(text=f"Клавиша: {self.current_key}")
                else:
                    self.key_label.configure(text=f"Key: {self.current_key}")
                self.speed_slider.set(profile["speed"])
                self.speed_value.configure(text=str(profile["speed"]))
                self.mode_var.set(profile["mode"])
                self.target_title = profile.get("target_title")
                if self.target_title:
                    if self.lang == "ru":
                        self.window_label.configure(text=f"Окно: {self.target_title}")
                    else:
                        self.window_label.configure(text=f"Window: {self.target_title}")
                    # Находим hwnd по названию
                    windows = enum_windows()
                    for hwnd, title in windows:
                        if title == self.target_title:
                            self.target_hwnd = hwnd
                            break
                else:
                    if self.lang == "ru":
                        self.window_label.configure(text="Окно: не выбрано")
                    else:
                        self.window_label.configure(text="Window: not selected")
                    self.target_hwnd = None

    def add_profile(self):
        if not self.current_key:
            messagebox.showerror(
                "Ошибка" if self.lang == "ru" else "Error",
                "Забиндьте клавишу!" if self.lang == "ru" else "Bind a key first!"
            )
            return
        speed = int(self.speed_slider.get())
        mode = self.mode_var.get()
        name = ctk.CTkInputDialog(
            text="Введите имя профиля:" if self.lang == "ru" else "Enter profile name:",
            title="Добавить профиль" if self.lang == "ru" else "Add profile"
        ).get_input()
        if name:
            profiles = load_profiles()
            if name in profiles:
                messagebox.showerror(
                    "Ошибка" if self.lang == "ru" else "Error",
                    "Профиль с таким именем уже существует!" if self.lang == "ru" else "Profile with this name already exists!"
                )
                return
            add_or_update_profile(name, self.current_key, speed, mode, self.target_title)
            self.current_profile_name = name
            self.update_profile_list()

    def delete_profile(self):
        selected = self.profiles_listbox.curselection()
        if selected:
            name = self.profiles_listbox.get(selected[0])
            if delete_profile(name):
                self.update_profile_list()
                self.current_profile_name = None
                self.current_key = None
                if self.lang == "ru":
                    self.key_label.configure(text="Клавиша: не выбрана")
                else:
                    self.key_label.configure(text="Key: not selected")

    def bind_key(self):
        if self.lang == "ru":
            self.key_label.configure(text="Нажмите клавишу...")
        else:
            self.key_label.configure(text="Press a key...")
        self.bind_key_button.configure(state="disabled")
        self.waiting_for_key = True

    def on_key_event(self, event):
        if hasattr(self, 'waiting_for_key') and self.waiting_for_key and event.event_type == 'down':
            self.current_key = ru_to_en_key(event.name)
            if self.lang == "ru":
                self.key_label.configure(text=f"Клавиша: {self.current_key}")
            else:
                self.key_label.configure(text=f"Key: {self.current_key}")
            self.bind_key_button.configure(state="normal")
            self.waiting_for_key = False

    def on_speed_change(self, value):
        self.speed_value.configure(text=str(int(float(value))))

    def toggle_spam(self):
        if not self.current_key:
            messagebox.showerror(
                "Ошибка" if self.lang == "ru" else "Error",
                "Забиндьте клавишу!" if self.lang == "ru" else "Bind a key first!"
            )
            return
        speed = int(self.speed_slider.get())
        mode = self.mode_var.get()
        self.spammer.set_profile(self.current_key, speed, mode, self.target_hwnd)
        if not hasattr(self, "is_spamming") or not self.is_spamming:
            self.is_spamming = True
            if self.lang == "ru":
                self.spam_button.configure(text="Остановить")
            else:
                self.spam_button.configure(text="Stop")
            self.spammer.start_spam()
        else:
            self.is_spamming = False
            if self.lang == "ru":
                self.spam_button.configure(text="Спам")
            else:
                self.spam_button.configure(text="Spam")
            self.spammer.stop_spam()