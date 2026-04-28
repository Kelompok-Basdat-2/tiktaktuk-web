-- ============================================================
-- TikTakTuk Web - SQL Queries for Core Features
-- DUMMY/PLACEHOLDER - represents required database queries
-- ============================================================

-- ============================================================
-- 1. NAVBAR - Role-based menu queries
-- ============================================================

-- Get navbar items for Guest (unauthenticated)
-- Returns: login/register options only
SELECT 'login' AS menu_item, '/login/' AS url UNION ALL
SELECT 'register', '/register/';

-- Get navbar items for Admin
-- Returns: dashboard, venues, events, artists, categories, tickets, orders, promotions, logout
SELECT menu_item, url FROM navbar_items WHERE role = 'admin';

-- Get navbar items for Organizer
-- Returns: dashboard, venues, events, artists, categories, tickets, orders, logout
SELECT menu_item, url FROM navbar_items WHERE role = 'organizer';

-- Get navbar items for Customer
-- Returns: dashboard, explore events, my tickets, logout
SELECT menu_item, url FROM navbar_items WHERE role = 'customer';

-- ============================================================
-- 2. C - PENGGUNA (User Registration / Create)
-- ============================================================

-- Insert new Role (if not exists)
INSERT INTO role (nama, deskripsi, created_at, updated_at)
VALUES ('admin', 'Administrator dengan akses penuh', NOW(), NOW())
ON CONFLICT (nama) DO NOTHING;

INSERT INTO role (nama, deskripsi, created_at, updated_at)
VALUES ('organizer', 'Penyelenggara acara', NOW(), NOW())
ON CONFLICT (nama) DO NOTHING;

INSERT INTO role (nama, deskripsi, created_at, updated_at)
VALUES ('customer', 'Pengguna biasa / pembeli tiket', NOW(), NOW())
ON CONFLICT (nama) DO NOTHING;

-- Insert new User (Django auth_user)
INSERT INTO auth_user (username, email, password, first_name, last_name, is_active, date_joined)
VALUES ('username_here', 'email@example.com', 'hashed_password_here', 'Nama', 'Lengkap', TRUE, NOW());

-- Insert new Pengguna (linked to User)
INSERT INTO pengguna (user_id, role_id, nama_lengkap, telepon, alamat, created_at, updated_at)
VALUES (
    (SELECT id FROM auth_user WHERE username = 'username_here'),
    (SELECT id FROM role WHERE nama = 'customer'),
    'Nama Lengkap User',
    '081234567890',
    'Alamat lengkap user',
    NOW(),
    NOW()
);

-- Full registration query (transaction)
BEGIN;
    INSERT INTO auth_user (username, email, password, first_name, last_name, is_active, date_joined)
    VALUES ($username, $email, $password_hash, $first_name, $last_name, TRUE, NOW());

    INSERT INTO pengguna (user_id, role_id, nama_lengkap, telepon, alamat, created_at, updated_at)
    VALUES (currval('auth_user_id_seq'), $role_id, $nama_lengkap, $telepon, $alamat, NOW(), NOW());
COMMIT;

-- ============================================================
-- 3. R - LOGIN dan LOGOUT (Authentication queries)
-- ============================================================

-- Verify user credentials for login
SELECT
    u.id,
    u.username,
    u.email,
    u.password,
    p.id AS pengguna_id,
    p.nama_lengkap,
    r.nama AS role
FROM auth_user u
JOIN pengguna p ON p.user_id = u.id
JOIN role r ON r.id = p.role_id
WHERE u.username = $input_username
AND u.is_active = TRUE;

-- Alternative: verify by email
SELECT
    u.id,
    u.username,
    u.email,
    u.password,
    p.id AS pengguna_id,
    r.nama AS role
FROM auth_user u
JOIN pengguna p ON p.user_id = u.id
JOIN role r ON r.id = p.role_id
WHERE u.email = $input_email
AND u.is_active = TRUE;

-- Check if username/email already exists (for registration validation)
SELECT COUNT(*) FROM auth_user WHERE username = $username;
SELECT COUNT(*) FROM auth_user WHERE email = $email;

-- Get session data (for logout tracking)
SELECT * FROM django_session WHERE session_key = $session_key;

-- Delete session (logout)
DELETE FROM django_session WHERE session_key = $session_key;

-- ============================================================
-- 4. R - DASHBOARD PENGGUNA (User Profile Dashboard)
-- ============================================================

-- Get full user profile for dashboard (all roles)
SELECT
    u.id AS user_id,
    u.username,
    u.email,
    u.date_joined,
    p.nama_lengkap,
    p.telepon,
    p.alamat,
    p.created_at AS pengguna_created,
    r.nama AS role,
    r.deskripsi AS role_description
FROM auth_user u
JOIN pengguna p ON p.user_id = u.id
JOIN role r ON r.id = p.role_id
WHERE u.id = $user_id;

-- Get admin dashboard summary
SELECT
    (SELECT COUNT(*) FROM pengguna) AS total_pengguna,
    (SELECT COUNT(*) FROM venue) AS total_venue,
    (SELECT COUNT(*) FROM acara) AS total_event,
    (SELECT COUNT(*) FROM artist) AS total_artist;

-- Get organizer dashboard summary
SELECT
    (SELECT COUNT(*) FROM acara WHERE created_by = $user_id) AS my_events,
    (SELECT COUNT(*) FROM venue WHERE created_by = $user_id) AS my_venues,
    (SELECT COUNT(*) FROM ticket_category WHERE created_by = $user_id) AS my_categories;

-- Get customer dashboard summary
SELECT
    u.username,
    u.email,
    p.nama_lengkap,
    p.telepon,
    p.alamat,
    r.nama AS role
FROM auth_user u
JOIN pengguna p ON p.user_id = u.id
JOIN role r ON r.id = p.role_id
WHERE u.id = $user_id;

-- Get user's ticket orders (customer)
SELECT
    t.id AS ticket_id,
    t.kode_tiket,
    t.status,
    a.nama AS acara,
    v.nama AS venue,
    tc.nama AS kategori,
    t.tanggal_pembelian
FROM ticket t
JOIN acara a ON a.id = t.acara_id
JOIN venue v ON v.id = a.venue_id
JOIN ticket_category tc ON tc.id = t.kategori_id
WHERE t.pengguna_id = $user_id
ORDER BY t.tanggal_pembelian DESC;

-- ============================================================
-- Database Schema Reference (for reference)
-- ============================================================

-- role table
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    nama VARCHAR(50) UNIQUE NOT NULL,
    deskripsi TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- auth_user (Django default)
-- id, username, email, password, first_name, last_name, is_active, is_staff, is_superuser, date_joined, last_login

-- pengguna table
CREATE TABLE pengguna (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES role(id) ON DELETE SET DEFAULT,
    nama_lengkap VARCHAR(255) DEFAULT '',
    telepon VARCHAR(20) DEFAULT '',
    alamat TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- django_session (Django default - for login/logout)
CREATE TABLE django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT,
    expire_date TIMESTAMP
);