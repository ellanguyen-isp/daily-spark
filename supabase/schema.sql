-- daily spark: recap, feedback and exercise picks (Supabase, free tier).
-- Paste into Supabase → SQL Editor → Run. Replace the two keys first:
--   __WRITE_KEY__  lets your browser add entries (saved once per device in the page menu)
--   __READ_KEY__   lets the morning Worker read entries (kept in your private profile.yaml)
-- The public page can only ADD rows, and only with the write key. Nobody can read rows without the read key.

create table if not exists public.recaps   (id bigserial primary key, day date not null, body text not null check (length(body) <= 4000), created_at timestamptz not null default now());
create table if not exists public.feedback (id bigserial primary key, day date not null, item text not null check (length(item) <= 20), value text not null check (value in ('useful','knew','notme','deeper','')), created_at timestamptz not null default now());
create table if not exists public.picks    (id bigserial primary key, day date not null, exercise text not null check (exercise in ('work','write','build','')), created_at timestamptz not null default now());

alter table public.recaps   enable row level security;
alter table public.feedback enable row level security;
alter table public.picks    enable row level security;

create or replace function public.ds_key_ok() returns boolean language sql stable as $$
  select coalesce(current_setting('request.headers', true)::json ->> 'x-ds-key', '') = '__WRITE_KEY__'
$$;

drop policy if exists "insert with key" on public.recaps;
drop policy if exists "insert with key" on public.feedback;
drop policy if exists "insert with key" on public.picks;
create policy "insert with key" on public.recaps   for insert to anon with check (public.ds_key_ok());
create policy "insert with key" on public.feedback for insert to anon with check (public.ds_key_ok());
create policy "insert with key" on public.picks    for insert to anon with check (public.ds_key_ok());
-- No select / update / delete policies: the public key cannot read or change anything.

create or replace function public.ds_recent(token text, days int default 7) returns json
language plpgsql security definer set search_path = public as $$
begin
  if token is distinct from '__READ_KEY__' then raise exception 'not allowed'; end if;
  return json_build_object(
    'recaps',   (select coalesce(json_agg(r order by r.created_at), '[]') from recaps r   where r.created_at > now() - make_interval(days => days)),
    'feedback', (select coalesce(json_agg(f order by f.created_at), '[]') from feedback f where f.created_at > now() - make_interval(days => days)),
    'picks',    (select coalesce(json_agg(p order by p.created_at), '[]') from picks p    where p.created_at > now() - make_interval(days => days))
  );
end $$;
revoke all on function public.ds_recent(text, int) from public;
grant execute on function public.ds_recent(text, int) to anon;
