import tkinter as tk
from PIL import Image, ImageTk
import random
import json

# Размеры окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Основные классы и функции

# Класс сцены
class Scene:
    def __init__(self, image_path, description, choices):
        self.image = Image.open(image_path)
        self.description = description
        self.choices = choices

# Класс игры пятнашки
class PuzzleGame:
    def __init__(self, parent):
        self.parent = parent
        self.size = 3
        self.buttons = [[None]*self.size for _ in range(self.size)]
        self.empty_row, self.empty_col = self.size - 1, self.size - 1
        self.sequence = list(range(1, self.size*self.size)) + [0]
        self.shuffle()

        # Интерфейс
        self.frame = tk.Frame(parent)
        self.frame.pack()
        self.create_buttons()

    def create_buttons(self):
        for i in range(self.size):
            for j in range(self.size):
                num = self.sequence[i*self.size+j]
                color = "#f0f0f0" if num==0 else "#dcdcdc"
                btn = tk.Button(self.frame, text=str(num) if num!=0 else '',
                                relief="raised", borderwidth=3, background=color, foreground="#000", width=7, height=3,
                                command=lambda row=i, col=j: self.move(row, col))
                btn.grid(row=i, column=j)
                self.buttons[i][j] = btn

    def shuffle(self):
        random.shuffle(self.sequence)

    def move(self, row, col):
        if abs(row-self.empty_row)+abs(col-self.empty_col) == 1:
            value = self.sequence[row*self.size+col]
            self.sequence[self.empty_row*self.size+self.empty_col], self.sequence[row*self.size+col] = value, 0
            self.update_board()
            self.empty_row, self.empty_col = row, col
            if self.is_solved():
                print("Головоломка решена!")

    def is_solved(self):
        return all(str(i+1)==str(self.sequence[i]) or self.sequence[i]==0 for i in range(self.size**2))

    def update_board(self):
        for i in range(self.size):
            for j in range(self.size):
                val = self.sequence[i*self.size+j]
                self.buttons[i][j]['text'] = str(val) if val!=0 else ''

