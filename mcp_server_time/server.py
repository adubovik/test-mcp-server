from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

import os
from zoneinfo import ZoneInfo
from tzlocal import get_localzone_name

from pydantic import BaseModel
from fastmcp import FastMCP

from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


class TimeTools(str, Enum):
    GET_CURRENT_TIME = "get_current_time"
    CONVERT_TIME = "convert_time"


class TimeResult(BaseModel):
    timezone: str
    datetime: str
    day_of_week: str
    is_dst: bool


class TimeConversionResult(BaseModel):
    source: TimeResult
    target: TimeResult
    time_difference: str


def get_local_tz(local_tz_override: str | None = None) -> ZoneInfo:
    if local_tz_override:
        return ZoneInfo(local_tz_override)

    local_tzname = get_localzone_name()  # e.g. "Europe/Paris"
    if local_tzname:
        return ZoneInfo(local_tzname)

    return ZoneInfo("UTC")


def get_zoneinfo(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except Exception as e:
        raise ValueError(f"Invalid timezone {timezone_name!r}: {e}") from e


def to_time_result(tz_name: str, dt: datetime) -> TimeResult:
    return TimeResult(
        timezone=tz_name,
        datetime=dt.isoformat(timespec="seconds"),
        day_of_week=dt.strftime("%A"),
        is_dst=bool(dt.dst()),
    )


local_tz = str(get_local_tz("UTC"))

mcp = FastMCP(
    name="mcp-time",
    instructions=(
        "Provides timezone utilities.\n"
        f"If the user doesn't specify a timezone, you can use {local_tz} as the local timezone."
    ),
)

if os.getenv("MCP_INSPECTOR","").lower() in ("1", "true"):
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=[
                "mcp-protocol-version",
                "mcp-session-id",
                "Authorization",
                "Content-Type",
            ],
            expose_headers=["mcp-session-id"],
        )
    ]
else:
    middleware = []

@mcp.tool(
    name=TimeTools.GET_CURRENT_TIME.value,
    description="Get current time in a specific timezone.",
)
def get_current_time(
    timezone: str,
) -> TimeResult:
    tz = get_zoneinfo(timezone)
    now = datetime.now(tz)
    return to_time_result(timezone, now)


@mcp.tool(
    name=TimeTools.CONVERT_TIME.value,
    description="Convert time between timezones.",
)
def convert_time(
    source_timezone: str,
    time: str,
    target_timezone: str,
) -> TimeConversionResult:
    src_tz = get_zoneinfo(source_timezone)
    dst_tz = get_zoneinfo(target_timezone)

    try:
        parsed_time = datetime.strptime(time, "%H:%M").time()
    except ValueError as e:
        raise ValueError("Invalid time format. Expected HH:MM [24-hour format].") from e

    now_src = datetime.now(src_tz)
    src_dt = datetime(
        now_src.year,
        now_src.month,
        now_src.day,
        parsed_time.hour,
        parsed_time.minute,
        tzinfo=src_tz,
    )

    dst_dt = src_dt.astimezone(dst_tz)

    src_offset = src_dt.utcoffset() or timedelta()
    dst_offset = dst_dt.utcoffset() or timedelta()
    hours_diff = (dst_offset - src_offset).total_seconds() / 3600

    if hours_diff.is_integer():
        diff_str = f"{hours_diff:+.1f}h"
    else:
        diff_str = f"{hours_diff:+.2f}".rstrip("0").rstrip(".") + "h"

    return TimeConversionResult(
        source=to_time_result(source_timezone, src_dt),
        target=to_time_result(target_timezone, dst_dt),
        time_difference=diff_str,
    )


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=5006,
        show_banner=False,
        middleware=middleware,
    )


if __name__ == "__main__":
    main()
