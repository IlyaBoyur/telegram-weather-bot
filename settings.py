import os

from dotenv import load_dotenv

load_dotenv()


DEBUG = os.getenv("DEBUG", "False") == "True"

ERR_MESSAGE_TEMPLATE = "Something wrong. Please contact with mentor."
MIN_MAJOR_PYTHON_VER = 3
MIN_MINOR_PYTHON_VER = 9

YANDEX_WEATHER_API_URL = os.getenv("YANDEX_WEATHER_API_URL")
YANDEX_WEATHER_API_KEY = os.getenv("YANDEX_WEATHER_API_KEY")
YANDEX_WEATHER_API_LANGUAGE = os.getenv("YANDEX_WEATHER_API_LANGUAGE", "ru_RU")
YANDEX_GEO_API_URL = os.getenv("YANDEX_GEO_API_URL")
YANDEX_GEO_API_KEY = os.getenv("YANDEX_GEO_API_KEY")
YANDEX_GEO_API_LANGUAGE = os.getenv("YANDEX_GEO_API_LANGUAGE", "ru_RU")

DATA_ROOT = os.getenv("DATA_ROOT", "./data")
DATA_FILE = "cities_data_debug.csv" if DEBUG else "cities_data.csv"

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
MONGODB_DBNAME = os.getenv("MONGODB_DBNAME", "weather")
USE_MONGODB = os.getenv("USE_MONGODB", "False") == "True"


def check_python_version():
    import sys

    if (
        sys.version_info.major < MIN_MAJOR_PYTHON_VER
        or sys.version_info.minor < MIN_MINOR_PYTHON_VER
    ):
        raise Exception(
            "Please use python version >= {}.{}".format(
                MIN_MAJOR_PYTHON_VER, MIN_MINOR_PYTHON_VER
            )
        )
