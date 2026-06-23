"""Geo lookup + impossible-travel detection.

Uses ip-api.com (free, no key, 45 req/min) when reachable; otherwise a
small offline map for demo IPs. Impossible travel = same user seen from
two far-apart geos within a short window.
"""
import ipaddress
import math
from typing import Any

import requests

# Offline coordinates for demo IPs (lat, lon, country, city).
# All genuinely public addresses (TEST-NET doc ranges read as private).
_DEMO_GEO = {
    "159.89.113.10": (1.3521, 103.8198, "SG", "Singapore"),
    "185.220.101.66": (55.7558, 37.6173, "RU", "Moscow"),
    "185.220.101.45": (52.2297, 21.0122, "PL", "Warsaw"),
    "45.155.205.233": (50.0647, 19.9450, "PL", "Krakow"),
    "8.8.8.8": (37.4056, -122.0775, "US", "Mountain View"),
}


def _is_private(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return True


def _haversine_km(a: tuple, b: tuple) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def lookup(ip: str) -> dict[str, Any]:
    """Geolocate one IP. Never raises."""
    if not ip or _is_private(ip):
        return {"ip": ip, "source": "local", "country": "internal", "city": None,
                "lat": None, "lon": None}

    if ip in _DEMO_GEO:
        lat, lon, country, city = _DEMO_GEO[ip]
        return {"ip": ip, "source": "demo", "country": country, "city": city,
                "lat": lat, "lon": lon}

    try:
        resp = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,countryCode,city,lat,lon"},
            timeout=10,
        )
        resp.raise_for_status()
        d = resp.json()
        if d.get("status") == "success":
            return {"ip": ip, "source": "ip-api", "country": d.get("countryCode"),
                    "city": d.get("city"), "lat": d.get("lat"), "lon": d.get("lon")}
    except Exception:
        pass
    return {"ip": ip, "source": "none", "country": "unknown", "city": None,
            "lat": None, "lon": None}


def impossible_travel(ips: list[str]) -> dict[str, Any]:
    """Flag impossible travel across a set of source IPs for one user.

    Demo assumption: events are within a short window (~1h). Two geos
    >1000 km apart in that window are physically impossible to travel.
    """
    geos = [g for g in (lookup(ip) for ip in ips)
            if g.get("lat") is not None and g.get("lon") is not None]
    if len(geos) < 2:
        return {"impossible": False, "max_distance_km": 0, "locations": geos}

    max_km = 0.0
    pair = None
    for i in range(len(geos)):
        for j in range(i + 1, len(geos)):
            km = _haversine_km(
                (geos[i]["lat"], geos[i]["lon"]),
                (geos[j]["lat"], geos[j]["lon"]),
            )
            if km > max_km:
                max_km, pair = km, (geos[i], geos[j])

    return {
        "impossible": max_km > 1000,
        "max_distance_km": round(max_km, 1),
        "pair": pair,
        "locations": geos,
    }
