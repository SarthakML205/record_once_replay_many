const BASE_COLUMNS = [
  "member_id",
  "first_name",
  "last_name",
  "ssn_last4",
  "account_type",
  "balance",
  "status",
];

const EXTRA_COLUMNS = ["hy_savings_name", "hy_savings_balance"];
const COLUMNS = [...BASE_COLUMNS, ...EXTRA_COLUMNS];

function splitCsvLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        current += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      cells.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  cells.push(current);
  return cells;
}

function escapeCsv(value) {
  const text = value == null ? "" : String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function parseMembersCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.trim() !== "");
  if (lines.length === 0) {
    return [];
  }
  const headers = splitCsvLine(lines[0]).map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header] = cells[index] ?? "";
    });
    EXTRA_COLUMNS.forEach((col) => {
      if (row[col] == null) {
        row[col] = "";
      }
    });
    return row;
  });
}

export function serializeMembersCsv(rows) {
  const header = COLUMNS.join(",");
  const body = rows.map((row) => COLUMNS.map((col) => escapeCsv(row[col] ?? "")).join(","));
  return `${[header, ...body].join("\n")}\n`;
}

export async function loadMembers() {
  const response = await fetch("/data/members.csv", { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Unable to load member file");
  }
  return parseMembersCsv(await response.text());
}

export async function saveMembers(rows) {
  const response = await fetch("/data/members.csv", {
    method: "PUT",
    headers: { "Content-Type": "text/csv" },
    body: serializeMembersCsv(rows),
  });
  if (!response.ok && response.status !== 204) {
    throw new Error("Unable to save member file");
  }
}
