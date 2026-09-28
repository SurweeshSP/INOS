import sys

file_path = r"c:\Users\surwe\Project\SupplyChainOptii\sih119-ui\src\components\SupplyChainNetworkView.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replacement 1
content = content.replace(
    "import { NativeCanvasGraph } from './NativeCanvasGraph';",
    "import { NativeCanvasGraph } from './NativeCanvasGraph';\nimport { OptimizedNetworkDashboard } from './OptimizedNetworkDashboard';"
)

# Replacement 2
old_header = """        <div>
          <h2 className="text-xl font-bold font-serif-claude text-[#f3efe6]">{t.network}</h2>
          <p className="text-xs text-[#867f74] font-mono mt-1">{t.subtitle}</p>
        </div>"""
new_header = """        <div>
          <h2 className="text-xl font-bold font-serif-claude text-[#f3efe6] flex items-center gap-3">
            {graphState === 'VALIDATED_DECISION' ? 'Supply Chain Network (Optimized)' : t.network}
            {graphState === 'VALIDATED_DECISION' && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3" /> VERIFIED SOLUTION
              </span>
            )}
          </h2>
          <p className="text-xs text-[#867f74] font-mono mt-1">
            {graphState === 'VALIDATED_DECISION' ? 'Optimized flow after Supplier S02 capacity -25%. Showing active flows and allocations.' : t.subtitle}
          </p>
        </div>"""
content = content.replace(old_header, new_header)

# Replacement 3 (Main Workspace wrap)
old_main = """      {/* Main Workspace */}
      <div className="flex-1 flex gap-6 px-6 min-h-[600px] relative">"""
new_main = """      {/* Main Workspace */}
      {graphState !== 'VALIDATED_DECISION' && (
      <div className="flex-1 flex gap-6 px-6 min-h-[600px] relative">"""
content = content.replace(old_main, new_main)

# Replacement 4 (Close Main Workspace)
old_close = """            </div>
          </div>
        )}
      </div>

      {/* Post-Optimization Results */}"""
new_close = """            </div>
          </div>
        )}
      </div>
      )}

      {/* Post-Optimization Results */}"""
content = content.replace(old_close, new_close)

# Replacement 5 (Post-Optimization Results block)
lines = content.split('\n')
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "{/* Post-Optimization Results */}" in line:
        start_idx = i
        break
for i in range(len(lines)-1, -1, -1):
    if lines[i].strip() == "</div>":
        if lines[i-1].strip() == ")}":
            end_idx = i - 1
            break

if start_idx != -1 and end_idx != -1:
    lines = lines[:start_idx] + [
        "      {/* Post-Optimization Results */}",
        "      {graphState === 'VALIDATED_DECISION' && (",
        "        <OptimizedNetworkDashboard decisionPackage={decisionPackage} />",
        "      )}"
    ] + lines[end_idx+1:]
    content = '\n'.join(lines)
else:
    print("Could not find Post-Optimization Results block bounds.")
    sys.exit(1)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Success")
