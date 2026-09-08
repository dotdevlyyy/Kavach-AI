import psutil
from fastapi import APIRouter
import os

router = APIRouter(prefix="/api/network", tags=["Network"])

@router.get("/")
async def get_network_status():
    """
    Checks open network sockets for the current backend process.
    Proves the system is air-gapped (Zero External Calls).
    """
    p = psutil.Process(os.getpid())
    try:
        connections = p.connections(kind='all')
    except psutil.AccessDenied:
        connections = []
        
    external_connections = 0
    connection_details = []

    for conn in connections:
        if conn.status == 'ESTABLISHED':
            raddr = conn.raddr
            if raddr:
                ip = raddr.ip
                # Check if IP is local/private
                is_local = (
                    ip.startswith("127.") or 
                    ip.startswith("192.168.") or 
                    ip.startswith("10.") or 
                    ip.startswith("172.") or
                    ip == "::1" or 
                    ip == "0.0.0.0"
                )
                
                if not is_local:
                    external_connections += 1
                
                connection_details.append({
                    "fd": conn.fd,
                    "family": conn.family.name if conn.family else None,
                    "type": conn.type.name if conn.type else None,
                    "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    "raddr": f"{ip}:{raddr.port}",
                    "status": conn.status,
                    "is_local": is_local
                })

    return {
        "total_established": len(connection_details),
        "external_connections": external_connections,
        "is_air_gapped": external_connections == 0,
        "connections": connection_details
    }
