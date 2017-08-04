import sys
import csv
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

DataKey = namedtuple(
  "DataKey",
  "Type, Client, Version, Partitions, Size, Acks")

DataValue = namedtuple(
  "DataValue",
  "MsgsPerSec, MbPerSec")

PlotKey = namedtuple(
  "PlotKey",
  "Acks, Client, Type, Version")


def read_data(filename):
    data = {}
    with open(filename, newline="") as f:
        reader = csv.reader(f)
        for vs in reader:
            if (len(vs) < 10):
                continue

            if (vs[0].startswith("#")):
                continue

            vs = list(map(lambda v: v.strip(), vs))
            k = DataKey(vs[0], vs[1], vs[2], vs[3], vs[4], vs[6])
            v = DataValue(vs[8], vs[9])
            if k in data:
                data[k].append(v)
            else:
                data[k] = [v]

    return data


css = ["#0054f2", "#63f011"]
cseen = []
def get_color(v):
    if not v in cseen:
        cseen.append(v)
    return css[cseen.index(v) % len(css)]

css2 = ["#0054F2", "#F2DE00", "#F20000", "#00F291"]
cseen2 = []
def get_color2(v):
    if not v in cseen2:
        cseen2.append(v)
    return css2[cseen2.index(v) % len(css2)]


seen = []
lss = ['solid', 'dashed', 'dashdot', 'dotted']
def get_linestyle(v):
    if not v in seen:
        seen.append(v)
    return lss[seen.index(v) % len(lss)]


client_labels = ['kafka-python', 'pykafka', 'confluent-kafka', 'java client']


def aggregate_data(data, type=None, client=None, version=None, partitions=None, acks=None):
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

        if type == None:
            k.append(key.Type)
        else:
            if key.Type != type:
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

    return (mbs, msgs)


def millions(x, pos):
    'The two args are the value and tick position'
    return '%1.0fk' % (x*1e-3)
formatter = FuncFormatter(millions)


def make_plot_qualitative_p(data):
    f, a = plt.subplots(2, 4)
    for i in range(4):
        a[1, i].set_xlabel('Message Size (bytes)')
        a[0, 0].set_ylabel('Mb Per Second')
        a[1, 0].set_ylabel('Msgs Per Second')
        a[1, i].yaxis.set_major_formatter(formatter)

    a[0, 0].set_title('kafka-python')
    a[0, 1].set_title('pykafka')
    a[0, 2].set_title('confluent-kafka')
    a[0, 3].set_title('java')

    for i in range(len(data)):
        mbs = data[i][0]
        msgs = data[i][1]

        for key in mbs:
            xs = list(map(lambda x: x[0], mbs[key]))
            ys = list(map(lambda x: x[1], mbs[key]))
            ys2 = list(map(lambda x: x[1], msgs[key]))

            a[0, i].plot(
                xs, ys, 
                color=get_color(key[1]), 
                label=key, 
                linestyle=get_linestyle(key[0]))

            a[1, i].plot(
                xs, ys2, 
                color=get_color(key[1]), 
                label=key, 
                linestyle=get_linestyle(key[0]))

        a[0, i].set_ylim(bottom=0)
        a[1, i].set_ylim(bottom=0)

    a[0, 0].legend()
    f.tight_layout()
    plt.subplots_adjust( wspace=0.3 )
    plt.show()

def make_plot_version_diff(p_data, c_data):
    f, a = plt.subplots(2, 4)
    for i in range(4):
        a[1, i].set_xlabel('Message Size (bytes)')
        a[0, 0].set_ylabel('Mb Per Second (produce)')
        a[1, 0].set_ylabel('Mb Per Second (consume)')

    a[0, 0].set_title('kafka-python')
    a[0, 1].set_title('pykafka')
    a[0, 2].set_title('confluent-kafka')
    a[0, 3].set_title('java')

    for i in range(len(p_data)):
        mbs_p = p_data[i][0]
        mbs_c = c_data[i][0]

        print(mbs_p)

        for key in mbs_p:
            xs = list(map(lambda x: x[0], mbs_p[key]))
            ys = list(map(lambda x: x[1], mbs_p[key]))
            ys2 = list(map(lambda x: x[1], mbs_c[key]))

            a[0, i].plot(
                xs, ys, 
                color=get_color(key[0]), 
                label=key)

            a[1, i].plot(
                xs, ys2, 
                color=get_color(key[0]), 
                label=key)

        a[0, i].set_ylim(bottom=0)
        a[1, i].set_ylim(bottom=0)

    a[0, 0].legend()
    f.tight_layout()
    plt.subplots_adjust( wspace=0.3 )
    plt.show()


