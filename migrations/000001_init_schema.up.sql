BEGIN;
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(20) NOT NULL DEFAULT 'GUEST' CHECK (role IN ('GUEST', 'MANAGER')),
    full_name VARCHAR(200) NOT NULL CHECK (btrim(full_name) <> ''),
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30),
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE hotels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL CHECK (btrim(name) <> ''),
    city VARCHAR(100) NOT NULL CHECK (btrim(city) <> ''),
    address VARCHAR(300) NOT NULL CHECK (btrim(address) <> ''),
    rating NUMERIC(3,2) NOT NULL DEFAULT 0 CHECK (rating BETWEEN 0 AND 5),
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (city, address, name)
);
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE RESTRICT,
    room_number VARCHAR(20) NOT NULL CHECK (btrim(room_number) <> ''),
    category VARCHAR(20) NOT NULL CHECK (category IN ('STANDARD', 'LUXE', 'SUITE')),
    price_per_night NUMERIC(12,2) NOT NULL CHECK (price_per_night >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE'
        CHECK (status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE')),
    capacity INT NOT NULL CHECK (capacity > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (hotel_id, room_number)
);
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    total_cost NUMERIC(12,2) NOT NULL CHECK (total_cost >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED'
        CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_booking_period CHECK (check_out_date > check_in_date)
);
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, hotel_id)
);
-- UNIQUE (hotel_id, room_number) already indexes the rooms.hotel_id FK.
-- UNIQUE (user_id, hotel_id) already indexes the reviews.user_id FK.
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_room_period ON bookings(room_id, check_in_date, check_out_date);
CREATE INDEX idx_reviews_hotel_id ON reviews(hotel_id);
COMMIT;
