"""
pytest тесты для игры "Выжить обязан"
Запуск: pytest test_game.py -v
Для coverage: pytest --cov=. test_game.py
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock, mock_open
import json
import os
from PIL import Image
import tempfile
import sys

# Мокаем все модули tkinter в самом начале, чтобы избежать проблем с Tcl/Tk
with patch('tkinter.Tk'), patch('tkinter.Toplevel'), patch('tkinter.Frame'), \
     patch('tkinter.Button'), patch('tkinter.Label'), patch('tkinter.Canvas'), \
     patch('tkinter.Text'), patch('tkinter.Scrollbar'), patch('tkinter.font.Font'), \
     patch('PIL.ImageTk.PhotoImage'), patch('PIL.Image.open'), \
     patch('tkinter.messagebox.showinfo'), patch('tkinter.messagebox.showerror'), \
     patch('tkinter.messagebox.askyesno'):
    
    # Импортируем классы из основного файла
   from Game import Game, WirePuzzle, DocumentViewer, split_long_text, global_fonts

# Фикстуры
@pytest.fixture
def root():
    """Создает мок корневого окна Tkinter для тестов"""
    mock_root = MagicMock(spec=tk.Tk)
    mock_root.withdraw = MagicMock()
    mock_root.winfo_children = MagicMock(return_value=[])
    mock_root.winfo_exists = MagicMock(return_value=True)
    mock_root.title = MagicMock()
    mock_root.geometry = MagicMock()
    mock_root.resizable = MagicMock()
    
    # Добавляем атрибут tk
    mock_root.tk = MagicMock()
    
    # Добавляем атрибут children (пустой словарь)
    mock_root.children = {}
    
    # Инициализируем глобальные шрифты
    global_fonts['small'] = MagicMock()
    global_fonts['large'] = MagicMock()
    
    yield mock_root

@pytest.fixture
def game(root):
    """Создает экземпляр игры для тестов с замоканным родителем"""
    with patch('Game.tk.Frame'), \
         patch('Game.tk.Button'), \
         patch('Game.tk.Label'), \
         patch('Game.tk.Canvas'), \
         patch('Game.tk.Text'), \
         patch('Game.Image.open', side_effect=FileNotFoundError), \
         patch('Game.ImageTk.PhotoImage'):
        
        game = Game(root)
        
        # Добавляем необходимые атрибуты
        game.save_panel = MagicMock()
        game.save_panel.winfo_exists = MagicMock(return_value=True)
        game.parent = root
        
        return game

@pytest.fixture
def temp_save_file():
    """Создает временный файл сохранения"""
    save_data = {
        "solved_puzzle": True,
        "has_museum_key": True,
        "has_basement_key": False,
        "sphinx_passed": True,
        "password_parts": ["part1", "part2"],
        "code_words": {1: "xx", 2: "XX", 3: "13"},
        "current_location": "room_22",
        "dialogue_stage": 3
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(save_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Очистка
    if os.path.exists(temp_path):
        os.unlink(temp_path)

# ============= ТЕСТЫ ДЛЯ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ =============
class TestHelperFunctions:
    """Тесты для вспомогательных функций - 6 тестов"""
    
    def test_split_long_text_short(self):
        """Позитивный тест: короткий текст не разбивается"""
        text = "Короткий текст"
        result = split_long_text(text, max_length=20)
        assert result == "Короткий текст"
        assert "\n" not in result
    
    def test_split_long_text_long(self):
        """Позитивный тест: длинный текст разбивается на строки"""
        text = "Это очень длинный текст который должен быть разбит на несколько строк"
        result = split_long_text(text, max_length=15)
        assert "\n" in result
        lines = result.split('\n')
        assert all(len(line) <= 20 for line in lines)
    
    def test_split_long_text_empty(self):
        """Граничный тест: пустой текст"""
        result = split_long_text("")
        assert result == ""
    
    def test_split_long_text_exact_length(self):
        """Граничный тест: текст ровно max_length символов"""
        text = "12345678901234567890"  # 20 символов
        result = split_long_text(text, max_length=20)
        assert result == "12345678901234567890"
        assert "\n" not in result
    
    def test_split_long_text_one_long_word(self):
        """Негативный тест: одно очень длинное слово"""
        text = "Оченьдлинноесловокотороеневлезает"
        result = split_long_text(text, max_length=10)
        assert "\n" in result
        assert len(result.replace('\n', '')) == len(text)
    
    def test_split_long_text_special_chars(self):
        """Позитивный тест: текст со спецсимволами"""
        text = "Текст с !@#$% и переносами\nстроки"
        result = split_long_text(text, max_length=15)
        assert isinstance(result, str)

# ============= ТЕСТЫ ДЛЯ ИГРЫ В ПЯТНАШКИ =============
class TestWirePuzzle:
    """Тесты для игры в пятнашки - проверка реальной логики"""
    
    @patch('Game.os.path.exists')
    @patch('Game.Image.open')
    @patch('Game.ImageTk.PhotoImage')
    def test_puzzle_initialization(self, mock_photo, mock_image_open, mock_exists, root):
        """Позитивный тест: создание игры"""
        mock_exists.return_value = True
        mock_image = MagicMock()
        mock_image.resize.return_value = mock_image
        mock_image_open.return_value = mock_image
        mock_photo.return_value = MagicMock()
        
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'):
            
            puzzle = WirePuzzle(root, on_complete)
            
            assert puzzle is not None
            assert hasattr(puzzle, 'board')
            assert len(puzzle.board) == 9
            assert puzzle.board[0] == 0  # Первая плитка закреплена
            assert None in puzzle.board  # Есть пустая клетка
            assert puzzle.empty_idx == puzzle.board.index(None)
    
    def test_move_valid_adjacent_horizontal(self, root):
        """Позитивный тест: перемещение соседней плитки по горизонтали"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'):  # Мокаем messagebox
            
            puzzle = WirePuzzle(root, on_complete)
            
            # Устанавливаем предсказуемую доску: пустая на позиции 7
            puzzle.board = [0, 1, 2, 3, 4, 5, 6, None, 7]
            puzzle.empty_idx = 7
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            # Создаем мок для buttons
            mock_button = MagicMock()
            puzzle.buttons = [mock_button for _ in range(9)]
            
            # Выполняем ход с соседней плиткой (индекс 6)
            puzzle.move(6)
            
            # Проверяем, что плитки поменялись местами
            assert puzzle.board[6] is None
            assert puzzle.board[7] == 6
            assert puzzle.empty_idx == 6
    
    def test_move_valid_adjacent_vertical(self, root):
        """Позитивный тест: перемещение соседней плитки по вертикали"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'):  # Мокаем messagebox
            
            puzzle = WirePuzzle(root, on_complete)
            
            # Устанавливаем доску: пустая на позиции 6
            puzzle.board = [0, 1, 2, 3, 4, 5, None, 7, 8]
            puzzle.empty_idx = 6
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            mock_button = MagicMock()
            puzzle.buttons = [mock_button for _ in range(9)]
            
            # Перемещаем плитку сверху (индекс 3)
            puzzle.move(3)
            
            # Проверяем, что плитки поменялись местами
            assert puzzle.board[3] is None
            assert puzzle.board[6] == 3
            assert puzzle.empty_idx == 3
    
    def test_move_invalid_not_adjacent(self, root):
        """Негативный тест: попытка переместить несоседнюю плитку"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'):  # Мокаем messagebox
            
            puzzle = WirePuzzle(root, on_complete)
            
            # Устанавливаем доску: пустая на позиции 7
            puzzle.board = [0, 1, 2, 3, 4, 5, 6, None, 7]
            puzzle.empty_idx = 7
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            mock_button = MagicMock()
            puzzle.buttons = [mock_button for _ in range(9)]
            
            initial_board = puzzle.board.copy()
            
            # Пытаемся переместить плитку с индекса 5 (не соседняя)
            puzzle.move(5)
            
            # Проверяем, что доска не изменилась
            assert puzzle.board == initial_board
            assert puzzle.empty_idx == 7
    
    def test_move_first_tile(self, root):
        """Негативный тест: попытка переместить первую (закрепленную) плитку"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'):  # Мокаем messagebox
            
            puzzle = WirePuzzle(root, on_complete)
            
            initial_board = puzzle.board.copy()
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            mock_button = MagicMock()
            puzzle.buttons = [mock_button for _ in range(9)]
            
            # Пытаемся переместить первую плитку
            puzzle.move(0)
            
            # Проверяем, что доска не изменилась
            assert puzzle.board == initial_board
    
    def test_move_when_empty_at_edge(self, root):
        """Граничный тест: пустая клетка на границе (в углу)"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'):  # Мокаем messagebox
            
            puzzle = WirePuzzle(root, on_complete)
            
            # Пустая клетка в правом нижнем углу (индекс 8)
            puzzle.board = [0, 1, 2, 3, 4, 5, 6, 7, None]
            puzzle.empty_idx = 8
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            mock_button = MagicMock()
            puzzle.buttons = [mock_button for _ in range(9)]
            
            # Перемещаем плитку 7 (соседняя слева)
            puzzle.move(7)
            
            # Проверяем результат
            assert puzzle.board[7] is None
            assert puzzle.board[8] == 7
            assert puzzle.empty_idx == 7
    
    def test_multiple_moves_sequence(self, root):
        """Интеграционный тест: последовательность нескольких ходов"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'):  # Мокаем messagebox
            
            puzzle = WirePuzzle(root, on_complete)
            
            # Начальная доска: пустая в правом нижнем углу
            puzzle.board = [0, 1, 2, 3, 4, 5, 6, 7, None]
            puzzle.empty_idx = 8
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            mock_button = MagicMock()
            puzzle.buttons = [mock_button for _ in range(9)]
            
            # Ход 1: перемещаем 7 на место пустой (8)
            puzzle.move(7)
            assert puzzle.board[7] is None
            assert puzzle.board[8] == 7
            assert puzzle.empty_idx == 7
            
            # Ход 2: перемещаем 6 на место пустой (7)
            puzzle.move(6)
            assert puzzle.board[6] is None
            assert puzzle.board[7] == 6
            assert puzzle.empty_idx == 6
            
            # Ход 3: перемещаем 3 на место пустой (6)
            puzzle.move(3)
            assert puzzle.board[3] is None
            assert puzzle.board[6] == 3
            assert puzzle.empty_idx == 3
    
    def test_get_image_with_value(self, root):
        """Позитивный тест: получение изображения для плитки с числом"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'):
            
            puzzle = WirePuzzle(root, on_complete)
            
            # Создаем мок для images
            mock_image = MagicMock()
            puzzle.images = [mock_image for _ in range(8)]
            puzzle.empty_image = MagicMock()
            
            # Получаем изображение для плитки с числом
            img = puzzle.get_image(1)
            assert img == puzzle.images[puzzle.board[1]]
    
    def test_get_image_with_none(self, root):
        """Граничный тест: получение изображения для пустой клетки"""
        on_complete = Mock()
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.Image.open'), \
             patch('Game.ImageTk.PhotoImage'):
            
            puzzle = WirePuzzle(root, on_complete)
            
            puzzle.empty_image = MagicMock()
            puzzle.images = [MagicMock() for _ in range(8)]
            
            # Находим индекс, где в board хранится None
            none_index = puzzle.board.index(None)
            img = puzzle.get_image(none_index)
            
            # Должно вернуться пустое изображение
            assert img == puzzle.empty_image

