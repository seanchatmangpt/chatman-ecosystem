import { createHash, createHmac, createVerify, X509Certificate } from "node:crypto";
import { createRemoteJWKSet, decodeProtectedHeader, importX509, jwtVerify } from "jose";
import { getAuditDbPool, newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getProject, setProjectTier } from "@/lib/k8s";
import { setPlanState, type PlanState } from "@/lib/plan-state";
import { isProjectTier, type ProjectTier } from "@/lib/tiers";

export type MarketplaceProvider = "aws" | "azure" | "gcp";
export type MarketplaceAction =
  | "subscribe" | "renew" | "plan_change" | "quantity_change"
  | "suspend" | "unsubscribe" | "reinstate" | "revoke";

type Acknowledgement = "azure-operation" | "gcp-entitlement" | "gcp-plan-change";

export interface MarketplaceEntitlementEvent {
  provider: MarketplaceProvider;
  eventId: string;
  buyerRef: string;
  productRef: string;
  agreementRef: string;
  entitlementRef: string;
  subscriptionRef: string;
  planRef: string;
  quantity: number;
  action: MarketplaceAction;
  occurredAt: string;
  acknowledgement?: Acknowledgement;
}

export interface TenantBinding {
  provider: MarketplaceProvider;
  buyerRef: string;
  productRef: string;
  projectName: string;
  namespace: string;
  orgId: string;
}

interface PlanBinding {
  provider: MarketplaceProvider;
  productRef: string;
  planRef: string;
  tier: ProjectTier;
}

export interface ResolvedMarketplacePurchase {
  provider: MarketplaceProvider;
  buyerRef: string;
  productRef: string;
  agreementRef: string;
  entitlementRef: string;
  subscriptionRef: string;
  planRef: string;
  quantity: number;
  usageReportingId?: string;
}

export interface MarketplaceBindingInput {
  projectName: string;
  namespace: string;
  orgId: string;
  linkedBy: string;
}

export interface MarketplaceUsage {
  provider: MarketplaceProvider;
  eventId: string;
  buyerRef: string;
  agreementRef: string;
  subscriptionRef: string;
  planRef: string;
  dimension: string;
  units: number;
  startTime: string;
  endTime: string;
  sourceReceipt: string;
  usageReportingId?: string;
}

export interface ApplyMarketplaceEventResult {
  duplicate: boolean;
  event: MarketplaceEntitlementEvent;
  binding: TenantBinding;
  planState: PlanState | null;
  tier: ProjectTier | null;
}

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`REFUSED:MISSING_CONFIG:${name}`);
  return value;
}

function parseArrayEnv<T>(name: string): T[] {
  let parsed: unknown;
  try { parsed = JSON.parse(requiredEnv(name)); }
  catch (error) { throw new Error(`REFUSED:INVALID_CONFIG:${name}:${(error as Error).message}`); }
  if (!Array.isArray(parsed)) throw new Error(`REFUSED:INVALID_CONFIG:${name}:expected array`);
  return parsed as T[];
}

function validateEvent(event: MarketplaceEntitlementEvent): void {
  for (const [name, value] of Object.entries({
    eventId: event.eventId, buyerRef: event.buyerRef, productRef: event.productRef,
    agreementRef: event.agreementRef, entitlementRef: event.entitlementRef,
    subscriptionRef: event.subscriptionRef, planRef: event.planRef, occurredAt: event.occurredAt,
  })) if (!value.trim()) throw new Error(`REFUSED:MISSING_EVENT_FIELD:${name}`);
  if (!Number.isInteger(event.quantity) || event.quantity < 0) throw new Error("REFUSED:INVALID_EVENT_FIELD:quantity");
  if (Number.isNaN(Date.parse(event.occurredAt))) throw new Error("REFUSED:INVALID_EVENT_FIELD:occurredAt");
  if (!["suspend", "unsubscribe", "revoke"].includes(event.action) && event.quantity === 0) {
    throw new Error("REFUSED:ZERO_ACTIVE_ENTITLEMENT_QUANTITY");
  }
}

async function ledger() {
  const pool = await getAuditDbPool();
  if (!pool) throw new Error("BLOCKED:MARKETPLACE_EVENT_LEDGER_UNAVAILABLE");
  await pool.query(`CREATE TABLE IF NOT EXISTS platform_console.marketplace_events (
    provider text NOT NULL,event_id text NOT NULL,payload_hash text NOT NULL,buyer_ref text NOT NULL,
    product_ref text NOT NULL,agreement_ref text NOT NULL,entitlement_ref text NOT NULL,
    subscription_ref text NOT NULL,plan_ref text NOT NULL,quantity bigint NOT NULL,action text NOT NULL,
    occurred_at timestamptz NOT NULL,status text NOT NULL,error text,applied_at timestamptz,
    PRIMARY KEY(provider,event_id))`);
  await pool.query(`CREATE TABLE IF NOT EXISTS platform_console.marketplace_bindings (
    provider text NOT NULL,buyer_ref text NOT NULL,product_ref text NOT NULL,agreement_ref text NOT NULL,
    entitlement_ref text NOT NULL,subscription_ref text NOT NULL,project_name text NOT NULL,namespace text NOT NULL,
    org_id text NOT NULL,linked_by text NOT NULL,usage_reporting_id text,linked_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(provider,buyer_ref,product_ref),UNIQUE(provider,agreement_ref))`);
  await pool.query(`CREATE TABLE IF NOT EXISTS platform_console.marketplace_usage_events (
    provider text NOT NULL,event_id text NOT NULL,source_receipt text NOT NULL,payload_hash text NOT NULL,
    status text NOT NULL,provider_receipt jsonb,error text,created_at timestamptz NOT NULL DEFAULT now(),
    accepted_at timestamptz,PRIMARY KEY(provider,event_id))`);
  return pool;
}

function hash(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(value), "utf8").digest("hex");
}

