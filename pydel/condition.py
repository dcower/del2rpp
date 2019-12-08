#! /usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import itertools
import math
import random


def add_complex_conditions(notes):
  _add_stacked_note_conditions(notes)
  _add_dotted_note_conditions(notes)


class Condition(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def active(self, iteration):
    raise NotImplementedError

  @abstractmethod
  def static(self):
    raise NotImplementedError

  @classmethod
  def from_value(cls, x):
    assert 0x00 <= x <= 0xFF

    if x == 0x14:
      return NoCondition()
    if x & 0b10000000 or x < 0x14:
      return ProbabilityCondition.from_value(x)
    if x > 0x14 and x & 0b10000000 == 0:
      return IterationCondition.from_value(x)

    print("Unexpected condition value: {}".format(x))

    return NoCondition()


class NoCondition(Condition):
  """Condition for notes with *no* condition."""

  def __init__(self):
    return

  def active(self, iteration):
    return True

  def static(self):
    return True


class IterationCondition(Condition):
  """
  Condition for "X out of Y" conditions. E.g., trigger every 1 out of 2 iterations.
  """

  def __init__(self, numerator, denominator):
    self.numerator = numerator
    self.denominator = denominator

  def active(self, iteration):
    return (iteration % self.denominator) == (self.numerator - 1)

  def static(self):
    return False

  @classmethod
  def from_value(cls, x):
    assert x > 0x14
    # No high bit set.
    assert x & 0b10000000 == 0

    x = x - 0x14

    # Quadratic formula for (n * (n+1)) / 2 = x.
    denominator = math.floor((-1 + math.sqrt(1 + 8 * x)) / 2) + 1
    previous_base = ((denominator - 1) * (denominator)) // 2
    numerator = x - previous_base + 1

    return IterationCondition(numerator, denominator)


class ProbabilityCondition(Condition):
  """Condition for notes with probabilistic condition."""

  def __init__(self, probability, dotted):
    """Probability between 0 and 1."""
    self.probability = probability
    self.dotted = dotted

  def active(self, iteration):
    # E.g., if probability = 0.25 (25%), we want to return true 25% of the time.
    return random.random() <= self.probability

  def static(self):
    return False

  @classmethod
  def from_value(cls, x):
    assert x < 0x14 or x & 0b10000000

    dotted = bool(x & 0b10000000)
    # Remove high bit.
    x &= ~0b10000000

    probability = x / 20.0

    return ProbabilityCondition(probability, dotted)


class SharedProbabilityCondition(Condition):
  """
  Condition for:
    - Stacks of notes with the same probability, where all of the notes play or
      none at all.
    - Dotted notes, where a note will trigger based on another note.
  """

  def __init__(self, condition):
    self.condition = condition
    self.active_this_iteration = False
    self.last_iteration = -1

  # Must be called in order (notes sorted by start).
  def active(self, iteration):
    if iteration != self.last_iteration:
      self.last_iteration = iteration
      self.active_this_iteration = self.condition.active(iteration)

    return self.active_this_iteration

  def static(self):
    return False


class SingleNoteFromProbabilityStackCondition(Condition):
  """
  Condition for stacks of notes where probability adds up to 100%. One note from
  the stack will ever be sounded for each iteration.
  """

  def __init__(self, stack_size):
    self.stack_size = stack_size
    self.note_to_trigger_in_stack = -1
    self.current_note_in_stack = -1
    self.last_iteration = -1

  # Must be called in order (notes sorted by start, then y).
  def active(self, iteration):
    if iteration != self.last_iteration:
      self.note_to_trigger_in_stack = random.randint(0, self.stack_size - 1)
      self.current_note_in_stack = 0

    triggered = False
    if self.current_note_in_stack == self.note_to_trigger_in_stack:
      triggered = True

    self.current_note_in_stack = (self.current_note_in_stack + 1) % iteration

    return triggered

  def static(self):
    return False


class InverseCondition(Condition):
  """Condition which negates the given condition's result."""

  def __init__(self, condition):
    self.condition = condition

  def active(self, iteration):
    return not self.condition.active(iteration)

  def static(self):
    return self.condition.static()


# Handles notes at the same start time:
#  - If their probabilities add up to 100%, only play 1 of the notes.
#  - If the notes all have the same probability, always trigger together or not at all.
#    - If they add up to 100%, the logic above applies first.
def _add_stacked_note_conditions(notes):
  notes.sort(key=lambda note: (note.start, note.y))

  probability_notes = filter(
      lambda note: isinstance(note.condition, ProbabilityCondition), notes)

  # Group by start to iterate through stacks of notes.
  for _, note_stack in itertools.groupby(probability_notes,
                                         lambda note: note.start):
    note_stack = list(note_stack)
    if len(note_stack) <= 1:
      continue

    # If the notes' probabilities add up to 100%, only play 1 of the notes.
    summed_probabilities = sum(
        note.condition.probability for note in note_stack)

    if summed_probabilities == 1.0:
      print(
          "Warning: Not well-tested functionality. Stack of notes summed to 1.")
      condition = SingleNoteFromProbabilityStackCondition(len(note_stack))
      for note in note_stack:
        note.condition = condition
      continue

    # Do all the notes have the same probability?
    all_same_probability = all(
        note.condition.probability == note_stack[0].condition.probability
        for note in note_stack)

    if all_same_probability:
      print(
          "Warning: Not well-tested functionality. Stack of notes with same probability."
      )
      condition = SharedProbabilityCondition(note_stack[0].condition)
      for note in note_stack:
        note.condition = condition


# Handles dotted notes:
# - Trigger if the previous note with *same probability* was successfully triggered.
# - If probability is dotted and previous (1 - probability) note was *not* played, trigger.
def _add_dotted_note_conditions(notes):
  probability_notes = list(
      filter(lambda note: isinstance(note.condition, ProbabilityCondition),
             notes))
  probability_notes.sort(
      key=lambda note: (note.start, note.condition.probability))

  # Maps probability to lists of notes (sorted by start time).
  # Combines notes with complementary probabilities (e.g., 30% and 70%) together.
  probability_to_notes = {}
  for note in probability_notes:
    p = note.condition.probability
    if p > 0.5:
      p = 1.0 - p

    probability_to_notes.get(p, []).append(note)

  for p, notes_for_probability in probability_to_notes.items():
    q = 1.0 - p

    # TODO: Can dotted probability conditions be chained?
    # E.g.: 70% -> 70% -> 70% -> 70% -> 70%, and all only trigger if the first is triggered.
    # Latest non-dotted (base) note for the probability.
    latest_base_note_for_p = None
    # Latest non-dotted (base) note for the complementary probability:
    #   q = 1 - p.
    latest_base_note_for_q = None

    for note in notes_for_probability:
      note_p = note.condition.probability
      note_q = 1.0 - note_p

      if not note.dotted:
        if note_p == p:
          latest_base_note_for_p = note
        if note_q == q:
          latest_base_note_for_q = note
        continue

      # Otherwise, we have a dotted note.

      if (latest_base_note_for_p is not None and
          note_p == latest_base_note_for_p.condition.probability):
        # Note is dotted. Link it to the previous non-dotted note.
        print("Warning: Not well-tested functionality. Added dotted.")
        condition = SharedProbabilityCondition(latest_base_note_for_p.condition)
        latest_base_note_for_p.condition = condition
        note.condition = condition
      elif (latest_base_note_for_q is not None and
            note_q == latest_base_note_for_q.condition.probability):
        # Note is negative-dotted. Link it to the previous non-dotted complementary note.
        print(
            "Warning: Not well-tested functionality. Added dotted complementary."
        )
        condition = SharedProbabilityCondition(latest_base_note_for_q.condition)
        latest_base_note_for_q.condition = condition
        note.condition = InverseCondition(condition)
