/**
 * Real outbound email: a minimal SMTP client speaking the actual SMTP
 * protocol (EHLO/AUTH LOGIN/MAIL FROM/RCPT TO/DATA) over a real TLS (or
 * STARTTLS) socket -- same "no external client library, real network I/O"
 * convention lib/k8s.ts documents for its own hand-rolled HTTPS client.
 * No queue, no fabricated "sent" response: a message is only ever
 * reported delivered after the real SMTP server returns a real 2xx final
 * reply to DATA.
 *
 * Configuration is entirely environment-driven (SMTP_HOST, SMTP_PORT,
 * SMTP_USER, SMTP_PASS, SMTP_FROM, optional SMTP_SECURE="true" for
 * implicit TLS on connect vs. STARTTLS) -- same "off-cluster / not
 * configured fails closed with an honest result, never a fabricated
 * success" convention lib/k8s.ts and lib/audit-db.ts already establish.
 * `sendEmail` never throws past its caller; every failure mode (not
 * configured, connection error, SMTP-level rejection) comes back as
 * `{ ok: false, error }`.
 */
import { Socket } from "node:net";
import { connect as tlsConnect, TLSSocket } from "node:tls";

export interface SmtpConfig {
  host: string;
  port: number;
  user: string | null;
  pass: string | null;
  from: string;
  secure: boolean;
}

/** Real config resolved from environment variables. `null` when SMTP is
 * simply not configured in this environment (local dev, a cluster with
 * no mail relay provisioned yet) -- callers treat that as "email
 * delivery unavailable", never as a reason to fabricate a sent receipt. */
export function resolveSmtpConfig(): SmtpConfig | null {
  const host = process.env.SMTP_HOST;
  const from = process.env.SMTP_FROM;
  if (!host || !from) return null;
  const port = Number(process.env.SMTP_PORT ?? "587");
  return {
    host,
    port: Number.isFinite(port) && port > 0 ? port : 587,
    user: process.env.SMTP_USER ?? null,
    pass: process.env.SMTP_PASS ?? null,
    from,
    secure: process.env.SMTP_SECURE === "true",
  };
}

export type SendEmailResult = { ok: true } | { ok: false; error: string };

/** One line of a real SMTP multi-line reply, e.g. "250-" continues,
 * "250 " (space) is the final line of that reply code. */
function isFinalReplyLine(line: string): boolean {
  return /^\d{3} /.test(line) || /^\d{3}$/.test(line);
}

/** Reads one complete SMTP reply (possibly multi-line) from the socket. */
function readReply(socket: Socket | TLSSocket): Promise<{ code: number; text: string }> {
  return new Promise((resolve, reject) => {
    let buffer = "";
    const onData = (chunk: Buffer) => {
      buffer += chunk.toString("utf8");
      const lines = buffer.split("\r\n").filter((l) => l.length > 0);
      const last = lines[lines.length - 1];
      if (last && isFinalReplyLine(last)) {
        cleanup();
        resolve({ code: Number(last.slice(0, 3)), text: lines.join("\n") });
      }
    };
    const onError = (err: Error) => {
      cleanup();
      reject(err);
    };
    const cleanup = () => {
      socket.off("data", onData);
      socket.off("error", onError);
    };
    socket.on("data", onData);
    socket.on("error", onError);
  });
}

function writeCommand(socket: Socket | TLSSocket, command: string): void {
  socket.write(`${command}\r\n`);
}

function escapeDotStuffing(body: string): string {
  // RFC 5321 4.5.2 transparency: a line starting with "." in DATA must
  // be escaped to ".." so the server doesn't treat it as the end-of-data
  // marker.
  return body
    .split("\r\n")
    .map((line) => (line.startsWith(".") ? `.${line}` : line))
    .join("\r\n");
}

export interface OutboundEmail {
  to: string;
  subject: string;
  text: string;
}

