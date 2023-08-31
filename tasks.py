import abc
import logging
import queue
from datetime import datetime
from multiprocessing import Pool, Process, Queue, current_process
from multiprocessing.dummy import Pool as ThreadPool
from typing import Any, Dict, List, Optional, Tuple, Union

from api_client import YandexGeoAPI, YandexWeatherAPI
from constants import (
    ERROR_GEO_API,
    ERROR_GEO_PARSING_API,
    ERROR_WEATHER_API,
    FORECAST_TARGET_HOURS,
    PLEASANT_CONDITIONS,
)
from utils import CITIES

logger = logging.getLogger(__name__)


class Task(abc.ABC):
    @abc.abstractmethod
    def worker(self) -> Any:
        pass


class DataFetchingTask(Task):
    """Получение данных через API."""

    def __init__(self, api: YandexWeatherAPI, locations: List[str]):
        self.api = api
        self.locations = locations

    def load_url(self, location: Union[str, Tuple[float, float]]):
        try:
            json_response = self.api.get_forecasting(location)
            result = dict(location=location, **json_response)
        except RuntimeError as error:
            logger.error(ERROR_WEATHER_API.format(city=location, error=error))
            result = None
        finally:
            return result

    def worker(self):
        with ThreadPool() as pool:
            data = [
                forecast
                for forecast in pool.map(self.load_url, self.locations)
                if forecast is not None
            ]
            logger.debug(f"DataFetchingTask output: {data}")
            return data


class DataCalculationTask(Task):
    """Вычисление погодных параметров."""

    def __init__(self, forecasts: List[Any]):
        self.forecasts = forecasts

    @staticmethod
    def select_forecast_hours(all_hours: List[Dict[str, Any]]):
        """Фильтрует прогнозные данные по времени."""

        hours = [
            hour
            for hour in all_hours
            if int(hour["hour"]) in FORECAST_TARGET_HOURS
        ]
        return hours

    @staticmethod
    def calculate_avg_temperature(hours: List[Dict[str, Any]]):
        """Считает среднюю температуру за период."""

        temperature = sum(hour["temp"] for hour in hours) / len(hours)
        return temperature

    @staticmethod
    def calculate_comfort_hours(hours: List[Dict[str, Any]]):
        """Считает время без осадков за период."""

        pleasant_hours = sum(
            1 for hour in hours if hour["condition"] in PLEASANT_CONDITIONS
        )
        return pleasant_hours

    def calculate_city_data(self, data: Dict[str, Any]):
        days = {}

        for forecast in data["forecasts"]:
            hours = self.select_forecast_hours(forecast["hours"])
            if not hours:
                continue
            day = {
                "temperature_avg": self.calculate_avg_temperature(hours),
                "pleasant_hours": self.calculate_comfort_hours(hours),
            }
            days[forecast["date"]] = day

        temperature_total_avg = sum(
            days[day]["temperature_avg"] for day in days
        ) / len(days)
        hours_total_avg = sum(
            days[day]["pleasant_hours"] for day in days
        ) / len(days)
        city = {
            "city": data["geo_object"]["locality"]["name"],
            "location": data["location"],
            "forecast_days": days,
            "temperature_total_avg": temperature_total_avg,
            "hours_total_avg": hours_total_avg,
        }
        return city

    def worker(self):
        with Pool() as pool:
            city_forecasts = pool.map(self.calculate_city_data, self.forecasts)
        logger.debug(f"forecasts_data: {city_forecasts}")
        return city_forecasts


class DataAggregationTask(Task):
    """Объединение вычисленных данных."""

    def __init__(self, city_aggregations: List[Any]):
        self.city_aggregations = city_aggregations

    def worker(self):
        for number, city in enumerate(
            sorted(
                self.city_aggregations,
                key=lambda city: (
                    -city["temperature_total_avg"],
                    -city["hours_total_avg"],
                ),
            ),
            1,
        ):
            logger.info(
                f"{number:3}) {city['city']:15}"
                f"   temp_avg:{city['temperature_total_avg']:5.2f}"
                f"   hours_avg:{city['hours_total_avg']:5.2f}"
            )
            city["rating"] = number
        logger.debug(f"aggregations_data: {self.city_aggregations}")
        return self.city_aggregations


