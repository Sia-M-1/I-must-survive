import tkinter as tk
from PIL import Image, ImageTk
import random
import json
import os
from tkinter import messagebox
import time
from tkinter.font import Font

# Размеры окна
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650

# Глобальная переменная для хранения ссылок на шрифты
global_fonts = {}

# Разрыв текста автоматически для удобочитаемости
def split_long_text(text, max_length=20):
    words = text.split(' ')
    result = ''
    current_line = ''
    for word in words:
        if len(current_line) + len(word) <= max_length:
            current_line += word + ' '
        else:
            result += current_line.strip() + '\n'
            current_line = word + ' '
    result += current_line.strip()
    return result

# Класс для игры в пятнашки (серверная комната)
class WirePuzzle:
    def __init__(self, parent, on_complete):
        from random import shuffle
        
        self.parent = parent
        self.on_complete = on_complete
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # ПРОВЕРКА: выводим все PNG файлы в директории
        print("\n=== Поиск файлов для пятнашков ===")
        print(f"Директория: {self.current_dir}")
        for file in os.listdir(self.current_dir):
            if file.lower().endswith('.png'):
                print(f"Найден PNG: {file}")
        print("================================\n")

        # Создаем окно для пятнашков
        self.puzzle_window = tk.Toplevel(parent)
        self.puzzle_window.title("🔧 Серверная - Ремонт проводов")
        self.puzzle_window.geometry("350x520")
        self.puzzle_window.configure(bg='#1a2a3a')
        self.puzzle_window.resizable(False, False)
        
        # Используем шрифты из глобальной переменной
        try:
            self.title_font = global_fonts['large']
            self.text_font = global_fonts['small']
        except:
            # Если шрифты не определены, создаем свои
            from tkinter.font import Font
            self.title_font = Font(family="Arial", size=14, weight="bold")
            self.text_font = Font(family="Arial", size=12, weight="bold")
        
        # Заголовок
        title_frame = tk.Frame(self.puzzle_window, bg='#2a3a4a', height=50)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="🔧 СОЕДИНИ ПРОВОДА 🔧", 
                font=self.title_font, bg='#2a3a4a', fg='#ffd700').pack(pady=10)
        
        # Описание
        desc_label = tk.Label(self.puzzle_window, 
                             text="Собери картинку, чтобы восстановить питание серверной",
                             font=self.text_font, bg='#1a2a3a', fg='white', wraplength=300)
        desc_label.pack(pady=5)
        
        # Проверяем наличие файлов
        self.check_image_files()
        
        # Список изображений
        image_files = ['img1.png', 'img3.png', 'img4.png', 'img5.png', 
                      'img6.png', 'img7.png', 'img8.png', 'img9.png']
        
        # Загружаем изображения
        self.images = []
        self.image_paths = []
        
        for filename in image_files:
            img_path = os.path.join(self.current_dir, filename)
            self.image_paths.append(img_path)
            print(f"Проверяем файл: {img_path}")
            
            try:
                if os.path.exists(img_path):
                    print(f"Файл найден: {filename}")
                    pil_image = Image.open(img_path)
                    # Изменяем размер до 90x90 для лучшей видимости
                    pil_image = pil_image.resize((90, 90), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_image)
                    self.images.append(photo)
                else:
                    print(f"Файл НЕ найден: {filename}")
                    # Создаем заглушку с именем файла
                    self.images.append(self.create_placeholder(filename))
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")
                self.images.append(self.create_placeholder(filename))
        
        # Создаем пустую плитку
        self.empty_image = self.create_empty_tile()
        
        # Фрейм для игрового поля
        game_frame = tk.Frame(self.puzzle_window, bg='#2a3a4a', padx=10, pady=10)
        game_frame.pack(pady=10)
        
        # Начальное расположение плиток (img1.png закреплена)
        self.board = [0]  # Первая плитка на позиции 0
        remaining = list(range(1, 8))
        shuffle(remaining)
        self.board.extend(remaining)
        self.board.append(None)  # Пустая плитка
        
        self.empty_idx = self.board.index(None)
        print(f"Начальная доска: {self.board}")
        print(f"Пустая клетка на позиции: {self.empty_idx}")
        
        # Создаем кнопки-плитки
        self.buttons = []
        for i in range(9):
            if i == 0:
                # Первая плитка закреплена
                btn = tk.Button(game_frame, image=self.get_image(i), state=tk.DISABLED,
                               width=90, height=90, relief='ridge', bd=2)
            else:
                btn = tk.Button(game_frame, image=self.get_image(i),
                               command=lambda idx=i: self.move(idx),
                               width=90, height=90, relief='ridge', bd=2)
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)
            self.buttons.append(btn)
        
        # Кнопка закрытия
        close_btn = tk.Button(self.puzzle_window, text="✖ Закрыть", 
                             font=self.text_font, bg='#6a4a4a', fg='white',
                             command=self.puzzle_window.destroy)
        close_btn.pack(pady=5)
        
        # Подсказка
        hint_label = tk.Label(self.puzzle_window, 
                             text="Подсказка: левый верхний угол не двигается\n",
                             font=self.text_font, bg='#1a2a3a', fg='#888888')
        hint_label.pack(pady=5)
    
    def check_image_files(self):
        """Проверяет наличие файлов изображений"""
        print(f"Текущая директория: {self.current_dir}")
        print("Файлы в директории:")
        try:
            for file in os.listdir(self.current_dir):
                if file.endswith('.png'):
                    print(f"  Найден PNG: {file}")
        except:
            print("  Не удалось прочитать директорию")
    
    def create_placeholder(self, filename):
        """Создает заглушку для отсутствующего изображения"""
        img = Image.new('RGB', (90, 90), color='#4a4a4a')
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 89, 89], outline='white', width=2)
        
        # Пытаемся загрузить шрифт
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Отображаем имя файла без расширения
        text = filename.replace('.png', '')
        draw.text((10, 35), text, fill='white', font=font)
        
        return ImageTk.PhotoImage(img)
    
    def create_empty_tile(self):
        """Создает изображение пустой плитки"""
        img = Image.new('RGB', (90, 90), color='#1a2a3a')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 89, 89], outline='gray', width=2)
        return ImageTk.PhotoImage(img)
    
    def move(self, index):
        """Перемещает плитку"""
        if index == 0:  # Первая плитка не двигается
            return
        
        empty_row, empty_col = self.empty_idx // 3, self.empty_idx % 3
        curr_row, curr_col = index // 3, index % 3
        
        # Проверяем соседство
        if (abs(curr_row - empty_row) == 1 and curr_col == empty_col) or \
           (abs(curr_col - empty_col) == 1 and curr_row == empty_row):
            
            # Меняем местами
            self.board[index], self.board[self.empty_idx] = self.board[self.empty_idx], self.board[index]
            
            # Обновляем изображения
            self.buttons[index].config(image=self.get_image(index))
            self.buttons[self.empty_idx].config(image=self.get_image(self.empty_idx))
            
            self.empty_idx = index
            
            # ВРЕМЕННО: всегда победа после первого хода (замените на оригинал позже)
            messagebox.showinfo("✅ Успех!", "Свет в коридоре загорелся! Электричество восстановлено!")
            self.puzzle_window.destroy()
            self.on_complete()
            return
            
            # Проверяем победу
            # if self.board == [0, None, 1, 2, 3, 4, 5, 6, 7]:
            #     messagebox.showinfo("✅ Успех!", "Свет в коридоре загорелся! Электричество восстановлено!")
            #     self.puzzle_window.destroy()
            #     self.on_complete()
    
    def get_image(self, index):
        """Возвращает изображение для позиции"""
        if self.board[index] is None:
            return self.empty_image
        return self.images[self.board[index]]

