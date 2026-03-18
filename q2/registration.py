"""
registration.py - Registration Module
Registers new crew members, storing name and role.
"""
from __future__ import annotations

import data_store

VALID_ROLES = {"driver", "mechanic", "strategist", "scout", "navigator"}


def register_member(name: str, role: str) -> tuple[bool, str]:
    """Register a new crew member with a name and role.

    Returns (success, message).
    """
    name = name.strip()
    role = role.strip().lower()

    if not name:
        return False, "Name cannot be empty."
    if role not in VALID_ROLES:
        return False, f"Invalid role '{role}'. Valid roles: {', '.join(sorted(VALID_ROLES))}."

    # Check for duplicate names
    for member in data_store.crew_members.values():
        if member["name"].lower() == name.lower():
            return False, f"A crew member named '{name}' is already registered."

    member_id = data_store.next_member_id()
    data_store.crew_members[member_id] = {
        "name": name,
        "role": role,
        "skill_level": 1,
        "available": True,
    }
    return True, f"Crew member '{name}' registered as {role} with ID {member_id}."


def get_member(member_id: str) -> dict | None:
    """Return a crew member dict, or None if not found."""
    return data_store.crew_members.get(member_id)


def is_registered(member_id: str) -> bool:
    """Check whether a member ID exists in the system."""
    return member_id in data_store.crew_members


def list_members() -> list[tuple[str, dict]]:
    """Return a list of (member_id, member_dict) tuples."""
    return list(data_store.crew_members.items())


def find_member_by_name(name: str) -> tuple[str, dict] | None:
    """Return (member_id, member_dict) matching name, or None."""
    for mid, m in data_store.crew_members.items():
        if m["name"].lower() == name.lower():
            return mid, m
    return None


def deregister_member(member_id: str) -> tuple[bool, str]:
    """Remove a crew member from the system."""
    if not is_registered(member_id):
        return False, f"No member with ID '{member_id}' found."
    name = data_store.crew_members[member_id]["name"]
    del data_store.crew_members[member_id]
    return True, f"Crew member '{name}' ({member_id}) removed from the system."


def registration_menu():
    while True:
        print("\n── REGISTRATION ──────────────────────")
        print("  1. Register crew member")
        print("  2. List all members")
        print("  3. Deregister member")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            name = input("  Name: ").strip()
            print(f"  Roles: {', '.join(sorted(VALID_ROLES))}")
            role = input("  Role: ").strip()
            ok, msg = register_member(name, role)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            members = list_members()
            if not members:
                print("  No members registered.")
            else:
                print(f"\n  {'ID':<6} {'Name':<20} {'Role':<12} {'Skill':>5} {'Avail':>5}")
                print("  " + "-" * 52)
                for mid, m in members:
                    avail = "Yes" if m["available"] else "No"
                    print(f"  {mid:<6} {m['name']:<20} {m['role']:<12} {m['skill_level']:>5} {avail:>5}")

        elif choice == "3":
            mid = input("  Member ID: ").strip()
            ok, msg = deregister_member(mid)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
