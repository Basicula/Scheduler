const BLACK = '000000';

class Gradient {
    constructor(from, to, min, max) {
        this.from = from;
        this.to = to;
        this.min = min;
        this.max = max;
    }

    at(i) {
        if (i < this.min || i > this.max)
            return BLACK;
        const diff = this.max - this.min;
        const left = (diff - (i - this.min)) / diff;
        const right = (diff - (this.max - i)) / diff;
        function process_channel(from, to) {
            var res = Math.round(parseInt(from, 16) * left + parseInt(to, 16) * right).toString(16);
            if (res.length < 2)
                res = '0' + res;
            return res;
        }
        const r = process_channel(this.from.substring(0,2), this.to.substring(0,2));
        const g = process_channel(this.from.substring(2,4), this.to.substring(2,4));
        const b = process_channel(this.from.substring(4,6), this.to.substring(4,6));
        return r + g + b;
    }
}