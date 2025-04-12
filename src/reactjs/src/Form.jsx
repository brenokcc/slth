import { React } from "react";
import ReactDOM from "react-dom/client";
import { useState, useEffect } from "react";
import { toLabelCase } from "./Utils";
import { closeDialog } from "./Modal";
import { ComponentFactory } from "./Root.jsx";
import { showMessage, Info, Instruction } from "./Message";
import { request, appurl, store } from "./Request.jsx";
import { reloadState } from "./Reloader.jsx";
import { Icon } from "./Icon.jsx";
import { Button } from "./Button.jsx";
import { Action } from "./Action.jsx";
import { Theme } from "./Theme";
import { Scheduler } from "./Library.jsx";

const INPUT_TYPES = [
  "text",
  "password",
  "email",
  "number",
  "date",
  "datetime-local",
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
const INPUT_STYLE = {
  padding: 15,
  border: "var(--input-border)",
  borderRadius: 5,
  backgroundColor: "var(--input-background)",
};

function serialize_form(form, input_name){
  const data = new FormData(form);
  for (let [name, value] of Array.from(data.entries())){
    const input = form[name];
    if (value !== '' && value!== null) continue;
    if (input_name == name) continue;
    if (input.tagName == "SELECT" && value !== '') continue;
    if (input.tagName == undefined && value !== '') continue;
    if (input.type == "radio" && value !== '') continue;
    if (input.type == "checkbox" && value !== '') continue;
    data.delete(name);
  };
  return new URLSearchParams(data).toString()
}

function add_form_params(url, form, input_name){
  //return url;
  const sep = url.indexOf("?") < 0 ? "?" : "&";
  const extra = serialize_form(form, input_name);
  url = url + (extra ? sep + extra : "");
  return url;
}

function isImage(url) {
  if (url) {
    const extensions = [".png", ".jpeg", ".jpeg", ".gif"];
    for (var i = 0; i < extensions.length; i++) {
      if (url.toLowerCase().indexOf(extensions[i]) > 0) return true;
    }
  }
}

function formChange(input, url) {
  request("GET", add_form_params(url, input.closest("form"), input.name), formControl);
}
function formHide(name) {
  if (name) {
    var fieldset = document.querySelector(".form-fieldset." + name);
    if (fieldset) fieldset.style.display = "none";
    var group = document.querySelector(".form-group." + name);
    if (group) group.style.display = "none";
    var field = document.querySelector(".form-field." + name);
    if (field) field.style.display = "none";
  }
}
function formShow(name) {
  if (name) {
    var fieldset = document.querySelector(".form-fieldset." + name);
    if (fieldset) fieldset.style.display = "block";
    var group = document.querySelector(".form-group." + name);
    if (group) group.style.display = "block";
    var field = document.querySelector(".form-field." + name);
    if (field) field.style.display = "block";
  }
}
function formReload(name){
  const funcname = 'reload-'+name+'-field';
  if(window[funcname]) window[funcname]();
}
function formValue(name, value) {
  var group = document.querySelector(".form-group." + name);
  var elements = group.querySelectorAll('*[name="' + name + '"]');
  if(elements.length > 1){
    elements.forEach(function(widget) {
      if(value == null) {
        widget.checked = false;
      } else {
        if(value.id != null){
          widget.checked = widget.value.toString() == value.id.toString()
        } else {
          widget.checked = widget.value.toString() == value.toString()
        }
      }
    });
  } else {
    const widget = elements[0];
    if (widget.tagName == "INPUT" || widget.tagName == "TEXTAREA") {
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
}
function formControl(controls) {
  if (controls) {
    for (var i = 0; i < controls.hide.length; i++) formHide(controls.hide[i]);
    for (var i = 0; i < controls.show.length; i++) formShow(controls.show[i]);
    for (var i = 0; i < controls.reload.length; i++) formReload(controls.reload[i]);
    for (var k in controls.set) formValue(k, controls.set[k]);
  }
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
      <div style={style} id={props.id} className="error">
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
    if (props.data.action) {
      props.data.action.icon = null;
      props.data.action.modal = true;
      props.data.action.urlfunc = function(){
        return add_form_params(props.data.action.url, document.getElementById(id).closest("form"));
      }
    }
    return (
      <div style={style}>
        <label className="bold">
          {props.data.label} {props.data.label && props.data.required ? "*" : ""}
        </label>
        {props.data.action && (
          <Action data={props.data.action} style={{ padding: 0, margin:0 }} tabIndex="-1" />
        )}
      </div>
    );
  }
  function renderInput() {
    if (props.data.type == "datetime") props.data.type = "datetime-local";

    if (INPUT_TYPES.indexOf(props.data.type) >= 0)
      return <InputField data={props.data} />;
    else if (props.data.type == "choice" && Array.isArray(props.data.choices))
      return props.data.pick ? (
        Array.isArray(props.data.value) ? (
          <Checkbox data={props.data} />
        ) : (
          <Radio data={props.data} />
        )
      ) : (
        <Select data={props.data} />
      );
    else if (props.data.type == "choice") {
      return props.data.pick ? (
        Array.isArray(props.data.value) ? (
          <Checkbox data={props.data} />
        ) : (
          <Radio data={props.data} />
        )
      ) : (
        <Selector data={props.data} />
      );
    } else if (props.data.type == "decimal")
      return <InputField data={props.data} />;
    else if (props.data.type == "boolean") return <Boolean data={props.data} />;
    else if (props.data.type == "textarea")
      return <Textarea data={props.data} />;
    else if (props.data.type == "scheduler") {
      props.data.scheduler.input_name = props.data.name;
      return <Scheduler data={props.data.scheduler} />;
    } else return <span>{props.data.name}</span>;
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
      width: "calc(100%-5px)",
    };
    return (
      <div id={id} style={style} className={"form-group "+props.data.name}>
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
    formChange(e.target, props.data.onchange);
  }

  function onChange(e) {
    if (props.data.type == "file") {
      if (e.target.files) {
        let file = e.target.files[0];
        var reader = new FileReader();
        reader.onload = function (event) {
          if (isImage(file.name)) {
            const DISPLAY_ID = "display" + id;
            var img = document.createElement("img");
            img.id = e.target.id + "img";
            img.style.width = "200px";
            img.style.display = "block";
            img.style.margin = "auto";
            img.style.marginTop = "20px";
            img.onload = function (event2) {
              const ratio =
                props.data.width > props.data.height
                  ? props.data.width / img.width
                  : props.data.height / img.height;
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
                //e.target.blob = blob;
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(new File([blob], file.name));
                e.target.files = dataTransfer.files;
              });
              var div = document.getElementById(DISPLAY_ID);
              if (div == null) {
                div = document.createElement("div");
                div.id = DISPLAY_ID;
              } else {
                div.removeChild(div.childNodes[0]);
              }
              div.appendChild(img);
              e.target.parentNode.appendChild(div);
            };
            img.src = event.target.result;
          }
          const info = document.getElementById("fileinfo" + id);
          var size = file.size / 1024;
          if (size < 1024) size = parseInt(size) + " Kb";
          else size = (size / 1024).toFixed(2) + " Mb";
          info.innerHTML = file.name + " / " + size;
          if (
            props.data.max_size &&
            file.size / 1024 / 1024 > props.data.max_size
          ) {
            alert(
              "O limite de tamanho é " +
                props.data.max_size +
                "Mb. O arquivo informado possui " +
                size +
                ". Por favor, adicione um arquivo menor."
            );
          }
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
      const style = {
        alignContent: "center",
        minHeight: 75,
        padding: 5,
        maxWidth: "100%",
        margin: "auto",
      };
      var accept = null;
      if (props.data.extensions && props.data.extensions.length > 0) {
        accept = props.data.extensions
          .map((extension) => "." + extension)
          .join(", ");
      }
      return (
        <>
          <div
            style={{
              display: window.innerWidth < 800 ? "block" : "flex",
              justifyContent: "space-between",
              backgroundColor: "rgba(15, 145, 210, 0.05)",
              border: "1px dashed rgba(15, 145, 210, 0.4)",
              borderRadius: 10,
              textAlign: "center",
            }}
          >
            <div style={style}>
              <Icon
                icon="cloud-upload"
                style={{ fontSize: "2.5rem", color: Theme.colors.primary }}
              />
            </div>
            <div style={style}>
              {props.data.value && isImage(props.data.value) && (
                <div style={{ textAlign: "center" }}>
                  <img src={props.data.value} height={50} />
                </div>
              )}
              {props.data.value && !isImage(props.data.value) && (
                <div style={{ textAlign: "center" }}>{props.data.value}</div>
              )}
              Selecione um arquivo clicando no botão ao lado.
              <div className="bold" id={"fileinfo" + id}>
                O arquivo
                {props.data.max_size &&
                  "deve possuir até " + props.data.max_size + " Mb e "}
                deve ter extensão{" "}
                {props.data.extensions
                  .map((extension) => "." + extension)
                  .join(" ou ")}
                .
              </div>
            </div>
            <div style={style} align="center">
              <Button
                label="Selecionar Arquivo"
                onClick={() => document.getElementById(id).click()}
              ></Button>
            </div>
          </div>
          <input
            className={"form-control " + className}
            type={type}
            name={props.data.name}
            id={id}
            data-label={toLabelCase(props.data.label)}
            readOnly={props.data.read_only}
            onBlur={props.data.onchange ? onBlur : null}
            onChange={onChange}
            style={{ zIndex: "-1", marginTop: -20 }}
            accept={accept}
          />
        </>
      );
    } else {
      var style = INPUT_STYLE;
      if (type == "color") {
        style = { ...INPUT_STYLE };
        style.width = "100%";
        style.height = 47.5;
      }
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
          style={style}
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
  if (props.data.id == null) props.data.id = Math.random();
  if (props.data.id2 == null) props.data.id2 = props.data.id + "__autocomplete";
  const id = props.data.id;
  const id2 = props.data.id2;

  const multiple = Array.isArray(props.data.value);
  const [seaching, setSearching] = useState(false);
  const [options, setOptions] = useState(null);
  var choosing = false;
  let timeout;

  useEffect(() => {
    select(initial, true);
    document.getElementById(id).addEventListener("customchange", function (e) {
      select(e.detail.value);
      const element = document.getElementById(props.data.name);
      if(element) reactTriggerChange(element);
    });
  }, []);

  function renderSelections() {
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

  function renderSelect() {
    return (
      <select
        id={id}
        name={props.data.name}
        multiple={multiple}
        readOnly
        style={{ display: "contents" }}
      ></select>
    );
  }

  function renderSelector() {
    const style = { ...INPUT_STYLE, ...(props.style || {}) };
    const ul = {
      padding: 0,
      margin: 0,
      border: "solid 1px #d9d9d9",
      marginTop: -1,
      borderRadius: 5,
      maxHeight: 150,
      overflowY: "auto",
      zIndex: 99999,
    };
    ul.position = "absolute";
    ul.backgroundColor = "var(--default-background)";
    const widget = document.getElementById(id2);
    if (props.data.icon) style.paddingLeft = 30;
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
      var top = rect.top + rect.height;
      var left = rect.left;
      if (dialog) {
        const rect2 = dialog.getBoundingClientRect();
        top = top - rect2.top;
        left = left - rect2.left;
      } else {
        top += window.scrollY;
        left += window.scrollX;
      }
      ul.width = rect.width;
      ul.top = top;
      ul.left = left;
    }
    const li = { cursor: "pointer", padding: 10 };
    const defaultValue =
      (!multiple && initial.length > 0 && initial[0]["value"]) || "";
    return (
      <>
        {props.data.icon && (
          <Icon
            icon={props.data.icon}
            style={{ position: "absolute", margin: 13, color: "#d9d9d9" }}
          />
        )}
        <input
          id={id2}
          name={props.data.name + "__autocomplete"}
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
          data-label={toLabelCase(props.data.label)}
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
                className="autocomplete-item"
                data-label={toLabelCase(option.value)}
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
      if (!choosing) hide(e);
    }, 250);
  }

  function hide(e) {
    const widget = document.getElementById(id);
    if (widget) {
      const input = document.getElementById(id2);
      if (!multiple) {
        if (
          widget.options.length > 0 &&
          input.value != widget.options[0].innerHTML
        ) {
          widget.innerHTML = "";
          input.value = "";
          setSearching(false);
          if (props.data.onchange) formChange(input, props.data.onchange);
        }
      }
      if (e.target.tagName == "UL") {
        setSearching(false);
      } else {
        if (!choosing) setSearching(false);
      }
    }
  }

  function search(e) {
    clearTimeout(timeout);
    timeout = setTimeout(function () {
      const form = e.target.closest("form");
      const sep = props.data.choices.indexOf("?") < 0 ? "?" : "&";
      setSearching(true);
      request(
        "GET",
        add_form_params(props.data.choices + sep + "term=" + e.target.value, form),
        function callback(options) {
          setOptions(options);
        }
      );
    }, 1000);
  }

  function select(value, initializing = false) {
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
      if(value){
        if (multiple) {
          widget.innerHTML += `<option selected value="${value.id}">${value.value}</option>`;
          input.value = "";
        } else {
          widget.innerHTML = `<option selected value="${value.id}">${value.value}</option>`;
          input.value = value.value;
        }
      } else {
        widget.innerHTML = '';
        input.value = "";
      }
    }
    if (props.data.onchange && !initializing) {
      formChange(input, props.data.onchange);
    }
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
        {renderSelections()}
        {renderSelect()}
        {renderSelector()}
      </>
    );
  }

  return render();
}

function Textarea(props) {
  function render() {
    var style = { ...INPUT_STYLE };
    style.height = 100;
    return (
      <textarea
        id={props.data.name}
        name={props.data.name}
        data-label={toLabelCase(props.data.label)}
        style={style}
        defaultValue={props.data.value || ""}
        className="form-control"
      ></textarea>
    );
  }
  return render();
}

function Boolean(props) {
  return <Radio data={props.data} />;
}

function Radio(props) {
  const [choices, setChoices] = useState(props.data.choices);
  
  var key = Math.random();
  var field = props.data;

  function checked(choice) {
    if (field.value !=null && field.value.toString() == choice.id.toString()) return true;
    if (field.value !=null && field.value.id !=null && field.value.id.toString() == choice.id.toString()) return true;
    if (field.value == null && choice.id.toString() == "null") return true;
    return false;
  }

  function toogle(id) {
    var radio = document.getElementById(id);
    if (field["checked"]) radio.checked = false;
    if (props.data.onchange) {
      formChange(radio, props.data.onchange);
    }
  }

  function ischecked(id) {
    var radio = document.getElementById(id);
    field["checked"] = radio.checked;
  }

  function render() {
    window['reload-'+field.name+'-field'] = function(){
      request(
        "GET",
        add_form_params(props.data.pick, document.querySelector(".radio-group."+field.name).closest("form")),
        function callback(choices) {
          setChoices(choices);
        }
      );
    }
    return choices.length > 0 ? (
      <div className={"radio-group "+field.name}>
        {choices.map(
          (choice, i) =>
            (choice.id || choice.id === false) && (
              <div
                key={key + i}
                style={{
                  paddingTop: 10,
                  display: "inline-block",
                  marginRight: 25,
                  width: window.innerWidth > 800 ? "auto" : "100%"
                }}
              >
                <input
                  id={field.name + key + i}
                  type="radio"
                  name={field.name}
                  defaultValue={choice.id}
                  defaultChecked={checked(choice)}
                  data-label={toLabelCase(choice.value)}
                  onClick={function () {
                    toogle(field.name + key + i);
                  }}
                  onMouseEnter={function () {
                    ischecked(field.name + key + i);
                  }}
                />
                <label htmlFor={field.name + key + i}>{choice.value}</label>
              </div>
            )
        )}
      </div>
    ) : (
      <div className={"radio-group empty "+field.name}>
        <Info data={{text: "Nenhuma opção disponível para seleção.",}}></Info>
      </div>
    );
  }
  return render();
}

function Checkbox(props) {
  const [choices, setChoices] = useState(props.data.choices);
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

  function onClick(e) {
    if (props.data.onchange) {
      formChange(e.target, props.data.onchange);
    }
  }

  function render() {
    window['reload-'+field.name+'-field'] = function(){
      request(
        "GET",
        add_form_params(props.data.pick, document.querySelector(".checkbox-group."+field.name).closest("form")),
        function callback(choices) {
          setChoices(choices);
        }
      );
    }
    return choices.length > 0 ? (
      <div className={"checkbox-group "+field.name}>
        {choices.map((choice, i) => (
          (choice.id || choice.id === false) && (
            <div
              key={key + i}
              style={{ paddingTop: 10, display: "inline-block", marginRight: 25, width: window.innerWidth > 800 ? "auto" : "100%" }}
            >
              <input
                id={field.name + key + i}
                type="checkbox"
                name={field.name}
                onClick={onClick}
                defaultValue={choice.id}
                defaultChecked={checked(choice)}
                data-label={toLabelCase(choice.value)}
              />
              <label htmlFor={field.name + key + i}>{choice.value}</label>
            </div>
          )
        ))}
      </div>
    ) : (
      <div className={"checkbox-group empty "+field.name}>
        <Info data={{text: "Nenhuma opção disponível para seleção.",}}></Info>
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
      <div className={"form-fieldset "+props.data.name}>
        <h2 style={style} data-label={toLabelCase(props.data.label)}>
          {props.data.label}
        </h2>
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
            text: 'Clique no botão com o ícone de "+" para adicionar e com o ícone da "lixeira" para remover.',
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
      <div className={"form-fieldset "+props.data.name}>
        <h2 style={style} data-label={toLabelCase(props.data.label)}>
          {props.data.label}
        </h2>
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
  useEffect(() => {
    if (props.data.controls) {
      formControl(props.data.controls);
    }
  }, []);

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
      return props.data.fields.length > 0 ? (
        <div className="form-fields default-fieldset">
          {props.data.fields.map((field) => renderField(field))}
        </div>
      ) : null;
    } else {
      return props.data.fieldsets.map((fieldset) => (
        <div key={Math.random()} className={"form-fieldset "+fieldset.name}>
          {fieldset.type == "inline" ? (
            renderField(fieldset)
          ) : (
            <>
              <h2
                data-label={toLabelCase(fieldset.title)}
                style={{ margin: 0 }}
              >
                {fieldset.title}
              </h2>
              {fieldset.fields.map((list) => (
                <div key={Math.random()}>
                  {list.map((field) => (
                    <div
                      className={"form-field " + field.name}
                      key={Math.random()}
                      style={{
                        verticalAlign: "bottom",
                        width: (window.innerWidth > 600 ? 100 / list.length : 100) + "%",
                        display:
                          field.type == "hidden" ? "none" : "inline-block",
                      }}
                    >
                      {renderField(field)}
                    </div>
                  ))}
                </div>
              ))}
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

  useEffect(() => {
    if(props.data.autosubmit){
      setInterval(submit, props.data.autosubmit*1000)
    }
  }, []);

  function renderTitle() {
    const style = { margin: 0, color: Theme.colors.primary};
    return <h1 style={style}>{props.data.title}</h1>;
  }

  function renderInstruction() {
    return props.data.info && <Instruction data={{ text: props.data.info }} />;
  }

  function renderDisplay() {
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

  function renderFields() {
    return <FormContent data={props.data} />;
  }

  function renderButtons() {
    return (
      <div style={{ marginTop: 20, textAlign: "right" }}>
        <Button onClick={cancel} label="Cancelar" default display="inline" />
        <Button
          onClick={submit}
          label={props.data.submit_label}
          primary
          display="inline"
          icon={props.data.submit_icon}
          spin
        />
      </div>
    );
  }

  function renderOutput() {
    return <div id="output" style={{ marginTop: 30 }}></div>;
  }

  function renderImage(){
    if(props.data.image){
      return <div style={{margin: "auto", width: "100%", textAlign:"center"}}><img src={props.data.image}></img></div>
    }
  }

  function render() {
    //<Icons />
    return (
      <form
        id={id}
        className={props.data.key}
        action={props.data.url}
        style={{
          margin: "auto",
          
        }}
        method={props.data.method}
      >
        <div>{false && JSON.stringify(props.data)}</div>
        <div style={{ padding: 5 }}>
          {renderTitle()}
          {renderImage()}
          {renderInstruction()}
          {renderDisplay()}
          {renderFields()}
          {renderButtons()}
          {renderOutput()}
        </div>
      </form>
    );
  }

  function cancel() {
    closeDialog();
  }

  function submit(e) {
    if(e) e.preventDefault();
    var url = props.data.url;
    var form = document.getElementById(id);
    var data = new FormData(form);
    if (form.method.toUpperCase() == "GET") {
      const sep = url.indexOf("?") >= 0 ? "&" : "?";
      url =
        url +
        sep +
        "form=" +
        props.data.key +
        "&" +
        new URLSearchParams(data).toString();
      data = null;
    }
    if(props.data.autosubmit && e == null) url += "&autosubmit=1";
    request(
      form.method.toUpperCase(),
      url,
      function callback(data) {
        form
          .querySelectorAll(".error")
          .forEach((el) => (el.style.display = "none"));
        if (e && e.target.dataset.spinning) {
          e.target.querySelector("i.fa-spin").style.display = "none";
          e.target.querySelector(
            "i.fa-" + e.target.dataset.spinning
          ).style.display = "inline-block";
        }
        if (data.type == "response") {
          if (data.store) store(data.store);
          if (data.redirect && data.redirect.length > 2) {
            if (data.message) localStorage.setItem("message", data.message);
            document.location.href = appurl(data.redirect);
          } else {
            if (data.message) showMessage(data.message);
            if (data.task){
              const tmp = e.target.innerHTML;
              e.target.innerHTML = "Aguarde... (0%)"
              function updateProgress(){
                request('GET', '/api/job/progress/'+data.task+'/', function callback(task) {
                    if(task==null || task.progress == 100){
                      e.target.innerHTML = tmp;
                    } else {
                      e.target.innerHTML = "Aguarde... ("+(task.progress || 0)+"%)";
                      setTimeout(updateProgress, 5000);
                    }
                })
              }
              updateProgress();
            } else {
              if (data.redirect == ".."){
                if(document.getElementsByTagName("dialog").length == 0) history.back();
                else closeDialog();
              }
              if (data.redirect == "."){
                if(document.getElementsByTagName("dialog").length == 0) form.reset();
                else closeDialog();
              }
              if (data.dispose) form.style.display = "none";
              reloadState();
            }
          }
        } else if (data.type == "error") {
          var message = data.text;
          console.log(data);
          Object.keys(data.errors).map(function (k) {
            if (k == "__all__") {
              message = data.errors[k];
            } else {
              const div = form.querySelector("#" + k + "_error");
              if (div == null){
                message = k + ":" +data.errors[k];
              } else {
                div.querySelector("span").innerHTML = data.errors[k];
                div.style.display = "block";
              }
            }
          });
          showMessage(message, true);
        } else if (data.type != "redirect")  {
          const output = document.querySelector("#output");
          output.innerHTML = "";
          ReactDOM.createRoot(
            output.appendChild(document.createElement("div"))
          ).render(<ComponentFactory data={data} />);
        }
      },
      data
    );
  }

  return render();
}

export { Field, Form, Selector, add_form_params };
export default Form;
