from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
import json
import os

app = Flask(__name__)
redis = Redis(host='localhost', port=6379, db=0)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",  # Используем Redis в качестве хранилища
    default_limits=["100 per day"]
)

# Загрузка данных из файла
data_file = 'data.json'
if os.path.exists(data_file):
    with open(data_file, 'r') as file:
        data = json.load(file)
else:
    data = {}


# Сохранение данных в файл
def save_data():
    with open(data_file, 'w') as file:
        json.dump(data, file)


@app.route('/set', methods=['POST'])
@limiter.limit("10 per minute")
def set_key():
    key = request.json.get('key')
    value = request.json.get('value')
    if key is None or value is None:
        return jsonify({"error": "Key and value are required"}), 400
    data[key] = value
    save_data()
    return jsonify({"message": "Key-value pair saved"}), 200


@app.route('/get/<key>', methods=['GET'])
@limiter.limit("100 per day")
def get_key(key):
    value = data.get(key)
    if value is None:
        return jsonify({"error": "Key not found"}), 404
    return jsonify({"key": key, "value": value}), 200


@app.route('/delete/<key>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_key(key):
    if key in data:
        del data[key]
        save_data()
        return jsonify({"message": "Key deleted"}), 200
    return jsonify({"error": "Key not found"}), 404


@app.route('/exists/<key>', methods=['GET'])
@limiter.limit("100 per day")
def exists_key(key):
    exists = key in data
    return jsonify({"exists": exists}), 200


if __name__ == '__main__':
    app.run(debug=True)
