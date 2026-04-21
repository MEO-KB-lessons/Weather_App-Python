# Weather_App.py
import requests
import json
import os
import datetime
from configparser import ConfigParser
from typing import Optional, Dict, List, Tuple

# =============================================================================
# 1. КОНСТАНТЫ И НАСТРОЙКИ
# =============================================================================

# --- API URL ---
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
# Visual Crossing API
VISUALCROSSING_BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

# --- Имена файлов ---
CONFIG_FILE = "config.cfg"
JOURNAL_FILE = "weather_journal.json"
API_KEY_FILE = "visualcrossing-api-key.txt"

# --- Форматы дат ---
DISPLAY_DATE_FORMAT = "%d.%m.%Y"
STORAGE_DATE_FORMAT = "%Y-%m-%d"

# --- Функция для загрузки API ключа Visual Crossing ---
def _load_visualcrossing_api_key() -> Optional[str]:
    """Загружает API ключ Visual Crossing из файла."""
    if not os.path.exists(API_KEY_FILE):
        print(f"⚠️ Файл с API ключом не найден: {API_KEY_FILE}")
        print("   Пожалуйста, создайте файл и поместите в него ваш ключ Visual Crossing.")
        return None
    try:
        with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
            key = f.read().strip()
            if key:
                print(f"✅ API ключ Visual Crossing загружен из {API_KEY_FILE}")
                return key
            else:
                print(f"⚠️ Файл {API_KEY_FILE} пуст.")
                return None
    except Exception as e:
        print(f"⚠️ Ошибка при чтении файла с API ключом: {e}")
        return None

VISUALCROSSING_API_KEY = _load_visualcrossing_api_key()

# =============================================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

def format_date_for_display(date_obj: datetime.date) -> str:
    return date_obj.strftime(DISPLAY_DATE_FORMAT)

def format_date_for_storage(date_obj: datetime.date) -> str:
    return date_obj.strftime(STORAGE_DATE_FORMAT)

def parse_display_date(date_str: str) -> Optional[datetime.date]:
    try:
        return datetime.datetime.strptime(date_str, DISPLAY_DATE_FORMAT).date()
    except ValueError:
        return None

def storage_to_display(storage_date_str: str) -> str:
    try:
        date_obj = datetime.datetime.strptime(storage_date_str, STORAGE_DATE_FORMAT).date()
        return format_date_for_display(date_obj)
    except ValueError:
        return storage_date_str

def kmh_to_ms(kmh: Optional[float]) -> Optional[float]:
    if kmh is None:
        return None
    return round(kmh * 0.27778, 1)

def ms_to_kmh(ms: Optional[float]) -> Optional[float]:
    if ms is None:
        return None
    return round(ms * 3.6, 1)

# =============================================================================
# 3. КЛАССЫ ДЛЯ РАБОТЫ С ДАННЫМИ
# =============================================================================

class ConfigManager:
    @staticmethod
    def load_city() -> Optional[str]:
        if not os.path.exists(CONFIG_FILE):
            return None
        config = ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        if 'Settings' in config and 'city' in config['Settings']:
            return config['Settings']['city']
        return None

    @staticmethod
    def load_timezone() -> Optional[str]:
        if not os.path.exists(CONFIG_FILE):
            return None
        config = ConfigParser()
        config.read(CONFIG_FILE, encoding='utf-8')
        if 'Settings' in config and 'timezone' in config['Settings']:
            return config['Settings']['timezone']
        return None

    @staticmethod
    def save_city(city_name: str, timezone: str = None):
        config = ConfigParser()
        config['Settings'] = {'city': city_name}
        if timezone:
            config['Settings']['timezone'] = timezone
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"✅ Город '{city_name}' сохранен в настройках.")

class JournalManager:
    @staticmethod
    def load_journal() -> Dict:
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
        with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(journal, f, ensure_ascii=False, indent=2)
        print(f"💾 Дневник сохранен в файл '{JOURNAL_FILE}'.")

    @staticmethod
    def get_weather_for_date(journal: Dict, city: str, storage_date_str: str) -> Optional[Dict]:
        city_key = city.lower()
        if city_key in journal and storage_date_str in journal[city_key]:
            return journal[city_key][storage_date_str]
        return None

    @staticmethod
    def add_weather_record(journal: Dict, city: str, storage_date_str: str, weather_data: Dict):
        city_key = city.lower()
        if city_key not in journal:
            journal[city_key] = {}
        journal[city_key][storage_date_str] = weather_data

