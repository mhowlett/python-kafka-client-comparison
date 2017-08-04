import sys
import csv
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt

DataKey = namedtuple(
  "DataKey",
  "Type, Client, Version, Partitions, Size, Acks")

DataValue = namedtuple(
  "DataValue",
  "MsgsPerSec, MbPerSec")

PlotKey = namedtuple(
  "PlotKey",
  "Acks, Client, Type, Version")

data = {}

with open(sys.argv[1], newline="") as f:
    reader = csv.reader(f)
    for vs in reader:
        if (len(vs) < 10):
            continue

        if (vs[0].startswith("#")):
            continue

        if (vs[0].startswith("python")):
            continue

        vs = list(map(lambda v: v.strip(), vs))
        k = DataKey(vs[0], vs[1], vs[2], vs[3], vs[4], vs[6])
        v = DataValue(vs[8], vs[9])
        if k in data:
            data[k].append(v)
        else:
            data[k] = [v]

css = ["#0054f2", "#63f011"]
cseen = []
def get_color2(v):
    if not v in cseen:
        cseen.append(v)
    return css[cseen.index(v) % len(css)]

def get_color(axis_number, count, max_count):
    hx = hex(int(255*count/max_count))[2:]
    if (len(hx) == 1):
        hx = "0" + hx
    if axis_number == 1:
        return "#00" + hx + "00"
    return "#" + hx + "0000"

seen = []
lss = ['solid', 'dashed', 'dashdot', 'dotted']
def get_linestyle(v):
    if not v in seen:
        seen.append(v)
    return lss[seen.index(v) % len(lss)]

def make_plot(typ=None, client=None, version=None, partitions=None, acks=None):
    msgs = {}
    mbs = {}

    for key in data:
        size = int(key.Size)

        k = []

        # ignore anything that doesn't match criteria.
        if acks == None:
            k.append(key.Acks)
        else:
            if key.Acks != acks:
                continue

        if client == None:
            k.append(key.Client)
        else:
            if key.Client != client:
                continue

        if typ == None:
            k.append(key.Type)
        else:
            if key.Type != typ:
                continue

        if version == None:
            k.append(key.Version)
        else:
            if key.Version != version:
                continue

        if partitions == None:
            k.append(key.Partitions)
        else:
            if key.Partitions != partitions:
                continue

        k = tuple(k)
        
        if (not k in msgs):
            msgs[k] = []
            mbs[k] = []

        if size in msgs[k]:
            raise Exception("error interpreting data")

        msgsps = list(map(lambda x: int(x.MsgsPerSec), data[key]))
        mbsps = list(map(lambda x: float(x.MbPerSec), data[key]))

        msgs[k].append((size, sum(msgsps)/len(msgsps)))
        mbs[k].append((size, sum(mbsps)/len(mbsps)))

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.set_xlabel('Message Size (bytes)')
    ax1.set_ylabel('ignore this axis')
    ax2.set_ylabel('Mb Per Second')

    count = 0
    for key in msgs:
        xs = list(map(lambda x: x[0], msgs[key]))
        ys = list(map(lambda x: x[1], msgs[key]))
        ys2 = list(map(lambda x: x[1], mbs[key]))
        #ax1.plot(xs, ys, color=get_color(1, count, len(msgs)), label=key)
        ax2.plot(
          xs, ys2, 
          color=get_color2(key[1]), 
          label=key, 
          linestyle=get_linestyle(key[0]))
        count += 1

    ax1.legend()
    ax2.legend()

    fig.tight_layout()
    plt.show()


make_plot(typ='P', version='3.3.0', client='K')