# Класс для загадок сфинкса
class SphinxPuzzle:
    def __init__(self, parent, on_success, on_fail):
        self.parent = parent
        self.on_success = on_success
        self.on_fail = on_fail
        self.questions = [
            {"question": "Что можно увидеть с закрытыми глазами?", "answer": "сон"},
            {"question": "Что становится больше, если его отдать?", "answer": "долг"},
            {"question": "Что принадлежит вам, но другие пользуются этим чаще?", "answer": "имя"}
        ]
        self.current_question = 0
        self.show_question()

    def show_question(self):
        self.question_window = tk.Toplevel(self.parent)
        self.question_window.title("Загадка сфинкса")
        self.question_window.geometry("600x400")
        self.question_window.configure(bg='#2a1a2a')

        # Заголовок
        name_label = tk.Label(self.question_window, text="🤖 Ирина Идуардовна (андроид) 🤖",
                            font=global_fonts['large'], bg='#2a1a2a', fg='#ff99ff')
        name_label.pack(pady=20)

        question_frame = tk.Frame(self.question_window, bg='#3a2a3a', padx=20, pady=20)
        question_frame.pack(pady=20)

        question_label = tk.Label(question_frame, text=self.questions[self.current_question]["question"],
                                font=global_fonts['small'], bg='#3a2a3a', fg='white', wraplength=400)
        question_label.pack()

        self.answer_entry = tk.Entry(self.question_window, width=30, font=global_fonts['small'])
        self.answer_entry.pack(pady=10)

        tk.Button(self.question_window, text="📝 Ответить", font=global_fonts['small'],
                  bg='#4a3a4a', fg='white', command=self.check_answer).pack(pady=10)

    def check_answer(self):
        answer = self.answer_entry.get().lower().strip()
        if answer == self.questions[self.current_question]["answer"]:
            self.current_question += 1
            if self.current_question >= len(self.questions):
                messagebox.showinfo("🎉 Успех! 🎉", "Ты ответил на все вопросы!\n")
                self.question_window.destroy()
                self.on_success()
            else:
                self.question_window.destroy()
                self.show_question()
        else:
            messagebox.showerror("💀 Ошибка! 💀", "Неверный ответ... Сущность поглощает тебя!")
            self.question_window.destroy()
            self.on_fail()

