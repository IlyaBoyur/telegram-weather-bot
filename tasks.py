import logging
from concurrent.futures import ProcessPoolExecutor
from constants import ERROR_WEATHER_API, TIMEOUT_PERIOD
from utils import CITIES, ERR_MESSAGE_TEMPLATE
from constants import FORECAST_TARGET_HOURS, PLEASANT_CONDITIONS

logger = logging.getLogger(__name__)


class DataFetchingTask:
    """Получение данных через API"""

    def __init__(self, api):
        self.api = api

    def load_url(self, city):
        try:
            return city, self.api.get_forecasting(city)
        except Exception as error:
            logger.error(ERROR_WEATHER_API.format(city=city, error=error))

    def get_weather_data(self):
        with ProcessPoolExecutor() as pool:
            # rough_data = pool.map(DataFetchingTask(YandexWeatherAPI()).run, CITIES)
            try:
                return pool.map(self.load_url, CITIES, timeout=TIMEOUT_PERIOD)
            except TimeoutError as error:
                logger.error(error)
                raise RuntimeError()


class DataCalculationTask:
    """Вычисление погодных параметров"""

    def __init__(self, data):
        self.data = data
        self.unique_days = set()
        self.city_forecasts = {}

    @staticmethod
    def select_forecast_hours(forecast):
        hours = [
            hour for hour in forecast["hours"] if int(hour["hour"]) in FORECAST_TARGET_HOURS
        ]
        return hours

    @staticmethod
    def calculate_avg_temperature(forecast_hours):
        """Считает среднюю температуру за период"""

        temperature = sum(hour["temp"] for hour in forecast_hours) / len(forecast_hours)
        return temperature
    
    @staticmethod
    def calculate_comfort_hours(forecast_hours):
        """Считает время без осадков за период"""

        pleasant_hours = sum(
            1 for hour in forecast_hours if hour["condition"] in PLEASANT_CONDITIONS
        )
        return pleasant_hours

    def worker(self):
        for city, data in self.data:
            forecast_days = {}
            
            for forecast in data["forecasts"]:
                hours = self.select_forecast_hours(forecast)
                if not hours:
                    continue
                forecast_days[forecast["date"]] = {
                    "temperature_avg": self.calculate_avg_temperature(hours),
                    "pleasant_hours": self.calculate_comfort_hours(hours),
                }

            self.city_forecasts[city] = {"forecast_days": forecast_days}
            self.unique_days.update(forecast_days.keys())


class DataAggregationTask:
    """Объединение вычисленных данных"""
    pass


class DataAnalyzingTask:
    """Финальный анализ и получение результата"""
    pass
