#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr

from .clip import AudioClip, InstrumentClip
from .instrument import AudioTrack, MidiChannel, CvChannel, Sound, Kit
from .util import ElementGetter, SAMPLE_RATE_HZ, PPQN, SECONDS_PER_MINUTE


@attr.s
class Project(object):
  tempo = attr.ib()
  instruments = attr.ib(factory=list)
  sections = attr.ib(factory=list)
  clips = attr.ib(factory=list)
  arrange_only_clips = attr.ib(factory=list)

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element) as e:
      deluge_project = Project(
          tempo=deluge_timer_to_tempo(
              e.get_attrib("timePerTimerTick", int),
              e.get_attrib("timerTickFraction", int)),
          instruments=e.get_child("instruments", Project._parse_instruments,
                                  []),
          sections=e.get_child("sections", Project._parse_sections, []),
          clips=e.get_child("sessionClips", Project._parse_clips, []),
          arrange_only_clips=e.get_child("arrangementOnlyTracks",
                                         Project._parse_clips, []))

    return deluge_project

  @staticmethod
  def _parse_instruments(element):
    with ElementGetter(element) as e:
      return e.get_any_children({
          "audioTrack": AudioTrack.from_element,
          "midiChannel": MidiChannel.from_element,
          "cvChannel": CvChannel.from_element,
          "sound": Sound.from_element,
          "kit": Kit.from_element,
      })

  @staticmethod
  def _parse_sections(element):
    # Ignore for now.
    return []

  @staticmethod
  def _parse_clips(element):
    with ElementGetter(element) as e:
      return e.get_any_children(
          {
              "audioClip": AudioClip.from_element,
              "instrumentClip": InstrumentClip.from_element,
          },
          # Append an empty clip to keep the instance indices in order.
          unknown_converter=lambda: None)


def deluge_timer_to_tempo(time_per_timer_tick, timer_tick_fraction):
  # Based on Downrush's calculation.
  # Get the tick fraction in floating point (0 = .0, 0xFFFFFFFF = .9999...)
  timer_tick_fraction = timer_tick_fraction / 0x100000000
  # How many samples are in each pulse.
  samples_per_pulse = time_per_timer_tick + timer_tick_fraction

  # Deluge uses 48 PPQN (pulses per quarter note), and a 44100Hz sampling rate.
  #
  # Example for 120 BPM:
  #  44100 samples     1 quarter note   60 seconds        1 pulse          120 quarter notes
  # --------------- * --------------- * ---------- * ------------------- = --------------------
  #    1 second          48 pulses       1 minute        459.375 samples       1 minute

  tempo = SAMPLE_RATE_HZ / PPQN * SECONDS_PER_MINUTE / samples_per_pulse

  return tempo
