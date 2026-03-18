"""
race_management.py - Race Management Module
Creates races, selects drivers and cars from the registered system.
Depends on: registration, crew_management, inventory.
"""
from __future__ import annotations

import data_store
import registration
import crew_management
import inventory


def create_race(name: str, prize_money: float) -> tuple[bool, str]:
    """Create a new race entry."""
    name = name.strip()
    if not name:
        return False, "Race name cannot be empty."
    if prize_money < 0:
        return False, "Prize money cannot be negative."
    race_id = data_store.next_race_id()
    data_store.races[race_id] = {
        "name": name,
        "prize_money": prize_money,
        "participants": [],   # list of {driver_id, vehicle_id}
        "status": "pending",  # pending | active | completed
    }
    return True, f"Race '{name}' created with ID {race_id}. Prize: ${prize_money:,.2f}."


def get_race(race_id: str) -> dict | None:
    return data_store.races.get(race_id)


def race_exists(race_id: str) -> bool:
    return race_id in data_store.races


def list_races() -> list[tuple[str, dict]]:
    return list(data_store.races.items())


def add_participant(race_id: str, driver_id: str, vehicle_id: str) -> tuple[bool, str]:
    """Add a driver-vehicle pair to a pending race.

    Business rules enforced:
    - Race must exist and be pending.
    - Driver must be registered.
    - Driver must have the 'driver' role.
    - Driver must be available.
    - Vehicle must exist and be in good condition.
    - No duplicate drivers or vehicles in the same race.
    """
    if not race_exists(race_id):
        return False, f"Race '{race_id}' not found."

    race = data_store.races[race_id]
    if race["status"] != "pending":
        return False, f"Race '{race_id}' is already {race['status']} — cannot add participants."

    # Check for duplicates first — gives a more informative error than "unavailable"
    for p in race["participants"]:
        if p["driver_id"] == driver_id:
            return False, f"Driver '{driver_id}' is already entered in this race."
        if p["vehicle_id"] == vehicle_id:
            return False, f"Vehicle '{vehicle_id}' is already entered in this race."

    # Validate driver
    if not registration.is_registered(driver_id):
        return False, f"Driver '{driver_id}' is not registered. Register them first."
    role = crew_management.get_role(driver_id)
    if role != "driver":
        return False, f"Member '{driver_id}' has role '{role}', not 'driver'. Only drivers may race."
    if not crew_management.is_available(driver_id):
        return False, f"Driver '{driver_id}' is currently unavailable."

    # Validate vehicle
    vehicle = inventory.get_vehicle(vehicle_id)
    if vehicle is None:
        return False, f"Vehicle '{vehicle_id}' not found in inventory."
    if vehicle["condition"] != "good":
        return False, f"Vehicle '{vehicle_id}' is '{vehicle['condition']}' — only 'good' vehicles may race."

    race["participants"].append({"driver_id": driver_id, "vehicle_id": vehicle_id})
    crew_management.set_availability(driver_id, False)
    inventory.assign_driver_to_vehicle(vehicle_id, driver_id)

    driver_name = registration.get_member(driver_id)["name"]
    veh_name = inventory.get_vehicle(vehicle_id)["name"]
    return True, f"'{driver_name}' entered race '{race['name']}' in '{veh_name}'."


def remove_participant(race_id: str, driver_id: str) -> tuple[bool, str]:
    """Remove a participant from a pending race."""
    if not race_exists(race_id):
        return False, f"Race '{race_id}' not found."
    race = data_store.races[race_id]
    if race["status"] != "pending":
        return False, "Cannot remove participants from a started or completed race."
    for p in race["participants"]:
        if p["driver_id"] == driver_id:
            race["participants"].remove(p)
            crew_management.set_availability(driver_id, True)
            inventory.assign_driver_to_vehicle(p["vehicle_id"], None)
            name = registration.get_member(driver_id)["name"]
            return True, f"'{name}' removed from race."
    return False, f"Driver '{driver_id}' not found in race '{race_id}'."


def start_race(race_id: str) -> tuple[bool, str]:
    """Change race status from pending to active."""
    if not race_exists(race_id):
        return False, f"Race '{race_id}' not found."
    race = data_store.races[race_id]
    if race["status"] != "pending":
        return False, f"Race is already '{race['status']}'."
    if len(race["participants"]) < 2:
        return False, "A race needs at least 2 participants."
    race["status"] = "active"
    return True, f"Race '{race['name']}' has started with {len(race['participants'])} participants!"


def list_race_participants(race_id: str) -> list[dict]:
    """Return participant list for a race."""
    race = get_race(race_id)
    if not race:
        return []
    result = []
    for p in race["participants"]:
        driver = registration.get_member(p["driver_id"])
        vehicle = inventory.get_vehicle(p["vehicle_id"])
        result.append({
            "driver_id": p["driver_id"],
            "driver_name": driver["name"] if driver else "Unknown",
            "vehicle_id": p["vehicle_id"],
            "vehicle_name": vehicle["name"] if vehicle else "Unknown",
            "skill": driver["skill_level"] if driver else 0,
        })
    return result


# ── CLI Menu ──────────────────────────────────────────────────────────────────

def race_menu():
    while True:
        print("\n── RACE MANAGEMENT ───────────────────")
        print("  1. Create race")
        print("  2. Add participant")
        print("  3. Remove participant")
        print("  4. Start race")
        print("  5. List races")
        print("  6. View race participants")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            name = input("  Race name: ").strip()
            try:
                prize = float(input("  Prize money: $").strip())
            except ValueError:
                print("  ERR: Enter a number.")
                continue
            ok, msg = create_race(name, prize)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            race_id = input("  Race ID: ").strip()
            driver_id = input("  Driver ID: ").strip()
            vehicle_id = input("  Vehicle ID: ").strip()
            ok, msg = add_participant(race_id, driver_id, vehicle_id)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "3":
            race_id = input("  Race ID: ").strip()
            driver_id = input("  Driver ID: ").strip()
            ok, msg = remove_participant(race_id, driver_id)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "4":
            race_id = input("  Race ID: ").strip()
            ok, msg = start_race(race_id)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "5":
            races = list_races()
            if not races:
                print("  No races created.")
            else:
                print(f"\n  {'ID':<6} {'Name':<22} {'Prize':>10} {'Status':<12} {'#Participants':>14}")
                print("  " + "-" * 68)
                for rid, r in races:
                    print(f"  {rid:<6} {r['name']:<22} ${r['prize_money']:>9,.0f} {r['status']:<12} {len(r['participants']):>14}")

        elif choice == "6":
            race_id = input("  Race ID: ").strip()
            participants = list_race_participants(race_id)
            if not participants:
                print("  No participants or race not found.")
            else:
                race = get_race(race_id)
                print(f"\n  Race: {race['name']} [{race['status'].upper()}]")
                print(f"  {'Driver ID':<8} {'Driver Name':<20} {'Vehicle ID':<10} {'Vehicle Name':<18} {'Skill':>5}")
                print("  " + "-" * 66)
                for p in participants:
                    print(f"  {p['driver_id']:<8} {p['driver_name']:<20} {p['vehicle_id']:<10} {p['vehicle_name']:<18} {p['skill']:>5}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
