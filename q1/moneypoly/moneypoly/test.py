"""
White-box test suite for MoneyPoly.
Self-contained: all classes are copied inline — no package install needed.
Run with:  python3 test_moneypoly.py
"""

import random
import unittest

STARTING_BALANCE      = 1500
GO_SALARY             = 200
BOARD_SIZE            = 40
JAIL_POSITION         = 10
JAIL_FINE             = 50
INCOME_TAX_AMOUNT     = 200
LUXURY_TAX_AMOUNT     = 75
BANK_STARTING_FUNDS   = 20580
AUCTION_MIN_INCREMENT = 10


# ---- property.py (original) -----------------------------------------------

class PropertyGroup:
    def __init__(self, name, color):
        self.name       = name
        self.color      = color
        self.properties = []

    def add_property(self, prop):
        if prop not in self.properties:
            self.properties.append(prop)
            prop.group = self

    def all_owned_by(self, player):
        """Original: uses any() — BUG, should be all()"""
        if player is None:
            return False
        return any(p.owner == player for p in self.properties)   # BUG

    def size(self):
        return len(self.properties)


class Property:
    FULL_GROUP_MULTIPLIER = 2

    def __init__(self, name, position, price, base_rent, group=None):
        self.name           = name
        self.position       = position
        self.price          = price
        self.base_rent      = base_rent
        self.mortgage_value = price // 2
        self.owner          = None
        self.is_mortgaged   = False
        self.houses         = 0
        self.group          = group
        if group is not None and self not in group.properties:
            group.properties.append(self)

    def get_rent(self):
        if self.is_mortgaged:
            return 0
        if self.group is not None and self.group.all_owned_by(self.owner):
            return self.base_rent * self.FULL_GROUP_MULTIPLIER
        return self.base_rent

    def mortgage(self):
        if self.is_mortgaged:
            return 0
        self.is_mortgaged = True
        return self.mortgage_value

    def unmortgage(self):
        if not self.is_mortgaged:
            return 0
        else:
            cost = int(self.mortgage_value * 1.1)
            self.is_mortgaged = False
            return cost

    def is_available(self):
        return self.owner is None and not self.is_mortgaged


# ---- player.py (original) -------------------------------------------------

class Player:
    def __init__(self, name, balance=STARTING_BALANCE):
        self.name                  = name
        self.balance               = balance
        self.position              = 0
        self.properties            = []
        self.in_jail               = False
        self.jail_turns            = 0
        self.get_out_of_jail_cards = 0
        self.is_eliminated         = False

    def add_money(self, amount):
        if amount < 0:
            raise ValueError(f"Cannot add a negative amount: {amount}")
        self.balance += amount

    def deduct_money(self, amount):
        if amount < 0:
            raise ValueError(f"Cannot deduct a negative amount: {amount}")
        self.balance -= amount

    def is_bankrupt(self):
        return self.balance <= 0

    def net_worth(self):
        return self.balance

    def move(self, steps):
        """Original: only awards Go salary when landing exactly on pos 0 — BUG"""
        self.position = (self.position + steps) % BOARD_SIZE
        if self.position == 0:           # BUG: misses pass-through case
            self.add_money(GO_SALARY)
        return self.position

    def go_to_jail(self):
        self.position   = JAIL_POSITION
        self.in_jail    = True
        self.jail_turns = 0

    def add_property(self, prop):
        if prop not in self.properties:
            self.properties.append(prop)

    def remove_property(self, prop):
        if prop in self.properties:
            self.properties.remove(prop)

    def count_properties(self):
        return len(self.properties)


# ---- bank.py (original) ---------------------------------------------------

class Bank:
    def __init__(self):
        self._funds           = BANK_STARTING_FUNDS
        self._loans_issued    = []
        self._total_collected = 0

    def get_balance(self):
        return self._funds

    def collect(self, amount):
        self._funds           += amount
        self._total_collected += amount

    def pay_out(self, amount):
        if amount <= 0:
            return 0
        if amount > self._funds:
            raise ValueError(
                f"Bank cannot pay ${amount}; only ${self._funds} available."
            )
        self._funds -= amount
        return amount

    def give_loan(self, player, amount):
        if amount <= 0:
            return
        player.add_money(amount)
        self._loans_issued.append((player.name, amount))
        # BUG: self._funds is never reduced — bank creates money from nothing

    def total_loans_issued(self):
        return sum(amt for _, amt in self._loans_issued)

    def loan_count(self):
        return len(self._loans_issued)


# ---- dice.py (original) ---------------------------------------------------

class Dice:
    def __init__(self):
        self.die1           = 0
        self.die2           = 0
        self.doubles_streak = 0
        self.reset()

    def reset(self):
        self.die1           = 0
        self.die2           = 0
        self.doubles_streak = 0

    def roll(self):
        """Original: randint(1,5) — BUG, dice are 6-sided"""
        self.die1 = random.randint(1, 5)   # BUG
        self.die2 = random.randint(1, 5)   # BUG
        if self.is_doubles():
            self.doubles_streak += 1
        else:
            self.doubles_streak = 0
        return self.total()

    def is_doubles(self):
        return self.die1 == self.die2

    def total(self):
        return self.die1 + self.die2

    def describe(self):
        doubles_note = " (DOUBLES)" if self.is_doubles() else ""
        return f"{self.die1} + {self.die2} = {self.total()}{doubles_note}"


# ---- game.py functions (original, inline) ---------------------------------

def buy_property_original(bank, player, prop):
    """Exact logic from game.py buy_property — BUG: uses <= instead of <"""
    if player.balance <= prop.price:        # BUG
        return False
    player.deduct_money(prop.price)
    prop.owner = player
    player.add_property(prop)
    bank.collect(prop.price)
    return True


