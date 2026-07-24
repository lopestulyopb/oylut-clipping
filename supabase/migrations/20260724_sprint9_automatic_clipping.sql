alter table public.schedules
add column if not exists window_start_time time;

update public.schedules
set window_start_time = (run_time - make_interval(hours => period_hours))::time
where window_start_time is null;

alter table public.schedules
alter column window_start_time set default '00:00';
