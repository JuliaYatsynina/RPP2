from flask import Flask, request, jsonify, redirect
import requests
import threading
import time

app = Flask(__name__)

instances = []
active_instances = []
current_instance_index = 0


def check_instance_health():
    global active_instances
    while True:
        active_instances = []
        for instance in instances:
            try:
                response = requests.get(f"http://{instance['ip']}:{instance['port']}/health")
                if response.status_code == 200:
                    active_instances.append(instance)
            except requests.exceptions.RequestException:
                pass
        time.sleep(5)


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "active_instances": len(active_instances)})


@app.route('/process')
def process():
    global current_instance_index
    if not active_instances:
        return jsonify({"error": "No active instances"}), 503
    instance = active_instances[current_instance_index]
    current_instance_index = (current_instance_index + 1) % len(active_instances)
    response = requests.get(f"http://{instance['ip']}:{instance['port']}/process")
    return jsonify(response.json())


@app.route('/')
def home():
    return '''
    <h1>Балансер</h1>
    <h2>Активные экземпляры</h2>
    <ul>
    ''' + ''.join([f"<li>{instance['ip']}:{instance['port']}</li>" for instance in active_instances]) + '''
    </ul>
    <h2>Добавить экземпляры</h2>
    <form action="/add_instance" method="post">
        IP: <input type="text" name="ip"><br>
        Port: <input type="text" name="port"><br>
        <input type="submit" value="Add">
    </form>
    <h2>Удалить экземпляры</h2>
    <form action="/remove_instance" method="post">
        Index: <input type="text" name="instance_index"><br>
        <input type="submit" value="Remove">
    </form>
    '''


@app.route('/add_instance', methods=['POST'])
def add_instance():
    ip = request.form['ip']
    port = request.form['port']
    instances.append({"ip": ip, "port": port})
    return redirect('/')


@app.route('/remove_instance', methods=['POST'])
def remove_instance():
    instance_index = int(request.form['instance_index'])
    if 0 <= instance_index < len(instances):
        instances.pop(instance_index)
    return redirect('/')


@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    global current_instance_index
    if not active_instances:
        return jsonify({"error": "Нет активных экземпляров"}), 503
    instance = active_instances[current_instance_index]
    current_instance_index = (current_instance_index + 1) % len(active_instances)
    response = requests.get(f"http://{instance['ip']}:{instance['port']}/{path}")
    return jsonify(response.json())


if __name__ == '__main__':
    threading.Thread(target=check_instance_health).start()
    app.run(port=5000)
