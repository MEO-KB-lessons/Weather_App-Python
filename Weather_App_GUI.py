# Weather_App_GUI.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import datetime
from typing import Optional, Dict, List
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
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # Данные приложения
        self.current_city = None      # Текущий выбранный город
        self.city_timezone = None     # Временная зона города
        self.journal = {}             # Дневник погоды (загружается из файла)
        self.history_data = {}        # словарь для хранения исторических данных

        # настройка стилей
        self.setup_styles()

        # настройка интерфейса
        self.setup_ui()

        # загрузка начальных данных
        self.load_initial_data()

        # таймер для обновления погоды по времени (не реализован, можно добавить)
        # self.schedule_refresh()

    def setup_styles(self):
        """Настройка цветовой схемы и стилей для виджетов"""
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
        """Настройка интерфейса - создание всех виджетов"""
        
        # ===== ВЕРХНЯЯ ПАНЕЛЬ =====
        self.header_frame = tk.Frame(self.root, bg=COLORS['header_bg'], height=80)
        self.header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.header_frame.pack_propagate(False)

        # Информация о городе
        self.city_label = tk.Label(self.header_frame, text='Город: Не выбран',
                                   bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                                   font=FONT_CITY)
        self.city_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.timezone_label = tk.Label(self.header_frame, text='Временная зона: --',
                                       bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                                       font=FONT_SMALL)
        self.timezone_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Кнопка смены города
        self.change_city_btn = tk.Button(self.header_frame, 
                                         text="✏️ Сменить город",
                                         font=FONT_BUTTON,
                                         bg=COLORS['button_bg'],
                                         fg='white',
                                         command=self.change_city,
                                         cursor='hand2')
        self.change_city_btn.pack(side=tk.RIGHT, padx=20, pady=15)

        # ===== СОЗДАНИЕ ВКЛАДОК =====
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка "Сегодня"
        self.today_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.today_frame, text='🌤️ Сегодня')
        self.setup_today_tab()

        # Вкладка "Другая дата"
        self.date_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.date_frame, text='📅 Другая дата')
        self.setup_date_tab()

        # Вкладка с историей погоды
        self.history_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.history_frame, text='📜 История погоды')
        self.setup_history_tab()

        # ===== СТАТУС БАР =====
        self.status_bar = tk.Label(self.root, text='Готов к работе',
                                   bg=COLORS['header_bg'], fg=COLORS['header_fg'],
                                   anchor=tk.W, padx=10, font=FONT_STATUS)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_today_tab(self):
        """Настройка вкладки с погодой на сегодня"""
        
        # Фрейм для отображения погоды (карточка)
        self.weather_card = tk.Frame(self.today_frame, bg=COLORS['card_bg'],
                                     relief=tk.RAISED, bd=2)
        self.weather_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок с датой
        self.today_date_label = tk.Label(self.weather_card, 
                                         text="",
                                         font=FONT_HEADER,
                                         bg=COLORS['card_bg'],
                                         fg=COLORS['text_color'])
        self.today_date_label.pack(pady=(20, 10))
        
        # Крупная температура
        self.temp_label = tk.Label(self.weather_card,
                                   text="--°C",
                                   font=FONT_TITLE,
                                   bg=COLORS['card_bg'],
                                   fg=COLORS['card_gradient_start'])
        self.temp_label.pack(pady=10)
        
        # Фрейм для деталей погоды (сетка 2x2)
        details_frame = tk.Frame(self.weather_card, bg=COLORS['card_bg'])
        details_frame.pack(pady=20, padx=30, fill=tk.BOTH)
        
        # Влажность
        self.humidity_label = tk.Label(details_frame, 
                                       text="💧 Влажность: --%",
                                       font=FONT_DETAILS,
                                       bg=COLORS['card_bg'])
        self.humidity_label.grid(row=0, column=0, sticky='w', pady=10, padx=20)
        
        # Давление
        self.pressure_label = tk.Label(details_frame,
                                       text="📊 Давление: -- мм рт. ст.",
                                       font=FONT_DETAILS,
                                       bg=COLORS['card_bg'])
        self.pressure_label.grid(row=0, column=1, sticky='w', pady=10, padx=20)
        
        # Осадки
        self.precip_label = tk.Label(details_frame,
                                     text="☔ Осадки: -- мм",
                                     font=FONT_DETAILS,
                                     bg=COLORS['card_bg'])
        self.precip_label.grid(row=1, column=0, sticky='w', pady=10, padx=20)
        
        # Ветер
        self.wind_label = tk.Label(details_frame,
                                   text="💨 Ветер: -- м/с",
                                   font=FONT_DETAILS,
                                   bg=COLORS['card_bg'])
        self.wind_label.grid(row=1, column=1, sticky='w', pady=10, padx=20)
        
        # Условия погоды
        self.conditions_label = tk.Label(self.weather_card,
                                         text="",
                                         font=FONT_SUBHEADER,
                                         bg=COLORS['card_bg'],
                                         fg=COLORS['text_color'])
        self.conditions_label.pack(pady=10)
        
        # Источник данных
        self.source_label = tk.Label(self.weather_card,
                                     text="",
                                     font=FONT_SMALL,
                                     bg=COLORS['card_bg'],
                                     fg='gray')
        self.source_label.pack(pady=(10, 20))
        
        # Кнопка обновления
        self.refresh_btn = tk.Button(self.today_frame,
                                     text="🔄 Обновить погоду",
                                     font=FONT_BUTTON,
                                     bg=COLORS['success_bg'],
                                     fg='white',
                                     command=self.refresh_today_weather,
                                     cursor='hand2')
        self.refresh_btn.pack(pady=(0, 20))
    
    def setup_date_tab(self):
        """Настройка вкладки для запроса погоды на конкретную дату"""
        
        # Верхняя панель ввода даты
        input_frame = tk.Frame(self.date_frame, bg=COLORS['bg'])
        input_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Подпись
        date_label = tk.Label(input_frame,
                              text="Введите дату (ДД.ММ.ГГГГ):",
                              font=FONT_NORMAL,
                              bg=COLORS['bg'])
        date_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Поле ввода даты
        self.date_entry = tk.Entry(input_frame, font=FONT_NORMAL, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка поиска
        self.search_btn = tk.Button(input_frame,
                                    text="🔍 Найти погоду",
                                    font=FONT_BUTTON,
                                    bg=COLORS['button_bg'],
                                    fg='white',
                                    command=self.search_weather_by_date,
                                    cursor='hand2')
        self.search_btn.pack(side=tk.LEFT)
        
        # Фрейм для отображения результата
        self.date_weather_card = tk.Frame(self.date_frame, bg=COLORS['card_bg'],
                                          relief=tk.RAISED, bd=2)
        self.date_weather_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок с датой
        self.date_result_title = tk.Label(self.date_weather_card,
                                          text="",
                                          font=FONT_HEADER,
                                          bg=COLORS['card_bg'],
                                          fg=COLORS['text_color'])
        self.date_result_title.pack(pady=(20, 10))
        
        # Температура
        self.date_temp_label = tk.Label(self.date_weather_card,
                                        text="--°C",
                                        font=FONT_TITLE,
                                        bg=COLORS['card_bg'],
                                        fg=COLORS['card_gradient_start'])
        self.date_temp_label.pack(pady=10)
        
        # Детали (используем ту же структуру, что и на вкладке "Сегодня")
        details_frame = tk.Frame(self.date_weather_card, bg=COLORS['card_bg'])
        details_frame.pack(pady=20, padx=30, fill=tk.BOTH)
        
        self.date_humidity_label = tk.Label(details_frame,
                                            text="💧 Влажность: --%",
                                            font=FONT_DETAILS,
                                            bg=COLORS['card_bg'])
        self.date_humidity_label.grid(row=0, column=0, sticky='w', pady=10, padx=20)
        
        self.date_pressure_label = tk.Label(details_frame,
                                            text="📊 Давление: -- мм рт. ст.",
                                            font=FONT_DETAILS,
                                            bg=COLORS['card_bg'])
        self.date_pressure_label.grid(row=0, column=1, sticky='w', pady=10, padx=20)
        
        self.date_precip_label = tk.Label(details_frame,
                                          text="☔ Осадки: -- мм",
                                          font=FONT_DETAILS,
                                          bg=COLORS['card_bg'])
        self.date_precip_label.grid(row=1, column=0, sticky='w', pady=10, padx=20)
        
        self.date_wind_label = tk.Label(details_frame,
                                        text="💨 Ветер: -- м/с",
                                        font=FONT_DETAILS,
                                        bg=COLORS['card_bg'])
        self.date_wind_label.grid(row=1, column=1, sticky='w', pady=10, padx=20)
        
        self.date_conditions_label = tk.Label(self.date_weather_card,
                                              text="",
                                              font=FONT_SUBHEADER,
                                              bg=COLORS['card_bg'],
                                              fg=COLORS['text_color'])
        self.date_conditions_label.pack(pady=10)
        
        self.date_source_label = tk.Label(self.date_weather_card,
                                          text="",
                                          font=FONT_SMALL,
                                          bg=COLORS['card_bg'],
                                          fg='gray')
        self.date_source_label.pack(pady=(10, 20))
    
    def setup_history_tab(self):
        """Настройка вкладки с историей погоды"""
        
        # Фрейм для кнопок управления
        control_frame = tk.Frame(self.history_frame, bg=COLORS['bg'])
        control_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Кнопка обновления истории
        self.refresh_history_btn = tk.Button(control_frame,
                                             text="🔄 Обновить историю",
                                             font=FONT_BUTTON,
                                             bg=COLORS['button_bg'],
                                             fg='white',
                                             command=self.refresh_history,
                                             cursor='hand2')
        self.refresh_history_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка статистики
        self.stats_btn = tk.Button(control_frame,
                                   text="📊 Статистика",
                                   font=FONT_BUTTON,
                                   bg=COLORS['card_gradient_start'],
                                   fg='white',
                                   command=self.show_statistics,
                                   cursor='hand2')
        self.stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Кнопка очистки истории для текущего города
        self.clear_history_btn = tk.Button(control_frame,
                                           text="🗑️ Очистить историю",
                                           font=FONT_BUTTON,
                                           bg=COLORS['warning_bg'],
                                           fg='white',
                                           command=self.clear_city_history,
                                           cursor='hand2')
        self.clear_history_btn.pack(side=tk.LEFT)
        
        # Текстовое поле с прокруткой для отображения истории
        self.history_text = scrolledtext.ScrolledText(self.history_frame,
                                                       font=FONT_LIST,
                                                       bg=COLORS['history_bg'],
                                                       fg=COLORS['text_color'],
                                                       wrap=tk.WORD,
                                                       height=20)
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Настройка тегов для форматирования текста
        self.history_text.tag_configure('header', font=FONT_HEADER, foreground=COLORS['header_bg'])
        self.history_text.tag_configure('date', font=FONT_NORMAL, foreground='#27ae60')
        self.history_text.tag_configure('temp', font=FONT_NORMAL, foreground='#e74c3c')
        self.history_text.tag_configure('separator', font=FONT_NORMAL, foreground='gray')
    
    def load_initial_data(self):
        """Загрузка начальных данных: города, временной зоны и дневника"""
        self.update_status("Загрузка данных...")
        
        # Загружаем сохраненный город
        self.current_city = weather_core.ConfigManager.load_city()
        self.city_timezone = weather_core.ConfigManager.load_timezone()
        
        # Загружаем дневник погоды
        self.journal = weather_core.JournalManager.load_journal()
        
        if self.current_city:
            # Обновляем интерфейс
            self.city_label.config(text=f"🏙️ {self.current_city}")
            if self.city_timezone:
                self.timezone_label.config(text=f"🕐 {self.city_timezone}")
            else:
                self.timezone_label.config(text="🕐 Временная зона не определена")
            
            # Загружаем погоду на сегодня
            self.refresh_today_weather()
            
            # Загружаем историю
            self.refresh_history()
        else:
            # Если город не выбран, предлагаем выбрать
            self.city_label.config(text="Город: Не выбран")
            self.timezone_label.config(text="Временная зона: --")
            self.update_status("Выберите город для начала работы")
            # Автоматически открываем диалог выбора города
            self.root.after(500, self.change_city)
    
    def update_status(self, message: str):
        """Обновление текста в статусной строке"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def change_city(self):
        """Смена города через диалоговое окно"""
        # Запрашиваем название города у пользователя
        new_city = simpledialog.askstring("Смена города",
                                          "Введите название города:",
                                          parent=self.root)
        
        if not new_city or not new_city.strip():
            return
        
        new_city = new_city.strip()
        self.update_status(f"Поиск города '{new_city}'...")
        
        # Получаем координаты и временную зону
        result = weather_core.get_coordinates_and_timezone(new_city)
        
        if result:
            lat, lon, timezone = result
            
            # Если временная зона не определилась, пробуем получить отдельно
            if not timezone:
                self.update_status(f"Определяем временную зону для {new_city}...")
                timezone = weather_core.get_timezone_for_city(lat, lon)
            
            # Сохраняем город в настройках
            if timezone:
                weather_core.ConfigManager.save_city(new_city, timezone)
            else:
                weather_core.ConfigManager.save_city(new_city)
                timezone = "Europe/Moscow"  # Зона по умолчанию
            
            # Обновляем данные приложения
            self.current_city = new_city
            self.city_timezone = timezone
            
            # Обновляем интерфейс
            self.city_label.config(text=f"🏙️ {self.current_city}")
            self.timezone_label.config(text=f"🕐 {self.city_timezone}")
            
            # Перезагружаем дневник (на случай, если для нового города есть записи)
            self.journal = weather_core.JournalManager.load_journal()
            
            # Обновляем погоду на сегодня
            self.refresh_today_weather()
            
            # Обновляем историю
            self.refresh_history()
            
            self.update_status(f"Город успешно изменен на '{new_city}'")
            messagebox.showinfo("Успех", f"Город '{new_city}' успешно установлен!")
        else:
            self.update_status(f"Город '{new_city}' не найден")
            messagebox.showerror("Ошибка", f"Город '{new_city}' не найден.\nПроверьте правильность написания.")
    
    def refresh_today_weather(self):
        """Обновление погоды на сегодня"""
        if not self.current_city:
            messagebox.showwarning("Внимание", "Сначала выберите город!")
            return
        
        self.update_status("Получение погоды на сегодня...")
        
        # Получаем текущую дату во временной зоне города
        target_date = weather_core.get_current_time_in_zone(self.city_timezone or "Europe/Moscow")
        storage_date_str = weather_core.format_date_for_storage(target_date)
        display_date_str = weather_core.format_date_for_display(target_date)
        
        # Проверяем, есть ли запись в дневнике
        record = weather_core.JournalManager.get_weather_for_date(self.journal, 
                                                                   self.current_city, 
                                                                   storage_date_str)
        
        if record:
            # Используем сохраненную запись
            self.display_weather_on_today_tab(record, display_date_str)
            self.update_status(f"Погода на {display_date_str} загружена из дневника")
        else:
            # Запрашиваем из API
            coords = weather_core.get_coordinates(self.current_city)
            if coords:
                weather = weather_core.get_weather_for_date(coords[0], coords[1], 
                                                           target_date, 
                                                           self.city_timezone or "Europe/Moscow")
                if weather:
                    # Сохраняем в дневник
                    weather_core.JournalManager.add_weather_record(self.journal, 
                                                                   self.current_city, 
                                                                   storage_date_str, 
                                                                   weather)
                    weather_core.JournalManager.save_journal(self.journal)
                    self.display_weather_on_today_tab(weather, display_date_str)
                    self.update_status(f"Погода на {display_date_str} успешно получена из API")
                else:
                    self.update_status("Не удалось получить погоду")
                    messagebox.showerror("Ошибка", "Не удалось получить данные о погоде")
            else:
                self.update_status("Не удалось получить координаты города")
                messagebox.showerror("Ошибка", "Не удалось определить координаты города")
    
    def display_weather_on_today_tab(self, weather_data: Dict, date_str: str):
        """Отображение погоды на вкладке 'Сегодня'"""
        # Дата
        self.today_date_label.config(text=f"📅 {date_str}")
        
        # Температура (отображаем максимальную и минимальную)
        t_max = weather_data.get('temperature_max')
        t_min = weather_data.get('temperature_min')
        
        if t_max is not None and t_min is not None:
            self.temp_label.config(text=f"{t_min:.1f}° / {t_max:.1f}°C")
        elif t_max is not None:
            self.temp_label.config(text=f"{t_max:.1f}°C")
        elif t_min is not None:
            self.temp_label.config(text=f"{t_min:.1f}°C")
        else:
            self.temp_label.config(text="--°C")
        
        # Влажность
        humidity = weather_data.get('humidity')
        if humidity is not None:
            self.humidity_label.config(text=f"💧 Влажность: {humidity:.0f}%")
        else:
            self.humidity_label.config(text="💧 Влажность: --%")
        
        # Давление
        pressure = weather_data.get('pressure_mmhg')
        if pressure is not None:
            self.pressure_label.config(text=f"📊 Давление: {pressure:.0f} мм рт. ст.")
        else:
            self.pressure_label.config(text="📊 Давление: -- мм рт. ст.")
        
        # Осадки
        precip = weather_data.get('precipitation_sum')
        if precip is not None:
            self.precip_label.config(text=f"☔ Осадки: {precip:.1f} мм")
        else:
            self.precip_label.config(text="☔ Осадки: -- мм")
        
        # Ветер
        wind = weather_data.get('wind_speed_ms')
        if wind is not None:
            self.wind_label.config(text=f"💨 Ветер: {wind:.1f} м/с")
        else:
            wind_kmh = weather_data.get('wind_speed_kmh')
            if wind_kmh is not None:
                self.wind_label.config(text=f"💨 Ветер: {wind_kmh:.1f} км/ч")
            else:
                self.wind_label.config(text="💨 Ветер: --")
        
        # Условия погоды (по коду weathercode)
        wcode = weather_data.get('weathercode')
        if wcode is not None:
            conditions = self.get_weather_conditions(wcode)
            self.conditions_label.config(text=conditions)
        
        # Источник данных
        source = weather_data.get('source', 'Неизвестно')
        self.source_label.config(text=f"📡 Источник: {source}")
    
    def get_weather_conditions(self, wcode: int) -> str:
        """Возвращает текстовое описание погодных условий по коду"""
        conditions_map = {
            0: '☀️ Ясно',
            1: '🌤️ Преимущественно ясно',
            2: '⛅ Переменная облачность',
            3: '☁️ Пасмурно',
            45: '🌫️ Туман',
            48: '🌫️ Изморозь',
            51: '🌧️ Легкая морось',
            53: '🌧️ Умеренная морось',
            55: '🌧️ Сильная морось',
            61: '🌧️ Небольшой дождь',
            63: '🌧️ Умеренный дождь',
            65: '🌧️ Сильный дождь',
            71: '🌨️ Небольшой снег',
            73: '🌨️ Умеренный снег',
            75: '🌨️ Сильный снег',
            95: '⛈️ Гроза',
            96: '⛈️ Гроза с градом',
            99: '⛈️ Сильная гроза с градом'
        }
        return conditions_map.get(wcode, f'🌡️ Код {wcode}')
    
    def search_weather_by_date(self):
        """Поиск погоды на указанную дату"""
        if not self.current_city:
            messagebox.showwarning("Внимание", "Сначала выберите город!")
            return
        
        date_str = self.date_entry.get().strip()
        if not date_str:
            messagebox.showwarning("Внимание", "Введите дату в формате ДД.ММ.ГГГГ")
            return
        
        # Парсим дату
        target_date = weather_core.parse_display_date(date_str)
        if not target_date:
            messagebox.showerror("Ошибка", "Неверный формат даты.\nИспользуйте ДД.ММ.ГГГГ")
            return
        
        # Проверяем, что дата не в будущем
        today = datetime.date.today()
        if target_date > today:
            messagebox.showwarning("Внимание", 
                                  "Нельзя запросить погоду на будущую дату.\n"
                                  "Дневник хранит только прошедшие даты.")
            return
        
        storage_date_str = weather_core.format_date_for_storage(target_date)
        display_date_str = weather_core.format_date_for_display(target_date)
        
        self.update_status(f"Поиск погоды на {display_date_str}...")
        
        # Проверяем дневник
        record = weather_core.JournalManager.get_weather_for_date(self.journal,
                                                                   self.current_city,
                                                                   storage_date_str)
        
        if record:
            self.display_weather_on_date_tab(record, display_date_str)
            self.update_status(f"Погода на {display_date_str} загружена из дневника")
        else:
            # Запрашиваем из API
            coords = weather_core.get_coordinates(self.current_city)
            if coords:
                weather = weather_core.get_weather_for_date(coords[0], coords[1],
                                                           target_date,
                                                           self.city_timezone or "Europe/Moscow")
                if weather:
                    # Сохраняем в дневник
                    weather_core.JournalManager.add_weather_record(self.journal,
                                                                   self.current_city,
                                                                   storage_date_str,
                                                                   weather)
                    weather_core.JournalManager.save_journal(self.journal)
                    self.display_weather_on_date_tab(weather, display_date_str)
                    self.update_status(f"Погода на {display_date_str} успешно получена из API")
                    
                    # Обновляем историю, так как добавилась новая запись
                    self.refresh_history()
                else:
                    self.update_status(f"Не удалось получить погоду на {display_date_str}")
                    messagebox.showerror("Ошибка", "Не удалось получить данные о погоде за указанную дату")
            else:
                self.update_status("Не удалось получить координаты города")
                messagebox.showerror("Ошибка", "Не удалось определить координаты города")
    
    def display_weather_on_date_tab(self, weather_data: Dict, date_str: str):
        """Отображение погоды на вкладке 'Другая дата'"""
        # Заголовок с датой
        self.date_result_title.config(text=f"📅 {date_str}")
        
        # Температура
        t_max = weather_data.get('temperature_max')
        t_min = weather_data.get('temperature_min')
        
        if t_max is not None and t_min is not None:
            self.date_temp_label.config(text=f"{t_min:.1f}° / {t_max:.1f}°C")
        elif t_max is not None:
            self.date_temp_label.config(text=f"{t_max:.1f}°C")
        elif t_min is not None:
            self.date_temp_label.config(text=f"{t_min:.1f}°C")
        else:
            self.date_temp_label.config(text="--°C")
        
        # Влажность
        humidity = weather_data.get('humidity')
        if humidity is not None:
            self.date_humidity_label.config(text=f"💧 Влажность: {humidity:.0f}%")
        else:
            self.date_humidity_label.config(text="💧 Влажность: --%")
        
        # Давление
        pressure = weather_data.get('pressure_mmhg')
        if pressure is not None:
            self.date_pressure_label.config(text=f"📊 Давление: {pressure:.0f} мм рт. ст.")
        else:
            self.date_pressure_label.config(text="📊 Давление: -- мм рт. ст.")
        
        # Осадки
        precip = weather_data.get('precipitation_sum')
        if precip is not None:
            self.date_precip_label.config(text=f"☔ Осадки: {precip:.1f} мм")
        else:
            self.date_precip_label.config(text="☔ Осадки: -- мм")
        
        # Ветер
        wind = weather_data.get('wind_speed_ms')
        if wind is not None:
            self.date_wind_label.config(text=f"💨 Ветер: {wind:.1f} м/с")
        else:
            wind_kmh = weather_data.get('wind_speed_kmh')
            if wind_kmh is not None:
                self.date_wind_label.config(text=f"💨 Ветер: {wind_kmh:.1f} км/ч")
            else:
                self.date_wind_label.config(text="💨 Ветер: --")
        
        # Условия погоды
        wcode = weather_data.get('weathercode')
        if wcode is not None:
            conditions = self.get_weather_conditions(wcode)
            self.date_conditions_label.config(text=conditions)
        else:
            self.date_conditions_label.config(text="")
        
        # Источник данных
        source = weather_data.get('source', 'Неизвестно')
        self.date_source_label.config(text=f"📡 Источник: {source}")
    
    def show_statistics(self):
        """
        Отображение статистики погоды в отдельном окне с прокруткой.
        Использует ScrolledText для автоматической прокрутки колесиком мыши.
        """
        # =========================================================================
        # 1. ПРОВЕРКА НАЛИЧИЯ ДАННЫХ
        # =========================================================================
        
        # Проверяем, выбран ли город
        if not self.current_city:
            messagebox.showwarning("Внимание", "Сначала выберите город!")
            return
        
        city_key = self.current_city.lower()
        
        # Проверяем, есть ли записи в истории для этого города
        if city_key not in self.journal or not self.journal[city_key]:
            messagebox.showinfo(
                "Статистика", 
                f"Для города '{self.current_city}' нет записей в истории.\n\n"
                f"Добавьте записи:\n"
                f"• На вкладке 'Сегодня' нажмите 'Обновить погоду'\n"
                f"• На вкладке 'Другая дата' укажите прошедшую дату"
            )
            return
        
        # =========================================================================
        # 2. СБОР ДАННЫХ ДЛЯ СТАТИСТИКИ
        # =========================================================================
        
        # Получаем все записи для текущего города
        records = self.journal[city_key]
        
        # Сортируем даты для определения периода
        sorted_dates = sorted(records.keys())
        
        # Списки для хранения числовых значений
        temps_max = []      # Максимальные температуры
        temps_min = []      # Минимальные температуры
        humidities = []     # Значения влажности
        pressures = []      # Значения давления
        precipitations = [] # Количество осадков
        wind_speeds = []    # Скорость ветра
        
        # Проходим по всем записям и собираем данные
        for date_str, weather in records.items():
            # Максимальная температура
            t_max = weather.get('temperature_max')
            if t_max is not None:
                temps_max.append(t_max)
            
            # Минимальная температура
            t_min = weather.get('temperature_min')
            if t_min is not None:
                temps_min.append(t_min)
            
            # Влажность
            humidity = weather.get('humidity')
            if humidity is not None:
                humidities.append(humidity)
            
            # Давление (в мм рт. ст.)
            pressure = weather.get('pressure_mmhg')
            if pressure is not None:
                pressures.append(pressure)
            
            # Осадки
            precip = weather.get('precipitation_sum')
            if precip is not None:
                precipitations.append(precip)
            
            # Скорость ветра (в м/с)
            wind = weather.get('wind_speed_ms')
            if wind is not None:
                wind_speeds.append(wind)
        
        # =========================================================================
        # 3. СОЗДАНИЕ ОКНА СТАТИСТИКИ
        # =========================================================================
        
        # Создаем новое окно поверх главного
        stats_window = tk.Toplevel(self.root)
        stats_window.title(f"📊 Статистика погоды - {self.current_city}")
        stats_window.geometry("550x650")  # Ширина x Высота
        stats_window.minsize(400, 400)    # Минимальный размер окна
        stats_window.configure(bg=COLORS['bg'])
        
        # Центрируем окно на экране
        stats_window.update_idletasks()
        x = (stats_window.winfo_screenwidth() // 2) - (550 // 2)
        y = (stats_window.winfo_screenheight() // 2) - (650 // 2)
        stats_window.geometry(f"+{x}+{y}")
        
        # =========================================================================
        # 4. СОЗДАНИЕ ЗАГОЛОВКА ОКНА
        # =========================================================================
        
        # Верхняя панель с градиентным фоном
        header_frame = tk.Frame(stats_window, bg=COLORS['card_gradient_start'], height=90)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)  # Запрещаем изменение высоты
        
        # Название города крупным шрифтом
        city_title = tk.Label(
            header_frame,
            text=f"📊 {self.current_city}",
            font=('Arial', 20, 'bold'),
            bg=COLORS['card_gradient_start'],
            fg='white'
        )
        city_title.pack(pady=(15, 5))
        
        # Подзаголовок с периодом
        period_text = f"{weather_core.storage_to_display(sorted_dates[0])} — {weather_core.storage_to_display(sorted_dates[-1])}"
        period_label = tk.Label(
            header_frame,
            text=period_text,
            font=('Arial', 12),
            bg=COLORS['card_gradient_start'],
            fg='white'
        )
        period_label.pack()
        
        # Количество записей
        records_label = tk.Label(
            header_frame,
            text=f"📋 Всего записей: {len(records)}",
            font=('Arial', 11),
            bg=COLORS['card_gradient_start'],
            fg='white'
        )
        records_label.pack(pady=(5, 10))
        
        # =========================================================================
        # 5. СОЗДАНИЕ ТЕКСТОВОЙ ОБЛАСТИ С ПРОКРУТКОЙ
        # =========================================================================
        
        # Создаем текстовое поле с автоматической прокруткой
        # ScrolledText - это готовый виджет, который включает в себя:
        # - Текстовую область
        # - Вертикальную полосу прокрутки
        # - Автоматическую поддержку прокрутки колесиком мыши
        text_area = scrolledtext.ScrolledText(
            stats_window,
            wrap=tk.WORD,           # Перенос слов, а не букв
            font=('Consolas', 11),  # Моноширинный шрифт для ровных колонок
            bg='white',
            fg=COLORS['text_color'],
            padx=20,
            pady=15,
            relief=tk.FLAT,         # Плоская граница
            highlightthickness=0    # Убираем подсветку
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Настраиваем теги (стили) для форматирования текста
        # Теги позволяют применять разные стили к разным частям текста
        
        # Заголовки секций (крупные)
        text_area.tag_configure(
            'section_title',
            font=('Arial', 14, 'bold'),
            foreground=COLORS['card_gradient_start'],
            spacing1=10,    # Отступ сверху
            spacing3=5      # Отступ снизу
        )
        
        # Подзаголовки
        text_area.tag_configure(
            'subsection_title',
            font=('Arial', 12, 'bold'),
            foreground='#2c3e50',
            spacing1=5
        )
        
        # Значения (выделенные)
        text_area.tag_configure(
            'value',
            font=('Arial', 11, 'bold'),
            foreground='#e74c3c'
        )
        
        # Обычный текст
        text_area.tag_configure(
            'normal',
            font=('Arial', 11),
            foreground='#333333'
        )
        
        # Разделители
        text_area.tag_configure(
            'separator',
            foreground='#bdc3c7'
        )
        
        # Примечание
        text_area.tag_configure(
            'note',
            font=('Arial', 10, 'italic'),
            foreground='#7f8c8d'
        )
        
        # =========================================================================
        # 6. ФОРМИРОВАНИЕ ТЕКСТА СТАТИСТИКИ
        # =========================================================================
        
        # Очищаем текстовое поле
        text_area.delete(1.0, tk.END)
        
        # Функция-помощник для вставки текста с тегом
        def insert_line(text, tag='normal', end='\n'):
            """Вставляет строку текста с указанным тегом"""
            text_area.insert(tk.END, text + end, tag)
        
        # ===== 1. ТЕМПЕРАТУРА =====
        if temps_max and temps_min:
            # Заголовок секции
            insert_line("🌡️  ТЕМПЕРАТУРА", 'section_title')
            insert_line("─" * 50, 'separator')
            
            # Средняя температура
            avg_temp = (sum(temps_max)/len(temps_max) + sum(temps_min)/len(temps_min)) / 2
            insert_line(f"  Средняя:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {avg_temp:.1f}°C\n", 'value')

            # Максимальная температура
            max_temp = max(temps_max)
            insert_line(f"  Максимальная:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {max_temp:.1f}°C\n", 'value')
            
            # Минимальная температура
            min_temp = min(temps_min)
            insert_line(f"  Минимальная:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {min_temp:.1f}°C\n\n", 'value')
  
        # ===== 2. ВЛАЖНОСТЬ =====
        if humidities:
            insert_line("💧  ВЛАЖНОСТЬ", 'section_title')
            insert_line("─" * 50, 'separator')
            
            avg_humidity = sum(humidities) / len(humidities)
            insert_line(f"  Средняя:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {avg_humidity:.1f}%\n", 'value')
            
            insert_line(f"  Максимальная:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {max(humidities):.1f}%\n", 'value')
            
            insert_line(f"  Минимальная:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {min(humidities):.1f}%\n\n", 'value')
        
        # ===== 3. ДАВЛЕНИЕ =====
        if pressures:
            insert_line("📊  ДАВЛЕНИЕ", 'section_title')
            insert_line("─" * 50, 'separator')
            
            avg_pressure = sum(pressures) / len(pressures)
            insert_line(f"  Среднее:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {avg_pressure:.1f} мм рт. ст.\n", 'value')
            
            insert_line(f"  Максимальное:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {max(pressures):.1f} мм рт. ст.\n", 'value')
            
            insert_line(f"  Минимальное:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {min(pressures):.1f} мм рт. ст.\n\n", 'value')
        
        # ===== 4. ОСАДКИ =====
        if precipitations:
            insert_line("☔  ОСАДКИ", 'section_title')
            insert_line("─" * 50, 'separator')
            
            total_precip = sum(precipitations)
            insert_line(f"  Общее количество:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {total_precip:.1f} мм\n", 'value')
            
            avg_precip = total_precip / len(precipitations)
            insert_line(f"  Среднее количество:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {avg_precip:.1f} мм\n", 'value')
            
            insert_line(f"  Максимальные осадки:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {max(precipitations):.1f} мм\n", 'value')
            
            days_with_precip = len([p for p in precipitations if p > 0])
            days_without_precip = len([p for p in precipitations if p == 0])
            
            insert_line(f"  Дней с осадками (>0 мм):", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {days_with_precip}\n", 'value')
            
            insert_line(f"  Дней без осадков:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {days_without_precip}\n\n", 'value')
        
        # ===== 5. ВЕТЕР =====
        if wind_speeds:
            insert_line("💨  ВЕТЕР", 'section_title')
            insert_line("─" * 50, 'separator')
            
            avg_wind = sum(wind_speeds) / len(wind_speeds)
            insert_line(f"  Средняя скорость:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {avg_wind:.1f} м/с\n", 'value')
            
            insert_line(f"  Максимальная скорость:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {max(wind_speeds):.1f} м/с\n", 'value')
            
            insert_line(f"  Минимальная скорость:", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {min(wind_speeds):.1f} м/с\n", 'value')
            
            # Дополнительно: скорость в км/ч
            insert_line(f"  В пересчете (средняя):", 'subsection_title', ' ')
            text_area.insert(tk.END, f" {avg_wind * 3.6:.1f} км/ч\n\n", 'value')
        
        # ===== 7. ПРИМЕЧАНИЕ =====
        insert_line("📌  ПРИМЕЧАНИЕ", 'section_title')
        insert_line("─" * 50, 'separator')
        
        note_text = (
            f"  Статистика рассчитана на основе {len(records)} записей\n"
            f"  из дневника погоды за указанный период.\n\n"
            f"  • Данные получены из API Visual Crossing и Open-Meteo\n"
            f"  • Все значения округлены до одного десятичного знака\n"
            f"  • Давление приведено к мм ртутного столба"
        )
        text_area.insert(tk.END, note_text, 'note')
        
        # =========================================================================
        # 7. БЛОКИРУЕМ РЕДАКТИРОВАНИЕ И НАСТРАИВАЕМ ВНЕШНИЙ ВИД
        # =========================================================================
        
        # Запрещаем редактирование текста (только для чтения)
        text_area.configure(state='disabled')
        
        # Убираем курсор-палочку (делаем его обычной стрелкой)
        text_area.configure(cursor='arrow')
        
        # Настраиваем цвета для разных состояний
        text_area.configure(
            selectbackground=COLORS['card_gradient_start'],  # Цвет выделения
            selectforeground='white',                        # Цвет текста при выделении
            inactiveselectbackground=COLORS['border']        # Цвет при потере фокуса
        )
        
        # =========================================================================
        # 8. КНОПКА ЗАКРЫТИЯ
        # =========================================================================
        
        # Создаем фрейм для кнопки внизу окна
        button_frame = tk.Frame(stats_window, bg=COLORS['bg'], height=50)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)
        
        # Кнопка закрытия окна
        close_button = tk.Button(
            button_frame,
            text="✖  Закрыть",
            font=FONT_BUTTON,
            bg=COLORS['button_bg'],
            fg='white',
            activebackground=COLORS['button_hover'],
            activeforeground='white',
            cursor='hand2',
            command=stats_window.destroy,
            width=15,
            height=1
        )
        close_button.pack(pady=10)
        
        # =========================================================================
        # 9. ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
        # =========================================================================
        
        # Прокрутка к началу (показываем верхнюю часть)
        text_area.see(1.0)
        
        # Обновляем статус в главном окне
        self.update_status(f"Статистика для города '{self.current_city}' отображена")
        
        # Возвращаем созданное окно (на всякий случай)
        return stats_window
    
    def refresh_history(self):
        """Обновление отображения истории погоды для текущего города"""
        if not self.current_city:
            self.history_text.delete(1.0, tk.END)
            self.history_text.insert(tk.END, "Выберите город для просмотра истории.")
            return
        
        # Очищаем текстовое поле
        self.history_text.delete(1.0, tk.END)
        
        city_key = self.current_city.lower()
        
        if city_key in self.journal and self.journal[city_key]:
            # Заголовок
            self.history_text.insert(tk.END, f"📜 ИСТОРИЯ ПОГОДЫ: {self.current_city}\n\n", 'header')
            
            # Сортируем даты (от новых к старым)
            sorted_dates = sorted(self.journal[city_key].keys(), reverse=True)
            
            for storage_date_str in sorted_dates:
                weather = self.journal[city_key][storage_date_str]
                display_date = weather_core.storage_to_display(storage_date_str)
                
                # Форматируем вывод для каждой записи
                self.history_text.insert(tk.END, f"{'─' * 60}\n", 'separator')
                self.history_text.insert(tk.END, f"📅 {display_date}\n", 'date')
                
                # Температура
                t_max = weather.get('temperature_max')
                t_min = weather.get('temperature_min')
                if t_max is not None and t_min is not None:
                    self.history_text.insert(tk.END, f"   🌡️ Температура: {t_min:.1f}°C / {t_max:.1f}°C\n", 'temp')
                elif t_max is not None:
                    self.history_text.insert(tk.END, f"   🌡️ Макс. температура: {t_max:.1f}°C\n", 'temp')
                elif t_min is not None:
                    self.history_text.insert(tk.END, f"   🌡️ Мин. температура: {t_min:.1f}°C\n", 'temp')
                
                # Влажность
                humidity = weather.get('humidity')
                if humidity is not None:
                    self.history_text.insert(tk.END, f"   💧 Влажность: {humidity:.0f}%\n")
                
                # Давление
                pressure = weather.get('pressure_mmhg')
                if pressure is not None:
                    self.history_text.insert(tk.END, f"   📊 Давление: {pressure:.0f} мм рт. ст.\n")
                
                # Осадки
                precip = weather.get('precipitation_sum')
                if precip is not None:
                    self.history_text.insert(tk.END, f"   ☔ Осадки: {precip:.1f} мм\n")
                
                # Ветер
                wind = weather.get('wind_speed_ms')
                if wind is not None:
                    self.history_text.insert(tk.END, f"   💨 Ветер: {wind:.1f} м/с\n")
                
                # Источник
                source = weather.get('source', 'Неизвестно')
                self.history_text.insert(tk.END, f"   📡 Источник: {source}\n")
            
            self.history_text.insert(tk.END, f"\n{'─' * 60}\n", 'separator')
            self.history_text.insert(tk.END, f"\n📊 Всего записей: {len(sorted_dates)}\n")
        else:
            self.history_text.insert(tk.END, f"📭 В дневнике пока нет записей для города {self.current_city}.\n\n")
            self.history_text.insert(tk.END, "💡 Чтобы добавить записи:\n")
            self.history_text.insert(tk.END, "   • На вкладке 'Сегодня' нажмите 'Обновить погоду'\n")
            self.history_text.insert(tk.END, "   • На вкладке 'Другая дата' укажите прошедшую дату\n")
        
        self.update_status("История обновлена")
    
    def clear_city_history(self):
        """Очистка истории погоды для текущего города"""
        if not self.current_city:
            return
        
        # Подтверждение действия
        result = messagebox.askyesno("Подтверждение",
                                     f"Вы уверены, что хотите очистить всю историю погоды\n"
                                     f"для города '{self.current_city}'?\n\n"
                                     f"Это действие нельзя отменить.")
        
        if result:
            city_key = self.current_city.lower()
            if city_key in self.journal:
                # Удаляем записи для текущего города
                del self.journal[city_key]
                # Сохраняем изменения
                weather_core.JournalManager.save_journal(self.journal)
                # Обновляем отображение
                self.refresh_history()
                self.update_status(f"История для города '{self.current_city}' очищена")
                messagebox.showinfo("Успех", "История успешно очищена")
            else:
                messagebox.showinfo("Информация", f"Для города '{self.current_city}' нет записей в истории")
    
    def run(self):
        """Запуск главного цикла приложения"""
        self.root.mainloop()


def main():
    """Точка входа в приложение"""
    # Проверяем наличие API ключа и выводим предупреждение при необходимости
    if not weather_core.VISUALCROSSING_API_KEY:
        print("⚠️ Внимание! API ключ Visual Crossing не настроен.")
        print("   Будет использоваться только резервный API Open-Meteo.")
        print(f"   Для получения ключа зарегистрируйтесь на https://www.visualcrossing.com/")
        print(f"   и сохраните ключ в файл 'visualcrossing-api-key.txt'")
    
    # Запуск приложения
    app = WeatherJournalGUI()
    app.run()


if __name__ == "__main__":
    main()
