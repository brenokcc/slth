import { React } from "react";
import ReactDOM from "react-dom/client";
import { useState, useEffect } from "react";
import { toLabelCase } from "./Utils";
import { closeDialog, openDialog } from "./Modal";
import { ComponentFactory } from "./Factory";
import { showMessage, Info } from "./Message";
import { request, response } from "./Request.jsx";
import { reloadState } from "./Reloader.jsx";
import { Icon } from "./Icon.jsx";
import { Button } from "./Button.jsx";
import { Action } from "./Action.jsx";

const INPUT_TYPES = [
  "text",
  "password",
  "email",
  "number",
  "date",
  "datetime-regional",
  "file",
  "image",
  "range",
  "search",
  "tel",
  "time",
  "url",
  "week",
  "hidden",
  "color",
];
const INPUT_STYLE = { padding: 15, border: "solid 1px #CCC", borderRadius: 5 };

function formChange(form, url) {
  var data = new FormData(form);
  request("POST", url, formControl, data);
}
function formHide(name) {
  if (name) {
    var fieldset = document.querySelector(".form-fieldset." + name);
    if (fieldset) fieldset.style.display = "none";
    var field = document.querySelector(".form-group." + name);
    if (field) field.style.display = "none";
  }
}
function formShow(name) {
  if (name) {
    var fieldset = document.querySelector(".form-fieldset." + name);
    if (fieldset) fieldset.style.display = "block";
    var field = document.querySelector(".form-group." + name);
    if (field) field.style.display = "inline-block";
  }
}
function formValue(name, value) {
  var group = document.querySelector(".form-group." + name);
  var widget = group.querySelector('*[name="' + name + '"]');
  if (widget.tagName == "INPUT") {
    widget.value = value;
  } else {
    if (widget.tagName == "SELECT") {
      if (widget.style.display != "none") {
        widget.dispatchEvent(
          new CustomEvent("customchange", { detail: { value: value } })
        );
      } else {
        for (var i = 0; i < widget.options.length; i++) {
          if (widget.options[i].value == value) {
            widget.selectedIndex = i;
            break;
          }
        }
      }
    }
  }
}
function formControl(controls) {
  if (controls) {
    for (var i = 0; i < controls.hide.length; i++) formHide(controls.hide[i]);
    for (var i = 0; i < controls.show.length; i++) formShow(controls.show[i]);
    for (var k in controls.set) formValue(k, controls.set[k]);
  }
}

function Instruction(props) {
  function render() {
    const style = {
      color: "#155bcb",
      backgroundColor: "#d4e5ff",
      padding: 20,
      display: "flex",
      justifyContent: "space-between",
      marginTop: 10,
      marginBottom: 10,
    };
    return (
      <div style={style}>
        <div>
          <Icon
            icon="circle-check"
            style={{ color: "#155bcb", marginRight: 20 }}
          />
          {props.data.text}
        </div>
        {props.children && <div>{props.children}</div>}
      </div>
    );
  }
  return render();
}

function Error(props) {
  function render() {
    const style = {
      color: "white",
      display: "none",
      backgroundColor: "#e52207",
      marginTop: 2,
      marginBottom: 2,
      padding: 8,
    };
    return (
      <div style={style} id={props.id}>
        <Icon icon="xmark-circle" style={{ marginRight: 5 }} />
        <span></span>
      </div>
    );
  }
  return render();
}

function HelpText(props) {
  function render() {
    const style = {
      marginTop: 2,
      marginBottom: 2,
      fontStyle: "italic",
    };
    return (
      <div style={style}>
        <span>{props.text}</span>
      </div>
    );
  }
  return render();
}

