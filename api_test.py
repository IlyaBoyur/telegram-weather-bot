def check_python_version():
    from utils import check_python_version

    check_python_version()


def check_api():
    from api_client import YandexWeatherAPI

    CITY_NAME_FOR_TEST = "MOSCOW"

    ywAPI = YandexWeatherAPI()
    response = ywAPI.get_forecasting(CITY_NAME_FOR_TEST)
    response.get("info")


if __name__ == "__main__":
    check_python_version()
    check_api()
