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

# Тесты для вспомогательных функций
class TestHelperFunctions:
    """Тесты для вспомогательных функций"""
    
    def test_split_long_text_short(self):
        """Тест разбиения короткого текста"""
        text = "Короткий текст"
        result = split_long_text(text, max_length=20)
        assert result == "Короткий текст"
        assert "\n" not in result
    
    def test_split_long_text_long(self):
        """Тест разбиения длинного текста"""
        text = "Это очень длинный текст который должен быть разбит на несколько строк"
        result = split_long_text(text, max_length=15)
        assert "\n" in result
        lines = result.split('\n')
        assert all(len(line) <= 20 for line in lines)
    
    def test_split_long_text_empty(self):
        """Тест разбиения пустого текста"""
        result = split_long_text("")
        assert result == ""

# Тесты для класса WirePuzzle
class TestWirePuzzle:
    """Тесты для игры в пятнашки"""
    
    @patch('Test_play.os.path.exists')
    @patch('Test_play.Image.open')
    def test_puzzle_initialization(self, mock_image_open, mock_exists, root):
        """Тест инициализации игры в пятнашки"""
        # Настройка моков
        mock_exists.return_value = True
        mock_image = MagicMock()
        mock_image.resize.return_value = mock_image
        mock_image_open.return_value = mock_image
        
        # Создаем мок для on_complete
        on_complete = Mock()
        
        # Создаем экземпляр головоломки
        puzzle = WirePuzzle(root, on_complete)
        
        # Проверяем создание окна
        assert puzzle.puzzle_window is not None
        assert puzzle.puzzle_window.title() == "🔧 Серверная - Ремонт проводов"
        
        # Проверяем начальное состояние
        assert len(puzzle.board) == 9
        assert puzzle.board[0] == 0  # Первая плитка закреплена
        assert None in puzzle.board  # Есть пустая плитка
    
    def test_move_valid(self, root):
        """Тест валидного перемещения плитки"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        # Сохраняем начальное состояние
        initial_board = puzzle.board.copy()
        empty_idx = puzzle.empty_idx
        
        # Находим соседнюю с пустой клетку
        empty_row, empty_col = empty_idx // 3, empty_idx % 3
        moved = False
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = empty_row + dr, empty_col + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                neighbor_idx = nr * 3 + nc
                if neighbor_idx != 0:  # Не двигаем первую плитку
                    with patch('tkinter.messagebox.showinfo'):
                        puzzle.move(neighbor_idx)
                        # Проверяем, что состояние изменилось
                        assert puzzle.board != initial_board
                        moved = True
                        break
        
        if not moved:
            pytest.skip("Нет доступных для перемещения соседних плиток")
    
    def test_move_invalid(self, root):
        """Тест невалидного перемещения плитки"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        initial_board = puzzle.board.copy()
        
        # Пытаемся переместить первую плитку
        puzzle.move(0)
        assert puzzle.board == initial_board
        
        # Пытаемся переместить далекую плитку (если есть такая возможность)
        for i in range(1, 9):
            if abs(i - puzzle.empty_idx) > 3:  # Не соседняя
                puzzle.move(i)
                assert puzzle.board == initial_board
                break
    
    def test_puzzle_completion(self, root):
        """Тест завершения головоломки"""
        on_complete = Mock()
        puzzle = WirePuzzle(root, on_complete)
        
        # Мокаем messagebox чтобы избежать реального диалога
        with patch('tkinter.messagebox.showinfo') as mock_showinfo:
            # Устанавливаем выигрышную комбинацию
            puzzle.board = [0, 1, 2, 3, 4, 5, 6, 7, None]
            puzzle.empty_idx = 8
            # Пытаемся сделать ход
            with patch.object(puzzle, 'on_complete') as mock_on_complete:
                puzzle.move(7)  # Перемещаем плитку 7 на место пустой

