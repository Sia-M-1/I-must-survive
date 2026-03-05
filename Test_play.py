import tkinter as tk
from PIL import Image, ImageTk
import random
import json
import os
from tkinter import messagebox

# Константы окна
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Класс для игры в пятнашки (пазл с проводами)
class WirePuzzle:
    def __init__(self, parent, on_complete):
        self.parent = parent
        self.on_complete = on_complete
        self.puzzle_window = tk.Toplevel(parent)
        self.puzzle_window.title("Почини провода")
        self.puzzle_window.geometry("400x400")
        
        # Создаем сетку 3x3 для пазла
        self.buttons = []
        self.empty_pos = (2, 2)  # Пустая клетка в правом нижнем углу
        self.tiles = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]  # 0 - пустая клетка
        
        self.create_puzzle()
        
    def create_puzzle(self):
        # Перемешиваем плитки
        for _ in range(20):
            self.random_move()
            
        # Создаем кнопки
        for i in range(3):
            row = []
            for j in range(3):
                if self.tiles[i][j] != 0:
                    btn = tk.Button(self.puzzle_window, text=str(self.tiles[i][j]), 
                                  width=10, height=5,
                                  command=lambda r=i, c=j: self.move_tile(r, c))
                else:
                    btn = tk.Button(self.puzzle_window, text="", 
                                  width=10, height=5, state="disabled")
                btn.grid(row=i, column=j, padx=2, pady=2)
                row.append(btn)
            self.buttons.append(row)
            
        tk.Label(self.puzzle_window, text="Собери провода по порядку от 1 до 8").grid(row=3, column=0, columnspan=3)
        
    def random_move(self):
        # Случайное перемещение
        moves = []
        if self.empty_pos[0] > 0: moves.append((-1, 0))
        if self.empty_pos[0] < 2: moves.append((1, 0))
        if self.empty_pos[1] > 0: moves.append((0, -1))
        if self.empty_pos[1] < 2: moves.append((0, 1))
        
        if moves:
            move = random.choice(moves)
            new_pos = (self.empty_pos[0] + move[0], self.empty_pos[1] + move[1])
            self.swap_tiles(self.empty_pos, new_pos)
            
    def move_tile(self, row, col):
        # Проверяем, можно ли переместить
        if (abs(row - self.empty_pos[0]) + abs(col - self.empty_pos[1])) == 1:
            self.swap_tiles((row, col), self.empty_pos)
            self.empty_pos = (row, col)
            self.update_buttons()
            
            # Проверяем победу
            if self.check_win():
                messagebox.showinfo("Успех!", "Провода подключены! Свет включился!")
                self.puzzle_window.destroy()
                self.on_complete()
                
    def swap_tiles(self, pos1, pos2):
        self.tiles[pos1[0]][pos1[1]], self.tiles[pos2[0]][pos2[1]] = \
            self.tiles[pos2[0]][pos2[1]], self.tiles[pos1[0]][pos1[1]]
            
    def update_buttons(self):
        for i in range(3):
            for j in range(3):
                if self.tiles[i][j] != 0:
                    self.buttons[i][j].config(text=str(self.tiles[i][j]), state="normal")
                else:
                    self.buttons[i][j].config(text="", state="disabled")
                    
    def check_win(self):
        target = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
        return self.tiles == target