function Field(props) {
  const id = props.data.name + Math.random();

  function renderLabel() {
    const style = {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "baseline",
    };
    if (props.data.action) props.data.action.modal = true;
    return (
      <div style={style}>
        <label>{props.data.label}</label>
        {props.data.action && (
          <Action data={props.data.action} style={{ padding: 0 }} />
        )}
      </div>
    );
  }
  function renderInput() {
    if (INPUT_TYPES.indexOf(props.data.type) >= 0)
      return <InputField data={props.data} />;
    else if (props.data.type == "choice" && Array.isArray(props.data.choices))
      return <Select data={props.data} />;
    else if (props.data.type == "choice") return <Selector data={props.data} />;
    else if (props.data.type == "decimal")
      return <InputField data={props.data} />;
    else if (props.data.type == "boolean") return <Boolean data={props.data} />;
    else return <span>{props.data.name}</span>;
  }

  function renderError() {
    return (
      <div>
        <Error id={props.data.name + "_error"} />
      </div>
    );
  }

  function renderHelpText() {
    return props.data.help_text && <HelpText text={props.data.help_text} />;
  }

  function render() {
    const style = {
      display: props.data.type == "hidden" ? "none" : "flex",
      flexDirection: "column",
      padding: 5,
    };
    return (
      <div id={id} className={"form-group " + props.data.name} style={style}>
        {renderLabel()}
        {renderInput()}
        {renderHelpText()}
        {renderError()}
      </div>
    );
  }
  return render();
}

function InputField(props) {
  var className = "";
  const id = props.data.name + Math.random();

  if (props.data.mask == "decimal") {
    className = "decimal";
    if (props.data.value)
      props.data.value = Math.round(parseFloat(props.data.value))
        .toFixed(2)
        .replace(".", ",");
  }

  useEffect(() => {
    function inputHandler(masks, max, event) {
      var c = event.target;
      var v = c.value.replace(/\D/g, "");
      var m = c.value.length > max ? 1 : 0;
      VMasker(c).unMask();
      VMasker(c).maskPattern(masks[m]);
      c.value = VMasker.toPattern(v, masks[m]);
    }
    if (props.data.mask) {
      var input = document.getElementById(id);
      if (props.data.mask == "decimal") {
        VMasker(input).maskMoney({
          precision: 2,
          separator: ",",
          delimiter: ".",
        }); // unit: 'R$', suffixUnit: 'reais', zeroCents: true
      } else if (props.data.mask.indexOf("|") > 0) {
        var masks = props.data.mask.split("|");
        VMasker(input).maskPattern(masks[0]);
        input.addEventListener(
          "input",
          inputHandler.bind(undefined, masks, 14),
          false
        );
      } else {
        VMasker(input).maskPattern(props.data.mask);
      }
    }
  }, []);

  function onBlur(e) {
    formChange(e.target.closest("form"), props.data.onchange);
  }

  function onChange(e) {
    if (props.data.type == "file") {
      if (e.target.files) {
        let file = e.target.files[0];
        if (
          ["png", "jpeg", "jpg", "gif"].indexOf(
            file.name.toLowerCase().split(".").slice(-1)[0]
          ) < 0
        )
          return;
        var reader = new FileReader();
        reader.onload = function (event) {
          const MAX_WIDTH = 400;
          var img = document.createElement("img");
          img.id = e.target.id + "img";
          img.style.width = "200px";
          img.style.display = "block";
          img.style.margin = "auto";
          img.style.marginTop = "20px";
          img.onload = function (event2) {
            const ratio = MAX_WIDTH / img.width;
            var canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            canvas.height = canvas.width * (img.height / img.width);
            const oc = document.createElement("canvas");
            const octx = oc.getContext("2d");
            oc.width = img.width * ratio;
            oc.height = img.height * ratio;
            octx.drawImage(img, 0, 0, oc.width, oc.height);
            ctx.drawImage(
              oc,
              0,
              0,
              oc.width * ratio,
              oc.height * ratio,
              0,
              0,
              canvas.width,
              canvas.height
            );
            oc.toBlob(function (blob) {
              e.target.blob = blob;
            });
            const div = document.createElement("div");
            div.appendChild(img);
            e.target.parentNode.appendChild(div);
          };
          img.src = event.target.result;
        };
        reader.readAsDataURL(file);
      }
    }
  }

  function render() {
    var type = props.data.type;
    if (type == "datetime") type = "datetime-regional";
    if (type == "decimal") type = "text";
    if (type == "file") {
      return (
        <input
          className={"form-control " + className}
          type={type}
          name={props.data.name}
          id={id}
          data-label={toLabelCase(props.data.label)}
          readOnly={props.data.read_only}
          onBlur={props.data.onchange ? onBlur : null}
          onChange={onChange}
          style={INPUT_STYLE}
        />
      );
    } else {
      return (
        <input
          className={"form-control " + className}
          type={type}
          name={props.data.name}
          id={id}
          defaultValue={props.data.value}
          data-label={toLabelCase(props.data.label)}
          readOnly={props.data.read_only}
          onBlur={props.data.onchange ? onBlur : null}
          onChange={onChange}
          style={INPUT_STYLE}
        />
      );
    }
  }

  return render();
}

