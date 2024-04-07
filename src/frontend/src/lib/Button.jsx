import { Icon } from "./Icon";

function Button({ id, onClick, icon, label, display, primary, compact }) {
  function renderContent() {
    if (icon) {
      if (compact || !label) {
        return <Icon icon={icon} />;
      } else {
        return (
          <>
            <Icon icon={icon} style={{ paddingRight: 10 }} />
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
        onClick={(e) => {
          e.preventDefault();
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
