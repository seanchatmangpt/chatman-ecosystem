import {
  createBackupJob,
  createDumpReaderJob,
  deleteJob,
  getJobStatus,
  getProject,
  getProjectDatabasePod,
  getProjectStorageService,
  getPodLogs,
  listPods,
  type K8sResult,
} from "@/lib/k8s";
import { fetchStorageBuckets, fetchStorageObjects, fetchStorageObject } from "@/lib/storage-api";
import { streamAuditLogAsEcsNdjson } from "@/lib/audit-export";
import { buildZip, type ZipEntryInput } from "@/lib/zip";

/**
 * Real "export everything for this tenant" bundle: triggers the exact
 * same pg_dump backup Job createBackupJob (Database Backups module)
 * already creates, lists+downloads every real storage object via the
 * exact primitives storage-signed-url-expiry-enforced already exposed
 * (fetchStorageBuckets/fetchStorageObject, plus the new
 * fetchStorageObjects list call this control adds), and pulls the exact
 * same real audit-log NDJSON export audit-export-valid-ndjson-matches-
 * source already produces (streamAuditLogAsEcsNdjson) -- then zips all
 * three real artifacts (lib/zip.ts) into one archive. Nothing here
 * fabricates content: the DB dump is read back from the real backup Job's
 * PVC via a short-lived reader Job (see createDumpReaderJob), storage
 * objects are real bytes from the real Storage API, and the audit export
 * is the real durable audit_log table.
 */

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 60; // 2 minutes per Job

export interface ExportAllSummary {
  projectName: string;
  namespace: string;
  generatedAt: string;
  backupJobName: string | null;
  dumpBytes: number;
  buckets: Array<{ name: string; objectCount: number; totalBytes: number }>;
  auditRowCount: number;
  warnings: string[];
}

export interface ExportAllOutcome {
  archive: Buffer;
  filename: string;
  summary: ExportAllSummary;
}