# Класс для загадок сфинкса
class SphinxPuzzle:
    def __init__(self, parent, on_success, on_fail):
        self.parent = parent
        self.on_success = on_success
        self.on_fail = on_fail
        self.questions = [
            {
                "question": "Что можно увидеть с закрытыми глазами?",
                "answer": "сон"
            },
            {
                "question": "Что становится больше, если его отдать?",
                "answer": "долг"
            },
            {
                "question": "Что принадлежит вам, но другие пользуются этим чаще?",
                "answer": "имя"
            }
        ]
        self.current_question = 0
        self.show_question()
        
    def show_question(self):
        self.question_window = tk.Toplevel(self.parent)
        self.question_window.title("Загадка сфинкса")
        self.question_window.geometry("500x300")
        
        # Диалог с Ириной Идуардовной
        tk.Label(self.question_window, text="Ирина Идуардовна (андроид):", 
                font=("Helvetica", 14, "bold")).pack(pady=10)
        
        tk.Label(self.question_window, text=self.questions[self.current_question]["question"],
                font=("Helvetica", 12), wraplength=400).pack(pady=20)
        
        self.answer_entry = tk.Entry(self.question_window, width=30)
        self.answer_entry.pack(pady=10)
        
        tk.Button(self.question_window, text="Ответить",
                 command=self.check_answer).pack(pady=10)
                 
    def check_answer(self):
        answer = self.answer_entry.get().lower().strip()
        if answer == self.questions[self.current_question]["answer"]:
            self.current_question += 1
            if self.current_question >= len(self.questions):
                messagebox.showinfo("Успех!", 
                    "Ты ответила на все вопросы!\nПодсказка: в подвале есть запасной выход.")
                self.question_window.destroy()
                self.on_success()
            else:
                self.question_window.destroy()
                self.show_question()
        else:
            messagebox.showerror("Ошибка!", "Неверный ответ... Сущность поглощает тебя!")
            self.question_window.destroy()
            self.on_fail()

