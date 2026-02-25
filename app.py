import os
import json
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "tasks.json"
tasks = []
next_id = 1

def load_tasks():
    global tasks, next_id
    try:
        with open(DATA_FILE, "r") as f:
            tasks = json.load(f)
            if tasks:
                next_id = max(task["id"] for task in tasks) + 1
            # Добавляем поле is_overdue для всех задач при загрузке
            update_overdue_status()
    except FileNotFoundError:
        tasks = []

def save_tasks():
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def update_overdue_status():
    """Обновляет статус просрочки для всех задач"""
    now = datetime.now()
    for task in tasks:
        if task.get("due_date") and not task.get("completed"):
            try:
                due_date = datetime.fromisoformat(task["due_date"])
                task["is_overdue"] = now > due_date
            except (ValueError, TypeError):
                task["is_overdue"] = False
        else:
            task["is_overdue"] = False

load_tasks()

# ----------------- REST API -----------------
@app.route("/tasks", methods=["GET"])
def get_tasks():
    # Обновляем статус просрочки перед отправкой
    update_overdue_status()
    return jsonify(tasks)

@app.route("/tasks", methods=["POST"])
def add_task():
    global next_id
    data = request.get_json()
    if not data or "title" not in data or not data["title"].strip():
        return jsonify({"error": "Title is required"}), 400
    
    # Создаем задачу с поддержкой сроков
    task = {
        "id": next_id,
        "title": data["title"].strip(),
        "completed": False,
        "created_at": datetime.now().isoformat(),
        "due_date": data.get("due_date"),  # Может быть None
        "description": data.get("description", ""),
        "is_overdue": False  # Будет обновлено при GET запросе
    }
    
    tasks.append(task)
    next_id += 1
    save_tasks()
    return jsonify(task), 201

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    for task in tasks:
        if task["id"] == task_id:
            # Обновляем только переданные поля
            if "completed" in data:
                task["completed"] = data["completed"]
            if "title" in data and data["title"].strip():
                task["title"] = data["title"].strip()
            if "due_date" in data:
                task["due_date"] = data["due_date"]
            if "description" in data:
                task["description"] = data["description"]
            
            save_tasks()
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

@app.route("/tasks/<int:task_id>/toggle", methods=["PUT"])
def toggle_task(task_id):
    """Отдельный эндпоинт для переключения статуса задачи"""
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]
            save_tasks()
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    global tasks
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        return jsonify({"error": "Task not found"}), 404
    tasks = new_tasks
    save_tasks()
    return jsonify({"message": "Deleted"})

# Дополнительный эндпоинт для получения статистики
@app.route("/tasks/stats", methods=["GET"])
def get_stats():
    """Возвращает статистику по задачам"""
    update_overdue_status()
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t["completed"])
    active = total - completed
    overdue = sum(1 for t in tasks if t.get("is_overdue") and not t["completed"])
    
    return jsonify({
        "total": total,
        "completed": completed,
        "active": active,
        "overdue": overdue
    })

# Эндпоинт для обновления конкретной задачи (частичное обновление)
@app.route("/tasks/<int:task_id>/due_date", methods=["PATCH"])
def update_due_date(task_id):
    """Обновляет только дату выполнения задачи"""
    data = request.get_json()
    if not data or "due_date" not in data:
        return jsonify({"error": "Due date is required"}), 400
    
    for task in tasks:
        if task["id"] == task_id:
            task["due_date"] = data["due_date"]
            save_tasks()
            return jsonify(task)
    return jsonify({"error": "Task not found"}), 404

# ----------------- Frontend -----------------
@app.route("/")
def home():
    return render_template("index.html")

# ----------------- Run -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)