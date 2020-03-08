#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import struct

from .util import generate_guid, bytes_to_hex, hex_to_base64

import rpp


def generate_sampler_plugin_data(path, note_start, note_end):
  note_start_hex = bytes_to_hex(struct.pack("<d", note_start / 127.0))
  note_end_hex = bytes_to_hex(struct.pack("<d", note_end / 127.0))
  data = bytes_to_hex(
      path.encode("utf-8")
  ) + "00000000000000f03f000000000000e03f000000000000f03f" + note_start_hex + note_end_hex + "9a9999999999b13fcdcccccccccceb3f00000000000000009a9999999999c93ffca9f1d24d62403ffca9f1d24d62403f000000000000000000000000000000000000000000000000000000000000f03f000000000000e03f010000000000000000000000000000000000f03f40000000555555555555c53fffffffff0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000000000000000000000000000000000000000cea421211a65903f000000000000f03ffca9f1d24d62303f0000000000000000"

  return hex_to_base64(data), len(data) // 2


def generate_sampler_plugin_vst(path, note_start, note_end):
  sampler_data, sampler_data_length = generate_sampler_plugin_data(
      path, note_start, note_end)
  vst_header = hex_to_base64(
      "6d6f7372ee5eedfe000000000200000001000000000000000200000000000000" +
      bytes_to_hex(struct.pack("<I", sampler_data_length)) + "0100000000001000")

  return rpp.Element(
      tag="VST",
      attrib=[
          "VSTi: ReaSamplOmatic5000 (Cockos)", "reasamplomatic.vst.dylib", 0,
          "", "1920167789<56535472736F6D72656173616D706C6F>", ""
      ],
      children=[
          [vst_header],
          [sampler_data],
          ["AAAQAAAA"],
      ])


def generate_sampler_fx_chain(paths_and_notes):
  vsts = []
  for path, note in paths_and_notes:
    vsts.append(generate_sampler_plugin_vst(path, note, note))

  return rpp.Element(
      tag="FXCHAIN", attrib=[], children=[
          ["BYPASS", 0, 0, 0],
      ] + vsts)


def generate_kit_fx_chain(kit, path_prefix):
  paths_and_notes = []
  for note, sound in enumerate(kit.sound_sources):
    for osc in sound.oscillators:
      if osc.typ == "sample" and osc.file_path:
        paths_and_notes.append((os.path.join(path_prefix, osc.file_path), note))

  return generate_sampler_fx_chain(paths_and_notes)


def generate_kit_sound_track(paths_and_notes):
  guid = generate_guid()

  fx_chain = generate_sampler_fx_chain(paths_and_notes)

  return rpp.Element(
      tag="TRACK",
      attrib=[guid],
      children=[["NAME", "kit bus"], ["TRACKID", guid], ["MUTESOLO", [0, 0, 0]]]
      + [fx_chain])


def generate_kit_bus_tracks(kit, path_prefix):
  # Container track: ISBUS 1 1
  # Last contained track: ISBUS 2 -1

  tracks = []
  for note, sound in enumerate(kit.sound_sources):
    paths_and_notes = []
    for osc in sound.oscillators:
      if osc.typ == "sample" and osc.file_path:
        paths_and_notes.append((os.path.join(path_prefix, osc.file_path), note))
    if len(paths_and_notes):
      tracks.append(generate_kit_sound_track(paths_and_notes))

  return tracks
