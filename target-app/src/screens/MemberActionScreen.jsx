import { formatMoney, maskSsn, memberDisplayName } from "../format.js";

export default function MemberActionScreen({
  member,
  accountName,
  initialDeposit,
  onAccountNameChange,
  onInitialDepositChange,
  onOpenSavings,
  onFreeze,
  onBack,
  alertText,
  receipt,
}) {
  return (
    <table cellPadding="0" cellSpacing="0" style={{ width: "100%" }}>
      <tbody>
        <tr>
          <td>
            <span
              onClick={onBack}
              style={{ color: "#0000ee", textDecoration: "underline", cursor: "pointer" }}
            >
              Return to Inquiry
            </span>
          </td>
        </tr>
        <tr>
          <td>
            <span style={{ fontWeight: "bold" }}>Member Servicing</span>
          </td>
        </tr>
        <tr>
          <td>
            <table cellPadding="4" cellSpacing="0" style={{ border: "1px solid #808080" }}>
              <tbody>
                <tr>
                  <td>
                    <span>Member ID</span>
                  </td>
                  <td>
                    <span>{member.member_id}</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>Name</span>
                  </td>
                  <td>
                    <span>{memberDisplayName(member)}</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>SSN</span>
                  </td>
                  <td>
                    <span>{maskSsn(member.ssn_last4)}</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>Account Type</span>
                  </td>
                  <td>
                    <span>{member.account_type}</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>Current Balance</span>
                  </td>
                  <td>
                    <span>{formatMoney(member.balance)}</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>Status</span>
                  </td>
                  <td>
                    <span>{member.status}</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>High-Yield Savings Balance</span>
                  </td>
                  <td>
                    <span>
                      {member.hy_savings_balance
                        ? formatMoney(member.hy_savings_balance)
                        : "No high-yield savings sub-account"}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        {alertText ? (
          <tr>
            <td>
              <table cellPadding="6" cellSpacing="0" style={{ border: "1px solid #990000", background: "#fde8e8", marginTop: 10 }}>
                <tbody>
                  <tr>
                    <td>
                      <span>{alertText}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        ) : null}
        {receipt ? (
          <tr>
            <td>
              <table cellPadding="6" cellSpacing="0" style={{ border: "1px solid #006600", background: "#e8fde8", marginTop: 10 }}>
                <tbody>
                  <tr>
                    <td>
                      <span>Transaction complete. Confirmation ID {receipt.id}</span>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <span>{receipt.detail}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        ) : null}
        <tr>
          <td>
            <table cellPadding="4" cellSpacing="0" style={{ marginTop: 14 }}>
              <tbody>
                <tr>
                  <td colSpan="2">
                    <span style={{ fontWeight: "bold" }}>Open High-Yield Savings Sub-Account</span>
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>Account Name</span>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={accountName}
                      onChange={(event) => onAccountNameChange(event.target.value)}
                    />
                  </td>
                </tr>
                <tr>
                  <td>
                    <span>Initial Deposit</span>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={initialDeposit}
                      onChange={(event) => onInitialDepositChange(event.target.value)}
                    />
                  </td>
                </tr>
                <tr>
                  <td></td>
                  <td>
                    <span
                      onClick={onOpenSavings}
                      style={{
                        border: "1px solid #333",
                        background: "#d4d0c8",
                        padding: "2px 10px",
                        cursor: "pointer",
                      }}
                    >
                      Submit Request
                    </span>
                  </td>
                </tr>
                <tr>
                  <td colSpan="2">
                    <span
                      onClick={onFreeze}
                      style={{
                        border: "1px solid #333",
                        background: "#d4d0c8",
                        padding: "2px 10px",
                        cursor: "pointer",
                      }}
                    >
                      Freeze Account
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
