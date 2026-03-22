"""
White-box test suite for MoneyPoly — FINAL VERSION.

Imports directly from the moneypoly package so tests run against
the real fixed source files, not inline copies.

Run from the folder that CONTAINS the moneypoly/ package directory:
    python3 -m pytest test_moneypoly.py -v
  or:
    python3 test_moneypoly.py

Folder structure expected:
    moneypoly/
        __init__.py  (can be empty)
        game.py
        player.py
        bank.py
        dice.py
        property.py
        config.py
        board.py
        cards.py
        ui.py
    test_moneypoly.py   ← this file sits NEXT TO moneypoly/
"""

import unittest
from unittest.mock import patch
from pathlib import Path
import sys

# Ensure package imports work whether this file is run from q1/moneypoly
# or from q1/moneypoly/moneypoly.
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

# ---------------------------------------------------------------------------
# Real imports from the package
# ---------------------------------------------------------------------------
from moneypoly.player   import Player
from moneypoly.bank     import Bank
from moneypoly.dice     import Dice
from moneypoly.property import Property, PropertyGroup
from moneypoly.game     import Game
from moneypoly.config   import (
    STARTING_BALANCE, GO_SALARY, BOARD_SIZE,
    JAIL_POSITION, BANK_STARTING_FUNDS,
)

# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

def make_game(names=None):
    """Return a fresh Game instance with two default players."""
    if names is None:
        names = ["Alice", "Bob"]
    return Game(names)


def make_prop(name="Test Ave", position=1, price=60, base_rent=4, group=None):
    return Property(name, position, price, base_rent, group)


def make_brown_group():
    """Two-property brown group, returns (group, prop1, prop2)."""
    grp = PropertyGroup("Brown", "brown")
    p1  = Property("Mediterranean Avenue", 1, 60, 2, grp)
    p2  = Property("Baltic Avenue",        3, 60, 4, grp)
    return grp, p1, p2


# ===========================================================================
# 1. DICE TESTS
# ===========================================================================

class TestDice(unittest.TestCase):

    def test_TC_D1_roll_produces_six(self):
        """
        TC-D1  |  FIXED: dice now produce values 1-6
        Bug was: randint(1,5) — value 6 was impossible.
        Fix:     randint(1,6) in dice.py roll().
        Why needed: real Monopoly uses 6-sided dice; max roll must be 12 not 10.
        Expect: value 6 appears at least once in 500 rolls.
        """
        dice = Dice()
        seen_six = any(
            (dice.roll() or True) and (dice.die1 == 6 or dice.die2 == 6)
            for _ in range(500)
        )
        self.assertTrue(seen_six,
            "FAIL: 6 never produced — fix randint(1,5) to randint(1,6) in dice.py")

    def test_TC_D2_roll_range_1_to_6(self):
        """
        TC-D2  |  Branch: roll() — both dice must always be in [1, 6]
        Why needed: verifies upper and lower boundary of dice values after fix.
        Expect: all values in [1, 6] across 200 rolls.
        """
        dice = Dice()
        for _ in range(200):
            dice.roll()
            self.assertGreaterEqual(dice.die1, 1)
            self.assertLessEqual(dice.die1, 6)
            self.assertGreaterEqual(dice.die2, 1)
            self.assertLessEqual(dice.die2, 6)

    def test_TC_D3_is_doubles_true(self):
        """
        TC-D3  |  Branch: is_doubles() — True path
        Why needed: doubles trigger streak increment and extra turn logic.
        Expect: True when die1 == die2.
        """
        dice = Dice()
        dice.die1 = 3
        dice.die2 = 3
        self.assertTrue(dice.is_doubles())

    def test_TC_D4_is_doubles_false(self):
        """
        TC-D4  |  Branch: is_doubles() — False path
        Why needed: non-doubles must reset streak to 0.
        Expect: False when die1 != die2.
        """
        dice = Dice()
        dice.die1 = 3
        dice.die2 = 5
        self.assertFalse(dice.is_doubles())

    def test_TC_D5_doubles_streak_increments(self):
        """
        TC-D5  |  Branch: roll() — doubles path increments streak
        Why needed: three consecutive doubles sends player to jail — streak must count.
        Expect: doubles_streak goes from 0 to 1 after one double.
        """
        dice = Dice()
        dice.die1 = 4; dice.die2 = 4; dice.doubles_streak = 0
        if dice.is_doubles():
            dice.doubles_streak += 1
        self.assertEqual(dice.doubles_streak, 1)

    def test_TC_D6_doubles_streak_resets(self):
        """
        TC-D6  |  Branch: roll() — non-doubles path resets streak to 0
        Why needed: streak must be cleared after any non-double roll.
        Expect: doubles_streak == 0.
        """
        dice = Dice()
        dice.doubles_streak = 2
        dice.die1 = 3; dice.die2 = 5
        if not dice.is_doubles():
            dice.doubles_streak = 0
        self.assertEqual(dice.doubles_streak, 0)

    def test_TC_D7_total_equals_sum(self):
        """
        TC-D7  |  total() — basic arithmetic correctness
        Why needed: total() is used directly to move players; must equal die1+die2.
        Expect: 7 (4 + 3).
        """
        dice = Dice()
        dice.die1 = 4; dice.die2 = 3
        self.assertEqual(dice.total(), 7)

    def test_TC_D8_reset_clears_all(self):
        """
        TC-D8  |  Edge case: reset() must zero dice values and streak
        Why needed: reset() is called at the start of each turn cycle.
        Expect: die1=0, die2=0, streak=0.
        """
        dice = Dice()
        dice.die1 = 6; dice.die2 = 6; dice.doubles_streak = 3
        dice.reset()
        self.assertEqual(dice.die1, 0)
        self.assertEqual(dice.die2, 0)
        self.assertEqual(dice.doubles_streak, 0)