class DataAnalyzingTask(Task):
    """Финальный анализ и получение результата."""

    def __init__(self, cities: List[Any]):
        self.cities = cities
        self.all_days = self.get_sorted_days(cities)

    @staticmethod
    def get_sorted_days(cities: List[Any]):
        days_gen = (city["forecast_days"] for city in cities)
        unique_days = set(key for days in days_gen for key in days.keys())
        sorted_days = sorted(unique_days)
        logger.info(f"unique days: {sorted_days}")
        return sorted_days

    @staticmethod
    def prepare_city_rows(city: Dict[str, Any], all_days: List[str]):
        days = city["forecast_days"]

        temperature_avg_days = [
            days.get(day, {}).get("temperature_avg", "") for day in all_days
        ]
        temperature_row = [
            city["city"].lower().title(),
            "Температура, среднее",
            *[
                f"{temperature:.1f}" if temperature else ""
                for temperature in temperature_avg_days
            ],
            f"{city['temperature_total_avg']:.1f}",
            city["rating"],
        ]
        hours_avg_days = [
            days.get(day, {}).get("pleasant_hours", "") for day in all_days
        ]
        hours_row = [
            "",
            "Без осадков, часов",
            *[f"{hours:.1f}" if hours else "" for hours in hours_avg_days],
            f"{city['hours_total_avg']:.1f}",
            "",
        ]
        return temperature_row, hours_row

    def prepare_city_rows_parallel(self, active: Queue, finished: Queue):
        while True:
            try:
                city = active.get_nowait()
            except queue.Empty:
                logging.debug(f"Process {current_process().pid} has finished")
                break
            else:
                finished.put(self.prepare_city_rows(city, self.all_days))

    def worker(self):
        import os

        import tablib

        dataset = tablib.Dataset()
        dataset.headers = [
            "Город/день",
            "",
            *[
                datetime.strptime(day, "%Y-%m-%d").strftime("%d-%m")
                for day in self.all_days
            ],
            "Среднее",
            "Рейтинг",
        ]

        queue_in, queue_out = Queue(), Queue()
        [queue_in.put(city) for city in self.cities]
        processes = []
        for _ in range(os.cpu_count()):
            process = Process(
                target=self.prepare_city_rows_parallel(queue_in, queue_out)
            )
            process.start()
            processes.append(process)
        [process.join() for process in processes]
        while not queue_out.empty():
            dataset.extend(queue_out.get())
        return dataset


class GeoDataFetchingTask(Task):
    """Получение данных через API Геокодера."""

    def __init__(
        self, api: YandexGeoAPI, addresses: Optional[List[str]] = None
    ):
        self.api = api
        self.addresses = addresses or CITIES

    def load_url(self, address: str):
        try:
            json_response = self.api.get_geolocation(address)
            result = dict(address=address, **json_response)
        except RuntimeError as error:
            logger.error(ERROR_GEO_API.format(address=address, error=error))
            result = None
        finally:
            return result

    def worker(self) -> List[Any]:
        with ThreadPool() as pool:
            data = [
                location
                for location in pool.map(self.load_url, self.addresses)
                if location is not None
            ]
            logger.debug(f"DataFetchingTask output: {data}")
            return data


class GeoDataParsingTask(Task):
    """Определение координат геообъекта."""

    def __init__(self, locations: list[Any]):
        self.locations = locations

    @staticmethod
    def get_coordinates(location) -> tuple[float, float]:
        try:
            collection = location["response"]["GeoObjectCollection"]
            count = collection["metaDataProperty"]["GeocoderResponseMetaData"][
                "found"
            ]
            if count != "1":
                logger.warning(
                    f"To many locations has been found: {count}. First location is used"
                )
            longitude, latitude = collection["featureMember"][0]["GeoObject"][
                "Point"
            ]["pos"].split()[:2]
            return float(latitude), float(longitude)
        except (TypeError, KeyError, RuntimeError) as error:
            raise RuntimeError(
                ERROR_GEO_PARSING_API.format(error=error, address=location)
            )

    def worker(self) -> List[Any]:
        with Pool() as pool:
            data = [
                coords
                for coords in pool.map(self.get_coordinates, self.locations)
                if coords is not None
            ]
            logger.debug(f"GeoDataParsingTask output: {data}")
            return data
