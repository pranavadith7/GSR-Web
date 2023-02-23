import datetime
from flask import Flask, render_template, url_for, request, jsonify
import pickle
import numpy as np
from flask_cors import CORS
import requests
import json
from urllib.request import urlopen, Request
from firebase_admin import db, credentials, firestore, initialize_app
# import urllib3
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
CORS(app)

gsr_model = pickle.load(open('gsr.pickle', 'rb'))
# test_data = np.array([[93, 41, 40, 20.87, 82.032, 6.5, 205.9]])
# prediction = crop_model.predict(test_data)
# print(prediction)

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred, {
    'databaseURL': 'https://gsrwithuv-default-rtdb.firebaseio.com/'
})
# db = firestore.client()
# gsr_ref = db.reference("/gsr")
gsr_coll = firestore.client().collection('gsr_data')

def getCityWeather(name):
    baseURL = "http://api.openweathermap.org/data/2.5/weather?"
    apiKey = "25ab0f2df8aee2f1e4def94d33a8900b"
    cityWeatherURL = baseURL + "appid=" + apiKey + "&q=" + name
    jsonResponse = requests.get(cityWeatherURL).json()
    if jsonResponse["cod"] != 200:
        return None
    else:
        cityData = jsonResponse["main"]
        temperature = round((cityData["temp"] - 273.15), 2)
        humidity = cityData["humidity"]
        return temperature, humidity


@app.route('/')
def index():
    # print(getCityWeather("Tiruppur"))
    return render_template('index.html')
    # return render_template('prediction_result.html', predicted_crop='orange')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    age = request.args.get('age') or 21
    name = request.args.get('name') or 'John Doe'
    gsrValue = request.args.get('gsrValue') or 270
    lat = request.args.get('lat') or "10.900"
    lng = request.args.get('lng') or "76.904"
    print(lat, lng)
    # Get gsr from arduino
    gsrValue, uv_max, uv = 0, 0, 0
    try:
        url = "http://192.168.77.201/getgsr"
        response = urlopen(url)
        data = response.read()
        dt = json.loads(data)
        print(dt)
        gsrValue = dt["gsrAvg"]
    except:
        gsrValue = 270

    # Get uv value
    try:
        req = Request(f"https://api.openuv.io/api/v1/uv?lat={lat}&lng={lng}", None, {'x-access-token' : '7044ee19687d7cffd25d10a64d540b50'})
        response = urlopen(req)
        dt = json.loads(response.read())
        # print(dt)
        uv_max = dt["result"]["uv_max"]
        uv = dt["result"]["uv"]
    except:
        uv_max = 8
        uv = 8
    print(uv, uv_max)


    data = np.array([[age, gsrValue]])
    predicted_status = gsr_model.predict(data)
    print(predicted_status)
    res = {
        "name": name,
        "age": age,
        "gsrValue": gsrValue,
        "status": predicted_status[0],
        "uv": uv,
        "uv_max": uv_max,
        "lat": lat,
        "lng": lng,
        "timestamp": datetime.datetime.now(),
    }
    print(res)
    # gsr_ref.push().set(res)
    gsr_coll.add(res)
    # return predicted_status[0]
    return jsonify(res)



# @app.route('/predict', methods=['GET', 'POST'])
# def predict():
#     if request.method == 'POST':
#         N = int(request.form['nitrogen'])
#         P = int(request.form['phosphorous'])
#         K = int(request.form['pottasium'])
#         ph = float(request.form['ph'])
#         rainfall = float(request.form['rainfall'])
#         city = request.form.get('city')
#         print(N, P, K, ph, rainfall, city)
#         try:
#             tempWeather = getCityWeather(city)
#             temperature = 28
#             humidity = 83
#             if tempWeather != None:
#                 temperature, humidity = tempWeather
#             data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
#             predicted_crop = crop_model.predict(data)
#             return render_template('prediction_result.html', predicted_crop=predicted_crop[0])
#         except:
#             print("Error")
#     return render_template('prediction_form.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
