import logging

from api_client import YandexWeatherAPI
from tasks import (
    DataAggregationTask,
    DataAnalyzingTask,
    DataCalculationTask,
    DataFetchingTask,
)

logger = logging.getLogger()


def forecast_weather():
    """Анализ погодных условий по городам"""

    rough_data = DataFetchingTask(YandexWeatherAPI()).worker()
    forecasts_data = DataCalculationTask(rough_data).worker()
    aggregations_data = DataAggregationTask(forecasts_data).worker()
    dataset = DataAnalyzingTask(aggregations_data).worker()
    return dataset


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(levelname)s] - %(asctime)s - %(message)s",
        level=logging.INFO,
        datefmt="%H:%M:%S",
    )

    dataset = forecast_weather()
    # Write spreadsheet to disk
    with open("forecasts.xls", "wb") as f:
        f.write(dataset.export("xls"))
