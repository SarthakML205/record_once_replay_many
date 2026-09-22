import { useEffect, useState } from "react";
import { loadMembers, saveMembers } from "./csv.js";
import { nextConfirmationId } from "./format.js";
import ConfirmModal from "./screens/ConfirmModal.jsx";
import MemberActionScreen from "./screens/MemberActionScreen.jsx";
import ResultsTable from "./screens/ResultsTable.jsx";
import SearchScreen from "./screens/SearchScreen.jsx";

export default function App() {
  const [members, setMembers] = useState([]);
  const [query, setQuery] = useState("");
  const [view, setView] = useState("search");
  const [alertText, setAlertText] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [accountName, setAccountName] = useState("");
  const [initialDeposit, setInitialDeposit] = useState("");
  const [pending, setPending] = useState(null);
  const [receipt, setReceipt] = useState(null);

  const selected = members.find((row) => row.member_id === selectedId) ?? null;

  useEffect(() => {
    loadMembers()
      .then(setMembers)
      .catch(() => setAlertText("Member file unavailable"));
  }, []);

  function persist(nextRows) {
    setMembers(nextRows);
    return saveMembers(nextRows);
  }

  function search() {
    setReceipt(null);
    setPending(null);
    const needle = query.trim();
    if (!needle) {
      setAlertText("Record Not Found");
      setSelectedId("");
      setView("search");
      return;
    }
    const match = members.find((row) => row.member_id.toUpperCase() === needle.toUpperCase());
    if (!match) {
      setAlertText("No matching member found");
      setSelectedId("");
      setView("search");
      return;
    }
    setAlertText("");
    setSelectedId(match.member_id);
    setView("search");
  }

  function openMember() {
    setAlertText("");
    setReceipt(null);
    setAccountName("");
    setInitialDeposit("");
    setPending(null);
    setView("detail");
  }

  function requestOpenSavings() {
    setReceipt(null);
    if (selected.status === "RESTRICTED") {
      setAlertText("Permission denied: account is restricted");
      return;
    }
    if (selected.status === "FROZEN") {
      setAlertText("Account Frozen");
      return;
    }
    if (selected.hy_savings_name) {
      setAlertText("Sub-account already exists");
      return;
    }
    const name = accountName.trim();
    const deposit = Number(initialDeposit);
    if (!name) {
      setAlertText("Account name is required");
      return;
    }
    if (!Number.isFinite(deposit) || deposit <= 0) {
      setAlertText("Initial deposit must be a number greater than 0");
      return;
    }
    setAlertText("");
    setPending({
      kind: "open_savings",
      title: "Confirm irreversible action",
      body: `Open high-yield savings sub-account "${name}" with initial deposit ${deposit}? This cannot be undone from this screen.`,
    });
  }

  function requestFreeze() {
    setReceipt(null);
    if (selected.status === "RESTRICTED") {
      setAlertText("Permission denied: account is restricted");
      return;
    }
    if (selected.status === "FROZEN") {
      setAlertText("Account already frozen");
      return;
    }
    setAlertText("");
    setPending({
      kind: "freeze",
      title: "Confirm irreversible action",
      body: `Freeze member ${selected.member_id}? This cannot be undone from this screen.`,
    });
  }

  async function confirmPending() {
    const confirmationId = nextConfirmationId();
    if (pending.kind === "open_savings") {
      const nextRows = members.map((row) =>
        row.member_id === selected.member_id
          ? {
              ...row,
              hy_savings_name: accountName.trim(),
              hy_savings_balance: String(Number(initialDeposit)),
            }
          : row,
      );
      await persist(nextRows);
      setReceipt({
        id: confirmationId,
        detail: `High-yield savings sub-account opened. Savings balance ${Number(initialDeposit).toFixed(2)}.`,
      });
    } else if (pending.kind === "freeze") {
      const nextRows = members.map((row) =>
        row.member_id === selected.member_id ? { ...row, status: "FROZEN" } : row,
      );
      await persist(nextRows);
      setReceipt({
        id: confirmationId,
        detail: "Account status set to FROZEN.",
      });
    }
    setPending(null);
  }

  return (
    <div style={{ fontFamily: "Tahoma, Verdana, sans-serif", fontSize: 13, color: "#000", padding: 8, background: "#efefe7", minHeight: "100vh" }}>
      <table cellPadding="6" cellSpacing="0" style={{ width: "100%", background: "#000080", color: "#fff" }}>
        <tbody>
          <tr>
            <td>
              <span>CoreServ Member Console</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div style={{ padding: 12, background: "#fff", border: "1px solid #808080" }}>
        {view === "search" ? (
          <div>
            <SearchScreen query={query} onQueryChange={setQuery} onSearch={search} alertText={alertText} />
            {selected && !alertText ? <ResultsTable member={selected} onOpen={openMember} /> : null}
          </div>
        ) : (
          <MemberActionScreen
            member={selected}
            accountName={accountName}
            initialDeposit={initialDeposit}
            onAccountNameChange={setAccountName}
            onInitialDepositChange={setInitialDeposit}
            onOpenSavings={requestOpenSavings}
            onFreeze={requestFreeze}
            onBack={() => {
              setView("search");
              setAlertText("");
              setPending(null);
              setReceipt(null);
              setAccountName("");
              setInitialDeposit("");
            }}
            alertText={alertText}
            receipt={receipt}
          />
        )}
      </div>
      {pending ? (
        <ConfirmModal
          title={pending.title}
          body={pending.body}
          onConfirm={confirmPending}
          onCancel={() => setPending(null)}
        />
      ) : null}
    </div>
  );
}