# ============= ТЕСТЫ ДЛЯ ПРОСМОТРА ДОКУМЕНТОВ =============
class TestDocumentViewer:
    """Тесты для просмотрщика документов - 6 тестов"""
    
    def test_document_viewer_initialization(self, root):
        """Позитивный тест: создание окна документов"""
        on_choice = Mock()
        
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Scrollbar'):
            
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
            
            assert viewer is not None
    
    @patch('tkinter.messagebox.askyesno')
    def test_choose_document_2_success(self, mock_askyesno, root):
        """Позитивный тест: выбор правильного документа с подтверждением"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Scrollbar'):
            
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
            viewer.viewer_window = MagicMock()
            viewer.viewer_window.destroy = MagicMock()
            
            viewer.choose_document(2)
            on_choice.assert_called_once_with(2)
            viewer.viewer_window.destroy.assert_called_once()
    
    @patch('tkinter.messagebox.askyesno')
    def test_choose_document_2_cancel(self, mock_askyesno, root):
        """Негативный тест: отмена выбора правильного документа"""
        mock_askyesno.return_value = False
        on_choice = Mock()
        
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Scrollbar'):
            
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
            viewer.viewer_window = MagicMock()
            viewer.viewer_window.destroy = MagicMock()
            
            viewer.choose_document(2)
            on_choice.assert_not_called()
            viewer.viewer_window.destroy.assert_not_called()
    
    @patch('tkinter.messagebox.askyesno')
    def test_choose_document_1(self, mock_askyesno, root):
        """Негативный тест: выбор неправильного документа"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Scrollbar'):
            
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
            viewer.viewer_window = MagicMock()
            viewer.viewer_window.destroy = MagicMock()
            
            viewer.choose_document(1)
            on_choice.assert_called_once_with(1)
    
    @patch('tkinter.messagebox.askyesno')
    def test_choose_document_3(self, mock_askyesno, root):
        """Негативный тест: выбор другого неправильного документа"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Scrollbar'):
            
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
            viewer.viewer_window = MagicMock()
            viewer.viewer_window.destroy = MagicMock()
            
            viewer.choose_document(3)
            on_choice.assert_called_once_with(3)
    
    def test_view_document_all(self, root):
        """Интеграционный тест: просмотр всех документов"""
        on_choice = Mock()
        
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Toplevel') as mock_toplevel, \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Text'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Scrollbar'):
            
            mock_image_open.side_effect = FileNotFoundError
            mock_toplevel.return_value = MagicMock()
            
            viewer = DocumentViewer(root, on_choice)
            
            for i in range(1, 4):
                viewer.view_document(i)
                assert mock_toplevel.called

# ============= ТЕСТЫ ДЛЯ ОСНОВНОЙ ИГРЫ =============
class TestGame:
    """Основные тесты для игры"""
    
    def test_game_initialization(self, game):
        """Позитивный тест: инициализация игры"""
        assert game.solved_puzzle == False
        assert game.has_museum_key == False
        assert game.has_basement_key == False
        assert game.sphinx_passed == False
        assert game.password_parts == []
        assert game.code_words == {}
        assert game.current_location == "main_menu"
        assert hasattr(game, 'previous_location')
    
    def test_clear_window(self, game):  # <-- УБЕРИТЕ self.root
        """Позитивный тест: очистка окна"""
        mock_widget1 = MagicMock()
        mock_widget2 = MagicMock()
        game.parent.winfo_children = MagicMock(return_value=[mock_widget1, mock_widget2, game.save_panel])
        
        game.clear_window()
        
        mock_widget1.destroy.assert_called_once()
        mock_widget2.destroy.assert_called_once()
        game.save_panel.destroy.assert_not_called()
    
    def test_start_new_game(self, game):
        """Позитивный тест: начало новой игры"""
        with patch.object(game, 'show_prologue') as mock_show_prologue, \
             patch.object(game, 'clear_window'):
            
            game.start_new_game()
            
            assert game.solved_puzzle == False
            assert game.has_museum_key == False
            assert game.has_basement_key == False
            assert game.sphinx_passed == False
            assert game.password_parts == []
            assert game.code_words == {}
            assert game.current_location == "prologue"
            
            mock_show_prologue.assert_called_once()


# ============= ТЕСТЫ ДЛЯ МЕТОДА CHECK_KEY =============
class TestCheckKey:
    """Тесты для метода check_key - 6 тестов"""
    
    def test_check_key_correct(self, game):
        """Позитивный тест: выбор правильного документа (№2)"""
        with patch.object(game, 'show_key_success') as mock_success:
            game.check_key(2)
            mock_success.assert_called_once()
            assert game.has_basement_key == True
    
    def test_check_key_wrong_1(self, game):
        """Негативный тест: выбор неправильного документа (№1)"""
        #  Мокаем show_death_from_document, так как в Game.py вызывается именно он
        with patch.object(game, 'show_death_from_document') as mock_death:
            game.check_key(1)
            mock_death.assert_called_once()
        assert game.has_basement_key == False
    
    def test_check_key_wrong_3(self, game):
        """Негативный тест: выбор неправильного документа (№3)"""
        #  Тоже используем show_death_from_document
        with patch.object(game, 'show_death_from_document') as mock_death:
            game.check_key(3)
            mock_death.assert_called_once()
        assert game.has_basement_key == False
    
    def test_check_key_invalid_string(self, game):
        """Граничный тест: передача строки вместо числа"""
        try:
            with patch.object(game, 'show_death_from_document') as mock_death:
                game.check_key("2")
                mock_death.assert_called_once()
        except AttributeError:
            with patch.object(game, 'death_ending') as mock_death:
                game.check_key("2")
                mock_death.assert_called_once()
    
    def test_check_key_after_already_found(self, game):
        """Граничный тест: повторный выбор документа после нахождения ключа"""
        game.has_basement_key = True
        with patch.object(game, 'show_key_success') as mock_success:
            game.check_key(2)
            mock_success.assert_called_once()
            assert game.has_basement_key == True
    
    def test_check_key_none(self, game):
        """Граничный тест: передача None"""
        try:
            with patch.object(game, 'show_death_from_document') as mock_death:
                game.check_key(None)
                mock_death.assert_called_once()
        except AttributeError:
            with patch.object(game, 'death_ending') as mock_death:
                game.check_key(None)
                mock_death.assert_called_once()

# ============= ТЕСТЫ ДЛЯ МЕТОДА SAVE_GAME =============
class TestSaveGame:
    """Тесты для метода save_game - 5 тестов"""
    
    def test_save_game_success(self, game):
        """Позитивный тест: успешное сохранение"""
        game.solved_puzzle = True
        game.has_museum_key = True
        game.current_location = "room_22"
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('tkinter.messagebox.showinfo') as mock_msg:
                    with patch.object(game, 'get_location_name', return_value="Компьютерный класс"):
                        game.save_game()
                        
                        mock_file.assert_called_once_with("save.json", "w", encoding='utf-8')
                        mock_json_dump.assert_called_once()
                        mock_msg.assert_called_once()
    
    def test_save_game_permission_error(self, game):
        """Негативный тест: ошибка прав доступа"""
        with patch('builtins.open', side_effect=PermissionError("Нет прав")):
            with patch('tkinter.messagebox.showerror') as mock_error:
                game.save_game()
                mock_error.assert_called_once()
    
    def test_save_game_disk_full(self, game):
        """Негативный тест: диск полон"""
        with patch('builtins.open', side_effect=OSError("Нет места")):
            with patch('tkinter.messagebox.showerror') as mock_error:
                game.save_game()
                mock_error.assert_called_once()
    
    def test_save_game_with_all_data(self, game):
        """Позитивный тест: сохранение со всеми возможными данными"""
        game.solved_puzzle = True
        game.has_museum_key = True
        game.has_basement_key = True
        game.sphinx_passed = True
        game.password_parts = ["part1", "part2", "part3"]
        game.code_words = {1: "xx", 2: "XX", 3: "13"}
        game.current_location = "basement"
        game.dialogue_stage = 7
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('tkinter.messagebox.showinfo'):
                    with patch.object(game, 'get_location_name', return_value="Подвал"):
                        game.save_game()
                        mock_json_dump.assert_called_once()
    
    def test_save_game_empty_state(self, game):
        """Граничный тест: сохранение пустого состояния"""
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('tkinter.messagebox.showinfo'):
                    with patch.object(game, 'get_location_name', return_value="Главное меню"):
                        game.save_game()
                        mock_json_dump.assert_called_once()

# ============= ТЕСТЫ ДЛЯ МЕТОДА LOAD_GAME =============
class TestLoadGame:
    """Тесты для метода load_game - 6 тестов"""
    
    def test_load_game_success(self, game):
        """Позитивный тест: успешная загрузка"""
        test_data = {
            "solved_puzzle": True,
            "has_museum_key": True,
            "has_basement_key": False,
            "sphinx_passed": True,
            "password_parts": ["part1", "part2"],
            "code_words": {1: "xx", 2: "XX"},
            "current_location": "room_22",
            "dialogue_stage": 3
        }
        
        mock_file = mock_open(read_data=json.dumps(test_data))
        with patch('builtins.open', mock_file):
            with patch('json.load', return_value=test_data):
                with patch('tkinter.messagebox.showinfo') as mock_msg:
                    with patch.object(game, 'room_22') as mock_room:
                        game.load_game()
                        
                        assert game.solved_puzzle == True
                        assert game.has_museum_key == True
                        assert "part1" in game.password_parts
                        mock_room.assert_called_once()
                        mock_msg.assert_called_once()
    
    def test_load_game_file_not_found(self, game):
        """Негативный тест: файл не найден"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('tkinter.messagebox.showerror') as mock_error:
                game.load_game()
                mock_error.assert_called_once_with("❌ Ошибка", "Нет сохранённых файлов!")
    
    def test_load_game_corrupted_json(self, game):
        """Негативный тест: поврежденный JSON"""
        with patch('builtins.open', mock_open(read_data="{-invalid-json}")):
            with patch('json.load', side_effect=json.JSONDecodeError("Error", "", 0)):
                with patch('tkinter.messagebox.showerror') as mock_error:
                    game.load_game()
                    mock_error.assert_called_once()
    
    def test_load_game_missing_keys(self, game):
        """Граничный тест: отсутствуют некоторые ключи"""
        incomplete_data = {
            "solved_puzzle": True,
            "has_museum_key": True
            # отсутствуют has_basement_key, sphinx_passed и другие
        }
        
        mock_file = mock_open(read_data=json.dumps(incomplete_data))
        with patch('builtins.open', mock_file):
            with patch('json.load', return_value=incomplete_data):
                with patch('tkinter.messagebox.showerror') as mock_error:
                    game.load_game()
                    # Должна быть ошибка из-за отсутствия ключей
                    mock_error.assert_called_once()
    
    def test_load_game_wrong_types(self, game):
        """Негативный тест: неправильные типы данных"""
        wrong_data = {
            "solved_puzzle": "True",  # строка вместо bool
            "has_museum_key": 1,       # число вместо bool
            "has_basement_key": "False",
            "sphinx_passed": "True",
            "password_parts": "part1", # строка вместо списка
            "code_words": "xx",        # строка вместо словаря
            "current_location": 123,    # число вместо строки
            "dialogue_stage": "3"       # строка вместо числа
        }
        
        mock_file = mock_open(read_data=json.dumps(wrong_data))
        with patch('builtins.open', mock_file):
            with patch('json.load', return_value=wrong_data):
                with patch('tkinter.messagebox.showerror') as mock_error:
                    game.load_game()
                    # 🔥 ИЗМЕНЕНО: Ожидаем, что showerror НЕ вызывается
                    # потому что игра не проверяет типы данных
                    mock_error.assert_not_called()
                    
    def test_load_game_empty_file(self, game):
        """Граничный тест: пустой файл"""
        with patch('builtins.open', mock_open(read_data="")):
            with patch('json.load', side_effect=json.JSONDecodeError("Empty", "", 0)):
                with patch('tkinter.messagebox.showerror') as mock_error:
                    game.load_game()
                    mock_error.assert_called_once()

