import { StyleSheet } from "./StyleSheet";

function ZoomMeet(props){
    StyleSheet(`
    .container {
        position: relative;
        width: 100%;
        overflow: hidden;
        padding-top: 56.25%; /* 16:9 Aspect Ratio */
      }
      .responsive-iframe {
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        width: 100%;
        height: 100%;
        border: none;
      }
    `)
    function render(){
        const url = `/zoom/?number=${props.data.number}&password=${props.data.password}&name=${props.data.name}`;
        return <div className="container"> 
            <iframe onLoad={onLoad} className="responsive-iframe" src={url}></iframe>
        </div>
    }

    function onLoad(e){
        if(e.target.contentWindow.location.href.indexOf("/zoom/") < 0){
            e.target.parentNode.style.display = "none";
        }
    }

    return render();
}

export {ZoomMeet};
export default ZoomMeet;