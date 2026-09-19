import pandas as pd
import numpy as np
import joblib


FEATURES = [
    "months_since_start",
    "county_encoded",
    "ev_total_lag1",
    "ev_total_lag2",
    "ev_total_lag3",
    "ev_total_roll_mean_3",
    "ev_total_pct_change_1",
    "ev_total_pct_change_3",
    "ev_growth_slope",
]


def forecast_ev(
    county,
    data_file="preprocessed_ev_data.csv",
    model_file="forecasting_ev_model.pkl",
    horizon=36,
):
    """
    Generate a recursive EV adoption forecast for one county.

    Parameters
    ----------
    county : str
        County to forecast.
    data_file : str
        Path to the preprocessed EV dataset.
    model_file : str
        Path to the trained Random Forest model.
    horizon : int
        Number of months to forecast.

    Returns
    -------
    pandas.DataFrame
        Forecast containing Date, County, Predicted EV Total and Source.
    """

    # Load data and model
    df = pd.read_csv(data_file)
    model = joblib.load(model_file)

    # Convert dates
    df["Date"] = pd.to_datetime(df["Date"])

    # Filter county
    county_df = (
        df[df["County"] == county]
        .sort_values("Date")
        .copy()
    )

    if county_df.empty:
        raise ValueError(f"County '{county}' was not found in the dataset.")

    if len(county_df) < 6:
        raise ValueError(
            f"County '{county}' does not have enough historical data "
            "for forecasting."
        )

    # Get county information
    county_code = int(county_df["county_encoded"].iloc[-1])
    months_since_start = int(
        county_df["months_since_start"].iloc[-1]
    )

    # Last six actual EV values
    historical_ev = list(
        county_df["Electric Vehicle (EV) Total"].values[-6:]
    )

    # Last six cumulative values
    cumulative_ev = list(
        county_df["cumulative_ev"].values[-6:]
    )

    # Last historical date
    last_date = county_df["Date"].iloc[-1]

    forecast_rows = []

    # Recursive forecasting
    for step in range(1, horizon + 1):

        months_since_start += 1

        lag1 = historical_ev[-1]
        lag2 = historical_ev[-2]
        lag3 = historical_ev[-3]

        # Rolling mean of previous three months
        roll_mean = np.mean(
            [lag1, lag2, lag3]
        )

        # Percentage changes
        pct_change_1 = (
            (lag1 - lag2) / lag2
            if lag2 != 0
            else 0
        )

        pct_change_3 = (
            (lag1 - lag3) / lag3
            if lag3 != 0
            else 0
        )

        # Growth slope
        recent_cumulative = cumulative_ev[-6:]

        if len(recent_cumulative) == 6:
            ev_growth_slope = np.polyfit(
                range(6),
                recent_cumulative,
                1
            )[0]
        else:
            ev_growth_slope = 0

        # Create model input
        new_row = {
            "months_since_start": months_since_start,
            "county_encoded": county_code,
            "ev_total_lag1": lag1,
            "ev_total_lag2": lag2,
            "ev_total_lag3": lag3,
            "ev_total_roll_mean_3": roll_mean,
            "ev_total_pct_change_1": pct_change_1,
            "ev_total_pct_change_3": pct_change_3,
            "ev_growth_slope": ev_growth_slope,
        }

        X_new = pd.DataFrame(
            [new_row]
        )[FEATURES]

        # Predict
        prediction = float(
            model.predict(X_new)[0]
        )

        # Proper month-end forecast date
        forecast_date = (
            last_date
            + pd.offsets.MonthEnd(step)
        )

        forecast_rows.append(
            {
                "Date": forecast_date,
                "County": county,
                "Predicted EV Total": prediction,
                "Source": "Forecast",
            }
        )

        # Add prediction to history
        historical_ev.append(prediction)

        if len(historical_ev) > 6:
            historical_ev.pop(0)

        # Update cumulative values
        cumulative_ev.append(
            cumulative_ev[-1] + prediction
        )

        if len(cumulative_ev) > 6:
            cumulative_ev.pop(0)

    return pd.DataFrame(forecast_rows)