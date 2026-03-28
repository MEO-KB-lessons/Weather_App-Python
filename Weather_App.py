# test string for commit
import requests
import json
import os
import datetime
from configparser import ConfigParser
from typing import Optional, Dict, List, Tuple

# --- Константы (API URL) ---
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
TIME_API_URL = "https://www.timeapi.io/api/Time/current/zone"

# --- Имена файлов ---
CONFIG_FILE = "config.cfg"
JOURNAL_FILE = "weather_journal.json"

# --- Форматы дат ---
DISPLAY_DATE_FORMAT = "%d.%m.%Y"  # формат для отображения пользователю
STORAGE_DATE_FORMAT = "%Y-%m-%d"  # ISO формат для хранения в JSON (API использует этот формат)

def format_date_for_display(date_obj: datetime.date) -> str:
    """Преобразует объект date в строку для отображения (dd.MM.yyyy)."""
    return date_obj.strftime(DISPLAY_DATE_FORMAT)

def format_date_for_storage(date_obj: datetime.date) -> str:
    """Преобразует объект date в строку для хранения в JSON (yyyy-MM-dd)."""
    return date_obj.strftime(STORAGE_DATE_FORMAT)

def parse_display_date(date_str: str) -> Optional[datetime.date]:
    """Парсит строку даты в формате dd.MM.yyyy и возвращает объект date."""
    try:
        return datetime.datetime.strptime(date_str, DISPLAY_DATE_FORMAT).date()
    except ValueError:
        return None

def storage_to_display(storage_date_str: str) -> str:
    """Преобразует дату из формата хранения в формат отображения."""
    try:
        date_obj = datetime.datetime.strptime(storage_date_str, STORAGE_DATE_FORMAT).date()
        return format_date_for_display(date_obj)
    except ValueError:
        return storage_date_str  # если не получается преобразовать, возвращаем как есть

def kmh_to_ms(kmh: Optional[float]) -> Optional[float]:
    """Переводит скорость ветра из км/ч в м/с."""
    if kmh is None:
        return None
    # 1 км/ч = 0.27778 м/с, округляем до 1 знака после запятой
    return round(kmh * 0.27778, 1)

# =============================================================================
# КЛАССЫ ДЛЯ РАБОТЫ С ДАННЫМИ
# =============================================================================

class ConfigManager:
    """Управление конфигурацией города в .cfg файле."""
    
    @staticmethod
    def load_city() -> Optional[str]:
        """Загружает название города из config.cfg."""
        if not os.path.exists(CONFIG_FILE):
            return None
        
        config = ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        
        if 'Settings' in config and 'city' in config['Settings']:
            return config['Settings']['city']
        return None

    @staticmethod
    def load_timezone() -> Optional[str]:
        """Загружает временную зону из config.cfg."""
        if not os.path.exists(CONFIG_FILE):
            return None
        
        config = ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        
        if 'Settings' in config and 'timezone' in config['Settings']:
            return config['Settings']['timezone']
        return None

    @staticmethod
    def save_city(city_name: str, timezone: str = None):
        """Сохраняет название города и временную зону в config.cfg."""
        config = ConfigParser()
        config['Settings'] = {'city': city_name}
        if timezone:
            config['Settings']['timezone'] = timezone
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"✅ Город '{city_name}' сохранен в настройках.")

class JournalManager:
    """Управление JSON-файлом дневника погоды."""
    
    @staticmethod
    def load_journal() -> Dict:
        """Загружает дневник из JSON-файла. Если файла нет, возвращает пустой словарь."""
        if not os.path.exists(JOURNAL_FILE):
            return {}
        try:
            with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("⚠️ Файл дневника поврежден или пуст. Будет создан новый.")
            return {}

    @staticmethod
    def save_journal(journal: Dict):
        """Сохраняет дневник в JSON-файл."""
        with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(journal, f, ensure_ascii=False, indent=2)
        print(f"💾 Дневник сохранен в файл '{JOURNAL_FILE}'.")

    @staticmethod
    def get_weather_for_date(journal: Dict, city: str, storage_date_str: str) -> Optional[Dict]:
        """
        Получает запись о погоде из дневника по городу и дате (дата в формате хранения).
        """
        city_key = city.lower()
        if city_key in journal and storage_date_str in journal[city_key]:
            return journal[city_key][storage_date_str]
        return None

    @staticmethod
    def add_weather_record(journal: Dict, city: str, storage_date_str: str, weather_data: Dict):
        """Добавляет или обновляет запись о погоде в дневнике (дата в формате хранения)."""
        city_key = city.lower()
        if city_key not in journal:
            journal[city_key] = {}
        journal[city_key][storage_date_str] = weather_data