# =============================================================================
# 4. ФУНКЦИИ ДЛЯ РАБОТЫ С API
# =============================================================================

def get_coordinates_and_timezone(city_name: str) -> Optional[Tuple[float, float, str]]:
    print(f"🔍 Поиск координат и часового пояса для города: {city_name}...")
    params = {'name': city_name, 'count': 1, 'language': 'ru', 'format': 'json'}
    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('results'):
            first_result = data['results'][0]
            lat = first_result['latitude']
            lon = first_result['longitude']
            timezone = first_result.get('timezone')
            print(f"✅ Найдены координаты: {lat:.4f}, {lon:.4f}")
            if timezone:
                print(f"✅ Определен часовой пояс: {timezone}")
            return lat, lon, timezone
        else:
            print(f"❌ Город '{city_name}' не найден.")
            return None
    except Exception as e:
        print(f"❌ Ошибка подключения к геокодеру: {e}")
        return None

def get_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    result = get_coordinates_and_timezone(city_name)
    if result:
        return result[0], result[1]
    return None

def get_timezone_for_city(lat: float, lon: float) -> Optional[str]:
    try:
        print(f"🕐 Определяем временную зону для координат {lat:.4f}, {lon:.4f}...")
        params = {'latitude': lat, 'longitude': lon, 'timezone': 'auto'}
        response = requests.get(WEATHER_URL_OPEN_METEO, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        timezone = data.get('timezone')
        if timezone:
            print(f"✅ Определена временная зона: {timezone}")
            return timezone
        else:
            print("⚠️ Не удалось определить временную зону")
            return None
    except Exception as e:
        print(f"⚠️ Не удалось определить временную зону: {e}")
        return None

def get_weather_from_visualcrossing(lat: float, lon: float, target_date: datetime.date, timezone: str = "Europe/Moscow") -> Optional[Dict]:
    """Получает погоду через Visual Crossing API."""
    if not VISUALCROSSING_API_KEY:
        print("⚠️ Visual Crossing API ключ не настроен. Пропускаем.")
        return None

    date_str = target_date.strftime("%Y-%m-%d")
    display_date_str = format_date_for_display(target_date)
    print(f"☁️ Запрос погоды через Visual Crossing на {display_date_str}...")

    location = f"{lat},{lon}"
    url = f"{VISUALCROSSING_BASE_URL}/{location}/{date_str}"
    params = {
        'unitGroup': 'metric',
        'key': VISUALCROSSING_API_KEY,
        'include': 'days',
        'contentType': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 401:
            print("❌ Ошибка авторизации Visual Crossing. Проверьте API ключ.")
            return None
        if response.status_code == 429:
            print("❌ Превышен лимит запросов к Visual Crossing.")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        if 'days' not in data or not data['days']:
            print("⚠️ Нет данных от Visual Crossing за указанную дату")
            return None
        
        day_data = data['days'][0]
        
        wind_speed_kmh = day_data.get('windspeed')
        wind_speed_ms = kmh_to_ms(wind_speed_kmh)
        pressure_mb = day_data.get('pressure')
        pressure_mmhg = round(pressure_mb * 0.75006, 1) if pressure_mb else None
        
        # Преобразуем icon в числовой код для совместимости с display_weather
        icon_code = day_data.get('icon', '')
        weathercode_map = {
            'clear-day': 0, 'clear-night': 0,
            'partly-cloudy-day': 2, 'partly-cloudy-night': 2,
            'cloudy': 3,
            'rain': 61, 'showers-day': 61, 'showers-night': 61,
            'snow': 71, 'snow-showers-day': 71, 'snow-showers-night': 71,
            'thunder-rain': 95, 'thunder-showers-day': 95, 'thunder-showers-night': 95,
            'fog': 45, 'wind': 2
        }
        weathercode = weathercode_map.get(icon_code, 0)
        
        weather_data = {
            'date_storage': date_str,
            'date_display': display_date_str,
            'temperature_max': day_data.get('tempmax'),
            'temperature_min': day_data.get('tempmin'),
            'precipitation_sum': day_data.get('precip'),
            'wind_speed_kmh': wind_speed_kmh,
            'wind_speed_ms': wind_speed_ms,
            'pressure_hpa': pressure_mb,
            'pressure_mmhg': pressure_mmhg,
            'humidity': day_data.get('humidity'),
            'weathercode': weathercode,
            'source': 'Visual Crossing API',
            'timezone': data.get('timezone', timezone)
        }
        
        weather_data['units'] = {
            'temperature': '°C',
            'precipitation': 'mm',
            'wind_speed': 'м/с',
            'pressure': 'мм рт. ст.',
            'humidity': '%'
        }
        
        print(f"✅ Данные о погоде получены от Visual Crossing")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к Visual Crossing: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"❌ Ошибка обработки данных Visual Crossing: {e}")
        return None

def get_weather_from_openmeteo(lat: float, lon: float, target_date: datetime.date, timezone: str = "Europe/Moscow") -> Optional[Dict]:
    """Получает погоду через Open-Meteo API (резервный)."""
    date_str = format_date_for_storage(target_date)
    display_date_str = format_date_for_display(target_date)
    print(f"☁️ Запрос погоды через Open-Meteo (резервный) на {display_date_str}...")
    
    params = {
        'latitude': lat, 'longitude': lon,
        'start_date': date_str, 'end_date': date_str,
        'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 
                  'wind_speed_10m_max', 'pressure_msl_mean', 'relative_humidity_2m_mean', 'weathercode'],
        'timezone': timezone
    }
    
    try:
        response = requests.get(WEATHER_URL_OPEN_METEO, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if 'daily' not in data:
            return None

        daily = data['daily']
        wind_speed_kmh = daily.get('wind_speed_10m_max', [None])[0]
        wind_speed_ms = kmh_to_ms(wind_speed_kmh)
        pressure_hpa = daily.get('pressure_msl_mean', [None])[0]
        pressure_mmhg = round(pressure_hpa * 0.75006, 1) if pressure_hpa else None
        
        weather_data = {
            'date_storage': date_str, 'date_display': display_date_str,
            'temperature_max': daily.get('temperature_2m_max', [None])[0],
            'temperature_min': daily.get('temperature_2m_min', [None])[0],
            'precipitation_sum': daily.get('precipitation_sum', [None])[0],
            'wind_speed_kmh': wind_speed_kmh, 'wind_speed_ms': wind_speed_ms,
            'pressure_hpa': pressure_hpa, 'pressure_mmhg': pressure_mmhg,
            'humidity': daily.get('relative_humidity_2m_mean', [None])[0],
            'weathercode': daily.get('weathercode', [None])[0],
            'source': 'Open-Meteo API (резервный)', 'timezone': timezone
        }
        if 'daily_units' in data:
            weather_data['units'] = {
                'temperature': data['daily_units'].get('temperature_2m_max', '°C'),
                'precipitation': data['daily_units'].get('precipitation_sum', 'mm'),
                'wind_speed': 'м/с', 'pressure': 'мм рт. ст.', 'humidity': '%'
            }
        print(f"✅ Данные о погоде получены от Open-Meteo (резервный)")
        return weather_data
    except Exception as e:
        print(f"❌ Ошибка получения погоды из Open-Meteo: {e}")
        return None

def get_weather_for_date(lat: float, lon: float, target_date: datetime.date, timezone: str = "Europe/Moscow") -> Optional[Dict]:
    """Получает погоду за конкретную дату. Сначала Visual Crossing, потом Open-Meteo."""
    weather_data = get_weather_from_visualcrossing(lat, lon, target_date, timezone)
    if not weather_data:
        print("🔄 Переключение на резервный API Open-Meteo...")
        weather_data = get_weather_from_openmeteo(lat, lon, target_date, timezone)
    return weather_data

def get_current_time_in_zone(timezone: str = "Europe/Moscow") -> Optional[datetime.date]:
    try:
        import pytz
        tz = pytz.timezone(timezone)
        now = datetime.datetime.now(tz)
        current_date = now.date()
        print(f"✅ Текущая дата в зоне {timezone} (pytz): {format_date_for_display(current_date)}")
        return current_date
    except ImportError:
        print(f"⚠️ Библиотека pytz не установлена. Используем системную дату UTC.")
        return datetime.date.today()
    except Exception as e:
        print(f"⚠️ Ошибка определения времени: {e}. Используем системную дату.")
        return datetime.date.today()

# =============================================================================
# 5. ФУНКЦИЯ ВЫВОДА ПОГОДЫ (ПОЛНАЯ ВЕРСИЯ)
# =============================================================================

def display_weather(weather_data: Dict, city: str):
    """Красиво выводит данные о погоде в консоль."""
    print("\n" + "="*50)
    print(f"🌍 Погода в городе: {city}")
    
    # Показываем источник данных
    if 'source' in weather_data:
        print(f"📡 Источник: {weather_data['source']}")
    
    # Дата
    if 'date_display' in weather_data:
        print(f"📅 Дата: {weather_data['date_display']}")
    elif 'date' in weather_data:
        print(f"📅 Дата: {storage_to_display(weather_data['date'])}")
    
    # Временная зона
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
    
    # Давление
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
    
    # Ветер
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
        
        # Эмодзи
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

# =============================================================================
# 6. ОСНОВНАЯ ЛОГИКА ПРИЛОЖЕНИЯ
# =============================================================================

def change_city_interactive() -> Tuple[Optional[str], Optional[str]]:
    while True:
        new_city = input("Введите название нового города: ").strip()
        if not new_city:
            print("Название города не может быть пустым.")
            continue
        result = get_coordinates_and_timezone(new_city)
        if result:
            lat, lon, timezone = result
            if not timezone:
                timezone = get_timezone_for_city(lat, lon)
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
    print("="*60)
    print("         🌦️  ДНЕВНИК ПОГОДЫ  🌦️")
    print("="*60)
    
    if not VISUALCROSSING_API_KEY:
        print("⚠️ Внимание! API ключ Visual Crossing не настроен.")
        print("   Будет использоваться только резервный API Open-Meteo.")
        print(f"   Для получения ключа зарегистрируйтесь на https://www.visualcrossing.com/")
        print(f"   и сохраните ключ в файл '{API_KEY_FILE}'\n")
    
    current_city = ConfigManager.load_city()
    city_timezone = ConfigManager.load_timezone()
    
    if not current_city:
        print("👋 Привет! Похоже, вы здесь впервые.")
        current_city = input("Введите название вашего города: ").strip()
        if not current_city:
            print("Город не указан. Выход.")
            return
        result = get_coordinates_and_timezone(current_city)
        if result:
            lat, lon, city_timezone = result
            if not city_timezone:
                city_timezone = get_timezone_for_city(lat, lon)
            ConfigManager.save_city(current_city, city_timezone)
        else:
            print("Не удалось найти указанный город. Попробуйте позже.")
            return
    else:
        print(f"🏙️  Текущий город, сохраненный в настройках: {current_city}")
        if city_timezone:
            print(f"🕐 Временная зона: {city_timezone}")
        else:
            print("🕐 Временная зона не сохранена. Пробуем определить...")
            result = get_coordinates_and_timezone(current_city)
            if result:
                lat, lon, city_timezone = result
                if not city_timezone:
                    city_timezone = get_timezone_for_city(lat, lon)
                if city_timezone:
                    ConfigManager.save_city(current_city, city_timezone)
    
    if not city_timezone:
        city_timezone = "Europe/Moscow"
        print(f"⚠️ Используется временная зона по умолчанию: {city_timezone}")
    
    journal = JournalManager.load_journal()
    
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
                print("-" * 80)
                # Заголовки
                print(f"{'Дата':<12} {'Температура':^20} {'Влажность':^12} {'Давление':^12} {'Ветер':^12} {'Источник':^15}")
                print("-" * 80)
                
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
                    source = weather.get('source', '?')
                    
                    # Форматируем температуру
                    temp_str = f"{t_min}..{t_max}°C"
                    
                    # Форматируем влажность
                    humidity_str = f"💧{humidity}%" if humidity != '?' else "💧--"
                    
                    # Форматируем давление
                    pressure_str = f"📊{pressure}" if pressure != '?' else "📊--"
                    
                    # Форматируем ветер
                    if wind != '?':
                        wind_unit = "м/с" if weather.get('wind_speed_ms') else "км/ч"
                        wind_str = f"💨{wind}{wind_unit}"
                    else:
                        wind_str = "💨--"
                    
                    # Выводим отформатированную строку
                    print(f"{display_date:<12} {temp_str:^20} {humidity_str:^12} {pressure_str:^12} {wind_str:^12} {source:^15}")
                
                print("-" * 80)
            else:
                print(f"📭 В дневнике пока нет записей для города {current_city}.")

        elif choice == '4':
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
