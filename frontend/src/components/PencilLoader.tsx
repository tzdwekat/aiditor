export function PencilLoader() {
  return (
    <div className="flex flex-col items-center gap-6 py-16">
      <svg width="280" height="160" viewBox="0 0 280 160" style={{ overflow: 'visible' }}>
        {/* Paper card */}
        <rect x="0" y="0" width="280" height="148" rx="2"
          fill="#FAF7EE" stroke="#A08040" strokeWidth="1" />

        {/* Faint ruled lines */}
        {[38, 68, 98, 128].map(y => (
          <line key={y} x1="18" y1={y} x2="262" y2={y}
            stroke="#C8A870" strokeWidth="0.4" opacity="0.55" />
        ))}

        {/* Scribble line 1 */}
        <path
          pathLength="1"
          d="M18,38 C58,30 98,46 138,38 C178,30 218,46 262,38"
          fill="none" stroke="#3D2B1F" strokeWidth="2" strokeLinecap="round"
          style={{
            strokeDasharray: 1,
            strokeDashoffset: 1,
            animation: 'scribble-draw 1.3s ease-in-out 0s infinite alternate',
          }}
        />

        {/* Scribble line 2 */}
        <path
          pathLength="1"
          d="M18,68 C68,60 118,76 168,68 C208,61 242,72 262,68"
          fill="none" stroke="#3D2B1F" strokeWidth="2" strokeLinecap="round"
          style={{
            strokeDasharray: 1,
            strokeDashoffset: 1,
            animation: 'scribble-draw 1.3s ease-in-out 0.43s infinite alternate',
          }}
        />

        {/* Scribble line 3 */}
        <path
          pathLength="1"
          d="M18,98 C78,90 138,106 198,98 C228,93 252,100 262,98"
          fill="none" stroke="#3D2B1F" strokeWidth="2" strokeLinecap="round"
          style={{
            strokeDasharray: 1,
            strokeDashoffset: 1,
            animation: 'scribble-draw 1.3s ease-in-out 0.86s infinite alternate',
          }}
        />

        {/* Scribble line 4 — short, like mid-sentence */}
        <path
          pathLength="1"
          d="M18,128 C48,122 78,134 108,128 C128,124 148,130 162,128"
          fill="none" stroke="#3D2B1F" strokeWidth="2" strokeLinecap="round"
          style={{
            strokeDasharray: 1,
            strokeDashoffset: 1,
            animation: 'scribble-draw 0.9s ease-in-out 1.29s infinite alternate',
          }}
        />

        {/* Pencil group — follows the lines */}
        <g style={{ animation: 'pencil-write 5.2s linear 0s infinite' }}>
          {/* Rotate ~-35° to tilt like writing */}
          <g transform="rotate(-35)">
            {/* Eraser (pink) */}
            <rect x="-4.5" y="-42" width="9" height="9" rx="1.5"
              fill="#F4ACAC" stroke="#D48080" strokeWidth="0.8" />
            {/* Metal ferrule band */}
            <rect x="-4.5" y="-33.5" width="9" height="3" fill="#C8A000" />
            {/* Body (yellow) */}
            <rect x="-4.5" y="-31" width="9" height="28" rx="0.5"
              fill="#F5C940" stroke="#D4A800" strokeWidth="0.8" />
            {/* Wood cone */}
            <polygon points="-4.5,-3 4.5,-3 0,9"
              fill="#DEBA8A" stroke="#C8A870" strokeWidth="0.8" />
            {/* Lead tip */}
            <polygon points="-1.5,5.5 1.5,5.5 0,9" fill="#2C1810" />
          </g>
        </g>
      </svg>

      <p className="font-serif text-sm text-ink-muted tracking-wide">
        Consulting the analyst… (15–30 seconds)
      </p>
    </div>
  )
}
