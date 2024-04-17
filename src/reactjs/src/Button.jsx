import { Icon, Spin } from "./Icon";
import toLabelCase from "./Utils";

function Button({ id, onClick, icon, label, display, primary, compact, spin }) {
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
      padding: 12,
      textDecoration: "none",
      whiteSpace: "nowrap",
      borderRadius: 5,
      margin: 5,
      cursor: "pointer",
      display: display || "block",
      width: "fit-content",
      textWrap: "nowrap",
    };
    if (primary) {
      style.backgroundColor = "#1351b4";
      style.color = "white";
    } else {
      style.border = "solid 1px #1351b4";
      style.color = "#1351b4";
    }
    return (
      <a
        id={id}
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
