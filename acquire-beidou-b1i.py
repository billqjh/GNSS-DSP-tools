#!/usr/bin/env python

import sys
import os
import numpy as np
import scipy.signal
import scipy.fftpack as fft

import gnsstools.beidou.b1i as b1i
import gnsstools.nco as nco
import gnsstools.io as io

#
# Acquisition search
#

def search(x,prn):
  fs = 8192000.0
  n = 8192                                         # 1 ms coherent integration
  incr = float(b1i.code_length)/n
  c = b1i.code(prn,0,0,incr,n)                     # obtain samples of the B1I code
  c = fft.fft(np.concatenate((c,np.zeros(n))))
  m_metric,m_code,m_doppler = 0,0,0
  for doppler in np.arange(-5000,5000,200):        # doppler bins
    q = np.zeros(2*n)
    w = nco.nco(-doppler/fs,0,2*n)
    for block in range(80):                        # 20 incoherent sums
      b = x[(block*n):((block+2)*n)]
      b = b*w
      r = fft.ifft(c*np.conj(fft.fft(b)))
      q = q + np.absolute(r)
    idx = np.argmax(q)
    if q[idx]>m_metric:
      m_metric = q[idx]
      m_code = b1i.code_length*(float(idx)/n)
      m_doppler = doppler
  m_code = m_code%b1i.code_length
  return m_metric,m_code,m_doppler

#
# main program
#

# parse command-line arguments
# example:
#   ./acquire-beidou-b1i.py data/gps-5001-l1_a.dat 68873142.857 -22984285.714

filename = sys.argv[1]        # input data, raw file, i/q interleaved, 8 bit signed (two's complement)
fs = float(sys.argv[2])       # sampling rate, Hz
coffset = float(sys.argv[3])  # offset to L1 BeiDou carrier, Hz (positive or negative)

# read first 85 ms of file

n = int(fs*0.085)
fp = open(filename,"rb")
x = io.get_samples_complex(fp,n)

# wipe off nominal offset from channel center to BeiDou B1 carrier

nco.mix(x,-coffset/fs,0)

# resample to 8.192 MHz

fsr = 8192000.0/fs
h = scipy.signal.firwin(161,3e6/(fs/2),window='hanning')
x = scipy.signal.filtfilt(h,[1],x)
xr = np.interp((1/fsr)*np.arange(85*8192),np.arange(len(x)),np.real(x))
xi = np.interp((1/fsr)*np.arange(85*8192),np.arange(len(x)),np.imag(x))
x = xr+(1j)*xi

# iterate over channels of interest

for prn in range(1,38):
#for prn in [1 2 3 4 5 6 7 8 9 10 11 12 13 14 30 31 32 33 34]:
  metric,code,doppler = search(x,prn)
  if metric>0.0:    # fixme: need a proper metric and threshold; and estimate cn0
    print('prn %2d doppler % 7.1f metric %7.1f code_offset %6.1f' % (prn,doppler,metric,code))
