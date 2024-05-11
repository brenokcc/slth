
import { useEffect } from "react";
const CLASSES = {}

function kebabize(str){
    return str.replace(/[A-Z]+(?![a-z])|[A-Z]/g, ($, ofs) => (ofs ? "-" : "") + $.toLowerCase());
}
 function cssize(style){
    return Object.keys(style).map((k)=>kebabize(k)+ ": " + style[k]).join('; ');
 }
 
 function Style(name, style){
    if (CLASSES[name] == null){
        CLASSES[name] = name +" {" + cssize(style) + "}";
    }
 }

function StyleSheet(props) {
    useEffect(() => {
        alert(1);
        const text = Object.keys(CLASSES).map((k)=>CLASSES[k]).join('\n')
        console.log("Creating style sheet...")
        console.log(text);
        document.body.appendChild(
            Object.assign(document.createElement("style"), {
                textContent: text
            })
        );
    }, []);
    return;
}

export {Style, StyleSheet};
export default Style;