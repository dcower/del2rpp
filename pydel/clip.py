#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr

from .condition import Condition, add_complex_conditions
from .note import Note, NoteRow
from .params import Params
from .util import ElementGetter, suffix_to_char


@attr.s
class Clip(object):
  length = attr.ib()
  colour_offset = attr.ib()
  section = attr.ib(default=-1)
  params = attr.ib(default=attr.Factory(Params))

  def has_audio(self):
    return False

  def has_midi(self):
    return False


@attr.s
class AudioClip(Clip):
  track_name = attr.ib()
  file_path = attr.ib()
  start_sample_pos = attr.ib()
  end_sample_pos = attr.ib()
  pitch_speed_independent = attr.ib(default=1)
  reversed = attr.ib(default=0)
  transpose = attr.ib(default=0.0)
  section = attr.ib(default=-1)
  params = attr.ib(default=attr.Factory(Params))

  # TODO: Add method to get path on disk (or file handle?).

  def has_audio(self):
    return True

  @classmethod
  def from_element(cls, element):
    with ElementGetter(
        element,
        unused_attribs=[
            "isPlaying", "priority", "overdubsShouldCloneAudioTrack",
            "isArmedForRecording", "isSoloing", "affectEntire", "selected",
            "attack", "beingEdited"
        ]) as e:

      audio_clip = AudioClip(
          track_name=e.get_attrib("trackName"),
          file_path=e.get_attrib("filePath"),
          start_sample_pos=e.get_attrib("startSamplePos", int),
          end_sample_pos=e.get_attrib("endSamplePos", int),
          length=e.get_attrib("length", int),
          colour_offset=e.get_attrib("colourOffset", int, 0),
          section=e.get_attrib("section", int, -1),
          pitch_speed_independent=bool(
              e.get_attrib("pitchSpeedIndependent", int, 1)),
          reversed=bool(e.get_attrib("reversed", int, 0)),
          transpose=e.get_attrib("transpose", float, 0.0),
      )

    for child in element:
      if child.tag == "params":
        audio_clip.params = Params.from_element(child)
      else:
        print("Unsupported child tag in audioClip: {}".format(child.tag))

    return audio_clip


@attr.s
class InstrumentClip(Clip):
  channel = attr.ib()
  preset_name = attr.ib()
  # Also known as: MIDI channel, instrument preset slot, CV channel.
  preset_slot = attr.ib()
  suffix = attr.ib()
  notes = attr.ib(factory=list)
  section = attr.ib(default=-1)
  params = attr.ib(default=attr.Factory(Params))

  def has_midi(self):
    return True

  @classmethod
  def from_element(cls, element):
    with ElementGetter(
        element,
        unused_attribs=[
            "yScroll",
            "yScrollKeyboard",
            "isArmedForRecording",
            "isSoloing",
            "inKeyMode",
            "isPlaying",
            "onKeyboardScreen",
            "affectEntire",
            "selected",
            "beingEdited",
            # TODO: Support.
            "midiBank",
            "midiPGM",
        ]) as e:
      instrument_clip = InstrumentClip(
          channel=e.get_attrib("midiChannel", int, 0),
          preset_name=e.get_attrib("instrumentPresetName", str, ""),
          preset_slot=e.get_any_attrib([
              "midiChannel",
              "instrumentPresetSlot",
              "cvChannel",
          ], int, -1),
          suffix=suffix_to_char(
              e.get_any_attrib([
                  "midiChannelSuffix",
                  "instrumentPresetSubSlot",
                  "cvChannelSuffix",
              ], int, -1)),
          length=e.get_attrib("length", int),
          colour_offset=e.get_attrib("colourOffset", int, 0),
          # Not present for arrange-only clips.
          section=e.get_attrib("section", int, -1),
      )

      for child in element:
        if child.tag == "noteRows":
          instrument_clip.notes = InstrumentClip._note_rows_to_notes(
              InstrumentClip._parse_note_rows(child))
        elif child.tag == "soundParams":
          # Not supported yet -- ignore.
          pass
        elif child.tag == "kitParams":
          # Not supported yet -- ignore.
          pass
        elif child.tag == "arpeggiator":
          # Not supported yet -- ignore.
          pass
        elif child.tag == "midiParams":
          # Not supported yet -- ignore.
          pass
        else:
          print("Unsupported child in instrumentClip: {}".format(child.tag))

      return instrument_clip

  @staticmethod
  def _parse_note_rows(element):
    note_rows = []
    for child in element:
      if child.tag == "noteRow":
        note_rows.append(NoteRow.from_element(child))
      else:
        print("Unsupported child in noteRows: {}".format(child.tag))
    return note_rows

  @staticmethod
  def _note_rows_to_notes(note_rows):
    notes = []

    for note_row in note_rows:
      y = note_row.y

      for note_row_note in note_row.notes:
        condition = Condition.from_value(note_row_note.condition_value)
        notes.append(
            Note(y, note_row_note.start, note_row_note.length,
                 note_row_note.velocity, condition, note_row.muted))

    add_complex_conditions(notes)

    return notes
