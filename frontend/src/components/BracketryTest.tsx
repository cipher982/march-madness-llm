import React, { useEffect, useRef } from "react";
import { createBracket } from "bracketry";

import { TEAM_MAPPINGS } from "../team_mappings";
import { BracketData, Matchup, Region, Round, Team } from "../types/bracket";

interface BracketryTestProps {
  bracket: BracketData;
}

interface BracketryInstance {
  uninstall: () => void;
}

interface BracketryMatch {
  roundIndex: number;
  order: number;
  sides: Array<{
    contestantId: string;
    title: string;
    isWinner: boolean;
  }>;
}

interface BracketryData {
  rounds: Array<{ name: string }>;
  matches: BracketryMatch[];
  contestants: Record<
    string,
    {
      players: Array<{
        title: string;
        seed: number;
      }>;
    }
  >;
}

const ROUND_TITLES = ["Round of 64", "Round of 32", "Sweet 16", "Elite 8"];
const TEAM_MAPPING_RECORD = TEAM_MAPPINGS as Record<string, { logo_id?: string }>;

const getTeamHTML = (teamName: string, seed: number) => {
  const teamInfo = TEAM_MAPPING_RECORD[teamName];
  const logoPath = teamInfo ? `/logos/optimized/50x50/${teamInfo.logo_id}.webp` : "";

  return `${logoPath ? `<img src="${logoPath}" alt="${teamName} logo" style="width: 18px; height: 18px; vertical-align: middle; margin-right: 3px;" />` : ""}${seed}. ${teamName}`;
};

const transformMatchesToBracketry = (rounds: Round[] = []): BracketryData => {
  const matches: BracketryMatch[] = rounds.flatMap((round, roundIndex) =>
    round.matchups.map((matchup: Matchup, matchOrder: number) => ({
      roundIndex,
      order: matchOrder,
      sides: [
        {
          contestantId: matchup.team1?.name || "TBD",
          title: matchup.team1?.name || "TBD",
          isWinner: Boolean(matchup.winner && matchup.team1 && matchup.winner.name === matchup.team1.name),
        },
        {
          contestantId: matchup.team2?.name || "TBD",
          title: matchup.team2?.name || "TBD",
          isWinner: Boolean(matchup.winner && matchup.team2 && matchup.winner.name === matchup.team2.name),
        },
      ],
    })),
  );

  const contestants = new Map<string, Team>();
  rounds.forEach((round) => {
    round.matchups.forEach((matchup) => {
      if (matchup.team1) {
        contestants.set(matchup.team1.name, matchup.team1);
      }
      if (matchup.team2) {
        contestants.set(matchup.team2.name, matchup.team2);
      }
    });
  });

  const contestantPayload = Object.fromEntries(
    Array.from(contestants.values()).map((team) => [
      team.name,
      {
        players: [{ title: team.name, seed: team.seed }],
      },
    ]),
  );

  return {
    rounds: ROUND_TITLES.map((name) => ({ name })),
    matches,
    contestants: contestantPayload,
  };
};

const BracketryTest: React.FC<BracketryTestProps> = ({ bracket }) => {
  const eastBracketRef = useRef<HTMLDivElement | null>(null);
  const westBracketRef = useRef<HTMLDivElement | null>(null);
  const southBracketRef = useRef<HTMLDivElement | null>(null);
  const midwestBracketRef = useRef<HTMLDivElement | null>(null);

  const eastBracketInstanceRef = useRef<BracketryInstance | null>(null);
  const westBracketInstanceRef = useRef<BracketryInstance | null>(null);
  const southBracketInstanceRef = useRef<BracketryInstance | null>(null);
  const midwestBracketInstanceRef = useRef<BracketryInstance | null>(null);

  const findRegion = (regionName: string): Region | undefined =>
    bracket.regions.find((region) => region.name.toLowerCase() === regionName);

  const eastRegion = findRegion("east");
  const westRegion = findRegion("west");
  const southRegion = findRegion("south");
  const midwestRegion = findRegion("midwest");

  useEffect(() => {
    [eastBracketInstanceRef, westBracketInstanceRef, southBracketInstanceRef, midwestBracketInstanceRef].forEach((ref) => {
      if (ref.current) {
        ref.current.uninstall();
        ref.current = null;
      }
    });

    const createRegionBracket = (
      region: Region | undefined,
      bracketRef: React.RefObject<HTMLDivElement>,
      bracketInstanceRef: React.MutableRefObject<BracketryInstance | null>,
      isRightSide = false,
    ) => {
      if (bracketRef.current && region) {
        if (bracketInstanceRef.current) {
          bracketInstanceRef.current.uninstall();
        }

        const bracketData = transformMatchesToBracketry(region.rounds);

        try {
          bracketInstanceRef.current = createBracket(bracketData, bracketRef.current, {
            getPlayerTitleHTML: (player: { title: string; seed: number }) => getTeamHTML(player.title, player.seed),
            visibleRoundsCount: 4,
            matchMinVerticalGap: 15,
            matchAxisMargin: 2,
            oneSidePlayersGap: 1,
            matchHorMargin: 12,
            matchMaxWidth: 320,
            matchFontSize: 12,
            matchTextColor: "#ffffff",
            rootBorderColor: "#666666",
            connectionLinesColor: "#666666",
            roundTitleColor: "#ffffff",
            highlightedConnectionLinesColor: "#888888",
            connectionLinesWidth: 1,
          });

          if (isRightSide && bracketRef.current) {
            bracketRef.current.classList.add("right-side-bracket");
          }
        } catch (_error) {
          bracketInstanceRef.current = null;
        }
      }
    };

    createRegionBracket(eastRegion, eastBracketRef, eastBracketInstanceRef);
    createRegionBracket(westRegion, westBracketRef, westBracketInstanceRef);
    createRegionBracket(southRegion, southBracketRef, southBracketInstanceRef, true);
    createRegionBracket(midwestRegion, midwestBracketRef, midwestBracketInstanceRef, true);

    return () => {
      [eastBracketInstanceRef, westBracketInstanceRef, southBracketInstanceRef, midwestBracketInstanceRef].forEach((ref) => {
        if (ref.current) {
          ref.current.uninstall();
        }
      });
    };
  }, [eastRegion, westRegion, southRegion, midwestRegion]);

  if (!eastRegion || !westRegion || !southRegion || !midwestRegion) {
    return <div>Region data not available</div>;
  }

  const bracketPanelStyle: React.CSSProperties = {
    minHeight: "420px",
    height: "min(45vw, 700px)",
    width: "100%",
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "20px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <h3>East Region</h3>
          <div ref={eastBracketRef} style={bracketPanelStyle} />
        </div>
        <div>
          <h3>West Region</h3>
          <div ref={westBracketRef} style={bracketPanelStyle} />
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <h3 style={{ textAlign: "right" }}>South Region</h3>
          <div ref={southBracketRef} style={bracketPanelStyle} />
        </div>
        <div>
          <h3 style={{ textAlign: "right" }}>Midwest Region</h3>
          <div ref={midwestBracketRef} style={bracketPanelStyle} />
        </div>
      </div>
    </div>
  );
};

export default BracketryTest; 
