import { Icon, Spin } from "./Icon";
import toLabelCase from "./Utils";
import { Theme } from "./Theme";
import StyleSheet from "./StyleSheet";

function Button({ id, onClick, icon, label, display, primary, compact, spin }) {
  StyleSheet(`
    .button{
      padding: 12px;
      text-decoration: none;
      white-space: nowrap;
      border-radius: 5px;
      margin: 5px;
      cursor: pointer;
      width: fit-content;
      text-wrap: nowrap;
    }
  `)
  
  function renderContent() {
    if (icon) {
      if (compact || !label) {
        return <Icon icon={icon} />;
      } else {
        return (
          <>
            <Spin style={{ marginRight: 10, display: "none" }} />
            <Icon icon={icon} style={{ marginRight: 10 }} />
            {label || ""}
          </>
        );
      }
    } else {
      return label;
    }
  }

  function render() {
    const style = {
      display: display || "block",
    };
    if (primary) {
      style.backgroundColor = Theme.colors.primary;
      style.color = "white";
    } else {
      style.border = "solid 1px " + Theme.colors.primary;
      style.color = Theme.colors.primary;
    }
    return (
      <a
        id={id}
        className="button"
        style={style}
        data-label={toLabelCase(label || icon)}
        onClick={(e) => {
          e.preventDefault();
          if (icon && spin) {
            e.target.dataset.spinning = icon;
            e.target.querySelector("i.fa-spin").style.display = "inline-block";
            e.target.querySelector("i.fa-" + icon).style.display = "none";
          }
          onClick(e);
        }}
      >
        {renderContent()}
      </a>
    );
  }
  return render();
}

export { Button };
export default Button;
