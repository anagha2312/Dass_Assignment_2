"""
data_store.py - Shared in-memory data store for StreetRace Manager.
All modules import from this file to read/write shared state.
"""

# ── Crew Members ──────────────────────────────────────────────────────────────
# { member_id: {name, role, skill_level, available} }
crew_members: dict = {}
_member_counter: int = 0

# ── Vehicles ──────────────────────────────────────────────────────────────────
# { vehicle_id: {name, model, speed_rating, condition, assigned_driver} }
vehicles: dict = {}
_vehicle_counter: int = 0

# ── Spare Parts & Tools ───────────────────────────────────────────────────────
# { part_name: quantity }
spare_parts: dict = {}

# ── Cash Balance ──────────────────────────────────────────────────────────────
cash_balance: float = 0.0

# ── Races ─────────────────────────────────────────────────────────────────────
# { race_id: {name, prize_money, participants, status} }
races: dict = {}
_race_counter: int = 0

# ── Race Results ──────────────────────────────────────────────────────────────
# { race_id: {positions, damaged_vehicles, prize_distributed} }
race_results: dict = {}

# ── Missions ──────────────────────────────────────────────────────────────────
# { mission_id: {name, type, required_roles, assigned_crew, status} }
missions: dict = {}
_mission_counter: int = 0

# ── Leaderboard ───────────────────────────────────────────────────────────────
# { driver_id: {wins, total_races, total_points, earnings} }
leaderboard: dict = {}

# ── Maintenance Log ───────────────────────────────────────────────────────────
# [ {vehicle_id, mechanic_id, description, status, timestamp} ]
maintenance_log: list = []
_maintenance_counter: int = 0


def next_member_id() -> str:
    global _member_counter
    _member_counter += 1
    return f"M{_member_counter:03d}"


def next_vehicle_id() -> str:
    global _vehicle_counter
    _vehicle_counter += 1
    return f"V{_vehicle_counter:03d}"


def next_race_id() -> str:
    global _race_counter
    _race_counter += 1
    return f"R{_race_counter:03d}"


def next_mission_id() -> str:
    global _mission_counter
    _mission_counter += 1
    return f"MS{_mission_counter:03d}"


def next_maintenance_id() -> str:
    global _maintenance_counter
    _maintenance_counter += 1
    return f"MNT{_maintenance_counter:03d}"


def reset_all():
    """Reset all data (used in testing)."""
    global crew_members, vehicles, spare_parts, cash_balance, races
    global race_results, missions, leaderboard, maintenance_log
    global _member_counter, _vehicle_counter, _race_counter
    global _mission_counter, _maintenance_counter
    crew_members.clear()
    vehicles.clear()
    spare_parts.clear()
    cash_balance = 0.0
    races.clear()
    race_results.clear()
    missions.clear()
    leaderboard.clear()
    maintenance_log.clear()
    _member_counter = 0
    _vehicle_counter = 0
    _race_counter = 0
    _mission_counter = 0
    _maintenance_counter = 0
