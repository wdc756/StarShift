import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from starshift.star_shift import *
from datetime import datetime



InvalidType = object()

@pytest.fixture(autouse=True)
def reset_starshift():
    reset_starshift_globals()
    yield
    reset_starshift_globals()



# Classes
########################################################################################################################

class Address(Shift):
    """Address with validation and transformation"""
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

    @shift_transformer('zip_code')
    def transform_zip(self, val):
        """Strip whitespace and format zip code"""
        if isinstance(val, str):
            return val.strip().replace('-', '')
        return str(val)

    @shift_validator('zip_code')
    def validate_zip(self, val):
        """Validate zip code is 5 or 9 digits"""
        return len(val) in [5, 9] and val.isdigit()

    @shift_validator('state')
    def validate_state(self, val):
        """Validate state is 2 uppercase letters"""
        return len(val) == 2 and val.isupper() and val.isalpha()

class ContactInfo(Shift):
    """Contact information with multiple validation rules"""
    email: str
    phone: str
    alternate_phone: Optional[str] = None
    preferred_contact: Literal['email', 'phone'] = 'email'

    @shift_transformer('email')
    def transform_email(self, val):
        """Normalize email to lowercase"""
        return val.lower().strip() if isinstance(val, str) else val

    @shift_validator('email')
    def validate_email(self, val):
        """Basic email validation"""
        return '@' in val and '.' in val.split('@')[1]

    @shift_transformer('phone', pre=True)
    def transform_phone(self, val):
        """Strip all non-numeric characters from phone"""
        if isinstance(val, str):
            return ''.join(c for c in val if c.isdigit())
        return str(val)

    @shift_validator('phone')
    def validate_phone(self, val):
        """Validate phone is 10 digits"""
        return len(val) == 10

    @shift_validator('alternate_phone')
    def validate_alt_phone(self, field: ShiftField, info: ShiftInfo):
        """Alternate phone must be different from primary"""
        if field.val is None:
            return True
        return field.val != self.phone

class OrderItem(Shift):
    """Individual order item with price calculations"""
    product_id: str
    name: str
    quantity: int
    unit_price: float
    discount_percent: float = 0.0
    _total_price: float = 0.0  # Private field, calculated

    @shift_validator('quantity')
    def validate_quantity(self, val):
        """Quantity must be positive"""
        return val > 0

    @shift_validator('unit_price')
    def validate_price(self, val):
        """Price must be non-negative"""
        return val >= 0

    @shift_validator('discount_percent')
    def validate_discount(self, val):
        """Discount must be between 0 and 100"""
        return 0 <= val <= 100

    @shift_setter('_total_price')
    def set_total_price(self, field: ShiftField, info: ShiftInfo):
        """Calculate total price after discount"""
        base_price = self.quantity * self.unit_price
        discount_amount = base_price * (self.discount_percent / 100)
        self._total_price = base_price - discount_amount


class Customer(Shift):
    """Customer with nested address and contact info"""
    customer_id: str
    name: str
    address: Address
    contact: ContactInfo
    vip_status: bool = False
    created_at: Optional[str] = None

    @shift_transformer('name')
    def transform_name(self, val):
        """Capitalize name properly"""
        if isinstance(val, str):
            return ' '.join(word.capitalize() for word in val.split())
        return val

    @shift_validator('customer_id')
    def validate_id(self, val):
        """Customer ID must start with 'CUST-'"""
        return isinstance(val, str) and val.startswith('CUST-')


class Order(Shift):
    """Order with forward reference to Customer and list of items"""
    order_id: str
    customer: 'Customer'  # Forward reference
    items: list[OrderItem]
    status: Literal['pending', 'processing', 'shipped', 'delivered', 'cancelled'] = 'pending'
    order_date: str
    shipping_address: Optional[Address] = None
    notes: dict[str, str] = {}
    _total_amount: float = 0.0

    @shift_validator('order_id')
    def validate_order_id(self, val):
        """Order ID must start with 'ORD-'"""
        return isinstance(val, str) and val.startswith('ORD-')

    @shift_validator('items')
    def validate_items(self, val):
        """Order must have at least one item"""
        return len(val) > 0

    @shift_setter('_total_amount')
    def calculate_total(self, field: ShiftField, info: ShiftInfo):
        """Calculate total from all items"""
        self._total_amount = sum(item._total_price for item in self.items)

    @shift_validator('_total_amount')
    def validate_total(self, field: ShiftField, info: ShiftInfo):
        """Total must be positive for non-cancelled orders"""
        if self.status == 'cancelled':
            return True
        return field.val > 0


