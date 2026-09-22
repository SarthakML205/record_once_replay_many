export function maskSsn(last4) {
  return `***-**-${last4}`;
}

export function formatMoney(value) {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return String(value ?? "");
  }
  return amount.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function memberDisplayName(member) {
  return `${member.last_name}, ${member.first_name}`;
}

export function nextConfirmationId() {
  const stamp = Date.now().toString(36).toUpperCase();
  const rand = Math.floor(Math.random() * 900 + 100);
  return `CNF-${stamp}-${rand}`;
}