# Класс для просмотра документов
class DocumentViewer:
    def __init__(self, parent, on_choice):
        self.parent = parent
        self.on_choice = on_choice
        self.viewer_window = tk.Toplevel(parent)
        self.viewer_window.title("Документы")
        self.viewer_window.geometry("700x500")
        self.viewer_window.configure(bg='#2b2b2b')

        # Заголовок
        title_label = tk.Label(self.viewer_window, text="📄 ТРИ ДОКУМЕНТА НА СТОЛЕ 📄",
                            font=global_fonts['large'], bg='#2b2b2b', fg='#ffd700')
        title_label.pack(pady=10)

        # Создаем фрейм для документов с прокруткой
        container = tk.Frame(self.viewer_window, bg='#3b3b3b')
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Canvas для прокрутки
        canvas = tk.Canvas(container, bg='#3b3b3b', highlightthickness=0)
        canvas.pack(side="top", fill="both", expand=True)

        # Горизонтальный скроллбар
        scrollbar = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scrollbar.pack(side="bottom", fill="x")

        # Настраиваем canvas
        canvas.configure(xscrollcommand=scrollbar.set)

        # Фрейм внутри canvas для документов
        docs_frame = tk.Frame(canvas, bg='#3b3b3b')
        canvas.create_window((0, 0), window=docs_frame, anchor="nw")

        # Три документа
        for i in range(1, 4):
            doc_frame = tk.Frame(docs_frame, bg='#4b4b4b', relief="raised", bd=3)
            doc_frame.pack(side="left", padx=10, pady=10)

            # Изображение документа
            try:
                img = Image.open(f"document_{i}.png")
                img = img.resize((180, 200))
                doc_img = ImageTk.PhotoImage(img)
                img_label = tk.Label(doc_frame, image=doc_img, bg='#4b4b4b')
                img_label.image = doc_img
                img_label.pack(pady=10)
            except:
                # Замещающий текст
                text_label = tk.Label(doc_frame, text=f"ДОКУМЕНТ {i}\n\n[Здесь должно быть изображение документа]",
                                    font=global_fonts['small'], bg='#4b4b4b', fg='white')
                text_label.pack(pady=20)

            # Кнопки для документа
            btn_frame = tk.Frame(doc_frame, bg='#4b4b4b')
            btn_frame.pack(pady=10)

            # Фиксируем значение i для каждой кнопки (чтобы избежать проблемы с lambda)
            doc_num = i

            tk.Button(btn_frame, text="👁️ Просмотреть", font=global_fonts['small'],
                bg='#5b5b5b', fg='white', command=lambda x=doc_num: self.view_document(x)).pack(side="left", padx=5)

            tk.Button(btn_frame, text="✅ Выбрать", font=global_fonts['small'],
                bg='#6b8e23', fg='white', command=lambda x=doc_num: self.choose_document(x)).pack(side="left", padx=5)

        # Обновляем область прокрутки
        docs_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def view_document(self, num):
        view_window = tk.Toplevel(self.viewer_window)
        view_window.title(f"Документ {num}")
        view_window.geometry("500x600")
        view_window.configure(bg='#f4e4c1')

        # Контент документа
        tk.Label(view_window, text=f"ДОКУМЕНТ №{num}",
            font=global_fonts['large'], bg='#f4e4c1', fg='#8b4513').pack(pady=10)

        try:
            # Пытаемся открыть картинку
            img = Image.open(f"document_{num}.png")
            
            # Увеличиваем размер для просмотра
            img = img.resize((450, 500), Image.Resampling.LANCZOS)
            doc_img = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(view_window, image=doc_img, bg='#f4e4c1')
            img_label.image = doc_img
            img_label.pack(pady=10, padx=10)
        
        except Exception as e:
            print(f"Ошибка загрузки документа {num}: {e}")
            # Если картинка не найдена, показываем текст
            text_widget = tk.Text(view_window, wrap="word", font=Font(family="Courier", size=12),
                             bg='#fff4e0', fg='#000000', padx=20, pady=20)
            text_widget.pack(expand=True, fill="both", padx=20, pady=20)

            if num == 2:
                text_widget.insert("1.0", "Это важный документ!\n\nПод ним лежит ключ от подвала.")
            else:
                text_widget.insert("1.0", f"Обычный документ №{num}\n\nЗдесь нет ничего интересного...")
            text_widget.config(state="disabled")
        
        # Кнопка закрытия
        tk.Button(view_window, text="✖ Закрыть", font=global_fonts['small'],
             bg='#8b4513', fg='white', command=view_window.destroy).pack(pady=10)

    def choose_document(self, num):
        if messagebox.askyesno("Подтверждение", f"Точно выбрать документ {num}?"):
            self.viewer_window.destroy()
            self.on_choice(num)
            
