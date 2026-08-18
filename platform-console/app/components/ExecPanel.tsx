"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface PodOption {
  name: string;
  phase: string;
  containers: string[];
  ready: boolean;
}

interface CommandOption {
  id: string;
  label: string;
  description: string;
  command: string[];
}

type SessionStatus = "idle" | "connecting" | "running" | "closed" | "error";

interface OutputLine {
  kind: "stdout" | "stderr" | "status" | "meta";
  text: string;
}

/**
 * Real hyperscaler-console browser-based shell access (AWS Systems Manager
 * Session Manager / GCP Cloud Shell / Azure Cloud Shell "run a command"
 * equivalent). Picks a real namespace/pod/container (dropdowns populated
 * from a live `GET /api/exec?namespace=X`) and ONE fixed, allowlisted
 * command (no free-text field anywhere in this component -- the dropdown
 * only ever contains the server's own `ALLOWED_EXEC_COMMANDS` ids), then
 * opens a real browser WebSocket to `/ws/exec` (server.js's relay) which
 * itself opens a real WebSocket to the target pod's k8s exec subresource
 * and streams every real stdout/stderr frame back here as it arrives.
 * Owner-gated server-side (this page/route/relay all enforce it
 * independently) -- this component has no client-side gate of its own to
 * bypass.
 */
export default function ExecPanel({ namespaces }: { namespaces: string[] }) {
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [pods, setPods] = useState<PodOption[]>([]);
  const [podsError, setPodsError] = useState<string | null>(null);
  const [podsLoading, setPodsLoading] = useState(false);

  const [pod, setPod] = useState("");
  const [container, setContainer] = useState("");

  const [commands, setCommands] = useState<CommandOption[]>([]);
  const [commandId, setCommandId] = useState("");

  const [status, setStatus] = useState<SessionStatus>("idle");
  const [output, setOutput] = useState<OutputLine[]>([]);
  const socketRef = useRef<WebSocket | null>(null);

  const loadPods = useCallback(async (ns: string) => {
    setPodsLoading(true);
    setPodsError(null);
    setPods([]);
    setPod("");
    setContainer("");
    try {
      const res = await fetch(`/api/exec?namespace=${encodeURIComponent(ns)}`);
      const body = await res.json();
      if (!res.ok) {
        setPodsError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      const podList: PodOption[] = body.pods ?? [];
      setPods(podList);
      if (podList.length > 0) {
        setPod(podList[0].name);
        setContainer(podList[0].containers[0] ?? "");
      }
      if (body.commands) {
        setCommands(body.commands);
        setCommandId((prev) => prev || body.commands[0]?.id || "");
      }
    } catch (err) {
      setPodsError(err instanceof Error ? err.message : String(err));
    } finally {
      setPodsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (namespace) loadPods(namespace);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namespace]);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  function runCommand() {
    if (!namespace || !pod || !container || !commandId) return;
    socketRef.current?.close();
    setOutput([]);
    setStatus("connecting");

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const params = new URLSearchParams({ namespace, pod, container, commandId });
    const socket = new WebSocket(`${proto}//${window.location.host}/ws/exec?${params.toString()}`);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      let msg: { type?: string; data?: string; error?: string };
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }
      if (msg.type === "connected") {
        setStatus("running");
        setOutput((prev) => [...prev, { kind: "meta", text: "-- exec session opened --" }]);
      } else if (msg.type === "stdout" && msg.data) {
        setOutput((prev) => [...prev, { kind: "stdout", text: msg.data as string }]);
      } else if (msg.type === "stderr" && msg.data) {
        setOutput((prev) => [...prev, { kind: "stderr", text: msg.data as string }]);
      } else if (msg.type === "status" && msg.data) {
        setOutput((prev) => [...prev, { kind: "status", text: msg.data as string }]);
      } else if (msg.type === "closed") {
        setStatus("closed");
        setOutput((prev) => [...prev, { kind: "meta", text: "-- exec session closed --" }]);
      } else if (msg.type === "error") {
        setStatus("error");
        setOutput((prev) => [...prev, { kind: "meta", text: `-- error: ${msg.error ?? "unknown"} --` }]);
      }
    };
    socket.onclose = () => {
      setStatus((s) => (s === "connecting" || s === "running" ? "closed" : s));
    };
    socket.onerror = () => {
      setStatus("error");
    };
  }

  const selectedPod = pods.find((p) => p.name === pod);
  const selectedCommand = commands.find((c) => c.id === commandId);

  return (
    <div className="card p-6">
      <div className="mb-4 grid gap-4 sm:grid-cols-5">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Namespace</span>
          <select
            value={namespace}
            onChange={(e) => setNamespace(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          >
            {namespaces.map((ns) => (
              <option key={ns} value={ns}>
                {ns}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Pod</span>
          <select
            value={pod}
            onChange={(e) => {
              const nextPod = e.target.value;
              setPod(nextPod);
              const match = pods.find((p) => p.name === nextPod);
              setContainer(match?.containers[0] ?? "");
            }}
            disabled={podsLoading || pods.length === 0}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {pods.length === 0 && <option value="">(no pods)</option>}
            {pods.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name} ({p.phase})
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Container</span>
          <select
            value={container}
            onChange={(e) => setContainer(e.target.value)}
            disabled={!selectedPod || selectedPod.containers.length <= 1}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {(selectedPod?.containers ?? []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm sm:col-span-2">
          <span className="mb-1 block text-gray-400">Command (fixed allowlist -- no free text)</span>
          <select
            value={commandId}
            onChange={(e) => setCommandId(e.target.value)}
            disabled={commands.length === 0}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {commands.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {selectedCommand && (
        <p className="mb-4 text-xs text-gray-500">
          <code>{selectedCommand.command.join(" ")}</code> -- {selectedCommand.description}
        </p>
      )}

      {podsError && (
        <p className="mb-4 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {podsError}
        </p>
      )}

      <div className="mb-4 flex items-center gap-3">
        <button
          type="button"
          onClick={runCommand}
          disabled={status === "connecting" || status === "running" || !pod || !commandId}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {status === "connecting" || status === "running" ? "Running..." : "Run command"}
        </button>
        <span
          className={
            "text-xs " +
            (status === "running"
              ? "text-emerald-400"
              : status === "error"
                ? "text-red-400"
                : status === "closed"
                  ? "text-gray-400"
                  : "text-amber-400")
          }
        >
          session: {status}
        </span>
      </div>

      <pre className="max-h-[32rem] overflow-auto rounded-md border border-border bg-bg p-4 text-xs leading-relaxed text-gray-200">
        {output.length === 0
          ? "No exec session run yet -- pick a namespace/pod/container/command, then press Run command."
          : output.map((line, i) => (
              <span
                key={i}
                className={
                  line.kind === "stderr"
                    ? "text-red-300"
                    : line.kind === "meta" || line.kind === "status"
                      ? "text-gray-500"
                      : "text-gray-200"
                }
              >
                {line.text}
                {line.kind !== "stdout" && line.kind !== "stderr" ? "\n" : ""}
              </span>
            ))}
      </pre>
    </div>
  );
}