class Warehouse(Shift):
    """Warehouse with multiple pending orders"""
    warehouse_id: str
    location: Address
    pending_orders: list[Order]
    processing_orders: list[Order] = []
    capacity: int = 1000

    @shift_validator('pending_orders', 'processing_orders')
    def validate_capacity(self, field: ShiftField, info: ShiftInfo):
        """Total orders cannot exceed capacity"""
        total = len(self.pending_orders) + len(self.processing_orders)
        return total <= self.capacity


# ================================================================================================
# TEST DATA - VALID CASES
# ================================================================================================

valid_address_1 = {
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701"
}

valid_address_2 = {
    "street": "456 Oak Ave",
    "city": "Portland",
    "state": "OR",
    "zip_code": "97201-1234",  # Will be transformed to "972011234"
    "country": "USA"
}

valid_contact_1 = {
    "email": "JOHN.DOE@EXAMPLE.COM",  # Will be lowercased
    "phone": "(555) 123-4567",  # Will be transformed to "5551234567"
    "preferred_contact": "email"
}

valid_contact_2 = {
    "email": "jane.smith@test.com",
    "phone": "555-987-6543",
    "alternate_phone": "555-111-2222",
    "preferred_contact": "phone"
}

valid_customer_1 = {
    "customer_id": "CUST-001",
    "name": "john doe",  # Will be capitalized to "John Doe"
    "address": valid_address_1,
    "contact": valid_contact_1,
    "vip_status": True
}

valid_customer_2 = {
    "customer_id": "CUST-002",
    "name": "jane smith",
    "address": valid_address_2,
    "contact": valid_contact_2
}

valid_items_1 = [
    {
        "product_id": "PROD-001",
        "name": "Widget",
        "quantity": 5,
        "unit_price": 19.99,
        "discount_percent": 10.0
    },
    {
        "product_id": "PROD-002",
        "name": "Gadget",
        "quantity": 3,
        "unit_price": 49.99,
        "discount_percent": 0.0
    }
]

valid_items_2 = [
    {
        "product_id": "PROD-003",
        "name": "Doohickey",
        "quantity": 10,
        "unit_price": 9.99,
        "discount_percent": 15.0
    }
]

valid_order_1 = {
    "order_id": "ORD-2024-001",
    "customer": valid_customer_1,
    "items": valid_items_1,
    "status": "processing",
    "order_date": "2024-12-01",
    "notes": {"special": "Gift wrap requested"}
}

valid_order_2 = {
    "order_id": "ORD-2024-002",
    "customer": valid_customer_2,
    "items": valid_items_2,
    "status": "pending",
    "order_date": "2024-12-02",
    "shipping_address": valid_address_2
}

valid_warehouse = {
    "warehouse_id": "WH-WEST-01",
    "location": {
        "street": "789 Industrial Blvd",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101"
    },
    "pending_orders": [valid_order_1, valid_order_2],
    "capacity": 5000
}

# ================================================================================================
# TEST DATA - INVALID CASES
# ================================================================================================

invalid_address_bad_zip = {
    "street": "999 Error St",
    "city": "Nowhere",
    "state": "XX",
    "zip_code": "123"  # Too short
}

invalid_address_bad_state = {
    "street": "999 Error St",
    "city": "Nowhere",
    "state": "InvalidState",  # Too long
    "zip_code": "12345"
}

invalid_contact_bad_email = {
    "email": "not-an-email",  # No @ symbol
    "phone": "5551234567"
}

invalid_contact_bad_phone = {
    "email": "valid@email.com",
    "phone": "123"  # Too short
}

invalid_contact_duplicate_phones = {
    "email": "test@test.com",
    "phone": "5551234567",
    "alternate_phone": "5551234567"  # Same as primary
}

