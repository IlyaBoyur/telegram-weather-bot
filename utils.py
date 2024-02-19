import csv
import functools
import settings



@functools.lru_cache(1)
def get_cities_from_csv() -> list["City"]:
    from city_repository import City

    cities: list[City] = []
    try:
        with open(f"{settings.DATA_ROOT}/{settings.DATA_FILE}") as csvfile:
            cities = [
                _ for _ in csv.DictReader(csvfile, delimiter=",", escapechar="\\")
            ]
        cities = [
            City(
                name=row["city"],
                url_source=row.get("source", ""),
                **[
                    {"longitude": lon, "latitude": lat}
                    for lon, lat in [
                        [
                            float(f)
                            for f in row.get("coords", "[0,0]")
                            .strip("[]")
                            .split(",")
                        ]
                    ]
                ][0],
            )
            for row in cities
        ]
    except (KeyError, ValueError):
        cities = []
    return cities