async function pollJobComplete(
  namespace: string,
  jobName: string,
): Promise<K8sResult<"Complete" | "Failed">> {
  for (let attempt = 0; attempt < POLL_MAX_ATTEMPTS; attempt++) {
    const result = await getJobStatus(namespace, jobName);
    if (!result.ok) return result;
    if (result.data.status === "Complete") return { ok: true, data: "Complete" };
    if (result.data.status === "Failed") return { ok: true, data: "Failed" };
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  return { ok: false, error: `Job ${jobName} did not reach Complete/Failed within the poll window` };
}

async function readDumpViaReaderJob(
  namespace: string,
  backupJobName: string,
): Promise<{ ok: true; data: Buffer } | { ok: false; error: string }> {
  const readerResult = await createDumpReaderJob(namespace, backupJobName);
  if (!readerResult.ok) return readerResult;
  const readerJobName = readerResult.data.name;

  const statusResult = await pollJobComplete(namespace, readerJobName);
  if (!statusResult.ok) return statusResult;
  if (statusResult.data !== "Complete") {
    return { ok: false, error: `dump reader Job ${readerJobName} did not complete successfully` };
  }

  const podsResult = await listPods(namespace, `job-name=${readerJobName}`);
  if (!podsResult.ok) return podsResult;
  const pod = podsResult.data[0];
  if (!pod) {
    return { ok: false, error: `dump reader Job ${readerJobName} has no Pod` };
  }

  const logsResult = await getPodLogs(namespace, pod.name, { tailLines: 5_000_000 });
  if (!logsResult.ok) return logsResult;

  // Cleanup best-effort: the reader Job also carries ttlSecondsAfterFinished
  // as a backstop, so a failed delete here is not fatal to the export.
  await deleteJob(namespace, readerJobName);

  const base64Text = logsResult.data.replace(/\s+/g, "");
  try {
    return { ok: true, data: Buffer.from(base64Text, "base64") };
  } catch (err) {
    return {
      ok: false,
      error: `failed to decode dump reader output as base64: ${err instanceof Error ? err.message : String(err)}`,
    };
  }
}

export async function exportProjectBundle(projectName: string): Promise<
  { ok: true; data: ExportAllOutcome } | { ok: false; error: string }
> {
  const warnings: string[] = [];
  const generatedAt = new Date().toISOString();

  const projectResult = await getProject(projectName);
  if (!projectResult.ok) return projectResult;
  if (!projectResult.data) return { ok: false, error: `project '${projectName}' not found` };
  const project = projectResult.data;

  const entries: ZipEntryInput[] = [];

  // ---------------------------------------------------------- 1. DB dump
  let backupJobName: string | null = null;
  let dumpBytes = 0;

  const dbPodResult = await getProjectDatabasePod(project);
  if (!dbPodResult.ok) {
    warnings.push(`database: ${dbPodResult.error}`);
  } else if (!dbPodResult.data) {
    warnings.push("database: no database Service found for this project -- no dump included");
  } else {
    const { namespace, podName } = dbPodResult.data;
    const backupResult = await createBackupJob(namespace, podName);
    if (!backupResult.ok) {
      warnings.push(`database backup: ${backupResult.error}`);
    } else {
      backupJobName = backupResult.data.name;
      const statusResult = await pollJobComplete(namespace, backupJobName);
      if (!statusResult.ok) {
        warnings.push(`database backup: ${statusResult.error}`);
      } else if (statusResult.data !== "Complete") {
        warnings.push(`database backup Job ${backupJobName} did not reach Complete`);
      } else {
        const dumpResult = await readDumpViaReaderJob(namespace, backupJobName);
        if (!dumpResult.ok) {
          warnings.push(`database dump read-back: ${dumpResult.error}`);
        } else {
          dumpBytes = dumpResult.data.length;
          entries.push({ name: `db/${backupJobName}.sql`, data: dumpResult.data });
        }
      }
    }
  }

  // ------------------------------------------------------ 2. Storage objects
  const bucketSummaries: ExportAllSummary["buckets"] = [];
  const svcResult = await getProjectStorageService(project);
  if (!svcResult.ok) {
    warnings.push(`storage: ${svcResult.error}`);
  } else if (!svcResult.data) {
    warnings.push("storage: no storage Service found for this project -- no objects included");
  } else {
    const { dns, port } = svcResult.data;
    const bucketsResult = await fetchStorageBuckets(dns, port);
    if (!bucketsResult.ok) {
      warnings.push(
        bucketsResult.notConfigured
          ? "storage: service-role key not configured -- no objects included"
          : `storage: ${bucketsResult.error}`,
      );
    } else {
      for (const bucketName of bucketsResult.bucketNames) {
        const objectsResult = await fetchStorageObjects(dns, port, bucketName);
        if (!objectsResult.ok) {
          warnings.push(
            `storage bucket '${bucketName}': ${
              objectsResult.notConfigured ? "service-role key not configured" : objectsResult.error
            }`,
          );
          continue;
        }
        let totalBytes = 0;
        for (const object of objectsResult.objects) {
          const objectResult = await fetchStorageObject(dns, port, bucketName, object.name);
          if (!objectResult.ok) {
            warnings.push(
              `storage object '${bucketName}/${object.name}': ${
                objectResult.notConfigured ? "service-role key not configured" : objectResult.error
              }`,
            );
            continue;
          }
          const data = Buffer.from(objectResult.body);
          totalBytes += data.length;
          entries.push({ name: `storage/${bucketName}/${object.name}`, data });
        }
        bucketSummaries.push({ name: bucketName, objectCount: objectsResult.objects.length, totalBytes });
      }
    }
  }

  // --------------------------------------------------------- 3. Audit log
  let auditRowCount = 0;
  try {
    const lines: string[] = [];
    for await (const line of streamAuditLogAsEcsNdjson({})) {
      lines.push(line);
      auditRowCount++;
    }
    entries.push({ name: "audit/audit-log-export.ndjson", data: Buffer.from(lines.join("")) });
  } catch (err) {
    warnings.push(`audit export: ${err instanceof Error ? err.message : String(err)}`);
  }

  // ------------------------------------------------------------- manifest
  const summary: ExportAllSummary = {
    projectName,
    namespace: project.namespace,
    generatedAt,
    backupJobName,
    dumpBytes,
    buckets: bucketSummaries,
    auditRowCount,
    warnings,
  };
  entries.push({
    name: "manifest.json",
    data: Buffer.from(JSON.stringify(summary, null, 2) + "\n"),
  });

  if (entries.length <= 1) {
    // Only the manifest -- nothing real was ever included.
    return {
      ok: false,
      error: `export-all produced no real artifacts for '${projectName}': ${warnings.join("; ") || "unknown reason"}`,
    };
  }

  const archive = buildZip(entries);
  const stamp = generatedAt.replace(/[:.]/g, "-");
  const filename = `export-all-${projectName}-${stamp}.zip`;

  return { ok: true, data: { archive, filename, summary } };
}