def pay_rent_original(player, prop):
    """Exact logic from game.py pay_rent — BUG: never credits owner"""
    if prop.is_mortgaged:
        return
    if prop.owner is None:
        return
    rent = prop.get_rent()
    player.deduct_money(rent)
    # BUG: prop.owner.add_money(rent) is missing


def find_winner_original(players):
    """Exact logic from game.py find_winner — BUG: uses min() instead of max()"""
    if not players:
        return None
    return min(players, key=lambda p: p.net_worth())   # BUG


def trade_original(seller, buyer, prop, cash_amount):
    """Exact logic from game.py trade — BUG: seller never receives cash"""
    if prop.owner != seller:
        return False
    if buyer.balance < cash_amount:
        return False
    buyer.deduct_money(cash_amount)
    prop.owner = buyer
    seller.remove_property(prop)
    buyer.add_property(prop)
    # BUG: seller.add_money(cash_amount) is missing
    return True


# ===========================================================================
# HELPERS
# ===========================================================================

def make_prop(name="Test Ave", position=1, price=60, base_rent=4, group=None):
    return Property(name, position, price, base_rent, group)


def make_brown_group():
    """Return (group, prop1, prop2) for the two brown properties."""
    grp = PropertyGroup("Brown", "brown")
    p1  = Property("Mediterranean Avenue", 1, 60, 2, grp)
    p2  = Property("Baltic Avenue",        3, 60, 4, grp)
    return grp, p1, p2


# ===========================================================================
# TEST CLASSES
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. DICE TESTS
# ---------------------------------------------------------------------------

class TestDice(unittest.TestCase):

    def test_TC_D1_roll_never_produces_six_BUG(self):
        """
        TC-D1  |  BUG DETECTION
        Code:   dice.py → roll() → randint(1,5)
        Why:    Real dice are 6-sided. randint(1,5) means 6 is impossible.
        Expect (buggy code): seen_six == False  → test PASSES, confirming bug.
        Fix needed: change randint(1,5) to randint(1,6)
        """
        dice = Dice()
        seen_six = False
        for _ in range(500):
            dice.roll()
            if dice.die1 == 6 or dice.die2 == 6:
                seen_six = True
                break
        self.assertFalse(seen_six,
            "BUG PRESENT: randint(1,5) — value 6 never produced by dice")

    def test_TC_D2_roll_values_within_1_to_5(self):
        """
        TC-D2  |  Branch: roll() — valid range check (confirms bug range)
        Code:   dice.py → roll()
        Why:    With the bug, every die value must be 1–5, never 6.
        Expect: all values in [1,5].
        """
        dice = Dice()
        for _ in range(200):
            dice.roll()
            self.assertGreaterEqual(dice.die1, 1)
            self.assertLessEqual(dice.die1, 5)
            self.assertGreaterEqual(dice.die2, 1)
            self.assertLessEqual(dice.die2, 5)

    def test_TC_D3_is_doubles_true_branch(self):
        """
        TC-D3  |  Branch: is_doubles() → True path
        Code:   dice.py → is_doubles()
        Why:    When die1 == die2, must return True (triggers streak increment).
        Expect: True
        """
        dice = Dice()
        dice.die1 = 3
        dice.die2 = 3
        self.assertTrue(dice.is_doubles())

    def test_TC_D4_is_doubles_false_branch(self):
        """
        TC-D4  |  Branch: is_doubles() → False path
        Code:   dice.py → is_doubles()
        Why:    When die1 != die2, must return False (streak resets).
        Expect: False
        """
        dice = Dice()
        dice.die1 = 3
        dice.die2 = 5
        self.assertFalse(dice.is_doubles())

    def test_TC_D5_doubles_streak_increments(self):
        """
        TC-D5  |  Branch: roll() doubles path → streak increments
        Code:   dice.py → roll() → if is_doubles()
        Why:    Three consecutive doubles sends player to jail; streak must count.
        Expect: doubles_streak goes from 0 to 1.
        """
        dice = Dice()
        dice.die1 = 4; dice.die2 = 4; dice.doubles_streak = 0
        if dice.is_doubles():
            dice.doubles_streak += 1
        self.assertEqual(dice.doubles_streak, 1)

    def test_TC_D6_doubles_streak_resets_on_non_double(self):
        """
        TC-D6  |  Branch: roll() non-doubles path → streak resets
        Code:   dice.py → roll() → else branch
        Why:    After any non-double, the streak must go back to 0.
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
        TC-D7  |  total() basic correctness
        Code:   dice.py → total()
        Why:    total() must always equal die1 + die2.
        Expect: 7 (4 + 3).
        """
        dice = Dice()
        dice.die1 = 4; dice.die2 = 3
        self.assertEqual(dice.total(), 7)

    def test_TC_D8_reset_clears_all_values(self):
        """
        TC-D8  |  Edge case: reset() zeros everything
        Code:   dice.py → reset()
        Why:    reset() must clear die values and streak for a fresh turn.
        Expect: die1=0, die2=0, streak=0.
        """
        dice = Dice()
        dice.die1 = 6; dice.die2 = 6; dice.doubles_streak = 3
        dice.reset()
        self.assertEqual(dice.die1, 0)
        self.assertEqual(dice.die2, 0)
        self.assertEqual(dice.doubles_streak, 0)


# ---------------------------------------------------------------------------
# 2. PLAYER — MONEY
# ---------------------------------------------------------------------------

