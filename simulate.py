#! /usr/bin/env python3

from typing import *

SELFSITTING='selfsitting'
BABYSITTING='babysitting'
BABYSAT='babysat'
CRISIS='crisis'

CRISIS_PROBABILITY=0.1
CRISIS_FAIL_UTILITY = -100

import collections
import copy

State = collections.namedtuple('State', ['flavor', 'scrip'])
Command = collections.namedtuple('Command', ['babysitter', 'recipient', 'size'])

def reset(pop: Dict[State, int]) -> Dict[State, int]:
    """
    >>> reset({State(CRISIS,1):10, State(BABYSAT,1):20})
    {State(flavor='selfsitting', scrip=1): 30}
    """
    new_pop: Dict[State, int] = collections.defaultdict(int)
    for s,ct in pop.items():
        s2 = State(flavor=SELFSITTING, scrip=s.scrip)
        new_pop[s2] += ct
    return dict(new_pop)

def induce_crisis(pop: Dict[State, int]):
    assert all(s.flavor == SELFSITTING for s in pop.keys())
    new_pop: Dict[State, int] = collections.defaultdict(int)
    for s,ct in pop.items():
        crisis_ct = int(ct * CRISIS_PROBABILITY)
        ok_ct = ct - crisis_ct
        new_pop[State(CRISIS, s.scrip)] += crisis_ct
        new_pop[State(SELFSITTING, s.scrip)] += ok_ct
    return new_pop

def resolve(pop: Dict[State, int]) -> Tuple[int, Dict[State, int]]:
    utility = 0
    for s in pop:
        if s.flavor == CRISIS:
            utility += pop[s] * CRISIS_FAIL_UTILITY

    return utility, reset(pop)

def execute(pop: Dict[State, int], commands: List[Command]) -> Dict[State, int]:
    initial_size = sum(pop.values())

    new_pop = copy.deepcopy(pop)

    for cmd in commands:
        assert cmd.babysitter.flavor == SELFSITTING
        assert cmd.recipient.flavor in [SELFSITTING, CRISIS]
        assert pop[cmd.babysitter] >= cmd.size
        assert pop[cmd.recipient] >= cmd.size
        assert cmd.recipient.scrip > 0

        bs2 = State(flavor=BABYSITTING, scrip=cmd.babysitter.scrip+1)
        rs2 = State(flavor=BABYSAT,     scrip=cmd.recipient.scrip-1)

        new_pop[cmd.babysitter] -= cmd.size
        new_pop[cmd.recipient]  -= cmd.size

        new_pop[bs2] += cmd.size
        new_pop[rs2] += cmd.size

    final_size = sum(new_pop.values())
    assert initial_size == final_size

    return new_pop

def cover_crises(pop: Dict[State, int]) -> List[Command]:
    # Collect all the populations in crisis.
    crisis_groups = [s for s in pop.keys() if s.flavor == CRISIS]

    # Find potential sitters. Try to select the poorest ones first.
    sitter_groups = [s for s in pop.keys() if s.flavor != CRISIS]
    sitter_groups.sort(key=lambda s: s.scrip)

    cmds = []
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
        cmds.append(Command(
            babysitter=sg,
            recipient=cg,
            size=pairing_size,
        ))

        pop = execute(pop, cmds[-1:])

    return cmds

def destroy_poverty(pop):
    poverty_sitter_group  = State(SELFSITTING, 0)
    wealthy_sitter_groups = [
        s for s in pop.keys()
        if s.flavor == SELFSITTING and s.scrip > 1
    ]

    # Try to spend the rich's money first.
    wealthy_sitter_groups.sort(key=lambda s: s.scrip, reverse=True)

    cmds = []
    impoverished_remaining = pop[poverty_sitter_group]
    while impoverished_remaining > 0 and len(wealthy_sitter_groups) > 0:
        # Either the wg will consume the remaining impoverished, or the impoverished
        # will consume the entire wg. In the first case, we're about to bounce out of
        # the loop, so it's fine to delete the wg.
        wg = wealthy_sitter_groups.pop(0)

        size = min(impoverished_remaining, pop[wg])
        impoverished_remaining -= size
        cmds.append(Command(
            babysitter=poverty_sitter_group,
            recipient= wg,
            size=size,
        ))
    return cmds

def gods_own_babysitting(pop):
    ccs = cover_crises(pop)

    ccpop = execute(pop, ccs)
    dps = destroy_poverty(ccpop)

    return ccs+dps

import doctest
assert doctest.testmod().failed == 0

population = {
    State(SELFSITTING, 1): 1000000,
}

for turn in range(10):
    cpop = induce_crisis(population)
    cmds = gods_own_babysitting(copy.deepcopy(cpop))
    ppop = execute(cpop, cmds)
    utility, population = resolve(ppop)
    print(turn, utility, sorted((s.scrip, ct) for s,ct in population.items()))