invalid_customer_bad_id = {
    "customer_id": "BAD-001",  # Doesn't start with CUST-
    "name": "Test User",
    "address": valid_address_1,
    "contact": valid_contact_1
}

invalid_items_negative_quantity = [
    {
        "product_id": "PROD-999",
        "name": "Bad Item",
        "quantity": -5,  # Negative quantity
        "unit_price": 10.0
    }
]

invalid_items_negative_price = [
    {
        "product_id": "PROD-999",
        "name": "Bad Item",
        "quantity": 1,
        "unit_price": -10.0  # Negative price
    }
]

invalid_items_bad_discount = [
    {
        "product_id": "PROD-999",
        "name": "Bad Item",
        "quantity": 1,
        "unit_price": 10.0,
        "discount_percent": 150.0  # Over 100%
    }
]

invalid_order_bad_id = {
    "order_id": "INVALID-001",  # Doesn't start with ORD-
    "customer": valid_customer_1,
    "items": valid_items_1,
    "order_date": "2024-12-01"
}

invalid_order_no_items = {
    "order_id": "ORD-2024-999",
    "customer": valid_customer_1,
    "items": [],  # Empty items list
    "order_date": "2024-12-01"
}

invalid_warehouse_over_capacity = {
    "warehouse_id": "WH-OVER-01",
    "location": valid_address_1,
    "pending_orders": [valid_order_1, valid_order_2],
    "processing_orders": [valid_order_1],
    "capacity": 2  # Can't fit 3 orders
}


# ================================================================================================
# RUN TESTS
# ================================================================================================

