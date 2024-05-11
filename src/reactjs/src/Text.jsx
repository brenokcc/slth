import StyleSheet from "./StyleSheet";


function Text(props){
    const style = {color: props.data.color}
    function render(){
         return <div style={style}>{props.data.text}</div>
    }
    return render();
}

export {Text};
export default Text;
