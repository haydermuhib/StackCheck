"""
Exchange rate manager and currency normalization engine for StackCheck.
Handles offline-first caching, daily live rate synchronization, country-based inference,
and user-customizable conversion rates to USD.
"""

import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from stackcheck.config import DEFAULT_DATA_DIR

logger = logging.getLogger("stackcheck.currency")

# Local cache file location
EXCHANGE_RATES_FILE = DEFAULT_DATA_DIR / "exchange_rates.json"

# Fallback exchange rates to USD (1 Foreign Currency = X USD)
# Updated to recent global market baseline
DEFAULT_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.30,
    "CAD": 0.73,
    "AUD": 0.65,
    "INR": 0.0119,       # ~84 INR = 1 USD
    "PHP": 0.0175,       # ~57 PHP = 1 USD
    "CRC": 0.00195,      # ~515 CRC = 1 USD (Costa Rican Colón)
    "PKR": 0.0036,       # ~278 PKR = 1 USD
    "JPY": 0.0066,       # ~152 JPY = 1 USD
    "BRL": 0.175,        # ~5.7 BRL = 1 USD
    "MXN": 0.051,        # ~19.6 MXN = 1 USD
    "PLN": 0.25,         # ~4.0 PLN = 1 USD
    "SGD": 0.75,         # ~1.33 SGD = 1 USD
    "NZD": 0.60,         # ~1.66 NZD = 1 USD
    "CHF": 1.13,         # ~0.88 CHF = 1 USD
    "SEK": 0.094,
    "NOK": 0.092,
    "DKK": 0.145,
    "ZAR": 0.056,
    "ILS": 0.27,
    "AED": 0.272,
    "SAR": 0.266,
    "CNY": 0.14,
    "VND": 0.000039,     # ~25,500 VND = 1 USD
    "IDR": 0.000063,     # ~15,800 IDR = 1 USD
    "COP": 0.00023,      # ~4,400 COP = 1 USD (Colombian Peso)
    "CLP": 0.00105,      # ~950 CLP = 1 USD (Chilean Peso)
    "ARS": 0.0010,       # Argentine Peso
    "NGN": 0.0006,       # Nigerian Naira
    "TRY": 0.029,        # Turkish Lira
}

# Country name substrings to expected local currency code
COUNTRY_CURRENCY_MAP: Dict[str, str] = {
    "india": "INR",
    "philippines": "PHP",
    "costa rica": "CRC",
    "pakistan": "PKR",
    "japan": "JPY",
    "brazil": "BRL",
    "mexico": "MXN",
    "colombia": "COP",
    "chile": "CLP",
    "argentina": "ARS",
    "vietnam": "VND",
    "indonesia": "IDR",
    "nigeria": "NGN",
    "turkey": "TRY",
    "united kingdom": "GBP",
    "uk": "GBP",
    "canada": "CAD",
    "australia": "AUD",
    "new zealand": "NZD",
    "singapore": "SGD",
    "switzerland": "CHF",
    "germany": "EUR",
    "france": "EUR",
    "spain": "EUR",
    "italy": "EUR",
    "netherlands": "EUR",
    "poland": "PLN",
    "sweden": "SEK",
    "norway": "NOK",
}

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "PHP": "₱",
    "CAD": "CA$",
    "AUD": "A$",
    "JPY": "¥",
    "BRL": "R$",
    "PKR": "Rs ",
    "CRC": "₡",
    "MXN": "Mex$",
    "PLN": "zł",
    "SGD": "S$",
    "NZD": "NZ$",
    "CHF": "CHF ",
}


