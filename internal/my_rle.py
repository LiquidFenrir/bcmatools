hex_start_set = "0123456789abcdef"
alpha_end_set = "ABCDEFGHIJKLMNOP"
convert_to_alpha = str.maketrans(hex_start_set, alpha_end_set)
convert_to_hex = str.maketrans(alpha_end_set, hex_start_set)

def do_compression(data):
    out = []
    data = data.translate(convert_to_alpha)

    duration = 0
    previous = data[0]
    for c in data:
        if c != previous:
            if duration != 1:
                out.append(str(duration))
            out.append(previous)
            duration = 1
            previous = c
        else:
            duration += 1

    if duration != 1:
        out.append(str(duration))
    out.append(previous)

    return "".join(out)

def do_decompression(compressed):
    out = []
    num = []
    for c in compressed:
        if c.isdigit():
            num.append(c)
        else:
            character = c
            if len(num) != 0:
                duration = int("".join(num))
                num.clear()
                out.append(character * duration)
            else:
                out.append(character)
    out = "".join(out)
    out = out.translate(convert_to_hex)
    return out
