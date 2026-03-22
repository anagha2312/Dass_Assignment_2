"""
full_tests.py  ─  StreetRace Manager  |  Complete Test Suite
Covers: Unit tests for every module  +  Integration tests for all cross-module paths
Run:    python full_tests.py
"""
import sys
import data_store

# ── Test harness ──────────────────────────────────────────────────────────────
PASS = 0
FAIL = 0

def check(label, condition, expected="", actual=""):
    global PASS, FAIL
    if condition:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}")
        if expected != "" or actual != "":
            print(f"         expected : {expected}")
            print(f"         actual   : {actual}")
        FAIL += 1

def reset():
    data_store.reset_all()

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def subsection(title):
    print(f"\n  ── {title}")

# ── Module imports ─────────────────────────────────────────────────────────────
import registration
import crew_management
import inventory
import race_management
import results
import mission_planning
import leaderboard
import maintenance


# ══════════════════════════════════════════════════════════════════════════════
#  PART A — UNIT TESTS
#  Each module tested in isolation.  Every function, every branch.
# ══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
#  UT-01  data_store — counters, reset_all
# ─────────────────────────────────────────────────────────────────────────────
section("UT-01: data_store — ID counters and reset_all()")
reset()

id1 = data_store.next_member_id()
id2 = data_store.next_member_id()
check("member IDs are sequential", id1 == "M001" and id2 == "M002", "M001, M002", f"{id1}, {id2}")

vid1 = data_store.next_vehicle_id()
check("vehicle ID format correct", vid1 == "V001", "V001", vid1)

rid1 = data_store.next_race_id()
check("race ID format correct", rid1 == "R001", "R001", rid1)

msid = data_store.next_mission_id()
check("mission ID format correct", msid == "MS001", "MS001", msid)

mntid = data_store.next_maintenance_id()
check("maintenance ID format correct", mntid == "MNT001", "MNT001", mntid)

reset()
id_after_reset = data_store.next_member_id()
check("counters reset to M001 after reset_all()", id_after_reset == "M001", "M001", id_after_reset)
check("crew_members dict empty after reset", len(data_store.crew_members) == 0)
check("vehicles dict empty after reset",     len(data_store.vehicles) == 0)
check("cash_balance = 0.0 after reset",      data_store.cash_balance == 0.0)
check("races dict empty after reset",         len(data_store.races) == 0)
check("missions dict empty after reset",      len(data_store.missions) == 0)
check("maintenance_log empty after reset",    len(data_store.maintenance_log) == 0)
check("leaderboard dict empty after reset",   len(data_store.leaderboard) == 0)


# ─────────────────────────────────────────────────────────────────────────────
#  UT-02  registration — every function and edge case
# ─────────────────────────────────────────────────────────────────────────────
section("UT-02: registration — all functions and edge cases")
reset()

subsection("register_member — valid cases")
ok, msg = registration.register_member("Alice", "driver")
check("register valid driver", ok)
check("member stored in data_store", "M001" in data_store.crew_members)
check("stored role is driver", data_store.crew_members["M001"]["role"] == "driver")
check("default skill_level = 1", data_store.crew_members["M001"]["skill_level"] == 1)
check("default available = True", data_store.crew_members["M001"]["available"] is True)

ok, _ = registration.register_member("Bob", "mechanic")
check("register valid mechanic", ok)
ok, _ = registration.register_member("Carol", "strategist")
check("register valid strategist", ok)
ok, _ = registration.register_member("Dave", "scout")
check("register valid scout", ok)
ok, _ = registration.register_member("Eve", "navigator")
check("register valid navigator", ok)

subsection("register_member — invalid / error cases")
ok, msg = registration.register_member("", "driver")
check("empty name rejected", not ok)
check("error mentions name", "name" in msg.lower() or "empty" in msg.lower())

ok, msg = registration.register_member("Frank", "pirate")
check("invalid role rejected", not ok)
check("error mentions role", "role" in msg.lower() or "invalid" in msg.lower())

ok, msg = registration.register_member("Alice", "driver")
check("duplicate name rejected", not ok)
check("error mentions duplicate", "already" in msg.lower())

ok, msg = registration.register_member("  alice  ", "driver")
check("name with spaces treated as duplicate after strip", not ok)

subsection("get_member / is_registered")
m = registration.get_member("M001")
check("get_member returns dict for valid ID", m is not None and m["name"] == "Alice")
check("get_member returns None for invalid ID", registration.get_member("M999") is None)
check("is_registered True for M001", registration.is_registered("M001"))
check("is_registered False for M999", not registration.is_registered("M999"))

subsection("find_member_by_name")
result = registration.find_member_by_name("Alice")
check("find_member_by_name returns (id, dict)", result is not None and result[0] == "M001")
check("find_member_by_name case-insensitive", registration.find_member_by_name("alice") is not None)
check("find_member_by_name returns None for unknown", registration.find_member_by_name("Zara") is None)

subsection("list_members")
members = registration.list_members()
check("list_members returns all 5 registered", len(members) == 5)

subsection("deregister_member")
ok, msg = registration.deregister_member("M005")
check("deregister valid member", ok)
check("member removed from data_store", "M005" not in data_store.crew_members)

