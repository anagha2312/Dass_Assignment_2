"""
inventory.py - Inventory Module
Tracks cars, spare parts, tools, and the cash balance.
"""
from __future__ import annotations

import data_store

VEHICLE_CONDITIONS = {"good", "damaged", "under_repair", "totalled"}


def add_vehicle(name: str, model: str, speed_rating: int) -> tuple[bool, str]:
    """Add a new vehicle to the inventory."""
    name = name.strip()
    model = model.strip()
    if not name or not model:
        return False, "Vehicle name and model cannot be empty."
    if not (1 <= speed_rating <= 10):
        return False, "Speed rating must be between 1 and 10."
    vid = data_store.next_vehicle_id()
    data_store.vehicles[vid] = {
        "name": name,
        "model": model,
        "speed_rating": speed_rating,
        "condition": "good",
        "assigned_driver": None,
    }
    return True, f"Vehicle '{name}' ({model}) added with ID {vid}."


def get_vehicle(vehicle_id: str) -> dict | None:
    """Return a vehicle dict or None."""
    return data_store.vehicles.get(vehicle_id)


def vehicle_exists(vehicle_id: str) -> bool:
    return vehicle_id in data_store.vehicles


def list_vehicles() -> list[tuple[str, dict]]:
    return list(data_store.vehicles.items())


def get_available_vehicles() -> list[tuple[str, dict]]:
    """Return vehicles in good condition with no assigned driver."""
    return [
        (vid, v)
        for vid, v in data_store.vehicles.items()
        if v["condition"] == "good" and v["assigned_driver"] is None
    ]


def update_vehicle_condition(vehicle_id: str, condition: str) -> tuple[bool, str]:
    """Update the condition of a vehicle."""
    if not vehicle_exists(vehicle_id):
        return False, f"Vehicle '{vehicle_id}' not found."
    condition = condition.lower()
    if condition not in VEHICLE_CONDITIONS:
        return False, f"Invalid condition. Valid: {', '.join(sorted(VEHICLE_CONDITIONS))}."
    data_store.vehicles[vehicle_id]["condition"] = condition
    name = data_store.vehicles[vehicle_id]["name"]
    return True, f"Vehicle '{name}' condition updated to '{condition}'."


def assign_driver_to_vehicle(vehicle_id: str, driver_id: str | None) -> tuple[bool, str]:
    """Assign or unassign a driver from a vehicle."""
    if not vehicle_exists(vehicle_id):
        return False, f"Vehicle '{vehicle_id}' not found."
    data_store.vehicles[vehicle_id]["assigned_driver"] = driver_id
    name = data_store.vehicles[vehicle_id]["name"]
    if driver_id:
        return True, f"Driver {driver_id} assigned to vehicle '{name}'."
    return True, f"Driver unassigned from vehicle '{name}'."



def add_spare_parts(part_name: str, quantity: int) -> tuple[bool, str]:
    """Add spare parts or tools to inventory."""
    part_name = part_name.strip()
    if not part_name:
        return False, "Part name cannot be empty."
    if quantity <= 0:
        return False, "Quantity must be positive."
    current = data_store.spare_parts.get(part_name, 0)
    data_store.spare_parts[part_name] = current + quantity
    return True, f"Added {quantity}x '{part_name}'. Total: {data_store.spare_parts[part_name]}."


def use_spare_part(part_name: str, quantity: int = 1) -> tuple[bool, str]:
    """Consume spare parts from inventory."""
    current = data_store.spare_parts.get(part_name, 0)
    if current < quantity:
        return False, f"Not enough '{part_name}'. Have {current}, need {quantity}."
    data_store.spare_parts[part_name] = current - quantity
    return True, f"Used {quantity}x '{part_name}'. Remaining: {data_store.spare_parts[part_name]}."


def list_spare_parts() -> dict:
    return dict(data_store.spare_parts)



def add_cash(amount: float) -> tuple[bool, str]:
    """Add money to the cash balance."""
    if amount <= 0:
        return False, "Amount must be positive."
    data_store.cash_balance += amount
    return True, f"Added ${amount:,.2f}. New balance: ${data_store.cash_balance:,.2f}."


def deduct_cash(amount: float) -> tuple[bool, str]:
    """Deduct money from the cash balance."""
    if amount <= 0:
        return False, "Amount must be positive."
    if data_store.cash_balance < amount:
        return False, f"Insufficient funds. Balance: ${data_store.cash_balance:,.2f}, need ${amount:,.2f}."
    data_store.cash_balance -= amount
    return True, f"Deducted ${amount:,.2f}. New balance: ${data_store.cash_balance:,.2f}."


def get_cash_balance() -> float:
    return data_store.cash_balance



def inventory_menu():
    while True:
        print("\n── INVENTORY ─────────────────────────")
        print("  1. Add vehicle")
        print("  2. List vehicles")
        print("  3. Update vehicle condition")
        print("  4. Add spare parts / tools")
        print("  5. List spare parts")
        print("  6. Add cash")
        print("  7. Deduct cash")
        print("  8. Show cash balance")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            name = input("  Vehicle name: ").strip()
            model = input("  Model: ").strip()
            try:
                speed = int(input("  Speed rating (1-10): ").strip())
            except ValueError:
                print("  ERR: Enter a number.")
                continue
            ok, msg = add_vehicle(name, model, speed)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            vehicles = list_vehicles()
            if not vehicles:
                print("  No vehicles in inventory.")
            else:
                print(f"\n  {'ID':<6} {'Name':<18} {'Model':<18} {'Speed':>5} {'Cond':<12} {'Driver'}")
                print("  " + "-" * 68)
                for vid, v in vehicles:
                    driver = v["assigned_driver"] or "-"
                    print(f"  {vid:<6} {v['name']:<18} {v['model']:<18} {v['speed_rating']:>5} {v['condition']:<12} {driver}")

        elif choice == "3":
            vid = input("  Vehicle ID: ").strip()
            print(f"  Conditions: {', '.join(sorted(VEHICLE_CONDITIONS))}")
            cond = input("  New condition: ").strip()
            ok, msg = update_vehicle_condition(vid, cond)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "4":
            part = input("  Part/tool name: ").strip()
            try:
                qty = int(input("  Quantity: ").strip())
            except ValueError:
                print("  ERR: Enter a number.")
                continue
            ok, msg = add_spare_parts(part, qty)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "5":
            parts = list_spare_parts()
            if not parts:
                print("  No spare parts in inventory.")
            else:
                for part, qty in parts.items():
                    print(f"  {part}: {qty}")

        elif choice == "6":
            try:
                amt = float(input("  Amount: $").strip())
            except ValueError:
                print("  ERR: Enter a number.")
                continue
            ok, msg = add_cash(amt)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "7":
            try:
                amt = float(input("  Amount: $").strip())
            except ValueError:
                print("  ERR: Enter a number.")
                continue
            ok, msg = deduct_cash(amt)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "8":
            print(f"  Current balance: ${get_cash_balance():,.2f}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
