import random
from datetime import datetime
from oopdb.OOPDB import OOPDB, RowsStyle
from oopdb.Expression import Expression, Operation

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

class Scheduler:
    activities_table_name = "Activities"
    activity_id_column_name = "Id"
    activity_disabled_column_name = "Disabled"
    activity_min_column_name = "Min"
    activity_max_column_name = "Max"
    activity_total_column_name = "TotalDone"

    queued_activities_table_name = "QueuedActivities"
    queued_activities_id_column_name = "Id"
    queued_activities_activity_id_column_name = "ActivityId"
    queued_activities_value_column_name = "Value"
    queued_activities_time_column_name = "Time"
    queued_activities_remaining_time_column_name = "RemainingTime"

    def __init__(self):
        self.session = OOPDB()
        self.session.open("session.db")
        self.cooldown_in_seconds = 1800 # every 30 min
        self.task_time = 43200 # 12 hours
        self.main_timer = Timer(self.cooldown_in_seconds)
        self.task_timers = {}
        self.paused = False

    def get_active_tasks(self):
        return self.session.select(self.queued_activities_table_name).fetch(RowsStyle.DICTIONARY)

    def get_tasks(self):
        return self.session.select(self.activities_table_name).fetch(RowsStyle.DICTIONARY)

    def update_main_timer(self):
        self.main_timer = Timer(self.cooldown_in_seconds)
        self.main_timer.start()

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
        active_task_id_match = Expression(self.queued_activities_id_column_name, Operation.EQUAL, id)
        completed_task = self.session.select(self.queued_activities_table_name,
                                            [self.queued_activities_value_column_name,
                                             self.queued_activities_activity_id_column_name]).where(active_task_id_match).fetch(RowsStyle.DICTIONARY)[0]
        self.session.delete(self.queued_activities_table_name).where(active_task_id_match).execute()
        self.task_timers.pop(id)

        task_id_match = Expression(self.activity_id_column_name, Operation.EQUAL, completed_task[self.queued_activities_activity_id_column_name])
        new_total = self.session.select(self.activities_table_name, [self.activity_total_column_name]).where(task_id_match).fetch()[0][0]
        new_total += completed_task[self.queued_activities_value_column_name]
        new_total = self.session.update(self.activities_table_name, [self.activity_total_column_name], [new_total]).where(task_id_match).execute()

    def toggle_task(self, id):
        task_id_match = Expression(self.activity_id_column_name, Operation.EQUAL, id)
        state = not self.session.select(self.activities_table_name, [self.activity_disabled_column_name]).where(task_id_match).fetch()[0][0]
        self.session.update(self.activities_table_name, [self.activity_disabled_column_name], [state]).where(task_id_match).execute()

    def backup(self):
        for task_id in self.task_timers:
            task_id_match = Expression(self.queued_activities_id_column_name, Operation.EQUAL, task_id)
            self.session.update(self.queued_activities_table_name,
                                [self.queued_activities_remaining_time_column_name],
                                [self.task_timers[task_id].remaining_time()]
                                ).where(task_id_match).execute()

    def load(self):
        active_tasks = self.session.select(self.queued_activities_table_name,
                                            [
                                                self.queued_activities_id_column_name,
                                                self.queued_activities_remaining_time_column_name
                                            ]).fetch(RowsStyle.DICTIONARY)
        for active_task in active_tasks:
            self.task_timers[active_task[self.queued_activities_id_column_name]] = Timer(active_task[self.queued_activities_remaining_time_column_name])

    def toggle(self, to_on):
        if to_on:
            self.paused = False
            for task_id in self.task_timers:
                self.task_timers[task_id].start()
            self.main_timer.start()
        else:
            self.paused = True
            for task_id in self.task_timers:
                self.task_timers[task_id].pause()
            self.main_timer.pause()

    def schedule_new_tasks(self, task_cnt):
        is_enabled = Expression(self.activity_disabled_column_name, Operation.EQUAL, False)
        available_tasks = self.session.select(self.activities_table_name, 
                                                [
                                                self.activity_id_column_name,
                                                self.activity_min_column_name,
                                                self.activity_max_column_name
                                                ]).where(is_enabled).fetch(RowsStyle.DICTIONARY)

        if len(available_tasks) == 0:
            return

        for _ in range(task_cnt):
            base_task = random.choice(available_tasks)
            self.session.insert_into(self.queued_activities_table_name, 
                                    [
                                        self.queued_activities_activity_id_column_name,
                                        self.queued_activities_value_column_name,
                                        self.queued_activities_time_column_name,
                                        self.queued_activities_remaining_time_column_name
                                    ],
                                    [
                                        base_task[self.activity_id_column_name],
                                        random.randint(base_task[self.activity_min_column_name], base_task[self.activity_max_column_name]),
                                        self.task_time,
                                        self.task_time
                                    ]).execute()
            task_id = self.session.last_row_id()
            self.task_timers[task_id] = Timer(self.task_time)
            self.task_timers[task_id].start()

    def start(self):
        self.update_main_timer()
        if len(self.task_timers) > 0:
            for task_id in self.task_timers:
                self.task_timers[task_id].start()

    def update(self):
        if self.main_timer.finished():
            self.schedule_new_tasks(1)
            self.update_main_timer()

        to_remove = []
        for task_id in self.task_timers:
            if self.task_timers[task_id].finished():
                to_remove.append(task_id)
            else:
                task_id_match = Expression(self.queued_activities_id_column_name, Operation.EQUAL, task_id)
                self.session.update(self.queued_activities_table_name,
                                    [self.queued_activities_remaining_time_column_name],
                                    [self.task_timers[task_id].remaining_time()]).where(task_id_match).execute()

        for task_id in to_remove:
            self.task_timers.pop(task_id)
            task_id_match = Expression(self.queued_activities_id_column_name, Operation.EQUAL, task_id)
            self.session.delete(self.queued_activities_table_name).where(task_id_match).execute()
            self.schedule_new_tasks(2)