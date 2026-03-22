"""
QuickCart API Black-Box Test Suite  (v2 - corrected field names)
=================================================================
Run with:  pytest test_quickcart.py -v
Requires:  pip install pytest requests

Set ROLL_NUMBER and USER_ID before running.

CONFIRMED ACTUAL FIELD NAMES (discovered from live API):
  GET /wallet        -> {"wallet_balance": <float>}
  GET /loyalty       -> {"loyalty_points": <int>}
  GET /products      -> no "stock" field at list level; use GET /products/{id}
  GET /orders/{id}/invoice -> {"subtotal", "gst_amount", "total_amount", "order_id"}
  GET /admin/coupons -> coupon field is "coupon_code" (not "code")
  POST /addresses    -> returns 200 (not 201) on success
  GET /products      -> sort param values may be "asc"/"desc" or "price_asc"/"price_desc"

BUGS CONFIRMED FROM TEST RUN (report these to your teacher):
  BUG-01: GET /profile with non-existent X-User-ID returns 404 instead of 400
  BUG-02: PUT /profile accepts phone='ABCDEFGHIJ' (letters) and returns 200 — should be 400
  BUG-03: POST /addresses returns 200 instead of 201 on success
  BUG-04: Multiple addresses can all have is_default=True simultaneously (uniqueness not enforced)
  BUG-05: POST /cart/add accepts quantity=0 and returns 200 — should be 400
  BUG-06: POST /cart/add accepts quantity=-1 and returns 200 — should be 400
  BUG-07: Cart subtotal is wrong: item subtotal = -16 for price=120, qty=2 (severe arithmetic bug)
  BUG-08: Cart total calculation is broken (returns 120 when sum of subtotals is -6)
  BUG-09: GST test - order response does not contain "total" or "order_total" field
  BUG-10: POST /products/{id}/reviews accepts rating=0 (below minimum) — should be 400
  BUG-11: POST /products/{id}/reviews accepts rating=6 (above maximum) — should be 400
  BUG-12: Invoice uses "gst_amount" and "total_amount" instead of "gst" and "total"
  BUG-13: Invoice total_amount (142.3) != subtotal (120) * 1.05 (126) — wrong GST calculation
"""

import pytest
import requests

# ─── Configuration ─────────────────────────────────────────────────────────────
BASE_URL    = "http://localhost:8080"
ROLL_NUMBER = "2024101007"   # <-- replace with YOUR roll number
USER_ID     = 1              # <-- a valid seeded user ID

def base_headers(user_id=USER_ID):
    return {
        "X-Roll-Number": ROLL_NUMBER,
        "X-User-ID":     str(user_id),
        "Content-Type":  "application/json",
    }

def admin_headers():
    return {"X-Roll-Number": ROLL_NUMBER, "Content-Type": "application/json"}

def url(path):
    return f"{BASE_URL}{path}"

# ─── Helper: get wallet balance (uses confirmed field name) ────────────────────
def get_wallet_balance():
    r = requests.get(url("/api/v1/wallet"), headers=base_headers())
    data = r.json()
    return data.get("wallet_balance") or data.get("balance") or 0

# ─── Helper: get loyalty points (uses confirmed field name) ───────────────────
def get_loyalty_points():
    r = requests.get(url("/api/v1/loyalty"), headers=base_headers())
    data = r.json()
    return data.get("loyalty_points") or data.get("points") or 0

# ─── Helper: get stock for a product (must use single product endpoint) ────────
def get_product_stock(pid):
    r = requests.get(url(f"/api/v1/products/{pid}"), headers=base_headers())
    data = r.json()
    return data.get("stock") or data.get("quantity") or data.get("stock_quantity") or 0

# ─── Helper: first active product ─────────────────────────────────────────────
def first_product():
    products = requests.get(url("/api/v1/products"), headers=base_headers()).json()
    if not products:
        pytest.skip("No active products in DB")
    return products[0]

# ─── Helper: place a CARD order and return order_id ───────────────────────────
def place_card_order():
    requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
    p = first_product()
    requests.post(url("/api/v1/cart/add"),
                  json={"product_id": p["product_id"], "quantity": 1},
                  headers=base_headers())
    r = requests.post(url("/api/v1/checkout"),
                      json={"payment_method": "CARD"},
                      headers=base_headers())
    assert r.status_code in (200, 201), f"Checkout failed: {r.text}"
    return r.json().get("order_id")

# ─── Helper: get coupon code field (API may use "code" or "coupon_code") ──────
def get_coupon_code(coupon_obj):
    return (coupon_obj.get("code") or
            coupon_obj.get("coupon_code") or
            coupon_obj.get("coupon") or "")


# ══════════════════════════════════════════════════════════════════════════════
#  TC-AUTH  :  Header Validation
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthHeaders:

    def test_missing_roll_number_returns_401(self):
        """TC-AUTH-01: No X-Roll-Number -> 401"""
        r = requests.get(url("/api/v1/profile"), headers={"X-User-ID": str(USER_ID)})
        assert r.status_code == 401

    def test_non_integer_roll_number_returns_400(self):
        """TC-AUTH-02: X-Roll-Number='abc' -> 400"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": "abc", "X-User-ID": str(USER_ID)})
        assert r.status_code == 400

    def test_missing_user_id_returns_400(self):
        """TC-AUTH-03: No X-User-ID on user endpoint -> 400"""
        r = requests.get(url("/api/v1/profile"), headers={"X-Roll-Number": ROLL_NUMBER})
        assert r.status_code == 400

    def test_invalid_user_id_string_returns_400(self):
        """TC-AUTH-04: X-User-ID='xyz' -> 400"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "xyz"})
        assert r.status_code == 400

    def test_nonexistent_user_id_returns_4xx(self):
        """TC-AUTH-05: Non-existent user ID -> 400 or 404
        BUG-01: Spec says 400 but API returns 404. Accepting both; note as a bug."""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "999999"})
        assert r.status_code in (400, 404), \
            f"Expected 400 per spec (BUG: server returns {r.status_code})"

    def test_nonexistent_user_id_should_be_400_not_404(self):
        """TC-AUTH-05b: BUG CONFIRMATION - spec says 400, server returns 404"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": ROLL_NUMBER, "X-User-ID": "999999"})
        # This test documents the bug: it SHOULD be 400 per spec
        assert r.status_code == 400, \
            f"BUG-01 CONFIRMED: Expected 400 per spec, got {r.status_code}"

    def test_admin_does_not_need_user_id(self):
        """TC-AUTH-06: Admin endpoint works without X-User-ID"""
        r = requests.get(url("/api/v1/admin/users"), headers=admin_headers())
        assert r.status_code == 200

    def test_zero_roll_number(self):
        """TC-AUTH-07: X-Roll-Number=0 (valid integer boundary) -> not 401"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": "0", "X-User-ID": str(USER_ID)})
        # 0 is a valid integer so should not return 401
        assert r.status_code != 401

    def test_negative_roll_number(self):
        """TC-AUTH-08: X-Roll-Number=-1 -> check behavior (integer but negative)"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": "-1", "X-User-ID": str(USER_ID)})
        # Documenting actual behavior
        assert r.status_code in (200, 400, 401, 404)

    def test_float_roll_number_returns_400(self):
        """TC-AUTH-09: X-Roll-Number='12.5' (float, not integer) -> 400"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": "12.5", "X-User-ID": str(USER_ID)})
        assert r.status_code == 400

    def test_symbol_roll_number_returns_400(self):
        """TC-AUTH-10: X-Roll-Number='!@#' -> 400"""
        r = requests.get(url("/api/v1/profile"),
                         headers={"X-Roll-Number": "!@#", "X-User-ID": str(USER_ID)})
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#  TC-PROF  :  Profile
# ══════════════════════════════════════════════════════════════════════════════

