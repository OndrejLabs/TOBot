# Standard library imports
from datetime import date, datetime
from functools import lru_cache
import requests
import warnings

@lru_cache(maxsize=None)
def get_fx_rate(target_date, currency):
    """
    Fetches the exchange rate for a specific currency against EUR on a given date.

    Args:
        target_date (str, date, datetime): The date to query (format: 'YYYY-MM-DD').
        currency (str): The 3-letter currency code (e.g., 'USD', 'GBP').

    Returns:
        float: The exchange rate value.
        None: If an error occurs (invalid input, API error, or network failure).
    """

    # 1. Input Validation and Formatting
    if currency == "EUR":
        return 1.0  # EUR is the base currency, so its rate against itself is always 1.0
    elif isinstance(target_date, (date, datetime)):
        date_str = target_date.strftime("%Y-%m-%d")
    elif isinstance(target_date, str):
        try:
            # Validate string format
            datetime.strptime(target_date, "%Y-%m-%d")
            date_str = target_date
        except ValueError:
            warnings.warn(f"Invalid date format: '{target_date}'. Expected 'YYYY-MM-DD'.")
            return None
    else:
        warnings.warn("Date must be a string ('YYYY-MM-DD') or a datetime object.")
        return None

    currency = str(currency).upper()

    # 2. Build the API Request (Frankfurter uses EUR as the default base)
    url = f"https://api.frankfurter.app/{date_str}?to={currency}"

    # 3. Execute and Handle Errors
    try:
        response = requests.get(url, timeout=10)

        # Will raise an HTTPError for 4xx or 5xx status codes
        response.raise_for_status()

        data = response.json()

        # 4. Extract the value
        rates = data.get("rates", {})
        if currency not in rates:
            warnings.warn(f"Currency '{currency}' not found for date {date_str}.")
            return None

        return rates[currency]

    except requests.exceptions.HTTPError as http_err:
        # Frankfurter usually returns a helpful JSON message for errors (e.g., 404, 400)
        err_response = http_err.response

        if err_response is not None:
            try:
                # Attempt to get the Frankfurter-specific error message
                error_msg = err_response.json().get('message', str(http_err))
            except ValueError:
                error_msg = str(http_err)
        else:
            error_msg = str(http_err)

        warnings.warn(f"API Error: {error_msg}")
        return None

    except requests.exceptions.Timeout:
        warnings.warn("Network Error: The API request timed out.")
        return None

    except requests.exceptions.RequestException as req_err:
        warnings.warn(f"Network Error: {req_err}")
        return None

    except ValueError as val_err:
        warnings.warn(f"Data Processing Error: Failed to parse JSON response. {val_err}")
        return None


# ==========================================
# Examples of usage and error handling
# ==========================================
if __name__ == "__main__":

    # 1. Successful Query (String date)
    rate_usd = get_fx_rate("2023-01-15", "USD")
    print(f"Standard Query (USD): {rate_usd}")

    # 2. Successful Query (Datetime object)
    today = datetime.today().date()
    rate_gbp = get_fx_rate(today, "GBP")
    print(f"Today's Query (GBP): {rate_gbp}")

    print("-" * 30)

    # 3. Error Handling: Invalid Date Format
    print("Testing Invalid Date Format:")
    bad_date_rate = get_fx_rate("15-01-2023", "USD")
    print(f"Result: {bad_date_rate}\n")

    # 4. Error Handling: Invalid Currency
    print("Testing Invalid Currency:")
    bad_currency_rate = get_fx_rate("2023-01-15", "XYZ")
    print(f"Result: {bad_currency_rate}\n")

    # 5. Error Handling: Future Date (API Error)
    print("Testing Future Date:")
    future_date = "2099-01-01"
    future_rate = get_fx_rate(future_date, "USD")
    print(f"Result: {future_rate}\n")