import { useState } from 'react'

interface Tab { label: string; content: React.ReactNode }

export function Tabs({ tabs, defaultTab = 0 }: { tabs: Tab[]; defaultTab?: number }) {
  const [active, setActive] = useState(defaultTab)
  return (
    <div>
      <div className="tab-bar">
        {tabs.map((t, i) => (
          <button
            key={i}
            className={`tab-btn ${active === i ? 'active' : ''}`}
            onClick={() => setActive(i)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="bg-paper pt-5">{tabs[active].content}</div>
    </div>
  )
}
