#! /usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import binascii
import uuid


def generate_guid():
  return "{" + str(uuid.uuid4()) + "}"


def color_to_reaper(color):
  return ((color.r << 16) | (color.g << 8) | color.b) | 0x1000000


def bytes_to_hex(b):
  return binascii.hexlify(bytearray(b)).decode("ascii")


def hex_to_base64(h):
  # Final encode() is to fix an infinite recursion in RPP.
  # RPP's encode_value function does not handle unicode type, which Python 2.x
  # gives this string without the additional encode().
  # TODO: Fix this properly.
  return base64.b64encode(bytearray.fromhex(h)).decode("ascii").encode("ascii")
