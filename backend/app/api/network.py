"""
Kavach AI — Network Sovereignty & Air-Gap Audit Router
Provides real system network socket inspection using psutil.
"""

import asyncio
import ipaddress
from datetime import datetime, timedelta, timezone

import psutil
from fastapi import APIRouter, Query
from loguru import logger

from app.models.network_log import NetworkLog
from app.schemas.responses import NetworkLogsResponse, NetworkResponse

router = APIRouter(prefix="/api/network", tags=["network"])

_last_connections: list[dict] = []
_last_snapshot_at: datetime | None = None
_last_collection_error: str | None = "not_collected"


async def _periodic_snapshotter(interval_seconds: int = 30) -> None:
    """Background task: snapshot psutil sockets every `interval_seconds`.

    ponytail: ticks forever until cancelled. Failure to read psutil logs and skips
    the tick — never crashes the loop. Single shared task for whole process.
    """
    while True:
        try:
            snap = _snapshot_connections()
            await _snapshot_to_db(snap)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"Network snapshotter tick failed: {e}")
        await asyncio.sleep(interval_seconds)


def is_local_address(ip_str: str) -> bool:
    """Check if an IP address is local, loopback, or private subnet."""
    if not ip_str or ip_str in ("*", "0.0.0.0", "::", "127.0.0.1", "localhost"):
        return True
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local
    except ValueError:
        return False


def _snapshot_connections():
    """Return a list of dicts describing current psutil sockets."""
    global _last_connections, _last_snapshot_at, _last_collection_error
    try:
        net_conns = psutil.net_connections(kind="inet")
    except Exception as e:
        logger.warning(f"psutil.net_connections error: {e}")
        _last_collection_error = "collection_failed"
        return []

    pid_name_map: dict[int, str] = {}
    for conn in net_conns:
        pid = conn.pid
        if pid and pid not in pid_name_map:
            try:
                pid_name_map[pid] = psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pid_name_map[pid] = "system"

    out = []
    for conn in net_conns:
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "0.0.0.0:0"
        if conn.raddr:
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}"
            try:
                ipaddress.ip_address(conn.raddr.ip)
            except ValueError:
                _last_collection_error = "invalid_remote_address"
                return []
            is_local = is_local_address(conn.raddr.ip)
        else:
            raddr = "LISTEN"
            is_local = True
        proto = "TCP" if conn.type == 1 else "UDP"
        out.append(
            {
                "process": pid_name_map.get(conn.pid, "system") if conn.pid else "system",
                "protocol": proto,
                "local_address": laddr,
                "remote_address": raddr,
                "status": conn.status,
                "is_local": is_local,
            }
        )
    _last_connections = out
    _last_snapshot_at = datetime.now(timezone.utc)
    _last_collection_error = None
    return out


def get_network_summary(refresh: bool = False) -> dict:
    """Return latest trustworthy network verdict."""
    connections = _snapshot_connections() if refresh else _last_connections
    if _last_collection_error:
        return {
            "status": "unknown",
            "is_air_gapped": None,
            "local_count": 0,
            "external_count": 0,
            "timestamp": _last_snapshot_at.isoformat() if _last_snapshot_at else None,
            "error": _last_collection_error,
            "connections": [],
        }

    local_count = sum(1 for connection in connections if connection["is_local"])
    external_count = len(connections) - local_count
    return {
        "status": "secure" if external_count == 0 else "external_connections_detected",
        "is_air_gapped": external_count == 0,
        "local_count": local_count,
        "external_count": external_count,
        "timestamp": _last_snapshot_at.isoformat() if _last_snapshot_at else None,
        "error": None,
        "connections": connections,
    }


async def _snapshot_to_db(connection_list: list[dict]) -> int:
    """Persist a snapshot of current connections to NetworkLog. Returns rows written."""
    rows = [
        NetworkLog(
            local_addr=c["local_address"],
            remote_addr=c["remote_address"],
            protocol=c["protocol"],
            status=c["status"],
            process_name=c["process"],
            is_local=c["is_local"],
        )
        for c in connection_list
    ]
    await NetworkLog.filter(timestamp__lt=datetime.now(timezone.utc) - timedelta(hours=24)).delete()
    if not rows:
        return 0
    await NetworkLog.bulk_create(rows)
    return len(rows)


@router.get("", response_model=NetworkResponse)
@router.get("/connections", response_model=NetworkResponse)
async def get_network_audit(persist: bool = Query(default=False)):
    """
    Inspect active system sockets via psutil to verify air-gap sovereignty.
    Returns safe process and socket metadata without exposing credentials or system secrets.
    Pass ?persist=true to snapshot into NetworkLog.
    """
    summary = get_network_summary(refresh=True)
    connection_list = summary["connections"]

    persisted = 0
    if persist:
        try:
            persisted = await _snapshot_to_db(connection_list)
        except Exception as e:
            logger.warning(f"Failed to persist NetworkLog snapshot: {e}")

    return {
        "total_connections": len(connection_list),
        "local_count": summary["local_count"],
        "external_count": summary["external_count"],
        "local_connections_count": summary["local_count"],
        "external_connections": summary["external_count"],
        "is_air_gapped": summary["is_air_gapped"],
        "air_gap_status": summary["status"],
        "monitor_error": summary["error"],
        "timestamp": summary["timestamp"],
        "persisted_rows": persisted,
        "connections": connection_list[:20],
    }


@router.get("/logs", response_model=NetworkLogsResponse)
async def list_network_logs(limit: int = Query(default=50, ge=1, le=500)):
    """GET /api/network/logs — Historical NetworkLog rows from psutil snapshots."""
    rows = await NetworkLog.all().order_by("-timestamp").limit(limit)
    return {
        "logs": [
            {
                "id": r.id,
                "timestamp": str(r.timestamp),
                "local_addr": r.local_addr,
                "remote_addr": r.remote_addr,
                "protocol": r.protocol,
                "status": r.status,
                "process_name": r.process_name,
                "is_local": r.is_local,
            }
            for r in rows
        ],
        "total": await NetworkLog.all().count(),
    }
