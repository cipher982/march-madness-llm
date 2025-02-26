import React, { useEffect, useRef } from "react";
import { createBracket } from "bracketry";
import { TEAM_MAPPINGS } from "../team_mappings";

interface Team {
  name: string;
  seed: number;
}

interface Match {
  team1: Team | null;
  team2: Team | null;
  winner?: Team;
  matchup_id: string;
}

interface Round {
  name: string;
  matchups: Match[];
}

interface BracketryTestProps {
  bracket: any; // We'll type this better later
}

const ROUND_TITLES = ["Round of 64", "Round of 32", "Sweet 16", "Elite 8"];

// Generate static HTML for team display
const getTeamHTML = (teamName: string, seed: number) => {
  const teamInfo = TEAM_MAPPINGS[teamName];
  
  // Debug logging for team mapping issues
  if (!teamInfo) {
    console.warn(`Team info not found for ${teamName}`);
  } else if (!teamInfo.logo_id) {
    console.warn(`Logo ID missing for ${teamName}`);
  }
  
  const logoPath = teamInfo ? `/logos/optimized/50x50/${teamInfo.logo_id}.webp` : "";
  
  // Debug logging for logo path
  if (logoPath) {
    console.log(`Logo path for ${teamName}: ${logoPath}`);
  }
  
  return `${logoPath ? `<img src="${logoPath}" alt="${teamName} logo" style="width: 25px; height: 25px; vertical-align: middle; margin-right: 4px;" />` : ""}${seed}. ${teamName}`;
};

const BracketryTest: React.FC<BracketryTestProps> = ({ bracket }) => {
  // Add a key that will change when bracket is updated
  const bracketKey = React.useMemo(() => Math.random().toString(36).substring(7), [bracket]);
  
  const eastBracketRef = useRef<HTMLDivElement>(null);
  const westBracketRef = useRef<HTMLDivElement>(null);
  const southBracketRef = useRef<HTMLDivElement>(null);
  const midwestBracketRef = useRef<HTMLDivElement>(null);
  
  const eastBracketInstanceRef = useRef<any>(null);
  const westBracketInstanceRef = useRef<any>(null);
  const southBracketInstanceRef = useRef<any>(null);
  const midwestBracketInstanceRef = useRef<any>(null);
  
  // Extract regions
  const eastRegion = bracket?.regions?.find((r: any) => r.name.toLowerCase() === "east");
  const westRegion = bracket?.regions?.find((r: any) => r.name.toLowerCase() === "west");
  const southRegion = bracket?.regions?.find((r: any) => r.name.toLowerCase() === "south");
  const midwestRegion = bracket?.regions?.find((r: any) => r.name.toLowerCase() === "midwest");
  
  // Transform data for bracketry
  const transformMatchesToBracketry = (rounds: Round[] = []) => {
    const matches = rounds.flatMap((round, roundIndex) => 
      round.matchups.map((matchup: Match, matchOrder: number) => ({
        roundIndex,
        order: matchOrder,
        sides: [
          {
            contestantId: matchup.team1?.name || "TBD",
            title: matchup.team1?.name || "TBD",
            isWinner: !!matchup.winner && !!matchup.team1 && matchup.winner.name === matchup.team1.name
          },
          {
            contestantId: matchup.team2?.name || "TBD",
            title: matchup.team2?.name || "TBD",
            isWinner: !!matchup.winner && !!matchup.team2 && matchup.winner.name === matchup.team2.name
          }
        ]
      }))
    );

    const contestants = Object.fromEntries(
      rounds.flatMap(round => 
        round.matchups.flatMap((matchup: Match) => [
          matchup.team1,
          matchup.team2
        ])
      )
      .filter(team => team !== null)
      .map(team => [
        team!.name,
        {
          players: [{
            title: team!.name,
            seed: team!.seed
          }]
        }
      ])
    );

    return {
      rounds: ROUND_TITLES.map(name => ({ name })),
      matches,
      contestants
    };
  };

  useEffect(() => {
    // Clean up any previous instances
    [eastBracketInstanceRef, westBracketInstanceRef, southBracketInstanceRef, midwestBracketInstanceRef].forEach(ref => {
      if (ref.current) {
        ref.current.uninstall();
        ref.current = null;
      }
    });

    const createRegionBracket = (
      region: any,
      bracketRef: React.RefObject<HTMLDivElement>,
      bracketInstanceRef: React.MutableRefObject<any>,
      isRightSide: boolean = false
    ) => {
      if (bracketRef.current && region) {
        if (bracketInstanceRef.current) {
          bracketInstanceRef.current.uninstall();
        }

        // Create a copy of the rounds data
        const bracketData = transformMatchesToBracketry(region.rounds);
        
        try {
          bracketInstanceRef.current = createBracket(
            bracketData,
            bracketRef.current,
            {
              getPlayerTitleHTML: (player: any) => getTeamHTML(player.title, player.seed),
              visibleRoundsCount: 4,
              matchMinVerticalGap: 15,
              matchAxisMargin: 2,
              oneSidePlayersGap: 1,
              matchHorMargin: 12,
              matchMaxWidth: 180,
              matchFontSize: 12,
              matchTextColor: "#ffffff",
              rootBorderColor: "#666666",
              connectionLinesColor: "#666666",
              roundTitleColor: "#ffffff",
              highlightedConnectionLinesColor: "#888888",
              connectionLinesWidth: 1
            }
          );
          
          // Add right-to-left class for right-side brackets
          if (isRightSide && bracketRef.current) {
            bracketRef.current.classList.add('right-side-bracket');
          }
        } catch (error) {
          console.error("Error creating bracket:", error);
        }
      }
    };

    createRegionBracket(eastRegion, eastBracketRef, eastBracketInstanceRef);
    createRegionBracket(westRegion, westBracketRef, westBracketInstanceRef);
    createRegionBracket(southRegion, southBracketRef, southBracketInstanceRef, true);
    createRegionBracket(midwestRegion, midwestBracketRef, midwestBracketInstanceRef, true);

    return () => {
      [eastBracketInstanceRef, westBracketInstanceRef, southBracketInstanceRef, midwestBracketInstanceRef].forEach(ref => {
        if (ref.current) {
          ref.current.uninstall();
        }
      });
    };
  }, [eastRegion, westRegion, southRegion, midwestRegion]);

  if (!eastRegion || !westRegion || !southRegion || !midwestRegion) {
    return <div>Region data not available</div>;
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <h3>East Region</h3>
          <div ref={eastBracketRef} style={{ height: "700px", width: "700px" }} />
        </div>
        <div>
          <h3>West Region</h3>
          <div ref={westBracketRef} style={{ height: "700px", width: "700px" }} />
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <h3 style={{ textAlign: "right" }}>South Region</h3>
          <div ref={southBracketRef} style={{ height: "700px", width: "700px" }} />
        </div>
        <div>
          <h3 style={{ textAlign: "right" }}>Midwest Region</h3>
          <div ref={midwestBracketRef} style={{ height: "700px", width: "700px" }} />
        </div>
      </div>
    </div>
  );
};

export default BracketryTest; 