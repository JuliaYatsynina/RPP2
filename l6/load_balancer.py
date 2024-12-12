from flask import Flask, jsonify, request, redirect, url_for
import requests
import threading
import time

app = Flask(__name__)

# Список инстансов
instances = [
    {"ip": "127.0.0.1", "port": 5001, "active": True},
    {"ip": "127.0.0.1", "port": 5002, "active": True},
    {"ip": "127.0.0.1", "port": 5003, "active": True},
]
current_instance = 0


# Функция проверки доступности инстансов
def check_health():
    while True:
        for instance in instances:
            try:
                response = requests.get(f"http://{instance['ip']}:{instance['port']}/health", timeout=2)
                instance["active"] = response.status_code == 200
            except requests.RequestException:
                instance["active"] = False
        time.sleep(5)


# Эндпоинт для получения состояния всех инстансов
@app.route('/health', methods=['GET'])
def health():
    return jsonify(instances)


# Эндпоинт для обработки запросов (Round Robin)
@app.route('/process', methods=['GET'])
def process():
    global current_instance
    active_instances = [i for i in instances if i["active"]]
    if not active_instances:
        return jsonify({"error": "No active instances available"}), 503

    instance = active_instances[current_instance]
    current_instance = (current_instance + 1) % len(active_instances)
    try:
        response = requests.get(f"http://{instance['ip']}:{instance['port']}/process")
        return response.json(), response.status_code
    except requests.RequestException:
        return jsonify({"error": "Instance unreachable"}), 503


# Web UI для управления инстансами
@app.route('/', methods=['GET'])
def web_ui():
    html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Экземпляры</title>
        </head>
        <body>
            <h1>Экземпляры</h1>
            <form action='/add_instance' method='post'>
                IP: <input name='ip' required> Port: <input name='port' required>
                <button type='submit'>Добавить</button>
            </form><br>
            <table border='1'>
                <tr>
                    <th>IP</th>
                    <th>Port</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
                
        """
    for idx, instance in enumerate(instances):
        status = "Active" if instance["active"] else "Inactive"
        html += f"<tr><td>{instance['ip']}</td><td>{instance['port']}</td><td>{status}</td>"
        html += f"<td><form action='/remove_instance' method='post' style='display:inline;'>"
        html += f"<input type='hidden' name='index' value='{idx}'>"
        html += "<button type='submit'>Удалить</button></form></td></tr>"
    html += "</table>"
    return html


# Эндпоинт для добавления нового инстанса
@app.route('/add_instance', methods=['POST'])
def add_instance():
    ip = request.form['ip']
    port = int(request.form['port'])
    instances.append({"ip": ip, "port": port, "active": True})
    return redirect(url_for('web_ui'))


# Эндпоинт для удаления инстанса
@app.route('/remove_instance', methods=['POST'])
def remove_instance():
    index = int(request.form['index'])
    if 0 <= index < len(instances):
        del instances[index]
    return redirect(url_for('web_ui'))


# Запуск фоновой проверки состояния инстансов
if __name__ == '__main__':
    threading.Thread(target=check_health, daemon=True).start()
    app.run(port=5000)
