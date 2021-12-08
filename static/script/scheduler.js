function check_collision(first_circle, second_circle) {
    const center_dist = (first_circle.center[0] - second_circle.center[0]) * (first_circle.center[0] - second_circle.center[0]) +
        (first_circle.center[1] - second_circle.center[1]) * (first_circle.center[1] - second_circle.center[1]);
    return center_dist < (first_circle.radius + second_circle.radius) * (first_circle.radius + second_circle.radius);
}

function reflect(vec, normal) {
    const dot2 = 2 * (vec[0] * normal[0] + vec[1] * normal[1]);
    return [vec[0] - dot2 * normal[0], vec[1] - dot2 * normal[1]];
}

class SchedulerField {
    constructor() {
        this.active_tasks = [];
        this.score = 0;

        this._field_element = document.getElementById("scheduler_field");

        this._field_element.onclick = update;
    }

    add_new_task(task) {
        this.active_tasks.push(task);
        this._field_element.appendChild(task.element);

        const parent_pos = $(this._field_element).position();
        const top = parent_pos.top + CommonUtils.random(0, this._field_element.offsetHeight - $(task.element).height());
        const left = parent_pos.left + CommonUtils.random(0, this._field_element.offsetWidth - $(task.element).width());
        task.set_position(top, left);
    }

    update_tasks(active_tasks, tasks) {
        var to_remove = [];
        for (let i = 0; i < this.active_tasks.length; ++i) {
            const task = this.active_tasks[i];
            let task_is_running = false;
            for (let j = 0; j < active_tasks.length; ++j) {
                if (task.id == active_tasks[j].Id) {
                    task_is_running = true;
                    break;
                }
            }
            if (!task_is_running)
                to_remove.push(i);
        }

        to_remove.reverse()
        for (let i = 0; i < to_remove.length; ++i) {
            this._field_element.removeChild(this.active_tasks[to_remove[i]].element);
            this.active_tasks.splice(to_remove[i], 1);
        }

        for (let i = 0; i < active_tasks.length; ++i) {
            const task = active_tasks[i];
            let task_is_new = true;
            for (let j = 0; j < this.active_tasks.length; ++j) {
                let active_task = this.active_tasks[j];
                if (task.Id == active_task.id) {
                    task_is_new = false;
                    active_task.update_remaining_time(task.RemainingTime);
                    break;
                }
            }
            if (task_is_new) {
                for (let i = 0; i < tasks.length; ++i) {
                    if (tasks[i].Id == task.ActivityId) {
                        if (tasks[i].ShortName)
                            this.add_new_task(new ActiveTask(task, tasks[i].ShortName));
                        else
                            this.add_new_task(new ActiveTask(task, tasks[i].Name));
                        break;
                    }
                }
            }
        }
    }

    // TODO physic simulation for particles
    update_physic() {
        for (let i = 0; i < this.active_tasks.length; ++i) {
            this.active_tasks[i].circle.move();
        }
        for (let i = 0; i < this.active_tasks.length; ++i) {
            var first_circle = this.active_tasks[i].circle;
            for (let j = i + 1; j < this.active_tasks.length; ++j) {
                var second_circle = this.active_tasks[j].circle;
                if (check_collision(first_circle, second_circle)) {
                    let dx = first_circle.center[0] - second_circle.center[0];
                    let dy = first_circle.center[1] - second_circle.center[1];
                    const len = Math.sqrt(dx * dx + dy * dy);
                    dx /= len;
                    dy /= len;
                    second_circle.speed_vec[0] += -dx;
                    second_circle.speed_vec[1] += -dy;
                    first_circle.speed_vec[0] += dx;
                    first_circle.speed_vec[1] += dy;
                }
            }
            const pos = $(this._field_element).position();
            const top = pos.top;
            const bottom = pos.top + this._field_element.offsetHeight;
            const left = pos.left;
            const right = pos.left + this._field_element.offsetWidth;
            if (first_circle.center[0] + first_circle.radius > right)
                first_circle.speed_vec = reflect(first_circle.speed_vec, [-1, 0]);
            else if (first_circle.center[0] - first_circle.radius < left)
                first_circle.speed_vec = reflect(first_circle.speed_vec, [1, 0]);
            else if (first_circle.center[1] + first_circle.radius > bottom)
                first_circle.speed_vec = reflect(first_circle.speed_vec, [0, -1]);
            else if (first_circle.center[1] - first_circle.radius < top)
                first_circle.speed_vec = reflect(first_circle.speed_vec, [0, 1]);
        }
    }

    sort_tasks() {
        this.active_tasks.sort(function (a, b) {
            return a.remaining_time - b.remaining_time;
        });
        var x = 0, y = 0;
        const pos = $(this._field_element).position();
        const maxx = this._field_element.offsetWidth;
        for (let i = 0; i < this.active_tasks.length; ++i) {
            var task = this.active_tasks[i];
            if (x + 2 * task.circle.radius > maxx) {
                x = 0;
                y += 2 * task.circle.radius;
            }
            task.set_position(y, pos.left + x);
            x += 2 * task.circle.radius;
            if (x >= maxx) {
                x = 0;
                y += 2 * task.circle.radius;
            }
        }
    }
}

scheduler_field = undefined;
paused = false;
base_tasks_elements = [];

function get_task_total_text(task) {
    if (task.Type == "Reps")
        return task.TotalDone;
    else
        return format_time(task.TotalDone);
}

function update_totals(tasks) {
    for (let i = 0; i < tasks.length; ++i) {
        const task = tasks[i];
        $(`#base_task_${task.Id}_total`).text(get_task_total_text(tasks[i]));
    }
}

