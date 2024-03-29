import { ChartFactory } from "./Chart";
import format from "./Formatter";

function Statistics(props) {
  function render1D() {
    var rows = [];
    for (var i = 0; i < props.data.series.length; i++) {
      rows.push([props.data.series[i][0], props.data.series[i][1]]);
    }
    if (props.data.chart)
      return (
        <ChartFactory
          type={props.data.chart}
          title={props.data.title}
          rows={rows}
        />
      );

    return (
      <div className="statistics">
        {props.data.title && <h2>{props.data.title}</h2>}
        <table style={{ width: "100%" }}>
          <tbody>
            {rows.map((row) => (
              <tr key={Math.random()}>
                {row.map((v, i) =>
                  i == 0 ? (
                    <th key={Math.random()}>{v}</th>
                  ) : (
                    <td key={Math.random()}>{format(v)}</td>
                  )
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  function render2D() {
    var headers = [];
    var rows = [];
    var keys = Object.keys(props.data.series);
    var tfoot = [];
    for (var i = 0; i < keys.length; i++) {
      if (i == 0) headers.push("");
      var row = [keys[i]];
      var total = 0;
      for (var j = 0; j < props.data.series[keys[i]].length; j++) {
        var serie = props.data.series[keys[i]];
        if (i == 0) headers.push(serie[j][0]);
        row.push(serie[j][1]);
        total += serie[j][1];
        if (keys.length > 1) {
          if (i == 0) tfoot.push(serie[j][1]);
          else tfoot[j] += serie[j][1];
          if (j > 0 && j == props.data.series[keys[i]].length - 1) {
            if (i == 0) tfoot.push(total);
            else tfoot[j + 1] += total;
          }
        }
      }
      if (row.length > 2) {
        if (i == 0) headers.push("TOTAL");
        row.push(total);
      }
      rows.push(row);
    }
    if (props.data.chart)
      return (
        <ChartFactory
          type={props.data.chart}
          title={props.data.title}
          headers={headers}
          rows={rows}
        />
      );

    return (
      <div className="statistics">
        {props.data.title && <h2>{props.data.title}</h2>}
        <table style={{ width: "100%" }}>
          {headers && (
            <thead>
              <tr>
                {headers.map((k) => (
                  <th key={Math.random()}>{k}</th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {rows.map((row) => (
              <tr key={Math.random()}>
                {row.map((v, i) =>
                  i == 0 ? (
                    <th key={Math.random()}>{v}</th>
                  ) : (
                    <td
                      align="center"
                      style={{
                        backgroundColor:
                          i == row.length - 1 &&
                          headers &&
                          headers[headers.length - 1] == "TOTAL"
                            ? "var(--info-color)"
                            : "inherite",
                      }}
                      key={Math.random()}
                    >
                      {format(v)}
                    </td>
                  )
                )}
              </tr>
            ))}
            {tfoot.length > 0 && (
              <tr key={Math.random()}>
                <th>TOTAL</th>
                {tfoot.map((total) => (
                  <td
                    align="center"
                    style={{ backgroundColor: "var(--info-color)" }}
                    key={Math.random()}
                  >
                    {format(total)}{" "}
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }

  return Array.isArray(props.data.series) ? render1D() : render2D();
}

export { Statistics };
export default Statistics;
