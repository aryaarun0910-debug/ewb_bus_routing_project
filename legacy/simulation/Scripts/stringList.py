import json
import random
def fillList(letter, max):
    list = []
    for i in range(0, max+1):
        list.append(f"{letter}{i}")
    return list
def randomList(length):
    indexes = []
    for i in range(0, length+1):
        indexes.append(random.randint(0, 26))
    return indexes

busStops = fillList("S", 15)
corners = fillList("Q", 26)
my_list = randomList(5)
# Replace indexes in list with values from busStops and coners. Alternate
for i in range(0, len(my_list)):
    if(i % 2 == 0):
        my_list[i] = busStops[my_list[i] % 15]
    else:
        my_list[i] = corners[my_list[i]]


# Must wrap in a dict with a key that matches C# field
print(json.dumps({"items": my_list}))