async function resolveTenantBinding(event: MarketplaceEntitlementEvent): Promise<TenantBinding> {
  const pool = await ledger();
  const result = await pool.query<{
    buyer_ref: string; product_ref: string; project_name: string; namespace: string; org_id: string;
  }>(`SELECT buyer_ref,product_ref,project_name,namespace,org_id FROM platform_console.marketplace_bindings
      WHERE provider=$1 AND buyer_ref=$2 AND product_ref=$3`, [event.provider,event.buyerRef,event.productRef]);
  const row = result.rows[0];
  if (row) return { provider:event.provider,buyerRef:row.buyer_ref,productRef:row.product_ref,
    projectName:row.project_name,namespace:row.namespace,orgId:row.org_id };
  const raw = process.env.MARKETPLACE_TENANT_BINDINGS_JSON?.trim();
  if (raw) {
    const found = parseArrayEnv<TenantBinding>("MARKETPLACE_TENANT_BINDINGS_JSON").find((candidate) =>
      candidate.provider === event.provider && candidate.buyerRef === event.buyerRef && candidate.productRef === event.productRef);
    if (found) return found;
  }
  throw new Error(`REFUSED:NO_TENANT_BINDING:${event.provider}:${event.buyerRef}:${event.productRef}`);
}

function resolveTier(event: MarketplaceEntitlementEvent): ProjectTier | null {
  if (["suspend", "unsubscribe", "revoke"].includes(event.action)) return null;
  const found = parseArrayEnv<PlanBinding>("MARKETPLACE_PLAN_BINDINGS_JSON").find((candidate) =>
    candidate.provider === event.provider && candidate.productRef === event.productRef && candidate.planRef === event.planRef);
  if (!found || !isProjectTier(found.tier)) throw new Error(`REFUSED:NO_PLAN_BINDING:${event.provider}:${event.productRef}:${event.planRef}`);
  return found.tier;
}

function desiredPlanState(action: MarketplaceAction): PlanState | null {
  if (["suspend", "unsubscribe", "revoke"].includes(action)) return "suspended";
  if (["subscribe", "renew", "reinstate"].includes(action)) return "active";
  return null;
}

async function claimEvent(event: MarketplaceEntitlementEvent): Promise<boolean> {
  const pool = await ledger(); const payloadHash = hash(event);
  const inserted = await pool.query<{event_id:string}>(
    `INSERT INTO platform_console.marketplace_events(provider,event_id,payload_hash,buyer_ref,product_ref,agreement_ref,
     entitlement_ref,subscription_ref,plan_ref,quantity,action,occurred_at,status)
     VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'processing') ON CONFLICT DO NOTHING RETURNING event_id`,
    [event.provider,event.eventId,payloadHash,event.buyerRef,event.productRef,event.agreementRef,event.entitlementRef,
      event.subscriptionRef,event.planRef,event.quantity,event.action,event.occurredAt]);
  if (inserted.rows.length === 1) return false;
  const existing = await pool.query<{payload_hash:string;status:string}>(
    `SELECT payload_hash,status FROM platform_console.marketplace_events WHERE provider=$1 AND event_id=$2`,
    [event.provider,event.eventId]);
  const row = existing.rows[0];
  if (!row) throw new Error("BLOCKED:MARKETPLACE_EVENT_CLAIM_LOST");
  if (row.payload_hash !== payloadHash) throw new Error("REFUSED:IDEMPOTENCY_KEY_CONFLICT");
  if (row.status === "applied") return true;
  if (row.status === "processing") throw new Error("BLOCKED:MARKETPLACE_EVENT_ALREADY_PROCESSING");
  const reclaimed = await pool.query<{event_id:string}>(
    `UPDATE platform_console.marketplace_events SET status='processing',error=NULL
     WHERE provider=$1 AND event_id=$2 AND status='failed' RETURNING event_id`, [event.provider,event.eventId]);
  if (reclaimed.rows.length !== 1) throw new Error("BLOCKED:MARKETPLACE_EVENT_RECLAIM_FAILED");
  return false;
}

async function markEvent(event: MarketplaceEntitlementEvent, status: "applied"|"failed", error?: string): Promise<void> {
  const pool = await ledger();
  await pool.query(`UPDATE platform_console.marketplace_events SET status=$3,error=$4,
    applied_at=CASE WHEN $3='applied' THEN now() ELSE applied_at END WHERE provider=$1 AND event_id=$2`,
    [event.provider,event.eventId,status,error ?? null]);
}

export async function applyMarketplaceEntitlementEvent(event: MarketplaceEntitlementEvent): Promise<ApplyMarketplaceEventResult> {
  validateEvent(event); const binding = await resolveTenantBinding(event); const tier = resolveTier(event);
  const state = desiredPlanState(event.action); const duplicate = await claimEvent(event);
  if (duplicate) return {duplicate,event,binding,planState:state,tier};
  try {
    if (tier) {
      const result = await setProjectTier(binding.projectName,binding.namespace,tier);
      if (!result.ok) throw new Error(`BLOCKED:PROJECT_TIER_ACTUATION:${result.error}`);
    }
    if (state) {
      const result = await setPlanState(binding.namespace,state,`marketplace:${event.provider}:${event.eventId}`);
      if (!result.ok) throw new Error(`BLOCKED:PLAN_STATE_ACTUATION:${result.error}`);
    }
    writeAuditLogEntry({timestamp:new Date().toISOString(),actor:`marketplace:${event.provider}:${event.eventId}`,
      method:"POST",path:`/api/marketplace/${event.provider}/webhook`,status:200,requestId:newRequestId(),orgId:binding.orgId});
    await markEvent(event,"applied"); return {duplicate:false,event,binding,planState:state,tier};
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await markEvent(event,"failed",message).catch(()=>{}); throw error;
  }
}

interface AwsSnsEnvelope { Type?:string;MessageId?:string;TopicArn?:string;Subject?:string;Message?:string;
  Timestamp?:string;SignatureVersion?:string;Signature?:string;SigningCertURL?:string;SigningCertUrl?:string;
  SubscribeURL?:string;Token?:string }

function awsSigningString(message: AwsSnsEnvelope): string {
  const names = message.Type === "Notification"
    ? ["Message","MessageId",...(message.Subject?["Subject"]:[]),"Timestamp","TopicArn","Type"]
    : ["SubscriptionConfirmation","UnsubscribeConfirmation"].includes(message.Type ?? "")
      ? ["Message","MessageId","SubscribeURL","Timestamp","Token","TopicArn","Type"] : [];
  if (!names.length) throw new Error(`REFUSED:AWS_SNS_TYPE:${message.Type ?? "missing"}`);
  return names.map((name)=>`${name}\n${String(message[name as keyof AwsSnsEnvelope] ?? "")}\n`).join("");
}

