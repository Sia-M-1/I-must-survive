import tkinter as tk
from PIL import Image, ImageTk
import random
import json

# Константы окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Класс сцены
class Scene:
    def __init__(self, image_path, description, choices):
        self.image = Image.open(image_path)
        self.description = description
        self.choices = choices

# Главная игра
class MainApp:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Колледж Винкс: Побег")
        self.parent.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.current_scene = None

        # Главное меню
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

    continue_button = tk.Button(prologue_frame, text="Продолжить", command=lambda: (
        prologue_frame.destroy(), first_choice_screen()
    ))
    continue_button.pack(pady=10)

# Функция отображения сцены
def show_scene(scene):
    scene_frame = tk.Frame(root)
    scene_frame.pack(expand=True, fill="both")

    # Картинка верхней части экрана
    img = ImageTk.PhotoImage(scene.image)
    canvas = tk.Canvas(scene_frame, width=WINDOW_WIDTH, height=int(WINDOW_HEIGHT * 0.6))
    canvas.create_image(0, 0, anchor="nw", image=img)
    canvas.img = img  # Чтобы не потерять ссылку
    canvas.pack()

    # Текстовая область и кнопки
    bottom_frame = tk.Frame(scene_frame)
    bottom_frame.pack(expand=True, fill="both")

    text_widget = tk.Text(bottom_frame, wrap="word", font=("Helvetica", 12))
    text_widget.insert(tk.END, scene.description)
    text_widget.pack(expand=True, fill="both")

    # Добавляем кнопки выбора
    for choice_text, next_scene in scene.choices.items():
        btn = tk.Button(bottom_frame, text=choice_text, command=lambda s=next_scene: show_scene(s))
        btn.pack(side="left", padx=5)

# Первый выбор пути
def first_choice_screen():
    choice_frame = tk.Frame(root)
    choice_frame.pack(expand=True, fill="both")

    location_desc = """
    Ты оказываешься в длинном коридоре колледжа. Свет мигает, воздух становится прохладным и влажным.
    Направо идет узкий проход, ведущий в темноту, прямо впереди закрыта дверь, слева видно лестницу наверх.
    Что будешь делать?
    """

    corridor_image = Image.open("corridor.png")  # картинка коридора
    scene = Scene(corridor_image, location_desc, {
        "Повернуть направо": Scene(None, "", {}),  # Действия тут заглушены
        "Повернуть налево": Scene(None, "", {}),  # Действия тут заглушены
        "Попробовать открыть дверь": Scene(None, "", {})
    })

    show_scene(scene)

# Основной цикл
def main():
    global root
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
