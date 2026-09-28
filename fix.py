import sys

file_path = r"c:\Users\surwe\Project\SupplyChainOptii\sih119-ui\src\components\SupplyChainNetworkView.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the start of Post-Optimization Results
marker = "{/* Post-Optimization Results */}"
idx = content.find(marker)

if idx != -1:
    # Keep everything up to the marker
    new_content = content[:idx]
    
    # Append the correct ending
    new_content += """{/* Post-Optimization Results */}
      {graphState === 'VALIDATED_DECISION' && (
        <OptimizedNetworkDashboard decisionPackage={decisionPackage} />
      )}

    </div>
  );
};
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed SupplyChainNetworkView.tsx")
else:
    print("Could not find marker.")
