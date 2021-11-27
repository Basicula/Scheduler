from scheduler import *
import random
from multiprocessing import Process
from multiprocessing.managers import BaseManager

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