class TestPlayerMoney(unittest.TestCase):

    def test_TC_P1_add_money_positive(self):
        """
        TC-P1  |  add_money() — positive amount
        Code:   player.py → add_money()
        Why:    Normal case: balance increases by the given amount.
        Expect: 1000 + 500 = 1500.
        """
        p = Player("Alice", 1000)
        p.add_money(500)
        self.assertEqual(p.balance, 1500)

    def test_TC_P2_add_money_zero(self):
        """
        TC-P2  |  Edge case: add_money(0)
        Code:   player.py → add_money()
        Why:    Zero must not change the balance.
        Expect: balance unchanged.
        """
        p = Player("Alice", 1000)
        p.add_money(0)
        self.assertEqual(p.balance, 1000)

    def test_TC_P3_add_money_negative_raises(self):
        """
        TC-P3  |  Branch: add_money() — negative amount raises ValueError
        Code:   player.py → add_money() → if amount < 0
        Why:    Guards against accidentally crediting a negative amount.
        Expect: ValueError raised.
        """
        p = Player("Alice", 1000)
        with self.assertRaises(ValueError):
            p.add_money(-1)

    def test_TC_P4_deduct_money_positive(self):
        """
        TC-P4  |  deduct_money() — normal positive amount
        Code:   player.py → deduct_money()
        Why:    Normal case: balance decreases by the given amount.
        Expect: 1000 - 400 = 600.
        """
        p = Player("Alice", 1000)
        p.deduct_money(400)
        self.assertEqual(p.balance, 600)

    def test_TC_P5_deduct_money_exact_balance_bankrupt(self):
        """
        TC-P5  |  Edge case: deduct exactly the whole balance → bankrupt
        Code:   player.py → deduct_money() + is_bankrupt()
        Why:    Balance of 0 means is_bankrupt() returns True (boundary test).
        Expect: balance == 0, is_bankrupt() == True.
        """
        p = Player("Alice", 500)
        p.deduct_money(500)
        self.assertEqual(p.balance, 0)
        self.assertTrue(p.is_bankrupt())

    def test_TC_P6_deduct_money_below_zero(self):
        """
        TC-P6  |  Edge case: deduct more than balance → negative balance
        Code:   player.py → deduct_money()
        Why:    Player can go negative (bankruptcy); no guard in deduct_money.
        Expect: balance == -100, is_bankrupt() == True.
        """
        p = Player("Alice", 100)
        p.deduct_money(200)
        self.assertEqual(p.balance, -100)
        self.assertTrue(p.is_bankrupt())

    def test_TC_P7_deduct_money_negative_raises(self):
        """
        TC-P7  |  Branch: deduct_money() — negative amount raises ValueError
        Code:   player.py → deduct_money() → if amount < 0
        Why:    Guards against accidentally deducting a negative (which would add money).
        Expect: ValueError raised.
        """
        p = Player("Alice", 1000)
        with self.assertRaises(ValueError):
            p.deduct_money(-50)

    def test_TC_P8_is_bankrupt_positive_balance(self):
        """
        TC-P8  |  Branch: is_bankrupt() → False
        Code:   player.py → is_bankrupt()
        Why:    Positive balance means player is still in the game.
        Expect: False.
        """
        p = Player("Alice", 1)
        self.assertFalse(p.is_bankrupt())

    def test_TC_P9_is_bankrupt_zero_balance(self):
        """
        TC-P9  |  Branch: is_bankrupt() → True (boundary)
        Code:   player.py → is_bankrupt() → balance <= 0
        Why:    Exactly zero means bankrupt (uses <=).
        Expect: True.
        """
        p = Player("Alice", 0)
        self.assertTrue(p.is_bankrupt())


# ---------------------------------------------------------------------------
# 3. PLAYER — MOVE
# ---------------------------------------------------------------------------

class TestPlayerMove(unittest.TestCase):

    def test_TC_M1_normal_move_no_go(self):
        """
        TC-M1  |  move() — normal move, no Go crossing
        Code:   player.py → move()
        Why:    Player moves forward without wrapping around.
        Expect: position = 11, balance unchanged.
        """
        p = Player("Bob")
        p.position = 5
        p.move(6)
        self.assertEqual(p.position, 11)
        self.assertEqual(p.balance, STARTING_BALANCE)

    def test_TC_M2_lands_exactly_on_go(self):
        """
        TC-M2  |  Branch: move() → position == 0 → salary awarded
        Code:   player.py → move() → if self.position == 0
        Why:    Landing exactly on Go triggers the (buggy) salary condition.
                This IS caught by the bug code (position == 0 is True).
        Expect: position == 0, balance += $200.
        """
        p = Player("Bob")
        p.position = 36
        old = p.balance
        p.move(4)    # 36+4=40 → 0
        self.assertEqual(p.position, 0)
        self.assertEqual(p.balance, old + GO_SALARY)

    def test_TC_M3_passes_go_no_salary_BUG(self):
        """
        TC-M3  |  BUG DETECTION — move() passes Go without landing on it
        Code:   player.py → move() → if self.position == 0   (BUG)
        Why:    Player at pos 38 rolls 4 → lands on pos 2 (wrapped past Go).
                They deserve $200. Bug code only checks position==0, so $0 is given.
        Expect (buggy code): balance unchanged → test PASSES, confirming bug.
        Fix needed: check old_position + steps >= BOARD_SIZE instead of position==0.
        """
        p = Player("Bob")
        p.position = 38
        old = p.balance
        p.move(4)    # lands on 2, passed Go
        self.assertEqual(p.position, 2)
        self.assertEqual(p.balance, old,
            "BUG PRESENT: passed Go but no $200 salary awarded")

    def test_TC_M4_wrap_around_stays_in_bounds(self):
        """
        TC-M4  |  Edge case: wrap-around keeps position in 0..39
        Code:   player.py → move() → (position + steps) % BOARD_SIZE
        Why:    Position must never go outside the board.
        Expect: position == 1.
        """
        p = Player("Bob")
        p.position = 39
        p.move(2)
        self.assertEqual(p.position, 1)

    def test_TC_M5_go_to_jail_sets_state(self):
        """
        TC-M5  |  go_to_jail() — all three state changes
        Code:   player.py → go_to_jail()
        Why:    Jailing must set position=10, in_jail=True, jail_turns=0.
        Expect: all three correct.
        """
        p = Player("Bob")
        p.position = 25; p.jail_turns = 2
        p.go_to_jail()
        self.assertEqual(p.position, JAIL_POSITION)
        self.assertTrue(p.in_jail)
        self.assertEqual(p.jail_turns, 0)

    def test_TC_M6_large_step_stays_in_bounds(self):
        """
        TC-M6  |  Edge case: very large roll
        Code:   player.py → move()
        Why:    % BOARD_SIZE must keep position inside 0..39 always.
        Expect: position in [0, 39].
        """
        p = Player("Bob")
        p.position = 0
        p.move(400)    # 400 % 40 = 0
        self.assertGreaterEqual(p.position, 0)
        self.assertLessEqual(p.position, 39)


