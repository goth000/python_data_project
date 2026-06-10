# Week 10 Docker and BI Validation

## Services

The analytical stand is started with Docker Compose:

```cmd
docker compose up -d postgres metabase
docker compose ps postgres metabase
```

PostgreSQL is published on `localhost:5432`. Metabase is available at
`http://localhost:3000`.

Metabase runs inside the Compose network, so its PostgreSQL connection uses
`postgres` as the host, not `localhost`. The dashboard reads the
`mart_open_meteo` table from PostgreSQL, not a CSV file.

## Volumes

The Compose configuration mounts:

- `pgdata` to `/var/lib/postgresql/data`;
- `metabase_data` to `/metabase-data`.

`docker volume ls` and `docker inspect` confirmed the volumes:

```text
python_data_project_pgdata => /var/lib/postgresql/data
python_data_project_metabase_data => /metabase-data
```

## Persistence Check

The containers were removed and recreated without deleting volumes:

```cmd
docker compose down
docker compose up -d postgres metabase
```

After recreation, PostgreSQL still contained:

```text
mart_open_meteo: 7 rows, 7 unique (date, city_id) keys
test_volume: 1 control row
```

This confirms that PostgreSQL data survived because it is stored in `pgdata`.

## Command Differences

- `docker compose stop` stops existing containers; `start` resumes the same containers.
- `docker compose down` removes containers and the Compose network, but keeps named volumes.
- `docker compose down -v` also deletes named volumes and therefore deletes persisted data.
- `localhost` means the current machine or container. From Metabase, PostgreSQL is reached by
  the Compose service name `postgres`.

## BI Dashboard

`Tokyo Weather Dashboard` contains three visualizations built from
`mart_open_meteo`:

- Temperature Trend;
- Rainfall Ranking;
- Max Temperature.

Screenshots are stored in `docs/bi/`.
