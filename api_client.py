import json
import logging
from http import HTTPStatus
from urllib.request import urlopen

from utils import CITIES, ERR_MESSAGE_TEMPLATE

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
    def _do_req(url):
        """Base request method"""
        try:
            with urlopen(url) as request:
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
        except YandexWeatherAPIError as error:
            logger.error(error)
            raise RuntimeError(ERR_MESSAGE_TEMPLATE)

    @staticmethod
    def _get_url_by_city_name(city_name: str) -> str:
        try:
            return CITIES[city_name]
        except KeyError:
            raise Exception(ERROR_NO_CITY.format(city=city_name))

    def get_forecasting(self, city_name: str):
        """
        :param city_name: key as str
        :return: response data as json
        """
        city_url = self._get_url_by_city_name(city_name)
        return self._do_req(city_url)
