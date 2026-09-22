export default function ConfirmModal({ title, body, onConfirm, onCancel }) {
  return (
    <div
      style={{
        position: "fixed",
        left: 0,
        top: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0,0,0,0.35)",
      }}
    >
      <table
        cellPadding="0"
        cellSpacing="0"
        style={{
          position: "absolute",
          left: "50%",
          top: "30%",
          marginLeft: -180,
          width: 360,
          background: "#fff",
          border: "2px solid #000",
        }}
      >
        <tbody>
          <tr>
            <td style={{ background: "#000080", color: "#fff", padding: 6 }}>
              <span>{title}</span>
            </td>
          </tr>
          <tr>
            <td style={{ padding: 12 }}>
              <span>{body}</span>
            </td>
          </tr>
          <tr>
            <td style={{ padding: 12 }}>
              <span
                onClick={onConfirm}
                style={{
                  border: "1px solid #333",
                  background: "#d4d0c8",
                  padding: "2px 10px",
                  cursor: "pointer",
                  marginRight: 8,
                }}
              >
                Confirm
              </span>
              <span
                onClick={onCancel}
                style={{
                  border: "1px solid #333",
                  background: "#d4d0c8",
                  padding: "2px 10px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
