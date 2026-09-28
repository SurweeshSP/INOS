import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

@dataclass(order=True)
class BranchAndBoundNode:
    """
    Represents a node in the Branch and Bound search tree.
    """
    id: int = field(compare=False)
    depth: int = field(compare=False)
    parent_id: int = field(compare=False)
    
    # Priority for queue (e.g. objective bound for best-first, or -depth for DFS)
    priority: float = 0.0
    
    # The additional bounds added to the node relative to the root problem
    # Dict mapping variable_name to (lb, ub). We only store the *tightened* bounds.
    bound_updates: Dict[str, Tuple[float, float]] = field(default_factory=dict, compare=False)
    
    # The result of the LP relaxation for this node
    lp_objective: float = field(default=float('inf'), compare=False)
    lp_primal_values: Dict[str, float] = field(default_factory=dict, compare=False)
    is_integer_feasible: bool = field(default=False, compare=False)

class NodeQueue:
    """
    Priority queue for managing active nodes in Branch and Bound.
    """
    def __init__(self, strategy: str = "depth_first"):
        self.strategy = strategy
        self._queue: List[BranchAndBoundNode] = []
        
    def push(self, node: BranchAndBoundNode):
        if self.strategy == "depth_first":
            # Priority is negative depth to pull deepest nodes first
            node.priority = -node.depth
        elif self.strategy == "best_bound":
            # Priority is LP objective bound (assuming minimization)
            node.priority = node.lp_objective
        else:
            # Default to best bound
            node.priority = node.lp_objective
            
        heapq.heappush(self._queue, node)
        
    def pop(self) -> BranchAndBoundNode:
        return heapq.heappop(self._queue)
        
    def is_empty(self) -> bool:
        return len(self._queue) == 0
        
    def __len__(self):
        return len(self._queue)
