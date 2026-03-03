import tkinter as tk

# Ширина и высота окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Цвет фона (позже можно поменять на изображение)
BG_COLOR = '#2C3E50'
BUTTON_BG_COLOR = '#3498DB'
BUTTON_FG_COLOR = '#FFFFFF'

# Класс Menu
class Menu:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Колледж Винкс: Побег")
        self.parent.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.parent.configure(bg=BG_COLOR)

        # Контейнер для кнопок
        buttons_frame = tk.Frame(parent, bg=BG_COLOR)
        buttons_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Три кнопки
        new_game_btn = tk.Button(buttons_frame, text="Начать игру с начала", fg=BUTTON_FG_COLOR, bg=BUTTON_BG_COLOR, font=("Helvetica", 16), command=self.start_new_game)
        new_game_btn.pack(pady=10)

        load_game_btn = tk.Button(buttons_frame, text="Продолжить с сохранения", fg=BUTTON_FG_COLOR, bg=BUTTON_BG_COLOR, font=("Helvetica", 16), command=self.load_game)
        load_game_btn.pack(pady=10)

        exit_btn = tk.Button(buttons_frame, text="Закрыть", fg=BUTTON_FG_COLOR, bg=BUTTON_BG_COLOR, font=("Helvetica", 16), command=self.exit_game)
        exit_btn.pack(pady=10)

    def start_new_game(self):
        print("Нажата кнопка 'Начать игру с начала'")
        # Тут будет вызов сценария игры

    def load_game(self):
        print("Нажата кнопка 'Продолжить с сохранения'")
        # Тут будет восстановление состояния игры

    def exit_game(self):
        self.parent.destroy()

# Основная функция запуска
def run_menu():
    root = tk.Tk()
    app = Menu(root)
    root.mainloop()

# Запускаем меню
run_menu()
