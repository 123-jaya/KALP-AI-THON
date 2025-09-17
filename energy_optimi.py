from flask import Flask, request, jsonify, render_template_string
import numpy as np
from datetime import datetime, timedelta
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
body{font-family:Arial,sans-serif;margin:0;background:#f5f6fa;color:#2f3640;}
header{background:#40739e;color:white;padding:15px 30px;display:flex;justify-content:space-between;align-items:center;}
header h1{margin:0;font-size:24px;}
nav button{margin-left:10px;padding:8px 15px;background:#353b48;color:white;border:none;border-radius:4px;cursor:pointer;}
nav button:hover{background:#2f3640;}
.container{padding:20px 40px;}
.card{background:#dcdde1;padding:10px;margin:10px 5px;border-radius:6px;display:inline-block;width:150px;text-align:center;}
.input-section,.chart-section,.history-section{background:#f1f2f6;padding:15px;border-radius:6px;margin-top:20px;}
input,button{padding:5px 8px;margin:5px;border-radius:4px;border:1px solid #dcdde1;}
button{background:#40739e;color:white;border:none;cursor:pointer;}
button:hover{background:#2f3640;}
table{border-collapse:collapse;width:100%;margin-top:10px;}
th,td{border:1px solid #dcdde1;padding:6px;text-align:center;}
canvas{margin-top:10px;max-height:150px;}
.suggestion-popup{background:#fbc531;padding:8px;border-radius:6px;margin-top:8px;display:none;}
.about{background:#f1f2f6;padding:12px;border-radius:6px;margin-top:20px;}
</style>
</head>
<body>
""" + NAVBAR + """
<div class="container">
<div class="about">
<h2>About Us</h2>
<p>Dynamic Energy Optimizer tracks and optimizes energy usage. Enter appliance data, visualize energy trends, get peak hour predictions, and receive suggestions.</p>
</div>
<div class="input-section">
<h2>Add Appliance</h2>
<input type="text" id="name" placeholder="Appliance Name">
<input type="number" id="hours" placeholder="Hours Used per Day">
<input type="number" id="power" placeholder="Power Rating (Watts)">
<input type="date" id="date">
<input type="text" id="day" placeholder="Day of Week">
<input type="time" id="time">
<button onclick="addAppliance()">Add</button>
<button onclick="showSuggestions()">Suggestions</button>
<div id="suggestion-popup" class="suggestion-popup"></div>
</div>
<div class="chart-section">
<h2>Energy Dashboard</h2>
<div class="card" id="totalEnergy">Total Energy: 0 kWh</div>
<div class="card" id="predictedPeak">Predicted Peak Hour: N/A</div>
<div class="card" id="suggestion">Suggested Off-Peak Usage: N/A</div>
</div>
<div class="chart-section" id="charts-area">
<h2>Appliance Comparison (Last 5 Entries)</h2>
</div>
<div class="history-section">
<h2>Appliance History</h2>
<table id="historyTable"><tr><th>Name</th><th>Hours</th><th>Power</th><th>Date</th><th>Day</th><th>Time</th></tr></table>
</div>
</div>

<script>
let chartMap={};

function addAppliance(){
const name=document.getElementById('name').value.trim();
const hours=parseFloat(document.getElementById('hours').value);
const power=parseFloat(document.getElementById('power').value);
const date=document.getElementById('date').value;
const day=document.getElementById('day').value;
const time=document.getElementById('time').value;

if(!name||isNaN(hours)||isNaN(power)||!date||!day||!time){alert("Fill all fields");return;}

fetch('/add_appliance',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({name,hours,power,date,day,time})
}).then(res=>res.json()).then(data=>{
document.getElementById('suggestion-popup').innerText=data.suggestion;
document.getElementById('suggestion-popup').style.display='block';
updateDashboard(data);
updateHistory(data.appliances);
updateCharts(data.last5);
});

document.getElementById('name').value='';
document.getElementById('hours').value='';
document.getElementById('power').value='';
document.getElementById('date').value='';
document.getElementById('day').value='';
document.getElementById('time').value='';
}

function showSuggestions(){
fetch('/get_suggestions').then(res=>res.json()).then(data=>{
alert(data.join('\\n'));
});
}

function updateDashboard(data){
document.getElementById('totalEnergy').innerText='Total Energy: '+data.total_energy.toFixed(2)+' kWh';
document.getElementById('predictedPeak').innerText='Predicted Peak Hour: '+data.predicted_peak;
document.getElementById('suggestion').innerText='Suggested Off-Peak Usage: '+data.suggestion;
}

function updateHistory(appliances){
const table=document.getElementById('historyTable');
table.innerHTML='<tr><th>Name</th><th>Hours</th><th>Power</th><th>Date</th><th>Day</th><th>Time</th></tr>';
appliances.forEach(a=>{
const row=table.insertRow();
row.insertCell(0).innerText=a.name;
row.insertCell(1).innerText=a.hours;
row.insertCell(2).innerText=a.power;
row.insertCell(3).innerText=a.date;
row.insertCell(4).innerText=a.day;
row.insertCell(5).innerText=a.time;
});
}

function updateCharts(last5){
const area=document.getElementById('charts-area');
area.innerHTML='<h2>Appliance Comparison (Last 5 Entries)</h2>';
for(let appliance in last5){
const canvas=document.createElement('canvas');
canvas.id='chart_'+appliance;
canvas.width=400; canvas.height=120;
area.appendChild(canvas);
const ctx=canvas.getContext('2d');
if(chartMap[appliance]) chartMap[appliance].destroy();
chartMap[appliance]=new Chart(ctx,{
type:'bar',
data:{
labels:last5[appliance].map(e=>e.date+' '+e.time),
datasets:[{label:appliance,data:last5[appliance].map(e=>e.energy),backgroundColor:'#40739e'}]
},
options:{responsive:true,maintainAspectRatio:false,height:80}
});
}
}
</script>
</body>
</html>
"""

# ------------------- SCHEDULE PAGE -------------------
SCHEDULE_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Weekly Schedule</title>
<style>
body{font-family:Arial,sans-serif;margin:20px;background:#f5f6fa;color:#2f3640;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #dcdde1;padding:8px;text-align:center;}
button{padding:8px 15px;margin-top:15px;border:none;border-radius:5px;background:#40739e;color:white;cursor:pointer;}
button:hover{background:#2f3640;}
</style>
</head>
<body>
""" + NAVBAR + """
<h1>Weekly Appliance Schedule (Start Hour Only)</h1>
<table>
<tr>
<th>Appliance</th>
<th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Sun</th>
</tr>
{% for appliance,row in schedule.items() %}
<tr>
<td>{{ appliance }}</td>
{% for hour in row %}
<td>{{ hour }}</td>
{% endfor %}
</tr>
{% endfor %}
</table>
<button onclick="location.href='/'">Back to Home</button>
</body>
</html>
"""

# ------------------- BILLS PAGE -------------------
BILLS_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Bills Comparison</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{font-family:Arial,sans-serif;margin:20px;background:#f5f6fa;color:#2f3640;}
canvas{max-width:400px; max-height:200px;}
button{padding:8px 15px;margin-top:15px;border:none;border-radius:5px;background:#40739e;color:white;cursor:pointer;}
button:hover{background:#2f3640;}
</style>
</head>
<body>
""" + NAVBAR + """
<h1>Bills Comparison</h1>
<canvas id="billsChart"></canvas>
<script>
const ctx=document.getElementById('billsChart').getContext('2d');
new Chart(ctx,{
type:'line',
data:{
labels:{{ months|safe }},
datasets:[
{label:'Bills ($)',data:{{ bills|safe }},borderColor:'#40739e',fill:false}
]
},
options:{responsive:true,maintainAspectRatio:false,height:120}
});
</script>
<button onclick="location.href='/'">Back to Home</button>
</body>
</html>
"""

# ------------------- ROUTES -------------------

@app.route("/")
def home():
    return render_template_string(HOME_PAGE)

@app.route("/add_appliance",methods=['POST'])
def add_appliance():
    data=request.json
    data['energy']=data['hours']*data['power']/1000
    appliances_data.append(data)

    # Suggestions
    hour=int(data['time'].split(":")[0])
    suggestions=[]
    if data['power']>2000 and not (0<=hour<5): suggestions.append("High energy appliance! Use off-peak.")
    if data['name'].lower() in ["ac","air conditioner","heater"] and not (0<=hour<5):
        suggestions.append("Avoid peak hours for AC/Heater.")
    suggestion_msg=" | ".join(suggestions) if suggestions else "Appliance added."

    # Last 5 entries per appliance
    last5={}
    for a in appliances_data:
        if a['name'] not in last5: last5[a['name']]=[]
        last5[a['name']].append(a)
    for k in last5: last5[k]=last5[k][-5:]

    total_energy=sum([d['energy'] for d in appliances_data])
    predicted_peak=12
    suggested_off_peak="10 PM - 6 AM"

    return jsonify({
        "appliances": appliances_data,
        "last5": last5,
        "suggestion":suggestion_msg,
        "total_energy":total_energy,
        "predicted_peak":predicted_peak,
        "suggestion":suggested_off_peak
    })

@app.route("/schedule")
def schedule_page():
    # Generate weekly schedule: start hour only
    schedule={}
    days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    for appliance in set([a['name'] for a in appliances_data]):
        row=[]
        for day in days:
            entries=[a for a in appliances_data if a['name']==appliance and a['day'][:3]==day]
            if entries: start_hour=int(entries[-1]['time'].split(":")[0])
            else: start_hour=random.randint(6,22)
            row.append(f"{start_hour}:00")
        schedule[appliance]=row
    return render_template_string(SCHEDULE_PAGE,schedule=schedule)

@app.route("/bills")
def bills_page():
    # Simulate 12 months
    if len(monthly_bills)<1: monthly_bills.append(random.randint(80,150))
    bills=[monthly_bills[0]]+[monthly_bills[0]+random.randint(-20,20) for _ in range(11)]
    months=[f"Month {i+1}" for i in range(12)]
    return render_template_string(BILLS_PAGE,months=months,bills=bills)

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


