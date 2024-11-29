from flask import Flask, request, jsonify, redirect
import requests
import threading  # Импорт модуля для работы с потоками
import time  # Импорт модуля для работы с временем

app = Flask(__name__)

instances = []  # Список для хранения всех экземпляров
active_instances = []  # Список для хранения активных экземпляров
current_instance_index = 0  # Индекс текущего активного экземпляра


# Функция для проверки состояния экземпляров
def check_instance_health():
    global active_instances  # Использование глобальной переменной
    while True:  # Бесконечный цикл
        active_instances = []
        for instance in instances:
            try:
                response = requests.get(f"http://{instance['ip']}:{instance['port']}/health")  # Запрос состояния
                if response.status_code == 200:
                    active_instances.append(instance)  # Добавление активного экземпляра
            except requests.exceptions.RequestException:  # Обработка исключений
                pass  # Пропуск исключений
        time.sleep(5)


# Эндпоинт для проверки состояния балансировщика
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "active_instances": len(active_instances)})  # Возврат состояния


# Эндпоинт для обработки запросов
@app.route('/process')
def process():
    global current_instance_index
    if not active_instances:
        return jsonify({"error": "Нет активных экземпляров"}), 503
    instance = active_instances[current_instance_index]  # Получение текущего активного экземпляра
    current_instance_index = (current_instance_index + 1) % len(active_instances)  # Обновление индекса
    response = requests.get(f"http://{instance['ip']}:{instance['port']}/process")  # Запрос к экземпляру
    return jsonify(response.json())


# Главная страница
@app.route('/')
def home():
    instance_rows = ''.join(
        [f"<tr><td>{index}</td><td>{instance['ip']}</td><td>{instance['port']}</td></tr>" for index, instance in
         enumerate(instances)])  # Генерация строк таблицы
    return f'''
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            h1, h2 {{
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            input[type="submit"] {{
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>Балансер</h1>
        <h2>Активные экземпляры</h2>
        <table>
            <tr>
                <th>Индекс</th>
                <th>IP</th>
                <th>Порт</th>
            </tr>
            {instance_rows}
        </table>
        <h2>Добавить экземпляры</h2>
        <form action="/add_instance" method="post">
            IP: <input type="text" name="ip"><br>
            Port: <input type="text" name="port"><br>
            <input type="submit" value="Добавить">
        </form>
        <h2>Удалить экземпляры</h2>
        <form action="/remove_instance" method="post">
            Index: <input type="text" name="instance_index"><br>
            <input type="submit" value="Удалить">
        </form>
    </body>
    </html>
    '''


# Эндпоинт для добавления нового экземпляра
@app.route('/add_instance', methods=['POST'])
def add_instance():
    ip = request.form['ip']  # Получение IP из формы
    port = request.form['port']  # Получение порта из формы
    instances.append({"ip": ip, "port": port})  # Добавление нового экземпляра
    return redirect('/')


# Эндпоинт для удаления экземпляра
@app.route('/remove_instance', methods=['POST'])
def remove_instance():
    instance_index = int(request.form['instance_index'])  # Получение индекса из формы
    if 0 <= instance_index < len(instances):  # Проверка корректности индекса
        instances.pop(instance_index)  # Удаление экземпляра
    return redirect('/')


# Эндпоинт для перехвата всех запросов
@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    global current_instance_index  # Использование глобальной переменной
    if not active_instances:
        return jsonify({"error": "Нет активных экземпляров"}), 503
    instance = active_instances[current_instance_index]  # Получение текущего активного экземпляра
    current_instance_index = (current_instance_index + 1) % len(active_instances)  # Обновление индекса
    response = requests.get(f"http://{instance['ip']}:{instance['port']}/{path}")  # Запрос к экземпляру
    return jsonify(response.json())


# Запуск балансировщика нагрузки
if __name__ == '__main__':
    threading.Thread(target=check_instance_health).start()  # Запуск потока для проверки состояния экземпляров
    app.run(port=5000)