function Selector(props) {
  var initial = [];
  if (Array.isArray(props.data.value)) {
    props.data.value.forEach(function (option, i) {
      initial.push({ id: option.id, value: option.label });
    });
  } else if (props.data.value != null) {
    initial.push({ id: props.data.value.id, value: props.data.value.label });
  }
  const id = props.data.name;
  const id2 = props.data.name + "__autocomplete";
  const multiple = Array.isArray(props.data.value);
  const [seaching, setSearching] = useState(false);
  const [options, setOptions] = useState(null);
  var choosing = false;

  useEffect(() => {
    select(initial);
    document.getElementById(id).addEventListener("customchange", function (e) {
      select(e.detail.value);
      reactTriggerChange(document.getElementById(props.data.name));
    });
  }, []);

  function getSelections() {
    const select = document.getElementById(id);
    if (multiple) {
      const style1 = { padding: 5, display: "inline" };
      const style2 = { cursor: "pointer", marginRight: 5 };
      const style3 = { fontSize: "0.8rem" };
      return (
        <div>
          {select == null &&
            initial.map((option, i) => (
              <div key={Math.random()} style={style1}>
                <span onClick={() => remove(i)} style={style2}>
                  <Icon icon="trash-can" style={style3} />
                </span>
                {option.value}
              </div>
            ))}
          {select != null &&
            Array.from(select.options).map((option, i) => (
              <div key={Math.random()} style={style1}>
                <span onClick={() => remove(i)} style={style2}>
                  <Icon icon="trash-can" style={style3} />
                </span>
                {option.innerHTML}
              </div>
            ))}
        </div>
      );
    }
  }

  function onChange(e) {
    setOptions([]);
  }

  function getSelect() {
    return (
      <select
        onChange={onChange}
        id={id}
        name={props.data.name}
        multiple={multiple}
        readOnly
        style={{ display: "contents" }}
      ></select>
    );
  }

  function getSelector() {
    const style = { ...INPUT_STYLE, ...(props.style || {}) };
    const ul = {
      padding: 0,
      margin: 0,
      border: "solid 1px #CCC",
      marginTop: -1,
      borderRadius: 5,
      maxHeight: 150,
      overflowY: "auto",
    };
    ul.position = "absolute";
    ul.backgroundColor = "white";
    const widget = document.getElementById(id2);
    if (widget) {
      let dialog = null;
      let element = widget;
      let result = null;
      while (
        !result &&
        (element = element.parentElement) instanceof HTMLElement
      ) {
        if (element.matches("dialog")) result = element;
      }
      dialog = result;

      const rect = widget.getBoundingClientRect();
      ul.width = rect.width;
      ul.top = dialog ? 0 : rect.top + rect.height + window.scrollY;
      ul.left = dialog ? 0 : rect.left + window.scrollX;
    }
    const li = { cursor: "pointer", padding: 10 };
    const defaultValue =
      (!multiple && initial.length > 0 && initial[0]["value"]) || "";
    return (
      <>
        <input
          id={id2}
          name={id2}
          type="text"
          className="form-control"
          onFocus={(e) => {
            e.target.select();
            search(e);
          }}
          onChange={search}
          onMouseLeave={onLeaveInput}
          onBlur={onLeaveInput}
          defaultValue={defaultValue}
          style={style}
        ></input>
        {options && seaching && (
          <ul
            style={ul}
            onMouseLeave={hide}
            onMouseEnter={function (e) {
              choosing = true;
            }}
          >
            {options.length == 0 && (
              <li style={li}>Nenhuma opção encontrada.</li>
            )}
            {options.map((option) => (
              <li
                key={Math.random()}
                onClick={() => {
                  setSearching(false);
                  props.onSelect ? props.onSelect(option) : select(option);
                }}
                style={li}
              >
                {option.value}
              </li>
            ))}
          </ul>
        )}
      </>
    );
  }

  function onLeaveInput(e) {
    choosing = false;
    setTimeout(function () {
      hide(e);
    }, 250);
  }

  function hide(e) {
    const widget = document.getElementById(id);
    const input = document.getElementById(id2);
    if (!multiple) {
      if (
        widget.options.length > 0 &&
        input.value != widget.options[0].innerHTML
      ) {
        widget.innerHTML = "";
        input.value = "";
        setSearching(false);
      }
    }
    if (e.target.tagName == "UL") {
      setSearching(false);
    } else {
      if (!choosing) setSearching(false);
    }
  }

  function search(e) {
    const sep = props.data.choices.indexOf("?") < 0 ? "?" : "&";
    setSearching(true);
    request(
      "GET",
      props.data.choices + sep + "term=" + e.target.value,
      function callback(options) {
        setOptions(options);
      }
    );
  }

  function select(value) {
    const widget = document.getElementById(id);
    const input = document.getElementById(id2);
    if (widget.innerHTML == undefined) widget.innerHTML = "";
    if (Array.isArray(value)) {
      widget.innerHTML = value
        .map(
          (item) => `<option selected value="${item.id}">${item.value}</option>`
        )
        .join("");
    } else {
      if (multiple) {
        widget.innerHTML += `<option selected value="${value.id}">${value.value}</option>`;
        input.value = "";
      } else {
        widget.innerHTML = `<option selected value="${value.id}">${value.value}</option>`;
        input.value = value.value;
      }
    }
    if (props.data.onchange)
      formChange(input.closest("form"), props.data.onchange);
  }

  function remove(i) {
    const select = document.getElementById(id);
    var options = Array.from(select.options);
    select.innerHTML = options
      .slice(0, i)
      .concat(options.slice(i + 1))
      .map(
        (item) =>
          `<option selected value="${item.value}">${item.innerHTML}</option>`
      )
      .join("");
    setOptions([]);
  }

  function render() {
    return (
      <>
        {getSelections()}
        {getSelect()}
        {getSelector()}
      </>
    );
  }

  return render();
}

