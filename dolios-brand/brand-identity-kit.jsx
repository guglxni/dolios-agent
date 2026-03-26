import { useState } from "react";

const colors = [
  { name: "Deep Midnight", hex: "#1A1A2E", usage: "Backgrounds, wordmark, headers", ratio: "60%" },
  { name: "Signal Red", hex: "#E94560", usage: "CTAs, active states, action spark", ratio: "10%" },
  { name: "Strategy Blue", hex: "#0F3460", usage: "Secondary text, code blocks, links", ratio: "25%" },
  { name: "Dark Navy", hex: "#16213E", usage: "Gradients, sidebars, cards", ratio: "—" },
  { name: "Antiquity Gold", hex: "#C4A35A", usage: "Greek letterforms, premium accents", ratio: "5%" },
  { name: "Light Gray", hex: "#F5F5F7", usage: "Page backgrounds, inputs", ratio: "—" },
];

const typeScale = [
  { role: "Display / H1", font: "Georgia, serif", weight: "700", size: "48px", tracking: "+0.02em", sample: "DOLIOS" },
  { role: "Heading / H2", font: "Georgia, serif", weight: "600", size: "32px", tracking: "+0.01em", sample: "The Crafty Agent" },
  { role: "Heading / H3", font: "Georgia, serif", weight: "600", size: "24px", tracking: "+0.01em", sample: "Autonomous Intelligence" },
  { role: "Body", font: "Inter, sans-serif", weight: "400", size: "16px", tracking: "0", sample: "Dolios mapped 4 tools, found the shortest path, and executed in 1.2s." },
  { role: "UI Label", font: "Inter, sans-serif", weight: "500", size: "13px", tracking: "+0.04em", sample: "STATUS INDICATORS" },
  { role: "Code", font: "monospace", weight: "400", size: "14px", tracking: "0", sample: "dolios.execute({ tools: [mcp, api], mode: 'autonomous' })" },
];

const voiceAttrs = [
  { attr: "Cunning", desc: "Smart without being smug. Show the plan, not just the result." },
  { attr: "Precise", desc: "No filler. Every word earns its place." },
  { attr: "Grounded", desc: "Mythological references used sparingly, never forced." },
  { attr: "Technical", desc: "Developer-first language. Don't dumb it down." },
];

function DeltaIcon({ size = 64 }) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size}>
      <polygon points="32,6 4,58 60,58" fill="none" stroke="#1A1A2E" strokeWidth="3.5" strokeLinejoin="round"/>
      <line x1="32" y1="24" x2="22" y2="44" stroke="#0F3460" strokeWidth="1.8"/>
      <line x1="32" y1="24" x2="42" y2="44" stroke="#0F3460" strokeWidth="1.8"/>
      <line x1="22" y1="44" x2="42" y2="44" stroke="#0F3460" strokeWidth="1.8"/>
      <circle cx="32" cy="24" r="4" fill="#E94560"/>
      <circle cx="22" cy="44" r="4" fill="#E94560"/>
      <circle cx="42" cy="44" r="4" fill="#E94560"/>
    </svg>
  );
}

function LettermarkIcon({ size = 64 }) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size}>
      <path d="M16,8 L16,56 Q48,56 48,32 Q48,8 16,8 Z" fill="#1A1A2E"/>
      <path d="M22,14 L22,50 Q42,50 42,32 Q42,14 22,14 Z" fill="white"/>
      <rect x="22" y="29" width="24" height="6" fill="#E94560"/>
      <polygon points="46,24 58,32 46,40" fill="#E94560"/>
    </svg>
  );
}

function WordmarkSVG() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      <span style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "42px", color: "#1A1A2E", letterSpacing: "3px" }}>
        D
      </span>
      <span style={{ position: "relative", fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "42px", color: "#1A1A2E", letterSpacing: "3px" }}>
        O
        <span style={{ position: "absolute", left: "4px", right: "4px", top: "50%", height: "2px", backgroundColor: "#E94560", transform: "translateY(-50%)" }}/>
      </span>
      <span style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "42px", color: "#1A1A2E", letterSpacing: "3px" }}>
        LIOS
      </span>
    </div>
  );
}