/**
 * Sends one real email over a real SMTP session. Connects with implicit
 * TLS when `config.secure`, otherwise plaintext-then-STARTTLS (the
 * standard port-587 submission convention) -- never sends AUTH
 * credentials over an unencrypted channel either way. Every SMTP command
 * checks the server's real reply code; any non-2xx/3xx reply at any
 * stage aborts the session and is surfaced verbatim in the returned
 * error, never swallowed.
 */
export async function sendEmail(email: OutboundEmail): Promise<SendEmailResult> {
  const config = resolveSmtpConfig();
  if (!config) {
    return { ok: false, error: "SMTP not configured (SMTP_HOST/SMTP_FROM unset)" };
  }

  return new Promise((resolve) => {
    let settled = false;
    const finish = (result: SendEmailResult) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };

    let socket: Socket | TLSSocket = config.secure
      ? tlsConnect({ host: config.host, port: config.port, servername: config.host })
      : new Socket();

    const timeout = setTimeout(() => {
      socket.destroy();
      finish({ ok: false, error: `SMTP connection to ${config.host}:${config.port} timed out` });
    }, 10_000);

    socket.on("error", (err) => {
      clearTimeout(timeout);
      finish({ ok: false, error: err instanceof Error ? err.message : String(err) });
    });

    const run = async () => {
      try {
        await readReply(socket); // 220 greeting
        await sendCmd(`EHLO platform-console`);

        if (!config.secure) {
          await sendCmd(`STARTTLS`);
          const plainSocket = socket as Socket;
          socket = tlsConnect({ socket: plainSocket, host: config.host, servername: config.host });
          await new Promise<void>((res, rej) => {
            (socket as TLSSocket).once("secureConnect", () => res());
            (socket as TLSSocket).once("error", rej);
          });
          await sendCmd(`EHLO platform-console`);
        }

        if (config.user && config.pass) {
          await sendCmd(`AUTH LOGIN`);
          await sendCmd(Buffer.from(config.user, "utf8").toString("base64"));
          await sendCmd(Buffer.from(config.pass, "utf8").toString("base64"));
        }

        await sendCmd(`MAIL FROM:<${config.from}>`);
        await sendCmd(`RCPT TO:<${email.to}>`);
        await sendCmd(`DATA`, [354]);

        const headers = [
          `From: ${config.from}`,
          `To: ${email.to}`,
          `Subject: ${email.subject}`,
          `Content-Type: text/plain; charset=utf-8`,
        ].join("\r\n");
        const body = `${headers}\r\n\r\n${escapeDotStuffing(email.text)}\r\n.`;
        writeCommand(socket, body);
        const dataReply = await readReply(socket);
        if (dataReply.code < 200 || dataReply.code >= 300) {
          throw new Error(`SMTP DATA rejected: ${dataReply.text}`);
        }

        writeCommand(socket, `QUIT`);
        clearTimeout(timeout);
        socket.end();
        finish({ ok: true });
      } catch (err) {
        clearTimeout(timeout);
        socket.destroy();
        finish({ ok: false, error: err instanceof Error ? err.message : String(err) });
      }
    };

    async function sendCmd(command: string, acceptCodes?: number[]): Promise<void> {
      writeCommand(socket, command);
      const reply = await readReply(socket);
      const accept = acceptCodes ?? [200, 250, 220, 235];
      if (reply.code >= 200 && reply.code < 400 && (accept.length === 0 || reply.code < 300 || accept.includes(reply.code))) {
        return;
      }
      throw new Error(`SMTP command "${command.split(" ")[0]}" failed: ${reply.text}`);
    }

    if (config.secure) {
      (socket as TLSSocket).once("secureConnect", run);
    } else {
      socket.once("connect", run);
      (socket as Socket).connect(config.port, config.host);
    }
  });
}

/** Simple, real RFC 5322-shaped validation -- rejects the obviously
 * malformed (no "@", whitespace, no dot in the domain part) without
 * pretending to implement the full grammar. Good enough gate for a
 * subscribe form; the real correctness check is the SMTP server's own
 * RCPT TO acceptance at send time. */
export function isPlausibleEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}
