# Solution

## Running locally

The project uses [`just`](https://github.com/casey/just) as a command runner.

| Command | Description |
|---|---|
| `just dev-env` | Starts a local PostgreSQL container for development, then run `alembic upgrade head` to apply migrations |
| `just test-env` | Starts a separate PostgreSQL container on a different port for running tests |
| `just up` | Builds the Docker image and starts the full stack (app + database) via Docker Compose |
| `just down` | Stops and removes the Docker Compose stack |

---

## Decisions & Assumptions

### Tech stack
- **FastAPI** for the REST API - good validation via Pydantic.
- **PostgreSQL** as the database - reliable, well-supported by SQLAlchemy.
- **SQLAlchemy + Alembic** for ORM and migrations.
- **Docker Compose** to run the application and database locally.

### Order placement
I initially designed and implemented order placement using FastAPI's `BackgroundTasks` - saving the order with `PENDING` status to the database and immediately returning `201`, with the exchange call happening asynchronously in the background.

After re-reading the requirement - *"it is guaranteed that the order **will** be placed on the stock exchange"* - I changed the implementation to call the exchange synchronously before returning. The endpoint now saves the order with `PENDING` status, calls `place_order_with_retry`, updates status accordingly and only returns `201` once placement succeeds:

```python
db_order = service.create_order(x_user_uuid, order.to_order_create())
service.place_order_with_retry(db_order.uuid)
return db_order
```

**Trade-off**: this means a slow or failing exchange will directly affect the endpoint's response time. The production solution to satisfy both guarantees is a durable message queue (see improvements below).

### Validation
Input validation is handled at the Pydantic model level before any business logic runs:
- `limit_price` is required for `limit` orders and must be absent for `market` orders - enforced via a `@model_validator`.
- `quantity` must be greater than zero - enforced via a field constraint.

This keeps validation close to the API boundary and produces clear 422 responses with field-level error details automatically.

### Retry logic
The exchange placement retries up to `MAX_RETRIES = 3` times. The limit exists for two reasons:
- **Rate limiting**: an external exchange API may block callers that hit it too aggressively in a short window.
- **Transient downtime**: a third-party service that is fully down should not tie up a thread indefinitely - failing fast and marking the order `FAILED` is better than retrying forever.

In production, permanent failures would land in a dead-letter queue for manual review or re-processing.

### Monetary values
`limit_price` is stored as an integer in milliunits (e.g. `1000` = €1.00) to avoid floating-point precision issues. A custom `Money` class handles conversion between the wire format (float) and storage format (integer).

---

## Future Improvements

### Guaranteed order placement via a durable message queue
The current background task approach does not truly guarantee placement. In a production system, this would be replaced with a durable message queue (e.g. RabbitMQ, Kafka or pubsub/SQS depending on the platform):

1. The endpoint saves the order to the DB and publishes a message to the queue atomically.
2. The endpoint returns `201` - at this point delivery to the exchange is guaranteed by the queue's durability.
3. A separate worker process consumes messages from the queue and places orders on the exchange, retrying on failure with a dead-letter queue for permanent failures.

This separates the HTTP layer, persistence, and exchange communication into independently scalable and fault-tolerant components.

### Database scalability

**Indexing** (near-term): `instrument` and `side` are important if a trading/matching system queries the same database - finding all open buy or sell orders for a given stock during order matching would be a full table scan without them. `user_id` speeds up `GET /orders` as the table grows. `created_at` supports date-range queries and is required for partitioning to perform well.

**Date-based partitioning** (near-term): Orders are time-series data and queries are almost always scoped to recent activity. Partitioning the `orders` table by `created_at` (e.g. monthly ranges) allows old partitions to be detached and archived cheaply without impacting query performance.

**Read replica** (medium-term): `GET /orders` is a read-only query. Routing reads to a replica separates read and write load with minimal operational overhead and no application-level changes beyond the connection string.

**Horizontal sharding by user** (large scale): Sharding by `user_id` is a natural fit if the dataset grows beyond what a single PostgreSQL instance can handle. Each shard handles a subset of users, distributing both the data and query load across multiple instances.

### Testing strategy

**Unit tests**: validate individual components in isolation - Pydantic validation rules (limit_price, quantity), retry/backoff logic with mocked exchange calls, repository methods against a real test database. These are already covered in the test suite.

**Integration tests**: verify the full request lifecycle - `POST /orders` persists the correct record and the background task updates the order status to `PLACED` or `FAILED`.

**Fault injection with Toxiproxy**: Toxiproxy sits in front of the database and lets you simulate real infrastructure failures in a controlled way. Useful scenarios:
- Cut the PostgreSQL connection mid-request to verify the endpoint returns 500 cleanly and no partial data is written.
- Introduce high latency on the DB connection to surface connection pool exhaustion under load.

**Load tests**: use a tool like Locust to simulate many concurrent users hitting `POST /orders` simultaneously.
