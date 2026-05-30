-- FamCARE Multi-Service Bulk Scheduler — PostgreSQL Schema
-- This script creates all tables for the booking engine.
-- For development, the ORM creates tables automatically with SQLite.
-- This script is for PostgreSQL production deployment.

-- ═══════════════════════════════════════════════════════════════════════
-- TABLES
-- ═══════════════════════════════════════════════════════════════════════

-- Services: bookable healthcare services with duration and pricing
CREATE TABLE IF NOT EXISTS services (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    duration_minutes INTEGER NOT NULL
        CHECK (duration_minutes > 0 AND duration_minutes % 15 = 0),
    price           DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Caregivers: healthcare professionals
CREATE TABLE IF NOT EXISTS caregivers (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Patients: users who book services
CREATE TABLE IF NOT EXISTS patients (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- M2M: which caregivers can perform which services
CREATE TABLE IF NOT EXISTS caregiver_services (
    caregiver_id UUID REFERENCES caregivers(id) ON DELETE CASCADE,
    service_id   UUID REFERENCES services(id) ON DELETE CASCADE,
    PRIMARY KEY (caregiver_id, service_id)
);

-- Bookings: a single atomic checkout transaction
CREATE TABLE IF NOT EXISTS bookings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id  UUID NOT NULL REFERENCES patients(id),
    total_price DECIMAL(10, 2) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'confirmed'
        CHECK (status IN ('confirmed', 'cancelled')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Booking items: individual slots within a booking
-- duration_minutes and price are SNAPSHOTS from the service at booking time
CREATE TABLE IF NOT EXISTS booking_items (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id       UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    service_id       UUID NOT NULL REFERENCES services(id),
    caregiver_id     UUID NOT NULL REFERENCES caregivers(id),
    slot_date        DATE NOT NULL,
    start_time       TIME NOT NULL
        CHECK (EXTRACT(MINUTE FROM start_time)::int % 15 = 0),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    price            DECIMAL(10, 2) NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════

-- Fast lookup: caregiver's bookings on a specific date (for conflict detection)
CREATE INDEX IF NOT EXISTS idx_booking_items_caregiver_date
    ON booking_items(caregiver_id, slot_date);

-- Fast lookup: patient's bookings on a specific date (for conflict detection)
CREATE INDEX IF NOT EXISTS idx_bookings_patient
    ON bookings(patient_id);

CREATE INDEX IF NOT EXISTS idx_booking_items_booking
    ON booking_items(booking_id);

-- ═══════════════════════════════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════════════════════════════

-- Services
INSERT INTO services (id, name, duration_minutes, price, description) VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Physiotherapy', 60, 1500.00, 'At-home physiotherapy session'),
    ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'Wound Dressing', 30, 500.00, 'Professional wound care'),
    ('c3d4e5f6-a7b8-9012-cdef-123456789012', 'IV Therapy', 45, 2000.00, 'Intravenous fluid administration'),
    ('d4e5f6a7-b8c9-0123-defa-234567890123', 'General Checkup', 30, 800.00, 'Routine health checkup')
ON CONFLICT (id) DO NOTHING;

-- Caregivers
INSERT INTO caregivers (id, name, phone) VALUES
    ('e5f6a7b8-c9d0-1234-efab-345678901234', 'Alice Sharma', '+91-9876543210'),
    ('f6a7b8c9-d0e1-2345-fabc-456789012345', 'Bob Patel', '+91-9876543211'),
    ('a7b8c9d0-e1f2-3456-abcd-567890123456', 'Carol Mehta', '+91-9876543212'),
    ('b8c9d0e1-f2a3-4567-bcde-678901234567', 'David Kumar', '+91-9876543213'),
    ('c9d0e1f2-a3b4-5678-cdef-789012345678', 'Eve Singh', '+91-9876543214')
ON CONFLICT (id) DO NOTHING;

-- Patients
INSERT INTO patients (id, name, phone) VALUES
    ('d0e1f2a3-b4c5-6789-defa-890123456789', 'John Doe', '+91-9123456780'),
    ('e1f2a3b4-c5d6-7890-efab-901234567890', 'Jane Smith', '+91-9123456781'),
    ('f2a3b4c5-d6e7-8901-fabc-012345678901', 'Mike Wilson', '+91-9123456782')
ON CONFLICT (id) DO NOTHING;
