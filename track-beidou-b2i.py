#!/usr/bin/env python

import sys
import numpy as np

import gnsstools.beidou.b1i as b1i
import gnsstools.nco as nco
import gnsstools.io as io
import gnsstools.discriminator as discriminator

class tracking_state:
  def __init__(self,fs,prn,code_p,code_f,code_i,carrier_p,carrier_f,carrier_i,mode):
    self.fs = fs
    self.prn = prn
    self.code_p = code_p
    self.code_f = code_f
    self.code_i = code_i
    self.carrier_p = carrier_p
    self.carrier_f = carrier_f
    self.carrier_i = carrier_i
    self.mode = mode
    self.prompt1 = 0 + 0*(1j)
    self.carrier_e1 = 0
    self.code_e1 = 0
    self.eml = 0

# tracking loops

def track(x,s):
  n = len(x)
  fs = s.fs

  nco.mix(x,-s.carrier_f/fs, s.carrier_p)
  s.carrier_p = s.carrier_p - n*s.carrier_f/fs
  s.carrier_p = np.mod(s.carrier_p,1)

  cf = (s.code_f+s.carrier_f/589.424)/fs

  p_early = b1i.correlate(x, s.prn, 0, s.code_p-0.5, cf, b1i.b1i_code(prn))
  p_prompt = b1i.correlate(x, s.prn, 0, s.code_p, cf, b1i.b1i_code(prn))
  p_late = b1i.correlate(x, s.prn, 0, s.code_p+0.5, cf, b1i.b1i_code(prn))

  if s.mode=='FLL_WIDE':
    fll_k = 2.0
    a = p_prompt
    b = s.prompt1
    e = discriminator.fll_atan(a,b)
    s.carrier_f = s.carrier_f + fll_k*e
    s.prompt1 = p_prompt
  elif s.mode=='FLL_NARROW':
    fll_k = 0.3
    a = p_prompt
    b = s.prompt1
    e = discriminator.fll_atan(a,b)
    s.carrier_f = s.carrier_f + fll_k*e
    s.prompt1 = p_prompt
  elif s.mode=='PLL':
    pll_k1 = 0.1
    pll_k2 = 5.0
    e = discriminator.pll_costas(p_prompt)
    e1 = s.carrier_e1
    s.carrier_f = s.carrier_f + pll_k1*e + pll_k2*(e-e1)
    s.carrier_e1 = e

# code loop

  dll_k1 = 0.00002
  dll_k2 = 0.2
  s.early = np.absolute(p_early)
  s.prompt = np.absolute(p_prompt)
  s.late = np.absolute(p_late)
  if (s.late+s.early)==0:
    e = 0
  else:
    e = (s.late-s.early)/(s.late+s.early)
  s.eml = e
  e1 = s.code_e1
  s.code_f = s.code_f + dll_k1*e + dll_k2*(e-e1)
  s.code_e1 = e

  s.code_p = s.code_p + n*cf
  s.code_p = np.mod(s.code_p,b1i.code_length)

  return p_prompt,s

#
# main program
#

# parse command-line arguments
# example:
#   ./track-beidou-b2i.py /dev/stdin 68873142.857 -32576571.429 14 2600 238.5

filename = sys.argv[1]             # input data, raw file, i/q interleaved, 8 bit signed (two's complement)
fs = float(sys.argv[2])            # sampling rate, Hz
coffset = float(sys.argv[3])       # offset to B1 carrier, Hz (positive or negative)
prn = int(sys.argv[4])             # PRN code
doppler = float(sys.argv[5])       # initial doppler estimate from acquisition
code_offset = float(sys.argv[6])   # initial code offset from acquisition

fp = open(filename,"rb")

n = int(fs*0.001*((b1i.code_length-code_offset)/b1i.code_length))  # align with 1 ms code boundary
x = io.get_samples_complex(fp,n)
code_offset += n*1000.0*b1i.code_length/fs

s = tracking_state(fs=fs, prn=prn,                    # initialize tracking state
  code_p=code_offset, code_f=b1i.chip_rate, code_i=0,
  carrier_p=0, carrier_f=doppler, carrier_i=0,
  mode='FLL_WIDE')

block = 0
coffset_phase = 0.0

while True:
  if s.code_p<b1i.code_length/2:
    n = int(fs*0.001*(b1i.code_length-s.code_p)/b1i.code_length)
  else:
    n = int(fs*0.001*(2*b1i.code_length-s.code_p)/b1i.code_length)

  x = io.get_samples_complex(fp,n)
  if x==None:
    break

  nco.mix(x,-coffset/fs,coffset_phase)
  coffset_phase = coffset_phase - n*coffset/fs
  coffset_phase = np.mod(coffset_phase,1)

  p_prompt,s = track(x,s)
  print block, np.real(p_prompt), np.imag(p_prompt), s.carrier_f, s.code_f-b1i.chip_rate, (180/np.pi)*np.angle(p_prompt), s.early, s.prompt, s.late

  block = block + 1
#  if (block%100)==0:
#    sys.stderr.write("%d\n"%block)
  if block==1000:
    s.mode = 'FLL_NARROW'
  if block==2000:
    s.mode = 'PLL'