def run_stress_test():
    """Run comprehensive stress tests"""

    print("=" * 80)
    print("STARSHIFT STRESS TEST")
    print("=" * 80)

    # Test 1: Valid Address
    print("\n[TEST 1] Valid Address Creation")
    try:
        addr1 = Address(**valid_address_1)
        print(f"✓ Created: {addr1}")
        assert addr1.zip_code == "62701"
        print("✓ Zip code validation passed")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 2: Address with zip code transformation
    print("\n[TEST 2] Address with Zip Code Transformation")
    try:
        addr2 = Address(**valid_address_2)
        print(f"✓ Created: {addr2}")
        assert addr2.zip_code == "972011234"  # Hyphen removed
        print("✓ Zip code transformed correctly")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 3: Valid Contact with transformations
    print("\n[TEST 3] Valid Contact with Email/Phone Transformation")
    try:
        contact1 = ContactInfo(**valid_contact_1)
        print(f"✓ Created: {contact1}")
        assert contact1.email == "john.doe@example.com"  # Lowercased
        assert contact1.phone == "5551234567"  # Cleaned
        print("✓ Email lowercased and phone cleaned")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 4: Valid Customer with nested objects
    print("\n[TEST 4] Valid Customer with Nested Address and Contact")
    try:
        customer1 = Customer(**valid_customer_1)
        print(f"✓ Created: {customer1}")
        assert customer1.name == "John Doe"  # Capitalized
        assert isinstance(customer1.address, Address)
        assert isinstance(customer1.contact, ContactInfo)
        print("✓ Name capitalized, nested objects created")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 5: Valid Order Items with price calculation
    print("\n[TEST 5] Valid Order Items with Price Calculation")
    try:
        item1 = OrderItem(**valid_items_1[0])
        print(f"✓ Created: {item1}")
        expected_total = 5 * 19.99 * 0.9  # 5 items at $19.99 with 10% discount
        assert abs(item1._total_price - expected_total) < 0.01
        print(f"✓ Total price calculated: ${item1._total_price:.2f}")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 6: Valid Order with forward reference to Customer
    print("\n[TEST 6] Valid Order with Forward Reference to Customer")
    try:
        order1 = Order(**valid_order_1)
        print(f"✓ Created: {order1}")
        assert isinstance(order1.customer, Customer)
        assert len(order1.items) == 2
        assert order1._total_amount > 0
        print(f"✓ Customer resolved, {len(order1.items)} items, total: ${order1._total_amount:.2f}")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 7: Valid Warehouse with multiple nested orders
    print("\n[TEST 7] Valid Warehouse with Multiple Nested Orders")
    try:
        warehouse = Warehouse(**valid_warehouse)
        print(f"✓ Created: {warehouse}")
        assert len(warehouse.pending_orders) == 2
        assert all(isinstance(order, Order) for order in warehouse.pending_orders)
        print(f"✓ Warehouse has {len(warehouse.pending_orders)} pending orders")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    # Test 8: Invalid address - bad zip code
    print("\n[TEST 8] Invalid Address - Bad Zip Code (should fail)")
    try:
        addr_bad = Address(**invalid_address_bad_zip)
        print(f"✗ UNEXPECTED SUCCESS: {addr_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 9: Invalid address - bad state
    print("\n[TEST 9] Invalid Address - Bad State (should fail)")
    try:
        addr_bad = Address(**invalid_address_bad_state)
        print(f"✗ UNEXPECTED SUCCESS: {addr_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 10: Invalid contact - bad email
    print("\n[TEST 10] Invalid Contact - Bad Email (should fail)")
    try:
        contact_bad = ContactInfo(**invalid_contact_bad_email)
        print(f"✗ UNEXPECTED SUCCESS: {contact_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 11: Invalid contact - bad phone
    print("\n[TEST 11] Invalid Contact - Bad Phone (should fail)")
    try:
        contact_bad = ContactInfo(**invalid_contact_bad_phone)
        print(f"✗ UNEXPECTED SUCCESS: {contact_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 12: Invalid contact - duplicate phones
    print("\n[TEST 12] Invalid Contact - Duplicate Phones (should fail)")
    try:
        contact_bad = ContactInfo(**invalid_contact_duplicate_phones)
        print(f"✗ UNEXPECTED SUCCESS: {contact_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 13: Invalid customer - bad ID
    print("\n[TEST 13] Invalid Customer - Bad ID (should fail)")
    try:
        customer_bad = Customer(**invalid_customer_bad_id)
        print(f"✗ UNEXPECTED SUCCESS: {customer_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 14: Invalid order item - negative quantity
    print("\n[TEST 14] Invalid Order Item - Negative Quantity (should fail)")
    try:
        item_bad = OrderItem(**invalid_items_negative_quantity[0])
        print(f"✗ UNEXPECTED SUCCESS: {item_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 15: Invalid order item - negative price
    print("\n[TEST 15] Invalid Order Item - Negative Price (should fail)")
    try:
        item_bad = OrderItem(**invalid_items_negative_price[0])
        print(f"✗ UNEXPECTED SUCCESS: {item_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 16: Invalid order item - bad discount
    print("\n[TEST 16] Invalid Order Item - Invalid Discount (should fail)")
    try:
        item_bad = OrderItem(**invalid_items_bad_discount[0])
        print(f"✗ UNEXPECTED SUCCESS: {item_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 17: Invalid order - bad ID
    print("\n[TEST 17] Invalid Order - Bad Order ID (should fail)")
    try:
        order_bad = Order(**invalid_order_bad_id)
        print(f"✗ UNEXPECTED SUCCESS: {order_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 18: Invalid order - no items
    print("\n[TEST 18] Invalid Order - No Items (should fail)")
    try:
        order_bad = Order(**invalid_order_no_items)
        print(f"✗ UNEXPECTED SUCCESS: {order_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 19: Invalid warehouse - over capacity
    print("\n[TEST 19] Invalid Warehouse - Over Capacity (should fail)")
    try:
        warehouse_bad = Warehouse(**invalid_warehouse_over_capacity)
        print(f"✗ UNEXPECTED SUCCESS: {warehouse_bad}")
    except ShiftError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 20: Serialization round-trip
    print("\n[TEST 20] Serialization Round-Trip")
    try:
        order1 = Order(**valid_order_1)
        serialized = order1.serialize()
        order2 = Order(**serialized)
        assert order1 == order2
        print("✓ Serialization and deserialization successful")
        print(f"  Original total: ${order1._total_amount:.2f}")
        print(f"  Restored total: ${order2._total_amount:.2f}")
    except Exception as e:
        print(f"✗ FAILED: {e}")

    print("\n" + "=" * 80)
    print("STRESS TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    run_stress_test()