async function verifyAwsSns(rawBody: string): Promise<AwsSnsEnvelope> {
  const message = JSON.parse(rawBody) as AwsSnsEnvelope;
  if (message.TopicArn !== requiredEnv("AWS_MARKETPLACE_SNS_TOPIC_ARN")) throw new Error("REFUSED:AWS_SNS_TOPIC_MISMATCH");
  if (!["1","2"].includes(message.SignatureVersion ?? "")) throw new Error("REFUSED:AWS_SNS_SIGNATURE_VERSION");
  const certUrl = new URL(message.SigningCertURL ?? message.SigningCertUrl ?? "");
  if (certUrl.protocol !== "https:" || !/^sns\.[a-z0-9-]+\.amazonaws\.com(?:\.cn)?$/.test(certUrl.hostname.toLowerCase()) ||
      !/^\/SimpleNotificationService-[A-Za-z0-9_-]+\.pem$/.test(certUrl.pathname)) throw new Error("REFUSED:AWS_SNS_CERT_URL");
  const response = await fetch(certUrl,{cache:"no-store"});
  if (!response.ok) throw new Error(`BLOCKED:AWS_SNS_CERT_FETCH:${response.status}`);
  const certificate = new X509Certificate(await response.text()); const now = Date.now();
  if (now < Date.parse(certificate.validFrom) || now > Date.parse(certificate.validTo)) throw new Error("REFUSED:AWS_SNS_CERT_EXPIRED");
  const verifier = createVerify(message.SignatureVersion === "2" ? "RSA-SHA256" : "RSA-SHA1");
  verifier.update(awsSigningString(message),"utf8"); verifier.end();
  if (!verifier.verify(certificate.publicKey,message.Signature ?? "","base64")) throw new Error("REFUSED:AWS_SNS_SIGNATURE");
  return message;
}

function awsAction(value: string): MarketplaceAction {
  const action = value.toLowerCase().replaceAll("-","_");
  if (action.includes("unsubscribe")||action.includes("cancel")) return "unsubscribe";
  if (action.includes("suspend")) return "suspend"; if (action.includes("reinstate")) return "reinstate";
  if (action.includes("plan")||action.includes("entitlement")) return "plan_change";
  if (action.includes("renew")) return "renew"; if (action.includes("subscribe")) return "subscribe";
  throw new Error(`REFUSED:AWS_ACTION:${value}`);
}

async function parseAwsEvent(rawBody:string):Promise<MarketplaceEntitlementEvent>{
  const envelope=await verifyAwsSns(rawBody); if(envelope.Type!=="Notification") throw new Error(`REFUSED:AWS_SNS_REQUIRES_OPERATOR:${envelope.Type}`);
  const detail=JSON.parse(envelope.Message??"{}") as Record<string,unknown>;
  const get=(...keys:string[])=>keys.map((k)=>detail[k]).find((v)=>typeof v==="string"&&v.trim()) as string|undefined ?? "";
  const productRef=get("product-code","ProductCode","productCode"); if(productRef!==requiredEnv("AWS_MARKETPLACE_PRODUCT_CODE")) throw new Error("REFUSED:AWS_PRODUCT_MISMATCH");
  const agreementRef=get("license-arn","LicenseArn","licenseArn");
  return {provider:"aws",eventId:envelope.MessageId??"",buyerRef:get("customer-aws-account-id","CustomerAWSAccountId","customerAWSAccountId"),
    productRef,agreementRef,entitlementRef:agreementRef,subscriptionRef:agreementRef,planRef:get("plan","Plan","dimension","Dimension")||"default",
    quantity:Number(detail.quantity??detail.Quantity??1),action:awsAction(get("action","Action","eventType","type")),occurredAt:envelope.Timestamp??""};
}

async function microsoftPublisherToken():Promise<string>{
  const tenantId=requiredEnv("MICROSOFT_MARKETPLACE_TENANT_ID");
  const body=new URLSearchParams({grant_type:"client_credentials",client_id:requiredEnv("MICROSOFT_MARKETPLACE_APP_ID"),
    client_secret:requiredEnv("MICROSOFT_MARKETPLACE_CLIENT_SECRET"),scope:"20e940b3-4c77-4b0b-9a53-9e16a1b010a7/.default"});
  const response=await fetch(`https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/token`,{method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},body,cache:"no-store"});
  const payload=await response.json().catch(()=>({})) as {access_token?:string};
  if(!response.ok||!payload.access_token) throw new Error(`BLOCKED:AZURE_TOKEN:${response.status}`); return payload.access_token;
}

async function verifyMicrosoftWebhook(rawBody:string,headers:Headers):Promise<Record<string,unknown>>{
  const authorization=headers.get("authorization")??""; if(!authorization.startsWith("Bearer ")) throw new Error("REFUSED:AZURE_MISSING_BEARER");
  const tenantId=requiredEnv("MICROSOFT_MARKETPLACE_TENANT_ID");
  const verified=await jwtVerify(authorization.slice(7),createRemoteJWKSet(new URL(`https://login.microsoftonline.com/${tenantId}/discovery/v2.0/keys`)),
    {audience:requiredEnv("MICROSOFT_MARKETPLACE_APP_ID")});
  if(verified.payload.tid!==tenantId) throw new Error("REFUSED:AZURE_TENANT_MISMATCH");
  if((verified.payload.appid??verified.payload.azp)!==requiredEnv("MICROSOFT_MARKETPLACE_CALLER_APP_ID")) throw new Error("REFUSED:AZURE_CALLER_MISMATCH");
  return JSON.parse(rawBody) as Record<string,unknown>;
}

async function microsoftOperation(subscriptionId:string,operationId:string):Promise<Record<string,unknown>>{
  const token=await microsoftPublisherToken(); const response=await fetch(
    `https://marketplaceapi.microsoft.com/api/saas/subscriptions/${encodeURIComponent(subscriptionId)}/operations/${encodeURIComponent(operationId)}?api-version=2018-08-31`,
    {headers:{authorization:`Bearer ${token}`},cache:"no-store"});
  if(!response.ok) throw new Error(`BLOCKED:AZURE_GET_OPERATION:${response.status}`); return await response.json() as Record<string,unknown>;
}

