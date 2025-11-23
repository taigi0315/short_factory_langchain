import React from 'react';

interface EffectSelectorProps {
    value: string;
    onChange: (effect: string) => void;
    disabled?: boolean;
}

const EFFECTS = [
    { value: 'ken_burns_zoom_in', label: 'Ken Burns (Zoom In)' },
    { value: 'ken_burns_zoom_out', label: 'Ken Burns (Zoom Out)' },
    { value: 'pan_left', label: 'Pan Left' },
    { value: 'pan_right', label: 'Pan Right' },
    { value: 'static', label: 'Static (No Effect)' },
];

export const EffectSelector: React.FC<EffectSelectorProps> = ({
    value,
    onChange,
    disabled
}) => {
    return (
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="effect-selector"
        >
            {EFFECTS.map(effect => (
                <option key={effect.value} value={effect.value}>
                    {effect.label}
                </option>
            ))}
        </select>
    );
};
