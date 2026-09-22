export default function SearchScreen({ query, onQueryChange, onSearch, alertText }) {
  return (
    <table cellPadding="0" cellSpacing="0" style={{ width: "100%" }}>
      <tbody>
        <tr>
          <td>
            <span style={{ fontWeight: "bold" }}>Member Inquiry</span>
          </td>
        </tr>
        <tr>
          <td>
            <table cellPadding="4" cellSpacing="0">
              <tbody>
                <tr>
                  <td>
                    <span>Member ID</span>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={query}
                      onChange={(event) => onQueryChange(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          onSearch();
                        }
                      }}
                    />
                  </td>
                  <td>
                    <span
                      onClick={onSearch}
                      style={{
                        border: "1px solid #333",
                        background: "#d4d0c8",
                        padding: "2px 10px",
                        cursor: "pointer",
                      }}
                    >
                      Search
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
              <table cellPadding="6" cellSpacing="0" style={{ border: "1px solid #990000", background: "#fde8e8" }}>
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
      </tbody>
    </table>
  );
}
