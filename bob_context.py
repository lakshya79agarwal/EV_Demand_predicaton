import json
from forecast_utils import forecast_ev


def create_bob_context(county, horizon=36):
    """
    Generate structured forecast context for IBM BOB.
    """

    forecast_df = forecast_ev(
        county=county,
        horizon=horizon
    )

    # Load the latest historical value
    import pandas as pd

    historical_df = pd.read_csv("preprocessed_ev_data.csv")
    historical_df["Date"] = pd.to_datetime(
        historical_df["Date"]
    )

    county_history = (
        historical_df[
            historical_df["County"] == county
        ]
        .sort_values("Date")
    )

    if county_history.empty:
        raise ValueError(
            f"County '{county}' was not found."
        )

    latest_ev = float(
        county_history[
            "Electric Vehicle (EV) Total"
        ].iloc[-1]
    )

    ending_ev = float(
        forecast_df[
            "Predicted EV Total"
        ].iloc[-1]
    )

    if latest_ev != 0:
        growth_percent = (
            (ending_ev - latest_ev)
            / latest_ev
        ) * 100
    else:
        growth_percent = 0

    if ending_ev > latest_ev:
        trend = "increasing"
    elif ending_ev < latest_ev:
        trend = "decreasing"
    else:
        trend = "stable"

    monthly_forecast = []

    for _, row in forecast_df.iterrows():
        monthly_forecast.append(
            {
                "month": row["Date"].strftime(
                    "%Y-%m-%d"
                ),
                "predicted_ev_total": round(
                    float(
                        row["Predicted EV Total"]
                    ),
                    2
                )
            }
        )

    context = {
        "project": (
            "AI-Based EV Adoption Forecasting "
            "for Sustainable Transportation Planning"
        ),
        "county": county,
        "forecast_horizon_months": horizon,

        "historical": {
            "latest_ev_total": round(
                latest_ev,
                2
            )
        },

        "forecast": {
            "ending_ev_total": round(
                ending_ev,
                2
            ),
            "growth_percent": round(
                growth_percent,
                2
            ),
            "trend": trend
        },

        "monthly_forecast": monthly_forecast,

        "model": {
            "algorithm": (
                "Random Forest Regression"
            ),
            "purpose": (
                "EV adoption forecasting"
            )
        }
    }

    return context


if __name__ == "__main__":

    context = create_bob_context(
        county="Fairfax",
        horizon=36
    )

    with open(
        "bob_context.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            context,
            file,
            indent=2
        )

    print(
        "BOB context created successfully:"
    )

    print(
        "bob_context.json"
    )