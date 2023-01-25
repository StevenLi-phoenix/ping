import tracemalloc

tracemalloc.start()

"""START APP HERE"""
import curioping
curioping.main()
"""END APP HERE"""

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')


print("[ Top 100 ]")
for stat in top_stats[:100]:
    print(stat)