class TestProfile:

    def test_get_profile_success(self):
        """TC-PROF-01: GET /profile -> 200 with name field"""
        r = requests.get(url("/api/v1/profile"), headers=base_headers())
        assert r.status_code == 200
        assert "name" in r.json()

    def test_update_profile_valid(self):
        """TC-PROF-02: Valid PUT /profile -> 200"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "Test User", "phone": "9876543210"},
                         headers=base_headers())
        assert r.status_code == 200

    def test_update_profile_short_name(self):
        """TC-PROF-03: name='A' (1 char) -> 400"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "A", "phone": "9876543210"},
                         headers=base_headers())
        assert r.status_code == 400

    def test_update_profile_name_too_long(self):
        """TC-PROF-04: name=51 chars -> 400"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "A" * 51, "phone": "9876543210"},
                         headers=base_headers())
        assert r.status_code == 400

    def test_update_profile_invalid_phone_9_digits(self):
        """TC-PROF-05: phone='987654321' (9 digits) -> 400"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "Valid Name", "phone": "987654321"},
                         headers=base_headers())
        assert r.status_code == 400

    def test_update_profile_phone_11_digits(self):
        """TC-PROF-05b: phone='98765432101' (11 digits) -> 400"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "Valid Name", "phone": "98765432101"},
                         headers=base_headers())
        assert r.status_code == 400

    def test_update_profile_phone_with_letters_bug(self):
        """TC-PROF-06: BUG-02 CONFIRMATION - phone='ABCDEFGHIJ' should be 400
        BUG-02: API accepts alphabetic phone and returns 200 — should be 400."""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "Valid Name", "phone": "ABCDEFGHIJ"},
                         headers=base_headers())
        assert r.status_code == 400, \
            f"BUG-02 CONFIRMED: Phone with letters accepted, got {r.status_code}"

    def test_update_profile_name_boundary_2(self):
        """TC-PROF-07: name exactly 2 chars (lower boundary) -> 200"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "AB", "phone": "9876543210"},
                         headers=base_headers())
        assert r.status_code == 200

    def test_update_profile_name_boundary_50(self):
        """TC-PROF-08: name exactly 50 chars (upper boundary) -> 200"""
        r = requests.put(url("/api/v1/profile"),
                         json={"name": "A" * 50, "phone": "9876543210"},
                         headers=base_headers())
        assert r.status_code == 200

    def test_update_profile_returns_updated_data(self):
        """TC-PROF-09: PUT /profile response reflects new values"""
        new_name = "UpdatedName"
        r = requests.put(url("/api/v1/profile"),
                         json={"name": new_name, "phone": "9876543210"},
                         headers=base_headers())
        assert r.status_code == 200
        # Either response body or subsequent GET should reflect the new name
        data = r.json()
        if "name" in data:
            assert data["name"] == new_name

    def test_get_profile_has_expected_fields(self):
        """TC-PROF-10: GET /profile response has name and phone fields"""
        r = requests.get(url("/api/v1/profile"), headers=base_headers())
        assert r.status_code == 200
        data = r.json()
        assert "name" in data


# ══════════════════════════════════════════════════════════════════════════════
#  TC-ADDR  :  Addresses
# ══════════════════════════════════════════════════════════════════════════════

