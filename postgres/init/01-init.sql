-- 1. Kimlik Doğrulama (Şifreler)
CREATE TABLE IF NOT EXISTS radcheck (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '==',
    value VARCHAR(253) NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS radcheck_username_idx ON radcheck (username);

-- 2. Grup Kontrol (FreeRADIUS'un hata verdiği tablo)
CREATE TABLE IF NOT EXISTS radgroupcheck (
    id SERIAL PRIMARY KEY,
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '==',
    value VARCHAR(253) NOT NULL DEFAULT ''
);

-- 3. Grup Yetki (VLAN Atamaları)
CREATE TABLE IF NOT EXISTS radgroupreply (
    id SERIAL PRIMARY KEY,
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    attribute VARCHAR(64) NOT NULL DEFAULT '',
    op VARCHAR(2) NOT NULL DEFAULT '=',
    value VARCHAR(253) NOT NULL DEFAULT ''
);

-- 4. Kullanıcı-Grup İlişkisi
CREATE TABLE IF NOT EXISTS radusergroup (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 1
);

-- 5. Accounting (Oturum Kayıtları) 
CREATE TABLE IF NOT EXISTS radacct (
    radacctid BIGSERIAL PRIMARY KEY,
    acctsessionid VARCHAR(64) NOT NULL DEFAULT '',
    acctuniqueid VARCHAR(32) NOT NULL UNIQUE, 
    username VARCHAR(64) NOT NULL DEFAULT '',
    groupname VARCHAR(64) NOT NULL DEFAULT '',
    realm VARCHAR(64) DEFAULT '',
    nasipaddress INET NOT NULL,
    nasportid VARCHAR(15) DEFAULT NULL,
    nasporttype VARCHAR(32) DEFAULT NULL,
    acctstarttime TIMESTAMP WITH TIME ZONE,
    acctupdatetime TIMESTAMP WITH TIME ZONE, 
    acctstoptime TIMESTAMP WITH TIME ZONE,
    acctinterval BIGINT,
    acctsessiontime BIGINT,
    acctauthentic VARCHAR(32),                
    connectinfo_start VARCHAR(50),            
    connectinfo_stop VARCHAR(50),             
    acctterminatecause VARCHAR(32) DEFAULT '',
    acctstatustype VARCHAR(32) DEFAULT '',
    acctinputoctets BIGINT,
    acctoutputoctets BIGINT,
    calledstationid VARCHAR(50) NOT NULL DEFAULT '',
    callingstationid VARCHAR(50) NOT NULL DEFAULT '',
    servicetype VARCHAR(32),                  
    framedprotocol VARCHAR(32),               
    framedipaddress INET DEFAULT NULL,
    framedipv6address INET,                   
    framedipv6prefix INET,                   
    framedinterfaceid VARCHAR(44),           
    delegatedipv6prefix INET                  
);

-- 6. Post-Auth Logları (Giriş Denemeleri)
CREATE TABLE IF NOT EXISTS radpostauth (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL DEFAULT '',
    pass VARCHAR(64) NOT NULL DEFAULT '',
    reply VARCHAR(32) NOT NULL DEFAULT '',
    authdate TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 7. Senin Özel MAB Tablon
CREATE TABLE IF NOT EXISTS mac_auth (
    id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    device_name VARCHAR(64),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OTOMATİK TEST VERİLERİ

-- Kullanıcılar
INSERT INTO radcheck (username, attribute, op, value) VALUES
('admin', 'MD5-Password', ':=', md5('admin123')),
('employee', 'MD5-Password', ':=', md5('emp123')),
('AABBCCDDEEFF', 'Cleartext-Password', ':=', 'AABBCCDDEEFF')
ON CONFLICT DO NOTHING;

-- Gruplar
INSERT INTO radusergroup (username, groupname) VALUES
('admin', 'admin_grp'),
('employee', 'emp_grp'),
('AABBCCDDEEFF', 'emp_grp')
ON CONFLICT DO NOTHING;

-- VLAN'lar
INSERT INTO radgroupreply (groupname, attribute, op, value) VALUES
('admin_grp', 'Tunnel-Type', ':=', 'VLAN'),
('admin_grp', 'Tunnel-Medium-Type', ':=', 'IEEE-802'),
('admin_grp', 'Tunnel-Private-Group-Id', ':=', '100'),
('emp_grp', 'Tunnel-Type', ':=', 'VLAN'),
('emp_grp', 'Tunnel-Medium-Type', ':=', 'IEEE-802'),
('emp_grp', 'Tunnel-Private-Group-Id', ':=', '200')
ON CONFLICT DO NOTHING;