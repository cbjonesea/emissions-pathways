# Module with useful function

def Interpolate(t, t1, t2, x1, x2):
    return x1 + ((t-t1)/(t2-t1))*(x2-x1)
