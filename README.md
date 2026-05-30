# FamCARE Multi-Service Bulk Scheduler

A home healthcare booking engine where patients book multiple services across multiple days in a single atomic checkout.

**Stack**: FastAPI, PostgreSQL (SQLite for local dev), Flutter (Riverpod), pytest

---

## 🚀 Quick Start

### 1. Backend (FastAPI)
The backend uses SQLite by default for easy local development, but is fully compatible with PostgreSQL via SQLAlchemy.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the server (seeds the database on first run)
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Swagger UI documentation is at `http://localhost:8000/docs`.

**Run Tests**:
```bash
pytest tests/ -v
```

### 2. Frontend (Flutter)
```bash
cd frontend/famcare_app
flutter pub get
flutter run
```
*Note: If running on a physical device, update `AppConstants.apiBaseUrl` in `lib/config/constants.dart` to your computer's local IP address.*

---

## 📝 Evaluation Criteria

Here are the direct answers to the evaluation criteria outlined in the assignment.

### 1. Design Decision: Atomic Checkout
**How did you make checkout atomic? DB transaction or optimistic locking — why?**
I chose **DB Transactions with Pessimistic Locking (`SELECT ... FOR UPDATE`)**. In a healthcare setting, deterministic correctness matters more than high-concurrency throughput. If two patients attempt to book the same caregiver at the exact same time, the first transaction acquires the row lock. The second transaction waits, then fails gracefully when the overlap validation runs again inside the lock, ensuring zero double-bookings without complex retry logic.

### 2. Conflict Correctness: Full Duration Checking
**Does your overlap check use start time only, or full duration? Show us the query.**
The overlap check rigorously uses the **full service duration**, never just the start time. A new booking `[start_a, start_a + duration_a)` overlaps with an existing booking `[start_b, start_b + duration_b)` if:
`start_a < (start_b + duration_b) AND start_b < (start_a + duration_a)`

Here is the exact SQLAlchemy query logic used in `checkout.py`:
```python
overlapping = db.query(BookingItem).filter(
    BookingItem.caregiver_id == item.caregiver_id,
    BookingItem.slot_date == item.date,
    BookingItem.start_time < end_time_str,
    BookingItem.end_time > start_time_str
).first()
```

### 3. Failure Handling: Clear UI Error States
**Which slot failed and why — does the Flutter UI tell the user clearly?**
Yes. If the cart contains 3 slots and 1 fails due to a conflict, the **entire checkout is rolled back** (No partial bookings). 
The Flutter UI intercepts the `409 Conflict` response and redirects to a dedicated `CheckoutFailureScreen`. 
**What the error state looks like:**
- A large red warning banner indicating "Booking Failed".
- A detailed list showing exactly which item failed (e.g., "Physiotherapy at 10:00 AM") and the specific reason provided by the backend (e.g., "Caregiver Bob Patel is already booked during this time").
- A "Return to Cart" button allowing the user to remove the conflicting slot and retry.

---

## 🏗️ Architecture & Database Schema

### 1. Conflict Resolution
*If two patients book the same caregiver at the same time — who wins?*
**Decision: First-write-wins via Pessimistic Locking.**
The first transaction to acquire the row lock on the caregiver's existing schedule for that day wins. The loser is informed **at checkout time** (synchronously) exactly which slot failed and why. In a healthcare setting, deterministic correctness matters more than high concurrency throughput.

### 2. Service Duration Source
*Where does service duration come from?*
**Decision: Database Table (`services`), Snapshot in `booking_items`.**
Duration is NEVER hardcoded. It is read from the `services.duration_minutes` column (enforced to be a multiple of 15 by a `CHECK` constraint). At checkout, the duration and price are copied as **snapshots** into the `booking_items` table. This ensures that if a service's duration changes later, past bookings remain intact.

### 3. Caregiver Assignment
*Does the patient pick their caregiver, or does the system assign one?*
**Decision: Patient picks.**
The Flutter UI's `SlotPickerScreen` shows the available caregivers for a specific 15-minute slot. The user explicitly selects their preferred professional.

### 4. Partial Cart Failure UX
*If 2 of 3 slots succeed and 1 fails — do we roll everything back?*
**Decision: Full Rollback (Atomic Checkout).**
The assignment explicitly states "No partial bookings". If *any* item in the cart fails validation (e.g., caregiver is double-booked), the **entire checkout is rolled back**. The UI then displays a clear error screen explaining exactly which item(s) caused the failure, allowing the user to modify their cart.

### 5. Pricing
*Is price fixed per service or per caregiver?*
**Decision: Fixed per service.**
Stored in `services.price`. No multi-slot discounts are implemented in this v1, but the cart aggregates the total price accurately.

---

## 🛠️ Architecture & Database Schema

The database schema is designed to support the atomic checkout and conflict detection constraints. 
A PostgreSQL schema file is provided in `backend/migrations/seed.sql` for reference, though the SQLAlchemy ORM manages this automatically.

### Key Tables
- **`services`**: `id`, `name`, `duration_minutes`, `price`.
- **`caregivers`**: `id`, `name`, `phone`.
- **`caregiver_services`** (M2M): Links caregivers to the services they are qualified to perform.
- **`bookings`**: The atomic cart transaction (`id`, `patient_id`, `total_price`).
- **`booking_items`**: The individual slots (`id`, `booking_id`, `caregiver_id`, `slot_date`, `start_time`, `duration_minutes`, `price`).

### The Checkout Conflict Query (Explained)
Conflict detection uses the **full service duration**, not just the start time.
A new booking `[start_a, start_a + duration_a)` overlaps with an existing booking `[start_b, start_b + duration_b)` if:
`start_a < (start_b + duration_b) AND start_b < (start_a + duration_a)`

In `backend/app/services/checkout.py`, we detect:
1. **Intra-cart conflicts**: Did the patient add overlapping items to their own cart?
2. **Caregiver conflicts**: Does this slot overlap with any of the caregiver's existing confirmed bookings?
3. **Patient conflicts**: Does this slot overlap with any of the patient's existing confirmed bookings?

---

## 🛑 Tradeoffs & What Breaks First Under Load

### What breaks first?
The pessimistic locking approach (`SELECT ... FOR UPDATE` in PostgreSQL, or serialized writes in SQLite) means that concurrent checkouts trying to book the **same caregiver on the same date** will block each other. 
If the platform scales to thousands of concurrent users trying to book the same popular caregiver, database lock contention will cause timeouts.

### What I would do differently with more time:
1. **Event Sourcing / Booking Queue**: Instead of synchronous pessimistic locking, place checkouts into a message queue (Kafka/RabbitMQ) and process them sequentially per caregiver. The UI would say "Processing..." and receive a webhook/WebSocket notification when confirmed.
2. **Caching for Availability**: The `GET /slots/available` query calculates availability on the fly. I would use Redis to cache caregiver schedules (represented as bitmasks or interval trees) for much faster reads.
3. **Authentication**: Implement a proper JWT auth flow. Currently, the patient ID is hardcoded for demonstration purposes.
4. **Timezones**: Currently, times are handled as simple strings (`HH:MM`). In a real system, all times should be `TIMESTAMPTZ` mapped to the patient's and caregiver's local timezones.
