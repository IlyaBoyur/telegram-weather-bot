import logging
from constants import ERROR_WEATHER_API, TIMEOUT_PERIOD,  FORECAST_TARGET_HOURS, PLEASANT_CONDITIONS
from utils import CITIES, ERR_MESSAGE_TEMPLATE
from multiprocessing import Process, Queue, Pool
from multiprocessing.dummy import Pool as ThreadPool
from datetime import datetime


logger = logging.getLogger(__name__)


class DataFetchingTask:
    """Получение данных через API"""

    def __init__(self, api):
        self.api = api

    def load_url(self, city):
        try:
            json_response = self.api.get_forecasting(city)
            result = dict(city=city, **json_response)
        except Exception as error:
            logger.error(ERROR_WEATHER_API.format(city=city, error=error))
            result = None
        finally:
            return result

    def worker(self):
        with ThreadPool() as pool:
            data = [
                forecast
                for forecast in pool.map(self.load_url, CITIES)
                if forecast is not None
            ]
            logger.debug(f"DataFetchingTask output: {data}")
            return data


class DataCalculationTask:
    """Вычисление погодных параметров"""

    def __init__(self, cities):
        self.cities = cities

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
        city["city"] = data["city"]
        city["forecast_days"] = days
        city["temperature_total_avg"] = temperature_total_avg
        city["hours_total_avg"] = hours_total_avg
        return city

    def worker(self):
        with Pool() as pool:
            city_forecasts = pool.map(self.calculate_city_data, self.cities)
        logger.debug(f"forecasts_data: {city_forecasts}")
        return city_forecasts


class DataAggregationTask:
    """Объединение вычисленных данных"""

    def __init__(self, city_aggregations):
        self.city_aggregations = city_aggregations

    def worker(self):
        # for number, city in enumerate(
        #     sorted(
        #         self.city_aggregations,
        #         key=lambda city: (
        #             -self.city_aggregations[city]["temperature_total_avg"],
        #             -self.city_aggregations[city]["hours_total_avg"],
        #         ),
        #     ),
        #     1,
        # ):
        #     logger.info(
        #         f"{number:3}) {city:15}"
        #         f"   temp_avg:{self.city_aggregations[city]['temperature_total_avg']:5.2f}"
        #         f"   hours_avg:{self.city_aggregations[city]['hours_total_avg']:5.2f}"
        #     )
        #     self.city_aggregations[city]['rating'] = number
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
            city['rating'] = number
        logger.debug(f"aggregations_data: {self.city_aggregations}")
        return self.city_aggregations


class DataAnalyzingTask:
    """Финальный анализ и получение результата"""

    def __init__(self, cities):
        self.cities = cities
        
    def get_sorted_days(self):
        days_gen = (city["forecast_days"] for city in self.cities)
        unique_days = set(
            key for days in days_gen for key in days.keys() 
        )
        sorted_days = sorted(unique_days)
        logger.info(f"unique days: {sorted_days}")
        return sorted_days

    @staticmethod
    def prepare_city_rows(city, all_days):
            days = city["forecast_days"]

        temperature_avg_days = [days.get(day, {}).get("temperature_avg", "") for day in all_days]
        temperature_row = [
                    city['city'].lower().title(),
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
                task = active.get_nowait()
            except queue.Empty:
                logging.debug(f"Process {current_process().pid} has finished")
                break
            else:
                tasks_completed.put(self.prepare_city_rows(city, all_days))

    def worker(self):
        import tablib
        import os

        sorted_days = self.get_sorted_days()

        dataset = tablib.Dataset()
        dataset.headers = [
            "Город/день",
            "",
            *[datetime.strptime(day, "%Y-%m-%d").strftime("%d-%m") for day in sorted_days],
            "Среднее",
            "Рейтинг",
        ]

        queue_in, queue_out = Queue(), Queue()
        processes = []
        for _ in range(os.cpu_count()):
            process = Process(target=self.prepare_city_rows_parallel(queue_in, queue_out))
            process.start()
            processes.append(process)
        [process.join() for process in processes]
        
        while not queue_out.empty():
            dataset.extend(queue.get())

        return dataset