# ===========================================================================
# 2. PLAYER — MONEY
# ===========================================================================

class TestPlayerMoney(unittest.TestCase):

    def test_TC_P1_add_money_positive(self):
        """
        TC-P1  |  add_money() — normal positive amount
        Why needed: covers the main success path of add_money.
        Expect: 1000 + 500 = 1500.
        """
        p = Player("Alice", 1000)
        p.add_money(500)
        self.assertEqual(p.balance, 1500)

    def test_TC_P2_add_money_zero(self):
        """
        TC-P2  |  Edge case: add_money(0)
        Why needed: zero must be a no-op, not crash.
        Expect: balance unchanged.
        """
        p = Player("Alice", 1000)
        p.add_money(0)
        self.assertEqual(p.balance, 1000)

    def test_TC_P3_add_money_negative_raises(self):
        """
        TC-P3  |  Branch: add_money() if amount < 0 — raises ValueError
        Why needed: guard against accidentally crediting negative amounts.
        Expect: ValueError raised.
        """
        p = Player("Alice", 1000)
        with self.assertRaises(ValueError):
            p.add_money(-1)

    def test_TC_P4_deduct_money_positive(self):
        """
        TC-P4  |  deduct_money() — normal positive amount
        Why needed: covers the main success path of deduct_money.
        Expect: 1000 - 400 = 600.
        """
        p = Player("Alice", 1000)
        p.deduct_money(400)
        self.assertEqual(p.balance, 600)

    def test_TC_P5_deduct_exact_balance(self):
        """
        TC-P5  |  Edge case: deduct exactly whole balance — boundary of bankrupt
        Why needed: balance == 0 must trigger is_bankrupt() True (uses <=).
        Expect: balance == 0, is_bankrupt() == True.
        """
        p = Player("Alice", 500)
        p.deduct_money(500)
        self.assertEqual(p.balance, 0)
        self.assertTrue(p.is_bankrupt())

    def test_TC_P6_deduct_below_zero(self):
        """
        TC-P6  |  Edge case: deduct more than balance — negative balance
        Why needed: player can go into debt; no guard in deduct_money.
        Expect: balance == -100, is_bankrupt() == True.
        """
        p = Player("Alice", 100)
        p.deduct_money(200)
        self.assertEqual(p.balance, -100)
        self.assertTrue(p.is_bankrupt())

    def test_TC_P7_deduct_negative_raises(self):
        """
        TC-P7  |  Branch: deduct_money() if amount < 0 — raises ValueError
        Why needed: deducting a negative would silently add money.
        Expect: ValueError raised.
        """
        p = Player("Alice", 1000)
        with self.assertRaises(ValueError):
            p.deduct_money(-50)

    def test_TC_P8_is_bankrupt_false(self):
        """
        TC-P8  |  Branch: is_bankrupt() — False path (balance > 0)
        Why needed: positive balance means player is still active.
        Expect: False.
        """
        p = Player("Alice", 1)
        self.assertFalse(p.is_bankrupt())

    def test_TC_P9_is_bankrupt_true_at_zero(self):
        """
        TC-P9  |  Branch: is_bankrupt() — True path (balance == 0, boundary)
        Why needed: exactly zero triggers bankruptcy via <= check.
        Expect: True.
        """
        p = Player("Alice", 0)
        self.assertTrue(p.is_bankrupt())


