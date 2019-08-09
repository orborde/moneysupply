#! /usr/bin/env python3

from typing import *

SELFSITTING='selfsitting'
BABYSITTING='babysitting'
BABYSAT='babysat'
CRISIS='crisis'

CRISIS_PROBABILITY=0.1
CRISIS_FAIL_UTILITY = -100

import collections

State = collections.namedtuple('State', ['flavor', 'scrip'])

def reset(pop: Dict[State, int]) -> Dict[State, int]:
    """
    >>> reset({State(CRISIS,1):10, State(BABYSAT,1):20})
    {State(flavor='selfsitting', scrip=1): 30}
    """
    new_pop = collections.defaultdict(int)
    for s,ct in pop.items():
        s2 = State(flavor=SELFSITTING, scrip=s.scrip)
        new_pop[s2] += ct
    return dict(new_pop)

def induce_crisis(pop):
    assert all(s.flavor == SELFSITTING for s in pop.keys())
    new_pop = collections.defaultdict(int)
    for s,ct in pop.items():
        crisis_ct = int(ct * CRISIS_PROBABILITY)
        ok_ct = ct - crisis_ct
        new_pop[State(CRISIS, s.scrip)] += crisis_ct
        new_pop[State(SELFSITTING, s.scrip)] += ok_ct
    return new_pop

def resolve(pop: Dict[State, int]) -> (int, Dict[State, int]):
    utility = 0
    for s in pop:
        if s.flavor == CRISIS:
            utility += pop[s] * CRISIS_FAIL_UTILITY

    return utility, reset(pop)

def gods_own_babysitting(pop):
    initial_size = sum(pop.values())

    # Collect all the populations in crisis.
    crisis_groups = [s for s in pop.keys() if s.flavor == CRISIS]

    # Find potential sitters. Try to select the poorest ones first.
    sitter_groups = [s for s in pop.keys() if s.flavor != CRISIS]
    sitter_groups.sort(key=lambda s: s.scrip)

    paired_pop = collections.defaultdict(int)
    while len(crisis_groups) > 0 and len(sitter_groups) > 0:
        cg = crisis_groups[0]
        sg = sitter_groups[0]

        if pop[cg] == 0:
            crisis_groups.pop(0)
            continue

        if pop[sg] == 0:
            sitter_groups.pop(0)
            continue

        if cg.scrip == 0:
            crisis_groups.pop(0)
            continue

        pairing_size = min(pop[cg], pop[sg])
        cg2 = State(flavor=BABYSAT,     scrip=cg.scrip-1)
        sg2 = State(flavor=BABYSITTING, scrip=sg.scrip+1)

        paired_pop[cg2] += pairing_size
        paired_pop[sg2] += pairing_size

        pop[cg] -= pairing_size
        pop[sg] -= pairing_size

    states = set(pop.keys()).union(set(paired_pop.keys()))
    new_pop = {x: (pop[x] + paired_pop[x]) for x in states}

    final_size = sum(new_pop.values())
    assert initial_size == final_size

    return new_pop


import doctest
assert doctest.testmod().failed == 0

population = {
    State(SELFSITTING, 1): 10000,
}

for turn in range(10):
    cpop = induce_crisis(population)
    ppop = gods_own_babysitting(cpop)
    utility, population = resolve(ppop)
    print(turn, utility, {s.scrip: ct for s,ct in population.items()})
