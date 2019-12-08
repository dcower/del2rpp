#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr

from .clip import AudioClip, InstrumentClip
from .instrument import AudioTrack, MidiChannel, CvChannel, Sound, Kit
from .util import SAMPLE_RATE_HZ, PPQN, SECONDS_PER_MINUTE


@attr.s
class Project(object):
  tempo = attr.ib()
  instruments = attr.ib(default=[])
  sections = attr.ib(default=[])
  clips = attr.ib(default=[])
  arrange_only_clips = attr.ib(default=[])

  @classmethod
  def from_element(cls, element):
    deluge_project = Project(
        tempo=deluge_timer_to_tempo(
            int(element.attrib["timePerTimerTick"]),
            int(element.attrib["timerTickFraction"])))

    for child in element:
      if child.tag == "instruments":
        deluge_project.instruments = Project._parse_instruments(child)
      elif child.tag == "sections":
        deluge_project.sections = Project._parse_sections()
      elif child.tag == "sessionClips":
        deluge_project.clips = Project._parse_clips(child)
      elif child.tag == "arrangementOnlyTracks":
        deluge_project.arrange_only_clips = Project._parse_clips(child)
      elif child.tag in [
          "modeNotes", "reverb", "delay", "compressor", "songParams"
      ]:
        # Ignore for now.
        pass
      else:
        print("Unsupported song child: {}".format(child.tag))

    return deluge_project

  @classmethod
  def _parse_instruments(cls, element):
    instruments = []

    for child in element:
      if child.tag == "audioTrack":
        instruments.append(AudioTrack.from_element(child))
      elif child.tag == "midiChannel":
        instruments.append(MidiChannel.from_element(child))
      elif child.tag == "cvChannel":
        instruments.append(CvChannel.from_element(child))
      elif child.tag == "sound":
        instruments.append(Sound.from_element(child))
      elif child.tag == "kit":
        instruments.append(Kit.from_element(child))
      else:
        print("Unsupported instrument: {}".format(child.tag))

    return instruments

  @classmethod
  def _parse_sections(cls):
    # Ignore.
    return []

  @classmethod
  def _parse_clips(cls, element):
    clips = []

    for child in element:
      if child.tag == "audioClip":
        clips.append(AudioClip.from_element(child))
      elif child.tag == "instrumentClip":
        clips.append(InstrumentClip.from_element(child))
      else:
        print("Unsupported clip type: {}".format(child.tag))
        # Append an empty clip to keep the instance indices in order.
        clips.append(None)

    return clips


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