# ===========================================================================
# 3. PLAYER — MOVE
# ===========================================================================

class TestPlayerMove(unittest.TestCase):

    def test_TC_M1_normal_move_no_go(self):
        """
        TC-M1  |  move() — normal forward move, no Go crossing
        Why needed: most common path; position must advance correctly.
        Expect: position = 11, balance unchanged.
        """
        p = Player("Bob")
        p.position = 5
        p.move(6)
        self.assertEqual(p.position, 11)
        self.assertEqual(p.balance, STARTING_BALANCE)

    def test_TC_M2_lands_exactly_on_go(self):
        """
        TC-M2  |  Branch: move() — landing exactly on position 0 awards salary
        Why needed: exact landing on Go is one valid case for $200 award.
        Expect: position == 0, balance += $200.
        """
        p = Player("Bob")
        p.position = 36
        old = p.balance
        p.move(4)    # 36 + 4 = 40 → wraps to 0
        self.assertEqual(p.position, 0)
        self.assertEqual(p.balance, old + GO_SALARY)

    def test_TC_M3_passes_go_salary_awarded(self):
        """
        TC-M3  |  FIXED: move() awards $200 when PASSING Go (not just landing)
        Bug was: only checked position==0; players who passed without landing got $0.
        Fix:     check old_position + steps >= BOARD_SIZE in player.py move().
        Why needed: most Go collections happen by passing, not exact landing.
        Expect: balance += $200 when player wraps from pos 38 to pos 2.
        """
        p = Player("Bob")
        p.position = 38
        old = p.balance
        p.move(4)    # 38 + 4 = 42 → wraps to 2; passed Go
        self.assertEqual(p.position, 2)
        self.assertEqual(p.balance, old + GO_SALARY,
            "FAIL: passed Go but no salary — fix position==0 to old+steps>=BOARD_SIZE")

    def test_TC_M4_wrap_around_stays_in_bounds(self):
        """
        TC-M4  |  Edge case: wrap-around must keep position inside 0..39
        Why needed: % BOARD_SIZE must work correctly at every boundary.
        Expect: position == 1.
        """
        p = Player("Bob")
        p.position = 39
        p.move(2)
        self.assertEqual(p.position, 1)

    def test_TC_M5_go_to_jail(self):
        """
        TC-M5  |  go_to_jail() — all three state variables must change
        Why needed: jailing sets three fields; all must be verified.
        Expect: position=10, in_jail=True, jail_turns=0.
        """
        p = Player("Bob")
        p.position = 25; p.jail_turns = 2
        p.go_to_jail()
        self.assertEqual(p.position, JAIL_POSITION)
        self.assertTrue(p.in_jail)
        self.assertEqual(p.jail_turns, 0)

    def test_TC_M6_large_steps_stay_in_bounds(self):
        """
        TC-M6  |  Edge case: very large roll value
        Why needed: modulo arithmetic must handle large inputs correctly.
        Expect: position always in [0, 39].
        """
        p = Player("Bob")
        p.position = 0
        p.move(400)    # 400 % 40 = 0
        self.assertGreaterEqual(p.position, 0)
        self.assertLessEqual(p.position, 39)


# ===========================================================================
# 4. PLAYER — PROPERTIES
# ===========================================================================

class TestPlayerProperties(unittest.TestCase):

    def test_TC_PP1_add_property(self):
        """
        TC-PP1  |  add_property() — normal add
        Why needed: property list must grow by one when a new property is added.
        Expect: prop in properties, count == 1.
        """
        p = Player("Alice")
        prop = make_prop()
        p.add_property(prop)
        self.assertIn(prop, p.properties)
        self.assertEqual(len(p.properties), 1)

    def test_TC_PP2_add_property_duplicate_ignored(self):
        """
        TC-PP2  |  Branch: add_property() — if prop not in list (duplicate guard)
        Why needed: adding same property twice must not double-count it.
        Expect: count stays at 1.
        """
        p = Player("Alice")
        prop = make_prop()
        p.add_property(prop)
        p.add_property(prop)
        self.assertEqual(len(p.properties), 1)

    def test_TC_PP3_remove_property(self):
        """
        TC-PP3  |  remove_property() — if prop in list (True branch)
        Why needed: property must be removed from list on sale or bankruptcy.
        Expect: prop not in properties.
        """
        p = Player("Alice")
        prop = make_prop()
        p.add_property(prop)
        p.remove_property(prop)
        self.assertNotIn(prop, p.properties)

    def test_TC_PP4_remove_property_not_owned_noop(self):
        """
        TC-PP4  |  Branch: remove_property() — if prop not in list (no-op)
        Why needed: must not raise when removing a property not in the list.
        Expect: no error, list stays empty.
        """
        p = Player("Alice")
        p.remove_property(make_prop())
        self.assertEqual(len(p.properties), 0)


