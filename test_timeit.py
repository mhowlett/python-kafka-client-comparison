import timeit

# quick utility to test speed of timeit.default_timer call

start_time = timeit.default_timer()
cnt = 0
while True:
    t = timeit.default_timer()
    cnt += 1
    if (t - start_time > 10):
        break

print("calls per second: {}".format(cnt / 10))
# ~ 3.5M per second -> negligible.