function azureAction(action:string):MarketplaceAction{
  const map:Record<string,MarketplaceAction>={subscribe:"subscribe",changeplan:"plan_change",changequantity:"quantity_change",renew:"renew",suspend:"suspend",unsubscribe:"unsubscribe",reinstate:"reinstate"};
  const found=map[action.toLowerCase()]; if(!found) throw new Error(`REFUSED:AZURE_ACTION:${action}`); return found;
}

async function parseAzureEvent(rawBody:string,headers:Headers):Promise<MarketplaceEntitlementEvent>{
  const body=await verifyMicrosoftWebhook(rawBody,headers); const subscriptionId=String(body.subscriptionId??""); const activityId=String(body.activityId??body.id??"");
  const operation=await microsoftOperation(subscriptionId,activityId); const offerId=String(body.offerId??operation.offerId??"");
  if(offerId!==requiredEnv("MICROSOFT_MARKETPLACE_OFFER_ID")) throw new Error("REFUSED:AZURE_OFFER_MISMATCH");
  const subscription=(body.subscription??operation.subscription??{}) as Record<string,unknown>; const beneficiary=(subscription.beneficiary??body.beneficiary??{}) as Record<string,unknown>;
  const purchaser=(subscription.purchaser??body.purchaser??{}) as Record<string,unknown>; const actionRaw=String(body.action??operation.action??"");
  return {provider:"azure",eventId:activityId,buyerRef:String(beneficiary.tenantId??purchaser.tenantId??body.beneficiaryTenantId??""),productRef:offerId,
    agreementRef:subscriptionId,entitlementRef:subscriptionId,subscriptionRef:subscriptionId,planRef:String(body.planId??operation.planId??""),quantity:Number(body.quantity??operation.quantity??1),
    action:azureAction(actionRaw),occurredAt:String(body.timeStamp??body.timestamp??new Date().toISOString()),
    ...(["changeplan","changequantity","reinstate"].includes(actionRaw.toLowerCase())?{acknowledgement:"azure-operation" as const}:{})};
}

async function googleAccessToken():Promise<string>{
  const explicit=process.env.GCP_MARKETPLACE_ACCESS_TOKEN?.trim(); if(explicit) return explicit;
  const response=await fetch("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",{headers:{"Metadata-Flavor":"Google"},cache:"no-store"});
  const payload=await response.json().catch(()=>({})) as {access_token?:string};
  if(!response.ok||!payload.access_token) throw new Error(`BLOCKED:GCP_ACCESS_TOKEN:${response.status}`); return payload.access_token;
}

export async function googleEntitlement(providerId:string,entitlementId:string):Promise<Record<string,unknown>>{
  const response=await fetch(`https://cloudcommerceprocurement.googleapis.com/v1/providers/${encodeURIComponent(providerId)}/entitlements/${encodeURIComponent(entitlementId)}`,
    {headers:{authorization:`Bearer ${await googleAccessToken()}`},cache:"no-store"});
  if(!response.ok) throw new Error(`BLOCKED:GCP_GET_ENTITLEMENT:${response.status}`); return await response.json() as Record<string,unknown>;
}

async function verifyGooglePush(rawBody:string,headers:Headers):Promise<Record<string,unknown>>{
  const authorization=headers.get("authorization")??""; if(!authorization.startsWith("Bearer ")) throw new Error("REFUSED:GCP_MISSING_BEARER");
  const verified=await jwtVerify(authorization.slice(7),createRemoteJWKSet(new URL("https://www.googleapis.com/oauth2/v3/certs")),
    {audience:requiredEnv("GCP_MARKETPLACE_PUBSUB_AUDIENCE"),issuer:["https://accounts.google.com","accounts.google.com"]});
  if(verified.payload.email!==requiredEnv("GCP_MARKETPLACE_PUBSUB_SERVICE_ACCOUNT")||verified.payload.email_verified!==true) throw new Error("REFUSED:GCP_PUSH_IDENTITY_MISMATCH");
  const wrapper=JSON.parse(rawBody) as {message?:{messageId?:string;publishTime?:string;data?:string}}; if(!wrapper.message?.data) throw new Error("REFUSED:GCP_MISSING_PUBSUB_DATA");
  const event=JSON.parse(Buffer.from(wrapper.message.data,"base64").toString("utf8")) as Record<string,unknown>;
  if(!event.eventId&&wrapper.message.messageId) event.eventId=wrapper.message.messageId; if(!event.publishTime&&wrapper.message.publishTime) event.publishTime=wrapper.message.publishTime; return event;
}

export function gcpAction(eventType:string):MarketplaceAction{
  const map:Record<string,MarketplaceAction>={ENTITLEMENT_CREATION_REQUESTED:"subscribe",ENTITLEMENT_ACTIVE:"subscribe",ENTITLEMENT_OFFER_ACCEPTED:"subscribe",
    ENTITLEMENT_PLAN_CHANGE_REQUESTED:"plan_change",ENTITLEMENT_PLAN_CHANGED:"plan_change",ENTITLEMENT_PENDING_CANCELLATION:"suspend",ENTITLEMENT_CANCELLED:"unsubscribe"};
  const found=map[eventType]; if(!found) throw new Error(`REFUSED:GCP_EVENT_TYPE:${eventType}`); return found;
}
function normalizeGcpAccount(value:unknown):string{const raw=String(value??"").trim();return raw.includes("/")?raw.split("/").filter(Boolean).at(-1)??"":raw;}

async function parseGcpEvent(rawBody:string,headers:Headers):Promise<MarketplaceEntitlementEvent>{
  const event=await verifyGooglePush(rawBody,headers); const providerId=String(event.providerId??requiredEnv("GCP_MARKETPLACE_PROVIDER_ID"));
  if(providerId!==requiredEnv("GCP_MARKETPLACE_PROVIDER_ID")) throw new Error("REFUSED:GCP_PROVIDER_MISMATCH");
  const pending=(event.entitlement??{}) as Record<string,unknown>; const entitlementId=String(pending.id??""); const current=await googleEntitlement(providerId,entitlementId);
  const productRef=String(current.product??pending.newProduct??""); if(productRef!==requiredEnv("GCP_MARKETPLACE_PRODUCT_ID")) throw new Error("REFUSED:GCP_PRODUCT_MISMATCH");
  const eventType=String(event.eventType??""); return {provider:"gcp",eventId:String(event.eventId??""),buyerRef:normalizeGcpAccount(current.account),productRef,
    agreementRef:entitlementId,entitlementRef:entitlementId,subscriptionRef:entitlementId,planRef:String(current.plan??pending.newPendingPlan??"default"),quantity:Number(current.quantity??1),
    action:gcpAction(eventType),occurredAt:String(pending.updateTime??current.updateTime??event.publishTime??new Date().toISOString()),
    ...(eventType==="ENTITLEMENT_CREATION_REQUESTED"?{acknowledgement:"gcp-entitlement" as const}:eventType==="ENTITLEMENT_PLAN_CHANGE_REQUESTED"?{acknowledgement:"gcp-plan-change" as const}:{})};
}

