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
import time

# Импортируем классы из основного файла
from Test_play import Game, WirePuzzle, DocumentViewer, split_long_text, global_fonts

# Фикстуры
@pytest.fixture
def root():
    """Создает корневое окно Tkinter для тестов"""
    root = tk.Tk()
    root.withdraw()  # Скрываем окно
    
    # Инициализируем глобальные шрифты
    from tkinter.font import Font
    global_fonts['small'] = Font(family="Arial", size=12, weight="bold")
    global_fonts['large'] = Font(family="Arial", size=14, weight="bold")
    
    yield root
    root.destroy()

@pytest.fixture
def game(root):
    """Создает экземпляр игры для тестов"""
    return Game(root)

@pytest.fixture
def temp_save_file():
    """Создает временный файл сохранения"""
    save_data = {
        "solved_puzzle": True,
        "has_museum_key": True,
        "has_basement_key": False,
        "sphinx_passed": True,
        "password_parts": ["part1", "part2"],
        "code_words": {1: "PRINT", 2: "BREAK"},
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
    """Тесты для вспомогательных функций - 6 тестов (минимум 4-5)"""
    
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
        # Слово должно быть разбито на части
        assert len(result.replace('\n', '')) == len(text)
    
    def test_split_long_text_special_chars(self):
        """Позитивный тест: текст со спецсимволами"""
        text = "Текст с !@#$% и переносами\nстроки"
        result = split_long_text(text, max_length=15)
        assert isinstance(result, str)

# ============= ТЕСТЫ ДЛЯ ИГРЫ В ПЯТНАШКИ =============
class TestWirePuzzle:
    """Тесты для игры в пятнашки - исправленные версии"""
    
    @patch('Test_play.os.path.exists')
    @patch('Test_play.Image.open')
    def test_puzzle_initialization(self, mock_image_open, mock_exists, root):
        """Позитивный тест: создание игры"""
        mock_exists.return_value = True
        mock_image = MagicMock()
        mock_image.resize.return_value = mock_image
        mock_image_open.return_value = mock_image
        
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        assert puzzle.puzzle_window is not None
        assert len(puzzle.board) == 9
        assert puzzle.board[0] == 0
        assert None in puzzle.board
    
    def test_move_valid_adjacent(self, root):
        """Позитивный тест: перемещение соседней плитки"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        initial_board = puzzle.board.copy()
        empty_idx = puzzle.empty_idx
        
        # Находим соседнюю клетку
        moved = False
        empty_row, empty_col = empty_idx // 3, empty_idx % 3
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = empty_row + dr, empty_col + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                neighbor_idx = nr * 3 + nc
                if neighbor_idx != 0:
                    with patch('tkinter.messagebox.showinfo'):
                        # Создаем мок для buttons с методом config
                        mock_button = MagicMock()
                        puzzle.buttons = [mock_button for _ in range(9)]
                        puzzle.move(neighbor_idx)
                        assert puzzle.board != initial_board
                        moved = True
                        break
        if not moved:
            pytest.skip("Нет доступных для перемещения соседних плиток")
    
    def test_move_invalid_not_adjacent(self, root):
        """Негативный тест: перемещение несоседней плитки"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        initial_board = puzzle.board.copy()
        
        # Пытаемся переместить плитку через одну
        moved = False
        for i in range(1, 9):
            if abs(i - puzzle.empty_idx) > 3:
                # Создаем мок для buttons
                mock_button = MagicMock()
                puzzle.buttons = [mock_button for _ in range(9)]
                puzzle.move(i)
                assert puzzle.board == initial_board
                moved = True
                break
        if not moved:
            pytest.skip("Нет подходящей несоседней плитки")
    
    def test_move_first_tile(self, root):
        """Негативный тест: попытка переместить первую плитку"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        initial_board = puzzle.board.copy()
        # Создаем мок для buttons
        mock_button = MagicMock()
        puzzle.buttons = [mock_button for _ in range(9)]
        puzzle.move(0)
        assert puzzle.board == initial_board
    
    def test_move_when_empty_at_edge(self, root):
        """Граничный тест: пустая клетка на границе"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        # Устанавливаем пустую клетку на границе (угол)
        puzzle.board = [0, 1, 2, 3, 4, 5, 6, 7, None]
        puzzle.empty_idx = 8
        
        # Создаем мок для buttons
        mock_button = MagicMock()
        puzzle.buttons = [mock_button for _ in range(9)]
        
        with patch('tkinter.messagebox.showinfo'):
            puzzle.move(7)  # Должно сработать
            assert puzzle.empty_idx == 7
            assert puzzle.board[7] is None
            assert puzzle.board[8] == 7
    
    def test_multiple_moves(self, root):
        """Интеграционный тест: несколько перемещений подряд"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        # Создаем простую доску для тестирования
        puzzle.board = [0, 1, 2, 3, 4, 5, 6, 7, None]
        puzzle.empty_idx = 8
        
        # Создаем мок для buttons
        mock_button = MagicMock()
        puzzle.buttons = [mock_button for _ in range(9)]
        
        moves_made = 0
        with patch('tkinter.messagebox.showinfo'):
            # Делаем несколько ходов
            # Ход 1: перемещаем 7 на место пустой (8)
            if abs(7 - puzzle.empty_idx) in [1, 3]:
                puzzle.move(7)
                moves_made += 1
                # После хода пустая должна быть на 7
                assert puzzle.empty_idx == 7
            
            # Ход 2: перемещаем 6 на место пустой (7)
            if abs(6 - puzzle.empty_idx) in [1, 3]:
                puzzle.move(6)
                moves_made += 1
            
            # Ход 3: перемещаем 3 на место пустой
            if abs(3 - puzzle.empty_idx) in [1, 3]:
                puzzle.move(3)
                moves_made += 1
        
        assert moves_made > 0  # Хотя бы один ход сделан
    
    def test_get_image_with_value(self, root):
        """Позитивный тест: получение изображения с числом"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        # Мокаем self.images
        puzzle.images = [MagicMock() for _ in range(8)]
        
        img = puzzle.get_image(1)
        assert img is not None
    
    def test_get_image_with_none(self, root):
        """Граничный тест: получение пустого изображения"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        # В методе get_image параметр index - это позиция на доске, а не значение
        # Нам нужно передать индекс, где в board хранится None
        none_index = puzzle.board.index(None)
        img = puzzle.get_image(none_index)
        assert img is not None
        assert img == puzzle.empty_image
        
# ============= ТЕСТЫ ДЛЯ ПРОСМОТРА ДОКУМЕНТОВ =============
class TestDocumentViewer:
    """Тесты для просмотрщика документов - 6 тестов (минимум 4-5)"""
    
    def test_document_viewer_initialization(self, root):
        """Позитивный тест: создание окна документов"""
        on_choice = Mock()
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        assert viewer.viewer_window is not None
        assert viewer.viewer_window.title() == "Документы"
    
    @patch('Test_play.messagebox.askyesno')
    def test_choose_document_2_success(self, mock_askyesno, root):
        """Позитивный тест: выбор правильного документа с подтверждением"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        viewer.choose_document(2)
        on_choice.assert_called_once_with(2)
    
    @patch('Test_play.messagebox.askyesno')
    def test_choose_document_2_cancel(self, mock_askyesno, root):
        """Негативный тест: отмена выбора правильного документа"""
        mock_askyesno.return_value = False
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        viewer.choose_document(2)
        on_choice.assert_not_called()
    
    @patch('Test_play.messagebox.askyesno')
    def test_choose_document_1(self, mock_askyesno, root):
        """Негативный тест: выбор неправильного документа"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        viewer.choose_document(1)
        on_choice.assert_called_once_with(1)
    
    @patch('Test_play.messagebox.askyesno')
    def test_choose_document_3(self, mock_askyesno, root):
        """Негативный тест: выбор другого неправильного документа"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        viewer.choose_document(3)
        on_choice.assert_called_once_with(3)
    
    def test_view_document_all(self, root):
        """Интеграционный тест: просмотр всех документов"""
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
            
            # Просматриваем все документы
            for i in range(1, 4):
                with patch('tkinter.Toplevel'):  # Мокаем создание нового окна
                    viewer.view_document(i)

# ============= ТЕСТЫ ДЛЯ ОСНОВНОЙ ИГРЫ =============
class TestGame:
    """Основные тесты для игры - много тестов"""
    
    def test_game_initialization(self, game):
        """Позитивный тест: инициализация игры"""
        assert game.solved_puzzle == False
        assert game.has_museum_key == False
        assert game.has_basement_key == False
        assert game.sphinx_passed == False
        assert game.password_parts == []
        assert game.code_words == {}
        assert game.current_location == "main_menu"
        
        # Проверяем создание панели сохранения
        assert game.save_panel is not None
        assert game.save_panel.winfo_exists()
    
    def test_clear_window(self, game):
        """Позитивный тест: очистка окна"""
        tk.Label(game.parent).pack()
        tk.Button(game.parent).pack()
        
        save_panel = game.save_panel
        game.clear_window()
        
        widgets = game.parent.winfo_children()
        assert len(widgets) == 1
        assert widgets[0] == save_panel
    
    def test_start_new_game(self, game):
        """Позитивный тест: начало новой игры"""
        with patch.object(game, 'show_prologue') as mock_show_prologue:
            game.start_new_game()
            
            assert game.solved_puzzle == False
            assert game.has_museum_key == False
            assert game.has_basement_key == False
            assert game.sphinx_passed == False
            assert game.password_parts == []
            assert game.code_words == {}
            
            mock_show_prologue.assert_called_once()

# ============= ТЕСТЫ ДЛЯ МЕТОДА CHECK_KEY (5 тестов) =============
class TestCheckKey:
    """Тесты для метода check_key - 5 тестов (минимум 4-5)"""
    
    def test_check_key_correct(self, game):
        """Позитивный тест: выбор правильного документа (№2)"""
        game.check_key(2)
        assert game.has_basement_key == True
    
    def test_check_key_wrong_1(self, game):
        """Негативный тест: выбор неправильного документа (№1)"""
        with patch.object(game, 'death_ending') as mock_death:
            game.check_key(1)
            mock_death.assert_called_once()
        assert game.has_basement_key == False
    
    def test_check_key_wrong_3(self, game):
        """Негативный тест: выбор неправильного документа (№3)"""
        with patch.object(game, 'death_ending') as mock_death:
            game.check_key(3)
            mock_death.assert_called_once()
        assert game.has_basement_key == False
    
    def test_check_key_invalid_string(self, game):
        """Граничный тест: передача строки вместо числа"""
        with patch.object(game, 'death_ending') as mock_death:
            game.check_key("2")  # Строка
            mock_death.assert_called_once()  # Должно умереть, т.к. ожидается число
    
    def test_check_key_after_already_found(self, game):
        """Граничный тест: повторный выбор документа после нахождения ключа"""
        game.has_basement_key = True
        # Должно быть все равно, но метод не должен ломаться
        game.check_key(2)
        assert game.has_basement_key == True

# ============= ТЕСТЫ ДЛЯ МЕТОДА SAVE_GAME (5 тестов) =============
class TestSaveGame:
    """Тесты для метода save_game - 5 тестов (минимум 4-5)"""
    
    def test_save_game_success(self, game):
        """Позитивный тест: успешное сохранение"""
        game.solved_puzzle = True
        game.has_museum_key = True
        game.current_location = "room_22"
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('Test_play.messagebox.showinfo') as mock_msg:
                    game.save_game()
                    
                    mock_file.assert_called_once_with("save.json", "w", encoding='utf-8')
                    mock_json_dump.assert_called_once()
                    mock_msg.assert_called_once()
    
    def test_save_game_permission_error(self, game):
        """Негативный тест: ошибка прав доступа"""
        with patch('builtins.open', side_effect=PermissionError("Нет прав")):
            with patch('Test_play.messagebox.showerror') as mock_error:
                game.save_game()
                mock_error.assert_called_once()
    
    def test_save_game_disk_full(self, game):
        """Негативный тест: диск полон"""
        with patch('builtins.open', side_effect=OSError("Нет места")):
            with patch('Test_play.messagebox.showerror') as mock_error:
                game.save_game()
                mock_error.assert_called_once()
    
    def test_save_game_with_all_data(self, game):
        """Позитивный тест: сохранение со всеми возможными данными"""
        game.solved_puzzle = True
        game.has_museum_key = True
        game.has_basement_key = True
        game.sphinx_passed = True
        game.password_parts = ["part1", "part2", "part3"]
        game.code_words = {1: "PRINT", 2: "BREAK", 3: "CONTINUE"}
        game.current_location = "basement"
        game.dialogue_stage = 7
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('Test_play.messagebox.showinfo'):
                    game.save_game()
                    mock_json_dump.assert_called_once()
    
    def test_save_game_empty_state(self, game):
        """Граничный тест: сохранение пустого состояния"""
        # Все значения по умолчанию
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('Test_play.messagebox.showinfo'):
                    game.save_game()
                    mock_json_dump.assert_called_once()

# ============= ТЕСТЫ ДЛЯ МЕТОДА LOAD_GAME (5 тестов) =============
class TestLoadGame:
    """Тесты для метода load_game - 5 тестов (минимум 4-5)"""
    
    def test_load_game_success(self, game):
        """Позитивный тест: успешная загрузка"""
        test_data = {
            "solved_puzzle": True,
            "has_museum_key": True,
            "has_basement_key": False,
            "sphinx_passed": True,
            "password_parts": ["part1", "part2"],
            "code_words": {1: "PRINT", 2: "BREAK"},
            "current_location": "room_22",
            "dialogue_stage": 3
        }
        
        mock_file = mock_open(read_data=json.dumps(test_data))
        with patch('builtins.open', mock_file):
            with patch('json.load', return_value=test_data):
                with patch('Test_play.messagebox.showinfo'):
                    with patch.object(game, 'room_22') as mock_room:
                        game.load_game()
                        
                        assert game.solved_puzzle == True
                        assert game.has_museum_key == True
                        assert "part1" in game.password_parts
                        mock_room.assert_called_once()
    
    def test_load_game_file_not_found(self, game):
        """Негативный тест: файл не найден"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('Test_play.messagebox.showerror') as mock_error:
                game.load_game()
                mock_error.assert_called_once_with("❌ Ошибка", "Нет сохранённых файлов!")
    
    def test_load_game_corrupted_json(self, game):
        """Негативный тест: поврежденный JSON"""
        with patch('builtins.open', mock_open(read_data="{-invalid-json}")):
            with patch('json.load', side_effect=json.JSONDecodeError("Error", "", 0)):
                with patch('Test_play.messagebox.showerror') as mock_error:
                    game.load_game()
                    mock_error.assert_called_once()
    
    def test_load_game_missing_keys(self, game):
        """Граничный тест: отсутствуют некоторые ключи"""
        incomplete_data = {
            "solved_puzzle": True,
            "has_museum_key": True
            # остальных ключей нет
        }
        
        with patch('builtins.open', mock_open()):
            with patch('json.load', return_value=incomplete_data):
                with patch('Test_play.messagebox.showinfo'):
                    with patch.object(game, 'first_floor'):  # Локация по умолчанию
                        game.load_game()  # Не должно упасть
    
    def test_load_game_wrong_types(self, game):
        """Негативный тест: неправильные типы данных"""
        wrong_data = {
            "solved_puzzle": "True",  # строка вместо bool
            "has_museum_key": 1,  # число вместо bool
            "password_parts": "part1"  # строка вместо списка
        }
        
        with patch('builtins.open', mock_open()):
            with patch('json.load', return_value=wrong_data):
                with patch('Test_play.messagebox.showinfo'):
                    with patch.object(game, 'first_floor'):
                        game.load_game()  # Не должно упасть

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

# ============= ТЕСТЫ ДЛЯ ДИАЛОГОВ =============
class TestDialogue:
    """Тесты для диалоговой системы"""
    
    def test_dialogue_progression(self, game):
        """Тест progression диалога"""
        game.dialogue_stage = 0
        game.dialogue_window = tk.Toplevel(game.parent)
        game.dialogue_canvas = tk.Canvas(game.dialogue_window)
        game.dialogue_text_frame = tk.Frame(game.dialogue_canvas)
        
        with patch.object(game, 'update_android_dialogue'):
            game.next_dialogue_stage()
            assert game.dialogue_stage == 1
            
            game.next_dialogue_stage()
            assert game.dialogue_stage == 2
            
            game.start_riddles()
            assert game.dialogue_stage == 3
        
        game.dialogue_window.destroy()
    
    def test_dialogue_out_of_range(self, game):
        """Граничный тест: невалидный этап диалога"""
        game.dialogue_stage = 999
        game.dialogue_window = tk.Toplevel(game.parent)
        game.dialogue_canvas = tk.Canvas(game.dialogue_window)
        game.dialogue_text_frame = tk.Frame(game.dialogue_canvas)
        
        with patch.object(game, 'update_android_dialogue'):
            game.next_dialogue_stage()  # Не должно упасть
        
        game.dialogue_window.destroy()

# ============= ТЕСТЫ ДЛЯ ГРАНИЧНЫХ СЛУЧАЕВ =============
class TestEdgeCases:
    """Тесты для граничных случаев"""
    
    def test_empty_password_parts(self, game):
        """Граничный тест: пустые части пароля"""
        game.password_parts = []
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.room_22()
    
    def test_code_words_empty(self, game):
        """Граничный тест: пустые кодовые слова"""
        game.code_words = {}
        game.password_parts = ["part1", "part2", "part3"]
        game.show_password_window()
    
    def test_show_help(self, game):
        """Позитивный тест: показ справки"""
        with patch('Test_play.messagebox.showinfo') as mock_showinfo:
            game.show_help()
            mock_showinfo.assert_called_once()

# ============= ИНТЕГРАЦИОННЫЕ ТЕСТЫ =============
class TestIntegration:
    """Интеграционные тесты"""
    
    def test_full_game_flow(self, game):
        """Тест полного прохождения игры"""
        with patch('Test_play.Image.open') as mock_image_open, \
             patch('Test_play.messagebox.showinfo'), \
             patch('Test_play.messagebox.askyesno', return_value=True):
            
            mock_image_open.side_effect = FileNotFoundError
            
            # Начало игры
            game.start_new_game()
            game.show_prologue()
            assert game.current_location == "prologue"
            
            # Первый этаж
            game.first_floor()
            assert game.current_location == "first_floor"
            
            # На второй этаж
            game.second_floor_1()
            assert game.current_location == "second_floor_1"
            
            # В основной коридор
            game.second_floor_2()
            assert game.current_location == "second_floor_2"
            
            # В серверную
            game.room_17()
            assert game.current_location == "room_17"
            
            # Решаем головоломку
            game.puzzle_complete()
            assert game.solved_puzzle == True
            
            # В компьютерный класс
            game.room_22()
            assert game.current_location == "room_22"
            
            # Находим ключ от музея
            game.find_museum_key()
            assert game.has_museum_key == True
            
            # На третий этаж
            game.third_floor()
            assert game.current_location == "third_floor"
            
            # Находим ключ от подвала
            game.check_key(2)
            assert game.has_basement_key == True
            
            # В подвал
            game.basement()
            assert game.current_location == "basement"
            
            # Хорошая концовка
            game.good_ending()
            assert game.current_location == "good_ending"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
