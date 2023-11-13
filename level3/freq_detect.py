# import ahrs.filters.complementary.Complementary
import json
from numpy.fft import fft
from scipy import fftpack

import numpy as np
import math

import matplotlib.pyplot as plt

from scipy.signal import filtfilt, butter

from ahrs.filters import Mahony, Madgwick
from ahrs.common.quaternion import Quaternion

BASE_DIR = '''/Users/encore/sandbox/wangyao/zsj1/'''
CAPTION_PREFIX = 'zsj1'


def load_mock(f=1):
    t = [i*0.2 for i in range(0,4501)]
    x = [math.sin(f*ti*2.0*3.14159) for ti in t]
    return t,x


def get_acc_mock_data():
    t, x = load_mock(0.1)
    _, y = load_mock(0.2)
    _, z = load_mock(0.05)
    return t, np.stack((x, y, z)).transpose()*9.8

def load_file(fn):
    f = json.load(open(fn))
    t = [float(i[0]) - f[0][0] for i in f]
    x = [float(i[1]) for i in f]
    return t, x


def do_fft(x, fs):
    W = fs * 2400
    x = x[:W]
    hann = np.hanning(len(x))
    hamm = np.hamming(len(x))
    black = np.blackman(len(x))

    s = x

    X = fftpack.fft(s)
    freqs = fftpack.fftfreq(len(s),1/fs)
    return freqs, X


def get_gyro_data():
    fnx = BASE_DIR + 'gx.json'
    fny = BASE_DIR + 'gy.json'
    fnz = BASE_DIR + 'gz.json'
    t, x = load_file(fnx)
    _, y = load_file(fny)
    _, z = load_file(fnz)
    return t, np.stack((x, y, z)).transpose()


def get_acc_data():
    fnx = BASE_DIR + 'ax.json'
    fny = BASE_DIR + 'ay.json'
    fnz = BASE_DIR + 'az.json'
    t, x = load_file(fnx)
    _, y = load_file(fny)
    _, z = load_file(fnz)
    x = x - np.average(x)
    x = abs(x)
    y = y - np.average(y)
    y = abs(y)
    z = z - np.average(z)
    z = abs(z)
    return t, np.stack((x, y, z)).transpose()*9.8

def get_fs(t):
    fs = round(1/(t[1]-t[0]))
    return fs


if __name__ == '__main__':
    # t, acc_data = get_acc_mock_data()
    t, acc_data = get_acc_data()
    _, gyro_data = get_gyro_data()

    fs = get_fs(t)
    print("sampling rate: %s Hz" % fs)

    _, ax = plt.subplots()
    ax.plot(t, acc_data[:,2])
    ax.set_xlabel('Time [s]')
    ax.set_ylabel(CAPTION_PREFIX + ' Acc Signal amplitude')

    _, ax = plt.subplots()
    ax.plot(t, gyro_data)
    ax.set_xlabel('Time [s]')
    ax.set_ylabel(CAPTION_PREFIX + ' Gyro Signal amplitude')

    #
    for i in range(0,3):
        x = acc_data[:,i]
        print(x)
        freqs, X = do_fft(x, fs)
        _, ax = plt.subplots()
        ax.stem(freqs, np.abs(X))
        ax.set_xlabel('Frequency in Hertz [Hz]')
        ax.set_ylabel(CAPTION_PREFIX + ' Acc Spectrum Magnitude ' + str(i+1))
        ax.set_xlim(-fs / 2, fs / 2)
        plt.savefig(CAPTION_PREFIX + '_acc_spec_' + str(i+1) + '.png')

    for i in range(0, 3):
        x = gyro_data[:, i]
        print(x)
        freqs, X = do_fft(x, fs)
        _, ax = plt.subplots()
        ax.stem(freqs, np.abs(X))
        ax.set_xlabel('Frequency in Hertz [Hz]')
        ax.set_ylabel(CAPTION_PREFIX + ' Gyro Spectrum Magnitude ' + str(i+1))
        ax.set_xlim(-fs / 2, fs / 2)
        plt.savefig(CAPTION_PREFIX + '_gyro_spec_' + str(i+1) + '.png')
    plt.show()
    #
    # orientation = Mahony(gyr=gyro_data, acc=acc_data)  # Using IMU
    # att = [Quaternion(q).to_angles() / 3.141592 * 180.0 for q in orientation.Q]
    # att = np.array(att)
    # fig, ax = plt.subplots()
    # ax.plot(t, att[:, 0])
    # ax.set_xlabel('Time [s]')
    # ax.set_ylabel('Rotation[deg]')
    # fig, ax = plt.subplots()
    # ax.plot(t, att[:, 1])
    # ax.set_xlabel('Time [s]')
    # ax.set_ylabel('Pitch[deg]')
    # fig, ax = plt.subplots()
    # ax.plot(t, att[:, 2])
    # ax.set_xlabel('Time [s]')
    # ax.set_ylabel('Yaw[deg]')
    # plt.show()