export async function authenticateMarketplaceEntitlement(provider:MarketplaceProvider,rawBody:string,headers:Headers):Promise<MarketplaceEntitlementEvent>{
  const event=provider==="aws"?await parseAwsEvent(rawBody):provider==="azure"?await parseAzureEvent(rawBody,headers):await parseGcpEvent(rawBody,headers); validateEvent(event); return event;
}

async function acknowledgeMicrosoft(event:MarketplaceEntitlementEvent,status:"Success"|"Failure"):Promise<void>{
  const response=await fetch(`https://marketplaceapi.microsoft.com/api/saas/subscriptions/${encodeURIComponent(event.subscriptionRef)}/operations/${encodeURIComponent(event.eventId)}?api-version=2018-08-31`,
    {method:"PATCH",headers:{authorization:`Bearer ${await microsoftPublisherToken()}`,"content-type":"application/json"},body:JSON.stringify({status}),cache:"no-store"});
  if(!response.ok&&response.status!==409) throw new Error(`BLOCKED:AZURE_OPERATION_ACK:${response.status}`);
}

async function acknowledgeGoogle(event:MarketplaceEntitlementEvent,success:boolean,reason?:string):Promise<void>{
  if(!event.acknowledgement?.startsWith("gcp-")) return; const token=await googleAccessToken(); const providerId=requiredEnv("GCP_MARKETPLACE_PROVIDER_ID");
  let suffix:string; let body:Record<string,unknown>={};
  if(event.acknowledgement==="gcp-entitlement"){suffix=success?":approve":":reject"; if(!success) body={reason:(reason??"local admission failed").slice(0,256)};}
  else {suffix=success?":approvePlanChange":":rejectPlanChange"; body=success?{pendingPlanName:event.planRef}:{reason:(reason??"local plan admission failed").slice(0,256)};}
  const response=await fetch(`https://cloudcommerceprocurement.googleapis.com/v1/providers/${encodeURIComponent(providerId)}/entitlements/${encodeURIComponent(event.entitlementRef)}${suffix}`,
    {method:"POST",headers:{authorization:`Bearer ${token}`,"content-type":"application/json"},body:JSON.stringify(body),cache:"no-store"});
  if(!response.ok&&response.status!==409) throw new Error(`BLOCKED:GCP_ENTITLEMENT_ACK:${response.status}`);
}

export async function acknowledgeMarketplaceEntitlement(event:MarketplaceEntitlementEvent,success:boolean,reason?:string):Promise<void>{
  if(event.acknowledgement==="azure-operation") return acknowledgeMicrosoft(event,success?"Success":"Failure");
  return acknowledgeGoogle(event,success,reason);
}

interface AwsCredentials{accessKeyId:string;secretAccessKey:string;sessionToken?:string}
function hmac(key:Buffer|string,value:string):Buffer{return createHmac("sha256",key).update(value,"utf8").digest();}
function sha256(value:string):string{return createHash("sha256").update(value,"utf8").digest("hex");}

async function awsCredentials():Promise<AwsCredentials>{
  const accessKeyId=process.env.AWS_ACCESS_KEY_ID?.trim(),secretAccessKey=process.env.AWS_SECRET_ACCESS_KEY?.trim();
  if(accessKeyId&&secretAccessKey) return {accessKeyId,secretAccessKey,...(process.env.AWS_SESSION_TOKEN?.trim()?{sessionToken:process.env.AWS_SESSION_TOKEN.trim()}:{})};
  const relative=process.env.AWS_CONTAINER_CREDENTIALS_RELATIVE_URI?.trim(),full=process.env.AWS_CONTAINER_CREDENTIALS_FULL_URI?.trim(); let endpoint="";
  if(relative) endpoint=`http://169.254.170.2${relative}`; if(full){const parsed=new URL(full);if(!(parsed.protocol==="http:"&&["169.254.170.2","169.254.170.23","127.0.0.1","localhost"].includes(parsed.hostname))) throw new Error("REFUSED:AWS_CONTAINER_CREDENTIAL_URI");endpoint=parsed.toString();}
  if(!endpoint) throw new Error("BLOCKED:AWS_SHORT_LIVED_CREDENTIALS_UNAVAILABLE");
  const headers:Record<string,string>={}; if(process.env.AWS_CONTAINER_AUTHORIZATION_TOKEN?.trim()) headers.authorization=process.env.AWS_CONTAINER_AUTHORIZATION_TOKEN.trim();
  const response=await fetch(endpoint,{headers,cache:"no-store"}); const payload=await response.json().catch(()=>({})) as {AccessKeyId?:string;SecretAccessKey?:string;Token?:string};
  if(!response.ok||!payload.AccessKeyId||!payload.SecretAccessKey) throw new Error(`BLOCKED:AWS_CONTAINER_CREDENTIALS:${response.status}`);
  return {accessKeyId:payload.AccessKeyId,secretAccessKey:payload.SecretAccessKey,...(payload.Token?{sessionToken:payload.Token}:{})};
}

