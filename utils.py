import os

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "False") == "True"
YANDEX_WEATHER_API_URL = os.getenv("YANDEX_WEATHER_API_URL", "")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_API_LANGUAGE = os.getenv("YANDEX_API_LANGUAGE", "ru_RU")

if DEBUG:
    CITIES = {
        "MOSCOW": "https://code.s3.yandex.net/async-module/moscow-response.json",
        "PARIS": "https://code.s3.yandex.net/async-module/paris-response.json",
        "LONDON": "https://code.s3.yandex.net/async-module/london-response.json",
        "BERLIN": "https://code.s3.yandex.net/async-module/berlin-response.json",
        "BEIJING": "https://code.s3.yandex.net/async-module/beijing-response.json",
        "KAZAN": "https://code.s3.yandex.net/async-module/kazan-response.json",
        "SPETERSBURG": "https://code.s3.yandex.net/async-module/spetersburg-response.json",
        "VOLGOGRAD": "https://code.s3.yandex.net/async-module/volgograd-response.json",
        "NOVOSIBIRSK": "https://code.s3.yandex.net/async-module/novosibirsk-response.json",
        "KALININGRAD": "https://code.s3.yandex.net/async-module/kaliningrad-response.json",
        "ABUDHABI": "https://code.s3.yandex.net/async-module/abudhabi-response.json",
        "WARSZAWA": "https://code.s3.yandex.net/async-module/warszawa-response.json",
        "BUCHAREST": "https://code.s3.yandex.net/async-module/bucharest-response.json",
        "ROMA": "https://code.s3.yandex.net/async-module/roma-response.json",
        "CAIRO": "https://code.s3.yandex.net/async-module/cairo-response.json",
    }
else:
    CITIES = {
        "MOSCOW": [55.755864, 37.617698],
        "PARIS": [48.856663, 2.351556],
        "LONDON": [51.507351, -0.127696],
        "BERLIN": [52.518621, 13.375142],
        "BEIJING": [39.901850, 116.391441],
        "KAZAN": [55.796127, 49.106414],
        "SPETERSBURG": [59.938784, 30.314997],
        "VOLGOGRAD": [48.707067, 44.516975],
        "NOVOSIBIRSK": [55.030204, 82.920430],
        "KALININGRAD": [54.710162, 20.510137],
        "ABUDHABI": [24.443257, 54.393071],
        "WARSZAWA": [52.232090, 21.007139],
        "BUCHAREST": [44.436379, 26.099041],
        "ROMA": [41.887064, 12.504809],
        "CAIRO": [30.050755, 31.246909],
    }

ERR_MESSAGE_TEMPLATE = "Something wrong. Please contact with mentor."

MIN_MAJOR_PYTHON_VER = 3
MIN_MINOR_PYTHON_VER = 9


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
