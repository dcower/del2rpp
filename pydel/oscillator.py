#! /usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

import attr

from .util import ElementGetter, suffix_to_char

UNUSED_OSCILLATOR_ATTRIBS = []


@attr.s
class Oscillator(object):
  __metaclass__ = ABCMeta
  typ = attr.ib(type=str)

  @classmethod
  @abstractmethod
  def from_element(cls, element):
    with ElementGetter(element, nag=False) as e:
      typ = e.get_attrib("type", str, "")

      # TODO: Support FM (oscillator has no type).

      if typ == "sample":
        return SampleOscillator.from_element(element)
      else:
        print("Unsupported oscillator type: {}".format(typ))
        return Oscillator(typ=typ)


@attr.s
class SampleOscillator(Oscillator):
  file_path = attr.ib(default="")

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=UNUSED_OSCILLATOR_ATTRIBS) as e:
      sample_oscillator = SampleOscillator(
          typ=e.get_attrib("type", str),
          file_path=e.get_attrib("fileName", str, ""))

    # TODO: Parse zone.

    return sample_oscillator