function Textarea(props) {
  function render() {
    return (
      <textarea
        className="form-control"
        id={props.data.name}
        name={props.data.name}
        data-label={toLabelCase(props.data.label)}
        style={{ height: 200 }}
        defaultValue={props.data.value || ""}
      ></textarea>
    );
  }
}

function Boolean(props) {
  var field = props.data;
  field["choices"] = [
    { id: true, text: "Sim" },
    { id: false, text: "Não" },
  ];
  return <Radio data={field} />;
}

function Radio(props) {
  var key = Math.random();
  var field = props.data;

  function checked(choice) {
    if (field.value != null) {
      if (field.value == choice.id) {
        return true;
      } else {
        return field.value.id == choice.id;
      }
    } else {
      return false;
    }
  }

  function toogle(id) {
    var radio = document.getElementById(id);
    if (field["checked"]) radio.checked = false;
  }

  function ischecked(id) {
    var radio = document.getElementById(id);
    field["checked"] = radio.checked;
  }

  function render() {
    return (
      <div className="radio-group">
        {field.choices.map((choice, i) => (
          <div key={key + i}>
            <input
              id={field.name + key + i}
              type="radio"
              name={field.name}
              defaultValue={choice.id}
              defaultChecked={checked(choice)}
              data-label={toLabelCase(choice.text)}
              onClick={function () {
                toogle(field.name + key + i);
              }}
              onMouseEnter={function () {
                ischecked(field.name + key + i);
              }}
            />
            <label htmlFor={field.name + key + i}>{choice.text}</label>
          </div>
        ))}
      </div>
    );
  }
  return render();
}

