function format_time(time_in_s) {
    var time = time_in_s;

    const s = String(time % 60).padStart(2, '0');
    time = Math.floor(time/60);
    const m = String(time % 60).padStart(2, '0');
    time = Math.floor(time/60);
    const h = String(time).padStart(2, '0');
    
    return `${h}:${m}:${s}`;
  }

class ActiveTask {
    constructor(task, name) {
        this.name = name;
        this.activity_id = task.ActivityId;
        this.value = task.Value;
        this.time = task.Time;
        this.remaining_time = task.RemainingTime;
        this.id = task.Id;
        this.position = [0, 0];
        
        this.alarm_sound = new Audio('https://media.geeksforgeeks.org/wp-content/uploads/20190531135120/beep.mp3');
        this.alarm_stoped = false;

        this._init_circle();
        this._init_element();
        this._init_timer_element();
    }

    _init_circle() {
        this.circle = {};
        this.circle.inner_radius = 50;
        this.circle.stroke_width = 5;
        this.circle.radius = this.circle.inner_radius + this.circle.stroke_width
        this.circle.center = [this.circle.radius, this.circle.radius];
        this.circle.speed_vec = [0, 0];

        var self = this;
        this.circle.move = function() {
            self.set_position(self.position[0] + this.speed_vec[1], self.position[1] + this.speed_vec[0]);
        }
    }

    _init_element() {
        this.element = document.createElement("div");
        this.element.classList.add('active-task');
    }

    _init_timer_element() {
        this._init_timer_label_info();
        this._init_svg();
    }

    _init_timer_label_info() {
        this.timer_label = document.createElement('div');
        this.timer_label.classList.add('timer-label');
        
        this.active_task_header = document.createElement("div");
        this.active_task_header.textContent = this.name;
        this.timer_label.appendChild(this.active_task_header);

        this.active_task_value = document.createElement("div");
        this.active_task_value.textContent = this.value;
        this.timer_label.appendChild(this.active_task_value);
        
        this.active_task_time = document.createElement("div");
        this.active_task_time.textContent = format_time(this.time);
        this.timer_label.appendChild(this.active_task_time);

        this.element.appendChild(this.timer_label);
    }

    _init_svg() {
        this.element.style.height = 2 * this.circle.radius + 'px';
        this.element.style.width = 2 * this.circle.radius + 'px';

        this.svg_element = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        const svgNS = this.svg_element.namespaceURI;
        this.svg_element.setAttribute('height', 2 * this.circle.radius);
        this.svg_element.setAttribute('width', 2 * this.circle.radius);

        this.g_element = document.createElementNS(svgNS, 'g');
        this.g_element.classList.add('timer-circle-container');

        this.circle_element = document.createElementNS(svgNS, 'circle');
        this.circle_element.classList.add('timer-circle');
        this.circle_element.setAttribute('cx', this.circle.center[0]);
        this.circle_element.setAttribute('cy', this.circle.center[1]);
        this.circle_element.setAttribute('r', this.circle.inner_radius);
        this.circle_element.setAttribute('fill', 'none');
        this.circle_element.setAttribute('stroke-width', this.circle.stroke_width);

        this.g_element.appendChild(this.circle_element);

        this.path_element = document.createElementNS(svgNS, 'path');
        this.path_element.classList.add('timer-path');
        this.path_element.setAttribute('d', 'M ' + this.circle.center[0] + ' ' + this.circle.center[1] + '\
                                m ' + (-this.circle.inner_radius) + ' 0 \
                                a ' + this.circle.inner_radius + ' ' + this.circle.inner_radius + ' 0 1 0 ' + 2 * (this.circle.inner_radius) + ' 0 \
                                a ' + this.circle.inner_radius + ' ' + this.circle.inner_radius + ' 0 1 0 ' + 2 * (-this.circle.inner_radius) + ' 0');
        this.path_length = Math.round(2 * this.circle.inner_radius * Math.PI);
        this.gradient = new Gradient('00ff00', 'ff0000', 0, this.path_length);
        this.path_element.setAttribute('stroke', '#' + this.gradient.at(0));
        this.path_element.setAttribute('stroke-width', this.circle.stroke_width);
        this.update_remaining_time(this.remaining_time);

        this.g_element.appendChild(this.path_element);

        this.svg_element.appendChild(this.g_element);

        this.element.appendChild(this.svg_element); 
    }

    update_remaining_time(remaining_time) {
        if (remaining_time < 600 && !this.alarm_stoped)
            this.alarm_sound.play();
        this.remaining_time = remaining_time;
        this.active_task_time.textContent = format_time(this.remaining_time);
        const path_length = Math.round(this.path_length * this.remaining_time / this.time);
        this.path_element.setAttribute('stroke-dasharray', `${path_length} ${this.path_length}`);
        this.path_element.setAttribute('stroke', '#' + this.gradient.at(this.path_length - path_length));
    }

    set_position(top, left) {
        this.position = [top, left];
        this.circle.center = [this.circle.radius + left, this.circle.radius + top];
        $(this.element).css('top', top);
        $(this.element).css('left', left);
    }
}