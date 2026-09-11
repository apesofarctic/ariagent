export type Mode = "protect" | "grow" | "guide";

export type Txn = {
  date: string;
  amount: number;
  merchant: string;
  category: string;
};

export type Nudge = {
  title: string;
  message: string;
  action_label: string;
  tool: string;
  tool_args: Record<string, unknown>;
  mode: Mode;
  reasoning: string[];
  regulated: boolean;
  reversible: boolean;
  journey: string[] | null;
};

export type StreamEvent = {
  stage: "sense" | "reason" | "decide" | "explain" | "act" | "done";
  agent: string;
  detail: string;
  mode?: Mode;
  signal?: string;
  action?: "fire" | "hold" | "suppress" | "sequence";
  urgency?: number;
  ev?: number;
  nudge?: Nudge;
  executed?: boolean;
  prepared?: boolean;
  deep_link?: string | null;
  tool?: string;
  signals?: { type: string; mode: Mode; evidence: string[] }[];
};

export type Consent = {
  granted: boolean;
  scopes: Partial<Record<Mode, boolean>>;
  granted_at: string | null;
  revoked_at: string | null;
};

export type Status = {
  data_mode: "demo" | "real";
  consent: Consent;
  use_llm: boolean;
  llm_model: string | null;
  real_data: { count: number; first: string | null; last: string | null; source: string | null };
  demo_source: string;
};

export type Forecast = {
  points: { date: string; balance: number }[];
  daily_spend: number;
  min_balance: number;
  overdraft_risk: boolean;
  buffer: number;
};

export type Profile = {
  profile: {
    name: string;
    current_balance: number;
    recurring: { type: string; day_of_month: number; amount: number }[];
  };
  balance: number;
  real: boolean;
};

export type Inference = {
  id: number;
  ts: string;
  type: string;
  mode: Mode;
  title: string;
  statement: string;
  evidence: string[];
  confidence: number;
};

export type AuditRow = {
  id: number;
  ts: string;
  actor: string;
  action: string;
  detail: string;
  why: string;
  reversible: boolean;
  mode: string;
  status: "executed" | "prepared" | "held" | "suppressed" | "blocked" | "info";
};

export type UploadResult = {
  token: string;
  filename: string;
  columns: string[];
  mapping: Record<string, string | null>;
  preview: string[][];
  total_rows: number;
};

export type ImportResult = {
  imported: number;
  skipped: number;
  errors: string[];
  categorizer: { merchants: number; by_rules: number; by_llm: number; uncategorized: number };
  target: string;
  date_range: [string, string];
};
