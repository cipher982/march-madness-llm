/**
 * Minimal valid BracketData fixtures for E2E tests.
 *
 * Real brackets have 8 matchups per round of 64 (16 teams per region),
 * but we only need enough structure for the bracketry component to
 * initialise without crashing (it uses try/catch internally).
 */

import type { BracketData, Matchup, Region } from "../../src/types/bracket";

const seeds: [string, number][] = [
  ["Alpha", 1],
  ["Beta", 16],
  ["Gamma", 2],
  ["Delta", 15],
  ["Epsilon", 3],
  ["Zeta", 14],
  ["Eta", 4],
  ["Theta", 13],
  ["Iota", 5],
  ["Kappa", 12],
  ["Lambda", 6],
  ["Mu", 11],
  ["Nu", 7],
  ["Xi", 10],
  ["Omicron", 8],
  ["Pi", 9],
];

function makeMatchup(team1Idx: number, team2Idx: number, winner?: number): Matchup {
  const [name1, seed1] = seeds[team1Idx];
  const [name2, seed2] = seeds[team2Idx];
  return {
    team1: { name: name1, seed: seed1 },
    team2: { name: name2, seed: seed2 },
    winner: winner !== undefined ? { name: seeds[winner][0], seed: seeds[winner][1] } : null,
  };
}

function makeRegion(name: string, withWinners = false): Region {
  // Round of 64 (8 matchups)
  const r64Matchups: Matchup[] = [
    makeMatchup(0, 1, withWinners ? 0 : undefined),
    makeMatchup(2, 3, withWinners ? 2 : undefined),
    makeMatchup(4, 5, withWinners ? 4 : undefined),
    makeMatchup(6, 7, withWinners ? 6 : undefined),
    makeMatchup(8, 9, withWinners ? 8 : undefined),
    makeMatchup(10, 11, withWinners ? 10 : undefined),
    makeMatchup(12, 13, withWinners ? 12 : undefined),
    makeMatchup(14, 15, withWinners ? 14 : undefined),
  ];

  // Round of 32 (4 matchups — winners from r64, TBD if no winners)
  const r32Matchups: Matchup[] = withWinners
    ? [
        { team1: { name: "Alpha", seed: 1 }, team2: { name: "Gamma", seed: 2 }, winner: { name: "Alpha", seed: 1 } },
        { team1: { name: "Epsilon", seed: 3 }, team2: { name: "Eta", seed: 4 }, winner: { name: "Epsilon", seed: 3 } },
        { team1: { name: "Iota", seed: 5 }, team2: { name: "Lambda", seed: 6 }, winner: { name: "Iota", seed: 5 } },
        { team1: { name: "Nu", seed: 7 }, team2: { name: "Omicron", seed: 8 }, winner: { name: "Nu", seed: 7 } },
      ]
    : [
        { team1: null, team2: null, winner: null },
        { team1: null, team2: null, winner: null },
        { team1: null, team2: null, winner: null },
        { team1: null, team2: null, winner: null },
      ];

  // Sweet 16 (2 matchups)
  const s16Matchups: Matchup[] = withWinners
    ? [
        { team1: { name: "Alpha", seed: 1 }, team2: { name: "Epsilon", seed: 3 }, winner: { name: "Alpha", seed: 1 } },
        { team1: { name: "Iota", seed: 5 }, team2: { name: "Nu", seed: 7 }, winner: { name: "Iota", seed: 5 } },
      ]
    : [
        { team1: null, team2: null, winner: null },
        { team1: null, team2: null, winner: null },
      ];

  // Elite 8 (1 matchup)
  const e8Matchups: Matchup[] = withWinners
    ? [{ team1: { name: "Alpha", seed: 1 }, team2: { name: "Iota", seed: 5 }, winner: { name: "Alpha", seed: 1 } }]
    : [{ team1: null, team2: null, winner: null }];

  return {
    name,
    rounds: [
      { name: "round_of_64", matchups: r64Matchups },
      { name: "round_of_32", matchups: r32Matchups },
      { name: "sweet_16", matchups: s16Matchups },
      { name: "elite_8", matchups: e8Matchups },
    ],
  };
}

export function makeInitialBracket(): BracketData {
  return {
    regions: [
      makeRegion("East"),
      makeRegion("West"),
      makeRegion("South"),
      makeRegion("Midwest"),
    ],
    finalFour: {
      name: "Final Four",
      matchups: [
        { team1: null, team2: null, winner: null },
        { team1: null, team2: null, winner: null },
      ],
    },
    championship: { team1: null, team2: null, winner: null },
  };
}

export function makeCompletedBracket(): BracketData {
  return {
    regions: [
      makeRegion("East", true),
      makeRegion("West", true),
      makeRegion("South", true),
      makeRegion("Midwest", true),
    ],
    finalFour: {
      name: "Final Four",
      matchups: [
        {
          team1: { name: "Alpha", seed: 1 },
          team2: { name: "Alpha", seed: 1 },
          winner: { name: "Alpha", seed: 1 },
        },
        {
          team1: { name: "Alpha", seed: 1 },
          team2: { name: "Alpha", seed: 1 },
          winner: { name: "Alpha", seed: 1 },
        },
      ],
    },
    championship: {
      team1: { name: "Alpha", seed: 1 },
      team2: { name: "Alpha", seed: 1 },
      winner: { name: "Alpha", seed: 1 },
    },
  };
}