# Тесты для класса DocumentViewer
class TestDocumentViewer:
    """Тесты для просмотрщика документов"""
    
    def test_document_viewer_initialization(self, root):
        """Тест инициализации просмотрщика документов"""
        on_choice = Mock()
        # Мокаем открытие изображений
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        assert viewer.viewer_window is not None
        assert viewer.viewer_window.title() == "Документы"
    
    @patch('Test_play.messagebox.askyesno')
    def test_choose_document(self, mock_askyesno, root):
        """Тест выбора документа"""
        mock_askyesno.return_value = True
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        viewer.choose_document(2)
        
        # Проверяем, что on_choice вызван с правильным аргументом
        on_choice.assert_called_once_with(2)
    
    @patch('Test_play.messagebox.askyesno')
    def test_choose_document_cancel(self, mock_askyesno, root):
        """Тест отмены выбора документа"""
        mock_askyesno.return_value = False
        on_choice = Mock()
        
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            viewer = DocumentViewer(root, on_choice)
        
        viewer.choose_document(2)
        
        # Проверяем, что on_choice НЕ вызван
        on_choice.assert_not_called()
        
        # Проверяем, что окно все еще существует
        assert viewer.viewer_window.winfo_exists()

# Тесты для класса Game
class TestGame:
    """Основные тесты для игры"""
    
    def test_game_initialization(self, game):
        """Тест инициализации игры"""
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
        """Тест очистки окна"""
        # Добавляем несколько виджетов
        tk.Label(game.parent).pack()
        tk.Button(game.parent).pack()
        
        # Сохраняем панель сохранения
        save_panel = game.save_panel
        
        game.clear_window()
        
        # Проверяем, что все виджеты кроме save_panel удалены
        widgets = game.parent.winfo_children()
        assert len(widgets) == 1
        assert widgets[0] == save_panel
    
    def test_start_new_game(self, game):
        """Тест начала новой игры"""
        with patch.object(game, 'show_prologue') as mock_show_prologue:
            game.start_new_game()
            
            # Проверяем сброс состояния
            assert game.solved_puzzle == False
            assert game.has_museum_key == False
            assert game.has_basement_key == False
            assert game.sphinx_passed == False
            assert game.password_parts == []
            assert game.code_words == {}
            
            # Проверяем вызов show_prologue
            mock_show_prologue.assert_called_once()
    
    def test_show_main_menu(self, game):
        """Тест отображения главного меню"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.show_main_menu()
        assert game.current_location == "main_menu"
    
    def test_first_floor(self, game):
        """Тест первого этажа"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.first_floor()
        assert game.current_location == "first_floor"
    
    def test_second_floor_1(self, game):
        """Тест первого коридора второго этажа"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.second_floor_1()
        assert game.current_location == "second_floor_1"
    
    def test_second_floor_2(self, game):
        """Тест второго коридора второго этажа"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.second_floor_2()
        assert game.current_location == "second_floor_2"
    
    def test_room_17(self, game):
        """Тест кабинета №17"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.room_17()
        assert game.current_location == "room_17"
    
    def test_room_22(self, game):
        """Тест компьютерного класса"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.room_22()
        assert game.current_location == "room_22"
    
    def test_museum_without_key(self, game):
        """Тест музея без ключа"""
        game.has_museum_key = False
        
        with patch('Test_play.messagebox.showinfo') as mock_showinfo:
            game.museum()
            mock_showinfo.assert_called_once_with("🏛 Музей", "Дверь заперта. Нужен ключ.")
    
    def test_museum_with_key(self, game):
        """Тест музея с ключом"""
        game.has_museum_key = True
        
        with patch.object(game, 'show_museum_closed') as mock_show:
            with patch('Test_play.Image.open') as mock_image_open:
                mock_image_open.side_effect = FileNotFoundError
                game.museum()
            mock_show.assert_called_once()
    
    def test_find_museum_key(self, game):
        """Тест нахождения ключа от музея"""
        with patch('Test_play.messagebox.showinfo'):
            with patch.object(game, 'room_22') as mock_room:
                game.find_museum_key()
                mock_room.assert_called()
        
        assert game.has_museum_key == True
    
    def test_third_floor(self, game):
        """Тест третьего этажа"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.third_floor()
        assert game.current_location == "third_floor"
    
    def test_basement_without_key(self, game):
        """Тест подвала без ключа"""
        game.has_basement_key = False
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.basement()
        assert game.current_location == "basement"
    
    def test_basement_with_key(self, game):
        """Тест подвала с ключом"""
        game.has_basement_key = True
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.basement()
        assert game.current_location == "basement"
    
    def test_good_ending(self, game):
        """Тест хорошей концовки"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.good_ending()
        assert game.current_location == "good_ending"
    
    def test_death_ending(self, game):
        """Тест плохой концовки"""
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.death_ending()
        assert game.current_location == "death"
    
    def test_puzzle_complete(self, game):
        """Тест завершения головоломки"""
        with patch.object(game, 'second_floor_2') as mock_floor:
            game.puzzle_complete()
            assert game.solved_puzzle == True
            mock_floor.assert_called_once()
    
    def test_show_computer_task_already_solved(self, game):
        """Тест показа задания для уже решенного компьютера"""
        game.password_parts = ["part1"]
        
        with patch('Test_play.messagebox.showinfo') as mock_showinfo:
            game.show_computer_task(1)
            mock_showinfo.assert_called_once_with("ℹ️ Компьютер", "Ответ на компьютер 1 уже введен!")
    
    def test_check_key_correct(self, game):
        """Тест проверки правильного документа"""
        game.check_key(2)
        assert game.has_basement_key == True
    
    def test_check_key_wrong(self, game):
        """Тест проверки неправильного документа"""
        with patch.object(game, 'death_ending') as mock_death:
            game.check_key(1)
            mock_death.assert_called_once()
    
    def test_android_dialogue_progression(self, game):
        """Тест progression диалога с андроидом"""
        # Создаем необходимые атрибуты для диалога
        game.dialogue_stage = 0
        game.dialogue_window = tk.Toplevel(game.parent)
        game.dialogue_canvas = tk.Canvas(game.dialogue_window)
        game.dialogue_text_frame = tk.Frame(game.dialogue_canvas)
        
        # Переходим к следующему этапу
        with patch.object(game, 'update_android_dialogue'):
            game.next_dialogue_stage()
            assert game.dialogue_stage == 1
            
            game.next_dialogue_stage()
            assert game.dialogue_stage == 2
            
            # Начинаем загадки
            game.start_riddles()
            assert game.dialogue_stage == 3
        
        # Закрываем окно диалога
        game.dialogue_window.destroy()

