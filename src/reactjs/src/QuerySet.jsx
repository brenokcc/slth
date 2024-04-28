import { useState, useEffect } from "react";
import { format } from "./Formatter";
import { Action } from "./Action";
import { Field } from "./Form";
import { request } from "./Request";
import { Info } from "./Message";
import { GridLayout } from "./Layout";
import { Button } from "./Button";
import { Link } from "./Link";
import { Icon, IconButton } from "./Icon";
import toLabelCase from "./Utils";
import ComponentFactory from "./Root";

function QuerySet(props) {
  if (props.data.id == null) props.data.id = Math.random();
  const [data, setData] = useState(props.data);

  function renderTitleText() {
    if (data.attrname) {
      return <h2 data-label={toLabelCase(data.title)}>{data.title}</h2>;
    } else {
      return <h1 data-label={toLabelCase(data.title)}>{data.title}</h1>;
    }
  }

  function renderTitle() {
    const syle = {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
    };
    return (
      <div style={syle}>
        {renderTitleText()}
        <i
          id={"loader-" + props.data.id}
          style={{ display: "none" }}
          className="fa-solid fa-circle-notch fa-spin fa-1x"
        ></i>
      </div>
    );
  }

  function showLoader(show) {
    document.getElementById("loader-" + props.data.id).style.display = show
      ? "block"
      : "none";
  }

  function renderTabs() {
    return (
      data.subsets && (
        <div
          style={{
            display: "inline-block",
            textAlign: "center",
            width: "100%",
            margin: "auto",
            paddingBottom: 20,
            lineHeight: "2.5rem",
          }}
        >
          {data.subsets.map(function (subset, i) {
            var active =
              data.subset === subset.name || (!data.subset && i == 0);
            return (
              <Link
                key={Math.random()}
                href="#"
                style={{
                  paddingBottom: 5,
                  paddingLeft: 15,
                  paddingRight: 15,
                  fontWeight: active ? "bold" : "normal",
                  borderBottom: active ? "solid 3px #2670e8" : "solid 3px #DDD",
                  textDecoration: "none",
                  color: "#0c326f",
                }}
                onClick={function (e) {
                  e.preventDefault();
                  setSubset(subset.name);
                }}
                dataLabel={toLabelCase(subset.label)}
              >
                <div style={{ display: "inline-block" }}>
                  {subset.label} ({subset.count})
                </div>
              </Link>
            );
          })}
        </div>
      )
    );
  }

  function setSubset(name) {
    const input = document.getElementById("subset-" + props.data.id);
    input.value = name || "";
    reload();
  }

  function calendarFilter(day, month, year) {
    const form = document.getElementById("form-" + props.data.id);
    form.querySelector("input[name=" + data.calendar.field + "__day]").value =
      day || "";
    form.querySelector("input[name=" + data.calendar.field + "__month]").value =
      month || "";
    form.querySelector("input[name=" + data.calendar.field + "__year]").value =
      year || "";
    reload();
  }

  function renderCalendar() {
    if (data.calendar) {
      const days = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"];
      const months = [
        "JANEIRO",
        "FEVEVEIRO",
        "MARÇO",
        "ABRIL",
        "MAIO",
        "JUNHO",
        "JULHO",
        "AGOSTO",
        "SETEMRO",
        "OUTUBRO",
        "NOVEMBRO",
        "DEZEMBRO",
      ];
      const table = {
        width: "100%",
        borderSpacing: 0,
        borderCollapse: "collapse",
        marginTop: 15,
        marginBottom: 15,
      };

      const day = {
        marginLeft: "17",
        textAlign: "right",
        paddingRight: 2,
        paddingTop: 2,
        float: "right",
        fontSize: "0.8rem",
      };
      const td = {
        verticalAlign: "top",
        width: "14.2%",
        height: 55,
        border: "solid 1px #EEE",
      };

      const number = {
        backgroundColor: "#1351b4",
        borderRadius: "50%",
        color: "white",
        display: "block",
        width: 30,
        height: 30,
        margin: "auto",
        cursor: "pointer",
        lineHeight: "2rem",
      };
      const total = {
        padding: 10,
        textAlign: "center",
      };
      const arrows = {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
      };

      const today = new Date();
      const selected = data.calendar.day
        ? new Date(
            data.calendar.year,
            data.calendar.month - 1,
            data.calendar.day
          )
        : null;
      var rows = [[], [], [], [], [], []];
      var month = data.calendar.month - 1;
      var start = new Date(data.calendar.year, data.calendar.month - 1, 1);
      while (start.getDay() > 1) start.setDate(start.getDate() - 1);
      var i = 0;
      while (start.getMonth() <= month || rows[i].length < 7) {
        if (rows[i].length == 7) i += 1;
        if (i == 5) break;
        rows[i].push({
          date: start.getDate(),
          total: data.calendar.total[start.toLocaleDateString("pt-BR")],
          today: start.getDate() === today.getDate(),
          selected: selected ? start.getDate() == selected.getDate() : false,
        });
        start.setDate(start.getDate() + 1);
      }
      return (
        <div className="calendar">
          <div style={arrows}>
            <div>
              <IconButton
                default
                icon="arrow-left"
                onClick={() =>
                  calendarFilter(
                    null,
                    data.calendar.previous.month,
                    data.calendar.previous.year
                  )
                }
              />
            </div>
            <div>
              <h3 align="center" style={{ margin: 0 }}>
                {months[data.calendar.month - 1]} {data.calendar.year}
              </h3>
              {data.calendar.day && (
                <div align="center" className={day}>
                  {new Date(
                    data.calendar.year,
                    data.calendar.month - 1,
                    data.calendar.day
                  ).toLocaleDateString("pt-BR")}
                  <Icon
                    default
                    icon="x"
                    onClick={() =>
                      calendarFilter(
                        null,
                        data.calendar.month,
                        data.calendar.year
                      )
                    }
                    style={{ marginLeft: 10, cursor: "pointer" }}
                  />
                </div>
              )}
            </div>
            <div>
              <IconButton
                default
                icon="arrow-right"
                onClick={() =>
                  calendarFilter(
                    null,
                    data.calendar.next.month,
                    data.calendar.next.year
                  )
                }
              />
            </div>
          </div>
          <table style={table}>
            <thead>
              <tr>
                {days.map((day) => (
                  <th key={Math.random()}>{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={Math.random()}>
                  {row.map((item) => (
                    <td key={Math.random()} style={td}>
                      <div style={day}>
                        {item.today ? (
                          <span style={{ textDecoration: "underline" }}>
                            {item.date}
                          </span>
                        ) : (
                          item.date + item.today
                        )}
                      </div>
                      {item.total && (
                        <div
                          style={total}
                          onClick={() =>
                            calendarFilter(
                              item.date,
                              data.calendar.month,
                              data.calendar.year
                            )
                          }
                        >
                          <div style={number}>
                            <span
                              style={{
                                textDecoration: item.selected
                                  ? "underline"
                                  : "normal",
                              }}
                            >
                              {item.total}
                            </span>
                          </div>
                        </div>
                      )}
                      {!item.total && <div style={total}>&nbsp;</div>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
  }

  function renderHeader(data) {
    const style = {
      textAlign: "left",
      verticalAlign: "top",
      //backgroundColor: "#f0f0f0",
      //lineHeight: "3rem",
      //borderBottom: "solid 1px #1351b4",
      padding: 5,
    };
    if (window.innerWidth < 800) {
    } else {
      return (
        <tr>
          {data.map(function (item) {
            return (
              item.label != "ID" && (
                <th key={Math.random()} style={style} className="bold">
                  {item.label}
                </th>
              )
            );
          })}
          <th style={style}></th>
        </tr>
      );
    }
  }

  function renderRow(row) {
    const td = { borderBottom: "solid 1px #DDD", padding: 5 };
    const actions = { borderBottom: "solid 1px #DDD", lineHeight: "3rem" };
    if (window.innerWidth < 800) {
      return (
        <tr key={Math.random()}>
          <td key={Math.random()} style={td}>
            {row.title}
          </td>
          <td style={actions}>
            <div style={{ verticalAlign: "center", textAlign: "right" }}>
              {row.actions.map(function (action) {
                return (
                  <Action key={Math.random()} data={action} default compact />
                );
              })}
            </div>
          </td>
        </tr>
      );
    } else {
      return (
        <tr key={Math.random()}>
          {row.data.map(function (field) {
            return (
              field.label != "ID" && (
                <td key={Math.random()} style={td}>
                  {format(field.value)}
                </td>
              )
            );
          })}
          <td style={actions}>
            <div style={{ verticalAlign: "center" }}>
              {row.actions.map(function (action) {
                return (
                  <Action key={Math.random()} data={action} default compact />
                );
              })}
            </div>
          </td>
        </tr>
      );
    }
  }

  function renderRows() {
    const div = {
      width: "100%",
      overflowX: "auto",
    };
    const table = {
      width: "100%",
      lineHeight: "2rem",
      borderSpacing: 0,
    };
    if (data.data.length > 0) {
      return (
        <div style={div}>
          <table style={table}>
            <thead>{renderHeader(data.data[0].data)}</thead>
            <tbody>
              {data.data.map(function (item) {
                return renderRow(item);
              })}
            </tbody>
          </table>
        </div>
      );
    } else {
      return (
        <Info
          data={{
            text: "Nenhum registro encontrado.",
          }}
        ></Info>
      );
    }
  }

  function setPage(page) {
    const form = document.getElementById("form-" + props.data.id);
    const input = form.querySelector("input[name=page]");
    input.value = page;
    reload();
  }

  function renderPaginator() {
    const form = document.getElementById("form-" + props.data.id);
    if (form) {
      const input = form.querySelector("input[name=page]");
      if (input) input.value = data.pagination.page.current;
    }
    const style = {
      display: "flex",
      justifyContent: "space-between",
      lineHeight: "4rem",
      alignItems: "baseline",
    };
    const inline = {
      display: "inline",
      paddingRight: 10,
    };
    const select = {
      marginLeft: 10,
      marginRight: 10,
      height: "2.5rem",
      paddingLeft: 5,
      paddingRight: 5,
      textAlign: "center",
    };
    return (
      data.pagination.page.total > 1 && (
        <div style={style}>
          <div>
            <div style={inline}>
              Exibir
              <select
                style={select}
                name="page_size"
                onChange={() => setPage(1)}
                value={data.pagination.page.size}
              >
                {data.pagination.page.sizes.map(function (size) {
                  return <option key={Math.random()}>{size}</option>;
                })}
              </select>
            </div>
            <div style={inline}>|</div>

            <div style={inline}>
              {data.pagination.start} - {data.pagination.end} de {data.total}
            </div>
          </div>
          <div>
            <div style={inline}>
              <span>Página</span>
              <input
                type="text"
                name="page"
                defaultValue={data.pagination.page.current}
                style={{
                  width: 30,
                  marginLeft: 10,
                  marginRight: 10,
                  height: "2rem",
                  textAlign: "center",
                }}
                onKeyDown={function (e) {
                  if (e.key == "Enter") {
                    e.preventDefault();
                    setPage(
                      e.target.value < 0
                        ? 1
                        : Math.min(e.target.value, data.pagination.page.total)
                    );
                  }
                }}
              />
              <div style={inline}>|</div>
              {data.pagination.page.previous && (
                <Button
                  icon="chevron-left"
                  default
                  display="inline"
                  onClick={() => setPage(data.pagination.page.previous)}
                />
              )}
              {data.pagination.page.next && (
                <Button
                  icon="chevron-right"
                  default
                  display="inline"
                  onClick={() => setPage(data.pagination.page.next)}
                />
              )}
            </div>
          </div>
        </div>
      )
    );
  }

  function renderActions() {
    return (
      <div align="right" style={{ marginTop: 20, marginBottom: 20 }}>
        {data.actions.map(function (action) {
          return <Action key={Math.random()} data={action} primary />;
        })}
      </div>
    );
  }

  function renderSearchFilterPanel() {
    const style = {};
    const searching = data.search.length > 0;
    const filtering = data.filters.length > 0;
    if (searching || filtering) {
      const field = {
        name: "q",
        value: "",
        mask: null,
        type: "text",
        label: "Palavras-chaves",
      };
      return (
        <>
          <GridLayout width={250}>
            {searching && (
              <div style={style}>
                <Field data={field} />
              </div>
            )}
            {filtering &&
              data.filters.map(function (field) {
                return (
                  field.type != "hidden" && (
                    <div key={Math.random()} style={style}>
                      <Field data={field} />
                    </div>
                  )
                );
              })}
            <div style={style}>
              <Button onClick={reload} label="Filtrar" default />
            </div>
          </GridLayout>
          {filtering &&
            data.filters.map(function (field) {
              return (
                field.type == "hidden" && (
                  <div key={Math.random()} style={style}>
                    <Field data={field} />
                  </div>
                )
              );
            })}
        </>
      );
    }
  }

  function reload() {
    showLoader(true);
    var url;
    const queryString = new URLSearchParams(
      new FormData(document.getElementById("form-" + props.data.id))
    ).toString();
    if (props.data.url.indexOf("?") > 0)
      url = props.data.url + "&" + queryString;
    else url = props.data.url + "?" + queryString;
    request("GET", url, function (data) {
      setData(data);
      showLoader(false);
    });
  }

  function renderContent() {
    if (data.bi) {
      return (
        <>
          {renderSearchFilterPanel()}
          {data.bi.map(function (items) {
            return (
              <GridLayout width={300} key={Math.random()} alignItems="start">
                {items.map(function (item) {
                  return (
                    <div key={Math.random()}>
                      <ComponentFactory data={item} />
                    </div>
                  );
                })}
              </GridLayout>
            );
          })}
        </>
      );
    } else {
      return (
        <>
          {renderActions()}
          {renderTabs()}
          {renderSearchFilterPanel()}
          {renderCalendar()}
          {renderRows()}
          {renderPaginator()}
        </>
      );
    }
  }

  function render() {
    window[props.data.id] = () => reload();
    const sytle = { backgroundColor: "white", padding: 20 };
    return (
      <div className="reloadable" id={props.data.id} sytle={sytle}>
        <form id={"form-" + props.data.id}>
          <div>{false && JSON.stringify(data)}</div>
          <input type="hidden" name="subset" id={"subset-" + props.data.id} />
          {renderTitle()}
          {renderContent()}
        </form>
      </div>
    );
  }

  return render();
}

export { QuerySet };
export default QuerySet;
