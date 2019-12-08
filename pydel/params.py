#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr
from .util import ElementGetter, unit_float_from_fixed_hex


@attr.s
class Params(object):
  volume = attr.ib(default=1.0)
  pan = attr.ib(default=0.0)

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, nag=False) as e:
      return Params(
          volume=e.get_attrib("volume", unit_float_from_fixed_hex,
                              "0xE0000000"),
          pan=e.get_attrib("pan", unit_float_from_fixed_hex, "0x00000000") * 2.0
          - 1.0,
      )
