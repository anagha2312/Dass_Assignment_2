"""
mission_planning.py - Mission Planning Module
Assigns missions and verifies required crew roles are available.
Depends on: registration, crew_management, inventory (for mechanic-related checks).
"""
from __future__ import annotations

import data_store
import registration
import crew_management
import inventory

MISSION_TYPES = {"delivery", "rescue", "surveillance", "extraction", "transport"}


def create_mission(
    name: str,
    mission_type: str,
    required_roles: list[str],
) -> tuple[bool, str]:
    """Create a new mission definition."""
    name = name.strip()
    mission_type = mission_type.strip().lower()
    if not name:
        return False, "Mission name cannot be empty."
    if mission_type not in MISSION_TYPES:
        return False, f"Invalid mission type. Valid types: {', '.join(sorted(MISSION_TYPES))}."
    if not required_roles:
        return False, "At least one required role must be specified."

    from registration import VALID_ROLES
    for role in required_roles:
        if role.lower() not in VALID_ROLES:
            return False, f"Invalid role '{role}' in required_roles."

    mission_id = data_store.next_mission_id()
    data_store.missions[mission_id] = {
        "name": name,
        "type": mission_type,
        "required_roles": [r.lower() for r in required_roles],
        "assigned_crew": [],
        "status": "planned",   # planned | active | completed | failed
    }
    return True, f"Mission '{name}' ({mission_type}) created with ID {mission_id}."


def get_mission(mission_id: str) -> dict | None:
    return data_store.missions.get(mission_id)


def mission_exists(mission_id: str) -> bool:
    return mission_id in data_store.missions


def list_missions() -> list[tuple[str, dict]]:
    return list(data_store.missions.items())


def check_required_roles(mission_id: str) -> tuple[bool, str]:
    """Verify that at least one available crew member exists for each required role."""
    mission = get_mission(mission_id)
    if not mission:
        return False, f"Mission '{mission_id}' not found."

    missing_roles = []
    for role in mission["required_roles"]:
        available = crew_management.get_available_members_by_role(role)
        if not available:
            missing_roles.append(role)

    if missing_roles:
        return False, f"No available crew for role(s): {', '.join(missing_roles)}. Mission cannot start."
    return True, "All required roles have available crew members."


def assign_mission_crew(mission_id: str, crew_ids: list[str]) -> tuple[bool, str]:
    """Assign specific crew members to a planned mission.

    Business rules:
    - Mission must be in 'planned' status.
    - Each crew_id must be registered and available.
    - The assigned crew must collectively cover all required roles.
    - If a required role is 'mechanic' and a car is damaged, verifies mechanic exists.
    """
    if not mission_exists(mission_id):
        return False, f"Mission '{mission_id}' not found."

    mission = data_store.missions[mission_id]
    if mission["status"] != "planned":
        return False, f"Mission is already '{mission['status']}', cannot reassign crew."

    # Validate each crew member
    for cid in crew_ids:
        if not registration.is_registered(cid):
            return False, f"Member '{cid}' is not registered."
        if not crew_management.is_available(cid):
            return False, f"Member '{cid}' is not available."

    # Check role coverage
    assigned_roles = {crew_management.get_role(cid) for cid in crew_ids}
    missing = [r for r in mission["required_roles"] if r not in assigned_roles]
    if missing:
        return False, f"Assigned crew does not cover required role(s): {', '.join(missing)}."

    # Check mechanic-vehicle dependency: if mechanic required, ensure a damaged vehicle exists
    if "mechanic" in mission["required_roles"]:
        damaged_vehicles = [
            vid for vid, v in data_store.vehicles.items()
            if v["condition"] == "damaged"
        ]
        if not damaged_vehicles:
            return False, "Mission requires a mechanic, but no damaged vehicles need repair."

    # Assign crew
    mission["assigned_crew"] = list(crew_ids)
    for cid in crew_ids:
        crew_management.set_availability(cid, False)

    names = [registration.get_member(cid)["name"] for cid in crew_ids]
    return True, f"Crew assigned to mission '{mission['name']}': {', '.join(names)}."


