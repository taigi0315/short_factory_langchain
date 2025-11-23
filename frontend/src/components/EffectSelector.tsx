import React from 'react';

interface EffectDisplayProps {
    effect: string;
    reasoning?: string;
    isRecommended?: boolean;
}

const EFFECTS = [
    { value: 'ken_burns_zoom_in', label: 'Ken Burns (Zoom In)', icon: '🔍' },
    { value: 'ken_burns_zoom_out', label: 'Ken Burns (Zoom Out)', icon: '🔎' },
    { value: 'pan_left', label: 'Pan Left', icon: '⬅️' },
    { value: 'pan_right', label: 'Pan Right', icon: '➡️' },
    { value: 'static', label: 'Static (No Effect)', icon: '📷' },
    { value: 'shake', label: 'Shake (Impact)', icon: '💥' },
    { value: 'tilt_up', label: 'Tilt Up', icon: '⬆️' },
    { value: 'tilt_down', label: 'Tilt Down', icon: '⬇️' },
];

export const EffectDisplay: React.FC<EffectDisplayProps> = ({
    effect,
    reasoning,
    isRecommended = true
}) => {
    const effectInfo = EFFECTS.find(e => e.value === effect) || EFFECTS[0];

    return (
        <div className="effect-display">
            <div className="effect-value">
                <span className="effect-icon">{effectInfo.icon}</span>
                <span className="effect-label">{effectInfo.label}</span>
                {isRecommended && (
                    <span className="ai-badge" title="AI Recommended">
                        🤖 AI
                    </span>
                )}
            </div>
            {reasoning && (
                <div className="effect-reasoning" title={reasoning}>
                    <span className="reasoning-icon">ℹ️</span>
                    <span className="reasoning-text">{reasoning}</span>
                </div>
            )}
        </div>
    );
};

// Keep the old selector for backward compatibility (if needed)
export const EffectSelector = EffectDisplay;
