-- daily spark: recap, feedback, exercise picks and notes (Supabase, free tier).
-- Paste into Supabase → SQL Editor → Run. Replace these first:
--   __OWNER_EMAIL__  the email you sign in with on the page (Menu > This device); only that account can add or read rows
--   __READ_KEY__     lets the morning Worker read entries (kept in your private profile.yaml)
-- The public anon key alone cannot read or change anything. Already set up with the old write key? Run signin.sql instead.

create table if not exists public.recaps   (id bigserial primary key, day date not null, body text not null check (length(body) <= 4000), created_at timestamptz not null default now());
create table if not exists public.feedback (id bigserial primary key, day date not null, item text not null check (length(item) <= 20), value text not null check (value in ('useful','knew','notme','deeper','')), created_at timestamptz not null default now());
create table if not exists public.picks    (id bigserial primary key, day date not null, exercise text not null check (exercise in ('work','write','build','')), created_at timestamptz not null default now());
create table if not exists public.notes    (id bigserial primary key, day date not null, item text not null check (length(item) <= 20), cid text check (cid is null or length(cid) <= 40), body text not null check (length(body) <= 2000), created_at timestamptz not null default now());

alter table public.recaps   enable row level security;
alter table public.feedback enable row level security;
alter table public.picks    enable row level security;
alter table public.notes    enable row level security;

create or replace function public.ds_owner() returns boolean language sql stable as $$
  select lower(coalesce(auth.jwt() ->> 'email', '')) = lower('__OWNER_EMAIL__')
$$;

do $$ declare t text; begin
  foreach t in array array['recaps', 'feedback', 'picks', 'notes'] loop
    execute format('drop policy if exists "owner insert" on public.%I', t);
    execute format('drop policy if exists "owner read" on public.%I', t);
    execute format('create policy "owner insert" on public.%I for insert to authenticated with check (public.ds_owner())', t);
    execute format('create policy "owner read" on public.%I for select to authenticated using (public.ds_owner())', t);
  end loop;
end $$;
-- No update / delete policies: an edit or a removal is a new row (latest row per note wins).

create or replace function public.ds_recent(token text, days int default 7) returns json
language plpgsql security definer set search_path = public as $$
begin
  if token is distinct from '__READ_KEY__' then raise exception 'not allowed'; end if;
  return json_build_object(
    'recaps',   (select coalesce(json_agg(r order by r.created_at), '[]') from recaps r   where r.created_at > now() - make_interval(days => days)),
    'feedback', (select coalesce(json_agg(f order by f.created_at), '[]') from feedback f where f.created_at > now() - make_interval(days => days)),
    'picks',    (select coalesce(json_agg(p order by p.created_at), '[]') from picks p    where p.created_at > now() - make_interval(days => days)),
    'notes',    (select coalesce(json_agg(n order by n.created_at), '[]') from notes n    where n.created_at > now() - make_interval(days => days))
  );
end $$;
revoke all on function public.ds_recent(text, int) from public;
grant execute on function public.ds_recent(text, int) to anon;
