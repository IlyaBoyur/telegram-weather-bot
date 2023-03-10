import logging

# import threading
# import subprocess
import multiprocessing



from api_client import YandexWeatherAPI
from constants import FORECAST_TARGET_HOURS, PLEASANT_CONDITIONS
from tasks import DataAggregationTask, DataAnalyzingTask, DataCalculationTask, DataFetchingTask


logger = logging.getLogger()


def forecast_weather():
    """Анализ погодных условий по городам"""

    # data request
    rough_data =  DataFetchingTask(YandexWeatherAPI()).get_weather_data()

    # weather params
    # unique_days = set()
    # city_forecasts = {}

    # for city, data in rough_data:
    #     forecast_days = {}
    #     for forecast in data["forecasts"]:
    #         forecast_hours = [
    #             hour for hour in forecast["hours"] if int(hour["hour"]) in FORECAST_TARGET_HOURS
    #         ]
    #         if not forecast_hours:
    #             continue

    #         # average temperature
    #         temperature_avg = sum(hour["temp"] for hour in forecast_hours) / len(forecast_hours)
    #         # pleasant condition hours
    #         pleasant_hours = sum(
    #             1 for hour in forecast_hours if hour["condition"] in PLEASANT_CONDITIONS
    #         )

    #         forecast_days[forecast["date"]] = {
    #             "temperature_avg": temperature_avg,
    #             "pleasant_hours": pleasant_hours,
    #         }

    #     city_forecasts[city] = {"forecast_days": forecast_days}
    #     unique_days.update(forecast_days.keys())

    # unique_city_names = set(city_forecasts.keys())
    forecasts_data = DataCalculationTask(rough_data).worker()
    # unique_city_names = set(task.city_forecasts.keys())
    # unique_days = task.unique_days
    # city_forecasts = task.city_forecasts
    logger.info(f"forecasts_data: {forecasts_data}\n")

    # # aggregations
    # for city in city_forecasts:
    #     days = city_forecasts[city]["forecast_days"]
    #     temperature_total_avg = sum(days[day]["temperature_avg"] for day in days) / len(days)
    #     hours_total_avg = sum(days[day]["pleasant_hours"] for day in days) / len(days)

    #     city_aggregations[city] = {
    #         "temperature_total_avg": temperature_total_avg,
    #         "hours_total_avg": hours_total_avg,
    #     }
    # city_aggregations = task.city_aggregations
    # logger.info(f"city_aggregations: {city_aggregations}\n")

    # rating
    # city_ratings = {}

    # for number, city in enumerate(
    #     sorted(
    #         city_aggregations,
    #         key=lambda city: (
    #             -city_aggregations[city]["temperature_total_avg"],
    #             -city_aggregations[city]["hours_total_avg"],
    #         ),
    #     ),
    #     1,
    # ):
    #     logger.info(
    #         f"{number:3}) {city:15}"
    #         f"   temp_avg:{city_aggregations[city]['temperature_total_avg']:5.2f}"
    #         f"   hours_avg:{city_aggregations[city]['hours_total_avg']:5.2f}"
    #     )
    #     city_ratings[city] = {"rating": number}


    aggregations_data = DataAggregationTask(forecasts_data).worker()
    # task.worker()
    # city_ratings = task.city_ratings

    # export
    # sorted_days = sorted(unique_days)

    # logger.info(f"unique days: {sorted_days}")
    # import tablib

    # dataset = tablib.Dataset()
    # dataset.headers = [
    #     "Город/день",
    #     "",
    #     *[datetime.strptime(day, "%Y-%m-%d").strftime("%d-%m") for day in sorted_days],
    #     "Среднее",
    #     "Рейтинг",
    # ]

    # for city in unique_city_names:
    #     days = city_forecasts[city]["forecast_days"]

    #     temperature_avg_days = [days.get(day, {}).get("temperature_avg", "") for day in sorted_days]
    #     dataset.append(
    #         [
    #             city.lower().title(),
    #             "Температура, среднее",
    #             *[
    #                 f"{temperature:.1f}" if temperature else ""
    #                 for temperature in temperature_avg_days
    #             ],
    #             f"{city_aggregations[city]['temperature_total_avg']:.1f}",
    #             city_ratings[city]["rating"],
    #         ]
    #     )

    #     pleasant_hours_avg_days = [
    #         days.get(day, {}).get("pleasant_hours", "") for day in sorted_days
    #     ]
    #     dataset.append(
    #         [
    #             "",
    #             "Без осадков, часов",
    #             *[f"{hours:.1f}" if hours else "" for hours in pleasant_hours_avg_days],
    #             f"{city_aggregations[city]['hours_total_avg']:.1f}",
    #             "",
    #         ]
    #     )
    dataset = DataAnalyzingTask(aggregations_data).worker()
    return dataset




if __name__ == "__main__":
    logging.basicConfig(format="[%(levelname)s] - %(asctime)s - %(message)s", level=logging.INFO, datefmt='%H:%M:%S')

    dataset = forecast_weather()
    # Write spreadsheet to disk
    with open("forecasts.xls", "wb") as f:
        f.write(dataset.export("xls"))
