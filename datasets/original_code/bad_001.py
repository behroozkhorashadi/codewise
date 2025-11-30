def f(d):
    x = []
    for k in d:
        if isinstance(d[k], list):
            for i in range(len(d[k])):
                if d[k][i] > 0 and d[k][i] < 100:
                    x.append(d[k][i] * 2)
    return x