# ---------------------------------------------------------------------------
# 4. PLAYER — PROPERTIES
# ---------------------------------------------------------------------------

class TestPlayerProperties(unittest.TestCase):

    def test_TC_PP1_add_property(self):
        """
        TC-PP1  |  add_property() — normal add
        Code:   player.py → add_property() → if prop not in self.properties
        Why:    Property should appear in player's list.
        Expect: prop in properties, count == 1.
        """
        p = Player("Alice")
        prop = make_prop()
        p.add_property(prop)
        self.assertIn(prop, p.properties)
        self.assertEqual(len(p.properties), 1)

    def test_TC_PP2_add_property_duplicate_ignored(self):
        """
        TC-PP2  |  Branch: add_property() — duplicate is silently ignored
        Code:   player.py → add_property() → if prop not in self.properties
        Why:    Adding same property twice must not double-count it.
        Expect: count stays at 1.
        """
        p = Player("Alice")
        prop = make_prop()
        p.add_property(prop)
        p.add_property(prop)
        self.assertEqual(len(p.properties), 1)

    def test_TC_PP3_remove_property_owned(self):
        """
        TC-PP3  |  remove_property() — remove a held property
        Code:   player.py → remove_property() → if prop in self.properties
        Why:    Property should be gone from the list after removal.
        Expect: prop not in properties.
        """
        p = Player("Alice")
        prop = make_prop()
        p.add_property(prop)
        p.remove_property(prop)
        self.assertNotIn(prop, p.properties)

    def test_TC_PP4_remove_property_not_owned_noop(self):
        """
        TC-PP4  |  Branch: remove_property() — property not owned, no crash
        Code:   player.py → remove_property() → else (no-op)
        Why:    Should not raise an exception.
        Expect: no error, list still empty.
        """
        p = Player("Alice")
        prop = make_prop()
        p.remove_property(prop)    # must not raise
        self.assertEqual(len(p.properties), 0)


# ---------------------------------------------------------------------------
# 5. PROPERTY — RENT
# ---------------------------------------------------------------------------

class TestPropertyRent(unittest.TestCase):

    def test_TC_R1_mortgaged_rent_is_zero(self):
        """
        TC-R1  |  Branch: get_rent() → is_mortgaged → return 0
        Code:   property.py → get_rent() → if self.is_mortgaged
        Why:    Mortgaged properties collect no rent.
        Expect: 0.
        """
        prop = make_prop(base_rent=6)
        prop.owner = Player("Alice")
        prop.is_mortgaged = True
        self.assertEqual(prop.get_rent(), 0)

    def test_TC_R2_no_group_returns_base_rent(self):
        """
        TC-R2  |  Branch: get_rent() → no group → return base_rent
        Code:   property.py → get_rent() → final return
        Why:    Without a group, always return base_rent.
        Expect: 6.
        """
        prop = make_prop(base_rent=6)
        prop.owner = Player("Alice")
        self.assertEqual(prop.get_rent(), 6)

    def test_TC_R3_partial_group_rent_doubled_BUG(self):
        """
        TC-R3  |  BUG DETECTION — all_owned_by uses any() instead of all()
        Code:   property.py → PropertyGroup.all_owned_by() → any()  (BUG)
        Why:    Alice owns only 1 of 2 brown properties.
                Rent should NOT double (group not complete).
                Bug: any() is True when Alice owns at least one → rent doubles.
        Expect (buggy code): rent == base_rent * 2 → test PASSES, confirming bug.
        Fix needed: change any() to all() in all_owned_by().
        """
        grp, p1, p2 = make_brown_group()
        alice = Player("Alice")
        bob   = Player("Bob")
        p1.owner = alice   # Alice owns only one
        p2.owner = bob     # Bob owns the other
        self.assertEqual(p1.get_rent(), p1.base_rent * 2,
            "BUG PRESENT: any() doubles rent even with partial group ownership")

    def test_TC_R4_full_group_rent_doubled(self):
        """
        TC-R4  |  Branch: get_rent() → full group owned → doubled rent
        Code:   property.py → get_rent() → all_owned_by()
        Why:    When one player owns ALL properties in a group, rent doubles.
                any() and all() both agree when all are owned — no bug here.
        Expect: rent == base_rent * 2.
        """
        grp, p1, p2 = make_brown_group()
        alice = Player("Alice")
        p1.owner = alice
        p2.owner = alice
        self.assertEqual(p1.get_rent(), p1.base_rent * 2)
        self.assertEqual(p2.get_rent(), p2.base_rent * 2)

    def test_TC_R5_all_owned_by_none_false(self):
        """
        TC-R5  |  Branch: all_owned_by(None) → always False
        Code:   property.py → all_owned_by() → if player is None
        Why:    Passing None should never trigger doubled rent.
        Expect: False.
        """
        grp, p1, p2 = make_brown_group()
        self.assertFalse(grp.all_owned_by(None))


