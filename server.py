from flask import Flask, render_template, url_for, request, Response

from scheduler import *

app = Flask(__name__)

scheduler = Scheduler()
scheduler.load()
scheduler.start()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/scheduler", methods=["GET"])
def scheduler_app():
    return render_template("scheduler.html", tasks=scheduler.get_tasks(), cooldown=scheduler.get_cooldown(), task_time=scheduler.get_task_time())

@app.route("/cooldown_set", methods=["PUT"])
def cooldown_set():
    scheduler.set_cooldown(int(request.form["cooldown_in_seconds"]))
    return Response(status=200)

@app.route("/task_time_set", methods=["PUT"])
def task_time_set():
    scheduler.set_task_time(int(request.form["task_time"]))
    return Response(status=200)

@app.route("/scheduler_get", methods=["GET"])
def scheduler_get_task():
    response = {}
    scheduler.update()
    response['countdown_time'] = scheduler.countdown_time()
    response['active_tasks'] = scheduler.get_active_tasks()
    response['tasks'] = scheduler.get_tasks()
    return response

@app.route("/complete_task", methods=["DELETE"])
def complete_task():
    form = request.form
    scheduler.complete_task(int(form['id']))
    return Response(status=200)

@app.route("/pause", methods=["PUT"])
def pause():
    scheduler.toggle(False)
    return Response(status=200)

@app.route("/start", methods=["PUT"])
def start():
    scheduler.toggle(True)
    return Response(status=200)

@app.route("/new_task", methods=["POST"])
def new_task():
    scheduler.schedule_new_tasks(1)
    return Response(status=200)

@app.route("/backup", methods=["PUT"])
def backup():
    scheduler.backup()
    return Response(status=200)

@app.route("/toggle_task", methods=["PUT"])
def toggle_task():
    form = request.form
    scheduler.toggle_task(int(form['id']))
    return Response(status=200)

if __name__ == "__main__":
    app.run(threaded=False, debug=False)