# DASS Assignment 2 Submission

This repository contains my solutions for all three questions in Assignment 2.  
I have organized the work question-wise (`q1`, `q2`, `q3`) and attached the corresponding reports in each folder.

## Submission Structure

- `q1/moneypoly/` - Question 1 (Money-Poly game + white-box testing)
- `q2/` - Question 2 (StreetRace Manager system)
- `q3/tests/` - Question 3 (QuickCart black-box API test suite)
- `Diagrams/` - supporting diagrams (if required by evaluator)

---

## Q1 - Money-Poly (White-Box Focus)

### What I implemented

- A terminal-based Monopoly-style game flow with:
  - board movement and turn rotation
  - dice and doubles handling
  - jail logic (fine/card/mandatory release flow)
  - property purchase, rent, mortgage/unmortgage, and auction flow
  - chance/community chest card handling
  - bankruptcy checks and winner logic integration
- Modular design inside `moneypoly/` package:
  - `game.py`, `player.py`, `bank.py`, `dice.py`, `board.py`, `property.py`, `cards.py`, `ui.py`
- White-box tests added to validate branch and edge behavior.

### Run (Q1)

From repository root:

```bash
cd q1/moneypoly
python main.py
```

### Test (Q1)

```bash
cd q1/moneypoly
python -m pytest test_whitebox.py -v
```

There is also an internal white-box suite in `q1/moneypoly/moneypoly/test_whitebox.py`.

### Report

- `q1/moneypoly/MoneyPoly_WhiteBox_Report.pdf`

---

## Q2 - StreetRace Manager

### What I implemented

Built a menu-driven, modular management system where all modules share state through `data_store.py`.

Core modules:
- `registration.py` - crew registration and validation
- `crew_management.py` - role updates, skill levels, availability
- `inventory.py` - vehicles, spare parts, and cash balance
- `race_management.py` - race creation, participant validation, race start
- `results.py` - race result recording, prize handling, release of resources

Additional modules:
- `mission_planning.py` - mission creation, required-role checks, crew assignment
- `leaderboard.py` - points/wins/podium tracking and ranking display
- `maintenance.py` - mechanic availability, repair scheduling, job completion/cancel

### Run (Q2)

```bash
cd q2
python main.py
```

### Test (Q2)

```bash
cd q2
python full_test.py
```

### Report

- `q2/StreetRace_Report.pdf`

---

## Q3 - QuickCart API Black-Box Testing

### What I implemented

- Wrote a black-box test suite using `pytest` + `requests` for QuickCart endpoints.
- Covered major API areas:
  - header/auth validation
  - profile updates and input constraints
  - address creation/validation
  - product/cart/checkout flows
  - loyalty/wallet checks
  - coupons, reviews, invoice behavior
- Included explicit bug-confirmation test cases with bug IDs (documented in test file/report).

### Prerequisites (Q3)

- QuickCart API server running at `http://localhost:8080`
- Python packages:

```bash
pip install pytest requests
```

- Update these values in `q3/tests/test_quickcart.py` before running:
  - `ROLL_NUMBER`
  - `USER_ID`

### Run (Q3)

```bash
cd q3/tests
pytest test_quickcart.py -v
```

### Report

- `q3/QuickCart_BlackBox_Test_Report.pdf`

---
Github repo link - https://github.com/anagha2312/Dass_Assignment_2

gdrive link- https://drive.google.com/file/d/1h3v89rnhygj2Ot8fTndhrasgrdWyBmtR/view?usp=sharing

gdrive link again- https://drive.google.com/file/d/1h3v89rnhygj2Ot8fTndhrasgrdWyBmtR/view?usp=sharing

.git link - https://github.com/anagha2312/Dass_Assignment_2.git
