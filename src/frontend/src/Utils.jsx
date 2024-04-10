
function toLabelCase(text){
    if(text!=null) text = text.toString().replace('-', '').normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace('_', '').toLowerCase();
    return text;
}

export default toLabelCase
export {toLabelCase}
