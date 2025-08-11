import { Icon } from "./Icon.jsx";

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

function ThemeToggle(props){

  function isDark(){
    return document.cookie.indexOf("dark") > 0 
  }

  function onClick(e){
    const theme = isDark() ? "light" : "dark";
    document.cookie = "theme="+theme+"; expires=Thu, 01 Jan 2030 00:00:00 UTC; path=/;";
    document.location.reload();
  }

  function render(){
    return 0 ? <Icon
      onClick={onClick}
      icon={isDark() ? "sun" : "moon"}
      style={{ cursor: "pointer", color: Theme.colors.primary }}
    /> : null;
  }

  return render()
}

export { Theme, Color, ThemeToggle };
export default Theme;
