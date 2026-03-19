"""
results.py - Results Module
Records race outcomes, updates driver rankings, and handles prize money.
Depends on: race_management, inventory, crew_management, leaderboard.
"""
from __future__ import annotations

import data_store
import registration
import crew_management
import inventory
import race_management
import leaderboard


def record_result(
    race_id: str,
    finishing_order: list[str],       # ordered list of driver_ids, 1st to last
    damaged_vehicle_ids: list[str],    # vehicles that were damaged in this race
) -> tuple[bool, str]:
    """Record the result of a completed race.

    Business rules:
    - Race must exist and be 'active'.
    - finishing_order must include every participant driver_id.
    - Damaged vehicles are updated to 'damaged' in inventory.
    - Prize money is added to cash balance (first-place earns full prize).
    - Leaderboard is updated for each driver.
    - Drivers and vehicles are released (availability restored).
    """
    if not race_management.race_exists(race_id):
        return False, f"Race '{race_id}' not found."

    race = race_management.get_race(race_id)
    if race["status"] != "active":
        return False, f"Race '{race_id}' is '{race['status']}', not 'active'. Start it first."

    participant_ids = {p["driver_id"] for p in race["participants"]}

    # Validate finishing order
    if set(finishing_order) != participant_ids:
        return False, (
            f"finishing_order must include all participant driver IDs. "
            f"Expected: {sorted(participant_ids)}, Got: {sorted(finishing_order)}."
        )

    # Update vehicle conditions
    for vid in damaged_vehicle_ids:
        inventory.update_vehicle_condition(vid, "damaged")

    # Distribute prize money (winner gets full prize)
    winner_id = finishing_order[0]
    prize = race["prize_money"]
    if prize > 0:
        inventory.add_cash(prize)

    # Update leaderboard for all participants
    for position, driver_id in enumerate(finishing_order, start=1):
        points = max(0, len(finishing_order) - position + 1)  # descending points
        leaderboard.update_standings(driver_id, position, points, prize if position == 1 else 0)

    # Release drivers and vehicles
    for p in race["participants"]:
        crew_management.set_availability(p["driver_id"], True)
        inventory.assign_driver_to_vehicle(p["vehicle_id"], None)

    # Mark race completed
    race["status"] = "completed"

    # Store result record
    data_store.race_results[race_id] = {
        "positions": finishing_order,
        "damaged_vehicles": damaged_vehicle_ids,
        "prize_distributed": prize > 0,
        "prize_amount": prize,
    }

    winner_name = registration.get_member(winner_id)["name"]
    return True, (
        f"Race '{race['name']}' completed. Winner: {winner_name}. "
        f"Prize ${prize:,.2f} added to cash balance."
    )


def get_results(race_id: str) -> dict | None:
    return data_store.race_results.get(race_id)


def list_results() -> list[tuple[str, dict]]:
    return list(data_store.race_results.items())


def show_race_result(race_id: str) -> str:
    """Return a formatted string of race results."""
    result = get_results(race_id)
    race = race_management.get_race(race_id)
    if not result or not race:
        return f"No results found for race '{race_id}'."

    lines = [f"\n  === Results: {race['name']} ==="]
    for pos, driver_id in enumerate(result["positions"], start=1):
        member = registration.get_member(driver_id)
        name = member["name"] if member else driver_id
        medal = {1: "1st", 2: "2nd", 3: "3rd"}.get(pos, f"{pos}th")
        prize_note = f"  <-- WINNER: ${result['prize_amount']:,.2f}" if pos == 1 else ""
        lines.append(f"  {medal:>4}  {driver_id:<6} {name}{prize_note}")

    if result["damaged_vehicles"]:
        lines.append(f"\n  Damaged vehicles: {', '.join(result['damaged_vehicles'])}")
    return "\n".join(lines)


# ── CLI Menu ──────────────────────────────────────────────────────────────────

def results_menu():
    while True:
        print("\n── RESULTS ───────────────────────────")
        print("  1. Record race result")
        print("  2. View race result")
        print("  3. List all results")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            race_id = input("  Race ID: ").strip()
            race = race_management.get_race(race_id)
            if not race:
                print(f"  ERR: Race '{race_id}' not found.")
                continue

            participants = race_management.list_race_participants(race_id)
            if not participants:
                print("  No participants found.")
                continue

            print("\n  Participants:")
            for p in participants:
                print(f"    {p['driver_id']} - {p['driver_name']}")

            print("\n  Enter finishing order (driver IDs, comma-separated, 1st to last):")
            order_input = input("  ").strip()
            finishing_order = [x.strip() for x in order_input.split(",") if x.strip()]

            print("  Enter damaged vehicle IDs (comma-separated, or leave blank):")
            dmg_input = input("  ").strip()
            damaged = [x.strip() for x in dmg_input.split(",") if x.strip()] if dmg_input else []

            ok, msg = record_result(race_id, finishing_order, damaged)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            race_id = input("  Race ID: ").strip()
            print(show_race_result(race_id))

        elif choice == "3":
            results = list_results()
            if not results:
                print("  No results recorded yet.")
            else:
                for rid, r in results:
                    race = race_management.get_race(rid)
                    rname = race["name"] if race else rid
                    winner_id = r["positions"][0]
                    member = registration.get_member(winner_id)
                    wname = member["name"] if member else winner_id
                    print(f"  {rid}: '{rname}' — Winner: {wname} — Prize: ${r['prize_amount']:,.2f}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
