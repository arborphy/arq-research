use role accountadmin;

create role if not exists team_arq;
grant role team_arq to role accountadmin;

create warehouse if not exists team_arq;
grant usage on warehouse team_arq to role team_arq;

create database if not exists team_arq;
grant ownership on database team_arq to role team_arq;
grant ownership on schema team_arq.public to role team_arq;
create schema if not exists team_arq.source;
grant ownership on schema team_arq.source to role team_arq;

create stage if not exists team_arq.source.gbif;

grant role rai_admin to role team_arq;
