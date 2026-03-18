"""
crew_management.py - Crew Management Module
Manages roles and records skill levels for each crew member.
Depends on: registration (to verify members exist before modifying them).
"""
from __future__ import annotations

import data_store
import registration

VALID_ROLES = registration.VALID_ROLES
MAX_SKILL = 10
MIN_SKILL = 1


def assign_role(member_id: str, new_role: str) -> tuple[bool, str]:
    """Change the role of a registered crew member."""
    if not registration.is_registered(member_id):
        return False, f"No member with ID '{member_id}'. Register them first."
    new_role = new_role.strip().lower()
    if new_role not in VALID_ROLES:
        return False, f"Invalid role '{new_role}'. Valid roles: {', '.join(sorted(VALID_ROLES))}."
    old_role = data_store.crew_members[member_id]["role"]
    data_store.crew_members[member_id]["role"] = new_role
    name = data_store.crew_members[member_id]["name"]
    return True, f"'{name}' role changed from {old_role} to {new_role}."


def update_skill(member_id: str, skill_level: int) -> tuple[bool, str]:
    """Set the skill level (1–10) for a registered crew member."""
    if not registration.is_registered(member_id):
        return False, f"No member with ID '{member_id}'. Register them first."
    if not (MIN_SKILL <= skill_level <= MAX_SKILL):
        return False, f"Skill level must be between {MIN_SKILL} and {MAX_SKILL}."
    data_store.crew_members[member_id]["skill_level"] = skill_level
    name = data_store.crew_members[member_id]["name"]
    return True, f"'{name}' skill level set to {skill_level}."


def get_role(member_id: str) -> str | None:
    """Return the role of a crew member, or None if not found."""
    member = registration.get_member(member_id)
    return member["role"] if member else None


def get_skill(member_id: str) -> int | None:
    """Return the skill level of a crew member, or None if not found."""
    member = registration.get_member(member_id)
    return member["skill_level"] if member else None


def is_available(member_id: str) -> bool:
    """Return True if the member exists and is available."""
    member = registration.get_member(member_id)
    return bool(member and member["available"])


def set_availability(member_id: str, available: bool) -> tuple[bool, str]:
    """Set availability status for a crew member."""
    if not registration.is_registered(member_id):
        return False, f"No member with ID '{member_id}'."
    data_store.crew_members[member_id]["available"] = available
    name = data_store.crew_members[member_id]["name"]
    status = "available" if available else "unavailable"
    return True, f"'{name}' marked as {status}."


def get_members_by_role(role: str) -> list[tuple[str, dict]]:
    """Return all members with the given role."""
    role = role.lower()
    return [
        (mid, m)
        for mid, m in data_store.crew_members.items()
        if m["role"] == role
    ]


def get_available_members_by_role(role: str) -> list[tuple[str, dict]]:
    """Return available members with the given role."""
    return [
        (mid, m)
        for mid, m in get_members_by_role(role)
        if m["available"]
    ]


def list_crew_by_role() -> dict[str, list]:
    """Return a dict grouping member summaries by role."""
    result: dict[str, list] = {}
    for mid, m in data_store.crew_members.items():
        result.setdefault(m["role"], []).append({
            "id": mid,
            "name": m["name"],
            "skill_level": m["skill_level"],
            "available": m["available"],
        })
    return result



def crew_menu():
    while True:
        print("\n── CREW MANAGEMENT ───────────────────")
        print("  1. Assign/change role")
        print("  2. Update skill level")
        print("  3. Set availability")
        print("  4. List crew by role")
        print("  5. Show available drivers")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            mid = input("  Member ID: ").strip()
            print(f"  Roles: {', '.join(sorted(VALID_ROLES))}")
            role = input("  New role: ").strip()
            ok, msg = assign_role(mid, role)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            mid = input("  Member ID: ").strip()
            try:
                skill = int(input("  Skill level (1-10): ").strip())
            except ValueError:
                print("  ERR: Please enter a number.")
                continue
            ok, msg = update_skill(mid, skill)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "3":
            mid = input("  Member ID: ").strip()
            avail_input = input("  Available? (yes/no): ").strip().lower()
            avail = avail_input in ("yes", "y", "1", "true")
            ok, msg = set_availability(mid, avail)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "4":
            grouped = list_crew_by_role()
            if not grouped:
                print("  No crew members registered.")
            else:
                for role, members in sorted(grouped.items()):
                    print(f"\n  [{role.upper()}]")
                    for m in members:
                        avail = "Avail" if m["available"] else "Busy"
                        print(f"    {m['id']} | {m['name']:<20} | Skill {m['skill_level']:>2} | {avail}")

        elif choice == "5":
            drivers = get_available_members_by_role("driver")
            if not drivers:
                print("  No available drivers.")
            else:
                print(f"\n  {'ID':<6} {'Name':<20} {'Skill':>5}")
                for mid, m in drivers:
                    print(f"  {mid:<6} {m['name']:<20} {m['skill_level']:>5}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
