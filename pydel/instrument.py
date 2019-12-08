#! /usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

import attr

from .util import ElementGetter, suffix_to_char

UNUSED_ATTRIBS = [
    "lpfMode",
    "voicePriority",
    "polyphonic",
    "transpose",
    "isArmedForRecording",
    "mode",
    "activeModFunction",
    "clippingAmount",
    "modFXType",
    "inputChannel",
    "currentFilterType",
    "modFXCurrentParam",
    "defaultVelocity",
]


@attr.s
class ClipInstance(object):
  # Start position and length, both in pulses (see PPQN).
  # E.g., start of 48 = 1 quarter note into the arranger.
  start = attr.ib()
  length = attr.ib()
  # Index into the list of clips.
  clip_idx = attr.ib()

  @classmethod
  def from_hex(cls, data):
    assert len(data) == 24

    return ClipInstance(
        start=int(data[0:8], 16),
        length=int(data[8:16], 16),
        clip_idx=int(data[16:24], 16),
    )


@attr.s
class Instrument(object):
  __metaclass__ = ABCMeta
  muted = attr.ib(type=bool)
  clip_instances = attr.ib(type=list)

  @abstractmethod
  def pretty_name(self):
    raise NotImplementedError

  @classmethod
  def _parse_clip_instances(cls, clip_instances_data):
    clip_instances = []

    # Remove 0x prefix.
    if len(clip_instances_data) >= 2 and clip_instances_data[:2] == "0x":
      clip_instances_data = clip_instances_data[2:]

    while clip_instances_data:
      clip_instances.append(ClipInstance.from_hex(clip_instances_data[0:24]))
      clip_instances_data = clip_instances_data[24:]

    return clip_instances


@attr.s
class AudioTrack(Instrument):
  name = attr.ib()

  def pretty_name(self):
    return self.name

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=UNUSED_ATTRIBS) as e:
      return AudioTrack(
          name=e.get_attrib("name"),
          muted=bool(e.get_attrib("isMutedInArrangement", int, 0)),
          clip_instances=Instrument._parse_clip_instances(
              e.get_attrib("clipInstances", str, "")))


@attr.s
class MidiChannel(Instrument):
  channel = attr.ib(type=int)
  suffix = attr.ib(type=str)

  def pretty_name(self):
    return "MIDI {}{}".format(self.channel + 1, self.suffix)

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=UNUSED_ATTRIBS) as e:
      return MidiChannel(
          channel=e.get_attrib("channel", int, 0),
          suffix=suffix_to_char(e.get_attrib("suffix", int, -1)),
          muted=bool(e.get_attrib("isMutedInArrangement", int, 0)),
          clip_instances=Instrument._parse_clip_instances(
              e.get_attrib("clipInstances", str, "")))


@attr.s
class CvChannel(Instrument):
  channel = attr.ib(type=int)
  suffix = attr.ib(type=str)

  def pretty_name(self):
    return "CV {}{}".format(self.channel + 1, self.suffix)

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=UNUSED_ATTRIBS) as e:
      return MidiChannel(
          channel=e.get_attrib("channel", int, 0),
          suffix=suffix_to_char(e.get_attrib("suffix", int, -1)),
          muted=bool(e.get_attrib("isMutedInArrangement", int, 0)),
          clip_instances=Instrument._parse_clip_instances(
              e.get_attrib("clipInstances", str, "")))


@attr.s
class Sound(Instrument):
  preset_slot = attr.ib()
  suffix = attr.ib()

  def pretty_name(self):
    return "Synth {}{}".format(self.preset_slot, self.suffix)

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=UNUSED_ATTRIBS) as e:
      return Sound(
          preset_slot=e.get_attrib("presetSlot", int, 0),
          suffix=suffix_to_char(e.get_attrib("presetSubSlot", int, -1)),
          muted=bool(e.get_attrib("isMutedInArrangement", int, 0)),
          clip_instances=Instrument._parse_clip_instances(
              e.get_attrib("clipInstances", str, "")))


@attr.s
class Kit(Instrument):
  preset_slot = attr.ib()
  suffix = attr.ib()

  def pretty_name(self):
    return "Kit {}{}".format(self.preset_slot, self.suffix)

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=UNUSED_ATTRIBS) as e:
      return Kit(
          preset_slot=e.get_attrib("presetSlot", int, 0),
          suffix=suffix_to_char(e.get_attrib("presetSubSlot", int, -1)),
          muted=bool(e.get_attrib("isMutedInArrangement", int, 0)),
          clip_instances=Instrument._parse_clip_instances(
              e.get_attrib("clipInstances", str, "")))
