from flask import Flask, render_template, request
from openai_utils import get_openai_response
from forecast_utils import generate_forecast_plot

app = Flask(__name__)

DATA_FILE = 'preprocessed_ev_data.csv'

@app.route('/', methods=['GET', 'POST'])
def index():
    openai_reply = None
    plot_json, forecast_summary = generate_forecast_plot(DATA_FILE)

    if request.method == 'POST':
        user_query = request.form.get('query')
        openai_reply = get_openai_response(user_query, forecast_summary)

    return render_template('index.html', openai_reply=openai_reply, plot_json=plot_json)

if __name__ == '__main__':
    app.run(debug=True)