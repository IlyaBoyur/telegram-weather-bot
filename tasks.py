import logging
from constants import ERROR_WEATHER_API, TIMEOUT_PERIOD,  FORECAST_TARGET_HOURS, PLEASANT_CONDITIONS
from utils import CITIES, ERR_MESSAGE_TEMPLATE
from multiprocessing import Process
from multiprocessing.dummy import Pool as ThreadPool
from datetime import datetime


logger = logging.getLogger(__name__)


class DataFetchingTask:
    """Получение данных через API"""

    def __init__(self, api):
        self.api = api

    def load_url(self, city):
        try:
            result = city, self.api.get_forecasting(city)
        except Exception as error:
            logger.error(ERROR_WEATHER_API.format(city=city, error=error))
            result = city, None
        finally:
            return result

    def worker(self):
        with ThreadPool() as pool:
            return [
                (city, forecast)
                for city, forecast in pool.map(self.load_url, CITIES)
                if forecast is not None
            ] 


class DataCalculationTask:
    """Вычисление погодных параметров"""

    def __init__(self, data):
        self.data = data

    @staticmethod
    def select_forecast_hours(all_hours):
        """Фильтрует прогнозные данные по времени"""

        hours = [
            hour for hour in all_hours if int(hour["hour"]) in FORECAST_TARGET_HOURS
        ]
        return hours

    @staticmethod
    def calculate_avg_temperature(hours):
        """Считает среднюю температуру за период"""

        temperature = sum(hour["temp"] for hour in hours) / len(hours)
        return temperature
    
    @staticmethod
    def calculate_comfort_hours(hours):
        """Считает время без осадков за период"""

        pleasant_hours = sum(
            1 for hour in hours if hour["condition"] in PLEASANT_CONDITIONS
        )
        return pleasant_hours

    # def calc_day_aggregates(self, hours):
    #     hours = self.select_forecast_hours(all_hours)
    #     if not hours:
    #         return
    #     return {
    #         "temperature_avg": self.calculate_avg_temperature(hours),
    #         "pleasant_hours": self.calculate_comfort_hours(hours),
    #     }

    def calculate_city_data(self, data):
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

        temperature_total_avg = sum(days[day]["temperature_avg"] for day in days) / len(days)
        hours_total_avg = sum(days[day]["pleasant_hours"] for day in days) / len(days)
        city = {}
        city["forecast_days"] = days
        city["temperature_total_avg"] = temperature_total_avg
        city["hours_total_avg"] = hours_total_avg
        return city

    def worker(self):

        city_forecasts = {
            city_name: self.calculate_city_data(data)
            for city_name, data in self.data
        }

        logger.info(f"forecasts_data: {city_forecasts}")
        return city_forecasts


class DataAggregationTask:
    """Объединение вычисленных данных"""

    def __init__(self, city_aggregations):
        self.city_aggregations = city_aggregations

    def worker(self):
        for number, city in enumerate(
            sorted(
                self.city_aggregations,
                key=lambda city: (
                    -self.city_aggregations[city]["temperature_total_avg"],
                    -self.city_aggregations[city]["hours_total_avg"],
                ),
            ),
            1,
        ):
            logger.info(
                f"{number:3}) {city:15}"
                f"   temp_avg:{self.city_aggregations[city]['temperature_total_avg']:5.2f}"
                f"   hours_avg:{self.city_aggregations[city]['hours_total_avg']:5.2f}"
            )
            self.city_aggregations[city]['rating'] = number
        logger.info(f"aggregations_data: {self.city_aggregations}")
        return self.city_aggregations


class DataAnalyzingTask:
    """Финальный анализ и получение результата"""

    def __init__(self, initial_data):
        self.data = initial_data
        
    def get_sorted_days(self):
        days_gen = (self.data[city]["forecast_days"] for city in self.data)
        unique_days = set(
            key for days in days_gen for key in days.keys() 
        )
        sorted_days = sorted(unique_days)
        logger.info(f"unique days: {sorted_days}")
        return sorted_days

    def get_unique_cities(self):
        cities = sorted(set(self.data))
        logger.info(f"unique cities: {cities}")
        return cities

    def worker(self):
        import tablib

        sorted_days = self.get_sorted_days()
        cities = self.get_unique_cities()

        dataset = tablib.Dataset()
        dataset.headers = [
            "Город/день",
            "",
            *[datetime.strptime(day, "%Y-%m-%d").strftime("%d-%m") for day in sorted_days],
            "Среднее",
            "Рейтинг",
        ]

        for city_name in cities:
            city = self.data[city_name]
            days = city["forecast_days"]

            temperature_avg_days = [days.get(day, {}).get("temperature_avg", "") for day in sorted_days]
            dataset.append(
                [
                    city_name.lower().title(),
                    "Температура, среднее",
                    *[
                        f"{temperature:.1f}" if temperature else ""
                        for temperature in temperature_avg_days
                    ],
                    f"{city['temperature_total_avg']:.1f}",
                    city["rating"],
                ]
            )

            pleasant_hours_avg_days = [
                days.get(day, {}).get("pleasant_hours", "") for day in sorted_days
            ]
            dataset.append(
                [
                    "",
                    "Без осадков, часов",
                    *[f"{hours:.1f}" if hours else "" for hours in pleasant_hours_avg_days],
                    f"{city['hours_total_avg']:.1f}",
                    "",
                ]
            )
        return dataset