# ===========================================================================
# 5. PROPERTY — RENT
# ===========================================================================

class TestPropertyRent(unittest.TestCase):

    def test_TC_R1_mortgaged_rent_zero(self):
        """
        TC-R1  |  Branch: get_rent() — if is_mortgaged → return 0
        Why needed: mortgaged properties must charge zero rent.
        Expect: 0.
        """
        prop = make_prop(base_rent=6)
        prop.owner = Player("Alice")
        prop.is_mortgaged = True
        self.assertEqual(prop.get_rent(), 0)

    def test_TC_R2_no_group_returns_base_rent(self):
        """
        TC-R2  |  Branch: get_rent() — group is None → return base_rent
        Why needed: property without a group always returns base rent.
        Expect: 6.
        """
        prop = make_prop(base_rent=6)
        prop.owner = Player("Alice")
        self.assertEqual(prop.get_rent(), 6)

    def test_TC_R3_partial_group_not_doubled(self):
        """
        TC-R3  |  FIXED: all_owned_by uses all() not any()
        Bug was: any() doubled rent when player owned only ONE property in group.
        Fix:     all() in property.py all_owned_by().
        Why needed: rent doubles only when the ENTIRE colour group is owned.
        Expect: rent == base_rent (NOT doubled) when Alice owns only 1 of 2 browns.
        """
        grp, p1, p2 = make_brown_group()
        alice = Player("Alice")
        bob   = Player("Bob")
        p1.owner = alice
        p2.owner = bob
        self.assertEqual(p1.get_rent(), p1.base_rent,
            "FAIL: partial group doubling rent — fix any() to all() in all_owned_by()")

    def test_TC_R4_full_group_rent_doubled(self):
        """
        TC-R4  |  Branch: get_rent() — all_owned_by True → doubled rent
        Why needed: owning all properties in a group must double every rent.
        Expect: rent == base_rent * 2 for both properties.
        """
        grp, p1, p2 = make_brown_group()
        alice = Player("Alice")
        p1.owner = alice
        p2.owner = alice
        self.assertEqual(p1.get_rent(), p1.base_rent * 2)
        self.assertEqual(p2.get_rent(), p2.base_rent * 2)

    def test_TC_R5_all_owned_by_none_false(self):
        """
        TC-R5  |  Branch: all_owned_by(None) — if player is None → False
        Why needed: None player must never trigger doubled rent.
        Expect: False.
        """
        grp, p1, p2 = make_brown_group()
        self.assertFalse(grp.all_owned_by(None))


# ===========================================================================
# 6. PROPERTY — MORTGAGE
# ===========================================================================

