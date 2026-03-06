import tkinter as tk
from tkinter import messagebox
from random import shuffle
from PIL import Image, ImageTk
import os

class Game:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Игра Пятнашки")
        
        # Получаем текущую директорию
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Загружаем изображения из: {self.current_dir}")
        
        # Список ваших изображений (img1.png закреплена, остальные будут перемещаться)
        image_files = ['img1.png', 'img3.png', 'img4.png', 'img5.png', 
                      'img6.png', 'img7.png', 'img8.png', 'img9.png']
        
        # Загружаем изображения
        self.images = []
        for i, filename in enumerate(image_files):
            img_path = os.path.join(self.current_dir, filename)
            try:
                if os.path.exists(img_path):
                    # Загружаем и изменяем размер изображения до 100x100
                    pil_image = Image.open(img_path)
                    pil_image = pil_image.resize((100, 100), Image.Resampling.LANCZOS)
                    self.images.append(ImageTk.PhotoImage(pil_image))
                    print(f"Загружено: {filename}")
                else:
                    print(f"Файл не найден: {img_path}")
                    # Создаем заглушку если файл не найден
                    self.images.append(self.create_placeholder(i+1, filename))
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")
                self.images.append(self.create_placeholder(i+1, filename))
        
        # Создаем пустую плитку (серую)
        self.empty_image = self.create_empty_tile()
        
        # Начальное расположение плиток
        # Индекс 0 (img1.png) всегда на позиции 0 (левый верхний угол)
        # Остальные 7 изображений перемешиваем на позиции 1-7, позиция 8 пустая
        self.board = [0]  # Первая плитка закреплена на позиции 0
        remaining = list(range(1, 8))  # Индексы 1-7 для остальных изображений
        shuffle(remaining)
        self.board.extend(remaining)  # Добавляем перемешанные на позиции 1-7
        self.board.append(None)  # Пустая плитка на позиции 8
        
        self.empty_idx = self.board.index(None)
        
        self.buttons = []
        for i in range(9):
            # Для первой кнопки отключаем возможность нажатия
            if i == 0:
                button = tk.Button(
                    self.root,
                    image=self.get_image(i),
                    state=tk.DISABLED  # Отключаем кнопку
                )
            else:
                button = tk.Button(
                    self.root,
                    image=self.get_image(i),
                    command=lambda idx=i: self.move(idx)
                )
            button.grid(row=i//3, column=i%3, padx=1, pady=1)
            self.buttons.append(button)
    
    def create_placeholder(self, number, filename):
        """Создает заглушку если изображение не найдено"""
        img = Image.new('RGB', (100, 100), color='gray')
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 99, 99], outline='black', width=2)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        text = f"miss {filename}"
        draw.text((10, 40), text, fill='white', font=font)
        
        return ImageTk.PhotoImage(img)
    
    def create_empty_tile(self):
        """Создает изображение пустой плитки"""
        img = Image.new('RGB', (100, 100), color='lightgray')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 99, 99], outline='black', width=2)
        return ImageTk.PhotoImage(img)
    
    def move(self, index):
        """Перемещает плитку (первая плитка закреплена и не двигается)"""
        # Первая плитка (index 0) не двигается
        if index == 0:
            return
        
        # Проверяем, можно ли переместить (соседняя ли клетка с пустой)
        empty_row, empty_col = self.empty_idx // 3, self.empty_idx % 3
        curr_row, curr_col = index // 3, index % 3
        
        # Проверяем, находятся ли клетки рядом
        if (abs(curr_row - empty_row) == 1 and curr_col == empty_col) or \
           (abs(curr_col - empty_col) == 1 and curr_row == empty_row):
            
            # Меняем местами плитки
            self.board[index], self.board[self.empty_idx] = self.board[self.empty_idx], self.board[index]
            
            # Обновляем изображения
            self.buttons[index].config(image=self.get_image(index))
            self.buttons[self.empty_idx].config(image=self.get_image(self.empty_idx))
            
            # Обновляем позицию пустой плитки
            self.empty_idx = index
            
            # Проверяем победу (первая плитка всегда на месте, проверяем остальные)
            # Правильный порядок: [0, 1, 2, 3, 4, 5, 6, 7, None]
            if self.board == [0, 1, 2, 3, 4, 5, 6, 7, None]:
                messagebox.showinfo("Поздравляем!", "Вы собрали головоломку!")
    
    def get_image(self, index):
        """Возвращает изображение для указанной позиции"""
        if self.board[index] is None:
            return self.empty_image
        else:
            return self.images[self.board[index]]
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = Game()
    game.run()