function Checkbox(props) {
  var key = Math.random();
  var field = props.data;
  function checked(choice) {
    var check = false;
    if (field.value) {
      for (var i = 0; i < field.value.length; i++) {
        var value = field.value[i];
        if (value == choice.id) {
          check = true;
        } else if (value.id == choice.id) {
          check = true;
        }
      }
    }
    return check;
  }

  function render() {
    return (
      <div className="checkbox-group">
        {field.choices.map((choice, i) => (
          <div key={key + i}>
            <input
              id={field.name + key + i}
              type="checkbox"
              name={field.name}
              defaultValue={choice.id}
              defaultChecked={checked(choice)}
              data-label={toLabelCase(choice.text)}
            />
            <label htmlFor={field.name + key + i}>{choice.text}</label>
          </div>
        ))}
      </div>
    );
  }
  return render();
}

function Select(props) {
  var field = props.data;

  return (
    <>
      <select
        className="form-control"
        id={field.name}
        name={field.name}
        data-label={toLabelCase(field.label)}
        defaultValue={field.value}
        style={INPUT_STYLE}
      >
        {field.choices.map((choice) => (
          <option key={Math.random()} value={choice.id}>
            {choice.value}
          </option>
        ))}
      </select>
    </>
  );
}

function Separator(props) {
  function render() {
    const style = {
      width: "50%",
      margin: "auto",
      border: "solid 0.5px #DDD",
      marginTop: 30,
      marginBottom: 30,
    };
    return <div style={style}></div>;
  }
  return render();
}

function OneToOne(props) {
  const id = Math.random();
  const inline = props.data.value[0];
  const initial = inline.fields
    ? inline.fields[0]
    : inline.fieldsets[0].fields[0][0];

  function renderInfo() {
    return (
      !props.data.required && (
        <div id={"info-" + id}>
          <Info
            data={{
              text: "Esta informação é opcional. Controle seu preenchimento com o botão ao lado.",
            }}
          >
            <Button
              primary
              icon="pen-clip"
              onClick={() => showForm(true)}
              id={"show-" + id}
              display={initial.value ? "none" : "inline"}
            />
            <Button
              primary
              icon="trash"
              onClick={() => showForm(false)}
              id={"hide-" + id}
              display={initial.value ? "inline" : "none"}
            />
          </Info>
        </div>
      )
    );
  }

  function showForm(display) {
    const widget = document.querySelector("input[name=" + initial.name + "]");
    const form = document.getElementById("inline-form-" + id);
    const showButton = document.getElementById("show-" + id);
    const hideButton = document.getElementById("hide-" + id);
    form.style.display = display ? "block" : "none";
    showButton.style.display = display ? "none" : "inline";
    hideButton.style.display = display ? "inline" : "none";
    if (display) {
      if (widget.value === "") widget.value = 0;
      else widget.value = -parseInt(widget.value);
    } else {
      if (parseInt(widget.value) == 0) widget.value = "";
      else widget.value = -parseInt(widget.value);
    }
  }

  function renderForm() {
    const style = {
      display: initial.value ? "block" : "none",
    };
    if (props.data.required) {
      style.display = "block";
      if (initial.value === "") initial.value = 0;
    }
    return (
      <div
        className="fieldset-inline-forms"
        style={style}
        id={"inline-form-" + id}
      >
        {props.data.value.map(function (form) {
          return <FormContent key={Math.random()} data={form} />;
        })}
      </div>
    );
  }

  function render() {
    const style = { margin: 0 };
    return (
      <div className="form-fieldset">
        <h2 style={style}>{props.data.label}</h2>
        {renderInfo()}
        {renderForm()}
      </div>
    );
  }
  return render();
}