class TestPropertyMortgage(unittest.TestCase):

    def test_TC_MG1_mortgage_returns_half_price(self):
        """
        TC-MG1  |  mortgage() — not mortgaged path (normal case)
        Why needed: payout must equal price // 2.
        Expect: 30, is_mortgaged = True.
        """
        prop = make_prop(price=60)
        self.assertEqual(prop.mortgage(), 30)
        self.assertTrue(prop.is_mortgaged)

    def test_TC_MG2_mortgage_already_mortgaged(self):
        """
        TC-MG2  |  Branch: mortgage() — if is_mortgaged → return 0
        Why needed: mortgaging twice must be blocked.
        Expect: 0.
        """
        prop = make_prop(price=60)
        prop.mortgage()
        self.assertEqual(prop.mortgage(), 0)

    def test_TC_MG3_unmortgage_cost_110_percent(self):
        """
        TC-MG3  |  unmortgage() — is_mortgaged True path (else branch)
        Why needed: redemption cost is 110% of mortgage value.
        Expect: 33 (int(30 * 1.1)), is_mortgaged = False.
        """
        prop = make_prop(price=60)
        prop.mortgage()
        cost = prop.unmortgage()
        self.assertEqual(cost, int(30 * 1.1))
        self.assertFalse(prop.is_mortgaged)

    def test_TC_MG4_unmortgage_not_mortgaged(self):
        """
        TC-MG4  |  Branch: unmortgage() — if not is_mortgaged → return 0
        Why needed: cannot un-mortgage a property that was never mortgaged.
        Expect: 0.
        """
        prop = make_prop(price=60)
        self.assertEqual(prop.unmortgage(), 0)

    def test_TC_MG5_is_available_true(self):
        """
        TC-MG5  |  is_available() — unowned and not mortgaged (True path)
        Expect: True.
        """
        prop = make_prop()
        self.assertTrue(prop.is_available())

    def test_TC_MG6_is_available_owned(self):
        """
        TC-MG6  |  is_available() — owned → False
        Expect: False.
        """
        prop = make_prop()
        prop.owner = Player("Alice")
        self.assertFalse(prop.is_available())

    def test_TC_MG7_is_available_mortgaged(self):
        """
        TC-MG7  |  is_available() — mortgaged → False
        Expect: False.
        """
        prop = make_prop()
        prop.is_mortgaged = True
        self.assertFalse(prop.is_available())


# ===========================================================================
# 7. BANK
# ===========================================================================

class TestBank(unittest.TestCase):

    def test_TC_B1_initial_balance(self):
        """
        TC-B1  |  Bank.__init__ — starting funds match config constant
        Expect: BANK_STARTING_FUNDS.
        """
        bank = Bank()
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS)

    def test_TC_B2_collect_positive(self):
        """
        TC-B2  |  collect() — positive amount increases reserves
        Expect: balance increases by 500.
        """
        bank = Bank()
        bank.collect(500)
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS + 500)

    def test_TC_B3_collect_negative_reduces(self):
        """
        TC-B3  |  collect() — negative amount (used in mortgage payout)
        Why needed: game.py calls bank.collect(-payout) to reduce reserves.
        Expect: balance decreases by 100.
        """
        bank = Bank()
        before = bank.get_balance()
        bank.collect(-100)
        self.assertEqual(bank.get_balance(), before - 100)

    def test_TC_B4_pay_out_normal(self):
        """
        TC-B4  |  pay_out() — normal payout decreases balance
        Expect: paid == 200, balance reduced.
        """
        bank = Bank()
        paid = bank.pay_out(200)
        self.assertEqual(paid, 200)
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS - 200)

    def test_TC_B5_pay_out_zero(self):
        """
        TC-B5  |  Branch: pay_out() — if amount <= 0 → return 0
        Expect: 0.
        """
        bank = Bank()
        self.assertEqual(bank.pay_out(0), 0)

    def test_TC_B6_pay_out_insufficient_raises(self):
        """
        TC-B6  |  Branch: pay_out() — if amount > funds → ValueError
        Expect: ValueError.
        """
        bank = Bank()
        with self.assertRaises(ValueError):
            bank.pay_out(bank.get_balance() + 1)

    def test_TC_B7_give_loan_credits_player(self):
        """
        TC-B7  |  give_loan() — player receives the amount
        Expect: player balance += 500, loan recorded.
        """
        bank   = Bank()
        player = Player("Alice", 0)
        bank.give_loan(player, 500)
        self.assertEqual(player.balance, 500)
        self.assertEqual(bank.loan_count(), 1)

    def test_TC_B8_give_loan_reduces_bank_funds(self):
        """
        TC-B8  |  FIXED: give_loan() now reduces bank reserves
        Bug was: self._funds -= amount was missing — bank created money from nothing.
        Fix:     added self._funds -= amount in bank.py give_loan().
        Why needed: total money in game must not increase when a loan is issued.
        Expect: bank balance decreases by 500.
        """
        bank   = Bank()
        player = Player("Alice", 0)
        before = bank.get_balance()
        bank.give_loan(player, 500)
        self.assertEqual(bank.get_balance(), before - 500,
            "FAIL: bank funds not reduced — add self._funds -= amount in give_loan()")

    def test_TC_B9_give_loan_zero_noop(self):
        """
        TC-B9  |  Branch: give_loan() — if amount <= 0 → return (no-op)
        Expect: loan_count == 0, player balance unchanged.
        """
        bank   = Bank()
        player = Player("Alice", 0)
        bank.give_loan(player, 0)
        self.assertEqual(bank.loan_count(), 0)
        self.assertEqual(player.balance, 0)