# Основная игра
class MainApp:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Колледж Винкс: Побег")
        self.parent.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.current_scene = None

        # Стартовое меню
        self.menu_frame = tk.Frame(parent)
        self.menu_frame.pack(expand=True, fill="both")

        # Приветствие
        title_label = tk.Label(self.menu_frame, text="Колледж Винкс: Побег", font=("Helvetica", 24))
        title_label.pack(pady=20)

        # Кнопки
        start_button = tk.Button(self.menu_frame, text="Начать игру с начала", command=self.start_new_game)
        start_button.pack(pady=10)

        load_button = tk.Button(self.menu_frame, text="Продолжить с сохранения", command=self.load_game)
        load_button.pack(pady=10)

        quit_button = tk.Button(self.menu_frame, text="Закрыть", command=self.quit_game)
        quit_button.pack(pady=10)

    def start_new_game(self):
        self.clear_current_view()
        prologue_scene()

    def clear_current_view(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def load_game(self):
        try:
            with open("save.json", "r") as f:
                saved_data = json.load(f)
                self.current_scene = Scene(saved_data["image_path"], saved_data["description"], saved_data["choices"])
                show_scene(self.current_scene)
        except FileNotFoundError:
            print("Нет сохранённого состояния.")

    def quit_game(self):
        self.parent.destroy()

# Кат-сцена
def prologue_scene():
    prologue_frame = tk.Frame(root)
    prologue_frame.pack(expand=True, fill="both")

    intro_text = """
    Ходит легенда, что в колледже \"Винкс\" обитает странная сущность, у которой нет имени. Тех, кто встречался с ней, больше никто не видел.
    Она проявляется только после 19:00, и у студентов второй смены есть ровно 10 минут, чтобы успеть покинуть здание колледжа.
    Студенточка Оксана учится во вторую смену. Сегодня она замешкалась, пытаясь найти пропуск в сумочке, и не успела выйти вовремя...
    Дверь оказалась закрытой, и теперь ей предстоит найти выход из этой ужасающей ситуации.
    """

    text_widget = tk.Text(prologue_frame, wrap="word", font=("Helvetica", 12))
    text_widget.insert(tk.END, intro_text)
    text_widget.pack(expand=True, fill="both")

    continue_button = tk.Button(prologue_frame, text="Продолжить", command=first_choice_screen)
    continue_button.pack(pady=10)

# Первый выбор пути
def first_choice_screen():
    choice_frame = tk.Frame(root)
    choice_frame.pack(expand=True, fill="both")

    location_desc = """
    Ты оказываешься в длинном коридоре колледжа. Свет мигает, воздух становится прохладным и влажным.
    Направо идет узкий проход, ведущий в темноту, прямо впереди закрыта дверь, слева видно лестницу наверх.
    Что будешь делать?
    """

    desc_widget = tk.Text(choice_frame, wrap="word", font=("Helvetica", 12))
    desc_widget.insert(tk.END, location_desc)
    desc_widget.pack(expand=True, fill="both")

    right_button = tk.Button(choice_frame, text="Повернуть направо", command=end_game_with_message)
    left_button = tk.Button(choice_frame, text="Повернуть налево", command=second_floor_screen)
    door_button = tk.Button(choice_frame, text="Попробовать открыть дверь", command=end_game_with_message)

    right_button.pack(pady=5)
    left_button.pack(pady=5)
    door_button.pack(pady=5)

# Концовка игры
def end_game_with_message(message):
    result_window = tk.Toplevel()
    result_window.title("Конец игры")
    result_text = tk.Text(result_window, wrap="word", font=("Helvetica", 12))
    result_text.insert(tk.END, message)
    result_text.pack(expand=True, fill="both")
    close_button = tk.Button(result_window, text="Закрыть", command=result_window.destroy)
    close_button.pack(pady=10)

# Второй этаж
def second_floor_screen():
    second_floor_frame = tk.Frame(root)
    second_floor_frame.pack(expand=True, fill="both")

    floor_desc = """
    Ты оказался на втором этаже. Справа от лестницы расположен кабинет №17, чуть дальше — тёмный зал (кабинет №22).
    Свет выключился, и вдали мерцают загадочные огоньки.
    Куда пойдешь?
    """

    desc_widget = tk.Text(second_floor_frame, wrap="word", font=("Helvetica", 12))
    desc_widget.insert(tk.END, floor_desc)
    desc_widget.pack(expand=True, fill="both")

    room17_button = tk.Button(second_floor_frame, text="Посмотреть кабинет №17", command=server_room_puzzle)
    room22_button = tk.Button(second_floor_frame, text="Посмотреть кабинет №22", command=notebooks_password_task)

    room17_button.pack(pady=5)
    room22_button.pack(pady=5)

# Мини-игра пятнашки
def server_room_puzzle():
    puzzle_root = tk.Tk()
    puzzle_app = PuzzleGame(puzzle_root)
    puzzle_root.mainloop()

# Пароли на ноутбуках
def notebooks_password_task():
    notebook_frame = tk.Frame(root)
    notebook_frame.pack(expand=True, fill="both")

    password_hint = """
    В ноутбуках найдены заметки преподавателей. Они общались друг с другом о спрятанном ключе.
    Чтобы продолжить, введи правильный пароль.
    """

    desc_widget = tk.Text(notebook_frame, wrap="word", font=("Helvetica", 12))
    desc_widget.insert(tk.END, password_hint)
    desc_widget.pack(expand=True, fill="both")

    entry_field = tk.Entry(notebook_frame)
    entry_field.pack(pady=10)

    submit_button = tk.Button(notebook_frame, text="Отправить", command=lambda: check_password(entry_field.get()))
    submit_button.pack(pady=5)

def check_password(password):
    correct_pass = "winxs_key"
    if password.lower() == correct_pass:
        print("Правильно! Следующая комната открыта.")
    else:
        print("Неправильный пароль.")

# Основная функция запуска
def main():
    global root
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
