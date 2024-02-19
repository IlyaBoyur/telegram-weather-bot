import json
import logging
from abc import ABC
from dataclasses import dataclass
from http import HTTPStatus
from typing import Tuple, Union
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from city_repository import CityRepository
from settings import (
    ERR_MESSAGE_TEMPLATE,
    YANDEX_GEO_API_KEY,
    YANDEX_GEO_API_LANGUAGE,
    YANDEX_GEO_API_URL,
    YANDEX_WEATHER_API_KEY,
    YANDEX_WEATHER_API_LANGUAGE,
    YANDEX_WEATHER_API_URL,
)

logger = logging.getLogger()

ERROR_HTTP = "Error during execute request. {status}: {reason}"
ERROR_NO_CITY = "Please check that city {city} exists"
ERROR_RESPONSE = "Invalid response format: {error}"


class YandexAPIError(RuntimeError):
    pass


@dataclass
class YandexAPI(ABC):
    """Base class for requests."""

    api_url: str
    api_key: str
    exception_class: RuntimeError = YandexAPIError
    language: str = "ru_RU"

    def _do_req(self, url: str):
        """Base request method."""
        headers = {"X-Yandex-API-Key": self.api_key} if self.api_key else {}
        try:
            with urlopen(Request(url, headers=headers)) as request:
                response = request.read().decode("utf-8")
                result = json.loads(response)
            if HTTPStatus.OK != request.status:
                raise self.exception_class(
                    ERROR_HTTP.format(response.status, response.reason)
                )
            return result
        except (TypeError, json.decoder.JSONDecodeError) as error:
            logger.error(ERROR_RESPONSE.format(error))
            raise RuntimeError(error)
        except (HTTPError, self.exception_class):
            logger.exception(ERR_MESSAGE_TEMPLATE)
            raise RuntimeError


class YandexWeatherAPIError(YandexAPIError):
    pass


@dataclass
class YandexWeatherAPI(YandexAPI):
    """Base class for requests to YandexWeatherAPI."""

    api_url: str = YANDEX_WEATHER_API_URL
    api_key: str = YANDEX_WEATHER_API_KEY
    exception_class: YandexAPIError = YandexWeatherAPIError
    language: str = YANDEX_WEATHER_API_LANGUAGE
    city_service: CityRepository

    def _get_url_by_city_name(self, city_name: str) -> str:
        if (city := self.city_service.first(name=city_name)) is None:
            raise self.exception_class(ERROR_NO_CITY.format(city=city_name))
        latitude, longitude = city
        return self._get_url_by_coords(latitude, longitude)

    def _get_url_by_coords(self, latitude: float, longitude: float) -> str:
        query = urlencode(
            {
                "lat": latitude,
                "lon": longitude,
                "lang": self.language,
                "limit": 1,
            }
        )
        return f"{self.api_url}?{query}"

    def get_forecasting(self, location: Union[str, Tuple[float, float]]):
        """
        :param location: string or a tuple of two float coordinates
        :return: response data as json
        """
        if isinstance(location, tuple):
            latitude, longitude = location
            location_url = self._get_url_by_coords(latitude, longitude)
        elif isinstance(location, str):
            location_url = self._get_url_by_city_name(location)
        else:
            raise self.exception_class(
                "City parameter should be a string or a tuple of two float coordinates"
            )
        return self._do_req(location_url)


class YandexGeoAPIError(YandexAPIError):
    pass


@dataclass
class YandexGeoAPI(YandexAPI):
    """Base class for requests to YandexGeoAPI."""

    api_url: str = YANDEX_GEO_API_URL
    api_key: str = YANDEX_GEO_API_KEY
    exception_class: YandexAPIError = YandexGeoAPIError
    language: str = YANDEX_GEO_API_LANGUAGE

    def get_geolocation(self, address: str):
        """
        :param address: key as str
        :return: response data as json
        """
        query = urlencode(
            {
                "apikey": self.api_key,
                "geocode": address,
                "format": "json",
            }
        )
        return self._do_req(f"{self.api_url}?{query}")