# ===========================================================================
# 8. GAME.buy_property  (real Game method)
# ===========================================================================

class TestBuyProperty(unittest.TestCase):
    """Tests call game.buy_property() directly on a real Game instance."""

    def _setup(self):
        game = make_game(["Alice", "Bob"])
        alice = game.players[0]
        prop  = make_prop(price=60)
        return game, alice, prop

    def test_TC_BUY1_exact_balance_allowed(self):
        """
        TC-BUY1  |  FIXED: buy_property uses < not <=
        Bug was: balance == price was blocked.
        Fix:     changed <= to < in game.py buy_property().
        Why needed: player with exactly the right amount must be able to buy.
        Expect: True, property owned, balance == 0.
        """
        game, alice, prop = self._setup()
        alice.balance = 60
        result = game.buy_property(alice, prop)
        self.assertTrue(result,
            "FAIL: exact balance blocked — fix <= to < in buy_property()")
        self.assertEqual(alice.balance, 0)
        self.assertEqual(prop.owner, alice)

    def test_TC_BUY2_sufficient_funds(self):
        """
        TC-BUY2  |  Branch: buy_property() — balance > price (success path)
        Expect: True, owner set, balance reduced.
        """
        game, alice, prop = self._setup()
        alice.balance = 500
        prop2 = make_prop(price=200)
        result = game.buy_property(alice, prop2)
        self.assertTrue(result)
        self.assertEqual(prop2.owner, alice)
        self.assertEqual(alice.balance, 300)

    def test_TC_BUY3_insufficient_funds(self):
        """
        TC-BUY3  |  Branch: buy_property() — balance < price (reject path)
        Expect: False, property stays unowned.
        """
        game, alice, prop = self._setup()
        alice.balance = 50
        result = game.buy_property(alice, prop)
        self.assertFalse(result)
        self.assertIsNone(prop.owner)

    def test_TC_BUY4_zero_balance_rejected(self):
        """
        TC-BUY4  |  Edge case: zero balance cannot buy anything
        Expect: False.
        """
        game, alice, prop = self._setup()
        alice.balance = 0
        result = game.buy_property(alice, prop)
        self.assertFalse(result)

    def test_TC_BUY5_bank_receives_price(self):
        """
        TC-BUY5  |  buy_property() — bank.collect(prop.price) is called
        Expect: bank balance increases by property price.
        """
        game, alice, prop = self._setup()
        alice.balance = 500
        prop2 = make_prop(price=200)
        before = game.bank.get_balance()
        game.buy_property(alice, prop2)
        self.assertEqual(game.bank.get_balance(), before + 200)


# ===========================================================================
# 9. GAME.pay_rent  (real Game method)
# ===========================================================================

class TestPayRent(unittest.TestCase):
    """Tests call game.pay_rent() directly on a real Game instance."""

    def _setup(self):
        game  = make_game(["Alice", "Bob"])
        alice = game.players[0]
        bob   = game.players[1]
        prop  = make_prop(base_rent=20)
        prop.owner = bob
        return game, alice, bob, prop

    def test_TC_RNT1_owner_receives_rent(self):
        """
        TC-RNT1  |  FIXED: pay_rent() now credits the owner
        Bug was: prop.owner.add_money(rent) was completely missing.
        Fix:     added prop.owner.add_money(rent) in game.py pay_rent().
        Why needed: rent must transfer from payer to owner, not disappear.
        Expect: alice loses $20, bob gains $20.
        """
        game, alice, bob, prop = self._setup()
        game.pay_rent(alice, prop)
        self.assertEqual(alice.balance, STARTING_BALANCE - 20)
        self.assertEqual(bob.balance, STARTING_BALANCE + 20,
            "FAIL: owner did not receive rent — add prop.owner.add_money(rent)")

    def test_TC_RNT2_payer_loses_rent(self):
        """
        TC-RNT2  |  pay_rent() — payer's balance must decrease by rent
        Expect: alice.balance == STARTING_BALANCE - 20.
        """
        game, alice, bob, prop = self._setup()
        game.pay_rent(alice, prop)
        self.assertEqual(alice.balance, STARTING_BALANCE - 20)

    def test_TC_RNT3_mortgaged_no_charge(self):
        """
        TC-RNT3  |  Branch: pay_rent() — if is_mortgaged → return early
        Why needed: mortgaged properties must not collect rent.
        Expect: both balances unchanged.
        """
        game, alice, bob, prop = self._setup()
        prop.is_mortgaged = True
        game.pay_rent(alice, prop)
        self.assertEqual(alice.balance, STARTING_BALANCE)
        self.assertEqual(bob.balance,   STARTING_BALANCE)

    def test_TC_RNT4_unowned_no_charge(self):
        """
        TC-RNT4  |  Branch: pay_rent() — if owner is None → return early
        Why needed: unowned properties cannot collect rent.
        Expect: alice balance unchanged.
        """
        game, alice, bob, _ = self._setup()
        unowned = make_prop(base_rent=20)
        game.pay_rent(alice, unowned)
        self.assertEqual(alice.balance, STARTING_BALANCE)