class CurrencyManager:
    """
    Manages exchange rates, persistence, daily automated sync,
    and conversions to USD.
    """

    def __init__(self, cache_file: Path = EXCHANGE_RATES_FILE):
        self.cache_file = cache_file
        self.rates: Dict[str, float] = dict(DEFAULT_RATES_TO_USD)
        self.last_updated: Optional[str] = None
        self.source: str = "built-in default"
        self._load_cache()

    def _load_cache(self) -> None:
        """Load rates from primary cache file, or fallback workspace location."""
        for target in [self.cache_file, Path.cwd() / ".stackcheck" / "exchange_rates.json"]:
            if target.exists():
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    cached_rates = data.get("rates_to_usd", {})
                    if isinstance(cached_rates, dict) and cached_rates:
                        self.rates.update({k.upper(): float(v) for k, v in cached_rates.items() if float(v) > 0})
                        self.last_updated = data.get("last_updated")
                        self.source = data.get("source", "cached file")
                        self.cache_file = target
                        return
                except Exception as e:
                    logger.warning(f"Could not load cached exchange rates from {target}: {e}")

    def save_cache(self, source: str = "user custom") -> None:
        """Persist current rates to disk with fallback to workspace directory if user home is restricted."""
        payload = {
            "rates_to_usd": self.rates,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "source": source
        }
        for target in [self.cache_file, Path.cwd() / ".stackcheck" / "exchange_rates.json"]:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                self.cache_file = target
                self.last_updated = payload["last_updated"]
                self.source = source
                return
            except (OSError, PermissionError):
                continue
            except Exception as e:
                logger.warning(f"Could not save exchange rates to {target}: {e}")

    def fetch_live_rates(self) -> bool:
        """
        Fetch latest market rates from the free keyless Open Exchange API.
        Returns True if successful, False otherwise.
        """
        api_url = "https://open.er-api.com/v6/latest/USD"
        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "StackCheck-CurrencyNormalizer/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    rates_from_usd = data.get("rates", {})
                    if rates_from_usd and isinstance(rates_from_usd, dict):
                        # Convert (1 USD = X Currency) -> (1 Currency = (1/X) USD)
                        new_rates: Dict[str, float] = {"USD": 1.0}
                        for code, rate_val in rates_from_usd.items():
                            try:
                                r_float = float(rate_val)
                                if r_float > 0:
                                    new_rates[code.upper()] = round(1.0 / r_float, 6)
                            except (ValueError, TypeError):
                                continue

                        self.rates.update(new_rates)
                        self.save_cache(source="Open Exchange Rates API (Live)")
                        return True
        except Exception as e:
            logger.warning(f"Live currency sync skipped or failed ({e}). Using cached/default rates.")

        return False

    def auto_sync_if_stale(self, max_age_days: int = 1) -> None:
        """Synchronize in the background if rates have not been updated in over max_age_days."""
        if not self.last_updated:
            self.fetch_live_rates()
            return

        try:
            last_dt = datetime.fromisoformat(self.last_updated.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            if now_dt - last_dt > timedelta(days=max_age_days):
                self.fetch_live_rates()
        except Exception:
            self.fetch_live_rates()

    def update_custom_rate(self, currency_code: str, rate_to_usd: float) -> None:
        """Update a specific currency's exchange rate."""
        code = currency_code.upper().strip()
        if code and rate_to_usd > 0:
            self.rates[code] = float(rate_to_usd)
            self.save_cache(source="User Custom Override")

    def reset_to_defaults(self) -> None:
        """Reset rates back to standard baseline."""
        self.rates = dict(DEFAULT_RATES_TO_USD)
        self.save_cache(source="Standard Built-in Defaults")

    def infer_currency(self, currency: Optional[str], country_or_loc: Optional[str], amount: float) -> str:
        """
        Infer the real currency code when a job has an ambiguous or missing currency.
        For example: a job in Costa Rica listing 36,000,000 or India listing 3,000,000.
        """
        curr = (currency or "USD").upper().strip()
        loc_str = (country_or_loc or "").lower().strip()

        # If already an explicit foreign currency, trust it
        if curr != "USD" and curr in self.rates:
            return curr

        # If labelled as USD, check if this is an obvious unnormalized local currency
        if loc_str:
            for country_key, detected_code in COUNTRY_CURRENCY_MAP.items():
                if country_key in loc_str:
                    # If amount is unusually large for USD (> 500,000) for countries with high-denomination currencies
                    if detected_code in ("CRC", "INR", "PHP", "PKR", "JPY", "COP", "CLP", "VND", "IDR", "KRW") and amount > 400000:
                        return detected_code
                    # If currency wasn't specified at all, bind to country's currency
                    if not currency or curr == "UNKNOWN":
                        return detected_code

        return curr

    def convert_to_usd(
        self,
        amount: float,
        currency: Optional[str] = "USD",
        country: Optional[str] = None,
        period: str = "yearly"
    ) -> float:
        """
        Convert any salary amount to annualized USD.
        """
        if not amount or amount <= 0:
            return 0.0

        p = (period or "yearly").lower().strip()
        annual_amt = amount
        if p == "hourly":
            annual_amt = amount * 2080
        elif p == "monthly":
            annual_amt = amount * 12

        # Detect real currency
        resolved_curr = self.infer_currency(currency, country, annual_amt)

        multiplier = self.rates.get(resolved_curr, 1.0)
        return annual_amt * multiplier


# Global singleton instance
currency_manager = CurrencyManager()
