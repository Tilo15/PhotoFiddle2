
def Scalar(value, channels=4):
    l = []
    for i in range(channels):
        l.append(value)

    return tuple(l)