import time
from datetime import datetime
from decimal import Decimal
from geopy.distance import geodesic
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from tqdm import tqdm

# ── Tuning constants ────────────────────────────────────────────────────────
MAX_SPEED_KMH        = 200   # ignore leg if implied speed exceeds this (GPS glitch)
MAX_GAP_SECONDS      = 3600  # ignore leg if time gap > 1 hour (parked / off)
MIN_VALID_LAT        = -90.0
MAX_VALID_LAT        =  90.0
MIN_VALID_LON        = -180.0
MAX_VALID_LON        =  180.0
# ────────────────────────────────────────────────────────────────────────────


def is_valid_coord(lat: float, lon: float) -> bool:
    """Return True only for non-zero coordinates inside valid WGS-84 bounds."""
    return (
        MIN_VALID_LAT <= lat <= MAX_VALID_LAT
        and MIN_VALID_LON <= lon <= MAX_VALID_LON
        and not (lat == 0.0 and lon == 0.0)   # null-island sentinel
    )


def test_odometer_from_gps_db(
    sensor_imeis: list,
    postgres_db_url: str,
    gps_db_url: str,
    start_date: str | None = None,   # e.g. "2025-01-01 00:00:00"
    end_date:   str | None = None,   # e.g. "2025-05-29 23:59:59"
):
    """
    Calculate odometer for sensors using data from a separate GPS database.
    Read-only — no data is written to either database.
    """
    postgres_engine = create_engine(postgres_db_url)
    gps_engine      = create_engine(gps_db_url)

    print("=" * 90)
    print("ODOMETER CALCULATION TEST (READ-ONLY – TWO DATABASES)")
    if start_date or end_date:
        print(f"Date range : {start_date or 'beginning'} → {end_date or 'now'}")
    print("=" * 90)

    try:
        for imei in sensor_imeis:
            start_time = time.time()

            # ── 1. Verify sensor exists ──────────────────────────────────────
            with Session(postgres_engine) as db:
                sensor = db.execute(
                    text("SELECT id, imei FROM sensors WHERE imei = :imei"),
                    {"imei": imei},
                ).first()

            if not sensor:
                print(f"\n❌  Sensor with IMEI {imei} not found in sensors table!")
                continue

            print(f"\n📍 Processing Sensor: {imei}")

            # ── 2. Fetch GPS records ─────────────────────────────────────────
            with Session(gps_engine) as db:
                gps_data = db.execute(
                    text("""
                        SELECT record_time, latitude, longitude
                        FROM   gps
                        WHERE  imei = :imei
                          AND  (:start_date IS NULL OR record_time >= :start_date)
                          AND  (:end_date   IS NULL OR record_time <= :end_date)
                        ORDER  BY record_time ASC
                    """),
                    {"imei": imei, "start_date": start_date, "end_date": end_date},
                ).all()

            print(f"   Total GPS records found : {len(gps_data):,}")

            if len(gps_data) < 2:
                print("   ⚠️  Not enough data points to calculate distance")
                continue

            # ── 3. Accumulate distance ───────────────────────────────────────
            total_km               = Decimal("0.00")
            prev_lat               = None
            prev_lon               = None
            prev_time              = None
            max_jump_km            = Decimal("0.00")

            skipped_invalid_coord  = 0
            skipped_speed_glitch   = 0
            skipped_time_gap       = 0
            legs_counted           = 0

            for record in tqdm(gps_data, desc=f"Calc {imei[-6:]}", leave=False):
                curr_lat  = float(record.latitude)
                curr_lon  = float(record.longitude)
                curr_time = record.record_time  # expected: datetime object

                # — validate coordinate —
                if not is_valid_coord(curr_lat, curr_lon):
                    skipped_invalid_coord += 1
                    continue

                if prev_lat is not None:
                    # — time gap check —
                    if prev_time is not None and isinstance(curr_time, datetime):
                        gap_seconds = (curr_time - prev_time).total_seconds()
                        if gap_seconds > MAX_GAP_SECONDS:
                            skipped_time_gap += 1
                            # Still update anchor so next leg starts fresh here
                            prev_lat, prev_lon, prev_time = curr_lat, curr_lon, curr_time
                            continue

                    # — compute leg distance —
                    distance_km = geodesic(
                        (prev_lat, prev_lon), (curr_lat, curr_lon)
                    ).kilometers

                    # — speed-based glitch filter —
                    if prev_time is not None and isinstance(curr_time, datetime):
                        elapsed_h = max(
                            (curr_time - prev_time).total_seconds() / 3600,
                            1 / 3600,   # floor at 1 second to avoid division-by-zero
                        )
                        implied_speed = distance_km / elapsed_h
                        if implied_speed > MAX_SPEED_KMH:
                            skipped_speed_glitch += 1
                            prev_lat, prev_lon, prev_time = curr_lat, curr_lon, curr_time
                            continue
                    else:
                        # No timestamp available — fall back to hard distance cap
                        if distance_km > 200:
                            skipped_speed_glitch += 1
                            prev_lat, prev_lon, prev_time = curr_lat, curr_lon, curr_time
                            continue

                    total_km += Decimal(str(round(distance_km, 6)))
                    legs_counted += 1

                    if distance_km > float(max_jump_km):
                        max_jump_km = Decimal(str(round(distance_km, 6)))

                prev_lat, prev_lon, prev_time = curr_lat, curr_lon, curr_time

            # ── 4. Report ────────────────────────────────────────────────────
            elapsed = time.time() - start_time
            valid_records = len(gps_data) - skipped_invalid_coord

            print(f"\n✅  Results for IMEI {imei}:")
            print(f"   Total Distance          : {total_km:>12,.2f} km")
            print(f"   GPS Records Fetched     : {len(gps_data):>12,}")
            print(f"   Invalid coords skipped  : {skipped_invalid_coord:>12,}")
            print(f"   Time-gap legs skipped   : {skipped_time_gap:>12,}  (gap > {MAX_GAP_SECONDS}s)")
            print(f"   Speed-glitch legs skip  : {skipped_speed_glitch:>12,}  (>{MAX_SPEED_KMH} km/h)")
            print(f"   Legs counted            : {legs_counted:>12,}")
            print(f"   Largest single leg      : {max_jump_km:>12,.2f} km")
            print(f"   Time taken              : {elapsed:>12.2f} s")
            if valid_records > 0:
                print(f"   Avg time / 10k pts      : {elapsed / valid_records * 10_000:>12.2f} s")
            print("-" * 70)

    except Exception as e:
        import traceback
        print(f"\n❌  Error occurred: {e}")
        traceback.print_exc()
    finally:
        print("\n🏁  Test completed (no data was modified)")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    POSTGRES_DB_URL = "postgresql://postgres:SOp4Cch76F54c2Jn@5.75.185.186/postgres"
    GPS_DB_URL      = "postgresql://postgres:SOp4Cch76F54c2Jn@5.75.185.186/gps"

    TEST_IMEIS = [
        "0869689043791748",
    ]

    test_odometer_from_gps_db(
        sensor_imeis    = TEST_IMEIS,
        postgres_db_url = POSTGRES_DB_URL,
        gps_db_url      = GPS_DB_URL,
        start_date      = None,               # e.g. "2025-01-01 00:00:00"
        end_date        = None,               # e.g. "2025-05-29 23:59:59"
    )