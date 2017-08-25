import sys
import csv
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

DataKey = namedtuple(
  "DataKey",
  "Client, Type, Version, Partitions, Size, Acks, Compression, Security")

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
            k = DataKey(vs[0], vs[1], vs[2], vs[3], vs[4], vs[6], vs[7], vs[8])
            v = DataValue(vs[10], vs[11])
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

css2 = ["#0054F2", "#F2DE00", "#F20000", "#00F291", "#F200CE"]
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


client_labels = ['kafka-python', 'pykafka', 'pykafka-rdkafka', 'confluent-kafka', 'java client']


def aggregate_data(data, type=None, client=None, version=None, partitions=None, acks=None, compression=None, security=None):
    msgs = {}
    mbs = {}

    for key in data:
        size = int(float(key.Size))

        k = []

        # ignore anything that doesn't match criteria.

        if acks == None:
            k.append(key.Acks)
        else:
            if key.Acks != acks:
                continue

        if compression == None:
            k.append(key.Compression)
        else:
            if key.Compression != compression:
                continue

        if security == None:
            k.append(key.Security)
        else:
            if key.Security != security:
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

        msgs[k].append((size, max(msgsps)))
        mbs[k].append((size, max(mbsps)))

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
    a[0, 2].set_title('pykafka-rdkafka')
    a[0, 3].set_title('confluent-kafka')

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

    a[1, 0].legend(bbox_to_anchor=(2.0, -0.15, 0.01, 0.01), ncol=2)

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
    a[0, 2].set_title('pykafka-rdkafka')
    a[0, 3].set_title('confluent-kafka')

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

    a[0].legend(bbox_to_anchor=(2.0, -0.15, 0.01, 0.01), ncol=5)

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

    a[0].legend(bbox_to_anchor=(2.0, -0.15, 0.01, 0.01), ncol=5)

    f.tight_layout()
    f.subplots_adjust(bottom=0.2)

    plt.show()


d_k = [
    read_data("results-kafka-python.csv"),
    read_data("results-pykafka.csv"),
    read_data("results-pykafka-rdkafka.csv"),
    read_data("results-confluent-kafka.csv"),
    read_data("results-java.csv")
]

# retention policy.
# page cache on write.
# log compaction. 
#  - possible

p_k = aggregate_data(d_k[0], type='P', version='3.3.0', client='KafkaPython', compression='none', security='none')
p_p = aggregate_data(d_k[1], type='P', version='3.3.0', client='Pykafka', compression='none', security='none')
p_r = aggregate_data(d_k[2], type='P', version='3.3.0', client='PykafkaRd', compression='none', security='none')
p_c = aggregate_data(d_k[3], type='P', version='3.3.0', client='Confluent', compression='none', security='none')
p_j = aggregate_data(d_k[4], type='P', version='3.3.0', client='Java', compression='none', security='none')
p_data = [p_k, p_p, p_r, p_c, p_j]
make_plot_p_comparison(p_data)
#p_data = [p_k, p_p, p_r, p_c]
#make_plot_qualitative_p(p_data)
#exit(0)

c_k = aggregate_data(d_k[0], type="C", version='3.3.0', client='KafkaPython', acks='-', compression='none', security='none')
c_p = aggregate_data(d_k[1], type='C', version='3.3.0', client='Pykafka', acks='-', compression='none', security='none')
c_r = aggregate_data(d_k[2], type='C', version='3.3.0', client='PykafkaRd', acks='-', compression='none', security='none')
c_c = aggregate_data(d_k[3], type="C", version='3.3.0', client='Confluent', acks='-', compression='none', security='none')
c_j = aggregate_data(d_k[4], type='C', version='3.3.0', client='Java', acks='-', compression='none', security='none')
c_data = [c_k, c_p, c_r, c_c, c_j]
make_plot_c_comparison(c_data)
exit(0)
c_data = [c_k, c_p, c_r, c_c]
make_plot_qualitative_c(c_data)
exit(0)

make_plot_version_diff(
    [
        aggregate_data(d_k[0], type='P', client='K', acks='1', partitions='3'),
        aggregate_data(d_k[1], type='P', client='P', acks='1', partitions='3'),
        aggregate_data(d_k[2], type='P', client='R', acks='1', partitions='3'),
        aggregate_data(d_k[3], type='P', client='C', acks='1', partitions='3')
    ], 
    [
        aggregate_data(d_k[0], type='C', client='K', acks='-', partitions='3'),
        aggregate_data(d_k[1], type='C', client='P', acks='-', partitions='3'),
        aggregate_data(d_k[2], type='C', client='R', acks='-', partitions='3'),
        aggregate_data(d_k[3], type='C', client='C', acks='-', partitions='3')
    ]
)