# Основной класс игры
class Game:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Выжить обязан")
        self.parent.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        # Создание шрифтов только после создания корневого окна
        global_fonts['small'] = Font(family="Arial", size=12, weight="bold")
        global_fonts['large'] = Font(family="Arial", size=14, weight="bold")

        # Переменные состояния игры
        self.solved_puzzle = False
        self.has_museum_key = False
        self.has_basement_key = False
        self.sphinx_passed = False
        self.password_parts = []
        self.current_location = "main_menu"
        
        # Стили кнопок
        self.button_style = {
            'font': global_fonts['small'],
            'bg': '#4a4a4a',
            'fg': 'white',
            'activebackground': '#6a6a6a',
            'activeforeground': 'white',
            'relief': 'flat',
            'highlightthickness': 1,
            'borderwidth': 0,
        }

        self.big_button_style = self.button_style.copy()
        self.big_button_style['font'] = global_fonts['large']
        self.big_button_style['padx'] = 10
        self.big_button_style['pady'] = 10

        # Создаем панель сохранения
        self.create_save_panel()
        
        # Начало с главного меню
        self.show_main_menu()

    def create_save_panel(self):
        """Создает постоянную панель с кнопкой сохранения"""
        self.save_panel = tk.Frame(self.parent, bg='#2a3a4a', height=40)
        self.save_panel.pack(side="bottom", fill="x")
        self.save_panel.pack_propagate(False)
        
        save_btn = tk.Button(self.save_panel, 
                            text="💾 СОХРАНИТЬ ИГРУ", 
                            font=global_fonts['small'],
                            bg='#4a6a8a', 
                            fg='white',
                            activebackground='#5a7a9a',
                            activeforeground='white',
                            command=self.save_game,
                            width=20,
                            height=1,
                            relief='raised',
                            bd=2)
        save_btn.pack(pady=5)

    def clear_window(self):
        """Очистка окна от всех виджетов, но сохраняет панель сохранения."""
        for widget in self.parent.winfo_children():
            if widget != self.save_panel:
                widget.destroy()

    def show_main_menu(self):
        self.current_location = "main_menu"
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
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#1a2a3a")
            canvas.pack()

        # Заголовок
        canvas.create_text(WINDOW_WIDTH//2, 150, text="ВЫЖИТЬ ОБЯЗАН",
                          fill="white", font=global_fonts['large'])
        canvas.create_text(WINDOW_WIDTH//2, 200, text="Колледж Винкс",
                          fill="#ff9999", font=global_fonts['small'])

        # Кнопки
        btn_frame = tk.Frame(self.parent, bg='#1a2a3a')
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(btn_frame, text="🌟 Начать новую игру", **self.big_button_style, command=self.start_new_game).pack(pady=10)
        tk.Button(btn_frame, text="💾 Продолжить игру", **self.big_button_style, command=self.load_game).pack(pady=10)
        tk.Button(btn_frame, text="🚪 Выйти", **self.big_button_style, command=self.parent.quit).pack(pady=10)

    def start_new_game(self):
        # Сбрасываем состояние игры
        self.solved_puzzle = False
        self.has_museum_key = False
        self.has_basement_key = False
        self.sphinx_passed = False
        self.password_parts = []
        self.current_location = "prologue"
        
        self.clear_window()
        self.show_prologue()

    def show_prologue(self):
        self.current_location = "prologue"
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
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#1a2a3a")
            canvas.pack()

        # Текст пролога с оформлением
        prologue_text = """Ходит легенда, что в колледже \"Винкс\" обитает странная сущность...
        
Она проявляется только после 19:00. Студентам даётся всего лишь 10 минут,
чтобы успеть выйти из здания.

Сегодня студентка Оксана задержалась, пытаясь найти пропавший пропуск в своей сумке.
Сейчас 19:00... Дверь захлопнулась. Ей предстоит выжить и найти путь наружу..."""

        # Полупрозрачный фон для текста
        text_bg = tk.Frame(canvas, bg='black')
        text_bg.place(relx=0.5, rely=0.4, anchor="center", width=600, height=250)

        text_widget = tk.Text(text_bg, wrap="word", font=global_fonts['small'],
                             bg="#000000", fg="#ffffff", width=60, height=10, bd=0)
        text_widget.insert("1.0", prologue_text)
        text_widget.pack(padx=10, pady=10)

        tk.Button(canvas, text="▶ Продолжить", font=global_fonts['large'],
                 bg="#4a6a8a", fg="white", activebackground="#5a7a9a", command=self.first_floor).place(relx=0.5, rely=0.7, anchor="center")

    def first_floor(self):
        self.current_location = "first_floor"
        self.clear_window()

        # Анимация мигающего света (чередование двух картинок)
        try:
            self.frames = []
            # Загружаем две картинки
            for i in range(1, 3):
                img = Image.open(f"corridor_flash_{i}.png")
                img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
                self.frames.append(ImageTk.PhotoImage(img))

            self.current_frame = 0
            self.canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            self.canvas.pack()
            self.animate_flashing()
        except:
            # Имитация мигания
            self.canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="gray")
            self.canvas.pack()
            self.flash_color = True
            self.animate_simple_flashing()

        # Текст описания с фоном
        desc_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        desc_bg.place(relx=0.5, rely=0.2, anchor="center")

        description = "Ты находишься в коридоре первого этажа. Свет периодически мерцает..."
        desc_label = tk.Label(desc_bg, text=split_long_text(description), font=global_fonts['small'], bg='black', fg='white')
        desc_label.pack(padx=20, pady=10)

        # Кнопки выбора
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.7, anchor="center")

        buttons = [
            ("⬅ Повернуть налево (на второй этаж)", self.second_floor),
            ("➡ Повернуть направо", self.death_ending),
            ("🚪 Попробовать открыть дверь", self.try_door),
            ("🍽 Зайти в столовую", self.canteen),
        ]
        
        # На первом этаже нет кнопки в подвал - подвал только со второго этажа!

        for text, command in buttons:
            btn = tk.Button(btn_frame, text=split_long_text(text), command=command, **self.button_style)
            btn.pack(pady=5)

    def animate_flashing(self):
        if hasattr(self, 'canvas') and self.frames:
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.parent.after(300, self.animate_flashing)

    def animate_simple_flashing(self):
        if hasattr(self, 'canvas'):
            if self.flash_color:
                self.canvas.configure(bg='white')
            else:
                self.canvas.configure(bg='gray')
            self.flash_color = not self.flash_color
            self.parent.after(300, self.animate_simple_flashing)

    def try_door(self):
        messagebox.showinfo("🚪 Дверь", "Дверь закрыта извне... Видимо, придётся искать другой выход.")

    def canteen(self):
        messagebox.showinfo("🍽 Столовая", "В столовой темно и пусто. Здесь недавно были студенты.")

    def death_ending(self):
        self.current_location = "death"
        self.clear_window()
        try:
            img = Image.open("wolf.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#330000")
            canvas.pack()

            # Символический рисунок волка
            canvas.create_text(400, 300, text="🐺", font=global_fonts['large'], fill="red")

        canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2,
                          text="💀 ТЫ ВСТРЕТИЛ СУЩНОСТЬ... 💀\n\nКрасный волк поражает тебя мощным зарядом энергии.\n\nКОНЕЦ ИГРЫ",
                          fill="white", font=global_fonts['large'], justify="center")

        tk.Button(self.parent, text="🏠 В главное меню", font=global_fonts['large'],
                 bg="#4a4a4a", fg="white", command=self.show_main_menu).place(relx=0.5, rely=0.8, anchor="center")

    def second_floor(self):
        self.current_location = "second_floor"
        self.clear_window()

        # Выбираем фон в зависимости от прохождения пятнашков
        if self.solved_puzzle:
            # Светлый второй этаж (после прохождения)
            try:
                img = Image.open("second_floor.png")
            except:
                img = None
        else:
            # Темный второй этаж (до прохождения)
            try:
                img = Image.open("second_floor_dark.png")
            except:
                img = None

        if img:
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        else:
            # Запасной вариант, если картинки нет
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, 
                            bg="#2a2a2a" if self.solved_puzzle else "#1a1a1a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2,
                            text="📚 ВТОРОЙ ЭТАЖ 📚\n" + ("☀️" if self.solved_puzzle else "🌑"),
                            fill="white", font=global_fonts['large'])

        

        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Button(btn_frame, text="🔧 Кабинет №17 (серверная)",
                 command=lambda: WirePuzzle(self.parent, self.puzzle_complete), **self.button_style).pack(pady=5)
        
        if self.solved_puzzle:
            tk.Button(btn_frame, text="💻 Кабинет №22 (комп. класс)", command=self.room_22, **self.button_style).pack(pady=5)
            tk.Button(btn_frame, text="🏛 Музей", command=self.museum, **self.button_style).pack(pady=5)

        # Кнопки перемещения
        tk.Button(btn_frame, text="⬆ На третий этаж", command=self.third_floor, **self.button_style).pack(pady=5)
        tk.Button(btn_frame, text="⬇ На первый этаж", command=self.first_floor, **self.button_style).pack(pady=5)
        
        # Кнопка в подвал - доступна всегда со второго этажа (без ключа можно зайти, но не выйти)
        tk.Button(btn_frame, text="🏚 Спуститься в подвал", command=self.basement, **self.button_style).pack(pady=5)
    
    
    def puzzle_complete(self):
        self.solved_puzzle = True
        self.second_floor()

    def room_22(self):
        self.current_location = "room_22"
        self.clear_window()

        try:
            img = Image.open("computer_class.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#2b2b2b")
            canvas.pack()

        canvas.create_text(WINDOW_WIDTH//2, 50, text="💻 КОМПЬЮТЕРНЫЙ КЛАСС 💻",
                          fill="white", font=global_fonts['large'])

        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Кнопки для компьютеров
        for i in range(1, 4):
            status = "✅" if f"part{i}" in self.password_parts else "⬜"
            tk.Button(btn_frame, text=f"{status} Компьютер {i} (написать код)",
                     font=global_fonts['small'], bg='#4a4a4a', fg='white',
                     command=lambda x=i: self.computer_task(x), width=25, height=1).pack(pady=2)

        if len(self.password_parts) == 3:
            tk.Button(btn_frame, text="🔑 Компьютер 4 (ввести пароль)",
                     font=global_fonts['small'], bg='#6b8e23', fg='white',
                     command=self.enter_password, width=25, height=1).pack(pady=5)

        # Ключ от музея
        if not self.has_museum_key:
            tk.Button(btn_frame, text="🔍 Осмотреть стол (найти ключ от музея)",
                     font=global_fonts['small'], bg='#b8860b', fg='white',
                     command=self.find_museum_key, width=25, height=1).pack(pady=5)

        tk.Button(btn_frame, text="◀ Вернуться в коридор", command=self.second_floor, **self.button_style).pack(pady=5)

        # Чат преподавателей
        chat_frame = tk.Frame(self.parent, bg="white", bd=2, relief="solid")
        chat_frame.place(relx=0.8, rely=0.2, anchor="center")

        tk.Label(chat_frame, text="💬 Чат преподавателей:",
                font=global_fonts['small'], bg="white").pack()
        tk.Label(chat_frame, text="Иван Петрович: Куда ты положил ключ?",
                font=global_fonts['small'], bg="white").pack()
        tk.Label(chat_frame, text="Мария Ивановна: В кабинете на третьем этаже",
                font=global_fonts['small'], bg="white").pack()

    def computer_task(self, num):
        if f"part{num}" not in self.password_parts:
            self.password_parts.append(f"part{num}")
            messagebox.showinfo("💻 Код написан", f"Ты написала код на компьютере {num}!\nПолучена часть пароля.")
        else:
            messagebox.showinfo("💻 Компьютер", "Здесь уже всё готово.")
        self.room_22()

    def enter_password(self):
        password_window = tk.Toplevel(self.parent)
        password_window.title("🔑 Введите пароль")
        password_window.geometry("350x200")
        password_window.configure(bg='#2a2a2a')

        tk.Label(password_window, text="ВВЕДИТЕ ПАРОЛЬ",
                font=global_fonts['large'], bg='#2a2a2a', fg='#ffd700').pack(pady=10)
        tk.Label(password_window, text="(части 1,2,3)",
                font=global_fonts['small'], bg='#2a2a2a', fg='#888888').pack()

        entry = tk.Entry(password_window, width=30, font=global_fonts['small'], show="*")
        entry.pack(pady=10)

        def check():
            if entry.get() == "part1part2part3":
                messagebox.showinfo("✅ Успех", "Пароль верный! Доступ к информации получен.")
                password_window.destroy()
            else:
                messagebox.showerror("❌ Ошибка", "Неверный пароль!")

        tk.Button(password_window, text="Проверить", font=global_fonts['small'],
                 bg='#4a4a4a', fg='white', command=check).pack(pady=10)

    def find_museum_key(self):
        self.has_museum_key = True
        messagebox.showinfo("🔑 Находка", "Ты нашла ключ от музея на столе!")
        self.room_22()

    def museum(self):
        if not self.has_museum_key:
            messagebox.showinfo("🏛 Музей", "Дверь заперта. Нужен ключ.")
            return

        SphinxPuzzle(self.parent,
                    lambda: self.sphinx_success(),
                    lambda: self.death_ending())

    def sphinx_success(self):
        self.sphinx_passed = True
        self.second_floor()

    def third_floor(self):
        self.current_location = "third_floor"
        self.clear_window()

        try:
            img = Image.open("third_floor.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#1a1a2a")
            canvas.pack()

        canvas.create_text(WINDOW_WIDTH//2, 50, text="⬆ ТРЕТИЙ ЭТАЖ ⬆",
                          fill="white", font=global_fonts['large'])

        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.4, anchor="center")

        # Кабинет на третьем этаже виден ТОЛЬКО если пройдены все кабинеты на втором этаже
        # Проверяем, что все кабинеты на втором этаже пройдены
        all_second_floor_complete = self.solved_puzzle and self.has_museum_key and self.sphinx_passed
        
        if all_second_floor_complete:
            tk.Button(btn_frame, text="📁 Зайти в кабинет", command=self.find_key_room, **self.button_style).pack(pady=5)
        else:
            # Показываем заглушку или просто не показываем кнопку
            tk.Label(btn_frame, text="❌ Кабинет закрыт\n",
                    font=global_fonts['small'], bg='black', fg='#888888').pack(pady=5)
        
        tk.Button(btn_frame, text="⬇ На второй этаж", command=self.second_floor, **self.button_style).pack(pady=5)
        
        # На третьем этаже НЕТ кнопки в подвал - только со второго!

    def find_key_room(self):
        DocumentViewer(self.parent, self.check_key)

    def check_key(self, num):
        if num == 2:  # Правильный документ
            self.has_basement_key = True
            messagebox.showinfo("🔑 Успех!", "Ты нашла ключ от запасного выхода!\n")
            self.third_floor()  # Возвращаемся на третий этаж
        else:
            messagebox.showerror("💀 Ошибка!", "Это обычный документ... Сущность поглотила тебя!")
            self.death_ending()

    def basement(self):
        self.current_location = "basement"
        self.clear_window()

        try:
            img = Image.open("basement.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#0a0a0a")
            canvas.pack()

        canvas.create_text(WINDOW_WIDTH//2, 100, text="🏚 ПОДВАЛ 🏚",
                          fill="white", font=global_fonts['large'])

        # Описание подвала
        desc_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        desc_bg.place(relx=0.5, rely=0.3, anchor="center")

        if self.has_basement_key:
            desc_label = tk.Label(desc_bg,
                                 text="Ты спускаешься в подвал. Перед тобой дверь с надписью 'ЗАПАСНОЙ ВЫХОД'. У тебя есть ключ!",
                                 font=global_fonts['small'], bg='black', fg='lightgreen')
            desc_label.pack(padx=20, pady=10)

            # Кнопка открытия двери
            open_btn = tk.Button(self.parent,
                                text="🔑 Открыть дверь (ключ есть)",
                                font=global_fonts['large'],
                                bg='#228b22', fg='white', activebackground='#32a032', activeforeground='white',
                                command=self.good_ending, width=25, height=2, relief="raised", bd=4)
            open_btn.place(relx=0.5, rely=0.6, anchor="center")

        else:
            desc_label = tk.Label(desc_bg,
                                 text="Ты спускаешься в подвал. Там дверь с надписью 'ЗАПАСНОЙ ВЫХОД', но она заперта.",
                                 font=global_fonts['small'], bg='black', fg='#ff6666')
            desc_label.pack(padx=20, pady=10)

            canvas.create_text(WINDOW_WIDTH//2, 200,
                              text="🚫 ДВЕРЬ ЗАПЕРТА 🚫",
                              fill="red", font=global_fonts['large'])

        # Кнопки возврата - можно вернуться ТОЛЬКО на 2 этаж
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.8, anchor="center")
        
        tk.Button(btn_frame, text="⬆ На второй этаж", font=global_fonts['small'],
                 bg='#4a4a4a', fg='white', command=self.second_floor, width=17).pack(side="left", padx=0)
    

    def good_ending(self):
        self.current_location = "good_ending"
        self.clear_window()

        try:
            img = Image.open("ending.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#87CEEB")
            canvas.pack()

            # Символическое солнце
            canvas.create_text(400, 150, text="☀️", font=global_fonts['large'], fill="yellow")

        # Текст победы
        victory_frame = tk.Frame(self.parent, bg='black', bd=3, relief="solid")
        victory_frame.place(relx=0.5, rely=0.4, anchor="center", width=600, height=300)

        victory_text = """🌟🌟🌟 ВЫЖИТЬ ОБЯЗАН! 🌟🌟🌟

Ты открываешь дверь и оказываешься на свежем воздухе!
Сущность осталась далеко позади. Оксана благополучно выбралась из колледжа.

🏆 ПОБЕДА 🏆

Спасибо за игру!"""

        victory_label = tk.Label(victory_frame,
                                text=victory_text,
                                font=global_fonts['small'], bg='black', fg='gold', justify="center")
        victory_label.pack(padx=20, pady=20)

        # Титры
        credits_frame = tk.Frame(self.parent, bg='#87CEEB')
        credits_frame.place(relx=0.5, rely=0.75, anchor="center")

        credits_text = """Создатели игры: Леденцы из барбариски
Вдохновлено историей колледжа Винкс
© 2026 Все права защищены"""

        credits_label = tk.Label(credits_frame,
                                text=credits_text,
                                font=global_fonts['small'], bg='#87CEEB', fg='#000080', justify="center")
        credits_label.pack()

        # Кнопка в главное меню
        tk.Button(self.parent,
                 text="🏠 В главное меню",
                 font=global_fonts['large'],
                 bg='#4a4a4a', fg='white', activebackground='#6a6a6a',
                 command=self.show_main_menu, width=20, height=2).place(relx=0.5, rely=0.9, anchor="center")

    def save_game(self):
        """Сохраняет состояние игры"""
        saved_data = {
            "solved_puzzle": self.solved_puzzle,
            "has_museum_key": self.has_museum_key,
            "has_basement_key": self.has_basement_key,
            "sphinx_passed": self.sphinx_passed,
            "password_parts": self.password_parts,
            "current_location": self.current_location
        }
        try:
            with open("save.json", "w", encoding='utf-8') as f:
                json.dump(saved_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("💾 Сохранение", "Игра успешно сохранена!\nМесто: " + self.get_location_name())
        except Exception as e:
            messagebox.showerror("❌ Ошибка", f"Не удалось сохранить игру: {e}")

    def get_location_name(self):
        """Возвращает название текущей локации"""
        locations = {
            "first_floor": "Первый этаж",
            "second_floor": "Второй этаж",
            "third_floor": "Третий этаж",
            "room_22": "Компьютерный класс",
            "basement": "Подвал",
            "main_menu": "Главное меню",
            "prologue": "Пролог",
            "death": "Смерть",
            "good_ending": "Хорошая концовка"
        }
        return locations.get(self.current_location, "Неизвестно")

    def load_game(self):
        """Загружает состояние игры"""
        try:
            with open("save.json", "r", encoding='utf-8') as f:
                saved_data = json.load(f)
                self.solved_puzzle = saved_data["solved_puzzle"]
                self.has_museum_key = saved_data["has_museum_key"]
                self.has_basement_key = saved_data["has_basement_key"]
                self.sphinx_passed = saved_data["sphinx_passed"]
                self.password_parts = saved_data["password_parts"]
                self.current_location = saved_data.get("current_location", "first_floor")
                
                messagebox.showinfo("💾 Загрузка", f"Игра успешно загружена!\nПродолжаем с: {self.get_location_name()}")
                
                # Переходим на сохраненную локацию
                if self.current_location == "first_floor":
                    self.first_floor()
                elif self.current_location == "second_floor":
                    self.second_floor()
                elif self.current_location == "third_floor":
                    self.third_floor()
                elif self.current_location == "room_22":
                    self.room_22()
                elif self.current_location == "basement":
                    self.basement()
                elif self.current_location == "prologue":
                    self.show_prologue()
                elif self.current_location == "good_ending":
                    self.good_ending()
                elif self.current_location == "death":
                    self.death_ending()
                else:
                    self.first_floor()  # По умолчанию

        except FileNotFoundError:
            messagebox.showerror("❌ Ошибка", "Нет сохранённых файлов!")
        except Exception as e:
            messagebox.showerror("❌ Ошибка", f"Ошибка загрузки: {e}")

    def show_help(self):
        """Справочная информация по игре"""
        help_text = """📖 СПРАВКА ПО ИГРЕ 📖     

Цель игры: Найти выход из колледжа, избежав встречи с опасной сущностью.

Управление:
- Используйте кнопки для выбора действий
- Кнопка 💾 СОХРАНИТЬ ИГРУ всегда внизу экрана
- Вводите правильные ответы на загадки
- Получайте важные предметы и ключи

Подсказки:
1. Никогда не поворачивайте направо на первом этаже
2. Почините систему проводов в серверной (№17)
3. Найдите ключ от музея в компьютерном классе
4. Решите загадки сфинкса в музее
5. Найдите ключ от запасного выхода на третьем этаже
6. После получения ключа от подвала, спуститесь туда со второго этажа
7. Выходите из здания через подвал!

Горячие клавиши:
- F1 - помощь
- Ctrl+S - быстрое сохранение
- ESC - вернуться в главное меню

Удачи! 🍀"""

        messagebox.showinfo("📚 Помощь", help_text)

# Основная точка входа
if __name__ == "__main__":
    root = tk.Tk()

    # Центрирование окна на экране
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - WINDOW_WIDTH) // 2
    y = (screen_height - WINDOW_HEIGHT) // 2
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    # Запрет изменения размера окна
    root.resizable(False, False)

    # Экземпляр игры
    game = Game(root)

    # Назначаем горячую клавишу
    def on_key_press(event):
        if event.keysym == 'F1':
            game.show_help()
        elif event.keysym == 's' and event.state & 0x4:  # Ctrl+S
            game.save_game()
        elif event.keysym == 'Escape':
            if messagebox.askyesno("Выход", "Вернуться в главное меню?"):
                game.show_main_menu()

    root.bind('<Key>', on_key_press)

    # Запуск главного цикла Tkinter
    root.mainloop()