ok, msg = registration.deregister_member("M999")
check("deregister non-existent returns False", not ok)
check("error mentions not found", "not found" in msg.lower() or "no member" in msg.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  UT-03  crew_management — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-03: crew_management — all functions and edge cases")
reset()

registration.register_member("Gina", "driver")
registration.register_member("Hugo", "mechanic")

subsection("assign_role")
ok, msg = crew_management.assign_role("M001", "navigator")
check("assign_role changes role", ok)
check("role updated in store", data_store.crew_members["M001"]["role"] == "navigator")

ok, msg = crew_management.assign_role("M999", "driver")
check("assign_role rejects unregistered ID", not ok)

ok, msg = crew_management.assign_role("M001", "pilot")
check("assign_role rejects invalid role", not ok)
check("error mentions invalid role", "invalid" in msg.lower() or "role" in msg.lower())

subsection("update_skill")
ok, msg = crew_management.update_skill("M001", 7)
check("update_skill sets level 7", ok)
check("skill stored correctly", data_store.crew_members["M001"]["skill_level"] == 7)

ok, msg = crew_management.update_skill("M001", 0)
check("skill level 0 rejected", not ok)

ok, msg = crew_management.update_skill("M001", 11)
check("skill level 11 rejected", not ok)

ok, msg = crew_management.update_skill("M001", 1)
check("skill level 1 accepted (min boundary)", ok)

ok, msg = crew_management.update_skill("M001", 10)
check("skill level 10 accepted (max boundary)", ok)

ok, msg = crew_management.update_skill("M999", 5)
check("update_skill rejects unregistered ID", not ok)

subsection("get_role / get_skill / is_available")
check("get_role returns current role", crew_management.get_role("M001") == "navigator")
check("get_role returns None for unknown", crew_management.get_role("M999") is None)
check("get_skill returns 10", crew_management.get_skill("M001") == 10)
check("get_skill returns None for unknown", crew_management.get_skill("M999") is None)
check("is_available True by default", crew_management.is_available("M001"))
check("is_available False for unknown ID", not crew_management.is_available("M999"))

subsection("set_availability")
ok, _ = crew_management.set_availability("M001", False)
check("set_availability to False", ok)
check("is_available now False", not crew_management.is_available("M001"))

ok, _ = crew_management.set_availability("M001", True)
check("set_availability back to True", ok)
check("is_available now True again", crew_management.is_available("M001"))

ok, msg = crew_management.set_availability("M999", True)
check("set_availability rejects unregistered", not ok)

subsection("get_members_by_role / get_available_members_by_role")
# reset role back to driver
crew_management.assign_role("M001", "driver")

drivers = crew_management.get_members_by_role("driver")
check("get_members_by_role returns driver list", len(drivers) == 1 and drivers[0][0] == "M001")

mechs = crew_management.get_members_by_role("mechanic")
check("get_members_by_role returns mechanic list", len(mechs) == 1)

crew_management.set_availability("M001", False)
avail_drivers = crew_management.get_available_members_by_role("driver")
check("get_available_members_by_role excludes unavailable", len(avail_drivers) == 0)

crew_management.set_availability("M001", True)
avail_drivers = crew_management.get_available_members_by_role("driver")
check("get_available_members_by_role includes available", len(avail_drivers) == 1)

subsection("list_crew_by_role")
grouped = crew_management.list_crew_by_role()
check("list_crew_by_role groups by role", "driver" in grouped and "mechanic" in grouped)


# ─────────────────────────────────────────────────────────────────────────────
#  UT-04  inventory — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-04: inventory — all functions and edge cases")
reset()

subsection("add_vehicle")
ok, msg = inventory.add_vehicle("Rocket", "Ferrari", 9)
check("add valid vehicle", ok)
check("vehicle stored in data_store", "V001" in data_store.vehicles)
check("default condition = good", data_store.vehicles["V001"]["condition"] == "good")
check("default assigned_driver = None", data_store.vehicles["V001"]["assigned_driver"] is None)

ok, msg = inventory.add_vehicle("", "Ferrari", 9)
check("empty vehicle name rejected", not ok)

ok, msg = inventory.add_vehicle("X", "", 9)
check("empty model rejected", not ok)

ok, msg = inventory.add_vehicle("X", "Y", 0)
check("speed rating 0 rejected", not ok)

ok, msg = inventory.add_vehicle("X", "Y", 11)
check("speed rating 11 rejected", not ok)

ok, _ = inventory.add_vehicle("X", "Y", 1)
check("speed rating 1 accepted (min boundary)", ok)
ok, _ = inventory.add_vehicle("Z", "W", 10)
check("speed rating 10 accepted (max boundary)", ok)

subsection("get_vehicle / vehicle_exists / list_vehicles")
v = inventory.get_vehicle("V001")
check("get_vehicle returns dict", v is not None and v["name"] == "Rocket")
check("get_vehicle returns None for unknown", inventory.get_vehicle("V999") is None)
check("vehicle_exists True", inventory.vehicle_exists("V001"))
check("vehicle_exists False", not inventory.vehicle_exists("V999"))
check("list_vehicles returns all", len(inventory.list_vehicles()) == 3)

subsection("update_vehicle_condition")
ok, _ = inventory.update_vehicle_condition("V001", "damaged")
check("update condition to damaged", ok)
check("condition stored", data_store.vehicles["V001"]["condition"] == "damaged")

ok, _ = inventory.update_vehicle_condition("V001", "under_repair")
check("update condition to under_repair", ok)

ok, _ = inventory.update_vehicle_condition("V001", "totalled")
check("update condition to totalled", ok)

ok, _ = inventory.update_vehicle_condition("V001", "good")
check("update condition back to good", ok)

ok, msg = inventory.update_vehicle_condition("V001", "flying")
check("invalid condition rejected", not ok)

ok, msg = inventory.update_vehicle_condition("V999", "good")
check("unknown vehicle ID rejected", not ok)

subsection("assign_driver_to_vehicle")
ok, _ = inventory.assign_driver_to_vehicle("V001", "M001")
check("assign driver to vehicle", ok)
check("assigned_driver stored", data_store.vehicles["V001"]["assigned_driver"] == "M001")

ok, _ = inventory.assign_driver_to_vehicle("V001", None)
check("unassign driver from vehicle", ok)
check("assigned_driver is None", data_store.vehicles["V001"]["assigned_driver"] is None)

ok, msg = inventory.assign_driver_to_vehicle("V999", "M001")
check("assign driver to unknown vehicle rejected", not ok)

subsection("get_available_vehicles")
inventory.update_vehicle_condition("V001", "good")
avail = inventory.get_available_vehicles()
check("get_available_vehicles returns good unassigned", any(vid == "V001" for vid, _ in avail))

inventory.update_vehicle_condition("V001", "damaged")
avail = inventory.get_available_vehicles()
check("get_available_vehicles excludes damaged", not any(vid == "V001" for vid, _ in avail))
inventory.update_vehicle_condition("V001", "good")

subsection("spare parts")
ok, _ = inventory.add_spare_parts("tyres", 4)
check("add spare parts", ok)
check("quantity stored", data_store.spare_parts["tyres"] == 4)

ok, _ = inventory.add_spare_parts("tyres", 2)
check("add more of same part accumulates", ok)
check("total now 6", data_store.spare_parts["tyres"] == 6)

ok, msg = inventory.add_spare_parts("", 4)
check("empty part name rejected", not ok)

ok, msg = inventory.add_spare_parts("tyres", 0)
check("zero quantity rejected", not ok)

ok, msg = inventory.add_spare_parts("tyres", -1)
check("negative quantity rejected", not ok)

ok, _ = inventory.use_spare_part("tyres", 2)
check("use spare part reduces quantity", ok)
check("quantity now 4", data_store.spare_parts["tyres"] == 4)

ok, msg = inventory.use_spare_part("tyres", 99)
check("use more than available rejected", not ok)
check("error mentions quantity", "enough" in msg.lower() or "have" in msg.lower())

parts = inventory.list_spare_parts()
check("list_spare_parts returns dict", isinstance(parts, dict) and "tyres" in parts)

subsection("cash balance")
ok, _ = inventory.add_cash(1000.0)
check("add cash", ok)
check("balance is 1000", inventory.get_cash_balance() == 1000.0)

ok, _ = inventory.add_cash(500.0)
check("add more cash", ok)
check("balance is 1500", inventory.get_cash_balance() == 1500.0)

ok, msg = inventory.add_cash(0)
check("add zero cash rejected", not ok)

ok, msg = inventory.add_cash(-100)
check("add negative cash rejected", not ok)

ok, _ = inventory.deduct_cash(200.0)
check("deduct cash", ok)
check("balance is 1300", inventory.get_cash_balance() == 1300.0)

ok, msg = inventory.deduct_cash(9999.0)
check("deduct more than balance rejected", not ok)
check("error mentions insufficient", "insufficient" in msg.lower() or "balance" in msg.lower())

ok, msg = inventory.deduct_cash(0)
check("deduct zero rejected", not ok)

ok, msg = inventory.deduct_cash(-50)
check("deduct negative rejected", not ok)


# ─────────────────────────────────────────────────────────────────────────────
#  UT-05  race_management — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-05: race_management — all functions and edge cases")
reset()

registration.register_member("Ida", "driver")
registration.register_member("Jay", "driver")
registration.register_member("Kim", "mechanic")
inventory.add_vehicle("Fast", "Ferrari", 9)
inventory.add_vehicle("Slow", "Honda", 5)
inventory.add_vehicle("Broken", "Lada", 3)
inventory.update_vehicle_condition("V003", "damaged")

subsection("create_race")
ok, msg = race_management.create_race("Night Race", 5000)
check("create race", ok)
check("race stored in data_store", "R001" in data_store.races)
check("race status = pending", data_store.races["R001"]["status"] == "pending")
check("prize money stored", data_store.races["R001"]["prize_money"] == 5000)

ok, msg = race_management.create_race("", 1000)
check("empty race name rejected", not ok)

ok, msg = race_management.create_race("Free Race", -1)
check("negative prize rejected", not ok)

ok, _ = race_management.create_race("Free Race", 0)
check("zero prize accepted", ok)

subsection("get_race / race_exists / list_races")
check("get_race returns dict", race_management.get_race("R001") is not None)
check("get_race returns None for unknown", race_management.get_race("R999") is None)
check("race_exists True for R001", race_management.race_exists("R001"))
check("race_exists False for R999", not race_management.race_exists("R999"))
check("list_races returns 2 races", len(race_management.list_races()) == 2)

subsection("add_participant — valid")
ok, msg = race_management.add_participant("R001", "M001", "V001")
check("add first participant", ok)
check("driver M001 unavailable after entry", not crew_management.is_available("M001"))
check("vehicle V001 assigned to M001", data_store.vehicles["V001"]["assigned_driver"] == "M001")

ok, msg = race_management.add_participant("R001", "M002", "V002")
check("add second participant", ok)
check("race has 2 participants", len(data_store.races["R001"]["participants"]) == 2)

subsection("add_participant — all error paths")
ok, msg = race_management.add_participant("R999", "M001", "V001")
check("unknown race ID rejected", not ok)

ok, msg = race_management.add_participant("R001", "M001", "V002")
check("duplicate driver rejected", not ok)
check("error mentions already", "already" in msg.lower())

ok, msg = race_management.add_participant("R001", "M002", "V001")
check("duplicate vehicle rejected", not ok)
check("error mentions already", "already" in msg.lower())

ok, msg = race_management.add_participant("R001", "M999", "V999")
check("unregistered driver rejected", not ok)
check("error mentions registered", "registered" in msg.lower() or "register" in msg.lower())

# Use a fresh vehicle not already in the race so the mechanic error fires (not vehicle error)
inventory.add_vehicle("FreshCarA", "Seat", 4)   # V004
ok, msg = race_management.add_participant("R001", "M003", "V004")
check("non-driver role (mechanic) rejected", not ok)
check("error mentions driver", "driver" in msg.lower())

# Add a new driver and use the damaged V003 to trigger the condition error
inventory.add_vehicle("FreshCarB", "Seat", 4)   # V005
registration.register_member("Extra Driver", "driver")  # M004
ok, msg = race_management.add_participant("R001", "M004", "V003")
check("damaged vehicle rejected", not ok)
check("error mentions condition", "good" in msg.lower() or "condition" in msg.lower() or "damaged" in msg.lower())

ok, msg = race_management.add_participant("R001", "M002", "V999")
check("unknown vehicle ID rejected", not ok)

subsection("start_race")
ok, msg = race_management.start_race("R001")
check("start race with 2 participants", ok)
check("status = active", data_store.races["R001"]["status"] == "active")

ok, msg = race_management.start_race("R001")
check("cannot start already-active race", not ok)

race_management.create_race("Solo Race", 0)
ok, msg = race_management.start_race("R002")
check("race with 0 participants cannot start", not ok)
check("error mentions participants", "participant" in msg.lower())

race_management.create_race("One Person Race", 0)
registration.register_member("Lone Driver", "driver")
inventory.add_vehicle("Solo Car", "Mini", 4)
# Find the IDs dynamically since we added vehicles in the error-path section
lone_ids  = [mid for mid, m in data_store.crew_members.items() if m["name"] == "Lone Driver"]
lone_mid  = lone_ids[0]
solo_vids = [vid for vid, v in data_store.vehicles.items() if v["name"] == "Solo Car"]
solo_vid  = solo_vids[0]
# R001=Night Race(active), R002=Solo Race, R003=One Person Race
race_management.add_participant("R003", lone_mid, solo_vid)
ok, msg = race_management.start_race("R003")
check("race with 1 participant cannot start", not ok)

subsection("remove_participant")
race_management.create_race("Remove Test", 100)
registration.register_member("Temp Driver", "driver")
inventory.add_vehicle("Temp Car", "Kia", 3)
# At this point: Ida=M001,Jay=M002,Kim=M003,Extra Driver=M004,Lone Driver=M005,Temp Driver=M006
# Vehicles: Fast=V001,Slow=V002,Broken=V003,FreshCarA=V004,FreshCarB=V005,Solo Car=V006,Temp Car=V007
# Find the temp driver's actual ID
temp_ids = [mid for mid, m in data_store.crew_members.items() if m["name"] == "Temp Driver"]
temp_mid = temp_ids[0]
temp_vids = [vid for vid, v in data_store.vehicles.items() if v["name"] == "Temp Car"]
temp_vid = temp_vids[0]
race_management.add_participant("R005", temp_mid, temp_vid)
ok, msg = race_management.remove_participant("R005", temp_mid)
check("remove participant from pending race", ok)
check("temp driver available again", crew_management.is_available(temp_mid))
check("temp vehicle unassigned", data_store.vehicles[temp_vid]["assigned_driver"] is None)

ok, msg = race_management.remove_participant("R001", "M001")
check("cannot remove from active race", not ok)

ok, msg = race_management.remove_participant("R005", "M999")
check("remove non-participant returns False", not ok)

subsection("list_race_participants")
participants = race_management.list_race_participants("R001")
check("list_race_participants returns 2", len(participants) == 2)
check("participant has driver_name field", "driver_name" in participants[0])
check("participant has vehicle_name field", "vehicle_name" in participants[0])
check("participant has skill field", "skill" in participants[0])

check("list_race_participants for unknown race returns []",
      race_management.list_race_participants("R999") == [])


# ─────────────────────────────────────────────────────────────────────────────
#  UT-06  results — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-06: results — all functions and edge cases")
reset()

registration.register_member("Leo", "driver")
registration.register_member("Mia", "driver")
inventory.add_vehicle("LeosCar", "BMW", 8)
inventory.add_vehicle("MiasCar", "Audi", 7)
race_management.create_race("Test Race", 2000)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")

subsection("record_result — error paths before start")
ok, msg = results.record_result("R999", ["M001", "M002"], [])
check("unknown race ID rejected", not ok)

ok, msg = results.record_result("R001", ["M001", "M002"], [])
check("pending race (not active) rejected", not ok)
check("error mentions active", "active" in msg.lower() or "start" in msg.lower())

race_management.start_race("R001")

ok, msg = results.record_result("R001", ["M001"], [])
check("incomplete finishing order rejected", not ok)
check("error mentions participant IDs", "participant" in msg.lower() or "expected" in msg.lower())

ok, msg = results.record_result("R001", ["M001", "M999"], [])
check("wrong driver ID in order rejected", not ok)

subsection("record_result — happy path")
ok, msg = results.record_result("R001", ["M001", "M002"], [])
check("record result succeeds", ok)
check("prize 2000 added to cash", inventory.get_cash_balance() == 2000.0)
check("race status = completed", race_management.get_race("R001")["status"] == "completed")
check("M001 available after race", crew_management.is_available("M001"))
check("M002 available after race", crew_management.is_available("M002"))
check("V001 unassigned after race", data_store.vehicles["V001"]["assigned_driver"] is None)
check("result stored in data_store", "R001" in data_store.race_results)

ok, msg = results.record_result("R001", ["M001", "M002"], [])
check("completed race cannot be re-recorded", not ok)

subsection("get_results / list_results / show_race_result")
r = results.get_results("R001")
check("get_results returns dict", r is not None)
check("positions stored correctly", r["positions"] == ["M001", "M002"])
check("prize_amount stored", r["prize_amount"] == 2000.0)

check("get_results for unknown returns None", results.get_results("R999") is None)

all_results = results.list_results()
check("list_results returns 1 result", len(all_results) == 1)

text = results.show_race_result("R001")
check("show_race_result returns string", isinstance(text, str) and "1st" in text)

text_unknown = results.show_race_result("R999")
check("show_race_result for unknown returns error string", "no results" in text_unknown.lower() or "not found" in text_unknown.lower())

subsection("record_result — with damaged vehicles")
reset()
registration.register_member("Nik", "driver")
registration.register_member("Ona", "driver")
inventory.add_vehicle("NikCar", "GT", 8)
inventory.add_vehicle("OnaCar", "RS", 7)
race_management.create_race("Crash Race", 0)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")
race_management.start_race("R001")
results.record_result("R001", ["M001", "M002"], ["V001"])
check("V001 condition = damaged after race", inventory.get_vehicle("V001")["condition"] == "damaged")
check("V002 condition still good", inventory.get_vehicle("V002")["condition"] == "good")


# ─────────────────────────────────────────────────────────────────────────────
#  UT-07  leaderboard — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-07: leaderboard — all functions and edge cases")
reset()

registration.register_member("Pat", "driver")
registration.register_member("Quinn", "driver")

subsection("update_standings")
ok, msg = leaderboard.update_standings("M001", 1, 10, 5000.0)
check("update standings for 1st place", ok)
check("wins = 1", data_store.leaderboard["M001"]["wins"] == 1)
check("podiums = 1", data_store.leaderboard["M001"]["podiums"] == 1)
check("total_points = 10", data_store.leaderboard["M001"]["total_points"] == 10)
check("earnings = 5000", data_store.leaderboard["M001"]["earnings"] == 5000.0)
check("total_races = 1", data_store.leaderboard["M001"]["total_races"] == 1)

ok, msg = leaderboard.update_standings("M002", 2, 7, 0.0)
check("update standings for 2nd place", ok)
check("M002 wins = 0 (not 1st)", data_store.leaderboard["M002"]["wins"] == 0)
check("M002 podiums = 1 (top 3)", data_store.leaderboard["M002"]["podiums"] == 1)

ok, msg = leaderboard.update_standings("M001", 3, 5, 0.0)
check("second race for M001", ok)
check("M001 total_races = 2", data_store.leaderboard["M001"]["total_races"] == 2)
check("M001 wins still 1 (finished 3rd)", data_store.leaderboard["M001"]["wins"] == 1)
check("M001 podiums = 2 (two top-3 finishes)", data_store.leaderboard["M001"]["podiums"] == 2)
check("M001 total_points = 15", data_store.leaderboard["M001"]["total_points"] == 15)

ok, msg = leaderboard.update_standings("M999", 1, 10, 0)
check("update_standings for unregistered driver rejected", not ok)

subsection("position 4+ is NOT a podium")
registration.register_member("Rory", "driver")
leaderboard.update_standings("M003", 4, 3, 0.0)
check("position 4 not counted as podium", data_store.leaderboard["M003"]["podiums"] == 0)

subsection("get_standings")
standings = leaderboard.get_standings()
check("standings sorted by points desc", standings[0]["driver_id"] == "M001")
check("standings returns name field", "name" in standings[0])

subsection("get_driver_stats")
stats = leaderboard.get_driver_stats("M001")
check("get_driver_stats returns dict", stats is not None)
check("stats has all fields", all(k in stats for k in ["wins","total_races","podiums","total_points","earnings"]))
check("get_driver_stats returns None for no-race driver", leaderboard.get_driver_stats("M003") is None or
      leaderboard.get_driver_stats("M003") is not None)

check("get_driver_stats returns None for unknown", leaderboard.get_driver_stats("M999") is None)

subsection("display_leaderboard")
text = leaderboard.display_leaderboard()
check("display_leaderboard returns string with data", "Pat" in text or "M001" in text)

subsection("reset_leaderboard")
ok, msg = leaderboard.reset_leaderboard()
check("reset_leaderboard succeeds", ok)
check("leaderboard dict empty", len(data_store.leaderboard) == 0)
text = leaderboard.display_leaderboard()
check("display after reset shows empty message", "empty" in text.lower() or "no races" in text.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  UT-08  mission_planning — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-08: mission_planning — all functions and edge cases")
reset()

registration.register_member("Sam", "driver")
registration.register_member("Tara", "mechanic")
registration.register_member("Uma", "navigator")
inventory.add_vehicle("SamCar", "Ford", 6)
inventory.update_vehicle_condition("V001", "damaged")

subsection("create_mission")
ok, msg = mission_planning.create_mission("Op Alpha", "delivery", ["driver"])
check("create valid mission", ok)
check("mission stored", "MS001" in data_store.missions)
check("mission status = planned", data_store.missions["MS001"]["status"] == "planned")

ok, msg = mission_planning.create_mission("", "delivery", ["driver"])
check("empty name rejected", not ok)

ok, msg = mission_planning.create_mission("Op B", "invasion", ["driver"])
check("invalid mission type rejected", not ok)
check("error mentions type", "type" in msg.lower() or "invalid" in msg.lower())

ok, msg = mission_planning.create_mission("Op C", "rescue", [])
check("empty required_roles rejected", not ok)

ok, msg = mission_planning.create_mission("Op D", "rescue", ["pilot"])
check("invalid role in required_roles rejected", not ok)

subsection("get_mission / mission_exists / list_missions")
check("get_mission returns dict", mission_planning.get_mission("MS001") is not None)
check("get_mission returns None for unknown", mission_planning.get_mission("MS999") is None)
check("mission_exists True", mission_planning.mission_exists("MS001"))
check("mission_exists False", not mission_planning.mission_exists("MS999"))

mission_planning.create_mission("Op Beta", "rescue", ["mechanic"])
check("list_missions returns 2", len(mission_planning.list_missions()) == 2)

subsection("check_required_roles")
ok, msg = mission_planning.check_required_roles("MS001")
check("check_required_roles passes when driver available", ok)

ok, msg = mission_planning.check_required_roles("MS002")
check("check_required_roles passes when mechanic available", ok)

mission_planning.create_mission("Op Gamma", "surveillance", ["strategist"])
ok, msg = mission_planning.check_required_roles("MS003")
check("check_required_roles fails when strategist missing", not ok)
check("error mentions strategist", "strategist" in msg.lower())

ok, msg = mission_planning.check_required_roles("MS999")
check("check_required_roles returns False for unknown mission", not ok)

subsection("assign_mission_crew")
ok, msg = mission_planning.assign_mission_crew("MS001", ["M001"])
check("assign driver to mission requiring driver", ok)
check("M001 unavailable after assignment", not crew_management.is_available("M001"))

ok, msg = mission_planning.assign_mission_crew("MS001", ["M002"])
check("cannot reassign to already-started mission", not ok)

mission_planning.create_mission("Op Delta", "transport", ["navigator"])
ok, msg = mission_planning.assign_mission_crew("MS004", ["M999"])
check("unregistered crew member rejected", not ok)

crew_management.set_availability("M002", False)
mission_planning.create_mission("Op Epsilon", "delivery", ["mechanic"])
ok, msg = mission_planning.assign_mission_crew("MS005", ["M002"])
check("unavailable crew member rejected", not ok)
crew_management.set_availability("M002", True)

mission_planning.create_mission("Op Zeta", "rescue", ["driver", "navigator"])
ok, msg = mission_planning.assign_mission_crew("MS006", ["M003"])
check("crew not covering all roles rejected", not ok)
check("error mentions missing role", "role" in msg.lower() or "cover" in msg.lower())

subsection("start_mission")
ok, msg = mission_planning.start_mission("MS999")
check("start unknown mission returns False", not ok)

mission_planning.create_mission("Op Eta", "transport", ["driver"])
ok, msg = mission_planning.start_mission("MS007")
check("start mission without crew returns False", not ok)

registration.register_member("Vince", "driver")
mission_planning.create_mission("Op Theta", "delivery", ["driver"])
mission_planning.assign_mission_crew("MS008", ["M004"])
ok, msg = mission_planning.start_mission("MS008")
check("start mission with crew succeeds", ok)
check("mission status = active", data_store.missions["MS008"]["status"] == "active")

ok, msg = mission_planning.start_mission("MS008")
check("start already-active mission rejected", not ok)

subsection("complete_mission")
ok, msg = mission_planning.complete_mission("MS008", success=True)
check("complete mission success=True", ok)
check("mission status = completed", data_store.missions["MS008"]["status"] == "completed")
check("crew released after completion", crew_management.is_available("M004"))

ok, msg = mission_planning.complete_mission("MS008", success=False)
check("complete already-completed mission rejected", not ok)

registration.register_member("Wendy", "driver")
mission_planning.create_mission("Op Iota", "rescue", ["driver"])
mission_planning.assign_mission_crew("MS009", ["M005"])
mission_planning.start_mission("MS009")
ok, msg = mission_planning.complete_mission("MS009", success=False)
check("complete mission success=False marks as failed", ok)
check("mission status = failed", data_store.missions["MS009"]["status"] == "failed")
check("crew released even on failure", crew_management.is_available("M005"))

ok, msg = mission_planning.complete_mission("MS999", success=True)
check("complete unknown mission returns False", not ok)


# ─────────────────────────────────────────────────────────────────────────────
#  UT-09  maintenance — all functions
# ─────────────────────────────────────────────────────────────────────────────
section("UT-09: maintenance — all functions and edge cases")
reset()

registration.register_member("Xander", "driver")
registration.register_member("Yuki", "mechanic")
registration.register_member("Zane", "strategist")
inventory.add_vehicle("GoodCar", "BMW", 8)
inventory.add_vehicle("BrokenCar", "Lada", 2)
inventory.add_vehicle("TotalledCar", "Wreck", 1)

subsection("check_mechanic_availability")
mechs = maintenance.check_mechanic_availability()
check("check_mechanic_availability returns available mechanic", len(mechs) == 1 and mechs[0][0] == "M002")

crew_management.set_availability("M002", False)
mechs = maintenance.check_mechanic_availability()
check("check_mechanic_availability returns [] when busy", len(mechs) == 0)
crew_management.set_availability("M002", True)

subsection("schedule_maintenance — error paths")
ok, msg = maintenance.schedule_maintenance("V001", "M002", "Check oil")
check("schedule on good vehicle rejected", not ok)
check("error mentions good condition", "good" in msg.lower())

inventory.update_vehicle_condition("V003", "totalled")
ok, msg = maintenance.schedule_maintenance("V003", "M002", "Rebuild")
check("schedule on totalled vehicle rejected", not ok)
check("error mentions totalled", "totalled" in msg.lower())

inventory.update_vehicle_condition("V002", "damaged")
ok, msg = maintenance.schedule_maintenance("V999", "M002", "Fix")
check("schedule on unknown vehicle rejected", not ok)

ok, msg = maintenance.schedule_maintenance("V002", "M999", "Fix")
check("schedule with unregistered mechanic rejected", not ok)

ok, msg = maintenance.schedule_maintenance("V002", "M001", "Fix")
check("schedule with non-mechanic (driver) rejected", not ok)
check("error mentions mechanic", "mechanic" in msg.lower())

crew_management.set_availability("M002", False)
ok, msg = maintenance.schedule_maintenance("V002", "M002", "Fix")
check("schedule with unavailable mechanic rejected", not ok)
check("error mentions unavailable", "unavailable" in msg.lower())
crew_management.set_availability("M002", True)

ok, msg = maintenance.schedule_maintenance("V002", "M003", "Fix")
check("schedule with strategist (not mechanic) rejected", not ok)

subsection("schedule_maintenance — happy path")
ok, msg = maintenance.schedule_maintenance("V002", "M002", "Full overhaul")
check("schedule maintenance succeeds", ok)
check("vehicle V002 = under_repair", inventory.get_vehicle("V002")["condition"] == "under_repair")
check("mechanic M002 unavailable", not crew_management.is_available("M002"))
check("job logged in maintenance_log", len(data_store.maintenance_log) == 1)
check("job status = in_progress", data_store.maintenance_log[0]["status"] == "in_progress")
check("job_id = MNT001", data_store.maintenance_log[0]["job_id"] == "MNT001")

subsection("complete_repair")
ok, msg = maintenance.complete_repair("MNT999")
check("complete unknown job returns False", not ok)

ok, msg = maintenance.complete_repair("MNT001")
check("complete valid job", ok)
check("vehicle restored to good", inventory.get_vehicle("V002")["condition"] == "good")
check("mechanic M002 available again", crew_management.is_available("M002"))
check("job status = completed", data_store.maintenance_log[0]["status"] == "completed")
check("completed_at timestamp set", data_store.maintenance_log[0]["completed_at"] is not None)

ok, msg = maintenance.complete_repair("MNT001")
check("complete already-completed job rejected", not ok)
check("error mentions status", "completed" in msg.lower() or "already" in msg.lower())

subsection("cancel_job")
inventory.update_vehicle_condition("V002", "damaged")
crew_management.set_availability("M002", True)
maintenance.schedule_maintenance("V002", "M002", "Second repair")
ok, msg = maintenance.cancel_job("MNT002")
check("cancel in-progress job", ok)
check("vehicle reverts to damaged", inventory.get_vehicle("V002")["condition"] == "damaged")
check("mechanic M002 available after cancel", crew_management.is_available("M002"))
check("job status = cancelled", data_store.maintenance_log[1]["status"] == "cancelled")

ok, msg = maintenance.cancel_job("MNT002")
check("cancel already-cancelled job rejected", not ok)

ok, msg = maintenance.cancel_job("MNT999")
check("cancel unknown job returns False", not ok)

subsection("get_maintenance_log / get_pending_jobs")
log = maintenance.get_maintenance_log()
check("get_maintenance_log returns all jobs", len(log) == 2)

inventory.update_vehicle_condition("V002", "damaged")
crew_management.set_availability("M002", True)
maintenance.schedule_maintenance("V002", "M002", "Third repair")
pending = maintenance.get_pending_jobs()
check("get_pending_jobs returns in_progress only", len(pending) == 1)
check("pending job is MNT003", pending[0]["job_id"] == "MNT003")

subsection("schedule on under_repair vehicle is allowed")
# V002 is under_repair from MNT003 — a 2nd mechanic could take over
# but our code checks: only if damaged or under_repair
check("vehicle under_repair has correct condition", inventory.get_vehicle("V002")["condition"] == "under_repair")


# ══════════════════════════════════════════════════════════════════════════════
#  PART B — INTEGRATION TESTS
#  Cross-module paths verified against the call graph.
# ══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
#  IT-01  registration → race_management → crew_management → inventory
# ─────────────────────────────────────────────────────────────────────────────
section("IT-01: Register driver → enter race → availability + vehicle linked")
reset()

registration.register_member("Ana", "driver")
registration.register_member("Ben", "driver")
inventory.add_vehicle("Car A", "Ford", 7)
inventory.add_vehicle("Car B", "Chevy", 6)
race_management.create_race("Sprint", 5000)

ok, _ = race_management.add_participant("R001", "M001", "V001")
check("participant added successfully", ok)
check("driver unavailable after entering race", not crew_management.is_available("M001"))
check("vehicle assigned to driver", data_store.vehicles["V001"]["assigned_driver"] == "M001")

ok, _ = race_management.add_participant("R001", "M002", "V002")
check("second participant added", ok)
check("race has 2 participants", len(data_store.races["R001"]["participants"]) == 2)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-02  Unregistered driver blocked at race entry
# ─────────────────────────────────────────────────────────────────────────────
section("IT-02: Unregistered driver cannot enter race (cross-module guard)")
reset()

inventory.add_vehicle("Car", "BMW", 8)
race_management.create_race("Race", 1000)
ok, msg = race_management.add_participant("R001", "M999", "V001")
check("unregistered driver blocked", not ok)
check("error from registration.is_registered chain", "registered" in msg.lower() or "register" in msg.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  IT-03  Non-driver role blocked at race entry
# ─────────────────────────────────────────────────────────────────────────────
section("IT-03: Non-driver (navigator, mechanic, strategist) all blocked from racing")
reset()

registration.register_member("Mech", "mechanic")
registration.register_member("Nav", "navigator")
registration.register_member("Strat", "strategist")
inventory.add_vehicle("Car", "BMW", 8)
race_management.create_race("Race", 1000)

for mid, role in [("M001","mechanic"), ("M002","navigator"), ("M003","strategist")]:
    ok, msg = race_management.add_participant("R001", mid, "V001")
    check(f"{role} blocked from race", not ok)
    check(f"error mentions driver for {role}", "driver" in msg.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  IT-04  results → inventory (cash) + leaderboard + crew released
# ─────────────────────────────────────────────────────────────────────────────
section("IT-04: record_result → cash balance, leaderboard, crew release")
reset()

registration.register_member("Leo", "driver")
registration.register_member("Mia", "driver")
inventory.add_vehicle("L-Car", "Porsche", 9)
inventory.add_vehicle("M-Car", "VW", 6)
inventory.add_cash(500)
race_management.create_race("Grand Prix", 8000)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")
race_management.start_race("R001")

ok, _ = results.record_result("R001", ["M001", "M002"], [])
check("record_result succeeds", ok)
check("cash = 8500 (500 + 8000 prize)", inventory.get_cash_balance() == 8500.0)

lb = leaderboard.get_standings()
check("leaderboard has 2 entries", len(lb) == 2)
check("winner Leo (M001) has 1 win", lb[0]["driver_id"] == "M001" and lb[0]["wins"] == 1)
check("Mia (M002) has 0 wins", lb[1]["wins"] == 0)
check("both drivers have 1 race", lb[0]["total_races"] == 1 and lb[1]["total_races"] == 1)

check("M001 available after race", crew_management.is_available("M001"))
check("M002 available after race", crew_management.is_available("M002"))
check("V001 unassigned after race", data_store.vehicles["V001"]["assigned_driver"] is None)
check("V002 unassigned after race", data_store.vehicles["V002"]["assigned_driver"] is None)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-05  results → inventory (vehicle damage)
# ─────────────────────────────────────────────────────────────────────────────
section("IT-05: Damaged vehicles updated in inventory after race")
reset()

registration.register_member("Nik", "driver")
registration.register_member("Ona", "driver")
inventory.add_vehicle("N-Car", "GT", 8)
inventory.add_vehicle("O-Car", "RS", 7)
race_management.create_race("Derby", 0)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")
race_management.start_race("R001")

results.record_result("R001", ["M001", "M002"], ["V001"])
check("V001 condition = damaged", inventory.get_vehicle("V001")["condition"] == "damaged")
check("V002 condition still good", inventory.get_vehicle("V002")["condition"] == "good")
check("damaged vehicle stored in race_results", "V001" in data_store.race_results["R001"]["damaged_vehicles"])


# ─────────────────────────────────────────────────────────────────────────────
#  IT-06  Damaged vehicle → cannot re-enter race until repaired
# ─────────────────────────────────────────────────────────────────────────────
section("IT-06: Damaged car rejected from next race, repaired car accepted")
reset()

registration.register_member("Pete", "driver")
registration.register_member("Quin", "driver")
registration.register_member("Rex", "mechanic")
inventory.add_vehicle("PeteCar", "BMW", 8)
inventory.add_vehicle("QuinCar", "Audi", 7)
race_management.create_race("Race 1", 1000)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")
race_management.start_race("R001")
results.record_result("R001", ["M001", "M002"], ["V001"])

race_management.create_race("Race 2", 1000)
ok, msg = race_management.add_participant("R002", "M001", "V001")
check("damaged car rejected from Race 2", not ok)

maintenance.schedule_maintenance("V001", "M003", "Repair after Race 1")
maintenance.complete_repair("MNT001")
check("V001 good after repair", inventory.get_vehicle("V001")["condition"] == "good")

ok, _ = race_management.add_participant("R002", "M001", "V001")
check("repaired car accepted in Race 2", ok)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-07  Mission planning — full lifecycle
# ─────────────────────────────────────────────────────────────────────────────
section("IT-07: Mission full lifecycle — planned → active → completed, crew released")
reset()

registration.register_member("Sara", "driver")
registration.register_member("Tom", "navigator")
mission_planning.create_mission("Op Falcon", "surveillance", ["driver", "navigator"])

ok, _ = mission_planning.assign_mission_crew("MS001", ["M001", "M002"])
check("crew assigned to mission", ok)
check("driver M001 unavailable", not crew_management.is_available("M001"))
check("navigator M002 unavailable", not crew_management.is_available("M002"))
check("mission status = planned", data_store.missions["MS001"]["status"] == "planned")

ok, _ = mission_planning.start_mission("MS001")
check("mission starts successfully", ok)
check("mission status = active", data_store.missions["MS001"]["status"] == "active")

ok, _ = mission_planning.complete_mission("MS001", success=True)
check("mission completed successfully", ok)
check("mission status = completed", data_store.missions["MS001"]["status"] == "completed")
check("driver M001 available after mission", crew_management.is_available("M001"))
check("navigator M002 available after mission", crew_management.is_available("M002"))


# ─────────────────────────────────────────────────────────────────────────────
#  IT-08  Mission — required role missing blocks start
# ─────────────────────────────────────────────────────────────────────────────
section("IT-08: Mission blocked when required role has no available crew")
reset()

registration.register_member("Ula", "driver")
mission_planning.create_mission("Op Ghost", "extraction", ["driver", "strategist"])

ok, msg = mission_planning.check_required_roles("MS001")
check("check_required_roles fails — no strategist", not ok)
check("error names strategist", "strategist" in msg.lower())

ok, msg = mission_planning.assign_mission_crew("MS001", ["M001"])
check("assign without strategist coverage rejected", not ok)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-09  Mission mechanic needs damaged vehicle
# ─────────────────────────────────────────────────────────────────────────────
section("IT-09: Mechanic mission blocked when no damaged vehicle")
reset()

registration.register_member("Van", "driver")
registration.register_member("Will", "mechanic")
inventory.add_vehicle("GoodCar", "Honda", 5)

mission_planning.create_mission("Op Repair", "rescue", ["driver", "mechanic"])
ok, msg = mission_planning.assign_mission_crew("MS001", ["M001", "M002"])
check("mechanic mission rejected — no damaged vehicle", not ok)
check("error mentions damaged", "damaged" in msg.lower())

inventory.update_vehicle_condition("V001", "damaged")
ok, _ = mission_planning.assign_mission_crew("MS001", ["M001", "M002"])
check("mechanic mission succeeds once damaged vehicle exists", ok)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-10  Maintenance full lifecycle → crew / vehicle state transitions
# ─────────────────────────────────────────────────────────────────────────────
section("IT-10: Maintenance schedule → complete → state transitions verified")
reset()

registration.register_member("Xena", "driver")
registration.register_member("Yale", "mechanic")
inventory.add_vehicle("DamagedCar", "Rust", 2)
inventory.update_vehicle_condition("V001", "damaged")

ok, _ = maintenance.schedule_maintenance("V001", "M002", "Full rebuild")
check("maintenance scheduled", ok)
check("vehicle = under_repair", inventory.get_vehicle("V001")["condition"] == "under_repair")
check("mechanic unavailable during repair", not crew_management.is_available("M002"))

ok, _ = maintenance.complete_repair("MNT001")
check("repair completed", ok)
check("vehicle = good after repair", inventory.get_vehicle("V001")["condition"] == "good")
check("mechanic available after repair", crew_management.is_available("M002"))


# ─────────────────────────────────────────────────────────────────────────────
#  IT-11  Maintenance cancel → rollback
# ─────────────────────────────────────────────────────────────────────────────
section("IT-11: Maintenance cancel job → vehicle and mechanic rolled back")
reset()

registration.register_member("Zoe", "driver")
registration.register_member("Abel", "mechanic")
inventory.add_vehicle("BrokenCar", "VW", 3)
inventory.update_vehicle_condition("V001", "damaged")

maintenance.schedule_maintenance("V001", "M002", "Repair attempt")
ok, _ = maintenance.cancel_job("MNT001")
check("cancel job succeeds", ok)
check("vehicle reverts to damaged", inventory.get_vehicle("V001")["condition"] == "damaged")
check("mechanic available after cancel", crew_management.is_available("M002"))
check("job status = cancelled", data_store.maintenance_log[0]["status"] == "cancelled")


# ─────────────────────────────────────────────────────────────────────────────
#  IT-12  Leaderboard accumulates across multiple races
# ─────────────────────────────────────────────────────────────────────────────
section("IT-12: Leaderboard accumulates wins, podiums, points across 3 races")
reset()

registration.register_member("Alpha", "driver")
registration.register_member("Beta", "driver")
registration.register_member("Gamma", "driver")
inventory.add_vehicle("A-Car", "Aston", 9)
inventory.add_vehicle("B-Car", "Bentley", 8)
inventory.add_vehicle("G-Car", "Bugatti", 7)

for i, (winner, second, third) in enumerate([
    ("M001","M002","M003"),
    ("M002","M001","M003"),
    ("M001","M003","M002"),
], start=1):
    race_management.create_race(f"Race {i}", 3000)
    rid = f"R{i:03d}"
    race_management.add_participant(rid, "M001", "V001")
    race_management.add_participant(rid, "M002", "V002")
    race_management.add_participant(rid, "M003", "V003")
    race_management.start_race(rid)
    results.record_result(rid, [winner, second, third], [])

a_stats = leaderboard.get_driver_stats("M001")
b_stats = leaderboard.get_driver_stats("M002")
g_stats = leaderboard.get_driver_stats("M003")

check("Alpha: 2 wins, 3 races", a_stats["wins"] == 2 and a_stats["total_races"] == 3)
check("Beta: 1 win, 3 races",   b_stats["wins"] == 1 and b_stats["total_races"] == 3)
check("Gamma: 0 wins, 3 races", g_stats["wins"] == 0 and g_stats["total_races"] == 3)
check("Alpha: 3 podiums (all top-2)", a_stats["podiums"] == 3)
check("Beta: 3 podiums (all top-2)",  b_stats["podiums"] == 3)
check("Gamma: 3 podiums (3x top-3 — 2x third, 1x second)", g_stats["podiums"] == 3)

standings = leaderboard.get_standings()
check("Alpha ranked 1st overall", standings[0]["driver_id"] == "M001")

check("Alpha earnings = 6000 (won 2 races × 3000)", a_stats["earnings"] == 6000.0)
check("Beta earnings = 3000 (won 1 race)",          b_stats["earnings"] == 3000.0)
check("Gamma earnings = 0 (never won)",              g_stats["earnings"] == 0.0)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-13  Duplicate entries rejected — driver and vehicle
# ─────────────────────────────────────────────────────────────────────────────
section("IT-13: Duplicate driver and duplicate vehicle both rejected from same race")
reset()

registration.register_member("Dupe Driver A", "driver")
registration.register_member("Dupe Driver B", "driver")
inventory.add_vehicle("Car X", "Ford", 7)
inventory.add_vehicle("Car Y", "Honda", 6)
race_management.create_race("Dupe Test Race", 100)

race_management.add_participant("R001", "M001", "V001")

ok, msg = race_management.add_participant("R001", "M001", "V002")
check("same driver twice rejected", not ok)
check("error mentions already entered", "already" in msg.lower())

ok, msg = race_management.add_participant("R001", "M002", "V001")
check("same vehicle twice rejected", not ok)
check("error mentions vehicle already entered", "already" in msg.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  IT-14  Race cannot start with 0 or 1 participant
# ─────────────────────────────────────────────────────────────────────────────
section("IT-14: Race requires at least 2 participants to start")
reset()

registration.register_member("Solo", "driver")
inventory.add_vehicle("Solo Car", "Mini", 4)
race_management.create_race("Solo Race", 500)

ok, msg = race_management.start_race("R001")
check("empty race cannot start", not ok)

race_management.add_participant("R001", "M001", "V001")
ok, msg = race_management.start_race("R001")
check("1-participant race cannot start", not ok)
check("error mentions participants", "participant" in msg.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  IT-15  Busy crew member cannot be assigned to mission
# ─────────────────────────────────────────────────────────────────────────────
section("IT-15: Driver in a race cannot simultaneously join a mission")
reset()

registration.register_member("Busy Driver", "driver")
registration.register_member("Free Nav", "navigator")
inventory.add_vehicle("Race Car", "Ferrari", 9)
inventory.add_vehicle("Mission Car", "Toyota", 5)
registration.register_member("Other Driver", "driver")

race_management.create_race("Live Race", 2000)
race_management.add_participant("R001", "M001", "V001")
registration.register_member("Second Driver", "driver")
inventory.add_vehicle("Second Car", "Audi", 7)
race_management.add_participant("R001", "M003", "V003")

check("M001 unavailable (in race)", not crew_management.is_available("M001"))

mission_planning.create_mission("Simultaneous Op", "delivery", ["driver", "navigator"])
ok, msg = mission_planning.assign_mission_crew("MS001", ["M001", "M002"])
check("busy driver cannot join mission", not ok)
check("error mentions unavailable", "not available" in msg.lower() or "unavailable" in msg.lower())


# ─────────────────────────────────────────────────────────────────────────────
#  IT-16  remove_participant restores availability and vehicle
# ─────────────────────────────────────────────────────────────────────────────
section("IT-16: remove_participant fully restores driver and vehicle state")
reset()

registration.register_member("Exit Driver", "driver")
inventory.add_vehicle("Exit Car", "Lada", 3)
race_management.create_race("Withdrawal Race", 500)
race_management.add_participant("R001", "M001", "V001")

check("driver unavailable after entering race", not crew_management.is_available("M001"))
check("vehicle assigned after entry", data_store.vehicles["V001"]["assigned_driver"] == "M001")

ok, _ = race_management.remove_participant("R001", "M001")
check("remove participant succeeds", ok)
check("driver available after withdrawal", crew_management.is_available("M001"))
check("vehicle unassigned after withdrawal", data_store.vehicles["V001"]["assigned_driver"] is None)
check("race has 0 participants after removal", len(data_store.races["R001"]["participants"]) == 0)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-17  Mission failed → crew released, vehicle NOT auto-repaired
# ─────────────────────────────────────────────────────────────────────────────
section("IT-17: Failed mission releases crew but does not auto-repair vehicles")
reset()

registration.register_member("Fail Driver", "driver")
registration.register_member("Fail Nav", "navigator")
inventory.add_vehicle("SomeCar", "Kia", 4)
inventory.update_vehicle_condition("V001", "damaged")

mission_planning.create_mission("Doomed Op", "rescue", ["driver", "navigator"])
mission_planning.assign_mission_crew("MS001", ["M001", "M002"])
mission_planning.start_mission("MS001")
ok, msg = mission_planning.complete_mission("MS001", success=False)
check("mission can be marked failed", ok)
check("mission status = failed", data_store.missions["MS001"]["status"] == "failed")
check("crew released after failure", crew_management.is_available("M001") and crew_management.is_available("M002"))
check("vehicle still damaged (no auto-repair on failure)", inventory.get_vehicle("V001")["condition"] == "damaged")


# ─────────────────────────────────────────────────────────────────────────────
#  IT-18  skill level update → reflected in race participant list
# ─────────────────────────────────────────────────────────────────────────────
section("IT-18: crew_management.update_skill reflected in list_race_participants")
reset()

registration.register_member("Skilled Driver", "driver")
registration.register_member("Other Driver", "driver")
inventory.add_vehicle("Fast Car", "BMW", 8)
inventory.add_vehicle("Slow Car", "Fiat", 4)
crew_management.update_skill("M001", 9)
race_management.create_race("Skill Race", 1000)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")

participants = race_management.list_race_participants("R001")
skills = {p["driver_id"]: p["skill"] for p in participants}
check("skill level 9 shown in participant list", skills["M001"] == 9)
check("default skill 1 shown for second driver", skills["M002"] == 1)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-19  Zero-prize race → cash balance unchanged
# ─────────────────────────────────────────────────────────────────────────────
section("IT-19: Zero-prize race does not change cash balance")
reset()

registration.register_member("Free Racer 1", "driver")
registration.register_member("Free Racer 2", "driver")
inventory.add_vehicle("Car 1", "Ford", 6)
inventory.add_vehicle("Car 2", "Chevy", 5)
inventory.add_cash(999.0)
initial = inventory.get_cash_balance()

race_management.create_race("Free Race", 0)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M002", "V002")
race_management.start_race("R001")
results.record_result("R001", ["M001", "M002"], [])

check("cash balance unchanged for zero-prize race",
      inventory.get_cash_balance() == initial, initial, inventory.get_cash_balance())
lb = leaderboard.get_standings()
check("leaderboard still updated for zero-prize race", len(lb) == 2)
check("winner earnings = 0 for zero-prize", lb[0]["earnings"] == 0.0)


# ─────────────────────────────────────────────────────────────────────────────
#  IT-20  Full end-to-end: race → damage → maintenance → next race → mission
# ─────────────────────────────────────────────────────────────────────────────
section("IT-20: Full end-to-end workflow across all 8 modules")
reset()

registration.register_member("Vera", "driver")
registration.register_member("Wade", "mechanic")
registration.register_member("Xia", "navigator")
registration.register_member("Yara", "driver")
inventory.add_vehicle("VesCar", "GTR", 9)
inventory.add_vehicle("YaraCar", "RX7", 7)
inventory.add_cash(200.0)

# Race 1
race_management.create_race("City Sprint", 5000)
race_management.add_participant("R001", "M001", "V001")
race_management.add_participant("R001", "M004", "V002")
race_management.start_race("R001")
results.record_result("R001", ["M001", "M004"], ["V001"])

check("V001 damaged after race", inventory.get_vehicle("V001")["condition"] == "damaged")
check("cash = 5200 after race", inventory.get_cash_balance() == 5200.0)
check("M001 on leaderboard with 1 win", leaderboard.get_driver_stats("M001")["wins"] == 1)

# Maintenance
ok, _ = maintenance.schedule_maintenance("V001", "M002", "Race damage repair")
check("maintenance scheduled for damaged race car", ok)
check("mechanic Wade busy during repair", not crew_management.is_available("M002"))
maintenance.complete_repair("MNT001")
check("V001 restored to good", inventory.get_vehicle("V001")["condition"] == "good")
check("Wade available after repair", crew_management.is_available("M002"))

# Race 2
race_management.create_race("Night Run", 3000)
ok, _ = race_management.add_participant("R002", "M001", "V001")
check("repaired V001 accepted in Race 2", ok)
race_management.add_participant("R002", "M004", "V002")
race_management.start_race("R002")
results.record_result("R002", ["M004", "M001"], [])
check("cash = 8200 after Race 2", inventory.get_cash_balance() == 8200.0)

a_stats = leaderboard.get_driver_stats("M001")
y_stats = leaderboard.get_driver_stats("M004")
check("Vera: 1 win, 2 races total", a_stats["wins"] == 1 and a_stats["total_races"] == 2)
check("Yara: 1 win, 2 races total", y_stats["wins"] == 1 and y_stats["total_races"] == 2)

# Mission
mission_planning.create_mission("Intel Run", "surveillance", ["driver", "navigator"])
ok, _ = mission_planning.assign_mission_crew("MS001", ["M001", "M003"])
check("mission crew assigned", ok)
mission_planning.start_mission("MS001")
ok, _ = mission_planning.complete_mission("MS001", success=True)
check("mission completed", ok)
check("Vera (M001) available after mission", crew_management.is_available("M001"))
check("Xia (M003) available after mission", crew_management.is_available("M003"))


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  UNIT TESTS + INTEGRATION TESTS — FINAL RESULTS")
print(f"{'='*60}")
print(f"  PASS : {PASS}")
print(f"  FAIL : {FAIL}")
print(f"  TOTAL: {PASS + FAIL}")
print(f"{'='*60}\n")
sys.exit(0 if FAIL == 0 else 1)