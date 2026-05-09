from pathlib import Path
import json
from src.aiditor.analyzer import analyze_script

script = Path("examples/be_delusional.md").read_text()
analysis = analyze_script(script)

# Save full output to a file you can inspect
output_path = Path("examples/sample_analysis.json")
output_path.write_text(analysis.model_dump_json(indent=2))
print(f"Full analysis saved to {output_path}\n")

# Print summary to terminal
print("=" * 70)
print("OVERALL ASSESSMENT")
print("=" * 70)
print(analysis.overall_assessment)

print("\n" + "=" * 70)
print(f"STRUCTURAL SUGGESTIONS ({len(analysis.structural_suggestions)})")
print("=" * 70)
for i, s in enumerate(analysis.structural_suggestions, 1):
    print(f"\n{i}. [{s.type.upper()}] {s.section}")
    print(f"   → {s.rationale}")

print("\n" + "=" * 70)
print(f"LINE EDITS ({len(analysis.line_edits)})")
print("=" * 70)
for i, e in enumerate(analysis.line_edits, 1):
    print(f"\n{i}. ORIGINAL: {e.original}")
    print(f"   SUGGESTED: {e.suggested}")
    print(f"   REASON: {e.reason}")

print("\n" + "=" * 70)
print(f"B-ROLL OPPORTUNITIES ({len(analysis.broll_opportunities)})")
print("=" * 70)
for i, shot in enumerate(analysis.broll_opportunities, 1):
    print(f"\n{i}. [{shot.priority.upper()}] {shot.timestamp_estimate}")
    print(f"   EXCERPT: {shot.script_excerpt}")
    print(f"   VISUAL: {shot.suggested_visual}")
    print(f"   TOOL: {shot.tool_recommendation}")
    print(f"   WHY: {shot.rationale}")

print("\n" + "=" * 70)
print(f"MUSIC TONE PER SECTION ({len(analysis.music_tone_per_section)})")
print("=" * 70)
for i, m in enumerate(analysis.music_tone_per_section, 1):
    print(f"\n{i}. {m.section}")
    print(f"   TONE: {m.tone} | TEMPO: {m.tempo}")
    print(f"   WHY: {m.rationale}")