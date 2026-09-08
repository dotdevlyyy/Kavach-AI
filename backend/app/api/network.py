"""
Kavach AI — Network Sovereignty & Air-Gap Audit Router
Provides real system network socket inspection using psutil.
"""

import ipaddress
import psutil
from fastapi import APIRouter
from loguru import logger

router = APIRouter(prefix="/api/network", tags=["network"])


def is_local_address(ip_str: str) -> bool:
    """Check if an IP address is local, loopback, or private subnet."""
    if not ip_str or ip_str in ("*", "0.0.0.0", "::", "127.0.0.1", "localhost"):
        return True
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local
    except ValueError:
        return True


@router.get("")
@router.get("/connections")
async def get_network_audit():
    """
    Inspect active system sockets via psutil to verify air-gap sovereignty.
    Returns safe process and socket metadata without exposing credentials or system secrets.
    """
    connection_list = []
    external_count = 0
    local_count = 0

    try:
        net_conns = psutil.net_connections(kind="inet")
    except Exception as e:
        logger.warning(f"psutil.net_connections error: {e}")
        net_conns = []

    # Map PIDs to process names safely
    pid_name_map = {}
    for conn in net_conns:
        pid = conn.pid
        if pid and pid not in pid_name_map:
            try:
                proc = psutil.Process(pid)
                pid_name_map[pid] = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pid_name_map[pid] = "system"

    for conn in net_conns:
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "0.0.0.0:0"
        
        if conn.raddr:
            raddr_ip = conn.raddr.ip
            raddr_port = conn.raddr.port
            raddr = f"{raddr_ip}:{raddr_port}"
            is_local = is_local_address(raddr_ip)
        else:
            raddr_ip = ""
            raddr = "LISTEN"
            is_local = True

        if is_local:
            local_count += 1
            remote_display = f"{raddr} (Local)" if conn.raddr else "LISTEN"
        else:
            external_count += 1
            remote_display = raddr

        proc_name = pid_name_map.get(conn.pid, "system") if conn.pid else "system"
        proto = "TCP" if conn.type == 1 else "UDP"

        connection_list.append({
            "process": proc_name,
            "protocol": proto,
            "local_address": laddr,
            "remote_address": remote_display,
            "status": conn.status,
            "is_local": is_local
        })

    is_air_gapped = (external_count == 0)

    # Return socket entries (limit 20 to avoid overwhelming payload)
    return {
        "total_connections": len(connection_list),
        "local_connections_count": local_count,
        "external_connections": external_count,
        "is_air_gapped": is_air_gapped,
        "air_gap_status": "100% SECURE" if is_air_gapped else "EXTERNAL WARNING",
        "connections": connection_list[:20]
    }
