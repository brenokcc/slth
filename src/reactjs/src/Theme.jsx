const Theme = {
  colors: {
    primary: "var(--primary-color)",
    success: "var(--success-color)",
    warning: "var(--warning-color)",
    info: "var(--info-color)",
    danger: "var(--danger-color)",
    highlight: "var(--highlight-color)",
    seconday: "var(--seconday-color)",
    auxiliary: "var(--auxiliary-color)",
  },
  border: {
    radius: "var(--border-radius)",
  },
  background: {
    info: "var(--info-background)",
  },
};

function Color(props) {
  function render() {
    const style = {
      width: 30,
      height: 30,
      borderRadius: "50%",
      backgroundColor: props.data.value,
    };
    return <div style={style}></div>;
  }
  return render();
}

export { Theme, Color };
export default Theme;
