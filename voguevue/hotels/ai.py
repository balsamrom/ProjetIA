from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class Preference:
    city: Optional[str] = None
    budget: Optional[float] = None


def _score_hotel(hotel, pref: Preference) -> float:
    score = 0.0
    if getattr(hotel, "is_available", False):
        score += 1.0
    rating = getattr(hotel, "rating", None)
    if rating is not None:
        try:
            score += min(float(rating) / 5.0, 1.0) * 1.5
        except Exception:
            pass
    if pref.city and getattr(hotel, "city", None):
        if hotel.city.strip().lower() == pref.city.strip().lower():
            score += 1.2
    if pref.budget is not None:
        try:
            price = float(getattr(hotel, "price_per_night"))
            diff = abs(price - float(pref.budget))
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


# Optional: Hugging Face pipeline for review sentiment (lazy import)
def analyze_sentiment(texts):
    try:
        from transformers import pipeline  # pyright: ignore[reportMissingImports]
        clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
        return clf(texts)
    except Exception:
        # Fallback: neutral results
        return [{"label": "NEUTRAL", "score": 0.0} for _ in texts]


def compute_eco_score(hotel) -> int:
    """Simple eco-score 0-100 using proxies (price, availability, rating).
    Lower price and higher rating with availability considered better.
    """
    score = 50
    try:
        price = float(getattr(hotel, 'price_per_night', 0) or 0)
        rating = float(getattr(hotel, 'rating', 0) or 0)
        avail = 10 if getattr(hotel, 'is_available', False) else 0
        # Normalize price effect: cheaper is considered eco-friendlier proxy here
        price_component = max(0, 30 - min(price, 300) / 10)  # 0..30
        rating_component = min(rating * 8, 40)  # up to 40
        score = int(min(max(price_component + rating_component + avail, 0), 100))
    except Exception:
        pass
    return score


