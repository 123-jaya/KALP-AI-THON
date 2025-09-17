from flask import Flask, request, jsonify, render_template_string
import numpy as np
from sklearn.linear_model import LinearRegression
import random

app = Flask(__name__)

appliances_data = []
monthly_bills = []

NAVBAR = """
<header>
<h1>Dynamic Energy Optimizer</h1>
<nav>
<button onclick="location.href='/'">Home</button>
<button onclick="location.href='/schedule'">Schedule</button>
<button onclick="location.href='/bills'">Bills & Savings</button>
</nav>
</header>
"""

# ------------------- HOME PAGE -------------------
HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Dynamic Energy Optimizer</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
/* ... your existing CSS ... */
</style>
</head>
<body>
""" + NAVBAR + """
<!-- ... your existing HTML ... -->
</body>
</html>
"""

# ------------------- SCHEDULE PAGE -------------------
SCHEDULE_PAGE = """<!-- ... your existing SCHEDULE_PAGE HTML ... -->"""

# ------------------- BILLS PAGE -------------------
BILLS_PAGE = """<!-- ... your existing BILLS_PAGE HTML ... -->"""

# ------------------- AI Integration -------------------
def predict_peak_hour(appliances):
    """
    Predict peak energy hour using Linear Regression.
    Input: appliances list of dicts with 'time' and 'energy'
    Output: predicted peak hour (0-23)
    """
    if len(appliances) < 2:  # not enough data
        return 12
    X = np.array([int(a['time'].split(':')[0]) for a in appliances]).reshape(-1, 1)
    y = np.array([a['energy'] for a in appliances])
    model = LinearRegression().fit(X, y)
    
    # Predict energy for each hour of the day
    hours = np.arange(24).reshape(-1, 1)
    predicted = model.predict(hours)
    peak_hour = int(np.argmax(predicted))
    return peak_hour

# ------------------- ROUTES -------------------

@app.route("/")
def home():
    return render_template_string(HOME_PAGE)

@app.route("/add_appliance", methods=['POST'])
def add_appliance():
    data = request.json
    data['energy'] = data['hours'] * data['power'] / 1000
    appliances_data.append(data)

    # AI-predicted peak hour
    predicted_peak = predict_peak_hour(appliances_data)

    # Suggestions based on AI
    hour = int(data['time'].split(":")[0])
    suggestions = []
    if data['power'] > 2000 and hour != predicted_peak:
        suggestions.append("High energy appliance! Prefer off-peak.")
    if data['name'].lower() in ["ac", "air conditioner", "heater"] and hour != predicted_peak:
        suggestions.append("Avoid peak hours for AC/Heater.")
    suggestion_msg = " | ".join(suggestions) if suggestions else "Appliance added."
    suggested_off_peak = f"{(predicted_peak + 1) % 24}:00 - {(predicted_peak + 7) % 24}:00"

    # Last 5 entries per appliance
    last5 = {}
    for a in appliances_data:
        if a['name'] not in last5: last5[a['name']] = []
        last5[a['name']].append(a)
    for k in last5: last5[k] = last5[k][-5:]

    total_energy = sum([d['energy'] for d in appliances_data])

    return jsonify({
        "appliances": appliances_data,
        "last5": last5,
        "suggestion": suggestion_msg,
        "total_energy": total_energy,
        "predicted_peak": predicted_peak,
        "suggestion_text": suggested_off_peak
    })

@app.route("/schedule")
def schedule_page():
    schedule = {}
    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    for appliance in set([a['name'] for a in appliances_data]):
        row = []
        for day in days:
            entries = [a for a in appliances_data if a['name']==appliance and a['day'][:3]==day]
            if entries: start_hour=int(entries[-1]['time'].split(":")[0])
            else: start_hour=random.randint(6,22)
            row.append(f"{start_hour}:00")
        schedule[appliance]=row
    return render_template_string(SCHEDULE_PAGE, schedule=schedule)

@app.route("/bills")
def bills_page():
    if len(monthly_bills) < 1: monthly_bills.append(random.randint(80,150))
    bills = [monthly_bills[0]] + [monthly_bills[0]+random.randint(-20,20) for _ in range(11)]
    months = [f"Month {i+1}" for i in range(12)]
    return render_template_string(BILLS_PAGE, months=months, bills=bills)

@app.route("/get_suggestions")
def get_suggestions():
    tips=[
        "Use appliances during off-peak hours.",
        "Turn off devices when not in use.",
        "Avoid high-power appliances during peak hours.",
        "Use LED lighting instead of incandescent bulbs.",
        "Maintain AC/Heater filters for efficiency."
    ]
    return jsonify(tips)

if __name__=="__main__":
    app.run(debug=True)
