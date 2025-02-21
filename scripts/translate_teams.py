import json
from openai import OpenAI
from typing import Dict, Set

from langsmith.wrappers import wrap_openai
import dotenv

dotenv.load_dotenv()


def extract_team_names(bracket_file: str) -> Set[str]:
    """Extract unique team names from bracket JSON file."""
    with open(bracket_file) as f:
        data = json.load(f)

    teams = set()
    for region in data["regions"].values():
        for matchup in region:
            teams.add(matchup["t1"][0])
            teams.add(matchup["t2"][0])
    return teams


def get_team_mappings(team_names: Set[str]) -> Dict[str, str]:
    """Use OpenAI to generate mappings from abbreviated to official names."""
    client = wrap_openai(OpenAI())

    # Load official names from team_mappings.ts
    with open("frontend/src/team_mappings.ts") as f:
        content = f.read()
        # Extract just the object part
        start = content.find("{") + 1
        end = content.rfind("};")
        official_teams = content[start:end]

    prompt = f"""Given these abbreviated team names from March Madness brackets:
{sorted(list(team_names))}

And this TypeScript object of official team names:
{official_teams}

Return a JSON object that maps each abbreviated name to its corresponding official name.
Format: {{"abbreviated_name": "official_name", ...}}
Example: {{"San Diego St.": "San Diego State"}}"""

    response = client.chat.completions.create(
        model="o3-mini",
        reasoning_effort="high",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that returns only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("No response content received from OpenAI")

    return json.loads(content)


def main():
    # Extract team names from bracket
    teams = extract_team_names("backend/data/bracket_2024.json")

    # Get mappings from OpenAI
    mappings = get_team_mappings(teams)

    print(mappings)

    # Save mappings
    with open("backend/data/team_name_mappings_high_effort.json", "w") as f:
        json.dump(mappings, f, indent=2)

    print("Mappings saved to team_name_mappings.json")


if __name__ == "__main__":
    main()