# Тесты для сохранения/загрузки
class TestSaveLoad:
    """Тесты для системы сохранения"""
    
    def test_save_game(self, game):
        """Тест сохранения игры"""
        # Настраиваем состояние игры
        game.solved_puzzle = True
        game.has_museum_key = True
        game.has_basement_key = False
        game.sphinx_passed = True
        game.password_parts = ["part1", "part2"]
        game.code_words = {1: "PRINT", 2: "BREAK"}
        game.current_location = "room_22"
        game.dialogue_stage = 3
        
        # Мокаем файловые операции
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            with patch('json.dump') as mock_json_dump:
                with patch('Test_play.messagebox.showinfo'):
                    game.save_game()
                    
                    # Проверяем, что файл был открыт
                    mock_file.assert_called_once_with("save.json", "w", encoding='utf-8')
                    mock_json_dump.assert_called_once()
    
    def test_load_game(self, game):
        """Тест загрузки игры"""
        # Подготавливаем тестовые данные
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
        
        # Мокаем открытие файла
        mock_file = mock_open(read_data=json.dumps(test_data))
        with patch('builtins.open', mock_file):
            with patch('json.load', return_value=test_data):
                with patch('Test_play.messagebox.showinfo'):
                    with patch.object(game, 'room_22') as mock_room:
                        game.load_game()
                        
                        # Проверяем загрузку состояния
                        assert game.solved_puzzle == True
                        assert game.has_museum_key == True
                        assert game.sphinx_passed == True
                        assert "part1" in game.password_parts
                        assert game.code_words[1] == "PRINT"
                        
                        # Проверяем переход на нужную локацию
                        mock_room.assert_called_once()
    
    def test_load_game_file_not_found(self, game):
        """Тест загрузки при отсутствии файла"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('Test_play.messagebox.showerror') as mock_error:
                game.load_game()
                mock_error.assert_called_once_with("❌ Ошибка", "Нет сохранённых файлов!")
    
    def test_load_game_exception(self, game):
        """Тест загрузки с общей ошибкой"""
        with patch('builtins.open', side_effect=Exception("Test error")):
            with patch('Test_play.messagebox.showerror') as mock_error:
                game.load_game()
                mock_error.assert_called_once()
    
    def test_get_location_name(self, game):
        """Тест получения названия локации"""
        test_cases = [
            ("first_floor", "Первый этаж"),
            ("second_floor_1", "Второй этаж (начало коридора)"),
            ("second_floor_2", "Второй этаж (основной коридор)"),
            ("room_17", "Кабинет №17 (серверная)"),
            ("room_22", "Компьютерный класс"),
            ("museum_closed", "Музей (закрыт)"),
            ("museum_open", "Музей (открыт)"),
            ("third_floor", "Третий этаж"),
            ("basement", "Подвал"),
            ("main_menu", "Главное меню"),
            ("prologue", "Пролог"),
            ("death", "Смерть"),
            ("good_ending", "Хорошая концовка"),
            ("unknown", "Неизвестно")
        ]
        
        for location, expected_name in test_cases:
            game.current_location = location
            assert game.get_location_name() == expected_name

# Тесты для граничных случаев
class TestEdgeCases:
    """Тесты для граничных случаев"""
    
    def test_empty_password_parts(self, game):
        """Тест с пустыми частями пароля"""
        game.password_parts = []
        with patch('Test_play.Image.open') as mock_image_open:
            mock_image_open.side_effect = FileNotFoundError
            game.room_22()  # Не должно вызвать ошибок
    
    def test_code_words_empty(self, game):
        """Тест с пустыми кодовыми словами"""
        game.code_words = {}
        game.password_parts = ["part1", "part2", "part3"]
        game.show_password_window()  # Не должно вызвать ошибок
    
    def test_dialogue_stage_out_of_range(self, game):
        """Тест с невалидным этапом диалога"""
        # Создаем необходимые атрибуты для диалога
        game.dialogue_stage = 999
        game.dialogue_window = tk.Toplevel(game.parent)
        game.dialogue_canvas = tk.Canvas(game.dialogue_window)
        game.dialogue_text_frame = tk.Frame(game.dialogue_canvas)
        
        # Проверяем, что методы диалога не падают
        with patch.object(game, 'update_android_dialogue'):
            game.next_dialogue_stage()
        
        # Закрываем окно диалога
        game.dialogue_window.destroy()
    
    def test_show_help(self, game):
        """Тест показа справки"""
        with patch('Test_play.messagebox.showinfo') as mock_showinfo:
            game.show_help()
            mock_showinfo.assert_called_once()

# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты"""
    
    def test_full_game_flow(self, game):
        """Тест полного прохождения игры"""
        # Мокаем все операции с изображениями и messagebox
        with patch('Test_play.Image.open') as mock_image_open, \
             patch('Test_play.messagebox.showinfo'), \
             patch('Test_play.messagebox.askyesno', return_value=True):
            
            mock_image_open.side_effect = FileNotFoundError
            
            # Начало игры
            game.start_new_game()
            
            # Пролог
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
            
            # В музей
            game.museum()
            
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