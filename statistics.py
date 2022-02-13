import json
import matplotlib
from oopdb.OOPDB import OOPDB, RowsStyle
from oopdb.Expression import Expression, Operation
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import datetime

def format_time_in_seconds(seconds, _):
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    return "{:d}:{:02d}:{:02d}".format(hours, minutes, seconds)
seconds_formatter = FuncFormatter(format_time_in_seconds)

def load_statistics():
    with open("statistics.json", 'r') as fi:
        return json.load(fi)

def get_day_statistics(statistics, day):
    day_statistics = {"Reps": [], "Time" : []}
    if not day in statistics:
        return day_statistics

    session = OOPDB()
    session.open("session.db")
    day_data = statistics[day]
    for status in ["failed", "done"]:
        for activity_data in day_data[status]:
            match_activity_id = Expression("Id", Operation.EQUAL, activity_data["id"])
            activity_info = session.select("Activities").where(match_activity_id).fetch(RowsStyle.DICTIONARY)[0]
            type = activity_info["Type"]
            exists_activity_stat_id = -1
            for i in range(len(day_statistics[type])):
                if day_statistics[type][i][0] == activity_data["id"]:
                    exists_activity_stat_id = i
                    break
            if exists_activity_stat_id == -1:
                day_statistics[type].append(
                    [activity_data["id"], 
                    activity_data["name"], 
                    0,
                    0])
            if status == "failed":
                day_statistics[type][exists_activity_stat_id][3] = activity_data["total"]
            else:
                day_statistics[type][exists_activity_stat_id][2] = activity_data["total"]

    return day_statistics

def get_period_statistics(statistics, start_date, end_date):
    step = datetime.timedelta(days=1)
    curr = datetime.datetime.strptime(start_date,'%d/%m/%Y').date()
    end = datetime.datetime.strptime(end_date,'%d/%m/%Y').date() + step
    period_statistics = {"Reps": [], "Time" : []}
    while curr != end:
        day_statistics = get_day_statistics(statistics, datetime.datetime.strftime(curr,'%d/%m/%Y'))
        for type in day_statistics:
            for day_activity_stat in day_statistics[type]:
                exists = False
                for period_activity_stat in period_statistics[type]:
                    if period_activity_stat[0] == day_activity_stat[0]:
                        exists = True
                        period_activity_stat[2] += day_activity_stat[2]
                        period_activity_stat[3] += day_activity_stat[3]
                        break
                if not exists:
                    period_statistics[type].append(day_activity_stat)
        curr += step
    return period_statistics

def plot_day_statistics(day_statistics, date = ""):
    fig = plt.figure()

    fig.suptitle(f"Statistics for {date}", fontsize=16)

    reps_ax = fig.add_subplot(2, 1, 1)
    reps_ax.title.set_text("Reps done activities")
    reps_ax.set_xlabel("Activity name")
    reps_ax.set_ylabel("Done reps")

    time_ax = fig.add_subplot(2, 1, 2)
    time_ax.title.set_text("Time done activities")
    time_ax.set_xlabel("Activity name")
    time_ax.set_ylabel("Done time")
    time_ax.yaxis.set_major_formatter(seconds_formatter)

    for data, ax in zip([day_statistics["Reps"], day_statistics["Time"]], [reps_ax, time_ax]):
        x = np.arange(len(data))
        done_x = x - 0.2
        failed_x = x + 0.2
        data = np.array(data)
        done_bars = ax.bar(done_x, np.array(data[:,2], dtype=np.int32), width=0.4, label="Done")
        failed_bars = ax.bar(failed_x, np.array(data[:,3], dtype=np.int32), width=0.4, label="Failed")
        ax.set_xticks(x, labels=data[:,1])
        ax.legend()

        ax.bar_label(done_bars, label_type="center")
        ax.bar_label(failed_bars, label_type="center")

    plt.show()

def plot_period_statistics(statistics, start, end):
    fig = plt.figure()

    fig.suptitle(f"Statistics for period {start} - {end}", fontsize=16)

    reps_ax = fig.add_subplot(2, 1, 1)
    reps_ax.title.set_text("Reps done activities")
    reps_ax.set_xlabel("Activity name")
    reps_ax.set_ylabel("Done reps")

    time_ax = fig.add_subplot(2, 1, 2)
    time_ax.title.set_text("Time done activities")
    time_ax.set_xlabel("Activity name")
    time_ax.set_ylabel("Done time")
    time_ax.yaxis.set_major_formatter(seconds_formatter)

    period_statistics = get_period_statistics(statistics, start, end)
    for data, ax in zip([period_statistics["Reps"], period_statistics["Time"]], [reps_ax, time_ax]):
        x = np.arange(len(data))
        done_x = x - 0.2
        failed_x = x + 0.2
        data = np.array(data)
        done_bars = ax.bar(done_x, np.array(data[:,2], dtype=np.int32), width=0.4, label="Done")
        failed_bars = ax.bar(failed_x, np.array(data[:,3], dtype=np.int32), width=0.4, label="Failed")
        ax.set_xticks(x, labels=data[:,1], rotation=10)
        ax.legend()

        ax.bar_label(done_bars, label_type="center")
        ax.bar_label(failed_bars, label_type="center")

    plt.show()

def plot_day_by_day_statistics(statistics):
    for day in statistics:
        day_statistics = get_day_statistics(statistics, day)
        plot_day_statistics(day_statistics, day)

def get_activity_total_statistic(statistics, activity_id):
    dates = []
    totals = []

    for day in statistics:
        day_statistic = statistics[day]
        dates.append(day)
        exists = False
        for activity_total in day_statistic["totals"]:
            if activity_total["id"] == activity_id:
                totals.append(activity_total["total"])
                exists = True
                break
        if not exists:
            totals.append(0)

    for i in range(len(totals)):
        if totals[i] != 0:
            continue
        if i > 0 and totals[i - 1] != 0:
            totals[i] = totals[i - 1]
        else:
            j = i + 1
            while j < len(totals) and totals[j] == 0:
                j += 1
            if j < len(totals):
                totals[i] = totals[j]

    return dates, totals

def plot_activity_total_statistic(statistics, activity_id):
    session = OOPDB()
    session.open("session.db")
    match_activity_id = Expression("Id", Operation.EQUAL, activity_id)
    activity = session.select("Activities").where(match_activity_id).fetch(RowsStyle.DICTIONARY)[0]

    dates, totals = get_activity_total_statistic(statistics, activity_id)

    plt.title(f"{activity['Name']} totals")
    plt.xlabel("Date")
    if activity["Type"] == "Reps":
        plt.ylabel("Total reps done")
    else:
        plt.ylabel("Total time spent")
        plt.gca().yaxis.set_major_formatter(seconds_formatter)

    dates = [datetime.datetime.strptime(d,'%d/%m/%Y').date() for d in dates]

    plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d/%m/%Y'))
    plt.gca().xaxis.set_major_locator(matplotlib.dates.DayLocator())
    plt.plot(dates, totals)
    plt.show()

if __name__ == "__main__":
    statistics = load_statistics()
    today = datetime.datetime.today().strftime("%d/%m/%Y")
    #day_statistics = get_day_statistics(statistics, today)
    #plot_day_statistics(day_statistics)
    plot_period_statistics(statistics, "01/02/2022", today)
    #plot_day_by_day_statistics(statistics)
    #plot_activity_total_statistic(statistics, 0)