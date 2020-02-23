#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import uuid
import xml.etree.ElementTree as ET

import rpp

try:
  from . import pydel
except:
  import pydel


def generate_guid():
  return "{" + str(uuid.uuid4()) + "}"


def color_to_reaper(color):
  return ((color.r << 16) | (color.g << 8) | color.b) | 0x1000000


def convert_notes_to_midi(channel, notes, clip_length, instance_length):
  notes = pydel.notes_to_on_off_notes(notes)

  # Sort by start pulse.
  notes.sort(key=lambda note: note.start)

  if pydel.condition_expansion_needed(notes):
    notes = pydel.condition_expand_notes(notes, clip_length, instance_length)
    # Update the clip length to reflect that it's been extended to the instance length.
    clip_length = instance_length

  midi_messages = []

  last_start = 0
  for note in notes:
    if note.velocity == 0:
      # Note off.
      ctrl = (0b1000 << 4) | channel
    else:
      # Note on.
      ctrl = (0b1001 << 4) | channel

    offset = note.start - last_start

    if note.muted:
      # Unselected, muted.
      command = "Em"
    else:
      # Unselected.
      command = "E"

    msg = [
        command,
        offset,
        hex(ctrl)[2:],
        hex(note.y)[2:],
        hex(note.velocity)[2:],
    ]

    last_start = note.start
    midi_messages.append(msg)

  # Append a final "note off" message to make the clip the correct length.
  offset = clip_length - last_start
  msg = [
      "E",  # Unselected.
      offset,
      hex(0xb0)[2:],
      hex(0x7b)[2:],
      hex(0x00)[2:],
  ]
  midi_messages.append(msg)

  return midi_messages


def clip_instance_to_reaper_item(clip_instance,
                                 clip,
                                 pretty_clip_idx,
                                 reaper_source,
                                 tempo,
                                 additional_children=None):
  if additional_children is None:
    additional_children = []

  color = color_to_reaper(pydel.section_to_color(clip.section))
  volume = clip.params.volume
  pan = clip.params.pan

  start_in_seconds = pydel.pulses_to_seconds(clip_instance.start, tempo)
  length_in_seconds = pydel.pulses_to_seconds(clip_instance.length, tempo)

  return rpp.Element(
      tag="ITEM",
      attrib=[],
      children=[
          ["POSITION", start_in_seconds],
          ["LENGTH", length_in_seconds],
          ["LOOP", 1],
          # Item GUID.
          ["IGUID", generate_guid()],
          # First take GUID.
          ["GUID", generate_guid()],
          ["NAME", "Clip {}".format(pretty_clip_idx)],
          ["VOLPAN", volume, pan],
          ["COLOR", color, "B"],
          # I think this is a no-op?
          ["POOLCOLOR", color, "B"],
          reaper_source,
      ] + additional_children)


def audio_clip_to_reaper_source(clip, path_prefix, tempo):
  file_path = clip.file_path

  # TODO. Hack to point to the right file (thanks to collect?).
  #file_path = "/Users/dcower/Downloads/bug1/Bug1/" + file_path[8:].replace("/", "_")
  file_path = os.path.join(path_prefix, file_path)

  reaper_source_wave = rpp.Element(
      tag="SOURCE", attrib=["WAVE"], children=[
          ["FILE", file_path],
      ])

  # The length of the stored selected audio sample (the chunk between the start and end sample
  # positions).
  sample_length_seconds = (clip.end_sample_pos - clip.start_sample_pos) / float(
      pydel.SAMPLE_RATE_HZ)
  # The actual length of the audio *clip*.
  clip_length_seconds = pydel.pulses_to_seconds(clip.length, tempo)
  playback_rate = sample_length_seconds / clip_length_seconds

  # TODO: Should we round playback rate and clip length to get nicer numbers?
  # playback_rate = round(playback_rate, 4)

  reaper_source_additional_children = [[
      "PLAYRATE",
      playback_rate,
      # 1 = Preserve pitch when changing rate.
      int(clip.pitch_speed_independent),
      # float, pitch adjust, in semitones.cents
      clip.transpose,
      # Default pitch shift mode.
      -1,
      # ?
      0,
      # ?
      0.0025,
  ]]

  section_children = [
      ["STARTPOS", clip.start_sample_pos / float(pydel.SAMPLE_RATE_HZ)],
      ["LENGTH", sample_length_seconds],
  ]

  if clip.reversed:
    section_children.append(["MODE", 2])

  section_children.append(reaper_source_wave)

  reaper_source_section = rpp.Element(
      tag="SOURCE", attrib=["SECTION"], children=section_children)

  return reaper_source_section, reaper_source_additional_children


# TODO: Get rid of this...?
class ReaperMidiPool(object):

  def __init__(self):
    return


