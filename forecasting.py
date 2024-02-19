import logging
from typing import Any, Dict, List, Tuple, Type

from api_client import YandexGeoAPI, YandexWeatherAPI
from city_repository import CityRepository
from tasks import (
    DataAggregationTask,
    DataAnalyzingTask,
    DataCalculationTask,
    DataFetchingTask,
    GeoDataFetchingTask,
    GeoDataParsingTask,
    Task,
)


logger = logging.getLogger()


def process_tasks(tasks: List[Tuple[Type[Task], Dict[str, Any]]]):
    """
    "_input" в списке параметров -
    куда направить результат работы предыдущей задачи.
    Значение None означает, что входные данные не требуются.
    Первая задача должна иметь этот параметр равным None.
    """
    for task, params in tasks:
        if (parameter := params.pop("_input", None)) is not None:
            params = {f"{parameter}": data, **params}
        data = task(**params).worker()
    return data


def forecast_weather():
    """
    Анализ погодных условий по городам.
    """
    tasks = [
        (
            GeoDataFetchingTask,
            {
                "api": YandexGeoAPI(),
                "addresses": [
                    city.name for city in CityRepository().get_multi()
                ],
                "_input": None,
            },
        ),
        (GeoDataParsingTask, {"_input": "locations"}),
        (DataFetchingTask, {"api": YandexWeatherAPI(), "_input": "locations"}),
        (DataCalculationTask, {"_input": "forecasts"}),
        (DataAggregationTask, {"_input": "city_aggregations"}),
        (DataAnalyzingTask, {"_input": "cities"}),
    ]
    return process_tasks(tasks)


def get_weather(location: str) -> Dict[str, Any]:
    tasks = [
        (
            GeoDataFetchingTask,
            {"api": YandexGeoAPI(), "addresses": (location,), "_input": None},
        ),
        (GeoDataParsingTask, {"_input": "locations"}),
        (DataFetchingTask, {"api": YandexWeatherAPI(), "_input": "locations"}),
        (DataCalculationTask, {"_input": "forecasts"}),
    ]
    result: List[Dict[str, Any]] = process_tasks(tasks)
    return result.pop()


def get_weather_by_position(
    latitude: float, longitude: float
) -> Dict[str, Any]:
    """Calculate weather for a location."""
    tasks = [
        (
            DataFetchingTask,
            {"api": YandexWeatherAPI(), "locations": ((latitude, longitude),)},
        ),
        (DataCalculationTask, {"_input": "forecasts"}),
    ]
    result: List[Dict[str, Any]] = process_tasks(tasks)
    return result.pop()


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