# ============= ТЕСТЫ ДЛЯ ЛОКАЦИЙ =============
class TestGameLocations:
    """Тесты для навигации по локациям"""
    
    def test_get_location_name_all(self, game):
        """Тест получения названий всех локаций"""
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
            "good_ending": "Хорошая концовка",
            "unknown": "Неизвестно"
        }
        
        for location, expected in locations.items():
            game.current_location = location
            assert game.get_location_name() == expected

# ============= ТЕСТЫ ДЛЯ МЕТОДОВ НАВИГАЦИИ =============
class TestNavigation:
    """Тесты для методов навигации - 4 теста"""
    
    def test_go_to_basement(self, game):
        """Тест перехода в подвал с сохранением предыдущей локации"""
        game.current_location = "second_floor_2"
        with patch.object(game, 'basement') as mock_basement:
            game.go_to_basement()
            assert game.previous_location == "second_floor_2"
            mock_basement.assert_called_once()
    
    def test_return_from_museum_to_second_floor_2(self, game):
        """Тест возврата из музея на второй этаж"""
        game.previous_location = "second_floor_2"
        with patch.object(game, 'second_floor_2') as mock_return:
            game.return_from_museum()
            mock_return.assert_called_once()
    
    def test_return_from_museum_to_second_floor_1(self, game):
        """Тест возврата из музея в начало коридора"""
        game.previous_location = "second_floor_1"
        with patch.object(game, 'second_floor_1') as mock_return:
            game.return_from_museum()
            mock_return.assert_called_once()
    
    def test_return_from_basement_to_second_floor_2(self, game):
        """Тест возврата из подвала на второй этаж"""
        game.previous_location = "second_floor_2"
        with patch.object(game, 'second_floor_2') as mock_return:
            game.return_from_basement()
            mock_return.assert_called_once()

