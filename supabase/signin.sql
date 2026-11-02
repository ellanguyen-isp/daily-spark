-- daily spark: switch from the write key to email sign-in, and let your signed-in devices read rows back
-- (so notes sync both ways between phone and web). Run once on a project set up with the old schema.sql.
-- Paste into Supabase → SQL Editor. Replace __OWNER_EMAIL__ first (the email you sign in with), then Run.
-- After this, only that account can add or read rows. The morning Worker still reads through ds_recent with the read key.

alter table public.notes add column if not exists cid text check (cid is null or length(cid) <= 40);

create or replace function public.ds_owner() returns boolean language sql stable as $$
  select lower(coalesce(auth.jwt() ->> 'email', '')) = lower('__OWNER_EMAIL__')
$$;

do $$ declare t text; begin
  foreach t in array array['recaps', 'feedback', 'picks', 'notes'] loop
    execute format('drop policy if exists "insert with key" on public.%I', t);
    execute format('drop policy if exists "owner insert" on public.%I', t);
    execute format('drop policy if exists "owner read" on public.%I', t);
    execute format('create policy "owner insert" on public.%I for insert to authenticated with check (public.ds_owner())', t);
    execute format('create policy "owner read" on public.%I for select to authenticated using (public.ds_owner())', t);
  end loop;
end $$;
drop function if exists public.ds_key_ok();
-- Still no update / delete policies: an edit or a removal is a new row (latest row per note wins).