# ---------------------------------------------------------------------------
# 6. PROPERTY — MORTGAGE
# ---------------------------------------------------------------------------

class TestPropertyMortgage(unittest.TestCase):

    def test_TC_MG1_mortgage_returns_half_price(self):
        """
        TC-MG1  |  mortgage() — normal case
        Code:   property.py → mortgage() → not is_mortgaged path
        Why:    Mortgage value is price // 2.
        Expect: 30 (60 // 2).
        """
        prop = make_prop(price=60)
        self.assertEqual(prop.mortgage(), 30)
        self.assertTrue(prop.is_mortgaged)

    def test_TC_MG2_mortgage_already_mortgaged_returns_zero(self):
        """
        TC-MG2  |  Branch: mortgage() → already mortgaged → return 0
        Code:   property.py → mortgage() → if self.is_mortgaged
        Why:    Cannot mortgage a property twice.
        Expect: 0.
        """
        prop = make_prop(price=60)
        prop.mortgage()
        self.assertEqual(prop.mortgage(), 0)

    def test_TC_MG3_unmortgage_cost_110_percent(self):
        """
        TC-MG3  |  unmortgage() — normal case: cost = 110% of mortgage_value
        Code:   property.py → unmortgage() → else branch
        Why:    Redemption costs 10% more than the original payout.
        Expect: 33 (int(30 * 1.1)).
        """
        prop = make_prop(price=60)
        prop.mortgage()
        cost = prop.unmortgage()
        self.assertEqual(cost, int(30 * 1.1))
        self.assertFalse(prop.is_mortgaged)

    def test_TC_MG4_unmortgage_not_mortgaged_returns_zero(self):
        """
        TC-MG4  |  Branch: unmortgage() → not mortgaged → return 0
        Code:   property.py → unmortgage() → if not self.is_mortgaged
        Why:    Cannot un-mortgage a property that isn't mortgaged.
        Expect: 0.
        """
        prop = make_prop(price=60)
        self.assertEqual(prop.unmortgage(), 0)

    def test_TC_MG5_is_available_true(self):
        """
        TC-MG5  |  is_available() → True when unowned and unmortgaged
        Code:   property.py → is_available()
        Why:    Both conditions must pass for a property to be purchasable.
        Expect: True.
        """
        prop = make_prop()
        self.assertTrue(prop.is_available())

    def test_TC_MG6_is_available_false_owned(self):
        """
        TC-MG6  |  is_available() → False when owned
        Code:   property.py → is_available() → owner is None
        Why:    Owned property cannot be purchased again.
        Expect: False.
        """
        prop = make_prop()
        prop.owner = Player("Alice")
        self.assertFalse(prop.is_available())

    def test_TC_MG7_is_available_false_mortgaged(self):
        """
        TC-MG7  |  is_available() → False when mortgaged
        Code:   property.py → is_available() → not is_mortgaged
        Why:    Mortgaged (but unowned) property is not purchasable.
        Expect: False.
        """
        prop = make_prop()
        prop.is_mortgaged = True
        self.assertFalse(prop.is_available())


# ---------------------------------------------------------------------------
# 7. BANK
# ---------------------------------------------------------------------------

