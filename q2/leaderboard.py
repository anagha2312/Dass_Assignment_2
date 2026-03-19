"""
leaderboard.py - Leaderboard Module  [EXTRA MODULE 1]
Tracks driver standings, points, win counts, and career earnings.
Updated by the Results module after each race completes.
Depends on: data_store, registration.
"""
from __future__ import annotations

import data_store
import registration


def update_standings(
    driver_id: str,
    position: int,
    points_earned: int,
    prize_earned: float = 0.0,
) -> tuple[bool, str]:
    """Update a driver's leaderboard entry after a race."""
    if not registration.is_registered(driver_id):
        return False, f"Driver '{driver_id}' is not registered."

    if driver_id not in data_store.leaderboard:
        data_store.leaderboard[driver_id] = {
            "wins": 0,
            "total_races": 0,
            "total_points": 0,
            "earnings": 0.0,
            "podiums": 0,   # top-3 finishes
        }

    entry = data_store.leaderboard[driver_id]
    entry["total_races"] += 1
    entry["total_points"] += points_earned
    entry["earnings"] += prize_earned

    if position == 1:
        entry["wins"] += 1
    if position <= 3:
        entry["podiums"] += 1

    return True, f"Leaderboard updated for driver '{driver_id}'."


def get_standings() -> list[dict]:
    """Return leaderboard sorted by points (desc), then wins (desc)."""
    result = []
    for driver_id, stats in data_store.leaderboard.items():
        member = registration.get_member(driver_id)
        result.append({
            "driver_id": driver_id,
            "name": member["name"] if member else driver_id,
            **stats,
        })
    result.sort(key=lambda x: (-x["total_points"], -x["wins"]))
    return result


def get_driver_stats(driver_id: str) -> dict | None:
    """Return stats for a single driver, or None if no races recorded."""
    if driver_id not in data_store.leaderboard:
        return None
    member = registration.get_member(driver_id)
    return {
        "driver_id": driver_id,
        "name": member["name"] if member else driver_id,
        **data_store.leaderboard[driver_id],
    }


def display_leaderboard() -> str:
    """Return a formatted leaderboard string."""
    standings = get_standings()
    if not standings:
        return "  Leaderboard is empty — no races completed yet."

    lines = [
        "\n  ╔══ DRIVER LEADERBOARD ══════════════════════════════════════════╗",
        f"  {'Rank':<5} {'Name':<20} {'Pts':>5} {'Wins':>5} {'Races':>6} {'Podiums':>8} {'Earnings':>12}",
        "  " + "─" * 64,
    ]
    for rank, s in enumerate(standings, start=1):
        lines.append(
            f"  {rank:<5} {s['name']:<20} {s['total_points']:>5} "
            f"{s['wins']:>5} {s['total_races']:>6} {s['podiums']:>8} "
            f"${s['earnings']:>10,.2f}"
        )
    lines.append("  ╚" + "═" * 64 + "╝")
    return "\n".join(lines)


def reset_leaderboard() -> tuple[bool, str]:
    """Clear all leaderboard data (admin action)."""
    data_store.leaderboard.clear()
    return True, "Leaderboard has been reset."


# ── CLI Menu ──────────────────────────────────────────────────────────────────

def leaderboard_menu():
    while True:
        print("\n── LEADERBOARD ───────────────────────")
        print("  1. Show full leaderboard")
        print("  2. View driver stats")
        print("  3. Reset leaderboard")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            print(display_leaderboard())

        elif choice == "2":
            driver_id = input("  Driver ID: ").strip()
            stats = get_driver_stats(driver_id)
            if not stats:
                print(f"  No stats found for '{driver_id}'.")
            else:
                print(f"\n  Driver  : {stats['name']} ({stats['driver_id']})")
                print(f"  Races   : {stats['total_races']}")
                print(f"  Wins    : {stats['wins']}")
                print(f"  Podiums : {stats['podiums']}")
                print(f"  Points  : {stats['total_points']}")
                print(f"  Earnings: ${stats['earnings']:,.2f}")

        elif choice == "3":
            confirm = input("  Reset leaderboard? (yes/no): ").strip().lower()
            if confirm in ("yes", "y"):
                ok, msg = reset_leaderboard()
                print(f"  {'OK' if ok else 'ERR'}: {msg}")
            else:
                print("  Cancelled.")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