def midi_clip_to_reaper_source(clip, clip_idx, length,
                               midi_clip_idx_to_reaper_midi_pool):
  midi_messages = convert_notes_to_midi(clip.channel, clip.notes, clip.length,
                                        length)

  # TODO: Move pooling into something else -- clip_idx shouldn't come into here.

  # TODO for MIDI pooling:
  # - If we have only condition codes >= 0x14, we can pool all instances and just create the largest
  #   instance.
  #   Right now, without this, if there are 2 instances *with condition codes* with different
  #   lengths, they will not be pooled.
  if (clip_idx in midi_clip_idx_to_reaper_midi_pool and
      midi_messages == midi_clip_idx_to_reaper_midi_pool[clip_idx].midi_messages
     ):
    reaper_midi_pool = midi_clip_idx_to_reaper_midi_pool[clip_idx]
    # Skip putting the MIDI data into the pool.
    midi_messages = []
  else:
    reaper_midi_pool = ReaperMidiPool()
    reaper_midi_pool.guid = generate_guid()
    reaper_midi_pool.pooledevts = generate_guid()
    reaper_midi_pool.midi_messages = midi_messages
    midi_clip_idx_to_reaper_midi_pool[clip_idx] = reaper_midi_pool

  return rpp.Element(
      tag="SOURCE",
      attrib=["MIDIPOOL"],
      children=[
          ["HASDATA", [1, pydel.PPQN, "QN"]],
          ["POOLEDEVTS", reaper_midi_pool.pooledevts],
          ["GUID", reaper_midi_pool.guid],
      ] + midi_messages)


def project_to_reaper_tracks(project, path_prefix):
  midi_clip_idx_to_reaper_midi_pool = {}
  reaper_tracks = []

  # Deluge instruments/tracks are stored bottom-to-top.
  for instrument in reversed(project.instruments):
    guid = generate_guid()

    reaper_items = []

    # TODO: Add unused clip instances to the end of the timeline.

    # Add the clip ("item" in REAPER) instances.
    for clip_instance in instrument.clip_instances:
      # Clip index is encoded as an arrange-only clip.
      # TODO: Deal with this as a clip-level abstraction?
      if clip_instance.clip_idx & 0x80000000:
        clip_idx = clip_instance.clip_idx - 0x80000000
        clip = project.arrange_only_clips[clip_idx]
        pretty_clip_idx = -clip_idx
      else:
        clip = project.clips[clip_instance.clip_idx]
        pretty_clip_idx = clip_instance.clip_idx

      reaper_item_additional_children = []

      if clip.has_audio():
        assert instrument.name == clip.track_name
        reaper_source, reaper_item_additional_children = audio_clip_to_reaper_source(
            clip, path_prefix, project.tempo)
      elif clip.has_midi():  # MIDI, synths, and kits.
        reaper_source = midi_clip_to_reaper_source(
            clip, clip_instance.clip_idx, clip_instance.length,
            midi_clip_idx_to_reaper_midi_pool)
      else:
        print("WARNING: Clip has neither audio nor MIDI")
        continue

      reaper_items.append(
          clip_instance_to_reaper_item(clip_instance, clip, pretty_clip_idx,
                                       reaper_source, project.tempo,
                                       reaper_item_additional_children))

    reaper_tracks.append(
        rpp.Element(
            tag="TRACK",
            attrib=[guid],
            children=[["NAME", instrument.pretty_name()], ["TRACKID", guid],
                      ["MUTESOLO", [int(instrument.muted), 0, 0]]] +
            reaper_items))

  return reaper_tracks


def convert(args):
  print("Converting {}".format(args.input_file.name))

  tree = ET.parse(args.input_file)
  root = tree.getroot()

  try:
    if root.tag != "song":
      print("ERROR: Root tag is not 'song'.")
      raise Error()
  except:
    print(
        "ERROR: Only songs from Deluge 3.x are supported. Try re-saving song using 3.x firmware."
    )
    return

  project = pydel.Project.from_element(root)

  # Prefix for file paths -- corresponds to root dir on Deluge SD card.
  input_dir = os.path.dirname(args.input_file.name)
  output_dir = os.path.dirname(args.output_file.name)
  # relpath doesn't handle empty input paths.
  if input_dir == "":
    input_dir = "./"
  path_prefix, songs = os.path.split(os.path.relpath(input_dir, output_dir))

  if songs != "SONGS":
    print(
        "WARNING: Expected song to be in SONGS/ directory. Audio clip paths may be incorrect."
    )
  # TODO: Support collect songs.

  reaper_project = rpp.Element(
      tag="REAPER_PROJECT",
      attrib=["0.1", "5.972/OSX64", "1372525904"],
      children=[
          ["RIPPLE", "0"],
          ["GROUPOVERRIDE", "0", "0", "0"],
          ["AUTOXFADE", "1"],
          ["TEMPO", project.tempo],
          ["PLAYRATE", 1, 0, 0.25, 4],
      ] + project_to_reaper_tracks(project, path_prefix))

  # TODO: Add markers + unused clips.

  rpp.dump(reaper_project, args.output_file)

  args.input_file.close()
  args.output_file.close()


def main():
  parser = argparse.ArgumentParser(
      description="Converts Synthstrom Audible Deluge songs (XML) to Reaper projects (RPP)."
  )

  parser.add_argument(
      "input_file",
      type=argparse.FileType("r"),
      help="input Deluge .XML song file")

  parser.add_argument(
      "output_file",
      nargs="?",
      type=argparse.FileType("w"),
      default="out.rpp",
      help="output Reaper .RPP project file")

  args = parser.parse_args()

  convert(args)


if __name__ == "__main__":
  main()
