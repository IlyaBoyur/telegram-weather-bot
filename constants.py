ERROR_WEATHER_API = (
    "Возникла ошибка {error} при запросе в API Яндекс Погоды. Город:{city}"
)
TIMEOUT_PERIOD = 25
PLEASANT_CONDITIONS = set(["clear", "partly-cloudy", "cloudy", "overcast"])
FORECAST_TARGET_HOURS = set(range(9, 20))