async function awsJsonRpc(host:string,target:string,payload:Record<string,unknown>):Promise<Record<string,unknown>>{
  const credentials=await awsCredentials(),body=JSON.stringify(payload),region="us-east-1",service="aws-marketplace",now=new Date();
  const amzDate=now.toISOString().replace(/[:-]|\.\d{3}/g,""),date=amzDate.slice(0,8); const headers:Record<string,string>={"content-type":"application/x-amz-json-1.1",host,"x-amz-date":amzDate,"x-amz-target":target};
  if(credentials.sessionToken) headers["x-amz-security-token"]=credentials.sessionToken; const names=Object.keys(headers).sort(); const canonicalHeaders=names.map((name)=>`${name}:${headers[name].trim()}\n`).join("");
  const signedHeaders=names.join(";"),canonicalRequest=["POST","/","",canonicalHeaders,signedHeaders,sha256(body)].join("\n"),scope=`${date}/${region}/${service}/aws4_request`;
  const stringToSign=["AWS4-HMAC-SHA256",amzDate,scope,sha256(canonicalRequest)].join("\n"); const signing=hmac(hmac(hmac(hmac(`AWS4${credentials.secretAccessKey}`,date),region),service),"aws4_request");
  const signature=createHmac("sha256",signing).update(stringToSign,"utf8").digest("hex"); const authorization=`AWS4-HMAC-SHA256 Credential=${credentials.accessKeyId}/${scope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;
  const response=await fetch(`https://${host}/`,{method:"POST",headers:{...headers,authorization},body,cache:"no-store"}); const result=await response.json().catch(()=>({})) as Record<string,unknown>;
  if(!response.ok) throw new Error(`BLOCKED:AWS_MARKETPLACE_API:${target}:${response.status}:${JSON.stringify(result)}`); return result;
}

async function resolveAwsRegistration(token:string):Promise<ResolvedMarketplacePurchase>{
  const resolved=await awsJsonRpc("metering.marketplace.us-east-1.amazonaws.com","AWSMPMeteringService.ResolveCustomer",{RegistrationToken:token});
  const buyerRef=String(resolved.CustomerAWSAccountId??""),productRef=String(resolved.ProductCode??""),agreementRef=String(resolved.LicenseArn??"");
  if(!buyerRef||!agreementRef||productRef!==requiredEnv("AWS_MARKETPLACE_PRODUCT_CODE")) throw new Error("REFUSED:AWS_RESOLVE_IDENTITY_MISMATCH");
  const entitlements=await awsJsonRpc("entitlement.marketplace.us-east-1.amazonaws.com","AWSMPEntitlementService.GetEntitlements",{ProductCode:productRef,Filter:{LICENSE_ARN:[agreementRef]},MaxResults:25});
  const rows=Array.isArray(entitlements.Entitlements)?entitlements.Entitlements as Array<Record<string,unknown>>:[]; if(!rows.length) throw new Error("REFUSED:AWS_NO_ENTITLEMENT");
  const dimension=process.env.AWS_MARKETPLACE_PLAN_DIMENSION?.trim(); const selected=dimension?rows.find((row)=>row.Dimension===dimension):rows.length===1?rows[0]:undefined;
  if(!selected) throw new Error("REFUSED:AWS_ENTITLEMENT_AMBIGUOUS"); const value=(selected.Value??{}) as Record<string,unknown>; const quantity=Number(value.IntegerValue??value.DoubleValue??1);
  return {provider:"aws",buyerRef,productRef,agreementRef,entitlementRef:agreementRef,subscriptionRef:agreementRef,planRef:String(selected.Dimension??dimension??"default"),quantity:Number.isFinite(quantity)&&quantity>=0?quantity:1};
}

async function resolveMicrosoftRegistration(tokenValue:string):Promise<ResolvedMarketplacePurchase>{
  const token=await microsoftPublisherToken(),id=globalThis.crypto.randomUUID(); const response=await fetch("https://marketplaceapi.microsoft.com/api/saas/subscriptions/resolve?api-version=2018-08-31",
    {method:"POST",headers:{authorization:`Bearer ${token}`,"content-type":"application/json","x-ms-marketplace-token":tokenValue,"x-ms-requestid":id,"x-ms-correlationid":id},cache:"no-store"});
  const payload=await response.json().catch(()=>({})) as Record<string,unknown>; if(!response.ok) throw new Error(`BLOCKED:AZURE_RESOLVE:${response.status}:${JSON.stringify(payload)}`);
  const subscriptionId=String(payload.id??""),offerId=String(payload.offerId??""),beneficiary=(payload.beneficiary??{}) as Record<string,unknown>,purchaser=(payload.purchaser??{}) as Record<string,unknown>;
  const buyerRef=String(beneficiary.tenantId??purchaser.tenantId??""); if(!subscriptionId||!buyerRef||offerId!==requiredEnv("MICROSOFT_MARKETPLACE_OFFER_ID")) throw new Error("REFUSED:AZURE_RESOLVE_IDENTITY_MISMATCH");
  return {provider:"azure",buyerRef,productRef:offerId,agreementRef:subscriptionId,entitlementRef:subscriptionId,subscriptionRef:subscriptionId,planRef:String(payload.planId??"default"),quantity:Number(payload.quantity??1)};
}

async function resolveGoogleRegistration(token:string):Promise<ResolvedMarketplacePurchase>{
  const header=decodeProtectedHeader(token); if(!header.kid||typeof header.kid!=="string") throw new Error("REFUSED:GCP_SIGNUP_KID_MISSING");
  const response=await fetch("https://www.googleapis.com/robot/v1/metadata/x509/cloud-commerce-partner@system.gserviceaccount.com",{cache:"no-store"});
  const certs=await response.json().catch(()=>({})) as Record<string,string>; if(!response.ok||!certs[header.kid]) throw new Error(`BLOCKED:GCP_SIGNUP_CERTS:${response.status}`);
  const issuer="https://www.googleapis.com/robot/v1/metadata/x509/cloud-commerce-partner@system.gserviceaccount.com";
  const verified=await jwtVerify(token,await importX509(certs[header.kid],header.alg??"RS256"),{issuer,audience:requiredEnv("GCP_MARKETPLACE_PARTNER_DOMAIN")});
  const buyerRef=String(verified.payload.sub??""); if(!buyerRef) throw new Error("REFUSED:GCP_SIGNUP_ACCOUNT_MISSING"); const orders=Array.isArray(verified.payload.orders)?verified.payload.orders as Array<Record<string,unknown>>:[];
  const productRef=requiredEnv("GCP_MARKETPLACE_PRODUCT_ID"),selected=orders.find((order)=>String(order.product??order.productId??"")===productRef)??orders[0]; const entitlementRef=String(selected?.entitlement??selected?.entitlementId??buyerRef);
  const providerId=requiredEnv("GCP_MARKETPLACE_PROVIDER_ID"),accessToken=await googleAccessToken(); const approval=await fetch(`https://cloudcommerceprocurement.googleapis.com/v1/providers/${encodeURIComponent(providerId)}/accounts/${encodeURIComponent(buyerRef)}:approve`,
    {method:"POST",headers:{authorization:`Bearer ${accessToken}`,"content-type":"application/json"},body:JSON.stringify({approvalName:"signup"}),cache:"no-store"});
  if(!approval.ok&&approval.status!==409) throw new Error(`BLOCKED:GCP_ACCOUNT_APPROVE:${approval.status}`);
  return {provider:"gcp",buyerRef,productRef,agreementRef:entitlementRef,entitlementRef,subscriptionRef:entitlementRef,planRef:String(selected?.plan??selected?.planId??"default"),quantity:Number(selected?.quantity??1)};
}