function OneToMany(props) {
  var next = 0;
  const id = Math.random();

  if (props.data.template == null) {
    props.data.template = props.data.value.pop();
  }

  function renderForm(form, addButtonDisplay) {
    const i = next;
    next += 1;
    return (
      <div
        key={Math.random()}
        style={{ display: "block" }}
        id={"form-" + i + "-" + id}
      >
        <FormContent data={form} />
        <div style={{ textAlign: "center", marginTop: 10, marginBottom: 10 }}>
          <Button
            primary
            icon="plus"
            onClick={() => addItem()}
            id={"extra-add-" + i + "-"}
            display={addButtonDisplay}
          />
          <Button
            primary
            icon="trash"
            onClick={() => removeItem(i)}
            display="inline"
          />
        </div>
      </div>
    );
  }

  function checkMessageDisplay() {
    const visible = visibleItems();
    const display = visible.length > 0 ? "none" : "inline";
    document.getElementById("add-" + id).style.display = display;
    for (var i = 0; i < next; i++) {
      var div = document.getElementById("extra-add-" + i + "-");
      div.style.display = "none";
    }
    if (visible.length > 0) {
      var div = document.getElementById(
        "extra-add-" + visible[visible.length - 1] + "-"
      );
      div.style.display = "inline";
    }
  }

  function addItem() {
    checkMessageDisplay();
    var form = JSON.parse(JSON.stringify(props.data.template));
    if (form.fields) {
      form.fields.map(function (field) {
        field.name = field.name.replace("__n__", "__" + next + "__");
      });
      form.fields[0].value = 0;
    } else {
      form.fieldsets.map(function (fieldet) {
        fieldet.fields.map(function (row) {
          row.map(function (field) {
            field.name = field.name.replace("__n__", "__" + next + "__");
          });
          row[0].value = 0;
        });
      });
    }
    ReactDOM.createRoot(
      document.getElementById(id).appendChild(document.createElement("div"))
    ).render(renderForm(form, "inline"));
    setTimeout(checkMessageDisplay, 100);
  }

  function removeItem(i) {
    const inline = props.data.template;
    const initial = inline.fields
      ? inline.fields[0]
      : inline.fieldsets[0].fields[0][0];
    const name = initial.name.replace("__n__", "__" + i + "__");
    const widget = document.querySelector("input[name=" + name + "]");
    if (parseInt(widget.value) == 0) widget.value = "";
    else widget.value = -parseInt(widget.value);
    document.getElementById("form-" + i + "-" + id).style.display = "none";
    checkMessageDisplay();
  }

  function visibleItems() {
    var items = [];
    for (var i = 0; i < next; i++) {
      if (
        document.getElementById("form-" + i + "-" + id).style.display == "block"
      )
        items.push(i);
    }
    return items;
  }

  function renderInfo() {
    return (
      <div id={"info-" + id}>
        <Info
          data={{
            text: "Clique no botão abaixo para adicionar um registro.",
          }}
        >
          <Button
            primary
            icon="add"
            onClick={() => addItem()}
            id={"add-" + id}
            display={props.data.value.length > 0 ? "none" : "inline"}
          />
        </Info>
      </div>
    );
  }

  function render() {
    const style = { margin: 0 };
    return (
      <div className="form-fieldset">
        <h2 style={style}>{props.data.label}</h2>
        <div>{false && JSON.stringify(props.data.value)}</div>
        <div id={id} className="fieldset-inline-forms">
          {renderInfo()}
          {props.data.value.map(function (form, i) {
            return renderForm(
              form,
              i == props.data.value.length - 1 ? "inline" : "none"
            );
          })}
        </div>
      </div>
    );
  }
  return render();
}