function init_base_tasks(tasks) {
    base_tasks_elements = [];
    var base_tasks_container = document.getElementById("base_tasks_container");
    while (base_tasks_container.firstChild) {
        base_tasks_container.removeChild(base_tasks_container.lastChild);
    }
    for (let i = 0; i < tasks.length; ++i) {
        const task = tasks[i];
        base_tasks_elements.push(new DropDownButton(task.Name + ": "));
        base_tasks_elements[i].element.classList.add("task");

        var task_buttons_container = document.createElement("div");
        task_buttons_container.classList.add("task-buttons-container");

        var color_picker = new ColorPicker();
        color_picker.element.classList.add("color-picker-button");
        color_picker.onchange_callback = function () {
            base_tasks_elements[i].element.style.backgroundColor = this.color;
        };
        task_buttons_container.appendChild(color_picker.element);

        var disabling_button = document.createElement("div");
        disabling_button.classList.add("disabling-button")
        if (task.Disabled)
            base_tasks_elements[i].element.classList.add("disabled");
        disabling_button.textContent = '⦸';
        disabling_button.onclick = function() {
            base_tasks_elements[i].element.classList.toggle("disabled");
            $.ajax({
                type: "PUT",
                url: "/toggle_task",
                data: {"id" : task.Id}
            });
        };
        task_buttons_container.appendChild(disabling_button);

        base_tasks_elements[i].element.appendChild(task_buttons_container);

        var task_inner_content = document.createElement("div");
        task_inner_content.classList.add("task-details");

        base_tasks_elements[i].task_total = document.createElement("div");
        base_tasks_elements[i].task_total.classList.add("task-total");
        base_tasks_elements[i].task_total.textContent = "Total: ";
        base_tasks_elements[i].task_total_span = document.createElement("span");
        base_tasks_elements[i].task_total_span.classList.add("task-total-done");
        base_tasks_elements[i].task_total_span.setAttribute("id", `base_task_${task.Id}_total`);
        base_tasks_elements[i].task_total_span.textContent = get_task_total_text(task);
        base_tasks_elements[i].button.appendChild(base_tasks_elements[i].task_total_span);
        task_inner_content.appendChild(base_tasks_elements[i].task_total);

        var task_type = document.createElement("div");
        task_type.classList.add("task-type");
        task_type.textContent = "Type: " + task.Type;
        task_inner_content.appendChild(task_type);

        var task_range = document.createElement("div");
        task_range.classList.add("task-range");
        task_range.textContent = "Range: [" + task.Min + ", " + task.Max + "]"
        task_inner_content.appendChild(task_range);

        base_tasks_elements[i].button.classList.add("task-header");
        base_tasks_elements[i].set_inner_content(task_inner_content);

        base_tasks_elements[i].on_open_callback = function () {
            base_tasks_elements[i].task_total.appendChild(base_tasks_elements[i].task_total_span);
        };

        base_tasks_elements[i].on_hide_callback = function () {
            base_tasks_elements[i].button.appendChild(base_tasks_elements[i].task_total_span);
        };

        base_tasks_container.appendChild(base_tasks_elements[i].element);
    }
}

function update() {
    if (!paused) {
        $.ajax({
            type: "GET",
            url: "/scheduler_get",
            success: function (response) {
                if (base_tasks_elements.length != response.tasks.length)
                    init_base_tasks(response.tasks);
                $("#scheduler_countdown").text(format_time(response.countdown_time));
                scheduler_field.update_tasks(response.active_tasks, response.tasks);
                update_totals(response.tasks);
            }
        });
    }
}

function set_events() {
    var scheduler_cooldown_input = document.getElementById("scheduler_cooldown_input");
    scheduler_cooldown_input.onchange = function () {
        $.ajax({
            type: 'PUT',
            url: "/cooldown_set",
            data: { "cooldown_in_seconds": this.value }
        });
        $(this).blur();
    };

    var scheduler_task_time_input = document.getElementById("scheduler_task_time_input");
    scheduler_task_time_input.onchange = function () {
        $.ajax({
            type: 'PUT',
            url: "/task_time_set",
            data: { "task_time": this.value }
        });
        $(this).blur();
    };

    var config_pause_button = document.getElementById("config_pause_button");
    config_pause_button.onclick = function () {
        if (this.value === "Pause") {
            this.value = "Start";
            paused = true;
            $.ajax({
                type: 'PUT',
                url: "/pause"
            });
        }
        else {
            this.value = "Pause";
            paused = false;
            $.ajax({
                type: 'PUT',
                url: "/start"
            });
        }
    };

    var config_get_task_button = document.getElementById("config_get_task_button");
    config_get_task_button.onclick = function () {
        $.ajax({
            type: 'POST',
            url: "/new_task"
        });
    };

    var config_backup_button = document.getElementById("config_backup_button");
    config_backup_button.onclick = function () {
        $.ajax({
            type: 'PUT',
            url: "/backup"
        });
    };

    $(document).keypress(function (event) {
        if (event.ctrlKey && event.shiftKey && event.code === "KeyS") // ctrl + shift + s
            scheduler_field.sort_tasks();
    });
}

var update_interval;
function update_rate_change() {
    clearInterval(update_interval);
    if(document.hidden)
        update_interval = setInterval(update, 60000);
    else
        update_interval = setInterval(update, 1000);
}
document.addEventListener("visibilitychange", update_rate_change, false);

$(document).ready(function () {
    scheduler_field = new SchedulerField();
    set_events();
    update_interval = setInterval(update, 1000);
});