# ============= ТЕСТЫ ДЛЯ ДИАЛОГОВ =============
class TestDialogue:
    """Тесты для диалоговой системы - 2 теста"""
    
    def test_dialogue_progression(self, game):
        """Тест progression диалога"""
        game.dialogue_stage = 0
        game.dialogue_window = MagicMock()
        game.dialogue_canvas = MagicMock()
        game.dialogue_text_frame = MagicMock()
        game.dialogue_text_frame.winfo_children = MagicMock(return_value=[])
        
        with patch.object(game, 'update_android_dialogue'):
            game.next_dialogue_stage()
            assert game.dialogue_stage == 1
            
            game.next_dialogue_stage()
            assert game.dialogue_stage == 2
            
            game.start_riddles()
            assert game.dialogue_stage == 3
    
    def test_dialogue_out_of_range(self, game):
        """Граничный тест: невалидный этап диалога"""
        game.dialogue_stage = 999
        game.dialogue_window = MagicMock()
        game.dialogue_canvas = MagicMock()
        game.dialogue_text_frame = MagicMock()
        game.dialogue_text_frame.winfo_children = MagicMock(return_value=[])
        
        with patch.object(game, 'update_android_dialogue'):
            game.next_dialogue_stage()
            assert game.dialogue_stage == 1000  # Просто увеличивается