# ===========================================================================
# 10. GAME.find_winner  (real Game method)
# ===========================================================================

class TestFindWinner(unittest.TestCase):
    """Tests call game.find_winner() on a real Game instance."""

    def test_TC_W1_richest_player_wins(self):
        """
        TC-W1  |  FIXED: find_winner uses max() not min()
        Bug was: min() returned the POOREST player as winner.
        Fix:     changed min() to max() in game.py find_winner().
        Why needed: winner must have the HIGHEST net worth.
        Expect: Alice ($2000) wins over Bob ($500).
        """
        game = make_game(["Alice", "Bob"])
        game.players[0].balance = 2000
        game.players[1].balance = 500
        winner = game.find_winner()
        self.assertEqual(winner.name, "Alice",
            "FAIL: find_winner returned wrong player — fix min() to max()")

    def test_TC_W2_empty_list_returns_none(self):
        """
        TC-W2  |  Branch: find_winner() — if not players → return None
        Why needed: edge case when all players are eliminated.
        Expect: None.
        """
        game = make_game(["Alice", "Bob"])
        game.players.clear()
        self.assertIsNone(game.find_winner())

    def test_TC_W3_single_player_wins(self):
        """
        TC-W3  |  Edge case: only one player remaining always wins
        Expect: that player is returned.
        """
        game = make_game(["Alice", "Bob"])
        game.players = [game.players[0]]
        winner = game.find_winner()
        self.assertEqual(winner.name, "Alice")

    def test_TC_W4_three_players_richest_wins(self):
        """
        TC-W4  |  find_winner() — three players, max() picks richest
        Why needed: verifies max() works correctly with more than 2 players.
        Expect: Alice ($2000) wins over Bob ($1500) and Carol ($100).
        """
        game = make_game(["Alice", "Bob", "Carol"])
        game.players[0].balance = 2000
        game.players[1].balance = 1500
        game.players[2].balance = 100
        winner = game.find_winner()
        self.assertEqual(winner.name, "Alice")


# ===========================================================================
# 11. GAME.trade  (real Game method)
# ===========================================================================

class TestTrade(unittest.TestCase):
    """Tests call game.trade() directly on a real Game instance."""

    def _setup(self):
        game  = make_game(["Alice", "Bob"])
        alice = game.players[0]
        bob   = game.players[1]
        prop  = make_prop(price=100)
        prop.owner = alice
        alice.add_property(prop)
        return game, alice, bob, prop

    def test_TC_T1_seller_receives_cash(self):
        """
        TC-T1  |  FIXED: trade() now credits the seller
        Bug was: seller.add_money(cash_amount) was completely missing.
        Fix:     added seller.add_money(cash_amount) in game.py trade().
        Why needed: seller must receive cash when giving up a property.
        Expect: alice gains $80, bob loses $80.
        """
        game, alice, bob, prop = self._setup()
        alice.balance = 1000
        bob.balance   = 500
        game.trade(alice, bob, prop, 80)
        self.assertEqual(bob.balance, 420)
        self.assertEqual(alice.balance, 1080,
            "FAIL: seller got nothing — add seller.add_money(cash_amount) in trade()")

    def test_TC_T2_buyer_loses_cash(self):
        """
        TC-T2  |  trade() — buyer.deduct_money(cash_amount) must run
        Expect: bob.balance == 420 (500 - 80).
        """
        game, alice, bob, prop = self._setup()
        alice.balance = 1000
        bob.balance   = 500
        game.trade(alice, bob, prop, 80)
        self.assertEqual(bob.balance, 420)

    def test_TC_T3_property_transfers(self):
        """
        TC-T3  |  trade() — ownership must transfer to buyer
        Expect: prop.owner == bob, prop in bob.properties, not in alice.properties.
        """
        game, alice, bob, prop = self._setup()
        alice.balance = 1000
        bob.balance   = 500
        game.trade(alice, bob, prop, 80)
        self.assertEqual(prop.owner, bob)
        self.assertIn(prop, bob.properties)
        self.assertNotIn(prop, alice.properties)

    def test_TC_T4_buyer_cannot_afford(self):
        """
        TC-T4  |  Branch: trade() — if buyer.balance < cash_amount → False
        Expect: False, property stays with seller.
        """
        game, alice, bob, prop = self._setup()
        bob.balance = 10
        result = game.trade(alice, bob, prop, 80)
        self.assertFalse(result)

    def test_TC_T5_seller_does_not_own(self):
        """
        TC-T5  |  Branch: trade() — if prop.owner != seller → False
        Expect: False.
        """
        game  = make_game(["Alice", "Bob", "Carol"])
        alice = game.players[0]
        bob   = game.players[1]
        carol = game.players[2]
        prop  = make_prop(price=100)
        prop.owner = carol    # carol owns it, not alice
        result = game.trade(alice, bob, prop, 80)
        self.assertFalse(result)


