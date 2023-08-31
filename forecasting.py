import logging

from api_client import YandexGeoAPI, YandexWeatherAPI
from tasks import (
    DataAggregationTask,
    DataAnalyzingTask,
    DataCalculationTask,
    DataFetchingTask,
    GeoDataFetchingTask,
    GeoDataParsingTask,
)
from utils import CITIES

logger = logging.getLogger()


def forecast_weather():
    """
    Анализ погодных условий по городам.
    "_input" в списке параметров -
    куда направить результат работы предыдущей задачи.
    Значение None означает, что входные данные не требуются.
    """
    for task, params in [
        [
            GeoDataFetchingTask,
            {
                "api": YandexGeoAPI(),
                "addresses": CITIES.keys(),
                "_input": None,
            },
        ],
        [GeoDataParsingTask, {"_input": "locations"}],
        [DataFetchingTask, {"api": YandexWeatherAPI(), "_input": "locations"}],
        [DataCalculationTask, {"_input": "forecasts"}],
        [DataAggregationTask, {"_input": "city_aggregations"}],
        [DataAnalyzingTask, {"_input": "cities"}],
    ]:
        if (parameter := params.pop("_input", None)) is not None:
            params = {f"{parameter}": data, **params}
        data = task(**params).worker()

    return data


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
