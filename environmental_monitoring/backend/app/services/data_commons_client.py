"""
Google Data Commons Client

Provides access to Google Data Commons API for environmental data:
- Climate data (temperature, precipitation, CO2 emissions)
- Air quality statistics (PM2.5 averages, etc.)
- Demographics (population data for correlation studies)
- Geographic data (place hierarchies, boundaries)

Data Commons aggregates data from sources like:
- NOAA, EPA, World Bank, UN, Census Bureau, WHO, etc.

Docs: https://docs.datacommons.org/api/
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx

logger = logging.getLogger(__name__)


class DataCommonsError(Exception):
    """Base exception for Data Commons API errors."""
    pass


class DataCommonsCategory(Enum):
    """Categories of data available from Data Commons."""
    CLIMATE = "climate"
    AIR_QUALITY = "air_quality"
    DEMOGRAPHICS = "demographics"
    HEALTH = "health"
    ECONOMY = "economy"
    ENERGY = "energy"
    ENVIRONMENT = "environment"


@dataclass
class StatisticalVariable:
    """A Data Commons statistical variable definition."""
    dcid: str
    name: str
    description: str
    category: DataCommonsCategory
    unit: Optional[str] = None
    measurement_period: Optional[str] = None


# Key environmental statistical variables from Data Commons
# Full list: https://datacommons.org/tools/statvar
ENVIRONMENTAL_VARIABLES: Dict[str, StatisticalVariable] = {
    # Climate / Temperature
    "Mean_Temperature": StatisticalVariable(
        dcid="Mean_Temperature",
        name="Mean Temperature",
        description="Average temperature over a time period",
        category=DataCommonsCategory.CLIMATE,
        unit="Celsius"
    ),
    "Max_Temperature": StatisticalVariable(
        dcid="Max_Temperature",
        name="Maximum Temperature",
        description="Maximum recorded temperature",
        category=DataCommonsCategory.CLIMATE,
        unit="Celsius"
    ),
    "Min_Temperature": StatisticalVariable(
        dcid="Min_Temperature",
        name="Minimum Temperature",
        description="Minimum recorded temperature",
        category=DataCommonsCategory.CLIMATE,
        unit="Celsius"
    ),
    "Annual_Precipitation": StatisticalVariable(
        dcid="AnnualPrecipitation",
        name="Annual Precipitation",
        description="Total annual precipitation",
        category=DataCommonsCategory.CLIMATE,
        unit="mm"
    ),
    
    # Air Quality
    "Mean_Concentration_AirPollutant_PM2.5": StatisticalVariable(
        dcid="Mean_Concentration_AirPollutant_PM2.5",
        name="PM2.5 Concentration",
        description="Mean concentration of particulate matter < 2.5 micrometers",
        category=DataCommonsCategory.AIR_QUALITY,
        unit="µg/m³"
    ),
    "Mean_Concentration_AirPollutant_Ozone": StatisticalVariable(
        dcid="Mean_Concentration_AirPollutant_Ozone",
        name="Ozone Concentration",
        description="Mean concentration of ground-level ozone",
        category=DataCommonsCategory.AIR_QUALITY,
        unit="ppb"
    ),
    "AirQualityIndex_AirPollutant": StatisticalVariable(
        dcid="AirQualityIndex_AirPollutant",
        name="Air Quality Index",
        description="EPA Air Quality Index value",
        category=DataCommonsCategory.AIR_QUALITY,
        unit="AQI"
    ),
    
    # Emissions
    "Annual_Emissions_CarbonDioxide": StatisticalVariable(
        dcid="Annual_Emissions_CarbonDioxide",
        name="CO2 Emissions",
        description="Annual carbon dioxide emissions",
        category=DataCommonsCategory.ENVIRONMENT,
        unit="metric tons"
    ),
    "Annual_Emissions_GreenhouseGas": StatisticalVariable(
        dcid="Annual_Emissions_GreenhouseGas",
        name="Greenhouse Gas Emissions",
        description="Total annual greenhouse gas emissions",
        category=DataCommonsCategory.ENVIRONMENT,
        unit="metric tons CO2e"
    ),
    
    # Demographics (useful for per-capita calculations)
    "Count_Person": StatisticalVariable(
        dcid="Count_Person",
        name="Population",
        description="Total population count",
        category=DataCommonsCategory.DEMOGRAPHICS,
        unit="persons"
    ),
    "Count_Household": StatisticalVariable(
        dcid="Count_Household",
        name="Household Count",
        description="Number of households",
        category=DataCommonsCategory.DEMOGRAPHICS,
        unit="households"
    ),
    
    # Water
    "Mean_WaterTemperature": StatisticalVariable(
        dcid="Mean_WaterTemperature",
        name="Water Temperature",
        description="Mean water temperature",
        category=DataCommonsCategory.ENVIRONMENT,
        unit="Celsius"
    ),
    
    # Energy
    "Amount_Consumption_Energy_Electricity": StatisticalVariable(
        dcid="Amount_Consumption_Energy_Electricity",
        name="Electricity Consumption",
        description="Total electricity consumption",
        category=DataCommonsCategory.ENERGY,
        unit="kWh"
    ),
    "Amount_Production_Energy_Renewable": StatisticalVariable(
        dcid="Amount_Production_Energy_Renewable",
        name="Renewable Energy Production",
        description="Energy produced from renewable sources",
        category=DataCommonsCategory.ENERGY,
        unit="kWh"
    ),
}


class DataCommonsClient:
    """
    Async client for Google Data Commons REST API V2.
    
    Features:
    - Statistical observations (time series data)
    - Node properties (entity information)
    - Entity resolution (find DCIDs)
    - In-memory caching for frequent queries
    
    Example usage:
        client = DataCommonsClient(api_key="YOUR_KEY")
        
        # Get temperature data for California
        data = await client.get_observations(
            entity="geoId/06",
            variable="Mean_Temperature",
            date="2020"
        )
    """
    
    BASE_URL = "https://api.datacommons.org/v2"
    TRIAL_API_KEY = "AIzaSyCTI4Xz-UW_G2Q2RfknhcfdAnTHq5X5XuI"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        cache_ttl: int = 3600
    ):
        """
        Initialize Data Commons client.
        
        Args:
            api_key: Data Commons API key. Uses trial key if not provided.
            timeout: Request timeout in seconds.
            cache_ttl: Cache time-to-live in seconds.
        """
        self.api_key = api_key or self.TRIAL_API_KEY
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._http_client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"X-API-Key": self.api_key}
            )
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            ts = self._cache_timestamps.get(key)
            if ts and (datetime.now() - ts).total_seconds() < self.cache_ttl:
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._cache_timestamps[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache."""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an API request."""
        client = await self._get_client()
        url = f"{self.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        params["key"] = self.api_key
        
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params)
            else:
                response = await client.post(url, params=params, json=data)
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Data Commons API error: {e.response.status_code} - {e.response.text}")
            raise DataCommonsError(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Data Commons request failed: {e}")
            raise DataCommonsError(f"Request failed: {e}")
    
    # ========================================================================
    # Observation API - Get statistical data
    # ========================================================================
    
    async def get_observations(
        self,
        entity: Union[str, List[str]],
        variable: Union[str, List[str]],
        date: Optional[str] = None,
        all_dates: bool = False
    ) -> Dict[str, Any]:
        """
        Get statistical observations for entities and variables.
        
        Args:
            entity: DCID of place(s) (e.g., "geoId/06" for California)
            variable: Statistical variable DCID(s)
            date: Specific date (ISO 8601: "YYYY", "YYYY-MM", "YYYY-MM-DD")
            all_dates: If True, get all available dates
        
        Returns:
            Dictionary with observations data
            
        Example:
            # Get California's 2020 population
            data = await client.get_observations(
                entity="geoId/06",
                variable="Count_Person",
                date="2020"
            )
        """
        # Build cache key
        entities = [entity] if isinstance(entity, str) else entity
        variables = [variable] if isinstance(variable, str) else variable
        cache_key = f"obs:{','.join(sorted(entities))}:{','.join(sorted(variables))}:{date}:{all_dates}"
        
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Build request
        params = {}
        if date:
            params["date"] = date
        
        data = {
            "nodes": entities,
            "select": ["entity", "variable", "value", "date"],
            "variable": {"dcids": variables}
        }
        
        if all_dates:
            data["select"].append("facets")
        
        result = await self._request("POST", "/observation", params=params, data=data)
        self._set_cache(cache_key, result)
        return result
    
    async def get_time_series(
        self,
        entity: str,
        variable: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get time series data for an entity and variable.
        
        Args:
            entity: Place DCID
            variable: Statistical variable DCID
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            List of {date, value} dictionaries
        """
        result = await self.get_observations(
            entity=entity,
            variable=variable,
            all_dates=True
        )
        
        # Parse response into time series format
        time_series = []
        
        if "byVariable" in result:
            var_data = result["byVariable"].get(variable, {})
            if "byEntity" in var_data:
                entity_data = var_data["byEntity"].get(entity, {})
                if "orderedFacets" in entity_data:
                    for facet in entity_data["orderedFacets"]:
                        if "observations" in facet:
                            for obs in facet["observations"]:
                                obs_date = obs.get("date", "")
                                value = obs.get("value")
                                
                                # Apply date filters
                                if start_date and obs_date < start_date:
                                    continue
                                if end_date and obs_date > end_date:
                                    continue
                                
                                time_series.append({
                                    "date": obs_date,
                                    "value": value
                                })
        
        # Sort by date
        time_series.sort(key=lambda x: x["date"])
        return time_series
    
    # ========================================================================
    # Node API - Get entity information
    # ========================================================================
    
    async def get_node_properties(
        self,
        node: Union[str, List[str]],
        properties: List[str]
    ) -> Dict[str, Any]:
        """
        Get properties of node(s) in the knowledge graph.
        
        Args:
            node: DCID(s) of node(s)
            properties: List of property names to fetch
        
        Returns:
            Dictionary with node properties
        """
        nodes = [node] if isinstance(node, str) else node
        prop_expr = "->[" + ",".join(properties) + "]"
        
        data = {
            "nodes": nodes,
            "property": prop_expr
        }
        
        return await self._request("POST", "/node", data=data)
    
    async def get_place_info(self, place_dcid: str) -> Dict[str, Any]:
        """
        Get information about a place.
        
        Args:
            place_dcid: Place DCID (e.g., "geoId/06" for California)
        
        Returns:
            Dictionary with place name, type, contained places, etc.
        """
        result = await self.get_node_properties(
            node=place_dcid,
            properties=["name", "typeOf", "containedInPlace", "latitude", "longitude"]
        )
        
        # Parse response
        place_info: Dict[str, Any] = {"dcid": place_dcid}
        
        if "data" in result and place_dcid in result["data"]:
            node_data = result["data"][place_dcid]
            if "arcs" in node_data:
                arcs = node_data["arcs"]
                
                if "name" in arcs:
                    place_info["name"] = arcs["name"]["nodes"][0].get("value")
                if "typeOf" in arcs:
                    place_info["type"] = arcs["typeOf"]["nodes"][0].get("dcid")
                if "latitude" in arcs:
                    place_info["latitude"] = float(arcs["latitude"]["nodes"][0].get("value"))
                if "longitude" in arcs:
                    place_info["longitude"] = float(arcs["longitude"]["nodes"][0].get("value"))
        
        return place_info
    
    async def get_contained_places(
        self,
        place_dcid: str,
        place_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get places contained within a place.
        
        Args:
            place_dcid: Parent place DCID
            place_type: Optional filter by place type (e.g., "County", "City")
        
        Returns:
            List of {dcid, name} dictionaries
        """
        prop_expr = "<-containedInPlace"
        if place_type:
            prop_expr += f"+{{typeOf:{place_type}}}"
        
        data = {
            "nodes": [place_dcid],
            "property": prop_expr
        }
        
        result = await self._request("POST", "/node", data=data)
        
        places = []
        if "data" in result and place_dcid in result["data"]:
            node_data = result["data"][place_dcid]
            if "arcs" in node_data:
                arcs = node_data["arcs"]
                if "containedInPlace" in arcs:
                    for node in arcs["containedInPlace"]["nodes"]:
                        places.append({
                            "dcid": node.get("dcid"),
                            "name": node.get("name")
                        })
        
        return places
    
    # ========================================================================
    # Resolve API - Find DCIDs
    # ========================================================================
    
    async def resolve_place_by_name(self, name: str) -> List[Dict[str, str]]:
        """
        Resolve a place name to its DCID(s).
        
        Args:
            name: Place name (e.g., "California", "San Francisco")
        
        Returns:
            List of matching {dcid, name, type} dictionaries
        """
        data = {
            "nodes": [name],
            "property": "<-description"
        }
        
        result = await self._request("POST", "/resolve", data=data)
        
        candidates = []
        if "entities" in result:
            for entity in result["entities"]:
                if entity.get("node") == name and "candidates" in entity:
                    for candidate in entity["candidates"]:
                        candidates.append({
                            "dcid": candidate.get("dcid"),
                            "type": candidate.get("dominantType")
                        })
        
        return candidates
    
    async def resolve_coordinates(
        self,
        lat: float,
        lon: float,
        place_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Resolve coordinates to place DCID(s).
        
        Args:
            lat: Latitude
            lon: Longitude
            place_type: Optional filter by place type
        
        Returns:
            List of matching {dcid, type} dictionaries
        """
        coord_str = f"{lat}#{lon}"
        
        prop_expr = "<-geoCoordinate"
        if place_type:
            prop_expr += f"{{typeOf:{place_type}}}"
        
        data = {
            "nodes": [coord_str],
            "property": prop_expr
        }
        
        result = await self._request("POST", "/resolve", data=data)
        
        candidates = []
        if "entities" in result:
            for entity in result["entities"]:
                if "candidates" in entity:
                    for candidate in entity["candidates"]:
                        candidates.append({
                            "dcid": candidate.get("dcid"),
                            "type": candidate.get("dominantType")
                        })
        
        return candidates
    
    # ========================================================================
    # Convenience methods for environmental data
    # ========================================================================
    
    async def get_climate_data(
        self,
        place_dcid: str,
        year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get climate data (temperature, precipitation) for a place.
        
        Args:
            place_dcid: Place DCID
            year: Optional year filter
        
        Returns:
            Dictionary with temperature and precipitation data
        """
        variables = [
            "Mean_Temperature",
            "Max_Temperature", 
            "Min_Temperature",
            "AnnualPrecipitation"
        ]
        
        result = await self.get_observations(
            entity=place_dcid,
            variable=variables,
            date=year,
            all_dates=year is None
        )
        
        return result
    
    async def get_air_quality_stats(
        self,
        place_dcid: str,
        year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get air quality statistics for a place.
        
        Args:
            place_dcid: Place DCID
            year: Optional year filter
        
        Returns:
            Dictionary with PM2.5, ozone, and AQI data
        """
        variables = [
            "Mean_Concentration_AirPollutant_PM2.5",
            "Mean_Concentration_AirPollutant_Ozone",
            "AirQualityIndex_AirPollutant"
        ]
        
        result = await self.get_observations(
            entity=place_dcid,
            variable=variables,
            date=year,
            all_dates=year is None
        )
        
        return result
    
    async def get_emissions_data(
        self,
        place_dcid: str,
        year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get emissions data for a place.
        
        Args:
            place_dcid: Place DCID
            year: Optional year filter
        
        Returns:
            Dictionary with CO2 and greenhouse gas emissions
        """
        variables = [
            "Annual_Emissions_CarbonDioxide",
            "Annual_Emissions_GreenhouseGas"
        ]
        
        result = await self.get_observations(
            entity=place_dcid,
            variable=variables,
            date=year,
            all_dates=year is None
        )
        
        return result
    
    async def get_population(
        self,
        place_dcid: str,
        year: Optional[str] = None
    ) -> Optional[int]:
        """
        Get population for a place.
        
        Args:
            place_dcid: Place DCID
            year: Optional year filter
        
        Returns:
            Population count or None if not available
        """
        result = await self.get_observations(
            entity=place_dcid,
            variable="Count_Person",
            date=year
        )
        
        # Parse single value from response
        if "byVariable" in result:
            var_data = result["byVariable"].get("Count_Person", {})
            if "byEntity" in var_data:
                entity_data = var_data["byEntity"].get(place_dcid, {})
                if "orderedFacets" in entity_data:
                    for facet in entity_data["orderedFacets"]:
                        if "observations" in facet and facet["observations"]:
                            return facet["observations"][0].get("value")
        
        return None
    
    def get_available_variables(
        self,
        category: Optional[DataCommonsCategory] = None
    ) -> List[StatisticalVariable]:
        """
        Get list of available statistical variables.
        
        Args:
            category: Optional filter by category
        
        Returns:
            List of StatisticalVariable objects
        """
        variables = list(ENVIRONMENTAL_VARIABLES.values())
        
        if category:
            variables = [v for v in variables if v.category == category]
        
        return variables


# Singleton instance
_dc_client: Optional[DataCommonsClient] = None


def get_data_commons_client(api_key: Optional[str] = None) -> DataCommonsClient:
    """Get or create Data Commons client singleton."""
    global _dc_client
    if _dc_client is None:
        _dc_client = DataCommonsClient(api_key=api_key)
    return _dc_client