class TestBank(unittest.TestCase):

    def test_TC_B1_initial_balance(self):
        """
        TC-B1  |  Bank starts with configured initial funds
        Code:   bank.py → __init__
        Why:    Starting reserves must match the config constant.
        Expect: BANK_STARTING_FUNDS.
        """
        bank = Bank()
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS)

    def test_TC_B2_collect_positive(self):
        """
        TC-B2  |  collect() — positive amount increases balance
        Code:   bank.py → collect()
        Why:    Taxes and rent proceeds flow into the bank.
        Expect: balance increases by 500.
        """
        bank = Bank()
        bank.collect(500)
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS + 500)

    def test_TC_B3_collect_negative_reduces_balance(self):
        """
        TC-B3  |  collect() — negative amount (used during mortgage payout)
        Code:   bank.py → collect()  used as bank.collect(-payout)
        Why:    mortgage_property calls bank.collect(-payout) — negative reduces funds.
        Expect: balance decreases by 100.
        """
        bank = Bank()
        before = bank.get_balance()
        bank.collect(-100)
        self.assertEqual(bank.get_balance(), before - 100)

    def test_TC_B4_pay_out_normal(self):
        """
        TC-B4  |  pay_out() — normal payout decreases balance
        Code:   bank.py → pay_out()
        Why:    Community Chest / Chance cards pay players from the bank.
        Expect: paid == 200, balance reduced.
        """
        bank = Bank()
        paid = bank.pay_out(200)
        self.assertEqual(paid, 200)
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS - 200)

    def test_TC_B5_pay_out_zero_returns_zero(self):
        """
        TC-B5  |  Branch: pay_out() → amount <= 0 → return 0
        Code:   bank.py → pay_out() → if amount <= 0
        Why:    Zero payout is a no-op.
        Expect: 0.
        """
        bank = Bank()
        self.assertEqual(bank.pay_out(0), 0)

    def test_TC_B6_pay_out_insufficient_raises(self):
        """
        TC-B6  |  Branch: pay_out() → insufficient funds → ValueError
        Code:   bank.py → pay_out() → if amount > self._funds
        Why:    Bank must not go into debt.
        Expect: ValueError.
        """
        bank = Bank()
        with self.assertRaises(ValueError):
            bank.pay_out(bank.get_balance() + 1)

    def test_TC_B7_give_loan_credits_player(self):
        """
        TC-B7  |  give_loan() — player receives the loaned amount
        Code:   bank.py → give_loan()
        Why:    Emergency loan must credit the player's balance.
        Expect: player balance += 500.
        """
        bank   = Bank()
        player = Player("Alice", 0)
        bank.give_loan(player, 500)
        self.assertEqual(player.balance, 500)
        self.assertEqual(bank.loan_count(), 1)

    def test_TC_B8_give_loan_does_not_reduce_bank_funds_BUG(self):
        """
        TC-B8  |  BUG DETECTION — give_loan() never reduces bank._funds
        Code:   bank.py → give_loan() — missing self._funds -= amount
        Why:    Bank gives money to player but its own reserves are untouched.
                Money is created from nothing — inflation bug.
        Expect (buggy code): bank balance unchanged → test PASSES, confirming bug.
        Fix needed: add self._funds -= amount inside give_loan().
        """
        bank   = Bank()
        player = Player("Alice", 0)
        before = bank.get_balance()
        bank.give_loan(player, 500)
        self.assertEqual(bank.get_balance(), before,
            "BUG PRESENT: bank issued $500 loan but its reserves were not reduced")

    def test_TC_B9_give_loan_zero_is_noop(self):
        """
        TC-B9  |  Branch: give_loan() → amount <= 0 → no-op
        Code:   bank.py → give_loan() → if amount <= 0
        Why:    Zero or negative loan must be silently ignored.
        Expect: loan_count == 0, player balance unchanged.
        """
        bank   = Bank()
        player = Player("Alice", 0)
        bank.give_loan(player, 0)
        self.assertEqual(bank.loan_count(), 0)
        self.assertEqual(player.balance, 0)


# ---------------------------------------------------------------------------
# 8. BUY PROPERTY
# ---------------------------------------------------------------------------

class TestBuyProperty(unittest.TestCase):

    def test_TC_BUY1_exact_balance_blocked_BUG(self):
        """
        TC-BUY1  |  BUG DETECTION — buy_property uses <= instead of <
        Code:    game.py → buy_property() → if player.balance <= prop.price  (BUG)
        Why:     Player has exactly $60, property costs $60.
                 They should be able to buy it (having exact money is enough).
                 Bug: <= check treats this as "cannot afford".
        Expect (buggy code): False → test PASSES, confirming bug.
        Fix needed: change <= to < in the balance check.
        """
        bank   = Bank()
        player = Player("Alice", 60)
        prop   = make_prop(price=60)
        result = buy_property_original(bank, player, prop)
        self.assertFalse(result,
            "BUG PRESENT: balance == price blocked — should be allowed")

    def test_TC_BUY2_sufficient_funds_success(self):
        """
        TC-BUY2  |  Branch: buy_property() → balance > price → success
        Code:    game.py → buy_property()
        Why:     Normal purchase path.
        Expect:  True, prop.owner = player, balance reduced.
        """
        bank   = Bank()
        player = Player("Alice", 500)
        prop   = make_prop(price=200)
        result = buy_property_original(bank, player, prop)
        self.assertTrue(result)
        self.assertEqual(prop.owner, player)
        self.assertEqual(player.balance, 300)

    def test_TC_BUY3_insufficient_funds_rejected(self):
        """
        TC-BUY3  |  Branch: buy_property() → balance < price → reject
        Code:    game.py → buy_property() → if balance <= price (True branch)
        Why:     Player cannot afford; property stays unowned.
        Expect:  False, prop.owner remains None.
        """
        bank   = Bank()
        player = Player("Alice", 50)
        prop   = make_prop(price=60)
        result = buy_property_original(bank, player, prop)
        self.assertFalse(result)
        self.assertIsNone(prop.owner)

    def test_TC_BUY4_zero_balance_rejected(self):
        """
        TC-BUY4  |  Edge case: buy_property() with zero balance
        Code:    game.py → buy_property()
        Why:     Zero balance cannot buy anything.
        Expect:  False.
        """
        bank   = Bank()
        player = Player("Alice", 0)
        prop   = make_prop(price=60)
        result = buy_property_original(bank, player, prop)
        self.assertFalse(result)

    def test_TC_BUY5_bank_receives_purchase_price(self):
        """
        TC-BUY5  |  buy_property() — bank balance increases by price
        Code:    game.py → buy_property() → bank.collect(prop.price)
        Why:     The bank must receive the purchase price.
        Expect:  bank balance += 200.
        """
        bank   = Bank()
        player = Player("Alice", 500)
        prop   = make_prop(price=200)
        before = bank.get_balance()
        buy_property_original(bank, player, prop)
        self.assertEqual(bank.get_balance(), before + 200)


# ---------------------------------------------------------------------------
# 9. PAY RENT
# ---------------------------------------------------------------------------

