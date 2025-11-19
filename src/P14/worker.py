def compute_something(n):
    r = 0
    for i in range(n):
        r += (200 ** 200) % (1000 + i)
    return r

def compute_something_with_index(index, l, n):
    r = 0
    for i in range(n):
        r += (200 ** 200) % (1000 + i)
    l[index] = r  # we store the result in the list
