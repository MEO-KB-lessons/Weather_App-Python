# Weather_App_GUI.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import datetime
from typing import Optional, Dict
import Weather_App as weather_core

# =============================================================================
# КОНСТАНТЫ ДЛЯ ШРИФТОВ
# =============================================================================

# Основные шрифты
FONT_TITLE = ('Arial', 50, 'bold')          # Для крупной температуры
FONT_HEADER = ('Arial', 18, 'bold')         # Для заголовков карточек
FONT_SUBHEADER = ('Arial', 20, 'bold')      # Для подзаголовков
FONT_NORMAL = ('Arial', 15)                 # Для обычного текста
FONT_SMALL = ('Arial', 14)                  # Для мелкого текста
FONT_VERY_SMALL = ('Arial', 14)              # Для очень мелкого текста
FONT_BUTTON = ('Arial', 15)                 # Для кнопок
FONT_LIST = ('Arial', 14)                   # Для списков
FONT_CITY = ('Arial', 16, 'bold')           # Для названия города

# Шрифты для статусной строки
FONT_STATUS = ('Arial', 14)

# Шрифты для деталей
FONT_DETAILS = ('Arial', 15)

# =============================================================================
# КОНСТАНТЫ ДЛЯ ЦВЕТОВ
# =============================================================================

COLORS = {
    'bg': '#f0f0f0',
    'header_bg': '#2c3e50',
    'header_fg': 'white',
    'card_bg': '#ffffff',
    'card_gradient_start': '#667eea',
    'card_gradient_end': '#764ba2',
    'button_bg': '#3498db',
    'button_hover': '#2980b9',
    'success_bg': '#27ae60',
    'warning_bg': '#e74c3c',
    'text_color': '#333333',
    'border': '#bdc3c7',
    'history_bg': '#f8f9fa'
}

# ===========================================================================
#             ОСНОВНОЙ КЛАСС ГРАФИЧЕСКОГО ИНТЕРФЕЙСА ПРИЛОЖЕНИЯ
# ===========================================================================

class WeatherJournalGUI:
    """ Главное окно приложения Weather Journal """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Дневник погоды")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Данные приложения
        self.current_city = None
        self.city_timezone = None
        self.journal = {}
        self.history_data = {} # словарь для хранения исторических данных

        # настройка стилей
        self.setup_styles()

        # настройка интерфейса
        self.setup_ui()

        # загрузка начальных данных
        #self.load_initial_data()

        # таймер для обновления погоды по времени
        # self.schedule_refresh()

    def setup_styles(self):

        # настройка цветовой схемы и стилей
        self.root.configure(bg=COLORS['bg'])

        # настройка стилей для ttk виджетов
        style = ttk.Style()
        style.theme_use('clam')

        # стиль для вкладок
        style.configure('TNotebook.Tab',
                        font=FONT_NORMAL,
                        padding=[10, 5])
    
    def setup_ui(self):
        # настройка интерфейса

        # верхняя панель
        self.header_frame = tk.Frame(self.root, bg=COLORS['header_bg'], height=80)
        self.header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.header_frame.pack_propagate(False)

        # информация о городе
        self.city_lable = tk.Label(self.header_frame, text='Город: Не выбран',
                                   bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                                   font=FONT_CITY)
        self.city_lable.pack(side=tk.LEFT, padx=20, pady=10)
        self.timezone_label = tk.Label(self.header_frame, text='Временная зона: --',
                                       bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                                       font=FONT_SMALL)
        self.timezone_label.pack(side=tk.LEFT, padx=200, pady=10)

        # КНОПКА СМЕНЫ ГОРОДА
        #####################

        # создание вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # вкладка "Сегодня"
        self.today_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.today_frame, text='Сегодня')
        #self.setup_today_tab()

        # вкладка "Другая дата"
        self.date_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.date_frame, text='Другая дата')
        #self.setup_date_tab()

        # вкладка с историей погоды
        self.history_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.history_frame, text='История погоды')
        #self.setup_history_tab()

        # статус бар
        self.status_bar = tk.Label(self.root, text='Готов к работе',
                                   bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                                   anchor=tk.W, padx=10, font=FONT_STATUS)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        



    
    
    
    def run(self):
            self.root.mainloop()


def main():
    # запуск приложения
    app = WeatherJournalGUI()
    app.run()

if __name__ == "__main__":
    main()