def start_mission(mission_id: str) -> tuple[bool, str]:
    """Begin a planned mission (changes status to active)."""
    if not mission_exists(mission_id):
        return False, f"Mission '{mission_id}' not found."

    mission = data_store.missions[mission_id]
    if mission["status"] != "planned":
        return False, f"Mission is '{mission['status']}', not 'planned'."
    if not mission["assigned_crew"]:
        return False, "No crew assigned. Assign crew before starting the mission."

    # Verify assigned crew still covers all required roles
    assigned_roles = {crew_management.get_role(cid) for cid in mission["assigned_crew"]}
    missing = [r for r in mission["required_roles"] if r not in assigned_roles]
    if missing:
        return False, f"Assigned crew does not cover role(s): {', '.join(missing)}. Reassign crew."

    mission["status"] = "active"
    return True, f"Mission '{mission['name']}' is now ACTIVE."


def complete_mission(mission_id: str, success: bool = True) -> tuple[bool, str]:
    """Mark a mission as completed or failed, and release crew."""
    if not mission_exists(mission_id):
        return False, f"Mission '{mission_id}' not found."

    mission = data_store.missions[mission_id]
    if mission["status"] != "active":
        return False, f"Mission is '{mission['status']}', not 'active'."

    # Release assigned crew
    for cid in mission["assigned_crew"]:
        crew_management.set_availability(cid, True)

    new_status = "completed" if success else "failed"
    mission["status"] = new_status

    # If mechanic was on a repair mission, mark relevant vehicles as repaired
    if "mechanic" in mission["required_roles"] and success:
        for vid, v in data_store.vehicles.items():
            if v["condition"] == "damaged":
                inventory.update_vehicle_condition(vid, "good")
                break  # repair one vehicle per mission

    return True, f"Mission '{mission['name']}' marked as {new_status.upper()}. Crew released."


# ── CLI Menu ──────────────────────────────────────────────────────────────────

def mission_menu():
    while True:
        print("\n── MISSION PLANNING ──────────────────")
        print("  1. Create mission")
        print("  2. Assign crew to mission")
        print("  3. Check role availability for mission")
        print("  4. Start mission")
        print("  5. Complete/fail mission")
        print("  6. List missions")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            name = input("  Mission name: ").strip()
            print(f"  Types: {', '.join(sorted(MISSION_TYPES))}")
            mtype = input("  Type: ").strip()
            from registration import VALID_ROLES
            print(f"  Roles: {', '.join(sorted(VALID_ROLES))}")
            roles_raw = input("  Required roles (comma-separated): ").strip()
            roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
            ok, msg = create_mission(name, mtype, roles)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            mid = input("  Mission ID: ").strip()
            crew_raw = input("  Crew member IDs (comma-separated): ").strip()
            crew_ids = [c.strip() for c in crew_raw.split(",") if c.strip()]
            ok, msg = assign_mission_crew(mid, crew_ids)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "3":
            mid = input("  Mission ID: ").strip()
            ok, msg = check_required_roles(mid)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "4":
            mid = input("  Mission ID: ").strip()
            ok, msg = start_mission(mid)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "5":
            mid = input("  Mission ID: ").strip()
            outcome = input("  Outcome (success/fail): ").strip().lower()
            success = outcome in ("success", "s", "yes", "y", "1")
            ok, msg = complete_mission(mid, success)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "6":
            missions = list_missions()
            if not missions:
                print("  No missions created.")
            else:
                print(f"\n  {'ID':<6} {'Name':<22} {'Type':<14} {'Status':<12} {'Crew'}")
                print("  " + "-" * 70)
                for mid, m in missions:
                    crew = ", ".join(m["assigned_crew"]) or "None"
                    print(f"  {mid:<6} {m['name']:<22} {m['type']:<14} {m['status']:<12} {crew}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