# =============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С API
# =============================================================================

def get_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    """
    Получает координаты (широта, долгота) города через Open-Meteo Geocoding API.
    Возвращает None, если город не найден.
    """
    print(f"🔍 Поиск координат для города: {city_name}...")
    params = {'name': city_name, 'count': 1, 'language': 'ru', 'format': 'json'}
    
    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get('results'):
            first_result = data['results'][0]
            lat = first_result['latitude']
            lon = first_result['longitude']
            print(f"✅ Найдены координаты: {lat:.4f}, {lon:.4f}")
            return lat, lon
        else:
            print(f"❌ Город '{city_name}' не найден.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к геокодеру: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"❌ Ошибка обработки ответа геокодера: {e}")
        return None

def get_timezone_for_city(lat: float, lon: float) -> Optional[str]:
    """
    Получает временную зону для координат через Open-Meteo API.
    """
    try:
        print(f"🕐 Определяем временную зону для координат {lat:.4f}, {lon:.4f}...")
        params = {
            'latitude': lat,
            'longitude': lon,
            'timezone': 'auto'
        }
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Open-Meteo возвращает временную зону в ответе
        timezone = data.get('timezone')
        if timezone:
            print(f"✅ Определена временная зона: {timezone}")
            return timezone
        else:
            print("⚠️ Не удалось определить временную зону из ответа API")
            return None
    except Exception as e:
        print(f"⚠️ Не удалось определить временную зону: {e}")
        return None

def get_weather_for_date(lat: float, lon: float, target_date: datetime.date, timezone: str = "Europe/Moscow") -> Optional[Dict]:
    """
    Получает погоду за конкретную дату из Open-Meteo Forecast API.
    Возвращает словарь с данными о погоде или None при ошибке.
    """
    date_str = format_date_for_storage(target_date)  # API требует ISO формат
    display_date_str = format_date_for_display(target_date)
    print(f"☁️ Запрос погоды на {display_date_str}...")
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': date_str,
        'end_date': date_str,
        'daily': [
            'temperature_2m_max', 
            'temperature_2m_min', 
            'precipitation_sum', 
            'wind_speed_10m_max',
            'pressure_msl_mean',  # среднее давление на уровне моря
            'relative_humidity_2m_mean',  # средняя относительная влажность
            'weathercode'
        ],
        'timezone': timezone  # используем определенную временную зону
    }
    
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if 'daily' not in data:
            print("⚠️ Не удалось получить данные о погоде (нет поля 'daily').")
            return None

        daily = data['daily']
        
        # Получаем сырые значения
        wind_speed_kmh = daily.get('wind_speed_10m_max', [None])[0]
        wind_speed_ms = kmh_to_ms(wind_speed_kmh)
        
        # Получаем давление (переводим из гПа в мм рт. ст. если нужно)
        # Open-Meteo возвращает давление в гПа (гектопаскалях), что эквивалентно мбар
        # 1 гПа = 0.75006 мм рт. ст.
        pressure_hpa = daily.get('pressure_msl_mean', [None])[0]
        pressure_mmhg = round(pressure_hpa * 0.75006, 1) if pressure_hpa else None
        
        # Индекс 0, так как запрашивали только один день
        weather_data = {
            'date_storage': date_str,  # храним ISO формат для совместимости с API
            'date_display': display_date_str,  # и для удобства отображения
            'temperature_max': daily.get('temperature_2m_max', [None])[0],
            'temperature_min': daily.get('temperature_2m_min', [None])[0],
            'precipitation_sum': daily.get('precipitation_sum', [None])[0],
            'wind_speed_kmh': wind_speed_kmh,  # сохраняем исходное значение в км/ч
            'wind_speed_ms': wind_speed_ms,  # и переведённое в м/с
            'pressure_hpa': pressure_hpa,  # давление в гПа
            'pressure_mmhg': pressure_mmhg,  # давление в мм рт. ст.
            'humidity': daily.get('relative_humidity_2m_mean', [None])[0],  # влажность в %
            'weathercode': daily.get('weathercode', [None])[0],
            'source': 'Open-Meteo API',
            'timezone': timezone  # сохраняем временную зону
        }
        
        # Добавляем единицы измерения, если они есть
        if 'daily_units' in data:
            weather_data['units'] = {
                'temperature': data['daily_units'].get('temperature_2m_max', '°C'),
                'precipitation': data['daily_units'].get('precipitation_sum', 'mm'),
                'wind_speed': 'м/с',  # мы переводим в м/с
                'pressure': 'мм рт. ст.',  # мы переводим в мм рт. ст.
                'humidity': '%'
            }
        
        print(f"✅ Данные о погоде получены.")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к сервису погоды: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"❌ Ошибка обработки данных погоды: {e}")
        return None

