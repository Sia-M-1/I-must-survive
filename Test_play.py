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

# Получаем размеры экрана
# mport tkinter as tk
# root = tk.Tk()
# WINDOW_WIDTH = root.winfo_screenwidth()
# WINDOW_HEIGHT = root.winfo_screenheight()
# root.destroy()  # Закрываем временное окно

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
        tk.Label(title_frame, text="СОЕДИНИ ПРОВОДА", 
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



# Класс для просмотра документов
class DocumentViewer:
    def __init__(self, parent, on_choice):
        self.parent = parent
        self.on_choice = on_choice
        self.viewer_window = tk.Toplevel(parent)
        self.viewer_window.title("Документы")
        self.viewer_window.geometry("700x420")
        self.viewer_window.configure(bg='#2b2b2b')

        # Заголовок
        title_label = tk.Label(self.viewer_window, text="ТРИ ДОКУМЕНТА НА СТОЛЕ",
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

            tk.Button(btn_frame, text="Просмотреть", font=global_fonts['small'],
                bg='#5b5b5b', fg='white', command=lambda x=doc_num: self.view_document(x)).pack(side="left", padx=5)

            tk.Button(btn_frame, text="Выбрать", font=global_fonts['small'],
                bg='#6b8e23', fg='white', command=lambda x=doc_num: self.choose_document(x)).pack(side="left", padx=5)

        # Обновляем область прокрутки
        docs_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def view_document(self, num):
        view_window = tk.Toplevel(self.viewer_window)
        view_window.title(f"Документ {num}")
        view_window.geometry("500x650")
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
             bg='#8b4513', fg='white', command=view_window.destroy, width=15, height=1).pack(pady=15)

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
        self.code_words = {}
        self.current_location = "main_menu"
        self.previous_location = "second_floor_2"

        
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
                            text="СОХРАНИТЬ ИГРУ", 
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
            img = Image.open("start.png")
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

        # Загружаем изображение для кнопки Play
        try:
            play_img = Image.open("play_1.png")
            # Изменяем размер кнопки (можно настроить под свой дизайн)
            play_img = play_img.resize((200, 60), Image.Resampling.LANCZOS)
            self.play_button_img = ImageTk.PhotoImage(play_img)
            
            # Создаем кнопку с изображением
            play_button = tk.Button(canvas, image=self.play_button_img, 
                                borderwidth=0, highlightthickness=0,
                                command=self.start_new_game)
            # Размещаем кнопку в нужном месте
            canvas.create_window(WINDOW_WIDTH//2, 300, window=play_button)
        except Exception as e:
            print(f"Ошибка загрузки play.png: {e}")
            # Если изображение не загрузилось, используем обычную кнопку
            play_button = tk.Button(canvas, text="🌟 Начать новую игру", 
                                font=global_fonts['large'], bg='#4a4a4a', 
                                fg='white', command=self.start_new_game)
            canvas.create_window(WINDOW_WIDTH//2, 300, window=play_button)

        # Кнопка "Продолжить игру" (обычная, пока без изображения)
        continue_btn = tk.Button(canvas, text="Продолжить игру", 
                            font=global_fonts['large'], bg='#4a4a4a', 
                            fg='white', command=self.load_game)
        canvas.create_window(WINDOW_WIDTH//2, 380, window=continue_btn)

        # Кнопка "Выйти"
        exit_btn = tk.Button(canvas, text="Выйти", 
                            font=global_fonts['large'], bg='#4a4a4a', 
                            fg='white', command=self.parent.quit)
        canvas.create_window(WINDOW_WIDTH//2, 460, window=exit_btn)
        
    def start_new_game(self):
        # Сбрасываем состояние игры
        self.solved_puzzle = False
        self.has_museum_key = False
        self.has_basement_key = False
        self.sphinx_passed = False
        self.password_parts = []
        self.code_words = {}
        self.dialogue_stage = 0  # Добавить
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
        prologue_text = """ТУТ БУДЕТ ГИФКАААА
        
        Ходит легенда, что в колледже \"Винкс\" обитает странная сущность...
        
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
                img = Image.open(f"first_floor_start.png")
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

        description = "Ты находишься в коридоре первого этажа."
        desc_label = tk.Label(desc_bg, text=split_long_text(description), font=global_fonts['small'], bg='black', fg='white')
        desc_label.pack(padx=20, pady=10)

        # Кнопки выбора
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.7, anchor="center")

        buttons = [
            ("⬅ Повернуть налево (на второй этаж)", self.second_floor_1),  # Ведет в первый коридор второго этажа
            ("➡ Повернуть направо", self.death_ending),
            ("Попробовать открыть дверь", self.try_door),
            ("Зайти в столовую", self.canteen),
        ]
        
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
        messagebox.showinfo("Дверь", "Дверь закрыта извне... Видимо, придётся искать другой выход.")

    def canteen(self):
        messagebox.showinfo("Столовая", "В столовой темно и пусто. Здесь недавно были студенты.")

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
                          text="ТЫ ВСТРЕТИЛ СУЩНОСТЬ... \n\nКрасный волк поражает тебя мощным зарядом энергии.\n\nКОНЕЦ ИГРЫ",
                          fill="white", font=global_fonts['large'], justify="center")

        tk.Button(self.parent, text="В главное меню", font=global_fonts['large'],
                 bg="#4a4a4a", fg="white", command=self.show_main_menu).place(relx=0.5, rely=0.8, anchor="center")

    # ПЕРВЫЙ КОРИДОР ВТОРОГО ЭТАЖА (с лестницами)
    def second_floor_1(self):
        self.current_location = "second_floor_1"
        self.clear_window()

        # Выбираем фон в зависимости от прохождения пятнашков
        if self.solved_puzzle:
            # Светлый коридор (после прохождения)
            try:
                img = Image.open("second_floor_1_light.png")
            except:
                img = None
        else:
            # Темный коридор (до прохождения)
            try:
                img = Image.open("second_floor_1_nolight.png")
            except:
                img = None

        if img:
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        else:
            # Запасной вариант
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, 
                            bg="#2a2a2a" if self.solved_puzzle else "#1a1a1a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2,
                            text="НАЧАЛО КОРИДОРА ВТОРОГО ЭТАЖА\n" + ("☀️" if self.solved_puzzle else "🌑"),
                            fill="white", font=global_fonts['large'])

        # Текст описания
        desc_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        desc_bg.place(relx=0.5, rely=0.2, anchor="center")

        if self.solved_puzzle:
            description = "Свет в коридоре зажегся! Видно лестницы на другие этажи."
        else:
            description = "Ты в начале коридора второго этажа. Здесь темно, но видны лестницы"
        
        desc_label = tk.Label(desc_bg, text=split_long_text(description), 
                             font=global_fonts['small'], bg='black', fg='white')
        desc_label.pack(padx=20, pady=10)

        # Кнопки выбора
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Кнопка в основной коридор (с кабинетами)
        tk.Button(btn_frame, text="⬅ Повернуть налево (в основной коридор)", 
                 command=self.second_floor_2, **self.button_style).pack(pady=5)
        
        # Кнопка на третий этаж
        tk.Button(btn_frame, text="⬆ Подняться на третий этаж", 
                 command=self.third_floor, **self.button_style).pack(pady=5)
        
        # Кнопка на первый этаж
        tk.Button(btn_frame, text="⬇ Спуститься на первый этаж", 
                 command=self.first_floor, **self.button_style).pack(pady=5)

    # ВТОРОЙ КОРИДОР ВТОРОГО ЭТАЖА (только кабинеты)
    def second_floor_2(self):
        self.current_location = "second_floor_2"
        self.clear_window()

        # Выбираем фон в зависимости от прохождения пятнашков
        if self.solved_puzzle:
            # Светлый коридор (после прохождения)
            try:
                img = Image.open("second_floor_2_light.png")
            except:
                img = None
        else:
            # Темный коридор (до прохождения)
            try:
                img = Image.open("second_floor_2_nolight.png")
            except:
                img = None

        if img:
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        else:
            # Запасной вариант
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, 
                            bg="#2a2a2a" if self.solved_puzzle else "#1a1a1a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2,
                            text="ОСНОВНОЙ КОРИДОР ВТОРОГО ЭТАЖА\n" + ("☀️" if self.solved_puzzle else "🌑"),
                            fill="white", font=global_fonts['large'])

        # Текст описания
        desc_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        desc_bg.place(relx=0.5, rely=0.2, anchor="center")

        if self.solved_puzzle:
            description = "В основном коридоре горит свет. Видны двери кабинетов."
        else:
            description = "Здесь темно... Нужно починить свет в серверной, чтобы увидеть хоть что-то..."
        
        desc_label = tk.Label(desc_bg, text=split_long_text(description), 
                             font=global_fonts['small'], bg='black', fg='white')
        desc_label.pack(padx=20, pady=10)

        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Кабинет №17 (серверная) - доступен всегда
        tk.Button(btn_frame, text="🔧 Кабинет №17 (серверная)",
                command=self.room_17, **self.button_style).pack(pady=5)
        
        # Кабинеты доступны только если свет починен
        if self.solved_puzzle:
            tk.Button(btn_frame, text="💻 Кабинет №22 (комп. класс)", command=self.room_22, **self.button_style).pack(pady=5)
            tk.Button(btn_frame, text="🏛 Музей", command=self.museum, **self.button_style).pack(pady=5)
        else:
            tk.Label(btn_frame, text="Другие кабинеты не видны в темноте", 
                    font=global_fonts['small'], bg='black', fg='#888888').pack(pady=5)
# Кнопка в подвал - добавлена!
        tk.Button(btn_frame, text="⬇ Спуститься в подвал", 
                command=self.basement, **self.button_style).pack(pady=5)
        
        # Кнопка возврата в начало коридора
        tk.Button(btn_frame, text="⬅ Вернуться в начало коридора", 
                 command=self.second_floor_1, **self.button_style).pack(pady=5)
        
    def room_17(self):
        self.current_location = "room_17"
        self.clear_window()

        # Фон кабинета №17
        try:
            img = Image.open("class_17.png")  # Фон кабинета
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#3a4a5a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, 100, text="КАБИНЕТ №17 (СЕРВЕРНАЯ)",
                            fill="white", font=global_fonts['large'])

        # Текст задания (вверху)
        if self.solved_puzzle:
            task_text = "Свет уже включен! Можно выходить"
        else:
            task_text = "Почини серверную, чтобы включить свет во всем здании!"
        
        task_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        task_bg.place(relx=0.5, rely=0.15, anchor="center")
        
        task_label = tk.Label(task_bg, text=split_long_text(task_text), 
                            font=global_fonts['small'], bg='black', fg='#ffd700')
        task_label.pack(padx=20, pady=10)

        # Кнопки отдельно, без черного фона
        btn_y = 0.85  # Позиция по вертикали
        
        if not self.solved_puzzle:
            # Кнопка "Починить" слева
            repair_btn = tk.Button(self.parent, text="Починить серверную", 
                                font=global_fonts['large'], 
                                bg='#4a8a4a', fg='white',
                                activebackground='#5a9a5a',
                                command=lambda: WirePuzzle(self.parent, self.puzzle_complete_from_17),
                                width=18, height=2, 
                                relief='raised', bd=3)
            repair_btn.place(relx=0.35, rely=btn_y, anchor="center")
            
            # Кнопка "Выйти" справа
            exit_btn = tk.Button(self.parent, text="🚪 Выйти из кабинета", 
                                font=global_fonts['large'],
                                bg='#8a4a4a', fg='white',
                                activebackground='#9a5a5a',
                                command=self.second_floor_2,
                                width=18, height=2,
                                relief='raised', bd=3)
            exit_btn.place(relx=0.65, rely=btn_y, anchor="center")
        else:
            # Если свет уже починен - показываем заглушку такого же размера
            repaired_label = tk.Label(self.parent, text="✅ Свет починен", 
                                    font=global_fonts['large'],
                                    bg='#228b22', fg='white',
                                    width=18, height=2,
                                    relief='raised', bd=3)
            repaired_label.place(relx=0.35, rely=btn_y, anchor="center")
            
            # Кнопка "Выйти" справа (такого же размера)
            exit_btn = tk.Button(self.parent, text="🚪 Выйти из кабинета", 
                                font=global_fonts['large'],
                                bg='#8a4a4a', fg='white',
                                activebackground='#9a5a5a',
                                command=self.second_floor_2,
                                width=18, height=2,
                                relief='raised', bd=3)
            exit_btn.place(relx=0.65, rely=btn_y, anchor="center")
            
    def puzzle_complete_from_17(self):
        self.solved_puzzle = True
        self.room_17()  # Возвращаемся в кабинет с обновленным статусом

    def puzzle_complete(self):
        self.solved_puzzle = True
        self.second_floor_2()

    def puzzle_complete_from_1(self):
        self.solved_puzzle = True
        self.second_floor_1()  # Возвращаемся в первый коридор с обновленным фоном

    def puzzle_complete_from_2(self):
        self.solved_puzzle = True
        self.second_floor_2()  # Возвращаемся во второй коридор с обновленным фоном

    def room_22(self):
        self.current_location = "room_22"
        self.clear_window()

        try:
            img = Image.open("class_22.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#2b2b2b")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, 50, text="КОМПЬЮТЕРНЫЙ КЛАСС",
                            fill="white", font=global_fonts['large'])

        # Текст подсказки
        hint_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        hint_bg.place(relx=0.5, rely=0.15, anchor="center")
        
        if len(self.password_parts) == 3:
            hint_text = "Все части пароля собраны! Можешь ввести пароль на 4 компьютере"
        else:
            hint_text = f"Собрано частей пароля: {len(self.password_parts)}/3"
        
        hint_label = tk.Label(hint_bg, text=hint_text,
                            font=global_fonts['small'], bg='black', fg='#ffd700')
        hint_label.pack(padx=20, pady=10)

        # Кнопки для компьютеров
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Компьютеры 1-3
        for i in range(1, 4):
            status = "✅" if f"part{i}" in self.password_parts else "⬜"
            btn = tk.Button(btn_frame, text=f"{status} Компьютер {i}",
                        font=global_fonts['small'], bg='#4a4a4a', fg='white',
                        command=lambda x=i: self.show_computer_task(x), width=20, height=1)
            btn.pack(pady=2)

        # Компьютер 4 (доступен только если собраны все части)
        if len(self.password_parts) == 3:
            tk.Button(btn_frame, text="Компьютер 4",
                    font=global_fonts['small'], bg='#6b8e23', fg='white',
                    command=self.show_password_window, width=20, height=1).pack(pady=5)
        else:
            tk.Label(btn_frame, text="Компьютер 4 недоступен", 
                    font=global_fonts['small'], bg='black', fg='#888888', width=20).pack(pady=5)

        # Ключ от музея (отдельно)
        if not self.has_museum_key:
            tk.Button(btn_frame, text="Взять ключ от музея",
                    font=global_fonts['small'], bg='#b8860b', fg='white',
                    command=self.find_museum_key, width=20, height=1).pack(pady=5)

        # Кнопка выхода
        tk.Button(btn_frame, text="Выйти из кабинета", 
                font=global_fonts['small'], bg='#8a4a4a', fg='white',
                command=self.second_floor_2, width=20, height=1).pack(pady=5)
        

    def show_computer_task(self, computer_num):
        """Показывает задание для компьютера"""
        
        # Проверяем, решено ли уже это задание
        part_key = f"part{computer_num}"
        if part_key in self.password_parts:
            # Если задание уже решено, показываем сообщение
            messagebox.showinfo("ℹ️ Компьютер", f"Ответ на компьютер {computer_num} уже введен!")
            return
        
        # Задания для каждого компьютера
        tasks = {
            1: {
                "title": "Компьютер №1 - Задание по программированию",
                "text": "В языке Python для вывода данных на экран используется функция ______",
                "answer": "print",
                "code_word": "PRINT",  # Кодовое слово (часть пароля)
                "part": "part1"
            },
            2: {
                "title": "Компьютер №2 - Задание по программированию",
                "text": """while True:
                    x = input('Введите строку: ')
                    if x == 'стоп':
                        ______
                    print(x + x)""",
                "answer": "break",
                "code_word": "BREAK",  # Кодовое слово (часть пароля)
                "part": "part2"
            },
            3: {
                "title": "Компьютер №3 - Задание по программированию",
                "text": """for i in range(5):
                    if i == 3:
                        ______
                    print(i)""",
                "answer": "continue",
                "code_word": "CONTINUE",  # Кодовое слово (часть пароля)
                "part": "part3"
            }
        }
        
        task = tasks[computer_num]
        
        # Создаем окно для задания
        task_window = tk.Toplevel(self.parent)
        task_window.title(task["title"])
        task_window.geometry("600x500+800+100")  # Смещено вправо
        task_window.configure(bg='#2a2a2a')
        task_window.transient(self.parent)
        task_window.grab_set()
        task_window.resizable(False, False)  # Запрещаем изменение размера
        
        # Заголовок
        tk.Label(task_window, text=f"КОМПЬЮТЕР №{computer_num}",
                font=global_fonts['large'], bg='#2a2a2a', fg='#ffd700').pack(pady=10)
        
        # Основной фрейм
        main_frame = tk.Frame(task_window, bg='#2a2a2a')
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Текст задания с выравниванием по левому краю
        text_frame = tk.Frame(main_frame, bg='#3a3a3a', bd=2, relief="solid")
        text_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Используем Text widget для лучшего отображения кода
        text_widget = tk.Text(text_frame, font=Font(family="Courier", size=12),
                            bg='#3a3a3a', fg='#00ff00',  # Зеленый текст как в терминале
                            wrap="word", height=8, width=50, bd=0)
        text_widget.pack(padx=10, pady=10, fill="both", expand=True)
        text_widget.insert("1.0", task["text"])
        text_widget.config(state="disabled")  # Делаем текст только для чтения
        
        # Фрейм для ввода ответа
        input_frame = tk.Frame(main_frame, bg='#2a2a2a')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Ваш ответ:", 
                font=global_fonts['small'], bg='#2a2a2a', fg='white').pack(side="left", padx=5)
        
        answer_entry = tk.Entry(input_frame, width=20, font=global_fonts['small'])
        answer_entry.pack(side="left", padx=5)
        
        # Фрейм для сообщений (результат будет显示在这里)
        message_frame = tk.Frame(main_frame, bg='#2a2a2a', height=50)
        message_frame.pack(pady=5, fill="x")
        message_frame.pack_propagate(False)
        
        message_label = tk.Label(message_frame, text="",
                                font=global_fonts['small'], bg='#2a2a2a', fg='white',
                                wraplength=500)
        message_label.pack(expand=True)

        # Кнопки
        button_frame = tk.Frame(main_frame, bg='#2a2a2a')
        button_frame.pack(pady=5)
        
        # Кнопка проверки
        check_btn = tk.Button(button_frame, text="✅ Проверить", 
                            font=global_fonts['small'], bg='#4a8a4a', fg='white',
                            command=None, width=15, height=1)
        check_btn.pack(side="left", padx=5)
        
        # Кнопка закрытия
        close_btn = tk.Button(button_frame, text="✖ Закрыть", 
                            font=global_fonts['small'], bg='#8a4a4a', fg='white',
                            command=task_window.destroy, width=15, height=1)
        close_btn.pack(side="left", padx=5)

        # Функция проверки ответа
        def check_answer():
            user_answer = answer_entry.get().lower().strip()
            
            if user_answer == task["answer"]:
                if task["part"] not in self.password_parts:
                    self.password_parts.append(task["part"])
                    # Сохраняем кодовое слово
                    if not hasattr(self, 'code_words'):
                        self.code_words = {}
                    self.code_words[computer_num] = task["code_word"]
                    
                    # Показываем сообщение об успехе
                    message_label.config(text=f"Правильно!\nПолучено кодовое слово: {task['code_word']}", 
                                    fg='#4aff4a')
                    
                    # Блокируем поле ввода
                    answer_entry.config(state="disabled")
                    
                    # БЛОКИРУЕМ ОБЕ КНОПКИ
                    check_btn.config(state="disabled", bg='#6a6a6a')
                    close_btn.config(state="disabled", bg='#6a6a6a')
                    
                    # Закрываем окно через 1.5 секунды и возвращаемся в комнату
                    task_window.after(1500, lambda: [task_window.destroy(), self.room_22()])
                else:
                    message_label.config(text="ℹ️ Ты уже решил это задание!", fg='#ffd700')
                    # Блокируем всё
                    answer_entry.config(state="disabled")
                    check_btn.config(state="disabled", bg='#6a6a6a')
                    close_btn.config(state="disabled", bg='#6a6a6a')
                    task_window.after(1000, task_window.destroy)
            else:
                message_label.config(text="❌ Неправильный ответ! Попробуй еще раз.", fg='#ff6666')
                answer_entry.delete(0, tk.END)  # Очищаем поле ввода
                
        # Назначаем команду для кнопки проверки
        check_btn.config(command=check_answer)
        
        # Центрируем окно на экране
        task_window.update_idletasks()
        x = (task_window.winfo_screenwidth() - task_window.winfo_width()) // 2
        y = (task_window.winfo_screenheight() - task_window.winfo_height()) // 2
        task_window.geometry(f"+{x}+{y}")
        
    def find_museum_key(self):
        self.has_museum_key = True
        messagebox.showinfo("🔑 Находка", "Ключ от музея лежал на столе!")
        self.room_22()

    def museum(self):
        """Вход в музей"""
        if not self.has_museum_key:
            messagebox.showinfo("🏛 Музей", "Дверь заперта. Нужен ключ.")
            return
        
        # Сохраняем текущую локацию перед входом в музей
        self.previous_location = self.current_location
        
        # Показываем закрытый музей
        self.show_museum_closed()
        
    def show_museum_closed(self):
        """Показывает закрытый музей (темный)"""
        self.current_location = "museum_closed"
        self.clear_window()
        
        # Фон закрытого музея
        try:
            img = Image.open("museum_close.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#2a1a2a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, 100, text="🏛 МУЗЕЙ (ЗАКРЫТ) 🏛",
                            fill="white", font=global_fonts['large'])
        
        # Кнопки
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.8, anchor="center")
        
        # Кнопка открыть музей
        open_btn = tk.Button(btn_frame, text="🔓 Открыть музей \n(ключ есть)", 
                            font=global_fonts['large'], bg='#4a8a4a', fg='white',
                            command=self.show_museum_open, width=20, height=2)
        open_btn.pack(pady=5)
        
        # Кнопка назад
        back_btn = tk.Button(btn_frame, text="⬅ Назад в коридор", 
                            font=global_fonts['small'], bg='#8a4a4a', fg='white',
                            command=self.second_floor_2, width=20, height=1)
        back_btn.pack(pady=5)

    def show_museum_open(self):
        """Показывает открытый музей (светлый)"""
        self.current_location = "museum_open"
        self.clear_window()
        
        # Фон открытого музея
        try:
            img = Image.open("museum_open.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#4a3a4a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, 100, text="🏛 МУЗЕЙ (ОТКРЫТ) 🏛",
                            fill="white", font=global_fonts['large'])
        
        # Показываем диалог с андроидом
        self.show_android_dialogue()
        
        # Кнопка выхода - возвращаемся в предыдущую локацию
        exit_btn = tk.Button(self.parent, text="🚪 Выйти из музея", 
                            font=global_fonts['small'], bg='#8a4a4a', fg='white',
                            command=self.return_from_museum, width=20, height=1)
        exit_btn.place(relx=0.5, rely=0.9, anchor="center")

    def return_from_museum(self):
        """Возврат в предыдущую локацию"""
        if self.previous_location == "second_floor_2":
            self.second_floor_2()
        elif self.previous_location == "second_floor_1":
            self.second_floor_1()
        else:
            self.second_floor_2()  # По умолчанию

    def show_android_dialogue(self):
        """Показывает диалоговое окно с андроидом"""
        dialogue_window = tk.Toplevel(self.parent)
        dialogue_window.title("Ирина Идуардовна (андроид)")
        dialogue_window.geometry("600x450")  # Увеличил размер для фона
        dialogue_window.configure(bg='#2a1a2a')
        dialogue_window.transient(self.parent)
        dialogue_window.grab_set()
        dialogue_window.resizable(False, False)
        
        # Центрируем окно на экране
        dialogue_window.update_idletasks()
        x = (dialogue_window.winfo_screenwidth() - 600) // 2
        y = (dialogue_window.winfo_screenheight() - 450) // 2
        dialogue_window.geometry(f"+{x}+{y}")
        
        # Загружаем фон с изображением андроида
        try:
            bg_image = Image.open("iiduardovna.png")
            bg_image = bg_image.resize((600, 450), Image.Resampling.LANCZOS)
            self.dialogue_bg = ImageTk.PhotoImage(bg_image)
            
            # Canvas для фона
            bg_canvas = tk.Canvas(dialogue_window, width=600, height=450, highlightthickness=0)
            bg_canvas.pack(fill="both", expand=True)
            bg_canvas.create_image(0, 0, anchor="nw", image=self.dialogue_bg)
            
            # Создаем фрейм для контента справа (примерно с 250px от левого края)
            content_frame = tk.Frame(bg_canvas, bg='#3a2a3a', bd=2, relief="solid")
            # Помещаем фрейм в правую часть (смещение 250px от левого края)
            bg_canvas.create_window(280, 50, window=content_frame, anchor="nw", width=280, height=350)
            
        except Exception as e:
            print(f"Ошибка загрузки фона: {e}")
            # Если фон не загрузился, используем обычный фрейм
            bg_canvas = tk.Canvas(dialogue_window, width=600, height=450, bg='#2a1a2a')
            bg_canvas.pack(fill="both", expand=True)
            
            # Заголовок с именем
            name_label = tk.Label(bg_canvas, text="🤖 Ирина Идуардовна 🤖",
                                font=global_fonts['large'], bg='#2a1a2a', fg='#ff99ff')
            bg_canvas.create_window(300, 40, window=name_label)
            
            # Фрейм для контента
            content_frame = tk.Frame(bg_canvas, bg='#3a2a3a', bd=2, relief="solid")
            bg_canvas.create_window(300, 150, window=content_frame, width=350, height=250)
        
        # Добавляем scrollbar для контента
        canvas = tk.Canvas(content_frame, bg='#3a2a3a', highlightthickness=0, height=330)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Фрейм для текста внутри canvas
        text_frame = tk.Frame(canvas, bg='#3a2a3a')
        canvas.create_window((0, 0), window=text_frame, anchor="nw", width=260)
        
        # Начинаем с первого этапа диалога
        if not self.sphinx_passed:
            self.dialogue_stage = 0
        else:
            self.dialogue_stage = 7
        
        self.dialogue_window = dialogue_window
        self.dialogue_canvas = canvas
        self.dialogue_text_frame = text_frame
        
        # Обновляем область прокрутки
        text_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        self.update_android_dialogue()
        
    def update_android_dialogue(self):
        """Обновляет диалог с андроидом"""
        # Очищаем фрейм
        for widget in self.dialogue_text_frame.winfo_children():
            widget.destroy()
        
        # Создаем виджет для сообщения с переносом текста
        def create_message(text):
            msg_frame = tk.Frame(self.dialogue_text_frame, bg='#3a2a3a')
            msg_frame.pack(fill="x", padx=5, pady=3)
            
            msg_label = tk.Label(msg_frame, text=text,
                            font=global_fonts['small'], bg='#3a2a3a', fg='white',
                            wraplength=240, justify="left")
            msg_label.pack()
        
        # Создаем кнопку
        def create_button(text, command, color='#4a6a8a'):
            btn_frame = tk.Frame(self.dialogue_text_frame, bg='#3a2a3a')
            btn_frame.pack(pady=5)
            btn = tk.Button(btn_frame, text=text, 
                        font=global_fonts['small'], bg=color, fg='white',
                        command=command, width=15, height=1)
            btn.pack()
        
        # Этапы диалога
        if self.dialogue_stage == 0:
            create_message("Наконец-то хоть кто-то включил свет! А то я так долго была без электричества...")
            create_button("Далее →", self.next_dialogue_stage)
        
        elif self.dialogue_stage == 1:
            create_message("Как ты сюда вообще смог пробраться? Охранник что, уснул?")
            create_button("Далее →", self.next_dialogue_stage)
        
        elif self.dialogue_stage == 2:
            create_message("Чтобы пройти дальше, тебе нужно будет отгадать загадки. Иначе тебя найдет сущность...")
            create_button("Начать загадки →", self.start_riddles, '#4a8a4a')
        
        elif self.dialogue_stage >= 3 and self.dialogue_stage <= 5:
            # Загадки
            riddles = [
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
            
            riddle_index = self.dialogue_stage - 3
            current_riddle = riddles[riddle_index]
            
            create_message(f"Загадка {riddle_index + 1}:")
            create_message(current_riddle['question'])
            
            # Поле для ответа
            answer_frame = tk.Frame(self.dialogue_text_frame, bg='#3a2a3a')
            answer_frame.pack(pady=5)
            
            tk.Label(answer_frame, text="Ответ:", 
                    font=global_fonts['small'], bg='#3a2a3a', fg='white').pack(side="left", padx=2)
            
            answer_entry = tk.Entry(answer_frame, width=12, font=global_fonts['small'])
            answer_entry.pack(side="left", padx=2)
            answer_entry.focus_set()
            
            # Сообщение об ошибке (изначально скрыто)
            error_label = tk.Label(self.dialogue_text_frame, text="",
                                font=global_fonts['small'], bg='#3a2a3a', fg='#ff6666',
                                wraplength=240)
            error_label.pack(pady=2)
            
            # Переменная для отслеживания, был ли уже дан ответ
            answered = [False]
            
            # Создаем кнопку ответить (сначала без команды)
            check_btn = tk.Button(self.dialogue_text_frame, text="Ответить", 
                                font=global_fonts['small'], bg='#4a8a4a', fg='white',
                                width=12)
            
            # Функция проверки ответа для конкретной загадки
            def create_check_function(riddle, entry, error, answered_flag, btn):
                def check():
                    if answered_flag[0]:
                        return
                    
                    user_answer = entry.get().lower().strip()
                    if user_answer == riddle["answer"]:
                        answered_flag[0] = True
                        # Показываем сообщение об успехе
                        success_label = tk.Label(self.dialogue_text_frame, 
                                                text="Правильно! Молодец!",
                                                font=global_fonts['small'], bg='#3a2a3a', fg='#4aff4a',
                                                wraplength=240)
                        success_label.pack(pady=2)
                        
                        # Блокируем поле ввода и кнопку
                        entry.config(state="disabled")
                        btn.config(state="disabled", bg='#6a6a6a')
                        
                        # Переходим к следующему этапу через 1 секунду
                        self.dialogue_text_frame.after(1000, self.next_dialogue_stage)
                    else:
                        # Неверный ответ - показываем скример с волком
                        error.config(text="❌ Неправильно! Сущность нашла тебя...", fg='#ff6666')
                        
                        # Закрываем диалоговое окно
                        self.dialogue_window.destroy()
                        
                        # Показываем скример с волком
                        self.show_death_from_riddle()
                return check
            
            # Назначаем команду для кнопки
            check_btn.config(command=create_check_function(current_riddle, answer_entry, error_label, answered, check_btn))
            check_btn.pack(pady=5)
                
        elif self.dialogue_stage == 6:
            create_message("А ты молодец! Не ожидала, что справишься со всеми загадками!")
            self.sphinx_passed = True
            create_button("Далее →", self.next_dialogue_stage)
        
        elif self.dialogue_stage == 7:
            create_message("Ну ладно, ищи выход дальше. Удачи!")
            create_button("✖ Закрыть", self.dialogue_window.destroy, '#8a4a4a')
        
        # Обновляем область прокрутки
        self.dialogue_text_frame.update_idletasks()
        self.dialogue_canvas.configure(scrollregion=self.dialogue_canvas.bbox("all"))
        # Прокручиваем вниз
        self.dialogue_canvas.yview_moveto(1.0)
        
    def next_dialogue_stage(self):
        """Переход к следующему этапу диалога"""
        self.dialogue_stage += 1
        # Если дошли до этапа после загадок, убеждаемся что sphinx_passed = True
        if self.dialogue_stage > 5:  # После всех загадок
            self.sphinx_passed = True
        self.update_android_dialogue()

    def start_riddles(self):
        """Начинает загадки"""
        self.dialogue_stage = 3  # Переходим к первой загадке
        self.update_android_dialogue()

    def show_password_window(self):
        """Показывает окно для ввода пароля на 4 компьютере"""
        
        # Проверяем, был ли уже введен пароль (можно по наличию чата или доп. переменной)
        # Для простоты будем проверять, что все части собраны и пароль еще не введен
        # Создадим новую переменную для отслеживания
        if not hasattr(self, 'password_entered'):
            self.password_entered = False
        
        # Если пароль уже был введен, сразу открываем чат
        if self.password_entered:
            self.show_teacher_chat()
            return
        
        password_window = tk.Toplevel(self.parent)
        password_window.title("🔑 Компьютер №4 - Ввод пароля")
        password_window.geometry("550x450+800+100")
        password_window.configure(bg='#2a2a2a')
        password_window.transient(self.parent)
        password_window.grab_set()
        password_window.resizable(False, False)
        
        # Заголовок
        tk.Label(password_window, text="🔑 КОМПЬЮТЕР №4 - ВВОД ПАРОЛЯ 🔑",
                font=global_fonts['large'], bg='#2a2a2a', fg='#ffd700').pack(pady=10)
        
        # Информация о частях пароля
        parts_frame = tk.Frame(password_window, bg='#3a3a3a', bd=2, relief="solid")
        parts_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(parts_frame, text="Полученные кодовые слова:",
                font=global_fonts['small'], bg='#3a3a3a', fg='#ffd700').pack(pady=5)
        
        parts_text = ""
        if "part1" in self.password_parts:
            parts_text += f"✅ Компьютер 1: {self.code_words.get(1, 'PRINT')}\n"
        else:
            parts_text += "❌ Компьютер 1: не пройден\n"
        
        if "part2" in self.password_parts:
            parts_text += f"✅ Компьютер 2: {self.code_words.get(2, 'BREAK')}\n"
        else:
            parts_text += "❌ Компьютер 2: не пройден\n"
        
        if "part3" in self.password_parts:
            parts_text += f"✅ Компьютер 3: {self.code_words.get(3, 'CONTINUE')}\n"
        else:
            parts_text += "❌ Компьютер 3: не пройден\n"
        
        parts_label = tk.Label(parts_frame, text=parts_text,
                            font=global_fonts['small'], bg='#3a3a3a', fg='white',
                            justify="left")
        parts_label.pack(pady=5, padx=20)
        
        # Подсказка
        hint_frame = tk.Frame(password_window, bg='#2a2a2a')
        hint_frame.pack(pady=5)
        tk.Label(hint_frame, text="Подсказка: введите кодовые слова через пробел в порядке компьютеров (1 2 3)",
                font=global_fonts['small'], bg='#2a2a2a', fg='#888888').pack()
        
        # Поле для ввода пароля
        input_frame = tk.Frame(password_window, bg='#2a2a2a')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="Введите кодовые слова через пробел:",
                font=global_fonts['small'], bg='#2a2a2a', fg='white').pack()
        
        password_entry = tk.Entry(input_frame, width=30, font=global_fonts['large'])
        password_entry.pack(pady=10)
        
        # Фрейм для сообщений
        message_frame = tk.Frame(password_window, bg='#2a2a2a', height=50)
        message_frame.pack(pady=5, fill="x")
        message_frame.pack_propagate(False)
        
        message_label = tk.Label(message_frame, text="",
                                font=global_fonts['small'], bg='#2a2a2a', fg='white',
                                wraplength=500)
        message_label.pack(expand=True)
        
        # Функция проверки пароля
        def check_password():
            # Ожидаемый пароль: кодовые слова
            expected_words = []
            if 1 in self.code_words:
                expected_words.append(self.code_words[1])
            if 2 in self.code_words:
                expected_words.append(self.code_words[2])
            if 3 in self.code_words:
                expected_words.append(self.code_words[3])
            
            expected = " ".join(expected_words).lower()
            user_input = password_entry.get().lower().strip()
            
            if user_input == expected:
                message_label.config(text="✅ Пароль верный! Открывается чат преподавателей...", fg='#4aff4a')
                password_entry.config(state="disabled")
                check_btn.config(state="disabled")
                
                # Запоминаем, что пароль введен
                self.password_entered = True
                
                # Открываем чат через 1.5 секунды
                password_window.after(1500, lambda: [password_window.destroy(), self.show_teacher_chat()])
            else:
                message_label.config(text="❌ Неверный пароль! Попробуй еще раз.", fg='#ff6666')
                password_entry.delete(0, tk.END)  # Очищаем поле ввода
        
        # Кнопка проверки
        check_btn = tk.Button(password_window, text="🔑 Проверить пароль", 
                            font=global_fonts['large'], bg='#4a8a4a', fg='white',
                            command=check_password, width=20, height=1)
        check_btn.pack(pady=10)
        
        # Кнопка закрытия
        close_btn = tk.Button(password_window, text="✖ Закрыть", 
                            font=global_fonts['small'], bg='#8a4a4a', fg='white',
                            command=password_window.destroy, width=15, height=1)
        close_btn.pack(pady=5)
        
    def show_teacher_chat(self):
        """Показывает окно с чатом преподавателей"""
        chat_window = tk.Toplevel(self.parent)
        chat_window.title("💬 Чат преподавателей")
        chat_window.geometry("450x450+750+100")  # Фиксированный размер, справа
        chat_window.configure(bg='#2b2b2b')
        chat_window.transient(self.parent)
        chat_window.grab_set()
        chat_window.resizable(False, False)  # Запрещаем изменение размера
        
        # Заголовок
        tk.Label(chat_window, text="ЧАТ ПРЕПОДАВАТЕЛЕЙ",
                font=global_fonts['large'], bg='#2b2b2b', fg='#ffd700').pack(pady=10)
        
        # Фрейм для сообщений с прокруткой
        main_frame = tk.Frame(chat_window, bg='#2b2b2b')
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        
       # Фрейм для сообщений (без прокрутки)
        messages_frame = tk.Frame(chat_window, bg='#3b3b3b')
        messages_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Сообщения с автоматическим переносом
        messages = [
            ("Дмитрий \nАЕгорович:", "Куда ты положил ключ от подвала?", "#4a6a8a"),
            ("Евгения \nАлексеевна:", "В кабинете на третьем этаже, в столе.", "#6a4a8a"),
            ("Дмитрий \nАЕгорович:", "Точно? А то студенты вечно теряют.", "#4a6a8a"),
            ("Евгения \nААлексеевна:", "Да, под документами, во втором ящике.", "#6a4a8a"),
        ]
        
        for i, (name, text, color) in enumerate(messages):
            msg_frame = tk.Frame(messages_frame, bg='#3b3b3b')
            msg_frame.pack(fill="x", padx=10, pady=8)
            
            # Имя (фиксированной ширины)
            name_label = tk.Label(msg_frame, text=name, 
                                font=global_fonts['small'], bg=color, fg='white',
                                width=12, height=2)
            name_label.pack(side="left", padx=5)
            
            # Текст с переносом
            text_label = tk.Label(msg_frame, text=text,
                                font=global_fonts['small'], bg='#4b4b4b', fg='white',
                                wraplength=250, justify="left")
            text_label.pack(side="left", padx=5, fill="x", expand=True)
        
        # Кнопка закрытия
        close_btn = tk.Button(chat_window, text="✖ Закрыть чат", 
                            font=global_fonts['large'], bg='#8a4a4a', fg='white',
                            command=lambda: [chat_window.destroy(), self.room_22()],
                            width=15, height=1)
        close_btn.pack(pady=10)


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
        all_second_floor_complete = self.solved_puzzle and self.has_museum_key and self.sphinx_passed
        
        if all_second_floor_complete:
            tk.Button(btn_frame, text="Зайти в кабинет", command=self.find_key_room, **self.button_style).pack(pady=5)
        else:
            tk.Label(btn_frame, text="❌ Кабинет закрыт",
                    font=global_fonts['small'], bg='black', fg='#888888').pack(pady=5)
        
        tk.Button(btn_frame, text="⬇ Спуститься на второй этаж", 
                 command=self.second_floor_1, **self.button_style).pack(pady=5)

    def find_key_room(self):
        """Вход в кабинет на третьем этаже"""
        self.current_location = "third_floor_room"
        self.clear_window()
        
        # Фон кабинета на третьем этаже
        try:
            img = Image.open("class_third_floor.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#3a4a5a")
            canvas.pack()
            canvas.create_text(WINDOW_WIDTH//2, 80, text="КАБИНЕТ НА ТРЕТЬЕМ ЭТАЖЕ",
                            fill="white", font=global_fonts['large'])
        
        # Название кабинета (вверху)
        title_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        title_bg.place(relx=0.5, rely=0.1, anchor="center")
        
        title_label = tk.Label(title_bg, text="КАБИНЕТ НА ТРЕТЬЕМ ЭТАЖЕ",
                            font=global_fonts['large'], bg='black', fg='#ffd700')
        title_label.pack(padx=20, pady=10)
        
        # Текст подсказки
        hint_bg = tk.Frame(self.parent, bg='black', bd=2, relief="solid")
        hint_bg.place(relx=0.5, rely=0.25, anchor="center")
        
        hint_label = tk.Label(hint_bg, 
                            text="Посмотри документы и разберись,\nкакой из них является правильным титульным листом",
                            font=global_fonts['small'], bg='black', fg='#ffffff',
                            wraplength=500, justify="center")
        hint_label.pack(padx=30, pady=15)
        
        # Кнопка просмотра документов (отдельно, без черного фона)
        docs_btn = tk.Button(self.parent, text="Просмотреть документы", 
                            font=global_fonts['large'], bg='#4a6a8a', fg='white',
                            command=lambda: DocumentViewer(self.parent, self.check_key),
                            width=25, height=2, bd=3, relief="raised")
        docs_btn.place(relx=0.5, rely=0.55, anchor="center")  # Чуть выше
        
        # Кнопка выхода (отдельно, без черного фона)
        exit_btn = tk.Button(self.parent, text="Выйти из кабинета", 
                            font=global_fonts['large'], bg='#8a4a4a', fg='white',
                            command=self.third_floor, width=20, height=2, bd=3, relief="raised")
        exit_btn.place(relx=0.5, rely=0.75, anchor="center")  # Внизу
        
    def check_key(self, num):
        """Проверка выбранного документа"""
        if num == 2:  # Правильный документ
            self.has_basement_key = True
            # Показываем сообщение об успехе прямо в кабинете
            self.show_key_success()
        else:
            self.death_ending()
    def show_key_success(self):
        """Показывает сообщение об успехе в кабинете"""
        self.clear_window()
        
        # Фон кабинета
        try:
            img = Image.open("class_third_floor.png")
            img = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image = ImageTk.PhotoImage(img)
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
            canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
            canvas.pack()
        except:
            canvas = tk.Canvas(self.parent, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#3a4a5a")
            canvas.pack()
        
        # Сообщение об успехе
        success_bg = tk.Frame(self.parent, bg='black', bd=3, relief="solid")
        success_bg.place(relx=0.5, rely=0.4, anchor="center")
        
        success_label = tk.Label(success_bg, 
                                text="КЛЮЧ ОТ ЗАПАСНОГО ВЫХОДА НАЙДЕН!",
                                font=global_fonts['large'], bg='black', fg='#4aff4a',
                                wraplength=500, justify="center")
        success_label.pack(padx=30, pady=30)
        
        # Кнопка выхода
        tk.Button(self.parent, text="🚪 Выйти из кабинета", 
                font=global_fonts['large'], bg='#8a4a4a', fg='white',
                command=self.third_floor, width=20, height=2).place(relx=0.5, rely=0.7, anchor="center")
        
    def show_death_from_riddle(self):
        """Показывает смерть от сущности при неверном ответе на загадку"""
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
            canvas.create_text(400, 300, text="🐺", font=('Arial', 100), fill="red")
            canvas.create_text(400, 400, text="СУЩНОСТЬ НАШЛА ТЕБЯ", 
                            font=global_fonts['large'], fill="white")

        canvas.create_text(WINDOW_WIDTH//2, WINDOW_HEIGHT//2,
                        text="ТЫ НЕ СПРАВИЛСЯ С ЗАГАДКОЙ...\n\nКрасный волк поражает тебя мощным зарядом энергии.\n\nКОНЕЦ ИГРЫ",
                        fill="white", font=global_fonts['large'], justify="center")

        tk.Button(self.parent, text="В главное меню", font=global_fonts['large'],
                bg="#4a4a4a", fg="white", command=self.show_main_menu).place(relx=0.5, rely=0.8, anchor="center")
        
            
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

        canvas.create_text(WINDOW_WIDTH//2, 100, text="ПОДВАЛ",
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

        # Кнопка возврата на второй этаж (в начало коридора)
        btn_frame = tk.Frame(self.parent, bg='black', bd=3, relief="raised")
        btn_frame.place(relx=0.5, rely=0.8, anchor="center")
        
        tk.Button(btn_frame, text="⬆ На второй этаж", font=global_fonts['small'],
                 bg='#4a4a4a', fg='white', command=self.second_floor_1, width=17).pack(side="left", padx=0)
    

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

        # Титры (без черного фона)
        credits_frame = tk.Frame(self.parent, bg='#87CEEB')
        credits_frame.place(relx=0.5, rely=0.5, anchor="center")  # По центру экрана

        credits_text = """Создатели игры: Леденцы из барбариски
    Вдохновлено историей колледжа Винкс
    © 2026 Все права защищены"""

        credits_label = tk.Label(credits_frame,
                                text=credits_text,
                                font=global_fonts['small'], bg='#87CEEB', fg='#000080', justify="center")
        credits_label.pack()

        # Кнопка в главное меню (чуть ниже)
        tk.Button(self.parent,
                text="🏠 В главное меню",
                font=global_fonts['large'],
                bg='#4a4a4a', fg='white', activebackground='#6a6a6a',
                command=self.show_main_menu, width=20, height=2).place(relx=0.5, rely=0.7, anchor="center")
        


    def save_game(self):
        """Сохраняет состояние игры"""
        saved_data = {
            "solved_puzzle": self.solved_puzzle,
            "has_museum_key": self.has_museum_key,
            "has_basement_key": self.has_basement_key,
            "sphinx_passed": self.sphinx_passed,
            "password_parts": self.password_parts,
            "code_words": self.code_words,
            "current_location": self.current_location,
            "dialogue_stage": getattr(self, 'dialogue_stage', 0)  # Добавить
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
            "second_floor_1": "Второй этаж (начало коридора)",
            "second_floor_2": "Второй этаж (основной коридор)",
            "room_17": "Кабинет №17 (серверная)",
            "room_22": "Компьютерный класс",
            "museum_closed": "Музей (закрыт)",
            "museum_open": "Музей (открыт)",
            "third_floor": "Третий этаж",
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
                self.code_words = saved_data.get("code_words", {})
                self.current_location = saved_data.get("current_location", "first_floor")
                self.dialogue_stage = saved_data.get("dialogue_stage", 0)  # Добавить
                
                messagebox.showinfo("💾 Загрузка", f"Игра успешно загружена!\nПродолжаем с: {self.get_location_name()}")
                
                # Переходим на сохраненную локацию
                if self.current_location == "first_floor":
                    self.first_floor()
                elif self.current_location == "second_floor_1":
                    self.second_floor_1()
                elif self.current_location == "second_floor_2":
                    self.second_floor_2()
                elif self.current_location == "room_17":  # Добавлено ДО else
                    self.room_17()
                elif self.current_location == "museum_closed":
                    self.show_museum_closed()
                elif self.current_location == "museum_open":
                    self.show_museum_open()
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
                    self.first_floor()
            
                
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
