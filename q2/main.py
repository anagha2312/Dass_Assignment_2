"""
main.py - StreetRace Manager
Entry point: displays the top-level menu and dispatches to each module's
sub-menu. All modules share state through data_store.py.

Run with:  python main.py
"""

import registration
import crew_management
import inventory
import race_management
import results
import mission_planning
import leaderboard
import maintenance


BANNER = r"""
  ╔═══════════════════════════════════════════════════════╗
  ║   ____  _                  _   ____                   ║
  ║  / ___|| |_ _ __ ___  ___ | |_|  _ \ __ _  ___ ___  ║
  ║  \___ \| __| '__/ _ \/ _ \| __| |_) / _` |/ __/ _ \ ║
  ║   ___) | |_| | |  __/  __/| |_|  _ < (_| | (_|  __/ ║
  ║  |____/ \__|_|  \___|\___| \__|_| \_\__,_|\___\___| ║
  ║                                                       ║
  ║        M a n a g e r   v 1 . 0                        ║
  ╚═══════════════════════════════════════════════════════╝
"""


def main_menu():
    print(BANNER)
    while True:
        print("\n══ MAIN MENU ══════════════════════════")
        print("  1. Registration")
        print("  2. Crew Management")
        print("  3. Inventory")
        print("  4. Race Management")
        print("  5. Results")
        print("  6. Mission Planning")
        print("  7. Leaderboard")
        print("  8. Maintenance")
        print("  0. Exit")
        print("══════════════════════════════════════")
        choice = input("Choice: ").strip()

        dispatch = {
            "1": registration.registration_menu,
            "2": crew_management.crew_menu,
            "3": inventory.inventory_menu,
            "4": race_management.race_menu,
            "5": results.results_menu,
            "6": mission_planning.mission_menu,
            "7": leaderboard.leaderboard_menu,
            "8": maintenance.maintenance_menu,
        }

        if choice == "0":
            print("\n  Goodbye. Keep racing!\n")
            break
        elif choice in dispatch:
            dispatch[choice]()
        else:
            print("  Invalid choice. Enter 0–8.")


if __name__ == "__main__":
    main_menu()