def make_plot_qualitative_c(data):
    f, a = plt.subplots(2, 4)
    for i in range(4):
        a[1, i].set_xlabel('Message Size (bytes)')
        a[0, 0].set_ylabel('Mb Per Second')
        a[1, 0].set_ylabel('Msgs Per Second')
        a[1, i].yaxis.set_major_formatter(formatter)

    a[0, 0].set_title('kafka-python')
    a[0, 1].set_title('pykafka')
    a[0, 2].set_title('confluent-kafka')
    a[0, 3].set_title('java')

    for i in range(len(data)):
        mbs = data[i][0]
        msgs = data[i][1]

        for key in mbs:
            xs = list(map(lambda x: x[0], mbs[key]))
            ys = list(map(lambda x: x[1], mbs[key]))
            ys2 = list(map(lambda x: x[1], msgs[key]))

            a[0, i].plot(
                xs, ys, 
                color=get_color(key[0]), 
                label=key)

            a[1, i].plot(
                xs, ys2, 
                color=get_color(key[0]), 
                label=key)

        a[0, i].set_ylim(bottom=0)
        a[1, i].set_ylim(bottom=0)

    a[0, 0].legend()
    f.tight_layout()
    plt.subplots_adjust( wspace=0.3 )
    plt.show()


def make_plot_p_comparison(data):
    f, a = plt.subplots(1, 2)

    a[0].set_xlabel('Message Size (bytes)')
    a[1].set_xlabel('Message Size (bytes)')
    a[0].set_ylabel('Mb per Second')
    a[1].set_ylabel('Msgs per Second')

    key = ('1', '3')
    for i in range(len(data)):
        mbs = data[i][0][key]
        msgs = data[i][1][key]

        xs = list(map(lambda x: x[0], mbs))
        ys = list(map(lambda x: x[1], mbs))
        ys2 = list(map(lambda x: x[1], msgs))

        a[0].plot(
            xs, ys, 
            color=get_color2(i), 
            label=client_labels[i],
            linestyle=get_linestyle(key[0]))

        a[1].plot(
            xs, ys2,
            color=get_color2(i), 
            label=client_labels[i], 
            linestyle=get_linestyle(key[0]))
    
    a[0].set_ylim(bottom=0)
    a[1].set_ylim(bottom=0)
    a[1].yaxis.set_major_formatter(formatter)

    a[0].legend(bbox_to_anchor=(1.8, -0.15, 0.01, 0.01), ncol=4)

    f.tight_layout()
    f.subplots_adjust(bottom=0.2)

    plt.show()


def make_plot_c_comparison(data):
    f, a = plt.subplots(1, 2)

    a[0].set_xlabel('Message Size (bytes)')
    a[1].set_xlabel('Message Size (bytes)')
    a[0].set_ylabel('Mb per Second')
    a[1].set_ylabel('Msgs per Second')

    key = ('3', )
    for i in range(len(data)):
        mbs = data[i][0][key]
        msgs = data[i][1][key]

        xs = list(map(lambda x: x[0], mbs))
        ys = list(map(lambda x: x[1], mbs))
        ys2 = list(map(lambda x: x[1], msgs))

        a[0].plot(
            xs, ys, 
            color=get_color2(i), 
            label=client_labels[i], 
            linestyle=get_linestyle(key[0]))

        a[1].plot(
            xs, ys2,
            color=get_color2(i), 
            label=client_labels[i], 
            linestyle=get_linestyle(key[0]))
    
    a[0].set_ylim(bottom=0)
    a[1].set_ylim(bottom=0)
    a[1].yaxis.set_major_formatter(formatter)

    a[0].legend(bbox_to_anchor=(1.8, -0.15, 0.01, 0.01), ncol=4)

    f.tight_layout()
    f.subplots_adjust(bottom=0.2)

    plt.show()


d_k = [
    read_data("results-kafka-python.csv"),
    read_data("results-pykafka.csv"),
    read_data("results-confluent-kafka.csv"),
    read_data("results-java.csv")
]

p_k = aggregate_data(d_k[0], type="P", version='3.3.0', client='K')
p_p = aggregate_data(d_k[1], type='P', version='3.3.0', client='P')
p_c = aggregate_data(d_k[2], type="P", version='3.3.0', client='C')
p_j = aggregate_data(d_k[3], type='P', version='3.3.0', client='J')
p_data = [p_k, p_p, p_c, p_j]
#make_plot_qualitative_p(p_data)
#make_plot_p_comparison(p_data)

c_k = aggregate_data(d_k[0], type="C", version='3.3.0', client='K', acks='-')
c_p = aggregate_data(d_k[1], type='C', version='3.3.0', client='P', acks='-')
c_c = aggregate_data(d_k[2], type="C", version='3.3.0', client='C', acks='-')
c_j = aggregate_data(d_k[3], type='C', version='3.3.0', client='J', acks='-')
c_data = [c_k, c_p, c_c, c_j]
#make_plot_qualitative_c(c_data)
#make_plot_c_comparison(c_data)


make_plot_version_diff(
    [
        aggregate_data(d_k[0], type="P", client='K', acks='1', partitions='3'),
        aggregate_data(d_k[1], type="P", client='P', acks='1', partitions='3'),
        aggregate_data(d_k[2], type="P", client='C', acks='1', partitions='3'),
        aggregate_data(d_k[3], type="P", client='J', acks='1', partitions='3')
    ], 
    [
        aggregate_data(d_k[0], type="C", client='K', acks='-', partitions='3'),
        aggregate_data(d_k[1], type="C", client='P', acks='-', partitions='3'),
        aggregate_data(d_k[2], type="C", client='C', acks='-', partitions='3'),
        aggregate_data(d_k[3], type="C", client='J', acks='-', partitions='3')
    ]
)