# Основной класс игры
class Game:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Колледж Винкс: Побег")
        self.parent.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Переменные состояния игры
        self.solved_puzzle = False
        self.has_museum_key = False
        self.has_basement_key = False
        self.sphinx_passed = False
        self.password_parts = []
        
        # Создаем главное меню
        self.show_main_menu()
        
    def show_main_menu(self):
        self.clear_window()
        
        # Фон главного меню
        try:
            img = Image.open("menu_bg.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="black")
            canvas.pack()
        
        # Заголовок
        canvas.create_text(WINDOW_WIDTH//2, 150, text="Колледж Винкс: Побег",
                          fill="white", font=("Helvetica", 36, "bold"))
        
        # Кнопки
        btn_frame = tk.Frame(self.parent, bg='black')
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Button(btn_frame, text="Начать новую игру", font=("Helvetica", 14),
                 command=self.start_new_game, width=20, height=2).pack(pady=10)
        tk.Button(btn_frame, text="Продолжить игру", font=("Helvetica", 14),
                 command=self.load_game, width=20, height=2).pack(pady=10)
        tk.Button(btn_frame, text="Выйти", font=("Helvetica", 14),
                 command=self.parent.quit, width=20, height=2).pack(pady=10)
    
    def start_new_game(self):
        self.clear_window()
        self.show_prologue()
    
    def show_prologue(self):
        self.clear_window()
        
        # Фон пролога
        try:
            img = Image.open("prologue_bg.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="darkblue")
            canvas.pack()
        
        # Текст пролога
        prologue_text = """Ходит легенда, что в колледже "Винкс" обитает странная сущность...
        
Она проявляет себя только после 19:00. У студентов второй смены есть ровно 10 минут,
чтобы покинуть здание.

Студенточка Оксана сегодня замешкалась, ища пропуск в своей бездонной сумочке...
19:00... Дверь закрылась. Теперь ей предстоит найти выход..."""
        
        text_widget = tk.Text(canvas, wrap="word", font=("Helvetica", 14),
                             bg="black", fg="white", width=60, height=10)
        text_widget.insert("1.0", prologue_text)
        text_widget.place(relx=0.5, rely=0.4, anchor="center")
        
        tk.Button(canvas, text="Продолжить", font=("Helvetica", 12),
                 command=self.first_floor).place(relx=0.5, rely=0.7, anchor="center")
    
    def first_floor(self):
        self.clear_window()
        
        # GIF анимация мигающего света
        try:
            self.frames = []
            for i in range(1, 5):
                img = Image.open(f"corridor_flash_{i}.png")
                img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
                self.frames.append(ImageTk.PhotoImage(img))
            
            self.current_frame = 0
            self.canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            self.canvas.pack()
            self.animate_flashing()
        except:
            self.canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="darkgray")
            self.canvas.pack()
        
        # Текст описания
        description = """Ты в коридоре первого этажа. Свет мигает... Слышны странные звуки.
Перед тобой несколько путей:"""
        
        self.canvas.create_text(WINDOW_WIDTH//2, 50, text=description,
                               fill="white", font=("Helvetica", 12), width=600)
        
        # Кнопки выбора
        btn_frame = tk.Frame(self.parent, bg='black')
        btn_frame.place(relx=0.5, rely=0.8, anchor="center")
        
        tk.Button(btn_frame, text="Повернуть налево", font=("Helvetica", 12),
                 command=self.second_floor, width=20).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Повернуть направо", font=("Helvetica", 12),
                 command=self.death_ending, width=20).pack(side="left", padx=10)  # ИСПРАВЛЕНО: добавил command=
        tk.Button(btn_frame, text="Попытаться открыть дверь", font=("Helvetica", 12),
                 command=self.try_door, width=20).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Зайти в столовую", font=("Helvetica", 12),
                 command=self.canteen, width=20).pack(side="left", padx=10)
    
    def animate_flashing(self):
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.parent.after(200, self.animate_flashing)
    
    def try_door(self):
        messagebox.showinfo("Дверь", "Дверь заперта снаружи... Похоже, придется искать другой выход.")
    
    def canteen(self):
        messagebox.showinfo("Столовая", "В столовой темно и пусто. Только перевернутые стулья намекают, что здесь кто-то был.")
    
    def death_ending(self):
        self.clear_window()
        try:
            img = Image.open("wolf.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="red")
            canvas.pack()
        
        canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2,
                          text="ТЫ ВСТРЕТИЛ СУЩНОСТЬ...\nКрасный волк поразил тебя энергетическим шаром.\n\nКОНЕЦ ИГРЫ",
                          fill="white", font=("Helvetica", 24, "bold"))
        
        tk.Button(self.parent, text="В главное меню", font=("Helvetica", 12),
                 command=self.show_main_menu).place(relx=0.5, rely=0.8, anchor="center")
    
    def second_floor(self):
        self.clear_window()
        
        try:
            img = Image.open("second_floor.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="gray")
            canvas.pack()
        
        canvas.create_text(WINDOW_WIDTH//2, 50, text="Ты на втором этаже. Перед тобой несколько кабинетов:",
                          fill="white", font=("Helvetica", 16))
        
        btn_frame = tk.Frame(self.parent, bg='black')
        btn_frame.place(relx=0.5, rely=0.8, anchor="center")
        
        tk.Button(btn_frame, text="Кабинет №17 (серверная)", font=("Helvetica", 12),
                 command=self.room_17, width=20).pack(pady=5)
        
        if self.solved_puzzle:
            tk.Button(btn_frame, text="Кабинет №22 (компьютерный класс)", font=("Helvetica", 12),
                     command=self.room_22, width=20).pack(pady=5)
            tk.Button(btn_frame, text="Музей", font=("Helvetica", 12),
                     command=self.museum, width=20).pack(pady=5)
        
        tk.Button(btn_frame, text="На третий этаж", font=("Helvetica", 12),
                 command=self.third_floor, width=20).pack(pady=5)
        tk.Button(btn_frame, text="Вернуться на первый этаж", font=("Helvetica", 12),
                 command=self.first_floor, width=20).pack(pady=5)
    
    def room_17(self):
        if not self.solved_puzzle:
            messagebox.showinfo("Серверная", "Ты видишь серверную с красным огоньком. На корпусе записка 'Помоги мне'")
            WirePuzzle(self.parent, self.puzzle_complete)
        else:
            messagebox.showinfo("Серверная", "Здесь уже всё исправно работает. Свет горит ярко.")
    
    def puzzle_complete(self):
        self.solved_puzzle = True
        messagebox.showinfo("Успех", "Свет в коридоре загорелся! Теперь видны другие кабинеты.")
        self.second_floor()
    
    def room_22(self):
        self.clear_window()
        
        try:
            img = Image.open("computer_class.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="lightgray")
            canvas.pack()
        
        canvas.create_text(WINDOW_WIDTH//2, 50, text="Компьютерный класс. Четыре ноутбука на столах.",
                          fill="white", font=("Helvetica", 16))
        
        btn_frame = tk.Frame(self.parent, bg='black')
        btn_frame.place(relx=0.5, rely=0.7, anchor="center")
        
        # Кнопки для компьютеров
        for i in range(1, 5):
            if i < 4:
                tk.Button(btn_frame, text=f"Компьютер {i} (написать код)", font=("Helvetica", 12),
                         command=lambda x=i: self.computer_task(x), width=20).pack(pady=5)
            else:
                if len(self.password_parts) == 3:
                    tk.Button(btn_frame, text=f"Компьютер {i} (ввести пароль)", font=("Helvetica", 12),
                             command=self.enter_password, width=20).pack(pady=5)
        
        # Ключ от музея
        if not self.has_museum_key:
            tk.Button(btn_frame, text="Осмотреть стол", font=("Helvetica", 12),
                     command=self.find_museum_key, width=20).pack(pady=5)
        
        tk.Button(btn_frame, text="Вернуться в коридор", font=("Helvetica", 12),
                 command=self.second_floor, width=20).pack(pady=5)
        
        # Чат преподавателей
        chat_frame = tk.Frame(self.parent, bg="white")
        chat_frame.place(relx=0.8, rely=0.2, anchor="center")
        tk.Label(chat_frame, text="Чат преподавателей:", bg="white").pack()
        tk.Label(chat_frame, text="Иван Петрович: Куда ты положил ключ?", bg="white").pack()
        tk.Label(chat_frame, text="Мария Ивановна: В кабинете на третьем этаже", bg="white").pack()
    
    def computer_task(self, num):
        self.password_parts.append(f"part{num}")
        messagebox.showinfo("Код написан", f"Ты получил часть пароля: часть {num}")
    
    def enter_password(self):
        password_window = tk.Toplevel(self.parent)
        password_window.title("Введите пароль")
        password_window.geometry("300x150")
        
        tk.Label(password_window, text="Введите пароль (части 1,2,3):").pack(pady=10)
        entry = tk.Entry(password_window)
        entry.pack(pady=5)
        
        def check():
            if entry.get() == "part1part2part3":
                messagebox.showinfo("Успех", "Пароль верный! Доступ к информации получен.")
                password_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Неверный пароль!")
        
        tk.Button(password_window, text="Проверить", command=check).pack(pady=5)
    
    def find_museum_key(self):
        self.has_museum_key = True
        messagebox.showinfo("Находка", "Ты нашла ключ от музея на столе!")
        self.room_22()
    
    def museum(self):
        if not self.has_museum_key:
            messagebox.showinfo("Музей", "Дверь заперта. Нужен ключ.")
            return
        
        SphinxPuzzle(self.parent, 
                    lambda: self.sphinx_success(),
                    lambda: self.death_ending())
    
    def sphinx_success(self):
        self.sphinx_passed = True
        self.second_floor()
    
    def third_floor(self):
        self.clear_window()
        
        try:
            img = Image.open("third_floor.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="darkgray")
            canvas.pack()
        
        canvas.create_text(WINDOW_WIDTH//2, 50, text="Третий этаж. Свет мигает...",
                          fill="white", font=("Helvetica", 16))
        canvas.create_text(WINDOW_WIDTH//2, 100, text="Виден только один открытый кабинет.",
                          fill="white", font=("Helvetica", 12))
        
        tk.Button(self.parent, text="Зайти в кабинет", font=("Helvetica", 12),
                 command=self.find_key_room).place(relx=0.5, rely=0.4, anchor="center")
        tk.Button(self.parent, text="Вернуться на второй этаж", font=("Helvetica", 12),
                 command=self.second_floor).place(relx=0.5, rely=0.6, anchor="center")
    
    def find_key_room(self):
        self.clear_window()
        
        try:
            img = Image.open("office.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="beige")
            canvas.pack()
        
        canvas.create_text(WINDOW_WIDTH//2, 50, text="На столе три документа. Под одним из них ключ.",
                          fill="white", font=("Helvetica", 16))
        
        btn_frame = tk.Frame(self.parent, bg='black')
        btn_frame.place(relx=0.5, rely=0.6, anchor="center")
        
        tk.Button(btn_frame, text="Взять документ 1", font=("Helvetica", 12),
                 command=lambda: self.check_key(1), width=20).pack(pady=5)
        tk.Button(btn_frame, text="Взять документ 2", font=("Helvetica", 12),
                 command=lambda: self.check_key(2), width=20).pack(pady=5)
        tk.Button(btn_frame, text="Взять документ 3", font=("Helvetica", 12),
                 command=lambda: self.check_key(3), width=20).pack(pady=5)
    
    def check_key(self, num):
        if num == 2:  # Правильный документ
            self.has_basement_key = True
            messagebox.showinfo("Успех!", "Ты нашла ключ от запасного выхода в подвале!")
            self.basement()
        else:
            messagebox.showerror("Ошибка!", "Это просто документ... Сущность настигла тебя!")
            self.death_ending()
    
    def basement(self):
        self.clear_window()
        
        try:
            img = Image.open("basement.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="black")
            canvas.pack()
        
        canvas.create_text(WINDOW_WIDTH//2, 100, text="Ты в подвале. Впереди видна дверь.",
                          fill="white", font=("Helvetica", 16))
        
        if self.has_basement_key:
            tk.Button(self.parent, text="Открыть дверь (есть ключ)", font=("Helvetica", 12),
                     command=self.good_ending).place(relx=0.5, rely=0.5, anchor="center")
        else:
            canvas.create_text(WINDOW_WIDTH//2, 200, text="Дверь заперта. Нужен ключ.",
                              fill="red", font=("Helvetica", 14))
        
        tk.Button(self.parent, text="Вернуться на второй этаж", font=("Helvetica", 12),
                 command=self.second_floor).place(relx=0.5, rely=0.7, anchor="center")
    
    def good_ending(self):
        self.clear_window()
        
        try:
            img = Image.open("ending.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="lightblue")
            canvas.pack()
        
        ending_text = """Ты открываешь дверь и выходишь на свежий воздух!
        
Сущность осталась позади. Ты смогла выбраться из колледжа живой.

ПОБЕДА!

Спасибо за игру!"""
        
        canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50,
                          text=ending_text, fill="white", font=("Helvetica", 18),
                          width=600)
        
        # Титры
        credits = """Создатель игры: Твоё имя
        Вдохновлено легендами о колледже Винкс
        
        КОНЕЦ"""
        
        canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 100,
                          text=credits, fill="white", font=("Helvetica", 12))
        
        tk.Button(self.parent, text="В главное меню", font=("Helvetica", 12),
                 command=self.show_main_menu).place(relx=0.5, rely=0.9, anchor="center")
    
    def clear_window(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
    
    def load_game(self):
        try:
            with open("save.json", "r") as f:
                saved_data = json.load(f)
                self.solved_puzzle = saved_data["solved_puzzle"]
                self.has_museum_key = saved_data["has_museum_key"]
                self.has_basement_key = saved_data["has_basement_key"]
                self.sphinx_passed = saved_data["sphinx_passed"]
                self.password_parts = saved_data["password_parts"]
                messagebox.showinfo("Загрузка", "Игра загружена!")
                self.first_floor()
        except:
            messagebox.showerror("Ошибка", "Нет сохранений!")

# Запуск игры
if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()
