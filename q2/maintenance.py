"""
maintenance.py - Vehicle Maintenance Module  [EXTRA MODULE 2]
Schedules and tracks vehicle repairs. Verifies mechanic availability before
scheduling work. Completing a repair restores the vehicle condition to 'good'.
Depends on: inventory, crew_management, registration.
"""
from __future__ import annotations

import datetime
import data_store
import registration
import crew_management
import inventory


def check_mechanic_availability() -> list[tuple[str, dict]]:
    """Return all available mechanics in the crew."""
    return crew_management.get_available_members_by_role("mechanic")


def schedule_maintenance(
    vehicle_id: str,
    mechanic_id: str,
    description: str,
) -> tuple[bool, str]:
    """Schedule a maintenance job for a vehicle.

    Business rules:
    - Vehicle must exist in inventory.
    - Mechanic must be registered with 'mechanic' role and be available.
    - Vehicle must be 'damaged' or 'under_repair' to need maintenance.
    """
    # Validate vehicle
    vehicle = inventory.get_vehicle(vehicle_id)
    if vehicle is None:
        return False, f"Vehicle '{vehicle_id}' not found in inventory."
    if vehicle["condition"] == "good":
        return False, f"Vehicle '{vehicle_id}' is already in good condition — no repair needed."
    if vehicle["condition"] == "totalled":
        return False, f"Vehicle '{vehicle_id}' is totalled — cannot be repaired."

    # Validate mechanic
    if not registration.is_registered(mechanic_id):
        return False, f"Mechanic '{mechanic_id}' is not registered."
    if crew_management.get_role(mechanic_id) != "mechanic":
        return False, f"Member '{mechanic_id}' is not a mechanic."
    if not crew_management.is_available(mechanic_id):
        return False, f"Mechanic '{mechanic_id}' is currently unavailable."

    # Mark vehicle as under_repair and mechanic as busy
    inventory.update_vehicle_condition(vehicle_id, "under_repair")
    crew_management.set_availability(mechanic_id, False)

    job_id = data_store.next_maintenance_id()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    data_store.maintenance_log.append({
        "job_id": job_id,
        "vehicle_id": vehicle_id,
        "mechanic_id": mechanic_id,
        "description": description.strip(),
        "status": "in_progress",
        "scheduled_at": timestamp,
        "completed_at": None,
    })

    mechanic_name = registration.get_member(mechanic_id)["name"]
    veh_name = vehicle["name"]
    return True, (
        f"Maintenance job {job_id} scheduled. "
        f"Mechanic '{mechanic_name}' repairing '{veh_name}'."
    )


def complete_repair(job_id: str) -> tuple[bool, str]:
    """Mark a maintenance job as done, restore vehicle, release mechanic."""
    job = _find_job(job_id)
    if job is None:
        return False, f"Maintenance job '{job_id}' not found."
    if job["status"] != "in_progress":
        return False, f"Job '{job_id}' is already '{job['status']}'."

    vehicle_id = job["vehicle_id"]
    mechanic_id = job["mechanic_id"]

    # Restore vehicle condition
    inventory.update_vehicle_condition(vehicle_id, "good")

    # Release mechanic
    crew_management.set_availability(mechanic_id, True)

    job["status"] = "completed"
    job["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    mechanic_name = registration.get_member(mechanic_id)["name"]
    veh_name = inventory.get_vehicle(vehicle_id)["name"]
    return True, (
        f"Job '{job_id}' completed. '{veh_name}' restored to 'good'. "
        f"Mechanic '{mechanic_name}' is now available."
    )


def cancel_job(job_id: str) -> tuple[bool, str]:
    """Cancel an in-progress maintenance job."""
    job = _find_job(job_id)
    if job is None:
        return False, f"Job '{job_id}' not found."
    if job["status"] != "in_progress":
        return False, f"Job '{job_id}' cannot be cancelled — it is '{job['status']}'."

    # Release mechanic and revert vehicle to 'damaged'
    crew_management.set_availability(job["mechanic_id"], True)
    inventory.update_vehicle_condition(job["vehicle_id"], "damaged")
    job["status"] = "cancelled"
    return True, f"Job '{job_id}' cancelled. Vehicle returned to 'damaged' status."


def get_maintenance_log() -> list[dict]:
    return list(data_store.maintenance_log)


def get_pending_jobs() -> list[dict]:
    return [j for j in data_store.maintenance_log if j["status"] == "in_progress"]


def _find_job(job_id: str) -> dict | None:
    for job in data_store.maintenance_log:
        if job["job_id"] == job_id:
            return job
    return None


# ── CLI Menu ──────────────────────────────────────────────────────────────────

def maintenance_menu():
    while True:
        print("\n── MAINTENANCE ───────────────────────")
        print("  1. Schedule repair job")
        print("  2. Complete repair job")
        print("  3. Cancel repair job")
        print("  4. View maintenance log")
        print("  5. View pending jobs")
        print("  6. Check available mechanics")
        print("  0. Back")
        choice = input("Choice: ").strip()

        if choice == "1":
            vid = input("  Vehicle ID: ").strip()
            mech_id = input("  Mechanic ID: ").strip()
            desc = input("  Description: ").strip()
            ok, msg = schedule_maintenance(vid, mech_id, desc)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "2":
            job_id = input("  Job ID: ").strip()
            ok, msg = complete_repair(job_id)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "3":
            job_id = input("  Job ID: ").strip()
            ok, msg = cancel_job(job_id)
            print(f"  {'OK' if ok else 'ERR'}: {msg}")

        elif choice == "4":
            log = get_maintenance_log()
            if not log:
                print("  No maintenance jobs logged.")
            else:
                print(f"\n  {'Job ID':<8} {'Vehicle':<8} {'Mechanic':<8} {'Status':<12} {'Scheduled':<18} {'Completed'}")
                print("  " + "-" * 72)
                for j in log:
                    completed = j["completed_at"] or "-"
                    print(f"  {j['job_id']:<8} {j['vehicle_id']:<8} {j['mechanic_id']:<8} {j['status']:<12} {j['scheduled_at']:<18} {completed}")

        elif choice == "5":
            pending = get_pending_jobs()
            if not pending:
                print("  No pending jobs.")
            else:
                for j in pending:
                    v = inventory.get_vehicle(j["vehicle_id"])
                    mech = registration.get_member(j["mechanic_id"])
                    vname = v["name"] if v else j["vehicle_id"]
                    mname = mech["name"] if mech else j["mechanic_id"]
                    print(f"  {j['job_id']}: '{vname}' — Mechanic: {mname} — \"{j['description']}\"")

        elif choice == "6":
            mechanics = check_mechanic_availability()
            if not mechanics:
                print("  No mechanics available.")
            else:
                print(f"\n  {'ID':<6} {'Name':<20} {'Skill':>5}")
                for mid, m in mechanics:
                    print(f"  {mid:<6} {m['name']:<20} {m['skill_level']:>5}")

        elif choice == "0":
            break
        else:
            print("  Invalid choice.")
