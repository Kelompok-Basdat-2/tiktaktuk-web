-- ============================================================
-- TikTakTuk Database Dump TK03
-- Bundled seed data — executed by `python manage.py seed_db`
-- ============================================================

-- ============================================================
-- DDL: Drop Tables (in reverse dependency order)
-- ============================================================
DROP TABLE IF EXISTS HAS_RELATIONSHIP;
DROP TABLE IF EXISTS ORDER_PROMOTION;
DROP TABLE IF EXISTS TICKET;
DROP TABLE IF EXISTS "ORDER";
DROP TABLE IF EXISTS PROMOTION;
DROP TABLE IF EXISTS TICKET_CATEGORY;
DROP TABLE IF EXISTS EVENT_ARTIST;
DROP TABLE IF EXISTS EVENT;
DROP TABLE IF EXISTS SEAT;
DROP TABLE IF EXISTS ARTIST;
DROP TABLE IF EXISTS VENUE;
DROP TABLE IF EXISTS ORGANIZER;
DROP TABLE IF EXISTS CUSTOMER;
DROP TABLE IF EXISTS ACCOUNT_ROLE;
DROP TABLE IF EXISTS ROLE;
DROP TABLE IF EXISTS USER_ACCOUNT;

-- ============================================================
-- DDL: Create Tables
-- ============================================================

