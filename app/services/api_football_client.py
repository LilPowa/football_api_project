from typing import Any

import httpx

from app.config import settings


class ApiFootballClient:
    def __init__(self) -> None:
        settings.validate()

        self.base_url = settings.API_FOOTBALL_BASE_URL.rstrip("/")
        self.headers = {
            "x-apisports-key": settings.API_FOOTBALL_KEY
        }

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(
                    url,
                    headers=self.headers,
                    params=params or {}
                )

            response.raise_for_status()
            data = response.json()

            if data.get("errors"):
                raise RuntimeError(f"Erreur API-Football : {data['errors']}")

            return data

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                f"Erreur HTTP API-Football : {error.response.status_code} - {error.response.text}"
            ) from error

        except httpx.RequestError as error:
            raise RuntimeError(
                f"Erreur de connexion à API-Football : {str(error)}"
            ) from error

    def get_status(self) -> dict[str, Any]:
        return self.get("status")

    def get_countries(self) -> dict[str, Any]:
        return self.get("countries")

    def get_leagues(
        self,
        country: str | None = None,
        season: int | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if country:
            params["country"] = country

        if season:
            params["season"] = season

        return self.get("leagues", params=params)