function FormContent(props) {
  function renderField(field) {
    return field.type == "inline" ? (
      (field.max == field.min) == 1 ? (
        <OneToOne key={Math.random()} data={field} />
      ) : (
        <OneToMany key={Math.random()} data={field} />
      )
    ) : (
      <Field key={Math.random()} data={field} />
    );
  }
  function render() {
    if (props.data.fields) {
      return (
        <div className="form-fields">
          {props.data.fields.map((field) => renderField(field))}
        </div>
      );
    } else {
      return props.data.fieldsets.map((fieldset) => (
        <div key={Math.random()} className="form-fieldset">
          {fieldset.type == "inline" ? (
            renderField(fieldset)
          ) : (
            <>
              <h2>{fieldset.title}</h2>
              <div className="fieldset-fields">
                {fieldset.fields.map((list) => (
                  <div key={Math.random()}>
                    {list.map((field) => (
                      <div
                        key={Math.random()}
                        style={{
                          width: 100 / list.length + "%",
                          display:
                            field.type == "hidden" ? "none" : "inline-block",
                        }}
                      >
                        {renderField(field)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      ));
    }
  }
  return render();
}

function Form(props) {
  const id = Math.random();

  function getTitle() {
    const style = { margin: 0 };
    return <h1 style={style}>{props.data.title}</h1>;
  }

  function renderInstruction() {
    return props.data.info && <Instruction data={{ text: props.data.info }} />;
  }

  function getDisplay() {
    if (props.data.display) {
      return (
        <>
          {props.data.display.map((data) => (
            <ComponentFactory key={Math.random()} data={data} />
          ))}
          <div style={{ marginTop: 30 }}></div>
        </>
      );
    }
  }

  function getFields() {
    return <FormContent data={props.data} />;
  }

  function getButtons() {
    return (
      <div style={{ marginTop: 20, textAlign: "right" }}>
        <Button onClick={cancel} label="Cancelar" default display="inline" />
        <Button
          onClick={submit}
          label="Enviar"
          primary
          display="inline"
          icon="chevron-right"
          spin
        />
      </div>
    );
  }

  function render() {
    //<Icons />
    return (
      <form
        id={id}
        action={props.data.url}
        style={{
          margin: "auto",
          width: props.data.width,
          backgroundColor: "white",
        }}
      >
        <div>{false && JSON.stringify(props.data)}</div>
        <div style={{ padding: 20 }}>
          {getTitle()}
          {renderInstruction()}
          {getDisplay()}
          {getFields()}
          {getButtons()}
        </div>
      </form>
    );
  }

  function cancel() {
    closeDialog();
  }

  function submit(e) {
    e.preventDefault();
    var form = document.getElementById(id);
    var data = new FormData(form);
    request(
      "POST",
      props.data.url,
      function callback(data) {
        if (e.target.dataset.spinning) {
          e.target.querySelector("i.fa-spin").style.display = "none";
          e.target.querySelector(
            "i.fa-" + e.target.dataset.spinning
          ).style.display = "inline-block";
        }
        if (data.type == "response") {
          closeDialog();
          reloadState();
          return response(data);
        } else {
          var message = data.text;
          console.log(data);
          Object.keys(data.errors).map(function (k) {
            if (k == "__all__") {
              message = data.errors[k];
            } else {
              const div = document.getElementById(k + "_error");
              div.querySelector("span").innerHTML = data.errors[k];
              div.style.display = "block";
            }
          });
          showMessage(message, true);
        }
      },
      data
    );
  }

  return render();
}

export { Field, Form, Selector };
export default Form;
