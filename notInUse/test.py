l = [{"start":1},
     {'start':5},
     {'start':3}]
l.sort(key=lambda x: x['start'])
print(l)