export async function resolveMarketplaceRegistration(provider:MarketplaceProvider,token:string):Promise<ResolvedMarketplacePurchase>{
  if(!token.trim()) throw new Error("REFUSED:MARKETPLACE_TOKEN_REQUIRED"); return provider==="aws"?resolveAwsRegistration(token.trim()):provider==="azure"?resolveMicrosoftRegistration(token.trim()):resolveGoogleRegistration(token.trim());
}

async function activateMicrosoft(purchase:ResolvedMarketplacePurchase):Promise<void>{
  const response=await fetch(`https://marketplaceapi.microsoft.com/api/saas/subscriptions/${encodeURIComponent(purchase.subscriptionRef)}/activate?api-version=2018-08-31`,
    {method:"POST",headers:{authorization:`Bearer ${await microsoftPublisherToken()}`,"content-type":"application/json"},body:JSON.stringify({planId:purchase.planRef,quantity:purchase.quantity}),cache:"no-store"});
  if(!response.ok&&response.status!==409) throw new Error(`BLOCKED:AZURE_ACTIVATE:${response.status}`);
}

export async function linkMarketplacePurchase(purchase:ResolvedMarketplacePurchase,input:MarketplaceBindingInput):Promise<TenantBinding>{
  for(const [name,value] of Object.entries(input)) if(!String(value).trim()) throw new Error(`REFUSED:MISSING_BINDING_FIELD:${name}`);
  const project=await getProject(input.projectName); if(!project.ok) throw new Error(`BLOCKED:PROJECT_LOOKUP:${project.error}`); if(!project.data||project.data.namespace!==input.namespace) throw new Error("REFUSED:PROJECT_NAMESPACE_MISMATCH");
  const pool=await ledger(); const existing=await pool.query<{buyer_ref:string;product_ref:string;agreement_ref:string;project_name:string;namespace:string;org_id:string}>(
    `SELECT buyer_ref,product_ref,agreement_ref,project_name,namespace,org_id FROM platform_console.marketplace_bindings WHERE (provider=$1 AND buyer_ref=$2 AND product_ref=$3) OR (provider=$1 AND agreement_ref=$4)`,
    [purchase.provider,purchase.buyerRef,purchase.productRef,purchase.agreementRef]); const row=existing.rows[0];
  if(row && (row.buyer_ref!==purchase.buyerRef||row.product_ref!==purchase.productRef||row.agreement_ref!==purchase.agreementRef||row.project_name!==input.projectName||row.namespace!==input.namespace||row.org_id!==input.orgId)) throw new Error("REFUSED:MARKETPLACE_BINDING_CONFLICT");
  if(!row) await pool.query(`INSERT INTO platform_console.marketplace_bindings(provider,buyer_ref,product_ref,agreement_ref,entitlement_ref,subscription_ref,project_name,namespace,org_id,linked_by,usage_reporting_id)
    VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,[purchase.provider,purchase.buyerRef,purchase.productRef,purchase.agreementRef,purchase.entitlementRef,purchase.subscriptionRef,input.projectName,input.namespace,input.orgId,input.linkedBy,purchase.usageReportingId??null]);
  if(purchase.provider==="azure") await activateMicrosoft(purchase);
  await applyMarketplaceEntitlementEvent({provider:purchase.provider,eventId:`registration:${purchase.agreementRef}`,buyerRef:purchase.buyerRef,productRef:purchase.productRef,
    agreementRef:purchase.agreementRef,entitlementRef:purchase.entitlementRef,subscriptionRef:purchase.subscriptionRef,planRef:purchase.planRef,
    quantity:Number.isFinite(purchase.quantity)&&purchase.quantity>=0?Math.trunc(purchase.quantity):1,action:"subscribe",occurredAt:new Date().toISOString()});
  return {provider:purchase.provider,buyerRef:purchase.buyerRef,productRef:purchase.productRef,projectName:input.projectName,namespace:input.namespace,orgId:input.orgId};
}

async function reportAwsUsage(usage:MarketplaceUsage):Promise<Record<string,unknown>>{
  const timestamp=new Date(usage.startTime); if(Number.isNaN(timestamp.getTime())) throw new Error("REFUSED:AWS_USAGE_TIMESTAMP");
  const payload=await awsJsonRpc("metering.marketplace.us-east-1.amazonaws.com","AWSMPMeteringService.BatchMeterUsage",{UsageRecords:[{LicenseArn:usage.agreementRef,CustomerAWSAccountId:usage.buyerRef,Dimension:usage.dimension,Quantity:Math.trunc(usage.units),Timestamp:Math.floor(timestamp.getTime()/1000)}]});
  if(Array.isArray(payload.UnprocessedRecords)&&payload.UnprocessedRecords.length) throw new Error(`BLOCKED:AWS_METER_UNPROCESSED:${JSON.stringify(payload.UnprocessedRecords)}`); return payload;
}

async function reportMicrosoftUsage(usage:MarketplaceUsage):Promise<Record<string,unknown>>{
  const response=await fetch("https://marketplaceapi.microsoft.com/api/usageEvent?api-version=2018-08-31",{method:"POST",headers:{authorization:`Bearer ${await microsoftPublisherToken()}`,"content-type":"application/json","x-ms-requestid":usage.eventId,"x-ms-correlationid":usage.eventId},
    body:JSON.stringify({resourceId:usage.subscriptionRef,quantity:usage.units,dimension:usage.dimension,effectiveStartTime:usage.startTime,planId:usage.planRef}),cache:"no-store"});
  const payload=await response.json().catch(()=>({})) as Record<string,unknown>; if(!response.ok&&response.status!==409) throw new Error(`BLOCKED:AZURE_METER:${response.status}:${JSON.stringify(payload)}`); return payload;
}

async function reportGoogleUsage(usage:MarketplaceUsage):Promise<Record<string,unknown>>{
  if(!usage.usageReportingId) throw new Error("REFUSED:GCP_USAGE_REPORTING_ID_REQUIRED"); const token=await googleAccessToken(),service=requiredEnv("GCP_MARKETPLACE_SERVICE_NAME");
  const operation={operationId:usage.eventId,operationName:"Chatman Marketplace Usage",consumerId:usage.usageReportingId,startTime:usage.startTime,endTime:usage.endTime,
    metricValueSets:[{metricName:usage.dimension,metricValues:[{int64Value:String(usage.units)}]}]};
  const call=async(verb:"check"|"report")=>{const response=await fetch(`https://servicecontrol.googleapis.com/v1/services/${encodeURIComponent(service)}:${verb}`,
    {method:"POST",headers:{authorization:`Bearer ${token}`,"content-type":"application/json"},body:JSON.stringify({operations:[operation]}),cache:"no-store"}); const payload=await response.json().catch(()=>({})) as Record<string,unknown>;
    if(!response.ok) throw new Error(`BLOCKED:GCP_SERVICE_CONTROL_${verb.toUpperCase()}:${response.status}`); return payload;};
  const checked=await call("check"); if(Array.isArray(checked.checkErrors)&&checked.checkErrors.length) throw new Error(`REFUSED:GCP_SERVICE_CONTROL_CHECK:${JSON.stringify(checked.checkErrors)}`); return call("report");
}

