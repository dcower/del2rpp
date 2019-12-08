#! /usr/bin/env python
# -*- coding: utf-8 -*-

import attr

from .condition import NoCondition
from .util import ElementGetter


def condition_expansion_needed(notes):
  """Determines whether expansion is needed; if not, don't expand."""

  return any(not note.condition.static() for note in notes)


def condition_expand_notes(notes, clip_length, instance_length):
  expanded_notes = []

  pos = 0
  note_idx = 0
  iteration = 0
  last_start = 0

  while pos < instance_length:
    note = notes[note_idx]

    note_idx = (note_idx + 1) % len(notes)
    pos += note.start - last_start

    if note.condition.active(iteration):
      expanded_notes.append(
          Note(note.y, pos, note.length, note.velocity, NoCondition(),
               note.muted))

    if note_idx == 0:
      last_start = 0
      iteration += 1
      # Round to the next iteration's start point.
      pos = clip_length * iteration
    else:
      last_start = note.start

  return expanded_notes


def notes_to_on_off_notes(notes):
  """
  Converts from a list of notes denoting start and length to a list of notes denoting
  on (velocity >= 0) and off (velocity = 0).
  """
  on_off_notes = []

  for note in notes:
    # Note on.
    on_off_notes.append(
        Note(note.y, note.start, 0, note.velocity, note.condition, note.muted))
    # Note off.
    on_off_notes.append(
        Note(note.y, note.start + note.length, 0, 0, note.condition,
             note.muted))

  return on_off_notes


@attr.s
class Note(object):
  y = attr.ib()
  start = attr.ib()
  length = attr.ib()
  velocity = attr.ib()
  condition = attr.ib()
  muted = attr.ib()


@attr.s
class NoteRowNote(object):
  start = attr.ib()
  length = attr.ib()
  velocity = attr.ib()
  condition_value = attr.ib()

  @classmethod
  def from_hex(cls, data):
    assert len(data) == 20

    return NoteRowNote(
        # Start position and length, both in pulses (see PPQN).
        # E.g., start of 48 = 1 quarter note into the arranger.
        start=int(data[0:8], 16),
        length=int(data[8:16], 16),
        velocity=int(data[16:18], 16),
        condition_value=int(data[18:20], 16),
    )


@attr.s
class NoteRow(object):
  y = attr.ib()
  muted = attr.ib()
  notes = attr.ib()

  @classmethod
  def from_element(cls, element):
    with ElementGetter(element, unused_attribs=["colourOffset"]) as e:
      return NoteRow(
          y=e.get_attrib("drumIndex" if e.has_attrib("drumIndex") else "y",
                         int),
          muted=bool(e.get_attrib("muted", int, 0)),
          notes=NoteRow._parse_note_data(e.get_attrib("noteData", str, "")),
      )

  @staticmethod
  def _parse_note_data(note_data):
    notes = []

    # Remove 0x prefix.
    if len(note_data) >= 2 and note_data[:2] == "0x":
      note_data = note_data[2:]

    while note_data:
      notes.append(NoteRowNote.from_hex(note_data[0:20]))
      note_data = note_data[20:]

    return notes
