-- Supabase Profiles Table Setup
-- Run this in your Supabase SQL Editor

-- Enable UUID extension (if not already enabled)
create extension if not exists "uuid-ossp";

-- Create profiles table
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique not null,
  created_at timestamptz not null default now()
);

-- Enable Row Level Security
alter table public.profiles enable row level security;

-- RLS Policies: Users can only view, insert, and update their own profile

-- Policy: Select own profile
create policy "Profiles are viewable by owner"
on public.profiles for select
to authenticated
using (id = auth.uid());

-- Policy: Insert own profile
create policy "Profiles can be inserted by owner"
on public.profiles for insert
to authenticated
with check (id = auth.uid());

-- Policy: Update own profile
create policy "Profiles can be updated by owner"
on public.profiles for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

-- Optional: Create an index on username for faster lookups
create index if not exists profiles_username_idx on public.profiles(username);