export default function DoliosBrandKit() {
  const [activeSection, setActiveSection] = useState("all");

  const sections = ["all", "identity", "colors", "typography", "logos", "voice"];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#1A1A2E", color: "#F5F5F7", fontFamily: "Inter, -apple-system, sans-serif" }}>
      {/* Navigation */}
      <nav style={{ position: "sticky", top: 0, zIndex: 50, backgroundColor: "rgba(26,26,46,0.95)", backdropFilter: "blur(12px)", borderBottom: "1px solid rgba(255,255,255,0.06)", padding: "12px 40px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <DeltaIcon size={28} />
          <span style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "18px", letterSpacing: "2px" }}>DOLIOS</span>
          <span style={{ fontSize: "11px", color: "#C4A35A", letterSpacing: "3px", textTransform: "uppercase", fontWeight: 500 }}>Brand System v1.0</span>
        </div>
        <div style={{ display: "flex", gap: "4px" }}>
          {sections.map(s => (
            <button
              key={s}
              onClick={() => setActiveSection(s)}
              style={{
                padding: "6px 14px", borderRadius: "6px", border: "none", cursor: "pointer",
                fontSize: "12px", fontWeight: 500, textTransform: "capitalize", letterSpacing: "0.5px",
                backgroundColor: activeSection === s ? "#E94560" : "transparent",
                color: activeSection === s ? "#fff" : "#6B7280",
                transition: "all 0.2s"
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </nav>

      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "0 40px" }}>

        {/* Hero / Identity */}
        {(activeSection === "all" || activeSection === "identity") && (
          <section style={{ padding: "80px 0 60px", textAlign: "center" }}>
            <div style={{ marginBottom: "24px" }}>
              <span style={{ fontFamily: "'Noto Serif', Georgia, serif", fontSize: "16px", color: "#C4A35A", letterSpacing: "6px" }}>ΔΟΛΙΟΣ</span>
            </div>
            <h1 style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "72px", color: "#F5F5F7", letterSpacing: "6px", margin: "0 0 16px" }}>
              DOLIOS
            </h1>
            <p style={{ fontSize: "14px", color: "#6B7280", letterSpacing: "6px", textTransform: "uppercase", fontWeight: 500, margin: "0 0 32px" }}>
              The Crafty Agent
            </p>
            <div style={{ width: "60px", height: "2px", backgroundColor: "#E94560", margin: "0 auto 32px" }}/>
            <p style={{ fontSize: "18px", color: "#9CA3AF", maxWidth: "600px", margin: "0 auto", lineHeight: 1.7 }}>
              The agentic execution layer for the Hermes model ecosystem. Cunning intelligence meets autonomous action.
            </p>
            <div style={{ display: "flex", justifyContent: "center", gap: "24px", marginTop: "40px" }}>
              <div style={{ padding: "10px 24px", border: "1px solid rgba(233,69,96,0.4)", borderRadius: "8px", fontSize: "13px", color: "#E94560", letterSpacing: "1px" }}>
                Scheme. Execute. Deliver.
              </div>
              <div style={{ padding: "10px 24px", border: "1px solid rgba(196,163,90,0.3)", borderRadius: "8px", fontSize: "13px", color: "#C4A35A", letterSpacing: "1px" }}>
                Hermes' Sharpest Heir
              </div>
            </div>
          </section>
        )}

        {/* Color System */}
        {(activeSection === "all" || activeSection === "colors") && (
          <section style={{ padding: "60px 0" }}>
            <div style={{ marginBottom: "8px", fontSize: "11px", color: "#E94560", letterSpacing: "4px", textTransform: "uppercase", fontWeight: 500 }}>02</div>
            <h2 style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "32px", margin: "0 0 8px" }}>Color System</h2>
            <p style={{ fontSize: "14px", color: "#6B7280", marginBottom: "36px" }}>
              Authority meets energy. Deep midnight establishes credibility. Signal Red is the spark of action.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "16px" }}>
              {colors.map(c => (
                <div key={c.hex} style={{ textAlign: "center" }}>
                  <div style={{
                    width: "100%", aspectRatio: "1", borderRadius: "12px",
                    backgroundColor: c.hex, marginBottom: "12px",
                    border: c.hex === "#F5F5F7" ? "1px solid rgba(255,255,255,0.1)" : "none",
                    boxShadow: "0 4px 16px rgba(0,0,0,0.3)"
                  }}/>
                  <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "2px" }}>{c.name}</div>
                  <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#6B7280" }}>{c.hex}</div>
                  {c.ratio !== "—" && (
                    <div style={{ fontSize: "11px", color: "#E94560", marginTop: "4px", fontWeight: 500 }}>{c.ratio}</div>
                  )}
                </div>
              ))}
            </div>
            {/* Color ratio bar */}
            <div style={{ marginTop: "32px", borderRadius: "8px", overflow: "hidden", height: "8px", display: "flex" }}>
              <div style={{ width: "60%", backgroundColor: "#1A1A2E", border: "1px solid rgba(255,255,255,0.1)" }}/>
              <div style={{ width: "25%", backgroundColor: "#0F3460" }}/>
              <div style={{ width: "10%", backgroundColor: "#E94560" }}/>
              <div style={{ width: "5%", backgroundColor: "#C4A35A" }}/>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px", fontSize: "10px", color: "#6B7280", letterSpacing: "1px" }}>
              <span>60% MIDNIGHT</span><span>25% BLUE</span><span>10% RED</span><span>5% GOLD</span>
            </div>
          </section>
        )}

        {/* Typography */}
        {(activeSection === "all" || activeSection === "typography") && (
          <section style={{ padding: "60px 0" }}>
            <div style={{ marginBottom: "8px", fontSize: "11px", color: "#E94560", letterSpacing: "4px", textTransform: "uppercase", fontWeight: 500 }}>03</div>
            <h2 style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "32px", margin: "0 0 8px" }}>Typography Scale</h2>
            <p style={{ fontSize: "14px", color: "#6B7280", marginBottom: "36px" }}>
              Georgia carries antiquity. Inter is the modern workhorse. Together: ancient intelligence, modern execution.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
              {typeScale.map((t, i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "160px 1fr",
                  padding: "20px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", alignItems: "baseline"
                }}>
                  <div>
                    <div style={{ fontSize: "11px", color: "#E94560", letterSpacing: "2px", textTransform: "uppercase", fontWeight: 500, marginBottom: "4px" }}>{t.role}</div>
                    <div style={{ fontSize: "10px", color: "#6B7280", fontFamily: "monospace" }}>{t.size} / {t.weight}</div>
                  </div>
                  <div style={{
                    fontFamily: t.font, fontWeight: t.weight, fontSize: t.size,
                    letterSpacing: t.tracking, color: "#F5F5F7",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
                  }}>
                    {t.sample}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Logo System */}
        {(activeSection === "all" || activeSection === "logos") && (
          <section style={{ padding: "60px 0" }}>
            <div style={{ marginBottom: "8px", fontSize: "11px", color: "#E94560", letterSpacing: "4px", textTransform: "uppercase", fontWeight: 500 }}>04</div>
            <h2 style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "32px", margin: "0 0 8px" }}>Logo System</h2>
            <p style={{ fontSize: "14px", color: "#6B7280", marginBottom: "36px" }}>
              Three variants: wordmark for headers, lettermark for compact use, pictorial mark for icons and favicons.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px" }}>
              {/* Wordmark */}
              <div style={{ backgroundColor: "#F5F5F7", borderRadius: "16px", padding: "40px 24px", textAlign: "center" }}>
                <div style={{ marginBottom: "20px", display: "flex", justifyContent: "center" }}>
                  <WordmarkSVG />
                </div>
                <div style={{ fontSize: "12px", color: "#1A1A2E", fontWeight: 600, letterSpacing: "2px", textTransform: "uppercase" }}>Wordmark</div>
                <div style={{ fontSize: "11px", color: "#6B7280", marginTop: "4px" }}>Headers, hero sections</div>
              </div>
              {/* Lettermark */}
              <div style={{ backgroundColor: "#F5F5F7", borderRadius: "16px", padding: "40px 24px", textAlign: "center" }}>
                <div style={{ marginBottom: "20px", display: "flex", justifyContent: "center" }}>
                  <LettermarkIcon size={56} />
                </div>
                <div style={{ fontSize: "12px", color: "#1A1A2E", fontWeight: 600, letterSpacing: "2px", textTransform: "uppercase" }}>Lettermark</div>
                <div style={{ fontSize: "11px", color: "#6B7280", marginTop: "4px" }}>Favicons, app icons</div>
              </div>
              {/* Icon */}
              <div style={{ backgroundColor: "#F5F5F7", borderRadius: "16px", padding: "40px 24px", textAlign: "center" }}>
                <div style={{ marginBottom: "20px", display: "flex", justifyContent: "center" }}>
                  <DeltaIcon size={56} />
                </div>
                <div style={{ fontSize: "12px", color: "#1A1A2E", fontWeight: 600, letterSpacing: "2px", textTransform: "uppercase" }}>Pictorial Mark</div>
                <div style={{ fontSize: "11px", color: "#6B7280", marginTop: "4px" }}>Δ = Change + Action</div>
              </div>
            </div>

            {/* Dark variants */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px", marginTop: "20px" }}>
              <div style={{ backgroundColor: "#16213E", borderRadius: "16px", padding: "40px 24px", textAlign: "center" }}>
                <div style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "36px", color: "#F5F5F7", letterSpacing: "4px" }}>
                  D<span style={{ position: "relative", display: "inline-block" }}>O<span style={{ position: "absolute", left: "2px", right: "2px", top: "50%", height: "2px", backgroundColor: "#E94560" }}/></span>LIOS
                </div>
                <div style={{ fontSize: "11px", color: "#6B7280", marginTop: "12px", letterSpacing: "1px" }}>ON DARK BACKGROUND</div>
              </div>
              <div style={{ backgroundColor: "#16213E", borderRadius: "16px", padding: "40px 24px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <svg viewBox="0 0 64 64" width={56} height={56}>
                  <path d="M16,8 L16,56 Q48,56 48,32 Q48,8 16,8 Z" fill="#F5F5F7"/>
                  <path d="M22,14 L22,50 Q42,50 42,32 Q42,14 22,14 Z" fill="#16213E"/>
                  <rect x="22" y="29" width="24" height="6" fill="#E94560"/>
                  <polygon points="46,24 58,32 46,40" fill="#E94560"/>
                </svg>
                <div style={{ fontSize: "11px", color: "#6B7280", marginTop: "12px", letterSpacing: "1px" }}>INVERTED LETTERMARK</div>
              </div>
              <div style={{ backgroundColor: "#16213E", borderRadius: "16px", padding: "40px 24px", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                <svg viewBox="0 0 64 64" width={56} height={56}>
                  <polygon points="32,6 4,58 60,58" fill="none" stroke="#F5F5F7" strokeWidth="3.5" strokeLinejoin="round"/>
                  <line x1="32" y1="24" x2="22" y2="44" stroke="#0F3460" strokeWidth="1.8"/>
                  <line x1="32" y1="24" x2="42" y2="44" stroke="#0F3460" strokeWidth="1.8"/>
                  <line x1="22" y1="44" x2="42" y2="44" stroke="#0F3460" strokeWidth="1.8"/>
                  <circle cx="32" cy="24" r="4" fill="#E94560"/>
                  <circle cx="22" cy="44" r="4" fill="#E94560"/>
                  <circle cx="42" cy="44" r="4" fill="#E94560"/>
                </svg>
                <div style={{ fontSize: "11px", color: "#6B7280", marginTop: "12px", letterSpacing: "1px" }}>INVERTED ICON</div>
              </div>
            </div>
          </section>
        )}

        {/* Brand Voice */}
        {(activeSection === "all" || activeSection === "voice") && (
          <section style={{ padding: "60px 0 80px" }}>
            <div style={{ marginBottom: "8px", fontSize: "11px", color: "#E94560", letterSpacing: "4px", textTransform: "uppercase", fontWeight: 500 }}>05</div>
            <h2 style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "32px", margin: "0 0 8px" }}>Brand Voice</h2>
            <p style={{ fontSize: "14px", color: "#6B7280", marginBottom: "36px" }}>
              How Dolios speaks: cunning without arrogance, precise without coldness.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "16px" }}>
              {voiceAttrs.map(v => (
                <div key={v.attr} style={{
                  backgroundColor: "#16213E", borderRadius: "12px", padding: "24px",
                  borderLeft: "3px solid #E94560"
                }}>
                  <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "6px", color: "#F5F5F7" }}>{v.attr}</div>
                  <div style={{ fontSize: "13px", color: "#9CA3AF", lineHeight: 1.6 }}>{v.desc}</div>
                </div>
              ))}
            </div>

            {/* Taglines */}
            <div style={{ marginTop: "36px", backgroundColor: "#16213E", borderRadius: "12px", padding: "28px" }}>
              <div style={{ fontSize: "12px", color: "#C4A35A", letterSpacing: "3px", textTransform: "uppercase", fontWeight: 500, marginBottom: "16px" }}>Tagline Variants</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {[
                  { tag: '"The Crafty Agent"', ctx: "Primary — under wordmark" },
                  { tag: '"Scheme. Execute. Deliver."', ctx: "Marketing / hero sections" },
                  { tag: '"Hermes\' Sharpest Heir"', ctx: "Blog / long-form" },
                  { tag: '"Autonomous intelligence, mythological precision."', ctx: "Enterprise / pitch deck" },
                ].map((t, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: i < 3 ? "1px solid rgba(255,255,255,0.04)" : "none" }}>
                    <span style={{ fontFamily: "Georgia, serif", fontSize: "16px", fontStyle: "italic", color: "#F5F5F7" }}>{t.tag}</span>
                    <span style={{ fontSize: "11px", color: "#6B7280", letterSpacing: "1px" }}>{t.ctx}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Footer */}
        <footer style={{ borderTop: "1px solid rgba(255,255,255,0.06)", padding: "32px 0", textAlign: "center" }}>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
            <DeltaIcon size={20} />
            <span style={{ fontFamily: "Georgia, serif", fontWeight: 700, fontSize: "14px", letterSpacing: "2px" }}>DOLIOS</span>
          </div>
          <div style={{ fontSize: "11px", color: "#6B7280" }}>Brand Identity System v1.0 — March 2026</div>
          <div style={{ fontSize: "11px", color: "#4B5563", marginTop: "4px" }}>Built for the Hermes ecosystem</div>
        </footer>
      </div>
    </div>
  );
}