def get_current_time_in_zone(timezone: str = "Europe/Moscow") -> Optional[datetime.date]:
    """
    Получает текущую дату для заданной временной зоны через TimeAPI.
    Используется для определения "сегодня" в конкретном городе.
    При ошибке возвращает системную дату UTC.
    """
    params = {'timeZone': timezone}
    try:
        print(f"🕐 Запрашиваем текущее время для зоны {timezone}...")
        response = requests.get(TIME_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        
        if year and month and day:
            current_date = datetime.date(year, month, day)
            print(f"✅ Текущая дата в зоне {timezone}: {format_date_for_display(current_date)}")
            return current_date
        else:
            print(f"⚠️ Не удалось получить дату из TimeAPI для зоны {timezone}, используется UTC.")
            return datetime.date.today()
            
    except Exception as e:
        print(f"⚠️ Ошибка получения времени через API ({e}). Используется системная дата UTC.")
        return datetime.date.today()

# =============================================================================
# ОСНОВНАЯ ЛОГИКА ПРИЛОЖЕНИЯ
# =============================================================================

def display_weather(weather_data: Dict, city: str):
    """Красиво выводит данные о погоде в консоль."""
    print("\n" + "="*50)
    print(f"🌍 Погода в городе: {city}")
    
    # Пытаемся отобразить дату в нужном формате
    if 'date_display' in weather_data:
        print(f"📅 Дата: {weather_data['date_display']}")
    elif 'date' in weather_data:
        # Если есть только старая дата, пробуем преобразовать
        print(f"📅 Дата: {storage_to_display(weather_data['date'])}")
    
    # Показываем временную зону, если она есть
    if 'timezone' in weather_data:
        print(f"🕐 Временная зона: {weather_data['timezone']}")
    
    print("-"*50)
    
    units = weather_data.get('units', {})
    t_unit = units.get('temperature', '°C')
    p_unit = units.get('precipitation', 'mm')
    w_unit = units.get('wind_speed', 'м/с')
    press_unit = units.get('pressure', 'мм рт. ст.')
    hum_unit = units.get('humidity', '%')
    
    # Температура
    t_max = weather_data.get('temperature_max')
    t_min = weather_data.get('temperature_min')
    if t_max is not None and t_min is not None:
        print(f"🌡️ Температура: от {t_min}{t_unit} до {t_max}{t_unit}")
    elif t_max is not None:
        print(f"🌡️ Макс. температура: {t_max}{t_unit}")
    elif t_min is not None:
        print(f"🌡️ Мин. температура: {t_min}{t_unit}")
    else:
        print("🌡️ Температура: нет данных")
    
    # Влажность
    humidity = weather_data.get('humidity')
    if humidity is not None:
        print(f"💧 Влажность: {humidity}{hum_unit}")
    
    # Давление (в мм рт. ст.)
    pressure = weather_data.get('pressure_mmhg')
    if pressure is not None:
        print(f"📊 Давление: {pressure} {press_unit}")
    else:
        pressure_hpa = weather_data.get('pressure_hpa')
        if pressure_hpa is not None:
            print(f"📊 Давление: {pressure_hpa} гПа")
    
    # Осадки
    precip = weather_data.get('precipitation_sum')
    if precip is not None:
        print(f"☔ Осадки: {precip} {p_unit}")
    
    # Ветер (в м/с)
    wind_ms = weather_data.get('wind_speed_ms')
    if wind_ms is not None:
        print(f"💨 Ветер: {wind_ms} {w_unit}")
    else:
        wind_kmh = weather_data.get('wind_speed_kmh')
        if wind_kmh is not None:
            print(f"💨 Ветер: {wind_kmh} км/ч")
    
    # Погодные условия
    wcode = weather_data.get('weathercode')
    if wcode is not None:
        conditions = {
            0: 'Ясно',
            1: 'Преимущественно ясно',
            2: 'Переменная облачность',
            3: 'Пасмурно',
            45: 'Туман',
            48: 'Изморозь',
            51: 'Легкая морось',
            53: 'Умеренная морось',
            55: 'Сильная морось',
            56: 'Легкая ледяная морось',
            57: 'Сильная ледяная морось',
            61: 'Небольшой дождь',
            63: 'Умеренный дождь',
            65: 'Сильный дождь',
            66: 'Легкий ледяной дождь',
            67: 'Сильный ледяной дождь',
            71: 'Небольшой снег',
            73: 'Умеренный снег',
            75: 'Сильный снег',
            77: 'Снежная крупа',
            80: 'Небольшой ливень',
            81: 'Умеренный ливень',
            82: 'Сильный ливень',
            85: 'Небольшой снегопад',
            86: 'Сильный снегопад',
            95: 'Гроза',
            96: 'Гроза с небольшим градом',
            99: 'Гроза с сильным градом'
        }
        condition = conditions.get(wcode, f'Код {wcode}')
        # Добавляем эмодзи в зависимости от кода погоды
        if wcode == 0:
            emoji = "☀️"
        elif wcode in [1, 2]:
            emoji = "⛅"
        elif wcode == 3:
            emoji = "☁️"
        elif wcode in [45, 48]:
            emoji = "🌫️"
        elif wcode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            emoji = "🌧️"
        elif wcode in [71, 73, 75, 77, 85, 86]:
            emoji = "🌨️"
        elif wcode in [95, 96, 99]:
            emoji = "⛈️"
        else:
            emoji = "🌡️"
        
        print(f"{emoji} Условия: {condition}")
    
    print("="*50)

def change_city_interactive() -> Tuple[Optional[str], Optional[str]]:
    """Интерактивная смена города с проверкой через геокодер."""
    while True:
        new_city = input("Введите название нового города: ").strip()
        if not new_city:
            print("Название города не может быть пустым.")
            continue
        
        coords = get_coordinates(new_city)
        if coords:
            # Получаем временную зону для нового города
            timezone = get_timezone_for_city(coords[0], coords[1])
            ConfigManager.save_city(new_city, timezone)
            return new_city, timezone
        else:
            retry = input("Город не найден. Попробовать снова? (y/n): ").lower()
            if retry != 'y':
                current_city = ConfigManager.load_city()
                if current_city:
                    print(f"Остаемся в городе '{current_city}'.")
                    current_timezone = ConfigManager.load_timezone()
                    return current_city, current_timezone
                else:
                    print("Не удалось установить город. Работа программы невозможна.")
                    exit()

def main():
    """Главная функция приложения."""
    print("="*60)
    print("         🌦️  ДНЕВНИК ПОГОДЫ  🌦️")
    print("="*60)
    
    # --- 1. Загрузка или выбор города ---
    current_city = ConfigManager.load_city()
    city_timezone = ConfigManager.load_timezone()
    
    if not current_city:
        print("👋 Привет! Похоже, вы здесь впервые.")
        current_city = input("Введите название вашего города: ").strip()
        if not current_city:
            print("Город не указан. Выход.")
            return
        
        coords = get_coordinates(current_city)
        if coords:
            # Получаем временную зону для нового города
            city_timezone = get_timezone_for_city(coords[0], coords[1])
            ConfigManager.save_city(current_city, city_timezone)
        else:
            print("Не удалось найти указанный город. Попробуйте позже.")
            return
    else:
        print(f"🏙️  Текущий город, сохраненный в настройках: {current_city}")
        if city_timezone:
            print(f"🕐 Временная зона: {city_timezone}")
        else:
            # Если временная зона не сохранена, пробуем определить
            print("🕐 Временная зона не сохранена. Пробуем определить...")
            coords = get_coordinates(current_city)
            if coords:
                city_timezone = get_timezone_for_city(coords[0], coords[1])
                if city_timezone:
                    ConfigManager.save_city(current_city, city_timezone)
    
    # Если всё ещё нет временной зоны, используем значение по умолчанию
    if not city_timezone:
        city_timezone = "Europe/Moscow"
        print(f"⚠️ Используется временная зона по умолчанию: {city_timezone}")
    
    # --- 2. Загрузка дневника ---
    journal = JournalManager.load_journal()
    
    # --- 3. Основной цикл меню ---
    while True:
        print(f"\n🏙️  Город: {current_city}")
        if city_timezone:
            print(f"🕐 Зона: {city_timezone}")
        print("\n--- Меню ---")
        print("1. Узнать погоду на сегодня")
        print("2. Узнать погоду на другую дату")
        print("3. Показать историю погоды для текущего города")
        print("4. Сменить город")
        print("5. Выйти")
        
        choice = input("Выберите действие (1-5): ").strip()
        
        if choice == '1':
            # --- Погода на сегодня ---
            print(f"\n🔍 Определяем текущую дату для временной зоны {city_timezone}...")
            target_date = get_current_time_in_zone(city_timezone)
            storage_date_str = format_date_for_storage(target_date)
            display_date_str = format_date_for_display(target_date)
            
            print(f"📅 Текущая дата в городе: {display_date_str}")
            
            record = JournalManager.get_weather_for_date(journal, current_city, storage_date_str)
            
            if record:
                print(f"📖 Найдена запись в дневнике на {display_date_str}:")
                display_weather(record, current_city)
            else:
                print(f"🌐 Записи на {display_date_str} нет. Запрашиваем из API...")
                coords = get_coordinates(current_city)
                if coords:
                    weather = get_weather_for_date(coords[0], coords[1], target_date, city_timezone)
                    if weather:
                        JournalManager.add_weather_record(journal, current_city, storage_date_str, weather)
                        JournalManager.save_journal(journal)
                        display_weather(weather, current_city)
                    else:
                        print("❌ Не удалось получить погоду.")
                else:
                    print("❌ Не удалось получить координаты города.")
        
        elif choice == '2':
            # --- Погода на другую дату ---
            date_str = input("Введите дату в формате ДД.ММ.ГГГГ (например, 25.12.2024): ").strip()
            target_date = parse_display_date(date_str)
            
            if not target_date:
                print("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                continue
            
            today = datetime.date.today()
            if target_date > today:
                print("⚠️ Нельзя запросить погоду на будущее (доступен только прогноз, но дневник хранит прошлое).")
                continue
            
            storage_date_str = format_date_for_storage(target_date)
            display_date_str = format_date_for_display(target_date)
            
            record = JournalManager.get_weather_for_date(journal, current_city, storage_date_str)
            
            if record:
                print(f"📖 Найдена запись в дневнике на {display_date_str}:")
                display_weather(record, current_city)
            else:
                print(f"🌐 Записи на {display_date_str} нет. Запрашиваем из API...")
                coords = get_coordinates(current_city)
                if coords:
                    weather = get_weather_for_date(coords[0], coords[1], target_date, city_timezone)
                    if weather:
                        JournalManager.add_weather_record(journal, current_city, storage_date_str, weather)
                        JournalManager.save_journal(journal)
                        display_weather(weather, current_city)
                    else:
                        print("❌ Не удалось получить погоду за эту дату.")
                else:
                    print("❌ Не удалось получить координаты города.")
        
        elif choice == '3':
            # --- История погоды ---
            city_key = current_city.lower()
            if city_key in journal and journal[city_key]:
                print(f"\n📜 История погоды для {current_city}:")
                # Сортируем даты (в формате хранения YYYY-MM-DD, что удобно для сортировки)
                sorted_dates = sorted(journal[city_key].keys(), reverse=True)
                for storage_date_str in sorted_dates:
                    weather = journal[city_key][storage_date_str]
                    display_date = storage_to_display(storage_date_str)
                    t_max = weather.get('temperature_max', '?')
                    t_min = weather.get('temperature_min', '?')
                    humidity = weather.get('humidity', '?')
                    pressure = weather.get('pressure_mmhg', weather.get('pressure_hpa', '?'))
                    wind = weather.get('wind_speed_ms', weather.get('wind_speed_kmh', '?'))
                    
                    # Формируем строку с дополнительными данными
                    extra = []
                    if humidity != '?':
                        extra.append(f"💧{humidity}%")
                    if pressure != '?':
                        extra.append(f"📊{pressure}")
                    if wind != '?':
                        wind_unit = "м/с" if weather.get('wind_speed_ms') else "км/ч"
                        extra.append(f"💨{wind}{wind_unit}")
                    
                    extra_str = " | ".join(extra) if extra else ""
                    print(f"  {display_date}: {t_min}..{t_max}°C  {extra_str}")
            else:
                print(f"📭 В дневнике пока нет записей для города {current_city}.")
        
        elif choice == '4':
            # --- Смена города ---
            new_city, new_timezone = change_city_interactive()
            if new_city and new_city != current_city:
                current_city = new_city
                city_timezone = new_timezone if new_timezone else "Europe/Moscow"
                print(f"🏙️ Текущий город изменен на: {current_city}")
                if city_timezone:
                    print(f"🕐 Временная зона: {city_timezone}")
        
        elif choice == '5':
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор. Пожалуйста, введите 1-5.")

if __name__ == "__main__":
    main()


