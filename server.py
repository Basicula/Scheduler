from flask import Flask, render_template, url_for, request, Response
from multiprocessing import Process
from multiprocessing.managers import BaseManager

from scheduler import *

app = Flask(__name__)

scheduler = None
scheduler_main_process = None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/scheduler", methods=["GET", "POST"])
def scheduler_app():
    if request.method == "POST":
        form = request.form
        scheduler.set_cooldown(int(form["cooldown_in_seconds"]))
    return render_template("scheduler.html", tasks=scheduler.get_tasks(), cooldown=scheduler.get_cooldown(), task_time=scheduler.get_task_time())

@app.route("/cooldown_set", methods=["POST"])
def cooldown_set():
    scheduler.set_cooldown(int(request.form["cooldown_in_seconds"]))
    return Response(status=200)

@app.route("/task_time_set", methods=["POST"])
def task_time_set():
    scheduler.set_task_time(int(request.form["task_time"]))
    return Response(status=200)

@app.route("/scheduler_get", methods=["GET"])
def scheduler_get_task():
    response = {}
    response['countdown_time'] = scheduler.countdown_time()
    response['active_tasks'] = scheduler.get_active_tasks()
    response['tasks'] = scheduler.get_tasks()
    return response

@app.route("/complete_task", methods=["POST"])
def complete_task():
    form = request.form
    new_total = scheduler.complete_task(int(form['id']))
    return Response(new_total, status=200)

@app.route("/pause", methods=["POST"])
def pause():
    scheduler.toggle(False)
    return Response(status=200)

@app.route("/start", methods=["POST"])
def start():
    scheduler.toggle(True)
    return Response(status=200)

@app.route("/new_task", methods=["Post"])
def new_task():
    scheduler.schedule_new_tasks(1)
    return Response(status=200)

@app.route("/backup", methods=["POST"])
def backup():
    scheduler.backup()
    return Response(status=200)

@app.route("/toggle_task", methods=["POST"])
def toggle_task():
    form = request.form
    scheduler.toggle_task(int(form['id']))
    return Response(status=200)


if __name__ == "__main__":
    BaseManager.register("Scheduler", Scheduler)
    manager = BaseManager()
    manager.start()

    scheduler = manager.Scheduler()
    scheduler.load()
    scheduler_main_process = Process(target=scheduler.start)
    scheduler_main_process.start()

    app.run(debug=True)