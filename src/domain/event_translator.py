import re
import time
from typing import Optional
from src.data_models import Event, EventType

class EventTranslator:
    
    @staticmethod
    def parse_command(command: str) -> Optional[Event]:
        """
        Translates a natural language command into the formal Event model.
        Examples:
        - "increase W01 capacity by 20%"
        - "increase C01 demand by 15%"
        - "increase P01->W01 cost by 10%"
        - "block route P01->W01"
        - "increase lead time P01->W01 by 2 days"
        - "P02 is unavailable tomorrow"
        """
        cmd_lower = command.lower()
        
        # 1. Capacity Change
        # "increase W01 capacity by 20%" or "reduce supplier S07 capacity by 20%"
        match = re.search(r'(increase|reduce|decrease|drop)(?: \w+)? (\w+) capacity by (\d+(?:\.\d+)?)%', cmd_lower)
        if match:
            direction = match.group(1)
            target = match.group(2).upper()
            magnitude = float(match.group(3)) / 100.0
            if direction in ['reduce', 'decrease', 'drop']:
                magnitude = -magnitude
            return Event(
                event_type=EventType.CAPACITY_CHANGE,
                affected_entities=[target],
                magnitude=magnitude
            )
            
        # Capacity decrease / unavailable
        # "P02 is unavailable tomorrow"
        match = re.search(r'(\w+) is unavailable', cmd_lower)
        if match:
            target = match.group(1).upper()
            return Event(
                event_type=EventType.FACILITY_DOWN,
                affected_entities=[target],
                magnitude=-1.0 # 100% loss
            )

        # 2. Demand Change
        # "increase C01 demand by 15%" or "decrease customer C01 demand by 10%"
        match = re.search(r'(increase|reduce|decrease|drop)(?: \w+)? (\w+) demand by (\d+(?:\.\d+)?)%', cmd_lower)
        if match:
            direction = match.group(1)
            target = match.group(2).upper()
            magnitude = float(match.group(3)) / 100.0
            if direction in ['reduce', 'decrease', 'drop']:
                magnitude = -magnitude
            return Event(
                event_type=EventType.DEMAND_CHANGE,
                affected_entities=[target],
                magnitude=magnitude
            )

        # 3. Route / Edge Changes
        # "increase P01->W01 cost by 10%" or "reduce P01->W01 cost by 5%"
        match = re.search(r'(increase|reduce|decrease|drop)(?: \w+)? (\w+)->(\w+) cost by (\d+(?:\.\d+)?)%', cmd_lower)
        if match:
            direction = match.group(1)
            source = match.group(2).upper()
            dest = match.group(3).upper()
            magnitude = float(match.group(4)) / 100.0
            if direction in ['reduce', 'decrease', 'drop']:
                magnitude = -magnitude
            return Event(
                event_type=EventType.COST_CHANGE,
                affected_entities=[f"{source}_{dest}"],
                magnitude=magnitude
            )
            
        # "increase lead time P01->W01 by 2 days" or "decrease lead time P01->W01 by 1 days"
        match = re.search(r'(increase|reduce|decrease|drop) lead time (\w+)->(\w+) by (\d+(?:\.\d+)?) days', cmd_lower)
        if match:
            direction = match.group(1)
            source = match.group(2).upper()
            dest = match.group(3).upper()
            magnitude = float(match.group(4))
            if direction in ['reduce', 'decrease', 'drop']:
                magnitude = -magnitude
            return Event(
                event_type=EventType.SERVICE_CHANGE,
                affected_entities=[f"{source}_{dest}"],
                magnitude=magnitude
            )

        # "block route P01->W01"
        match = re.search(r'block route (\w+)->(\w+)', cmd_lower)
        if match:
            source = match.group(1).upper()
            dest = match.group(2).upper()
            return Event(
                event_type=EventType.ROUTE_BLOCKED,
                affected_entities=[f"{source}_{dest}"],
                magnitude=-1.0
            )

        return None
