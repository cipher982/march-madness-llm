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
  winner?: Team | null;
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
  const logoPath = teamInfo ? `/logos/optimized/50x50/${teamInfo.logo_id}.webp` : "";
  return `${logoPath ? `<img src="${logoPath}" alt="${teamName} logo" style="width: 25px; height: 25px; vertical-align: middle; margin-right: 4px;" />` : ""}${seed}. ${teamName}`;
};

const BracketryTest: React.FC<BracketryTestProps> = ({ bracket }) => {
  console.log("1. Initial bracket data:", bracket);
  
  const bracketRef = useRef<HTMLDivElement>(null);
  const bracketInstanceRef = useRef<any>(null);
  
  // Extract just the South region for now
  const southRegion = bracket?.regions?.find((r: any) => r.name.toLowerCase() === "south");
  console.log("2. South region data:", southRegion);
  
  // Transform data for bracketry
  const transformMatchesToBracketry = (rounds: Round[] = []) => {
    console.log("3. Input rounds:", rounds);

    // Create matches array with all matches from all rounds
    const matches = rounds.flatMap((round, roundIndex) => 
      round.matchups.map((matchup: Match, matchOrder: number) => ({
        roundIndex,
        order: matchOrder,
        sides: [
          {
            contestantId: matchup.team1?.name || "TBD",
            title: matchup.team1?.name || "TBD",
            isWinner: matchup.winner?.name === matchup.team1?.name
          },
          {
            contestantId: matchup.team2?.name || "TBD",
            title: matchup.team2?.name || "TBD",
            isWinner: matchup.winner?.name === matchup.team2?.name
          }
        ]
      }))
    );

    // Create contestants object
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

    const result = {
      rounds: ROUND_TITLES.map(name => ({ name })),
      matches,
      contestants
    };

    console.log("4. Final transformed data:", result);
    return result;
  };

  useEffect(() => {
    console.log("5. Effect running, bracketRef exists:", !!bracketRef.current);
    console.log("6. South region exists:", !!southRegion);

    if (bracketRef.current && southRegion) {
      // Clean up previous instance if it exists
      if (bracketInstanceRef.current) {
        console.log("7. Cleaning up previous instance");
        bracketInstanceRef.current.uninstall();
      }

      const bracketData = transformMatchesToBracketry(southRegion.rounds);
      console.log("8. Creating bracket with data:", bracketData);

      try {
        // Create the bracket instance
        bracketInstanceRef.current = createBracket(
          bracketData,
          bracketRef.current,
          {
            getPlayerTitleHTML: (player: any) => getTeamHTML(player.title, player.seed),
            visibleRoundsCount: 4,
            // Vertical spacing
            matchMinVerticalGap: 15,
            matchAxisMargin: 2,
            oneSidePlayersGap: 1,
            // Horizontal spacing
            matchHorMargin: 12,
            matchMaxWidth: 180,
            // Font size adjustments
            matchFontSize: 12,
            // Colors for dark theme
            matchTextColor: "#ffffff",
            rootBorderColor: "#666666",
            connectionLinesColor: "#666666",
            roundTitleColor: "#ffffff",
            highlightedConnectionLinesColor: "#888888",
            connectionLinesWidth: 1
          }
        );
        console.log("10. Bracket instance created successfully");
      } catch (error) {
        console.error("11. Error creating bracket:", error);
      }
    }

    return () => {
      if (bracketInstanceRef.current) {
        bracketInstanceRef.current.uninstall();
      }
    };
  }, [southRegion]);

  if (!southRegion) {
    console.log("12. No south region found, returning early");
    return <div>No South region data available</div>;
  }

  return (
    <div style={{ padding: "20px" }}>
      <h3>South Region (Bracketry Test)</h3>
      <div ref={bracketRef} style={{ width: "100%", height: "600px", backgroundColor: "transparent", border: "1px solid #666" }} />
    </div>
  );
};

export default BracketryTest; 