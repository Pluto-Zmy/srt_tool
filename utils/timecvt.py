def timecvt(time_code: str, base_fps: int):
    if base_fps <= 0:
        return 0

    time_list = time_code.split(':') if ':' in time_code else time_code.split(';')
    if len(time_list) < 4:
        return 0

    h = int(time_list[0])
    m = int(time_list[1])
    s = int(time_list[2])
    f = int(time_list[3])

    seconds = f / base_fps + s + m * 60 + h * 3600
    return seconds