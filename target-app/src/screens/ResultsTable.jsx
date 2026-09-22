import { formatMoney, maskSsn, memberDisplayName } from "../format.js";

export default function ResultsTable({ member, onOpen }) {
  return (
    <table cellPadding="4" cellSpacing="0" style={{ border: "1px solid #808080", marginTop: 12 }}>
      <tbody>
        <tr style={{ background: "#c0c0c0" }}>
          <td>
            <span>Name</span>
          </td>
          <td>
            <span>SSN</span>
          </td>
          <td>
            <span>Account Type</span>
          </td>
          <td>
            <span>Current Balance</span>
          </td>
          <td>
            <span>Status</span>
          </td>
        </tr>
        <tr>
          <td>
            <span
              onClick={onOpen}
              style={{ color: "#0000ee", textDecoration: "underline", cursor: "pointer" }}
            >
              {memberDisplayName(member)}
            </span>
          </td>
          <td>
            <span>{maskSsn(member.ssn_last4)}</span>
          </td>
          <td>
            <span>{member.account_type}</span>
          </td>
          <td>
            <span>{formatMoney(member.balance)}</span>
          </td>
          <td>
            <span>{member.status}</span>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