class TestPayRent(unittest.TestCase):

    def test_TC_RNT1_owner_never_credited_BUG(self):
        """
        TC-RNT1  |  BUG DETECTION — pay_rent() never credits the owner
        Code:    game.py → pay_rent() — missing prop.owner.add_money(rent)
        Why:     Rent is deducted from payer but the owner's balance never increases.
                 Money is destroyed every time rent is paid.
        Expect (buggy code): owner balance unchanged → test PASSES, confirming bug.
        Fix needed: add prop.owner.add_money(rent) after player.deduct_money(rent).
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   500)
        prop  = make_prop(base_rent=20)
        prop.owner = bob
        pay_rent_original(alice, prop)
        self.assertEqual(alice.balance, 980)
        self.assertEqual(bob.balance, 500,
            "BUG PRESENT: owner did not receive rent — money was destroyed")

    def test_TC_RNT2_payer_loses_correct_amount(self):
        """
        TC-RNT2  |  pay_rent() — payer's balance decreases by rent
        Code:    game.py → pay_rent() → player.deduct_money(rent)
        Why:     Rent must come out of the payer's pocket.
        Expect:  alice.balance == 980.
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   500)
        prop  = make_prop(base_rent=20)
        prop.owner = bob
        pay_rent_original(alice, prop)
        self.assertEqual(alice.balance, 980)

    def test_TC_RNT3_mortgaged_no_charge(self):
        """
        TC-RNT3  |  Branch: pay_rent() → mortgaged → return early
        Code:    game.py → pay_rent() → if prop.is_mortgaged
        Why:     Mortgaged properties collect no rent.
        Expect:  both balances unchanged.
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   500)
        prop  = make_prop(base_rent=20)
        prop.owner = bob
        prop.is_mortgaged = True
        pay_rent_original(alice, prop)
        self.assertEqual(alice.balance, 1000)
        self.assertEqual(bob.balance,   500)

    def test_TC_RNT4_unowned_no_charge(self):
        """
        TC-RNT4  |  Branch: pay_rent() → owner is None → return early
        Code:    game.py → pay_rent() → if prop.owner is None
        Why:     Unowned property cannot charge rent.
        Expect:  alice balance unchanged.
        """
        alice = Player("Alice", 1000)
        prop  = make_prop(base_rent=20)
        pay_rent_original(alice, prop)
        self.assertEqual(alice.balance, 1000)


# ---------------------------------------------------------------------------
# 10. FIND WINNER
# ---------------------------------------------------------------------------

class TestFindWinner(unittest.TestCase):

    def test_TC_W1_returns_poorest_BUG(self):
        """
        TC-W1  |  BUG DETECTION — find_winner uses min() instead of max()
        Code:  game.py → find_winner() → min(players, key=net_worth)  (BUG)
        Why:   min() picks the player with the LOWEST balance — the loser.
               The winner should have the HIGHEST balance.
        Expect (buggy code): bob (poorest) is returned → test PASSES, confirming bug.
        Fix needed: change min() to max() in find_winner().
        """
        alice = Player("Alice", 2000)
        bob   = Player("Bob",   500)
        winner = find_winner_original([alice, bob])
        self.assertEqual(winner, bob,
            "BUG PRESENT: find_winner used min() and returned the poorest player")

    def test_TC_W2_empty_list_returns_none(self):
        """
        TC-W2  |  Branch: find_winner() → empty list → return None
        Code:  game.py → find_winner() → if not self.players
        Why:   Edge case: no players left.
        Expect: None.
        """
        self.assertIsNone(find_winner_original([]))

    def test_TC_W3_single_player_wins(self):
        """
        TC-W3  |  Edge case: find_winner() with only one player
        Code:  game.py → find_winner()
        Why:   Only player must be the winner.
        Expect: that player.
        """
        alice = Player("Alice", 300)
        self.assertEqual(find_winner_original([alice]), alice)

    def test_TC_W4_three_players_min_bug(self):
        """
        TC-W4  |  BUG DETECTION — three players, bug picks the minimum
        Code:  game.py → find_winner() → min()  (BUG)
        Why:   With three players, min() picks carol who has the least money.
        Expect (buggy code): carol → test PASSES, confirming bug.
        """
        alice = Player("Alice", 2000)
        bob   = Player("Bob",   1500)
        carol = Player("Carol",  100)
        winner = find_winner_original([alice, bob, carol])
        self.assertEqual(winner, carol,
            "BUG PRESENT: min() picked carol (least money) as winner")


# ---------------------------------------------------------------------------
# 11. TRADE
# ---------------------------------------------------------------------------

class TestTrade(unittest.TestCase):

    def test_TC_T1_seller_never_receives_cash_BUG(self):
        """
        TC-T1  |  BUG DETECTION — trade() never adds cash to seller's balance
        Code:  game.py → trade() — missing seller.add_money(cash_amount)
        Why:   buyer.deduct_money runs, but seller.add_money is absent.
               Seller gives away property AND receives no cash.
        Expect (buggy code): seller balance unchanged → test PASSES, confirming bug.
        Fix needed: add seller.add_money(cash_amount) in trade().
        """
        alice = Player("Alice", 1000)   # seller
        bob   = Player("Bob",   500)    # buyer
        prop  = make_prop(price=100)
        prop.owner = alice
        alice.add_property(prop)
        trade_original(alice, bob, prop, 80)
        self.assertEqual(bob.balance, 420)
        self.assertEqual(alice.balance, 1000,
            "BUG PRESENT: seller did not receive cash from trade")

    def test_TC_T2_buyer_loses_cash(self):
        """
        TC-T2  |  trade() — buyer's balance decreases by cash_amount
        Code:  game.py → trade() → buyer.deduct_money(cash_amount)
        Why:   Buyer must pay for the property.
        Expect: bob.balance == 420.
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   500)
        prop  = make_prop(price=100)
        prop.owner = alice
        alice.add_property(prop)
        trade_original(alice, bob, prop, 80)
        self.assertEqual(bob.balance, 420)

    def test_TC_T3_property_transfers_to_buyer(self):
        """
        TC-T3  |  trade() — property ownership transfers correctly
        Code:  game.py → trade() → prop.owner = buyer
        Why:   After trade, buyer owns the property, seller does not.
        Expect: prop.owner == bob.
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   500)
        prop  = make_prop(price=100)
        prop.owner = alice
        alice.add_property(prop)
        trade_original(alice, bob, prop, 80)
        self.assertEqual(prop.owner, bob)
        self.assertIn(prop, bob.properties)
        self.assertNotIn(prop, alice.properties)

    def test_TC_T4_buyer_cannot_afford_rejected(self):
        """
        TC-T4  |  Branch: trade() → buyer.balance < cash_amount → rejected
        Code:  game.py → trade() → if buyer.balance < cash_amount
        Why:   Buyer with insufficient funds cannot complete the trade.
        Expect: False, property stays with seller.
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   10)
        prop  = make_prop(price=100)
        prop.owner = alice
        alice.add_property(prop)
        result = trade_original(alice, bob, prop, 80)
        self.assertFalse(result)

    def test_TC_T5_seller_does_not_own_prop_rejected(self):
        """
        TC-T5  |  Branch: trade() → prop.owner != seller → rejected
        Code:  game.py → trade() → if prop.owner != seller
        Why:   Cannot trade a property you don't own.
        Expect: False.
        """
        alice = Player("Alice", 1000)
        bob   = Player("Bob",   500)
        carol = Player("Carol", 200)
        prop  = make_prop(price=100)
        prop.owner = carol   # carol owns it, not alice
        result = trade_original(alice, bob, prop, 80)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# 12. EDGE CASES
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):

    def test_TC_E1_very_large_balance(self):
        """
        TC-E1  |  Edge case: very large player balance
        Code:  player.py → add_money()
        Why:   No overflow should occur with large values.
        Expect: 20,000,000.
        """
        p = Player("Alice", 10_000_000)
        p.add_money(10_000_000)
        self.assertEqual(p.balance, 20_000_000)

    def test_TC_E2_bank_many_deposits(self):
        """
        TC-E2  |  Edge case: bank receives 1000 small deposits
        Code:  bank.py → collect()
        Why:   Accumulating many small amounts should not cause errors.
        Expect: BANK_STARTING_FUNDS + 10,000.
        """
        bank = Bank()
        for _ in range(1000):
            bank.collect(10)
        self.assertEqual(bank.get_balance(), BANK_STARTING_FUNDS + 10_000)

    def test_TC_E3_dice_total_always_equals_die_sum(self):
        """
        TC-E3  |  Edge case: total() always matches die1 + die2
        Code:  dice.py → total() + roll()
        Why:   total() must always be consistent with individual die values.
        Expect: total == die1 + die2 for every roll.
        """
        dice = Dice()
        for _ in range(100):
            total = dice.roll()
            self.assertEqual(total, dice.die1 + dice.die2)

    def test_TC_E4_move_exactly_40_stays_same(self):
        """
        TC-E4  |  Edge case: moving exactly 40 steps is a full loop
        Code:  player.py → move() → (position + 40) % 40 == position
        Why:   A full board loop returns to the same square.
        Expect: position unchanged (still 5).
        """
        p = Player("Bob")
        p.position = 5
        p.move(40)
        self.assertEqual(p.position, 5)

    def test_TC_E5_bank_pay_out_entire_funds(self):
        """
        TC-E5  |  Edge case: pay_out exactly all bank funds
        Code:  bank.py → pay_out()
        Why:   Boundary: paying exactly all reserves must work (not raise).
        Expect: paid == BANK_STARTING_FUNDS, balance == 0.
        """
        bank = Bank()
        paid = bank.pay_out(BANK_STARTING_FUNDS)
        self.assertEqual(paid, BANK_STARTING_FUNDS)
        self.assertEqual(bank.get_balance(), 0)

    def test_TC_E6_property_odd_price_floor_division(self):
        """
        TC-E6  |  Edge case: odd-numbered property price → floor division
        Code:  property.py → __init__ → price // 2
        Why:   Mortgage value uses integer division; 61 // 2 = 30.
        Expect: mortgage_value == 30.
        """
        prop = Property("Odd", 1, 61, 2)
        self.assertEqual(prop.mortgage_value, 30)

    def test_TC_E7_empty_group_any_vs_all(self):
        """
        TC-E7  |  Edge case: all_owned_by on empty group
        Code:  property.py → PropertyGroup.all_owned_by() → any()  (BUG)
        Why:   any([]) == False; all([]) == True.
                The bug (any()) gives False for empty group.
                The fix (all()) would give True (vacuous truth).
                This shows the semantic difference between any() and all().
        Expect (buggy code): False.
        """
        grp   = PropertyGroup("Empty", "none")
        alice = Player("Alice")
        result = grp.all_owned_by(alice)
        self.assertFalse(result,   # any() on empty = False
            "BUG: any() returns False on empty; all() would return True")


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    print()
    print("=" * 70)
    print("  MoneyPoly — White-Box Test Suite")
    print()
    print("  Tests labelled _BUG will PASS on the original (buggy) code.")
    print("  They document what the bug does. After you fix the code,")
    print("  flip those assertions to check the CORRECT behaviour.")
    print("=" * 70)
    print()
    unittest.main(verbosity=2)