import { useState, useEffect } from "react";
import { toLabelCase } from "./Utils";
import { Icon, Icons } from "./Icon";
import { closeDialog, openDialog } from "./Modal";
import { ComponentFactory } from "./Factory";
import { showMessage } from "./Message";

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
const INPUT_STYLE = { padding: 10, border: "solid 1px #CCC", borderRadius: 5 };
const BUTTON_STYLE = {
  padding: 10,
  border: "solid 1px #CCC",
  borderRadius: 5,
  marginLeft: 10,
  cursor: "pointer",
};

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

function Field(props) {
  const id = props.data.name + Math.random();

  function renderLabel() {
    const style = { fontWeight: props.data.required ? "bold" : "normal" };
    return <label style={style}>{props.data.label}</label>;
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
    const style = { color: "red", display: "none" };
    return <div style={style} id={props.data.name + "_error"}></div>;
  }

  function render() {
    const style = {
      display: "flex",
      flexDirection: "column",
      paddingBottom: 10,
    };
    return (
      <div id={id} className={"form-group " + props.data.name} style={style}>
        {renderLabel()}
        {renderInput()}
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

  function render() {
    var type = props.data.type;
    if (type == "datetime") type = "datetime-regional";
    if (type == "decimal") type = "text";
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
        style={INPUT_STYLE}
      />
    );
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
  const id2 = props.data.name + "input";
  const multiple = Array.isArray(props.data.value);
  const [seaching, setSearching] = useState(false);
  const [options, setOptions] = useState([]);

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
      const style2 = { cursor: "pointer" };
      return (
        <div>
          {select == null &&
            initial.map((option, i) => (
              <div key={Math.random()} style={style1}>
                {option.value}
                <span onClick={() => remove(i)} style={style2}>
                  [X]
                </span>
              </div>
            ))}
          {select != null &&
            Array.from(select.options).map((option, i) => (
              <div key={Math.random()} style={style1}>
                {option.innerHTML}
                <span onClick={() => remove(i)} style={style2}>
                  [X]
                </span>
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
    const ul = {
      padding: 0,
      margin: 0,
      border: "solid 1px #CCC",
      marginTop: -1,
      borderRadius: 5,
      maxHeight: 150,
      overflowY: "scroll",
    };
    const li = { cursor: "pointer", padding: 10 };
    const defaultValue =
      (!multiple && initial.length > 0 && initial[0]["value"]) || "";
    return (
      <>
        <input
          id={id2}
          type="text"
          className="form-control"
          onFocus={(e) => {
            e.target.select();
            search(e);
          }}
          onChange={search}
          defaultValue={defaultValue}
          style={INPUT_STYLE}
        ></input>
        {seaching && (
          <ul style={ul} onMouseLeave={(e) => setSearching(false)}>
            {false && options.length == 0 && <li>Nenhuma opção encontrada.</li>}
            {options.map((option) => (
              <li
                key={Math.random()}
                onClick={() => {
                  setSearching(false);
                  select(option);
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

  function search(e) {
    setSearching(true);
    request(
      "GET",
      props.data.choices + "&q=" + e.target.value,
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

  function clear() {}

  return (
    <>
      <select
        className="form-control"
        id={field.name}
        name={field.name}
        data-label={toLabelCase(field.label)}
        defaultValue={field.value}
      >
        {field.choices.map((choice) => (
          <option key={Math.random()} value={choice.id}>
            {choice.value}
          </option>
        ))}
      </select>
      <i className="fa-solid fa-chevron-down clearer" onClick={clear} />
    </>
  );
}

function Form(props) {
  const id = Math.random();

  function getTitle() {
    return <h1>{props.data.title}</h1>;
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

  function getButtons() {
    return (
      <div className="right" style={{ marginTop: 20, textAlign: "right" }}>
        <a
          className="btn"
          onClick={cancel}
          data-label={toLabelCase("Cancelar")}
          style={BUTTON_STYLE}
        >
          Cancelar
        </a>
        <a
          className="btn submit primary"
          onClick={submit}
          data-label={toLabelCase("Enviar")}
          style={BUTTON_STYLE}
        >
          Enviar
        </a>
      </div>
    );
  }

  function getFields() {
    return (
      <div className="form-fields">
        {props.data.fields.map((field) => (
          <Field key={Math.random()} data={field} />
        ))}
      </div>
    );
  }

  function render() {
    //<Icons />
    return (
      <form id={id}>
        <div>{false && JSON.stringify(props.data)}</div>
        {getTitle()}
        {getDisplay()}
        {getFields()}
        {getButtons()}
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
    // for (var pair of data.entries()) {
    //   console.log(pair[0] + ", " + pair[1]);
    // }
    var button = form.querySelector(".btn.submit");
    var label = button.innerHTML;
    button.innerHTML = "Aguarde...";
    request(
      "POST",
      props.data.url,
      function callback(data) {
        button.innerHTML = label;
        if (data.type == "message") {
          closeDialog();
          showMessage(data.text);
        } else {
          var message = data.text;
          console.log(data);
          Object.keys(data.errors).map(function (k) {
            if (k == "__all__") {
              message = data.errors[k];
            } else {
              const div = document.getElementById(k + "_error");
              div.innerHTML = data.errors[k];
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

export { Form };
export default Form;
