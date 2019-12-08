#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr


@attr.s
class Color(object):
  r = attr.ib()
  g = attr.ib()
  b = attr.ib()


def section_to_color(section):
  if section == -1:
    return Color(255, 255, 255)

  section_colors = [
      Color(96, 192, 255),  # Light blue.
      Color(255, 64, 255),  # Light pink.
      Color(255, 192, 64),  # Light yellow.
      Color(96, 255, 192),  # Light ~seafoam~.
      Color(255, 0, 0),  # Red.
      Color(192, 255, 96),  # Greenish yellow.
      Color(0, 0, 255),  # blu.
      Color(255, 96, 0),  # Orange.
      Color(96, 96, 255),  # Blue again.
      Color(96, 255, 0),  # Green.
      Color(96, 255, 96),  # Green again.
      Color(128, 64, 255),  # Purple.
  ]
  return section_colors[section % 12]
