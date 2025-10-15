from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass
class Preference:
    city: Optional[str] = None
    budget: Optional[float] = None  # expected price per night


def _score_hotel(hotel, pref: Preference) -> float:
    score = 0.0

    # Availability boosts
    if getattr(hotel, "is_available", False):
        score += 1.0

    # Rating (0..5 approx). Normalize to 0..1 and weight
    rating = getattr(hotel, "rating", None)
    if rating is not None:
        try:
            score += min(float(rating) / 5.0, 1.0) * 1.5
        except Exception:
            pass

    # City match
    if pref.city and getattr(hotel, "city", None):
        if hotel.city.strip().lower() == pref.city.strip().lower():
            score += 1.2

    # Budget proximity: closer price gets higher score
    if pref.budget is not None:
        try:
            price = float(getattr(hotel, "price_per_night"))
            diff = abs(price - float(pref.budget))
            # Map diff to 0..1 with soft decay
            proximity = max(0.0, 1.0 - (diff / max(1.0, pref.budget)))
            score += proximity * 1.3
        except Exception:
            pass

    return score


def recommend_hotels(hotels: Iterable, city: Optional[str] = None, budget: Optional[float] = None, top_k: int = 6):
    pref = Preference(city=city, budget=budget)
    scored = [(h, _score_hotel(h, pref)) for h in hotels]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [h for h, s in scored[:top_k] if s > 0]


