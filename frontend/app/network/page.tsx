"use client";

import { useEffect, useState } from "react";
import { AgentOpsMonitor, type IncidentEvent, type OpsServiceMetric, type OpsSignal } from "@/components/agents-ui/agent-ops-monitor";

interface NetworkConnection {
  process: string;
  protocol: string;
  local_address: string;
  remote_address: string;
  status: string;
  is_local: boolean;
}

interface NetworkAuditData {
  total_connections: number;
  local_connections_count: number;
  external_connections: number;
  is_air_gapped: boolean | null;
  air_gap_status: string;
  connections: NetworkConnection[];
}

export default function NetworkMonitorPage() {
  const [audit, setAudit] = useState<NetworkAuditData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchNetworkAudit = async () => {
    setError(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiBase}/api/network/connections`);
      if (!response.ok) throw new Error(`Network audit returned HTTP ${response.status}`);
      setAudit(await response.json() as NetworkAuditData);
    } catch (cause) {
      setAudit(null);
      setError(cause instanceof Error ? cause.message : "Unable to reach the network audit endpoint");
    }
  };

  useEffect(() => { void fetchNetworkAudit(); }, []);

  const signals: OpsSignal[] = audit ? [
    {
      id: "air-gap",
      title: "Air-gap verification",
      status: audit.is_air_gapped === true ? "healthy" : audit.is_air_gapped === false ? "critical" : "warning",
      detail: audit.air_gap_status,
      lastUpdated: "Latest audit",
    },
    {
      id: "connections",
      title: "External connections",
      status: audit.external_connections === 0 ? "healthy" : "critical",
      detail: `${audit.external_connections} external connection${audit.external_connections === 1 ? "" : "s"} reported.`,
      lastUpdated: "Latest audit",
    },
  ] : [{ id: "network", title: "Network audit unavailable", status: "warning", detail: error ?? "Fetching latest audit..." }];

  const metrics: OpsServiceMetric[] = audit ? [
    { label: "Total connections", value: String(audit.total_connections), threshold: "Live snapshot", trend: "stable" },
    { label: "Local connections", value: String(audit.local_connections_count), threshold: "Loopback expected", trend: "stable" },
    { label: "External connections", value: String(audit.external_connections), threshold: "0 expected", trend: audit.external_connections === 0 ? "stable" : "up" },
  ] : [];
  const incidents: IncidentEvent[] = (audit?.connections ?? []).filter((connection) => !connection.is_local).map((connection, index) => ({
    id: `${connection.process}-${index}`,
    timestamp: connection.status,
    summary: `${connection.process}: ${connection.local_address} → ${connection.remote_address}`,
  }));

  return <div className="mx-auto w-full max-w-6xl p-4 sm:p-8"><AgentOpsMonitor environment="Local network" uptime={audit?.is_air_gapped === true ? "Air-gapped" : "Verification required"} signals={signals} metrics={metrics} incidents={incidents} /></div>;
}
