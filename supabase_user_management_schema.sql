-- Supabase Database Schema for User and Role Management
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    permissions TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    role_id UUID REFERENCES roles(id),
    department VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('active', 'inactive', 'pending', 'suspended')),
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_role_id ON user_profiles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_status ON user_profiles(status);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Roles: Only authenticated users can read, only admins can modify
CREATE POLICY "Roles are viewable by authenticated users"
    ON roles FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Roles are modifiable by service role only"
    ON roles FOR ALL
    USING (auth.role() = 'service_role');

-- User profiles: Users can view their own profile, admins can view all
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "User profiles are modifiable by service role only"
    ON user_profiles FOR ALL
    USING (auth.role() = 'service_role');

-- Insert default roles
INSERT INTO roles (name, description, permissions) VALUES
    ('Admin', 'Full system access and management capabilities', ARRAY[
        'create_user', 'read_user', 'update_user', 'delete_user',
        'create_role', 'read_role', 'update_role', 'delete_role',
        'create_blog', 'read_blog', 'update_blog', 'delete_blog',
        'manage_system', 'view_analytics'
    ]),
    ('Manager', 'Team management and operational oversight', ARRAY[
        'create_blog', 'read_blog', 'update_blog',
        'read_user', 'view_analytics'
    ]),
    ('User', 'Standard user with basic blog creation access', ARRAY[
        'create_blog', 'read_blog', 'update_blog'
    ])
ON CONFLICT (name) DO NOTHING;

