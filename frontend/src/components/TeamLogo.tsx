import React, { useState } from "react";
import { TEAM_MAPPINGS } from "../team_mappings";
import { ABBREVIATED_TO_OFFICIAL } from "../team_name_mappings";

interface TeamLogoProps {
    teamName: string;
    size?: number;
    className?: string;
    useOriginal?: boolean;  // Add flag to force original PNG
}

export const TeamLogo: React.FC<TeamLogoProps> = ({ 
    teamName, 
    size = 50,  // Default size
    className = "",
    useOriginal = false,
}) => {
    const [imgError, setImgError] = useState(false);

    // First try to find the official name if this is an abbreviated version
    const officialName = ABBREVIATED_TO_OFFICIAL[teamName] || teamName;
    const teamInfo = TEAM_MAPPINGS[officialName];
    
    if (!teamInfo) {
        console.warn(`No logo info found for team: ${teamName} (official name: ${officialName})`);
        return null;
    }

    if (imgError) {
        console.warn(`Failed to load logo for ${teamName}`);
        return null;
    }
    
    // Use optimized WebP for small logos, original PNG for larger ones
    const useOptimized = !useOriginal && size <= 100;
    const logoUrl = useOptimized 
        ? `/logos/optimized/${teamInfo.logo_id}.webp`
        : `/logos/${teamInfo.logo_id}.png`;
    
    return (
        <picture>
            {useOptimized && (
                <source
                    srcSet={`/logos/optimized/${teamInfo.logo_id}.webp`}
                    type="image/webp"
                />
            )}
            <img
                src={logoUrl}
                alt={`${teamName} logo`}
                width={size}
                height={size}
                className={`object-contain ${className}`}
                loading="lazy"
                onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    console.error(`Error loading logo for ${teamName} (ID: ${teamInfo.logo_id}):`, e);
                    target.style.display = "none";
                    setImgError(true);
                }}
            />
        </picture>
    );
}; 