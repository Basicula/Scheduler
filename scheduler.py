import random
import time
import json
from shutil import copyfile
from datetime import datetime
from multiprocessing import Process
from multiprocessing.managers import BaseManager

class Timer:
    def __init__(self, time):
        self.time = time
        self.running = False

    def pause(self):
        self.time = self.remaining_time()
        self.running = False

    def start(self):
        self.start_time = datetime.now()
        self.running = True

    def finished(self):
        if not self.running:
            return False
        return int((datetime.now() - self.start_time).total_seconds()) >= self.time

    def remaining_time(self):
        if self.running:
            return self.time - int((datetime.now() - self.start_time).total_seconds())
        else:
            return self.time

class ActiveTask(Process):
    def __init__(self, name, value, task_time, remaining_time, id):
        super(ActiveTask, self).__init__()
        self.name = name
        self.value = value
        self.task_time = task_time
        self.remaining = remaining_time
        self.id = id
        self.timer = Timer(self.remaining)

    def start(self):
        self.timer.start()

    def pause(self):
        self.timer.pause()

    def remaining_time(self):
        return self.timer.remaining_time()

    def finished(self):
        return self.timer.finished()

    def dict(self):
        return {
            'name': self.name,
            'value': self.value,
            'time': self.task_time,
            'remaining_time': self.remaining_time(),
            'id': self.id
        }

class BaseTask:
    def __init__(self, name, type, min, max, total, id):
        self.name = name
        self.type = type
        self.min = min
        self.max = max
        self.total = total
        self.id = id
        self.disabled = False

    def generate_value(self):
        return random.randint(self.min, self.max)

    def toggle(self):
        self.disabled = not self.disabled

    def dict(self):
        return {
            'name': self.name,
            'id': self.id,
            'type': self.type,
            'min': self.min,
            'max': self.max,
            'total': self.total,
            'disabled': self.disabled
        }

class Scheduler:
    def __init__(self):
        self.tasks = []
        self.active_tasks = []
        self.cooldown_in_seconds = 1800 # every 30 min
        #self.task_time = 86400 # 1 day
        self.task_time = 43200 # 12 hours
        self.free_id = 0
        self.main_timer = Timer(self.cooldown_in_seconds)
        self.paused = False

    def add_new_task(self, task):
        self.tasks.append(task)

    def get_active_tasks(self):
        return list(map(lambda task: task.dict(), self.active_tasks))

    def get_tasks(self):
        return list(map(lambda task: task.dict(), self.tasks))

    def set_cooldown(self, cooldown_in_seconds):
        self.cooldown_in_seconds = cooldown_in_seconds
        if self.main_timer.remaining_time() > self.cooldown_in_seconds:
            self.update_main_timer()

    def get_cooldown(self):
        return self.cooldown_in_seconds

    def set_task_time(self, task_time):
        self.task_time = task_time

    def get_task_time(self):
        return self.task_time

    def countdown_time(self):
        return self.main_timer.remaining_time()

    def complete_task(self, id):
        for i, active_task in enumerate(self.active_tasks):
            if active_task.id == id:
                for task in self.tasks:
                    if task.name == active_task.name:
                        task.total += active_task.value
                self.active_tasks.pop(i)
                return

    def toggle_task(self, id):
        for task in self.tasks:
            if task.id == id:
                task.toggle()
                return

    def backup(self):
        with open("backup.json", 'w') as f:
            json.dump({
                'tasks': self.get_tasks(),
                'active_tasks': self.get_active_tasks(),
                'cooldown': self.cooldown_in_seconds,
                'task_time': self.task_time,
                'free_id': self.free_id
            },f,indent=4)

    def load(self):
        try:
            with open("backup.json", 'r') as f:
                data = json.load(f)
                for task in data['tasks']:
                    base_task = BaseTask(task['name'], task['type'], task['min'], task['max'], task['total'], task['id'])
                    self.tasks.append(base_task)
                for active_task in data['active_tasks']:
                    active_task = ActiveTask(active_task['name'], active_task['value'], active_task['time'], active_task['remaining_time'], active_task['id'])
                    self.active_tasks.append(active_task)
                self.cooldown_in_seconds = data['cooldown']
                self.task_time = data['task_time']
                self.free_id = data['free_id']
        except:
            pass

    def toggle(self, to_on):
        if to_on:
            self.paused = False
            for task in self.active_tasks:
                task.start()
            self.main_timer.start()
        else:
            self.paused = True
            for task in self.active_tasks:
                task.pause()
            self.main_timer.pause()

    def schedule_new_tasks(self, task_cnt):
        available_tasks = []
        for task in self.tasks:
            if not task.disabled:
                available_tasks.append(task)
        if len(available_tasks) == 0:
            return
        for _ in range(task_cnt):
            base_task = random.choice(available_tasks)
            self.active_tasks.append(ActiveTask(base_task.name, base_task.generate_value(), self.task_time, self.task_time, self.free_id))
            self.free_id += 1
            self.active_tasks[-1].start()

    
    def update_main_timer(self):
        self.main_timer = Timer(self.cooldown_in_seconds)
        self.main_timer.start()

    def start(self):
        self.update_main_timer()
        if len(self.active_tasks) > 0:
            for active_task in self.active_tasks:
                active_task.start()

        while True:
            time.sleep(0.5)
            if self.paused:
                continue

            if self.main_timer.finished():
                self.schedule_new_tasks(1)
                self.update_main_timer()

            to_remove = []
            for i, task_timer in enumerate(self.active_tasks):
                if task_timer.finished():
                    to_remove.append(i)
            
            for id in to_remove:
                self.active_tasks.pop(id)
                self.schedule_new_tasks(2)

def fill_random_tasks(scheduler):
    types = ["Reps", "Time"]
    for i in range(10):
        scheduler.add_new_task(BaseTask("Task" + str(i), random.choice(types), random.randint(0, 10), random.randint(10, 20), 0))

def test_timer():
    timer = Timer(6)
    timer.start()
    time.sleep(2)
    print(timer.remaining_time())
    timer.pause()
    time.sleep(2)
    print(timer.remaining_time())
    timer.start()
    time.sleep(5)
    print(timer.finished())

def test_scheduler():
    BaseManager.register("Scheduler", Scheduler)
    manager = BaseManager()
    manager.start()

    scheduler = manager.Scheduler()
    scheduler.load()
    process = Process(target=scheduler.start)
    process.start()
    for i in range(10):
        print(scheduler.get_active_tasks())
        time.sleep(2)
    scheduler.backup()
    process.terminate()
    process.join()

if __name__ == "__main__":
    #test_timer()
    test_scheduler()