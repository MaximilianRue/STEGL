ACTIVE = True

def print_log(text, end="\n"):
    if ACTIVE: print(text, end=end, flush=True)