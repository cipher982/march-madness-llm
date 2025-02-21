import React, { useState, useMemo } from "react";
import { TEAM_MAPPINGS } from "../team_mappings";
import { ABBREVIATED_TO_OFFICIAL } from "../team_name_mappings";

interface TeamLogoProps {
    teamName: string;
    size?: number;
    className?: string;
    useOriginal?: boolean;  // Add flag to force original PNG
}

// Cache for team info lookups
const teamInfoCache = new Map<string, typeof TEAM_MAPPINGS[keyof typeof TEAM_MAPPINGS]>();

export const TeamLogo: React.FC<TeamLogoProps> = ({ 
    teamName, 
    size = 50,  // Default size
    className = "",
    useOriginal = false,
}) => {
    const [imgError, setImgError] = useState(false);

    // Memoize the team info and URL calculations
    const { teamInfo, logoUrl, useOptimized } = useMemo(() => {
        // First try to find the official name if this is an abbreviated version
        const officialName = ABBREVIATED_TO_OFFICIAL[teamName] || teamName;
        
        // Check cache first
        let info = teamInfoCache.get(officialName);
        if (!info) {
            info = TEAM_MAPPINGS[officialName];
            if (info) {
                teamInfoCache.set(officialName, info);
            }
        }
        
        // Calculate if we should use optimized version
        const shouldUseOptimized = !useOriginal && size <= 100;
        
        // Generate URL
        const url = info ? (shouldUseOptimized 
            ? `/logos/optimized/${info.logo_id}.webp`
            : `/logos/${info.logo_id}.png`) : "";
            
        return { teamInfo: info, logoUrl: url, useOptimized: shouldUseOptimized };
    }, [teamName, size, useOriginal]);
    
    if (!teamInfo) {
        console.warn(`No logo info found for team: ${teamName} (official name: ${ABBREVIATED_TO_OFFICIAL[teamName] || teamName})`);
        return null;
    }

    if (imgError) {
        console.warn(`Failed to load logo for ${teamName}`);
        return null;
    }
    
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