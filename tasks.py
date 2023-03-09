import logging
from concurrent.futures import ProcessPoolExecutor
from constants import ERROR_WEATHER_API, TIMEOUT_PERIOD
from utils import CITIES, ERR_MESSAGE_TEMPLATE


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

    pass


class DataAggregationTask:
    """Объединение вычисленных данных"""
    pass


class DataAnalyzingTask:
    """Финальный анализ и получение результата"""
    pass
