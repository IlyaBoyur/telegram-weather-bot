import json
import logging
from http import HTTPStatus
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from utils import (
    CITIES,
    ERR_MESSAGE_TEMPLATE,
    YANDEX_API_KEY,
    YANDEX_API_LANGUAGE,
    YANDEX_WEATHER_API_URL,
)

logger = logging.getLogger()

ERROR_HTTP = "Error during execute request. {status}: {reason}"
ERROR_NO_CITY = "Please check that city {city} exists"
ERROR_RESPONSE = "Invalid response format: {error}"


class YandexWeatherAPIError(RuntimeError):
    pass


class YandexWeatherAPI:
    """
    Base class for requests
    """

    @staticmethod
    def _do_req(url: str):
        """Base request method"""
        try:
            with urlopen(
                Request(url, headers={"X-Yandex-API-Key": YANDEX_API_KEY})
            ) as request:
                response = request.read().decode("utf-8")
                result = json.loads(response)
            if HTTPStatus.OK != request.status:
                raise YandexWeatherAPIError(
                    ERROR_HTTP.format(response.status, response.reason)
                )
            return result
        except (TypeError, json.decoder.JSONDecodeError) as error:
            logger.error(ERROR_RESPONSE.format(error))
            raise RuntimeError(error)
        except (HTTPError, YandexWeatherAPIError):
            logger.exception(ERR_MESSAGE_TEMPLATE)
            raise RuntimeError

    @staticmethod
    def _get_url_by_city_name(city_name: str) -> str:
        if (city := CITIES.get(city_name)) is None:
            raise RuntimeError(ERROR_NO_CITY.format(city=city_name))
        lat, lon = city
        query = urlencode(
            {
                "lat": lat,
                "lon": lon,
                "lang": YANDEX_API_LANGUAGE,
                "limit": 1,
            }
        )
        return f"{YANDEX_WEATHER_API_URL}?{query}"

    def get_forecasting(self, city_name: str):
        """
        :param city_name: key as str
        :return: response data as json
        """
        city_url = self._get_url_by_city_name(city_name)
        return self._do_req(city_url)
