from utils import ERR_MESSAGE_TEMPLATE


class DataFetchingTask:
    """Получение данных через API"""

    def __init__(self, api):
        self.api = api

    def run(self, city):
        try:
            return city, self.api.get_forecasting(city)
        except Exception as error:
            logger.error(ERR_MESSAGE_TEMPLATE)


class DataCalculationTask:
    """Вычисление погодных параметров"""

    pass


class DataAggregationTask:
    """Объединение вычисленных данных"""
    pass


class DataAnalyzingTask:
    """Финальный анализ и получение результата"""
    pass
