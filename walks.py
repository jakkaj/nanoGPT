from math import dist
from numpy import random
from operator import add
import plotille
import secrets

trials = 1000
steps = 20
step_limit = 4
backlog_multiplier = 3
experiment_success_bar = 85 # in [0, 255], lower is better

start = (70, 70)
good = (95, 95)
max = (100, 100)

rng = random.default_rng(secrets.randbits(128))

def incline(p, step, step_limit, max):
    limits = tuple(map(lambda d: 0 if d[1] > 98 else (d[0] - d[1]) // step_limit + 1, zip(max, p)))
    return tuple(map(min, zip(step, limits)))

def prioritize_x(item):
    return item[0] * 10 + item[1]

def prioritize_y(item):
    return item[1] * 10 + item[0]

def walks(trials, steps, step_limit, start, max, t):
    end_points = []
    for _ in range (0, trials):
        p = start
        backlog = list(rng.integers(-step_limit, step_limit, (steps * backlog_multiplier, 2), endpoint=True))
        for _ in range(0, steps):
            if p[0] < p[1]:
                backlog.sort(reverse=True, key=prioritize_x)
            else:
                backlog.sort(reverse=True, key=prioritize_y)
            h = backlog.pop(0)
            e = tuple(map(add, p, incline(p, h, step_limit, max))) if rng.bytes(1)[0] > experiment_success_bar else p
            p = e if t(p, e, max) else p
            if p == max:
                break
        end_points.append(p)
    return end_points

end_points_three = walks(trials, steps, step_limit, start, max, lambda a, b, c: dist(b, c) < dist(a, c))

start_dist_three = list(map(lambda p: dist(start, p), end_points_three))
max_dist_three = list(map(lambda p: dist(max, p), end_points_three))

print()

def scatter_plot(label, points, start, good):
    print(label)
    fig = plotille.Figure()
    fig.width = 25
    fig.height = 10
    fig.set_x_limits(min_=50, max_=100)
    fig.set_y_limits(min_=50, max_=100)
    fig.x_label = 'm2'
    fig.y_label = 'm1'
    fig.origin = False
    fig.color_mode = 'names'
    x, y = zip(*points)
    fig.scatter(x, y)
    fig.scatter([start[0]], [start[1]], lc='blue')
    fig.scatter([good[0]], [good[1]], lc='green')
    print(fig.show())
    print()

scatter_plot('WALKS THREE', end_points_three, start, good)

def histogram(label, distances):
    bins = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 100.0]
    counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for d in distances:
        i = round(d) // 5 if d < 55 else 11
        counts[i] += 1
    print(label)
    print(plotille.hist_aggregated(counts, bins, width=25))
    print()

histogram('WALKS THREE START DISTANCE', start_dist_three)
histogram('WALKS THREE MAX DISTANCE', max_dist_three)