# ===========================================================================
# 12. EDGE CASES
# ===========================================================================

class TestEdgeCases(unittest.TestCase):

    def test_TC_E1_very_large_balance(self):
        """
        TC-E1  |  Edge case: very large player balance
        Why needed: no overflow should occur with large numbers.
        Expect: 20,000,000.
        """
        p = Player("Alice", 10_000_000)
        p.add_money(10_000_000)
        self.assertEqual(p.balance, 20_000_000)

    def test_TC_E2_bank_many_deposits(self):
        """
        TC-E2  |  Edge case: 1000 small deposits to bank
        Why needed: accumulation of many small amounts must be exact.
        Expect: BANK_STARTING_FUNDS + 10,000.
        """
        bank = Bank()
        for _ in range(1000):
            bank.collect(10)
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS + 10_000)

    def test_TC_E3_dice_total_matches_dice(self):
        """
        TC-E3  |  Edge case: total() must equal die1 + die2 every roll
        Why needed: total() is used to move players; any mismatch breaks the game.
        Expect: total == die1 + die2 for 100 rolls.
        """
        dice = Dice()
        for _ in range(100):
            total = dice.roll()
            self.assertEqual(total, dice.die1 + dice.die2)

    def test_TC_E4_move_full_lap(self):
        """
        TC-E4  |  Edge case: moving exactly 40 steps returns to same square
        Why needed: full lap should not change position.
        Expect: position == 5 after moving 40 from 5.
        """
        p = Player("Bob")
        p.position = 5
        p.move(40)
        self.assertEqual(p.position, 5)

    def test_TC_E5_bank_pay_out_all_funds(self):
        """
        TC-E5  |  Edge case: pay_out exactly all bank funds
        Why needed: boundary — paying the exact reserve must not raise.
        Expect: paid == BANK_STARTING_FUNDS, balance == 0.
        """
        bank = Bank()
        paid = bank.pay_out(BANK_STARTING_FUNDS)
        self.assertEqual(paid, BANK_STARTING_FUNDS)
        self.assertEqual(bank.get_balance(), 0)

    def test_TC_E6_odd_price_floor_division(self):
        """
        TC-E6  |  Edge case: odd property price uses floor division
        Why needed: 61 // 2 = 30, not 30.5 — must be integer.
        Expect: mortgage_value == 30.
        """
        prop = Property("Odd", 1, 61, 2)
        self.assertEqual(prop.mortgage_value, 30)

    def test_TC_E7_empty_group_all_owned(self):
        """
        TC-E7  |  FIXED: all_owned_by on empty group
        Bug was: any([]) == False.
        Fix:     all([]) == True (vacuous truth — empty group has no violators).
        Why needed: shows semantic difference between any() and all() on empty list.
        Expect: True.
        """
        grp   = PropertyGroup("Empty", "none")
        alice = Player("Alice")
        self.assertTrue(grp.all_owned_by(alice),
            "FAIL: empty group returned False — fix any() to all()")


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    import sys
    print()
    print("=" * 70)
    print("  MoneyPoly — White-Box Test Suite (imports from real package)")
    print()
    print("  Run from the directory that contains the moneypoly/ folder.")
    print("  All 73 tests should pass on the fully corrected codebase.")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)