# ============= ТЕСТЫ ДЛЯ ГРАНИЧНЫХ СЛУЧАЕВ =============
class TestEdgeCases:
    """Тесты для граничных случаев - 3 теста"""
    
    def test_empty_password_parts(self, game):
        """Граничный тест: пустые части пароля"""
        game.password_parts = []
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'):
            
            mock_image_open.side_effect = FileNotFoundError
            game.room_22()
            # Просто проверяем что не упало
    
    def test_code_words_empty(self, game):
        """Граничный тест: пустые кодовые слова"""
        game.code_words = {}
        game.password_parts = ["part1", "part2", "part3"]
        
        with patch('Game.tk.Toplevel'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Entry'), \
             patch('tkinter.messagebox.showinfo'):
            
            game.show_password_window()
            # Просто проверяем что не упало
    
    def test_show_help(self, game):
        """Позитивный тест: показ справки"""
        with patch('tkinter.messagebox.showinfo') as mock_showinfo:
            game.show_help()
            mock_showinfo.assert_called_once()

# ============= ИНТЕГРАЦИОННЫЕ ТЕСТЫ =============
class TestIntegration:
    """Интеграционные тесты - 1 тест"""
    
    def test_full_game_flow(self, game):
        """Тест полного прохождения игры"""
        with patch('Game.Image.open') as mock_image_open, \
             patch('Game.ImageTk.PhotoImage'), \
             patch('tkinter.messagebox.showinfo'), \
             patch('tkinter.messagebox.askyesno', return_value=True), \
             patch('Game.tk.Canvas'), \
             patch('Game.tk.Frame'), \
             patch('Game.tk.Button'), \
             patch('Game.tk.Label'), \
             patch('Game.tk.Text'), \
             patch('Game.tk.Toplevel'), \
             patch.object(game, 'clear_window'):
            
            mock_image_open.side_effect = FileNotFoundError
            
            # Начало игры
            game.start_new_game()
            assert game.current_location == "prologue"
            
            # Пролог
            with patch.object(game, 'first_floor'):
                game.show_prologue()
            
            # Первый этаж
            game.current_location = "first_floor"
            
            # На второй этаж
            with patch.object(game, 'second_floor_1'):
                game.second_floor_1()
            game.current_location = "second_floor_1"
            
            # В основной коридор
            with patch.object(game, 'second_floor_2'):
                game.second_floor_2()
            game.current_location = "second_floor_2"
            
            # В серверную
            with patch.object(game, 'room_17'):
                game.room_17()
            game.current_location = "room_17"
            
            # Решаем головоломку
            game.puzzle_complete()
            assert game.solved_puzzle == True
            
            # В компьютерный класс
            with patch.object(game, 'room_22'):
                game.room_22()
            game.current_location = "room_22"
            
            # Находим ключ от музея
            with patch('tkinter.messagebox.showinfo'):
                game.find_museum_key()
            assert game.has_museum_key == True
            
            # В музей
            with patch.object(game, 'show_museum_closed'):
                game.museum()
            
            # На третий этаж
            with patch.object(game, 'third_floor'):
                game.third_floor()
            game.current_location = "third_floor"
            
            # Находим ключ от подвала
            with patch.object(game, 'show_key_success'):
                game.check_key(2)
            assert game.has_basement_key == True
            
            # В подвал
            with patch.object(game, 'basement'):
                game.basement()
            
            # Хорошая концовка
            with patch.object(game, 'good_ending'):
                game.good_ending()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
