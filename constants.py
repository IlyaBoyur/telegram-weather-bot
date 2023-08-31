ERROR_WEATHER_API = (
    "Возникла ошибка {error} при запросе в API Яндекс Погоды. Город: {city}"
)
ERROR_GEO_API = (
    "Возникла ошибка {error}"
    " при запросе в API Яндекс Геокодера. Адрес: {address}"
)
ERROR_GEO_PARSING_API = (
    "Возникла ошибка {error}"
    " при обработке ответа API Яндекс Геокодера. Адрес: {address}"
)
TIMEOUT_PERIOD = 25
PLEASANT_CONDITIONS = {"clear", "partly-cloudy", "cloudy", "overcast"}
FORECAST_TARGET_HOURS = set(range(9, 20))
