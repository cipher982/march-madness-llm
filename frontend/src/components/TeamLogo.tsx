import React, { useState } from "react";
import { TEAM_MAPPINGS } from "../team_mappings";
import { ABBREVIATED_TO_OFFICIAL } from "../team_name_mappings";

interface TeamLogoProps {
    teamName: string;
    size?: number;
    className?: string;
}

export const TeamLogo: React.FC<TeamLogoProps> = ({ 
    teamName, 
    size = 50,  // Default size
    className = "",
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
    
    // Use the same backend URL configuration as the rest of the app
    const backendUrl = process.env.REACT_APP_BACKEND_URL || window.location.origin;
    const logoUrl = `${backendUrl}/api/team/logo/${teamInfo.logo_id}`;
    console.debug(`Loading logo for ${teamName} from ${logoUrl} (backend: ${backendUrl})`);
    
    return (
        <img
            src={logoUrl}
            alt={`${teamName} logo`}
            width={size}
            height={size}
            className={`object-contain ${className}`}
            loading="lazy"
            crossOrigin="anonymous"  // Add this for CORS images
            onError={(e) => {
                const target = e.target as HTMLImageElement;
                console.error(`Error loading logo for ${teamName} (ID: ${teamInfo.logo_id}):`, e);
                target.style.display = "none";
                setImgError(true);
            }}
        />
    );
}; 