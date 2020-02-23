#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr

SAMPLE_RATE_HZ = 44100
PPQN = 48
SECONDS_PER_MINUTE = 60

PRINT_WARNINGS = True


def fixed_to_unit_float(x):
  # Convert unsigned value to signed.
  if x & 0x80000000:
    x = x - 2**32
  # See: http://blog.bjornroche.com/2009/12/int-float-int-its-jungle-out-there.html
  return float(x + 2**31) / 2**32


def pulses_to_seconds(pulses, tempo):
  # Tempo is in units of quarter notes / minute.
  return ((pulses / float(PPQN)) / tempo) * SECONDS_PER_MINUTE


def unit_float_from_fixed_hex(x):
  return fixed_to_unit_float(int(x, 16))


def suffix_to_char(suffix):
  if suffix == -1:
    return ""

  return chr(ord('A') + int(suffix))


@attr.s
class ElementGetter(object):
  element = attr.ib()
  nag = attr.ib(default=True)
  _attribs_gotten = attr.ib(default=attr.Factory(set))
  _unused_attribs = attr.ib(default=attr.Factory(set), converter=set)

  def has_attrib(self, name):
    return name in self.element.attrib

  def get_any_attrib(self, names, converter=None, default=None):
    for name in names:
      if self.has_attrib(name):
        return self.get_attrib(name, converter, default)

    if default is None:
      raise KeyError("None of {} found in {}'s attrib: {}".format(
          names, self.element.tag, self.element.attrib))

    if converter is not None:
      return converter(default)

    return default

  def get_attrib(self, name, converter=None, default=None):
    self._attribs_gotten.add(name)

    v = None
    if name in self.element.attrib:
      v = self.element.attrib.get(name)
    elif default is not None:
      v = default
    else:
      raise KeyError("{} not found in attrib: {}".format(
          name, self.element.attrib))

    if converter is not None:
      return converter(v)
    return v

  def __enter__(self):
    self._attribs_gotten = set()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    for name in self.element.attrib:
      if name not in self._unused_attribs and name not in self._attribs_gotten and self.nag:
        print("Warning: Unused attrib on {}: {}".format(self.element.tag, name))
