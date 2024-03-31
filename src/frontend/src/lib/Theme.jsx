const COLORS = {
  primary: "blue",
  success: "green",
  warning: "orange",
  info: "blue",
  danger: "red",
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

export { COLORS, Color };
export default COLORS;