async function admitUsage(input:MarketplaceUsage):Promise<{duplicate:boolean;usage:MarketplaceUsage;receipt?:Record<string,unknown>}>{
  let usage=input; if(!usage.eventId.trim()||!usage.buyerRef.trim()||!usage.agreementRef.trim()||!usage.subscriptionRef.trim()||!usage.planRef.trim()||!usage.dimension.trim()||!usage.sourceReceipt.trim()||
    !Number.isFinite(usage.units)||usage.units<=0||Number.isNaN(Date.parse(usage.startTime))||Number.isNaN(Date.parse(usage.endTime))||Date.parse(usage.endTime)<=Date.parse(usage.startTime)) throw new Error("REFUSED:INVALID_USAGE");
  const pool=await ledger(); const binding=await pool.query<{subscription_ref:string;usage_reporting_id:string|null}>(`SELECT subscription_ref,usage_reporting_id FROM platform_console.marketplace_bindings WHERE provider=$1 AND buyer_ref=$2 AND agreement_ref=$3`,[usage.provider,usage.buyerRef,usage.agreementRef]);
  const bound=binding.rows[0]; if(!bound||bound.subscription_ref!==usage.subscriptionRef) throw new Error("REFUSED:USAGE_BINDING_MISMATCH"); if(usage.provider==="gcp"&&!usage.usageReportingId) usage={...usage,usageReportingId:bound.usage_reporting_id??undefined};
  const receipt=await pool.query<{request_id:string}>(`SELECT request_id FROM platform_console.audit_log WHERE castle_receipt_digest=$1 LIMIT 1`,[usage.sourceReceipt]); if(receipt.rows.length!==1) throw new Error("REFUSED:SOURCE_RECEIPT_NOT_IN_TRUSTED_CUSTODY");
  const payloadHash=hash(usage); const inserted=await pool.query<{event_id:string}>(`INSERT INTO platform_console.marketplace_usage_events(provider,event_id,source_receipt,payload_hash,status) VALUES($1,$2,$3,$4,'processing') ON CONFLICT DO NOTHING RETURNING event_id`,[usage.provider,usage.eventId,usage.sourceReceipt,payloadHash]);
  if(inserted.rows.length===1) return {duplicate:false,usage}; const existing=await pool.query<{payload_hash:string;status:string;provider_receipt:Record<string,unknown>|null}>(`SELECT payload_hash,status,provider_receipt FROM platform_console.marketplace_usage_events WHERE provider=$1 AND event_id=$2`,[usage.provider,usage.eventId]); const row=existing.rows[0];
  if(!row) throw new Error("BLOCKED:USAGE_CLAIM_LOST"); if(row.payload_hash!==payloadHash) throw new Error("REFUSED:USAGE_IDEMPOTENCY_CONFLICT"); if(row.status==="accepted") return {duplicate:true,usage,receipt:row.provider_receipt??{}}; if(row.status==="processing") throw new Error("BLOCKED:USAGE_ALREADY_PROCESSING");
  const reclaimed=await pool.query<{event_id:string}>(`UPDATE platform_console.marketplace_usage_events SET status='processing',error=NULL WHERE provider=$1 AND event_id=$2 AND status='failed' RETURNING event_id`,[usage.provider,usage.eventId]); if(reclaimed.rows.length!==1) throw new Error("BLOCKED:USAGE_RECLAIM_FAILED"); return {duplicate:false,usage};
}

async function markUsage(usage:MarketplaceUsage,status:"accepted"|"failed",receipt?:Record<string,unknown>,error?:string):Promise<void>{
  const pool=await ledger(); await pool.query(`UPDATE platform_console.marketplace_usage_events SET status=$3,provider_receipt=$4,error=$5,accepted_at=CASE WHEN $3='accepted' THEN now() ELSE accepted_at END WHERE provider=$1 AND event_id=$2`,
    [usage.provider,usage.eventId,status,receipt?JSON.stringify(receipt):null,error??null]);
}

export async function reportMarketplaceUsage(input:MarketplaceUsage):Promise<Record<string,unknown>>{
  const admitted=await admitUsage(input); if(admitted.duplicate) return {duplicate:true,providerReceipt:admitted.receipt??{}}; const usage=admitted.usage;
  try {const providerReceipt=usage.provider==="aws"?await reportAwsUsage(usage):usage.provider==="azure"?await reportMicrosoftUsage(usage):await reportGoogleUsage(usage); await markUsage(usage,"accepted",providerReceipt);
    writeAuditLogEntry({timestamp:new Date().toISOString(),actor:`marketplace-meter:${usage.provider}:${usage.eventId}`,method:"POST",path:`/api/marketplace/${usage.provider}/usage`,status:200,requestId:newRequestId(),castleReceiptDigest:usage.sourceReceipt}); return {duplicate:false,providerReceipt};}
  catch(error){await markUsage(usage,"failed",undefined,error instanceof Error?error.message:String(error)).catch(()=>{});throw error;}
}
