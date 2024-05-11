import { useState, useEffect } from "react";
import { format } from "./Formatter";
import { Action } from "./Action";
import { Field } from "./Form";
import { request } from "./Request";
import { Theme } from "./Theme";
import { Info } from "./Message";
import { openActionDialog } from "./Modal";
import { GridLayout } from "./Layout";
import { Button } from "./Button";
import { Link } from "./Link";
import { Icon, IconButton } from "./Icon";
import toLabelCase from "./Utils";
import ComponentFactory from "./Root";
import { StyleSheet} from "./StyleSheet.jsx"
import Calendar from "./Calendar.jsx";
import Paginator from "./Paginator.jsx";

function Counter(props) {
  function render() {
    const style = {
      backgroundColor: Theme.colors.primary,
      color: "white",
      borderRadius: "50%",
      minWidth: 13,
      marginLeft: 2,
      padding: 4,
      fontSize: "70%",
      display: "inline-block",
      verticalAlign: "bottom",
      marginBottom: 10,
      lineHeight: 1,
    };
    return <div style={style}>{props.total}</div>;
  }
  return render();
}

function QuerySet(props) {

  StyleSheet(`
    .queryset h1, .queryset h2{
      margin: 0px;
    }
    .queryset .title{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .queryset .title .fa-spin{
      display: none;
    }
    .queryset .tabs{
      text-align: center;
      width: 100%;
      margin: auto;
      padding-bottom: 20px;
      line-height: 2.5rem;
    }
    .queryset .tabs .a{
        padding-bottom: 5px;
        padding-left: 15px;
        padding-right: 15px;
        font-weight: active ? bold : normal;
        text-decoration: none;
    }
  `)

  if (props.data.id == null) props.data.id = Math.random();
  const [data, setData] = useState(props.data);

  function renderTitleText() {
    if (data.attrname) {
      return (
        <h2 data-label={toLabelCase(data.title)}>
          {data.title}
        </h2>
      );
    } else {
      return (
        <h1 data-label={toLabelCase(data.title)}>
          {data.title}
        </h1>
      );
    }
  }

  function renderTitle() {
    return (
      <div className="title">
        {renderTitleText()}
        <i
          id={"loader-" + props.data.id}
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
        <div className="tabs"
        >
          {data.subsets.map(function (subset, i) {
            var active =
              data.subset === subset.name || (!data.subset && i == 0);
            return (
              <Link
                key={Math.random()}
                href="#"
                style={{
                  borderBottom: active ? "solid 3px #2670e8" : 0,
                  color: "#0c326f",
                }}
                onClick={function (e) {
                  e.preventDefault();
                  setSubset(subset.name);
                }}
                dataLabel={toLabelCase(subset.label)}
              >
                {subset.label} <Counter total={subset.count} />
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
    setPage(1);
  }

  function renderCalendar() {
    if (data.calendar) {
      return <Calendar data={data.calendar} onChange={calendarFilter}/>
    }
  }

  function renderHeader(data) {
    const style = {
      textAlign: "left",
      verticalAlign: "top",
      lineHeight: "1.2rem",
      color: Theme.colors.primary,
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
    const actions = {
      borderBottom: "solid 1px #DDD",
      lineHeight: "3rem",
      textAlign: "right",
    };
    if (window.innerWidth < 800) {
      return (
        <tr key={Math.random()}>
          <td key={Math.random()} style={td}>
            {row.title}
          </td>
          <td style={actions}>
            <div style={{ verticalAlign: "center" }}>
              <Icon
                icon="chevron-right"
                onClick={() => openActionDialog(row.actions)}
                style={{ cursor: "pointer", marginRight: 20 }}
              />
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

  function renderData() {
    if (data.data.length > 0) {
      if (data.renderer) {
        if(data.renderer=="cards"){
          return (
            <GridLayout width={300} alignItems="start">
              {data.data.map(function (item) {
                item.type = data.renderer;
                return <div>
                  <ComponentFactory data={item} key={Math.random()} />
                </div>;
              })}
          </GridLayout>
          )
        } else {
          return (
            <div style={{ marginBottom: 15 }}>
              {data.data.map(function (item) {
                item.type = data.renderer;
                return <ComponentFactory data={item} key={Math.random()} />;
              })}
            </div>
          );
        }
      } else {
        return renderTable();
      }
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

  function renderTable() {
    const div = {
      width: "100%",
      overflowX: "auto",
    };
    const table = {
      width: "100%",
      lineHeight: "2rem",
      borderSpacing: 0,
    };
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
  }

  function setPage(page) {
    const form = document.getElementById("form-" + props.data.id);
    const input = form.querySelector("input[name=page]");
    if(input) input.value = page;
    reload();
  }

  function renderPaginator() {
    const form = document.getElementById("form-" + props.data.id);
    if (form) {
      const input = form.querySelector("input[name=page]");
      if (input) input.value = data.pagination.page.current;
    }
    return <Paginator data={data.pagination} onChange={setPage} total={data.total}/>

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

  function scrollTop(){
    const rect = document.getElementById(props.data.id).getBoundingClientRect();
    console.log(rect);
    window.scrollTo(
      { top: rect.x,  behavior: 'smooth' }
    );
  }

  function renderSearchFilterPanel() {
    const style = {
      backgroundColor: "#f8f8f8",
      borderBottom: "solid 1px #DDD",
      marginBottom: 10,
      padding: 10,
    };
    const searching = data.search.length > 0;
    const filtering = data.filters.length > 0;
    if ((data.bi || data.data.length >= 0) && (searching || filtering)) {
      const field = {
        name: "q",
        value: "",
        mask: null,
        type: "text",
        label: "Palavras-chaves",
      };
      return (
        <div style={style}>
          <GridLayout width={250}>
            {searching && (
              <div>
                <Field data={field} />
              </div>
            )}
            {filtering &&
              data.filters.map(function (field) {
                return (
                  field.type != "hidden" && (
                    <div key={Math.random()}>
                      <Field data={field} />
                    </div>
                  )
                );
              })}
            <div>
              <Button onClick={reload} label="Filtrar" icon="filter" />
            </div>
          </GridLayout>
          {filtering &&
            data.filters.map(function (field) {
              return (
                field.type == "hidden" && (
                  <div key={Math.random()}>
                    <Field data={field} />
                  </div>
                )
              );
            })}
        </div>
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
      scrollTop();
    });
  }

  function renderReloader(){
    const style = {color: Theme.colors.primary}
    return props.data.reloadable && <div align="center">
      <i>Ultima atualização em {new Date().toLocaleTimeString()}</i>
      <div><Link style={style} onClick={(e)=>{e.preventDefault(); reload()}}>Atualizar agora</Link></div>
    </div>
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
        <div className="content">
          {renderReloader()}
          {renderActions()}
          {renderTabs()}
          {renderSearchFilterPanel()}
          {renderCalendar()}
          {renderData()}
          {renderPaginator()}
        </div>
      );
    }
  }

  function render() {
    window[props.data.id] = () => reload();
    const sytle = { backgroundColor: "white", padding: 20 };
    return (
      <div className="reloadable queryset" id={props.data.id} sytle={sytle}>
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