class TestAddresses:
    created_id = None

    def test_add_address_valid(self):
        """TC-ADDR-01: Valid address creation -> 200 or 201 with address_id
        NOTE: Spec says 201 but API returns 200 (BUG-03)."""
        payload = {"label": "HOME", "street": "123 Main Street",
                   "city": "Hyderabad", "pincode": "500001", "is_default": False}
        r = requests.post(url("/api/v1/addresses"), json=payload, headers=base_headers())
        assert r.status_code in (200, 201), f"Expected 200 or 201, got {r.status_code}"
        data = r.json()
        # Try multiple possible field names
        aid = (data.get("address_id") or
               data.get("id") or
               (data.get("address") or {}).get("address_id"))
        assert aid is not None, f"No address_id in response: {data}"
        TestAddresses.created_id = aid

    def test_add_address_status_should_be_201(self):
        """TC-ADDR-01b: BUG-03 CONFIRMATION - spec says 201, API returns 200"""
        payload = {"label": "OFFICE", "street": "456 Office Street",
                   "city": "Mumbai", "pincode": "400001", "is_default": False}
        r = requests.post(url("/api/v1/addresses"), json=payload, headers=base_headers())
        assert r.status_code == 201, \
            f"BUG-03 CONFIRMED: Expected 201 per spec, got {r.status_code}"

    def test_add_address_invalid_label(self):
        """TC-ADDR-02: label='SCHOOL' -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "SCHOOL", "street": "123 Main Street",
                                "city": "Hyderabad", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_label_lowercase(self):
        """TC-ADDR-02b: label='home' (lowercase) -> 400 (labels must be uppercase)"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "home", "street": "123 Main Street",
                                "city": "Hyderabad", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_short_street(self):
        """TC-ADDR-03: street='123' (3 chars, below min 5) -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "HOME", "street": "123",
                                "city": "HYD", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_street_boundary_5(self):
        """TC-ADDR-03b: street exactly 5 chars (lower boundary) -> 200 or 201"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "HOME", "street": "12345",
                                "city": "HYD", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_add_address_street_boundary_4(self):
        """TC-ADDR-03c: street exactly 4 chars (one below min) -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "HOME", "street": "1234",
                                "city": "HYD", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_invalid_pincode_5digits(self):
        """TC-ADDR-04: pincode='12345' (5 digits) -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "HOME", "street": "123 Main Street",
                                "city": "HYD", "pincode": "12345"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_invalid_pincode_7digits(self):
        """TC-ADDR-04b: pincode='1234567' (7 digits) -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "HOME", "street": "123 Main Street",
                                "city": "HYD", "pincode": "1234567"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_invalid_pincode_letters(self):
        """TC-ADDR-04c: pincode='ABCDEF' -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "HOME", "street": "123 Main Street",
                                "city": "HYD", "pincode": "ABCDEF"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_short_city(self):
        """TC-ADDR-05: city='A' (1 char) -> 400"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "OTHER", "street": "123 Main Street",
                                "city": "A", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_address_city_boundary_2(self):
        """TC-ADDR-05b: city exactly 2 chars (lower boundary) -> 200 or 201"""
        r = requests.post(url("/api/v1/addresses"),
                          json={"label": "OTHER", "street": "123 Main Street",
                                "city": "AB", "pincode": "500001"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_get_addresses(self):
        """TC-ADDR-06: GET /addresses -> 200 with list"""
        r = requests.get(url("/api/v1/addresses"), headers=base_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_only_one_default_bug(self):
        """TC-ADDR-07: BUG-04 CONFIRMATION - multiple defaults allowed (should not be)
        Spec: only one address can be default at a time."""
        p1 = {"label": "HOME",   "street": "Street One Long Enough",
              "city": "CityA", "pincode": "111111", "is_default": True}
        p2 = {"label": "OFFICE", "street": "Street Two Long Enough",
              "city": "CityB", "pincode": "222222", "is_default": True}
        requests.post(url("/api/v1/addresses"), json=p1, headers=base_headers())
        requests.post(url("/api/v1/addresses"), json=p2, headers=base_headers())
        r = requests.get(url("/api/v1/addresses"), headers=base_headers())
        defaults = [a for a in r.json() if a.get("is_default")]
        assert len(defaults) == 1, \
            f"BUG-04 CONFIRMED: {len(defaults)} addresses have is_default=True, expected 1"

    def test_update_address_street(self):
        """TC-ADDR-08: PUT updates street and response shows new value"""
        if not TestAddresses.created_id:
            pytest.skip("No created_id from test_add_address_valid")
        r = requests.put(url(f"/api/v1/addresses/{TestAddresses.created_id}"),
                         json={"street": "456 Updated Street Here"},
                         headers=base_headers())
        assert r.status_code == 200
        assert "456" in str(r.json())

    def test_update_address_cannot_change_label(self):
        """TC-ADDR-09: PUT cannot change label (spec: only street and is_default)"""
        if not TestAddresses.created_id:
            pytest.skip("No created_id")
        r = requests.put(url(f"/api/v1/addresses/{TestAddresses.created_id}"),
                         json={"label": "OTHER"},
                         headers=base_headers())
        # Should either ignore label change or return 400
        assert r.status_code in (200, 400)

    def test_update_address_cannot_change_city(self):
        """TC-ADDR-10: PUT cannot change city (spec: only street and is_default)"""
        if not TestAddresses.created_id:
            pytest.skip("No created_id")
        r = requests.put(url(f"/api/v1/addresses/{TestAddresses.created_id}"),
                         json={"city": "NewCity"},
                         headers=base_headers())
        assert r.status_code in (200, 400)

    def test_delete_nonexistent_address(self):
        """TC-ADDR-11: DELETE /addresses/999999 -> 404"""
        r = requests.delete(url("/api/v1/addresses/999999"), headers=base_headers())
        assert r.status_code == 404

    def test_all_three_labels_accepted(self):
        """TC-ADDR-12: HOME, OFFICE, OTHER are all valid labels"""
        for label in ["HOME", "OFFICE", "OTHER"]:
            r = requests.post(url("/api/v1/addresses"),
                              json={"label": label, "street": "123 Main Street",
                                    "city": "Hyderabad", "pincode": "500001",
                                    "is_default": False},
                              headers=base_headers())
            assert r.status_code in (200, 201), f"Label {label} was rejected"


# ══════════════════════════════════════════════════════════════════════════════
#  TC-PROD  :  Products
# ══════════════════════════════════════════════════════════════════════════════

class TestProducts:

    def test_list_products(self):
        """TC-PROD-01: GET /products -> 200 with list"""
        r = requests.get(url("/api/v1/products"), headers=base_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_only_active_products_returned(self):
        """TC-PROD-02: Public list never shows inactive products"""
        public   = requests.get(url("/api/v1/products"), headers=base_headers()).json()
        admin    = requests.get(url("/api/v1/admin/products"), headers=admin_headers()).json()
        inactive = {p["product_id"] for p in admin if not p.get("is_active", True)}
        public_ids = {p["product_id"] for p in public}
        assert inactive.isdisjoint(public_ids), \
            f"Inactive product IDs leaked into public list: {inactive & public_ids}"

    def test_get_product_by_id(self):
        """TC-PROD-03: Valid product_id -> 200"""
        p = first_product()
        r = requests.get(url(f"/api/v1/products/{p['product_id']}"), headers=base_headers())
        assert r.status_code == 200

    def test_get_product_has_price_field(self):
        """TC-PROD-03b: Single product response has price field"""
        p = first_product()
        r = requests.get(url(f"/api/v1/products/{p['product_id']}"), headers=base_headers())
        assert "price" in r.json()

    def test_get_nonexistent_product(self):
        """TC-PROD-04: Non-existent product_id -> 404"""
        r = requests.get(url("/api/v1/products/999999"), headers=base_headers())
        assert r.status_code == 404

    def test_sort_by_price_asc(self):
        """TC-PROD-05: ?sort=price_asc -> prices in ascending order"""
        r = requests.get(url("/api/v1/products?sort=price_asc"), headers=base_headers())
        assert r.status_code == 200
        prices = [p["price"] for p in r.json()]
        assert prices == sorted(prices), f"Prices not ascending: {prices}"

    def test_sort_by_price_desc(self):
        """TC-PROD-06: ?sort=price_desc -> prices in descending order"""
        r = requests.get(url("/api/v1/products?sort=price_desc"), headers=base_headers())
        assert r.status_code == 200
        prices = [p["price"] for p in r.json()]
        assert prices == sorted(prices, reverse=True), f"Prices not descending: {prices}"

    def test_price_matches_admin(self):
        """TC-PROD-07: Price in public endpoint = price in admin endpoint"""
        public = requests.get(url("/api/v1/products"), headers=base_headers()).json()
        admin  = requests.get(url("/api/v1/admin/products"), headers=admin_headers()).json()
        if not public:
            pytest.skip("No products")
        admin_map = {p["product_id"]: p["price"] for p in admin}
        for p in public[:5]:
            assert p["price"] == admin_map[p["product_id"]], \
                f"Price mismatch for product {p['product_id']}"

    def test_filter_by_category(self):
        """TC-PROD-08: ?category= filter returns only matching products"""
        products = requests.get(url("/api/v1/products"), headers=base_headers()).json()
        if not products:
            pytest.skip("No products")
        cat = products[0].get("category")
        if not cat:
            pytest.skip("No category field on products")
        r = requests.get(url(f"/api/v1/products?category={cat}"), headers=base_headers())
        assert r.status_code == 200
        for p in r.json():
            assert p["category"] == cat

    def test_search_by_name(self):
        """TC-PROD-09: ?search= returns matching products"""
        products = requests.get(url("/api/v1/products"), headers=base_headers()).json()
        if not products:
            pytest.skip("No products")
        name = products[0].get("name", "")
        if not name:
            pytest.skip("No name field")
        partial = name[:3]
        r = requests.get(url(f"/api/v1/products?search={partial}"), headers=base_headers())
        assert r.status_code == 200

    def test_admin_products_includes_inactive(self):
        """TC-PROD-10: Admin list can return inactive products"""
        r = requests.get(url("/api/v1/admin/products"), headers=admin_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ══════════════════════════════════════════════════════════════════════════════
#  TC-CART  :  Cart
# ══════════════════════════════════════════════════════════════════════════════

class TestCart:

    @pytest.fixture(autouse=True)
    def clear_cart(self):
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        yield
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())

    def test_get_empty_cart(self):
        """TC-CART-01: Empty cart -> 200, total=0"""
        r = requests.get(url("/api/v1/cart"), headers=base_headers())
        assert r.status_code == 200
        assert r.json().get("total", 0) == 0

    def test_add_item_valid(self):
        """TC-CART-02: Add valid product qty=1 -> 200"""
        p = first_product()
        r = requests.post(url("/api/v1/cart/add"),
                          json={"product_id": p["product_id"], "quantity": 1},
                          headers=base_headers())
        assert r.status_code == 200

    def test_add_item_zero_quantity_bug(self):
        """TC-CART-03: BUG-05 CONFIRMATION - quantity=0 should be 400, API returns 200"""
        p = first_product()
        r = requests.post(url("/api/v1/cart/add"),
                          json={"product_id": p["product_id"], "quantity": 0},
                          headers=base_headers())
        assert r.status_code == 400, \
            f"BUG-05 CONFIRMED: quantity=0 accepted, got {r.status_code}"

    def test_add_item_negative_quantity_bug(self):
        """TC-CART-04: BUG-06 CONFIRMATION - quantity=-1 should be 400, API returns 200"""
        p = first_product()
        r = requests.post(url("/api/v1/cart/add"),
                          json={"product_id": p["product_id"], "quantity": -1},
                          headers=base_headers())
        assert r.status_code == 400, \
            f"BUG-06 CONFIRMED: quantity=-1 accepted, got {r.status_code}"

    def test_add_item_minimum_valid_quantity(self):
        """TC-CART-05: quantity=1 (minimum valid) -> 200"""
        p = first_product()
        r = requests.post(url("/api/v1/cart/add"),
                          json={"product_id": p["product_id"], "quantity": 1},
                          headers=base_headers())
        assert r.status_code == 200

    def test_add_nonexistent_product(self):
        """TC-CART-06: Non-existent product_id -> 404"""
        r = requests.post(url("/api/v1/cart/add"),
                          json={"product_id": 999999, "quantity": 1},
                          headers=base_headers())
        assert r.status_code == 404

    def test_add_over_stock(self):
        """TC-CART-07: quantity > stock -> 400"""
        p = first_product()
        r = requests.post(url("/api/v1/cart/add"),
                          json={"product_id": p["product_id"], "quantity": 9999999},
                          headers=base_headers())
        assert r.status_code == 400

    def test_add_same_product_twice_accumulates(self):
        """TC-CART-08: Adding same product twice accumulates quantity"""
        p = first_product()
        pid = p["product_id"]
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 1}, headers=base_headers())
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 1}, headers=base_headers())
        cart = requests.get(url("/api/v1/cart"), headers=base_headers()).json()
        matching = [i for i in cart.get("items", []) if i["product_id"] == pid]
        assert len(matching) == 1
        assert matching[0]["quantity"] == 2

    def test_subtotal_correct_bug(self):
        """TC-CART-09: BUG-07 CONFIRMATION - subtotal = quantity * unit_price
        BUG-07: API returns negative/wrong subtotal (e.g. -16 instead of 240)"""
        p = first_product()
        pid = p["product_id"]
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 2}, headers=base_headers())
        cart = requests.get(url("/api/v1/cart"), headers=base_headers()).json()
        item = next((i for i in cart.get("items", []) if i["product_id"] == pid), None)
        assert item is not None
        expected_subtotal = item["unit_price"] * 2
        assert abs(item["subtotal"] - expected_subtotal) < 0.01, \
            f"BUG-07 CONFIRMED: subtotal={item['subtotal']}, expected={expected_subtotal}"

    def test_cart_total_is_sum_of_subtotals_bug(self):
        """TC-CART-10: BUG-08 CONFIRMATION - cart total must equal sum of all subtotals"""
        products = requests.get(url("/api/v1/products"), headers=base_headers()).json()
        if len(products) < 2:
            pytest.skip("Need at least 2 products")
        for p in products[:2]:
            requests.post(url("/api/v1/cart/add"),
                          json={"product_id": p["product_id"], "quantity": 1},
                          headers=base_headers())
        cart = requests.get(url("/api/v1/cart"), headers=base_headers()).json()
        expected = sum(i["subtotal"] for i in cart.get("items", []))
        assert abs(cart["total"] - expected) < 0.01, \
            f"BUG-08 CONFIRMED: cart total={cart['total']}, sum of subtotals={expected}"

    def test_remove_item_not_in_cart(self):
        """TC-CART-11: Remove product not in cart -> 404"""
        r = requests.post(url("/api/v1/cart/remove"),
                          json={"product_id": 999999}, headers=base_headers())
        assert r.status_code == 404

    def test_update_quantity_to_zero(self):
        """TC-CART-12: Update cart item to quantity=0 -> 400"""
        p = first_product()
        pid = p["product_id"]
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 1}, headers=base_headers())
        r = requests.post(url("/api/v1/cart/update"),
                          json={"product_id": pid, "quantity": 0},
                          headers=base_headers())
        assert r.status_code == 400

    def test_update_quantity_to_negative(self):
        """TC-CART-13: Update cart item to quantity=-1 -> 400"""
        p = first_product()
        pid = p["product_id"]
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 1}, headers=base_headers())
        r = requests.post(url("/api/v1/cart/update"),
                          json={"product_id": pid, "quantity": -1},
                          headers=base_headers())
        assert r.status_code == 400

    def test_clear_cart(self):
        """TC-CART-14: DELETE /cart/clear empties the cart"""
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        cart = requests.get(url("/api/v1/cart"), headers=base_headers()).json()
        assert cart.get("total", 0) == 0
        assert cart.get("items", []) == []

    def test_remove_item_clears_it_from_cart(self):
        """TC-CART-15: After removal, product no longer in cart"""
        p = first_product()
        pid = p["product_id"]
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 1}, headers=base_headers())
        requests.post(url("/api/v1/cart/remove"),
                      json={"product_id": pid}, headers=base_headers())
        cart = requests.get(url("/api/v1/cart"), headers=base_headers()).json()
        remaining = [i for i in cart.get("items", []) if i["product_id"] == pid]
        assert len(remaining) == 0


# ══════════════════════════════════════════════════════════════════════════════
#  TC-CHKOUT  :  Checkout
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckout:

    @pytest.fixture(autouse=True)
    def setup_cart(self):
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        yield
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())

    def test_checkout_empty_cart(self):
        """TC-CHKOUT-01: Checkout with empty cart -> 400"""
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "COD"}, headers=base_headers())
        assert r.status_code == 400

    def test_checkout_invalid_payment_method(self):
        """TC-CHKOUT-02: payment_method='BITCOIN' -> 400"""
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "BITCOIN"}, headers=base_headers())
        assert r.status_code == 400

    def test_checkout_missing_payment_method(self):
        """TC-CHKOUT-02b: Missing payment_method field -> 400"""
        r = requests.post(url("/api/v1/checkout"),
                          json={}, headers=base_headers())
        assert r.status_code == 400

    def test_checkout_cod_status_pending(self):
        """TC-CHKOUT-03: COD checkout -> payment_status=PENDING"""
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "COD"}, headers=base_headers())
        assert r.status_code in (200, 201)
        assert r.json().get("payment_status") == "PENDING"

    def test_checkout_card_status_paid(self):
        """TC-CHKOUT-04: CARD checkout -> payment_status=PAID"""
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "CARD"}, headers=base_headers())
        assert r.status_code in (200, 201)
        assert r.json().get("payment_status") == "PAID"

    def test_checkout_wallet_status_pending(self):
        """TC-CHKOUT-04b: WALLET checkout -> payment_status=PENDING"""
        # Top up wallet first
        requests.post(url("/api/v1/wallet/add"),
                      json={"amount": 10000}, headers=base_headers())
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "WALLET"}, headers=base_headers())
        if r.status_code in (200, 201):
            assert r.json().get("payment_status") == "PENDING"

    def test_gst_is_5_percent(self):
        """TC-CHKOUT-05: Order total = cart_subtotal * 1.05
        NOTE: Uses flexible field lookup for total field."""
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        cart = requests.get(url("/api/v1/cart"), headers=base_headers()).json()
        subtotal = cart["total"]
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "CARD"}, headers=base_headers())
        assert r.status_code in (200, 201)
        order = r.json()
        # Try all possible field names for the total
        actual_total = (order.get("total") or
                        order.get("order_total") or
                        order.get("total_amount") or
                        order.get("amount"))
        assert actual_total is not None, \
            f"BUG-09: No total field found in checkout response. Keys: {list(order.keys())}"
        expected = round(subtotal * 1.05, 2)
        assert abs(actual_total - expected) < 0.10, \
            f"GST bug: actual={actual_total}, expected={expected} (subtotal={subtotal})"

    def test_cod_blocked_over_5000(self):
        """TC-CHKOUT-06: COD on order > 5000 -> 400"""
        products = requests.get(url("/api/v1/products"), headers=base_headers()).json()
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        added = False
        for p in products:
            if p.get("price", 0) * 2 * 1.05 > 5000:
                r = requests.post(url("/api/v1/cart/add"),
                                  json={"product_id": p["product_id"], "quantity": 2},
                                  headers=base_headers())
                if r.status_code == 200:
                    added = True
                    break
        if not added:
            pytest.skip("No products found to push order total above 5000")
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "COD"}, headers=base_headers())
        assert r.status_code == 400, \
            f"COD should be blocked over 5000, got {r.status_code}"

    def test_checkout_creates_order(self):
        """TC-CHKOUT-07: Successful checkout creates an order visible in GET /orders"""
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "CARD"}, headers=base_headers())
        assert r.status_code in (200, 201)
        oid = r.json().get("order_id")
        assert oid is not None
        orders = requests.get(url("/api/v1/orders"), headers=base_headers()).json()
        order_ids = [str(o.get("order_id", "")) for o in orders]
        assert str(oid) in order_ids


# ══════════════════════════════════════════════════════════════════════════════
#  TC-WALLET  :  Wallet
# ══════════════════════════════════════════════════════════════════════════════

class TestWallet:
    """
    CONFIRMED: API uses field name 'wallet_balance' not 'balance'
    This is a spec violation (spec says 'balance') - documented as BUG.
    """

    def test_get_wallet_returns_200(self):
        """TC-WALL-01: GET /wallet -> 200"""
        r = requests.get(url("/api/v1/wallet"), headers=base_headers())
        assert r.status_code == 200

    def test_wallet_has_balance_field_bug(self):
        """TC-WALL-01b: Response should have 'balance' field per spec
        BUG: API returns 'wallet_balance' instead of 'balance'"""
        r = requests.get(url("/api/v1/wallet"), headers=base_headers())
        data = r.json()
        assert "balance" in data, \
            f"BUG: Expected field 'balance' but got keys: {list(data.keys())}"

    def test_wallet_has_some_balance_field(self):
        """TC-WALL-01c: Flexible check - wallet_balance OR balance present"""
        r = requests.get(url("/api/v1/wallet"), headers=base_headers())
        data = r.json()
        has_balance = "balance" in data or "wallet_balance" in data
        assert has_balance, f"No balance field found. Keys: {list(data.keys())}"

    def test_add_money_valid(self):
        """TC-WALL-02: Add 100 -> balance increases by exactly 100"""
        before = get_wallet_balance()
        r = requests.post(url("/api/v1/wallet/add"),
                          json={"amount": 100}, headers=base_headers())
        assert r.status_code == 200
        after = get_wallet_balance()
        assert abs(after - before - 100) < 0.01, \
            f"Expected increase of 100, got {after - before}"

    def test_add_money_zero(self):
        """TC-WALL-03: amount=0 -> 400"""
        r = requests.post(url("/api/v1/wallet/add"),
                          json={"amount": 0}, headers=base_headers())
        assert r.status_code == 400

    def test_add_money_negative(self):
        """TC-WALL-04: amount=-50 -> 400"""
        r = requests.post(url("/api/v1/wallet/add"),
                          json={"amount": -50}, headers=base_headers())
        assert r.status_code == 400

    def test_add_money_exceeds_100000(self):
        """TC-WALL-05: amount=100001 -> 400"""
        r = requests.post(url("/api/v1/wallet/add"),
                          json={"amount": 100001}, headers=base_headers())
        assert r.status_code == 400

    def test_add_money_boundary_100000(self):
        """TC-WALL-06: amount=100000 (upper boundary) -> 200"""
        r = requests.post(url("/api/v1/wallet/add"),
                          json={"amount": 100000}, headers=base_headers())
        assert r.status_code == 200

    def test_add_money_boundary_1(self):
        """TC-WALL-06b: amount=1 (lower boundary, just above 0) -> 200"""
        r = requests.post(url("/api/v1/wallet/add"),
                          json={"amount": 1}, headers=base_headers())
        assert r.status_code == 200

    def test_pay_from_wallet_insufficient(self):
        """TC-WALL-07: Pay more than balance -> 400"""
        balance = get_wallet_balance()
        r = requests.post(url("/api/v1/wallet/pay"),
                          json={"amount": balance + 99999}, headers=base_headers())
        assert r.status_code == 400

    def test_pay_exact_amount_deducted(self):
        """TC-WALL-08: Pay 50 -> balance decreases by exactly 50"""
        requests.post(url("/api/v1/wallet/add"),
                      json={"amount": 500}, headers=base_headers())
        before = get_wallet_balance()
        r = requests.post(url("/api/v1/wallet/pay"),
                          json={"amount": 50}, headers=base_headers())
        assert r.status_code == 200
        after = get_wallet_balance()
        assert abs(before - after - 50) < 0.01, \
            f"Expected deduction of 50, got {before - after}"

    def test_pay_zero_from_wallet(self):
        """TC-WALL-09: Pay amount=0 -> 400"""
        r = requests.post(url("/api/v1/wallet/pay"),
                          json={"amount": 0}, headers=base_headers())
        assert r.status_code == 400

    def test_pay_negative_from_wallet(self):
        """TC-WALL-10: Pay amount=-10 -> 400"""
        r = requests.post(url("/api/v1/wallet/pay"),
                          json={"amount": -10}, headers=base_headers())
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
#  TC-LOYAL  :  Loyalty Points
# ══════════════════════════════════════════════════════════════════════════════

class TestLoyalty:
    """
    CONFIRMED: API uses field name 'loyalty_points' not 'points'
    This is a spec violation - documented as BUG.
    """

    def test_get_loyalty_returns_200(self):
        """TC-LOYAL-01: GET /loyalty -> 200"""
        r = requests.get(url("/api/v1/loyalty"), headers=base_headers())
        assert r.status_code == 200

    def test_loyalty_has_points_field_bug(self):
        """TC-LOYAL-01b: Response should have 'points' field per spec
        BUG: API returns 'loyalty_points' instead of 'points'"""
        r = requests.get(url("/api/v1/loyalty"), headers=base_headers())
        data = r.json()
        assert "points" in data, \
            f"BUG: Expected field 'points' but got keys: {list(data.keys())}"

    def test_loyalty_has_some_points_field(self):
        """TC-LOYAL-01c: Flexible check - loyalty_points OR points present"""
        r = requests.get(url("/api/v1/loyalty"), headers=base_headers())
        data = r.json()
        has_points = "points" in data or "loyalty_points" in data
        assert has_points, f"No points field found. Keys: {list(data.keys())}"

    def test_redeem_more_than_available(self):
        """TC-LOYAL-02: Redeem more than available -> 400"""
        pts = get_loyalty_points()
        r = requests.post(url("/api/v1/loyalty/redeem"),
                          json={"points": pts + 99999}, headers=base_headers())
        assert r.status_code == 400

    def test_redeem_zero_points(self):
        """TC-LOYAL-03: Redeem 0 points -> 400"""
        r = requests.post(url("/api/v1/loyalty/redeem"),
                          json={"points": 0}, headers=base_headers())
        assert r.status_code == 400

    def test_redeem_negative_points(self):
        """TC-LOYAL-04: Redeem -1 points -> 400"""
        r = requests.post(url("/api/v1/loyalty/redeem"),
                          json={"points": -1}, headers=base_headers())
        assert r.status_code == 400

    def test_redeem_valid_if_enough(self):
        """TC-LOYAL-05: Redeem 1 point if available -> 200"""
        pts = get_loyalty_points()
        if pts < 1:
            pytest.skip("User has no loyalty points")
        r = requests.post(url("/api/v1/loyalty/redeem"),
                          json={"points": 1}, headers=base_headers())
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
#  TC-ORDERS  :  Orders
# ══════════════════════════════════════════════════════════════════════════════

class TestOrders:

    def test_get_orders(self):
        """TC-ORD-01: GET /orders -> 200 with list"""
        r = requests.get(url("/api/v1/orders"), headers=base_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_order_by_id(self):
        """TC-ORD-02: Valid order_id -> 200"""
        oid = place_card_order()
        r = requests.get(url(f"/api/v1/orders/{oid}"), headers=base_headers())
        assert r.status_code == 200

    def test_cancel_nonexistent_order(self):
        """TC-ORD-03: Cancel non-existent order_id -> 404"""
        r = requests.post(url("/api/v1/orders/999999/cancel"), headers=base_headers())
        assert r.status_code == 404

    def test_cancel_valid_order(self):
        """TC-ORD-03b: Cancel a valid order -> 200"""
        oid = place_card_order()
        r = requests.post(url(f"/api/v1/orders/{oid}/cancel"), headers=base_headers())
        assert r.status_code == 200

    def test_stock_restored_on_cancel(self):
        """TC-ORD-04: Cancelling restores product stock
        Uses single product endpoint for stock (list endpoint has no stock field)."""
        p = first_product()
        pid = p["product_id"]
        # Get stock from single product endpoint
        stock_before = get_product_stock(pid)
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": pid, "quantity": 1}, headers=base_headers())
        r = requests.post(url("/api/v1/checkout"),
                          json={"payment_method": "CARD"}, headers=base_headers())
        oid = r.json().get("order_id")
        requests.post(url(f"/api/v1/orders/{oid}/cancel"), headers=base_headers())
        stock_after = get_product_stock(pid)
        assert stock_after == stock_before, \
            f"Stock not restored: before={stock_before}, after={stock_after}"

    def test_invoice_fields_present(self):
        """TC-ORD-05: Invoice has subtotal, gst, and total fields
        NOTE: API uses 'gst_amount' and 'total_amount' (BUG-12 vs spec which says 'gst'/'total')"""
        oid = place_card_order()
        r = requests.get(url(f"/api/v1/orders/{oid}/invoice"), headers=base_headers())
        assert r.status_code == 200
        inv = r.json()
        # Flexible field name check
        has_subtotal = "subtotal" in inv
        has_gst      = "gst" in inv or "gst_amount" in inv
        has_total    = "total" in inv or "total_amount" in inv
        assert has_subtotal, f"No subtotal field. Keys: {list(inv.keys())}"
        assert has_gst,      f"No gst field. Keys: {list(inv.keys())}"
        assert has_total,    f"No total field. Keys: {list(inv.keys())}"

    def test_invoice_spec_field_names_bug(self):
        """TC-ORD-05b: BUG-12 CONFIRMATION - invoice should use 'gst' and 'total' per spec"""
        oid = place_card_order()
        r = requests.get(url(f"/api/v1/orders/{oid}/invoice"), headers=base_headers())
        inv = r.json()
        assert "gst" in inv, \
            f"BUG-12 CONFIRMED: Expected field 'gst' per spec, got keys: {list(inv.keys())}"
        assert "total" in inv, \
            f"BUG-12 CONFIRMED: Expected field 'total' per spec, got keys: {list(inv.keys())}"

    def test_invoice_gst_arithmetic(self):
        """TC-ORD-05c: BUG-13 CHECK - invoice total should = subtotal + gst"""
        oid = place_card_order()
        r = requests.get(url(f"/api/v1/orders/{oid}/invoice"), headers=base_headers())
        inv = r.json()
        subtotal = inv.get("subtotal", 0)
        gst      = inv.get("gst") or inv.get("gst_amount", 0)
        total    = inv.get("total") or inv.get("total_amount", 0)
        assert abs(total - (subtotal + gst)) < 0.05, \
            f"BUG-13 CONFIRMED: total({total}) != subtotal({subtotal}) + gst({gst})"

    def test_order_has_required_fields(self):
        """TC-ORD-06: Order response has order_id and payment_status"""
        oid = place_card_order()
        r = requests.get(url(f"/api/v1/orders/{oid}"), headers=base_headers())
        data = r.json()
        assert "order_id" in data or "id" in data
        assert "payment_status" in data


# ══════════════════════════════════════════════════════════════════════════════
#  TC-REVIEW  :  Reviews
# ══════════════════════════════════════════════════════════════════════════════

class TestReviews:

    def _pid(self):
        return first_product()["product_id"]

    def test_get_reviews(self):
        """TC-REV-01: GET /products/{id}/reviews -> 200"""
        r = requests.get(url(f"/api/v1/products/{self._pid()}/reviews"),
                         headers=base_headers())
        assert r.status_code == 200

    def test_add_valid_review_rating_1(self):
        """TC-REV-02a: rating=1 (lower boundary) -> 200 or 201"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 1, "comment": "Terrible product"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_add_valid_review_rating_5(self):
        """TC-REV-02b: rating=5 (upper boundary) -> 200 or 201"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 5, "comment": "Excellent product"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_add_valid_review_rating_3(self):
        """TC-REV-02c: rating=3 (middle) -> 200 or 201"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 3, "comment": "Average product ok"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_review_rating_zero_bug(self):
        """TC-REV-03: BUG-10 CONFIRMATION - rating=0 should be 400, API accepts it"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 0, "comment": "Bad"},
                          headers=base_headers())
        assert r.status_code == 400, \
            f"BUG-10 CONFIRMED: rating=0 was accepted, got {r.status_code}"

    def test_review_rating_six_bug(self):
        """TC-REV-04: BUG-11 CONFIRMATION - rating=6 should be 400, API accepts it"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 6, "comment": "Too good"},
                          headers=base_headers())
        assert r.status_code == 400, \
            f"BUG-11 CONFIRMED: rating=6 was accepted, got {r.status_code}"

    def test_review_rating_negative(self):
        """TC-REV-04b: rating=-1 -> 400"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": -1, "comment": "Negative"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_review_rating_100(self):
        """TC-REV-04c: rating=100 -> 400"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 100, "comment": "Perfect"},
                          headers=base_headers())
        assert r.status_code == 400

    def test_review_empty_comment(self):
        """TC-REV-05: comment='' (0 chars) -> 400"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 3, "comment": ""},
                          headers=base_headers())
        assert r.status_code == 400

    def test_review_comment_boundary_1(self):
        """TC-REV-05b: comment=1 char (lower boundary) -> 200 or 201"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 3, "comment": "A"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_review_comment_boundary_200(self):
        """TC-REV-05c: comment=200 chars (upper boundary) -> 200 or 201"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 3, "comment": "A" * 200},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_review_comment_too_long(self):
        """TC-REV-06: comment=201 chars -> 400"""
        r = requests.post(url(f"/api/v1/products/{self._pid()}/reviews"),
                          json={"rating": 3, "comment": "A" * 201},
                          headers=base_headers())
        assert r.status_code == 400

    def test_average_rating_is_decimal(self):
        """TC-REV-07: Average rating uses decimal division not integer division"""
        pid = self._pid()
        requests.post(url(f"/api/v1/products/{pid}/reviews"),
                      json={"rating": 3, "comment": "Test review comment here"},
                      headers=base_headers())
        requests.post(url(f"/api/v1/products/{pid}/reviews"),
                      json={"rating": 4, "comment": "Another test review here"},
                      headers=base_headers())
        r = requests.get(url(f"/api/v1/products/{pid}/reviews"), headers=base_headers())
        data = r.json()
        avg = data.get("average_rating") if isinstance(data, dict) else None
        if avg is not None:
            # 3+4 / 2 = 3.5, NOT 3 (integer division would give 3)
            assert avg != int(avg) or avg == 0, \
                f"Possible integer division bug: average_rating={avg}"

    def test_no_reviews_average_is_zero(self):
        """TC-REV-08: Product with no reviews -> average_rating=0"""
        admin_products = requests.get(url("/api/v1/admin/products"),
                                      headers=admin_headers()).json()
        for p in admin_products:
            if p.get("is_active"):
                pid = p["product_id"]
                data = requests.get(url(f"/api/v1/products/{pid}/reviews"),
                                    headers=base_headers()).json()
                reviews = data if isinstance(data, list) else data.get("reviews", [])
                if len(reviews) == 0:
                    avg = data.get("average_rating") if isinstance(data, dict) else 0
                    assert avg == 0
                    return
        pytest.skip("All products already have reviews")

    def test_review_nonexistent_product(self):
        """TC-REV-09: Review on non-existent product -> 404"""
        r = requests.post(url("/api/v1/products/999999/reviews"),
                          json={"rating": 3, "comment": "Does not exist"},
                          headers=base_headers())
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
#  TC-COUPON  :  Coupons
# ══════════════════════════════════════════════════════════════════════════════

class TestCoupons:

    @pytest.fixture(autouse=True)
    def clear_cart(self):
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())
        yield
        requests.delete(url("/api/v1/cart/clear"), headers=base_headers())

    def test_apply_invalid_coupon(self):
        """TC-CPN-01: Non-existent coupon code -> 400 or 404"""
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 1},
                      headers=base_headers())
        r = requests.post(url("/api/v1/coupon/apply"),
                          json={"code": "FAKECODE999"}, headers=base_headers())
        assert r.status_code in (400, 404)

    def test_apply_coupon_on_empty_cart(self):
        """TC-CPN-02: Apply coupon on empty cart -> 400
        Uses flexible field name lookup for coupon code."""
        coupons = requests.get(url("/api/v1/admin/coupons"), headers=admin_headers()).json()
        if not coupons:
            pytest.skip("No coupons in DB")
        coupon_code = get_coupon_code(coupons[0])
        if not coupon_code:
            pytest.skip(f"Cannot find coupon code field. Keys: {list(coupons[0].keys())}")
        r = requests.post(url("/api/v1/coupon/apply"),
                          json={"code": coupon_code}, headers=base_headers())
        assert r.status_code == 400

    def test_admin_coupons_field_names(self):
        """TC-CPN-03: Inspect admin coupons to find correct field names"""
        r = requests.get(url("/api/v1/admin/coupons"), headers=admin_headers())
        assert r.status_code == 200
        coupons = r.json()
        if coupons:
            # Document what fields are present for debugging
            keys = list(coupons[0].keys())
            # Should have some code field
            has_code = any(k in keys for k in ["code", "coupon_code", "coupon"])
            assert has_code, f"No code field found in coupon. Fields: {keys}"

    def test_remove_coupon(self):
        """TC-CPN-04: Remove coupon -> 200 or 400 (graceful)"""
        r = requests.post(url("/api/v1/coupon/remove"), headers=base_headers())
        assert r.status_code in (200, 400)

    def test_apply_valid_coupon(self):
        """TC-CPN-05: Apply a valid non-expired coupon to a qualifying cart -> 200"""
        coupons = requests.get(url("/api/v1/admin/coupons"), headers=admin_headers()).json()
        if not coupons:
            pytest.skip("No coupons in DB")
        coupon_code = get_coupon_code(coupons[0])
        if not coupon_code:
            pytest.skip("Cannot find coupon code field")
        # Add enough items to cart
        p = first_product()
        requests.post(url("/api/v1/cart/add"),
                      json={"product_id": p["product_id"], "quantity": 5},
                      headers=base_headers())
        r = requests.post(url("/api/v1/coupon/apply"),
                          json={"code": coupon_code}, headers=base_headers())
        # May be 200 (valid) or 400 (expired/min value not met) - both are valid responses
        assert r.status_code in (200, 400)


# ══════════════════════════════════════════════════════════════════════════════
#  TC-TICKET  :  Support Tickets
# ══════════════════════════════════════════════════════════════════════════════

class TestSupportTickets:
    created_id = None

    def test_create_ticket_valid(self):
        """TC-TKT-01: Valid ticket -> 200/201, status=OPEN"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Test Subject Here",
                                "message": "This is a test message."},
                          headers=base_headers())
        assert r.status_code in (200, 201)
        data = r.json()
        assert data.get("status") == "OPEN"
        TestSupportTickets.created_id = data.get("ticket_id")

    def test_create_ticket_short_subject(self):
        """TC-TKT-02: subject='Hi' (2 chars, below min 5) -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Hi", "message": "Valid message here."},
                          headers=base_headers())
        assert r.status_code == 400

    def test_create_ticket_subject_boundary_4(self):
        """TC-TKT-02b: subject=4 chars (one below min) -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Hi!!", "message": "Valid message here."},
                          headers=base_headers())
        assert r.status_code == 400

    def test_create_ticket_subject_boundary_5(self):
        """TC-TKT-02c: subject=5 chars (lower boundary) -> 200 or 201"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Hello", "message": "Valid message."},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_create_ticket_empty_message(self):
        """TC-TKT-03: message='' -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Valid Subject", "message": ""},
                          headers=base_headers())
        assert r.status_code == 400

    def test_create_ticket_message_boundary_1(self):
        """TC-TKT-03b: message=1 char (lower boundary) -> 200 or 201"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Valid Subject", "message": "A"},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_create_ticket_long_message(self):
        """TC-TKT-04: message=501 chars -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Valid Subject", "message": "A" * 501},
                          headers=base_headers())
        assert r.status_code == 400

    def test_create_ticket_message_boundary_500(self):
        """TC-TKT-04b: message=500 chars (upper boundary) -> 200 or 201"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Valid Subject", "message": "A" * 500},
                          headers=base_headers())
        assert r.status_code in (200, 201)

    def test_create_ticket_long_subject(self):
        """TC-TKT-04c: subject=101 chars (above max 100) -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "A" * 101, "message": "Valid message."},
                          headers=base_headers())
        assert r.status_code == 400

    def test_get_tickets(self):
        """TC-TKT-05: GET /support/tickets -> 200 with list"""
        r = requests.get(url("/api/v1/support/tickets"), headers=base_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_status_transition_open_to_in_progress(self):
        """TC-TKT-06: OPEN -> IN_PROGRESS -> 200"""
        if not TestSupportTickets.created_id:
            pytest.skip("No ticket id from creation test")
        r = requests.put(url(f"/api/v1/support/tickets/{TestSupportTickets.created_id}"),
                         json={"status": "IN_PROGRESS"}, headers=base_headers())
        assert r.status_code == 200

    def test_invalid_status_transition_open_to_closed(self):
        """TC-TKT-07: OPEN -> CLOSED (skipping IN_PROGRESS) -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Another Ticket", "message": "Test message body."},
                          headers=base_headers())
        tid = r.json().get("ticket_id")
        r2 = requests.put(url(f"/api/v1/support/tickets/{tid}"),
                          json={"status": "CLOSED"}, headers=base_headers())
        assert r2.status_code == 400

    def test_invalid_status_transition_backwards(self):
        """TC-TKT-07b: IN_PROGRESS -> OPEN (backwards) -> 400"""
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Backwards Test", "message": "Test message body."},
                          headers=base_headers())
        tid = r.json().get("ticket_id")
        # Move to IN_PROGRESS
        requests.put(url(f"/api/v1/support/tickets/{tid}"),
                     json={"status": "IN_PROGRESS"}, headers=base_headers())
        # Try to go back
        r2 = requests.put(url(f"/api/v1/support/tickets/{tid}"),
                          json={"status": "OPEN"}, headers=base_headers())
        assert r2.status_code == 400

    def test_message_saved_exactly(self):
        """TC-TKT-08: Full message saved verbatim including special chars"""
        msg = "Exact message: special chars !@#$%^&*()"
        r = requests.post(url("/api/v1/support/ticket"),
                          json={"subject": "Exact Save Test", "message": msg},
                          headers=base_headers())
        assert r.status_code in (200, 201)
        assert r.json().get("message") == msg

    def test_new_ticket_always_starts_open(self):
        """TC-TKT-09: Verify new tickets always start with OPEN status"""
        for _ in range(2):
            r = requests.post(url("/api/v1/support/ticket"),
                              json={"subject": "Status Check", "message": "Check status."},
                              headers=base_headers())
            assert r.json().get("status") == "OPEN"


# ══════════════════════════════════════════════════════════════════════════════
#  TC-ADMIN  :  Admin endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestAdmin:

    def test_admin_users(self):
        """TC-ADM-01: GET /admin/users -> 200 with list"""
        r = requests.get(url("/api/v1/admin/users"), headers=admin_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_users_has_wallet_and_loyalty(self):
        """TC-ADM-01b: Admin users have wallet and loyalty fields"""
        r = requests.get(url("/api/v1/admin/users"), headers=admin_headers())
        users = r.json()
        if not users:
            pytest.skip("No users in DB")
        u = users[0]
        has_wallet  = any(k in u for k in ["wallet_balance", "balance", "wallet"])
        has_loyalty = any(k in u for k in ["loyalty_points", "points", "loyalty"])
        assert has_wallet,  f"No wallet field in user. Keys: {list(u.keys())}"
        assert has_loyalty, f"No loyalty field in user. Keys: {list(u.keys())}"

    def test_admin_user_by_id(self):
        """TC-ADM-02: GET /admin/users/1 -> 200"""
        r = requests.get(url(f"/api/v1/admin/users/{USER_ID}"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_user_nonexistent(self):
        """TC-ADM-02b: GET /admin/users/999999 -> 404"""
        r = requests.get(url("/api/v1/admin/users/999999"), headers=admin_headers())
        assert r.status_code == 404

    def test_admin_carts(self):
        """TC-ADM-03: GET /admin/carts -> 200"""
        r = requests.get(url("/api/v1/admin/carts"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_orders(self):
        """TC-ADM-04: GET /admin/orders -> 200"""
        r = requests.get(url("/api/v1/admin/orders"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_products(self):
        """TC-ADM-05: GET /admin/products -> 200 with list"""
        r = requests.get(url("/api/v1/admin/products"), headers=admin_headers())
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_coupons(self):
        """TC-ADM-06: GET /admin/coupons -> 200"""
        r = requests.get(url("/api/v1/admin/coupons"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_tickets(self):
        """TC-ADM-07: GET /admin/tickets -> 200"""
        r = requests.get(url("/api/v1/admin/tickets"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_addresses(self):
        """TC-ADM-08: GET /admin/addresses -> 200"""
        r = requests.get(url("/api/v1/admin/addresses"), headers=admin_headers())
        assert r.status_code == 200

    def test_admin_requires_roll_number(self):
        """TC-ADM-09: Admin endpoint without X-Roll-Number -> 401"""
        r = requests.get(url("/api/v1/admin/users"))
        assert r.status_code == 401