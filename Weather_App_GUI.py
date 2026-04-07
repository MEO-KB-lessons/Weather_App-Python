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
        self.setup_today_tab()

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

    def setup_today_tab(self):
        """ настройка вкладки с погодой на сегодня """
        # кнопка обновить
#        refresh_btn = tk.Button(self.today_frame, text="Обновить",
                                #command=self.refresh_today_weather,
#                                bg=COLORS['button_bg'], fg='white', font=FONT_BUTTON,
                                #cursor='hand2', relief=tk.FLAT, padx=20, pady=8)
        #refresh_btn.pack(pady=10)
        #refresh_btn.bind('<Enter>', lambda e:
        #                 refresh_btn.configure(bg=COLORS['button_hover']))
        #refresh_btn.bind('<Leave>', lambda e:
        #                 refresh_btn.configure(bg=COLORS['button_bg']))
        
        # карточка погоды
        self.weather_card = tk.Frame(self.today_frame, bg=COLORS['card_gradient_start'], relief=tk.RAISED, bd=2)
        self.weather_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # контейнер для виджетов
        self.weather_container = tk.Frame(self.weather_card, bg=COLORS['card_gradient_start'])
        self.weather_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок
        self.today_date_label = tk.Label(self.weather_container, text="Дата: --",
                                         font=FONT_HEADER, bg=COLORS['card_gradient_start'],
                                         fg='white')
        self.today_date_label.pack(pady=15)
        
        # Температура
        self.temp_label = tk.Label(self.weather_container, text="--°С", font=FONT_TITLE,
                                   bg=COLORS['card_gradient_start'], fg='white')
        self.temp_label.pack(pady=10)
        
        # Погодные условия
        self.condition_label = tk.Label(self.weather_container, text="--",
                                        font=FONT_SUBHEADER, bg=COLORS['card_gradient_start'], fg='white')
        self.condition_label.pack(pady=5)
        
        #Детали погоды
        details_frame = tk.Frame(self.weather_container, bg=COLORS['card_gradient_start'])
        details_frame.pack(pady=20)
        
        self.humidity_label = tk.Label(details_frame, text="Влажность: --", font=FONT_DETAILS,
                                       bg=COLORS['card_gradient_start'], fg='white')
        self.humidity_label.grid(row=0, column=0, padx=20, pady=5)
        
        self.pressure_label = tk.Label(details_frame, text="Давление: --", font=FONT_DETAILS,
                                       bg=COLORS['card_gradient_start'], fg='white')
        self.pressure_label.grid(row=0, column=1, padx=20, pady=5)
        
        self.wind_label = tk.Label(details_frame, text="Ветер: --", font=FONT_DETAILS,
                                   bg=COLORS['card_gradient_start'], fg='white')
        self.wind_label.grid(row=1, column=0, padx=20, pady=5)

        self.precip_label = tk.Label(details_frame, text="Осадки: --", font=FONT_DETAILS,
                                     bg=COLORS['card_gradient_start'], fg='white')
        self.precip_label.grid(row=1, column=1, padx=20, pady=5)

    def setup_date_tab(self):
        """ Настройка вкладки выбора даты """
        # Фрейм для выбора даты
        select_frame = tk.Frame(self.date_frame, bg=COLORS['bg'])
        select_frame.pack(fill=tk.X, pady=20, padx=20)

        tk.Label(select_frame, text="Выберите дату: ", font=FONT_NORMAL, 
                 bg=COLORS['bg']).pack(side=tk.LEFT, padx=5)
        
        # Виджет выбора даты
        self.date_var = tk.StringVar()
        today = datetime.date.today()
        self.date_var.set(today.strftime(weather_core.DISPLAY_DATE_FORMAT))

        self.date_entry = tk.Entry(select_frame, textvariable=self.date_var, 
                                   font=FONT_SMALL, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(select_frame, text="(формат: ДД.ММ.ГГГГ)", font=FONT_VERY_SMALL,
                 bg=COLORS['bg'], fg='gray').pack(side=tk.LEFT, padx=5)
        
        # Кнопка получения погоды
        get_weather_btn = tk.Button(select_frame, text="Получить погоду",
                                    #command=get_weather_for_selected_date,
                                    bg=COLORS['success_bg'], fg='white', font=FONT_BUTTON,
                                    cursor='hand2', relief=tk.FLAT, padx=15, pady=5)
        get_weather_btn.pack(side=tk.LEFT, padx=20)
        get_weather_btn.bind('<Enter>', lambda e: get_weather_btn.configure(bg='#229954'))
        get_weather_btn.bind('<Leave>', lambda e: get_weather_btn.configure(bg=COLORS['success_bg']))

        #############################################################################



    def refresh_today_weather(self):
        """ Обновление погоды на сегодня """
        if not self.current_city:
            return
        
        self.status_bar.config(text="Загрузка погоды...")
        self.root.update()











        



    
    
    
    def run(self):
            self.root.mainloop()


def main():
    # запуск приложения
    app = WeatherJournalGUI()
    app.run()

if __name__ == "__main__":
    main()










