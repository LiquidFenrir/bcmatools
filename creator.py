import sys
from internal.creation import BCMA

def do_creation(xml_name, out_name):
    with open(xml_name, "rb") as f:
        bcma = BCMA(f)

    with open(out_name, "wb") as f:
        bcma.write_to_file(f)

    print("Complete")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        do_creation(sys.argv[1], sys.argv[2])
    else:
        print("Usage: {} <input .xml path> <output .bcma path>".format(sys.argv[0]))
        sys.exit(0)