-- Table 1: USER_ACCOUNT
CREATE TABLE IF NOT EXISTS USER_ACCOUNT (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: ROLE
CREATE TABLE IF NOT EXISTS ROLE (
    role_id VARCHAR(36) PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Table 3: ACCOUNT_ROLE (composite PK: role_id + user_id)
CREATE TABLE IF NOT EXISTS ACCOUNT_ROLE (
    role_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, user_id),
    FOREIGN KEY (role_id) REFERENCES ROLE(role_id),
    FOREIGN KEY (user_id) REFERENCES USER_ACCOUNT(user_id)
);

-- Table 4: CUSTOMER
CREATE TABLE IF NOT EXISTS CUSTOMER (
    customer_id VARCHAR(36) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    user_id VARCHAR(36) NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES USER_ACCOUNT(user_id)
);

-- Table 5: ORGANIZER
CREATE TABLE IF NOT EXISTS ORGANIZER (
    organizer_id VARCHAR(36) PRIMARY KEY,
    organizer_name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(100),
    user_id VARCHAR(36) NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES USER_ACCOUNT(user_id)
);

-- Table 6: VENUE
CREATE TABLE IF NOT EXISTS VENUE (
    venue_id VARCHAR(36) PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL
);

-- Table 7: SEAT
CREATE TABLE IF NOT EXISTS SEAT (
    seat_id VARCHAR(36) PRIMARY KEY,
    section VARCHAR(50) NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    row_number VARCHAR(10) NOT NULL,
    venue_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (venue_id) REFERENCES VENUE(venue_id)
);

-- Table 8: EVENT
CREATE TABLE IF NOT EXISTS EVENT (
    event_id VARCHAR(36) PRIMARY KEY,
    event_datetime TIMESTAMP NOT NULL,
    event_title VARCHAR(200) NOT NULL,
    venue_id VARCHAR(36) NOT NULL,
    organizer_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (venue_id) REFERENCES VENUE(venue_id),
    FOREIGN KEY (organizer_id) REFERENCES ORGANIZER(organizer_id)
);

-- Table 9: ARTIST
CREATE TABLE IF NOT EXISTS ARTIST (
    artist_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    genre VARCHAR(100)
);

-- Table 10: EVENT_ARTIST (composite PK: event_id + artist_id)
CREATE TABLE IF NOT EXISTS EVENT_ARTIST (
    event_id VARCHAR(36) NOT NULL,
    artist_id VARCHAR(36) NOT NULL,
    role VARCHAR(100),
    PRIMARY KEY (event_id, artist_id),
    FOREIGN KEY (event_id) REFERENCES EVENT(event_id),
    FOREIGN KEY (artist_id) REFERENCES ARTIST(artist_id)
);

-- Table 11: TICKET_CATEGORY
CREATE TABLE IF NOT EXISTS TICKET_CATEGORY (
    category_id VARCHAR(36) PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    quota INTEGER NOT NULL CHECK (quota > 0),
    price NUMERIC NOT NULL CHECK (price >= 0),
    tevent_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (tevent_id) REFERENCES EVENT(event_id)
);

-- Table 12: ORDER
CREATE TABLE IF NOT EXISTS "ORDER" (
    order_id VARCHAR(36) PRIMARY KEY,
    order_date TIMESTAMP NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    total_amount NUMERIC NOT NULL CHECK (total_amount >= 0),
    customer_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES CUSTOMER(customer_id)
);

-- Table 13: TICKET
CREATE TABLE IF NOT EXISTS TICKET (
    ticket_id VARCHAR(36) PRIMARY KEY,
    ticket_code VARCHAR(100) NOT NULL UNIQUE,
    tcategory_id VARCHAR(36) NOT NULL,
    torder_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (tcategory_id) REFERENCES TICKET_CATEGORY(category_id),
    FOREIGN KEY (torder_id) REFERENCES "ORDER" (order_id)
);

-- Table 14: HAS_RELATIONSHIP (composite PK: seat_id + ticket_id)
CREATE TABLE IF NOT EXISTS HAS_RELATIONSHIP (
    seat_id VARCHAR(36) NOT NULL,
    ticket_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (seat_id, ticket_id),
    FOREIGN KEY (seat_id) REFERENCES SEAT(seat_id),
    FOREIGN KEY (ticket_id) REFERENCES TICKET(ticket_id)
);

-- Table 15: PROMOTION
CREATE TABLE IF NOT EXISTS PROMOTION (
    promotion_id VARCHAR(36) PRIMARY KEY,
    promo_code VARCHAR(50) NOT NULL UNIQUE,
    discount_type VARCHAR(20) NOT NULL,
    discount_value NUMERIC NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    usage_limit INTEGER NOT NULL
);

-- Table 16: ORDER_PROMOTION
CREATE TABLE IF NOT EXISTS ORDER_PROMOTION (
    order_promotion_id VARCHAR(36) PRIMARY KEY,
    promotion_id VARCHAR(36) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    FOREIGN KEY (promotion_id) REFERENCES PROMOTION(promotion_id),
    FOREIGN KEY (order_id) REFERENCES "ORDER" (order_id)
);

-- ============================================================
-- DUMMY DATA: ROLE (3 records)
-- ============================================================
INSERT INTO ROLE (role_id, role_name) VALUES
('r-001', 'administrator'),
('r-002', 'organizer'),
('r-003', 'customer');

-- ============================================================
-- DUMMY DATA: USER_ACCOUNT (18 records - exceeding 12)
-- ============================================================
INSERT INTO USER_ACCOUNT (user_id, username, password) VALUES
('u-001', 'admin_reva', 'hashed_password_123'),
('u-002', 'admin_andi', 'hashed_password_456'),
('u-003', 'admin_budi', 'hashed_password_789'),
('u-004', 'org_soundfest', 'hashed_password_abc'),
('u-005', 'org_techindo', 'hashed_password_def'),
('u-006', 'org_comedyclub', 'hashed_password_ghi'),
('u-007', 'org_festpro', 'hashed_password_jkl'),
('u-008', 'cust_budi', 'hashed_password_mno'),
('u-009', 'cust_siti', 'hashed_password_pqr'),
('u-010', 'cust_rina', 'hashed_password_stu'),
('u-011', 'cust_joko', 'hashed_password_vwx'),
('u-012', 'cust_dewi', 'hashed_password_yz1'),
('u-013', 'org_musicfest', 'hashed_password_abc2'),
('u-014', 'cust_ange', 'hashed_password_abc3'),
('u-015', 'cust_kevin', 'hashed_password_abc4'),
('u-016', 'cust_lina', 'hashed_password_abc5'),
('u-017', 'cust_michael', 'hashed_password_abc6'),
('u-018', 'cust_nadia', 'hashed_password_abc7');

-- ============================================================
-- DUMMY DATA: ACCOUNT_ROLE (21 records - exceeding 15)
-- ============================================================
INSERT INTO ACCOUNT_ROLE (role_id, user_id) VALUES
('r-001', 'u-001'),
('r-001', 'u-002'),
('r-001', 'u-003'),
('r-002', 'u-004'),
('r-002', 'u-005'),
('r-002', 'u-006'),
('r-002', 'u-007'),
('r-003', 'u-008'),
('r-003', 'u-009'),
('r-003', 'u-010'),
('r-003', 'u-011'),
('r-003', 'u-012'),
('r-002', 'u-013'),
('r-003', 'u-014'),
('r-003', 'u-015'),
('r-003', 'u-016'),
('r-003', 'u-017'),
('r-003', 'u-018'),
('r-003', 'u-004'),
('r-003', 'u-005'),
('r-003', 'u-006');

-- ============================================================
-- DUMMY DATA: CUSTOMER (10 records - exceeding 6)
-- ============================================================
INSERT INTO CUSTOMER (customer_id, full_name, phone_number, user_id) VALUES
('cust-001', 'Budi Santoso', '081234567890', 'u-008'),
('cust-002', 'Siti Rahayu', '081234567891', 'u-009'),
('cust-003', 'Rina Wati', '081234567892', 'u-010'),
('cust-004', 'Joko Pramono', '081234567893', 'u-011'),
('cust-005', 'Dewi Lestari', '081234567894', 'u-012'),
('cust-006', 'Fajar Nugroho', '081234567895', 'u-004'),
('cust-007', 'Angelina Putri', '081234567896', 'u-014'),
('cust-008', 'Kevin Wijaya', '081234567897', 'u-015'),
('cust-009', 'Lina Hartati', '081234567898', 'u-016'),
('cust-010', 'Michael Tanoto', '081234567899', 'u-017');

-- ============================================================
-- DUMMY DATA: ORGANIZER (6 records - exceeding 4)
-- ============================================================
INSERT INTO ORGANIZER (organizer_id, organizer_name, contact_email, user_id) VALUES
('org-001', 'SoundFest Indonesia', 'soundfest@organizer.com', 'u-004'),
('org-002', 'TechIndo Events', 'techindo@organizer.com', 'u-005'),
('org-003', 'Comedy Club Indonesia', 'comedyclub@organizer.com', 'u-006'),
('org-004', 'FestPro Management', 'festpro@organizer.com', 'u-007'),
('org-005', 'MusicFest Organizer', 'musicfest@organizer.com', 'u-013');

-- ============================================================
-- DUMMY DATA: VENUE (8 records - exceeding 5)
-- ============================================================
INSERT INTO VENUE (venue_id, venue_name, capacity, address, city) VALUES
('ven-001', 'Jakarta Convention Center', 5000, 'Jl. Jend. Gatot Subroto No.1', 'Jakarta'),
('ven-002', 'Gelora Bung Karno Stadium', 8000, 'Jl. Tambak No.2', 'Jakarta'),
('ven-003', 'Bandung Techno Park', 2000, 'Jl. Gegerkalong Hilir', 'Bandung'),
('ven-004', 'Surabaya Grand Ballroom', 3000, 'Jl. Pemuda No.100', 'Surabaya'),
('ven-005', 'Bali Nusa Dua Theater', 1500, 'Kawasan Nusa Dua', 'Bali'),
('ven-006', 'Yogyakarta Borobudur Hall', 2500, 'Jl. Solo No.42', 'Yogyakarta'),
('ven-007', 'Semarang Java Mall Atrium', 1800, 'Jl. Pemuda No.88', 'Semarang'),
('ven-008', 'Makassar Four Points', 1200, 'Jl. Sultan Hasanuddin No.10', 'Makassar');

-- ============================================================
-- DUMMY DATA: SEAT (45 records - exceeding 30)
-- ============================================================
INSERT INTO SEAT (seat_id, section, seat_number, row_number, venue_id) VALUES
-- Venue 1: Jakarta Convention Center (Reserved Seating)
('seat-001', 'WVIP', '1', 'A', 'ven-001'),
('seat-002', 'WVIP', '2', 'A', 'ven-001'),
('seat-003', 'VIP', '1', 'B', 'ven-001'),
('seat-004', 'VIP', '2', 'B', 'ven-001'),
('seat-005', 'CAT1', '1', 'C', 'ven-001'),
('seat-006', 'CAT1', '2', 'C', 'ven-001'),
('seat-007', 'CAT1', '3', 'C', 'ven-001'),
('seat-008', 'CAT2', '1', 'D', 'ven-001'),
('seat-009', 'CAT2', '2', 'D', 'ven-001'),
('seat-010', 'CAT2', '3', 'D', 'ven-001'),
-- Venue 2: Gelora Bung Karno (Reserved Seating)
('seat-011', 'TRIBUNE', '1', 'A', 'ven-002'),
('seat-012', 'TRIBUNE', '2', 'A', 'ven-002'),
('seat-013', 'TRIBUNE', '3', 'A', 'ven-002'),
('seat-014', 'WEST', '1', 'B', 'ven-002'),
('seat-015', 'WEST', '2', 'B', 'ven-002'),
('seat-016', 'EAST', '1', 'B', 'ven-002'),
('seat-017', 'EAST', '2', 'B', 'ven-002'),
('seat-018', 'NORTH', '1', 'C', 'ven-002'),
('seat-019', 'NORTH', '2', 'C', 'ven-002'),
('seat-020', 'NORTH', '3', 'C', 'ven-002'),
-- Venue 3: Bandung Techno Park (Free Seating)
('seat-021', 'FESTIVAL', '1', 'A', 'ven-003'),
('seat-022', 'FESTIVAL', '2', 'A', 'ven-003'),
('seat-023', 'FESTIVAL', '3', 'A', 'ven-003'),
('seat-024', 'FESTIVAL', '4', 'A', 'ven-003'),
('seat-025', 'REGULAR', '1', 'B', 'ven-003'),
('seat-026', 'REGULAR', '2', 'B', 'ven-003'),
('seat-027', 'REGULAR', '3', 'B', 'ven-003'),
('seat-028', 'REGULAR', '4', 'B', 'ven-003'),
('seat-029', 'REGULAR', '5', 'B', 'ven-003'),
('seat-030', 'REGULAR', '6', 'B', 'ven-003'),
-- Venue 6: Yogyakarta Borobudur Hall
('seat-031', 'VIP', '1', 'A', 'ven-006'),
('seat-032', 'VIP', '2', 'A', 'ven-006'),
('seat-033', 'CAT1', '1', 'B', 'ven-006'),
('seat-034', 'CAT1', '2', 'B', 'ven-006'),
('seat-035', 'CAT2', '1', 'C', 'ven-006'),
('seat-036', 'CAT2', '2', 'C', 'ven-006'),
-- Venue 7: Semarang Java Mall
('seat-037', 'MAIN', '1', 'A', 'ven-007'),
('seat-038', 'MAIN', '2', 'A', 'ven-007'),
('seat-039', 'CAT1', '1', 'B', 'ven-007'),
('seat-040', 'CAT1', '2', 'B', 'ven-007'),
('seat-041', 'CAT2', '1', 'C', 'ven-007'),
('seat-042', 'CAT2', '2', 'C', 'ven-007'),
-- Venue 8: Makassar Four Points
('seat-043', 'VIP', '1', 'A', 'ven-008'),
('seat-044', 'CAT1', '1', 'B', 'ven-008'),
('seat-045', 'CAT2', '1', 'C', 'ven-008');

-- ============================================================
-- DUMMY DATA: EVENT (10 records - exceeding 6)
-- ============================================================
INSERT INTO EVENT (event_id, event_datetime, event_title, venue_id, organizer_id) VALUES
('evt-001', '2026-05-15 19:00:00', 'SoundFest 2026', 'ven-001', 'org-001'),
('evt-002', '2026-05-20 20:00:00', 'Tech Conference Indonesia', 'ven-003', 'org-002'),
('evt-003', '2026-06-01 18:30:00', 'Stand Up Comedy Night', 'ven-004', 'org-003'),
('evt-004', '2026-06-10 15:00:00', 'Rock Festival Java', 'ven-002', 'org-001'),
('evt-005', '2026-06-20 19:00:00', 'Digital Innovation Summit', 'ven-003', 'org-002'),
('evt-006', '2026-07-05 20:00:00', 'Comedy Festival Bali', 'ven-005', 'org-003'),
('evt-007', '2026-07-15 19:00:00', 'Java Jazz Festival', 'ven-001', 'org-005'),
('evt-008', '2026-08-10 16:00:00', 'Music Awards Indonesia', 'ven-002', 'org-005'),
('evt-009', '2026-08-20 19:00:00', 'Startup Summit Yogyakarta', 'ven-006', 'org-002'),
('evt-010', '2026-09-05 18:00:00', 'Comedy Night Surabaya', 'ven-004', 'org-003');

-- ============================================================
-- DUMMY DATA: ARTIST (12 records - exceeding 8)
-- ============================================================
INSERT INTO ARTIST (artist_id, name, genre) VALUES
('art-001', 'Raisa', 'Pop'),
('art-002', 'Hindia', 'Indie'),
('art-003', 'Fiersa Besari', 'Indie Folk'),
('art-004', 'Tulus', 'Pop'),
('art-005', 'Maliq & The Essential', 'Soul Jazz'),
('art-006', 'Barry Likumahuwa', 'Jazz'),
('art-007', 'Mamet', 'Comedy'),
('art-008', 'Cak Lontong', 'Comedy'),
('art-009', 'Isyana Sarasvati', 'Pop'),
('art-010', 'Nadin Amizah', 'Indie Folk'),
('art-011', 'Feast', 'Indie Rock'),
('art-012', 'Pamungkas', 'Pop');

-- ============================================================
-- DUMMY DATA: EVENT_ARTIST (18 records - exceeding 12)
-- ============================================================
INSERT INTO EVENT_ARTIST (event_id, artist_id, role) VALUES
('evt-001', 'art-001', 'Headliner'),
('evt-001', 'art-002', 'Supporting'),
('evt-001', 'art-004', 'Special Guest'),
('evt-001', 'art-009', 'Supporting'),
('evt-002', 'art-003', 'Speaker'),
('evt-002', 'art-010', 'Speaker'),
('evt-003', 'art-007', 'Performer'),
('evt-003', 'art-008', 'Performer'),
('evt-004', 'art-002', 'Headliner'),
('evt-004', 'art-003', 'Supporting'),
('evt-004', 'art-005', 'Supporting'),
('evt-004', 'art-011', 'Special Guest'),
('evt-005', 'art-006', 'Performer'),
('evt-005', 'art-010', 'Performer'),
('evt-006', 'art-007', 'Headliner'),
('evt-006', 'art-008', 'Supporting'),
('evt-007', 'art-005', 'Headliner'),
('evt-007', 'art-006', 'Supporting'),
('evt-007', 'art-009', 'Special Guest'),
('evt-008', 'art-012', 'Headliner'),
('evt-008', 'art-001', 'Special Guest'),
('evt-009', 'art-003', 'Speaker'),
('evt-010', 'art-008', 'Headliner');

-- ============================================================
-- DUMMY DATA: TICKET_CATEGORY (20 records - exceeding 14)
-- ============================================================
INSERT INTO TICKET_CATEGORY (category_id, category_name, quota, price, tevent_id) VALUES
-- Event 1: SoundFest 2026
('tc-001', 'WVIP', 50, 2500000.00, 'evt-001'),
('tc-002', 'VIP', 200, 1500000.00, 'evt-001'),
('tc-003', 'Category 1', 500, 750000.00, 'evt-001'),
('tc-004', 'Category 2', 1000, 350000.00, 'evt-001'),
-- Event 2: Tech Conference
('tc-005', 'Premium', 100, 500000.00, 'evt-002'),
('tc-006', 'Standard', 400, 250000.00, 'evt-002'),
('tc-007', 'Student', 500, 100000.00, 'evt-002'),
-- Event 3: Comedy Night
('tc-008', 'Front Row', 30, 1000000.00, 'evt-003'),
('tc-009', 'Standard', 200, 500000.00, 'evt-003'),
-- Event 4: Rock Festival
('tc-010', 'VIP', 100, 2000000.00, 'evt-004'),
('tc-011', 'Festival', 1500, 500000.00, 'evt-004'),
-- Event 5: Digital Summit
('tc-012', 'Corporate', 50, 1000000.00, 'evt-005'),
('tc-013', 'Individual', 150, 350000.00, 'evt-005'),
-- Event 6: Comedy Bali
('tc-014', 'VVIP', 20, 1500000.00, 'evt-006'),
('tc-015', 'VIP', 50, 1000000.00, 'evt-006'),
('tc-016', 'Regular', 200, 500000.00, 'evt-006'),
-- Event 7: Java Jazz
('tc-017', 'VVIP', 30, 3000000.00, 'evt-007'),
('tc-018', 'VIP', 150, 2000000.00, 'evt-007'),
('tc-019', 'Festival', 800, 750000.00, 'evt-007'),
-- Event 8: Music Awards
('tc-020', 'VIP', 100, 2500000.00, 'evt-008');

-- ============================================================
-- DUMMY DATA: ORDER (18 records - exceeding 12)
-- ============================================================
INSERT INTO "ORDER" (order_id, order_date, payment_status, total_amount, customer_id) VALUES
('ord-001', '2026-04-01 10:30:00', 'Lunas', 2500000.00, 'cust-001'),
('ord-002', '2026-04-02 14:15:00', 'Lunas', 1500000.00, 'cust-002'),
('ord-003', '2026-04-03 09:45:00', 'Pending', 750000.00, 'cust-003'),
('ord-004', '2026-04-04 16:20:00', 'Lunas', 500000.00, 'cust-001'),
('ord-005', '2026-04-05 11:00:00', 'Lunas', 1000000.00, 'cust-004'),
('ord-006', '2026-04-06 13:30:00', 'Pending', 350000.00, 'cust-005'),
('ord-007', '2026-04-07 15:45:00', 'Lunas', 2000000.00, 'cust-002'),
('ord-008', '2026-04-08 08:00:00', 'Pending', 500000.00, 'cust-003'),
('ord-009', '2026-04-09 17:30:00', 'Lunas', 500000.00, 'cust-004'),
('ord-010', '2026-04-10 12:00:00', 'Dibatalkan', 1000000.00, 'cust-005'),
('ord-011', '2026-04-11 10:15:00', 'Lunas', 250000.00, 'cust-001'),
('ord-012', '2026-04-12 14:45:00', 'Lunas', 1500000.00, 'cust-006'),
('ord-013', '2026-04-13 09:00:00', 'Lunas', 3000000.00, 'cust-007'),
('ord-014', '2026-04-14 11:30:00', 'Pending', 2000000.00, 'cust-008'),
('ord-015', '2026-04-15 16:00:00', 'Lunas', 750000.00, 'cust-009'),
('ord-016', '2026-04-16 13:45:00', 'Lunas', 500000.00, 'cust-010'),
('ord-017', '2026-04-17 08:30:00', 'Pending', 350000.00, 'cust-007'),
('ord-018', '2026-04-18 14:00:00', 'Lunas', 2000000.00, 'cust-008');

-- ============================================================
-- DUMMY DATA: TICKET (30 records - exceeding 20)
-- ============================================================
INSERT INTO TICKET (ticket_id, ticket_code, tcategory_id, torder_id) VALUES
('tkt-001', 'TKT-SF-001', 'tc-001', 'ord-001'),
('tkt-002', 'TKT-SF-002', 'tc-001', 'ord-001'),
('tkt-003', 'TKT-VIP-001', 'tc-002', 'ord-002'),
('tkt-004', 'TKT-C1-001', 'tc-003', 'ord-003'),
('tkt-005', 'TKT-C2-001', 'tc-004', 'ord-004'),
('tkt-006', 'TKT-FR-001', 'tc-008', 'ord-005'),
('tkt-007', 'TKT-FR-002', 'tc-008', 'ord-005'),
('tkt-008', 'TKT-VIP-002', 'tc-010', 'ord-007'),
('tkt-009', 'TKT-VIP-003', 'tc-010', 'ord-007'),
('tkt-010', 'TKT-FEST-001', 'tc-011', 'ord-007'),
('tkt-011', 'TKT-FEST-002', 'tc-011', 'ord-007'),
('tkt-012', 'TKT-FEST-003', 'tc-011', 'ord-007'),
('tkt-013', 'TKT-FEST-004', 'tc-011', 'ord-007'),
('tkt-014', 'TKT-CORP-001', 'tc-012', 'ord-006'),
('tkt-015', 'TKT-IND-001', 'tc-013', 'ord-008'),
('tkt-016', 'TKT-IND-002', 'tc-013', 'ord-008'),
('tkt-017', 'TKT-FEST-005', 'tc-011', 'ord-009'),
('tkt-018', 'TKT-FEST-006', 'tc-011', 'ord-009'),
('tkt-019', 'TKT-STD-001', 'tc-009', 'ord-010'),
('tkt-020', 'TKT-STD-002', 'tc-009', 'ord-010'),
('tkt-021', 'TKT-VVIP-001', 'tc-017', 'ord-013'),
('tkt-022', 'TKT-VIP-J001', 'tc-018', 'ord-013'),
('tkt-023', 'TKT-FEST-J001', 'tc-019', 'ord-013'),
('tkt-024', 'TKT-FEST-J002', 'tc-019', 'ord-013'),
('tkt-025', 'TKT-VIP-M001', 'tc-020', 'ord-018'),
('tkt-026', 'TKT-IND-S001', 'tc-016', 'ord-014'),
('tkt-027', 'TKT-IND-S002', 'tc-016', 'ord-014'),
('tkt-028', 'TKT-STD-J001', 'tc-019', 'ord-015'),
('tkt-029', 'TKT-FEST-J003', 'tc-019', 'ord-016'),
('tkt-030', 'TKT-IND-S003', 'tc-016', 'ord-017');

-- ============================================================
-- DUMMY DATA: HAS_RELATIONSHIP (15 records - exceeding 10)
-- Seat assignments for tickets with reserved seating
-- ============================================================
INSERT INTO HAS_RELATIONSHIP (seat_id, ticket_id) VALUES
('seat-001', 'tkt-001'),
('seat-002', 'tkt-002'),
('seat-003', 'tkt-003'),
('seat-008', 'tkt-004'),
('seat-011', 'tkt-008'),
('seat-012', 'tkt-009'),
('seat-018', 'tkt-010'),
('seat-019', 'tkt-011'),
('seat-020', 'tkt-012'),
('seat-014', 'tkt-013'),
('seat-031', 'tkt-021'),
('seat-032', 'tkt-022'),
('seat-033', 'tkt-023'),
('seat-034', 'tkt-024'),
('seat-037', 'tkt-025');

-- ============================================================
-- DUMMY DATA: PROMOTION (10 records - exceeding 6)
-- ============================================================
INSERT INTO PROMOTION (promotion_id, promo_code, discount_type, discount_value, start_date, end_date, usage_limit) VALUES
('promo-001', 'RAKSAFULL20', 'PERCENTAGE', 20.00, '2026-04-01', '2026-12-31', 100),
('promo-002', 'FLAT100K', 'NOMINAL', 100000.00, '2026-04-01', '2026-12-31', 200),
('promo-003', 'EARLYBIRD', 'PERCENTAGE', 15.00, '2026-03-01', '2026-05-31', 50),
('promo-004', 'TECHFEST', 'PERCENTAGE', 25.00, '2026-04-15', '2026-06-15', 75),
('promo-005', 'COMEDY10', 'NOMINAL', 50000.00, '2026-05-01', '2026-10-31', 150),
('promo-006', 'SIKAT95', 'PERCENTAGE', 10.00, '2026-06-01', '2026-08-31', 300),
('promo-007', 'JAZZ20', 'PERCENTAGE', 20.00, '2026-07-01', '2026-07-31', 100),
('promo-008', 'MUSIC15', 'PERCENTAGE', 15.00, '2026-08-01', '2026-08-31', 150),
('promo-009', 'FLAT75K', 'NOMINAL', 75000.00, '2026-05-01', '2026-09-30', 100),
('promo-010', 'VIP50', 'PERCENTAGE', 50.00, '2026-06-15', '2026-06-30', 25);

-- ============================================================
-- DUMMY DATA: ORDER_PROMOTION (8 records - exceeding 5)
-- ============================================================
INSERT INTO ORDER_PROMOTION (order_promotion_id, promotion_id, order_id) VALUES
('op-001', 'promo-001', 'ord-001'),
('op-002', 'promo-002', 'ord-002'),
('op-003', 'promo-003', 'ord-004'),
('op-004', 'promo-004', 'ord-006'),
('op-005', 'promo-005', 'ord-009'),
('op-006', 'promo-007', 'ord-013'),
('op-007', 'promo-008', 'ord-018'),
('op-008', 'promo-009', 'ord-015');

-- ============================================================
-- End of Dump
-- ============================================================
