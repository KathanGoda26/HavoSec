import subprocess


def unsafe(user_input):
    return eval(user_input)


def also_unsafe(user_input):
    # Intentionally vulnerable local static-analysis fixture; never execute this file.
    return subprocess.run(user_input, shell=True)
