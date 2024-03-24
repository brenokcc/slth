

import { useState, useEffect } from 'react'
import {toLabelCase} from './Utils';

function Field(props){
    function get_label(){
        return <label>{props.data.label}</label>
    }
    function get_input(){
        switch(props.data.type) {
            case 'text':
                return <InputField data={props.data}/>
            case 'choice':
                return <SelectField data={props.data}/>
            default:
                return <span>{props.data.name}</span> 
        }
    }
    function render(){
        return <div className='form-field'>
            {get_label()}
            {get_input()}
        </div>
    }
    return render()
}

function InputField(props){
    var className = ""
    const id = props.data.name+Math.random();

    if(props.data.mask=='decimal'){
        className = 'decimal';
        if(props.data.value) props.data.value = Math.round(parseFloat(props.data.value)).toFixed(2).replace('.', ',');
    }

    useEffect(()=>{
        function inputHandler(masks, max, event) {
            var c = event.target;
            var v = c.value.replace(/\D/g, '');
            var m = c.value.length > max ? 1 : 0;
            VMasker(c).unMask();
            VMasker(c).maskPattern(masks[m]);
            c.value = VMasker.toPattern(v, masks[m]);
        }
        if(props.data.mask){
            var input = document.getElementById(id);
            if(props.data.mask=='decimal'){
                VMasker(input).maskMoney({precision: 2, separator: ',', delimiter: '.'}); // unit: 'R$', suffixUnit: 'reais', zeroCents: true
            } else if(props.data.mask.indexOf('|')>0){
                var masks = props.data.mask.split('|');
                VMasker(input).maskPattern(masks[0]);
                input.addEventListener('input', inputHandler.bind(undefined, masks, 14), false);
            } else {
                VMasker(input).maskPattern(props.data.mask);
            }
        }
    }, [])

    function render(){
        return <input className={"form-control "+className} type={props.data.type} name={props.data.name} id={id} defaultValue={props.data.value} data-label={toLabelCase(props.data.label)} readOnly={props.data.read_only}/>
    }

    return render()
}

function SelectField(props){
    var initial = []
    if(Array.isArray(props.data.value)){
        props.data.value.forEach(function(option, i) {
            initial.push({id:option.id, value:option.label})
        })
    } else if(props.data.value!=null) {
        initial.push({id:props.data.value.id, value:props.data.value.label})
    }
    const id = props.data.name+Math.random();
    const id2 = props.data.name+Math.random();
    const multiple = Array.isArray(props.data.value);
    const [options, setOptions] = useState([]);
    const [selections, setSelections] = useState(initial);
    const [seaching, setSearching] = useState(false);

    function getSelections(){
        if(multiple){
            const style1 = {padding: 5, display: "inline"}
            const style2 = {cursor: "pointer"}
            return (
                <div>
                    {selections.map((option, i) => (
                        <div key={Math.random()} style={style1}>
                            {option.value}
                            <span onClick={()=>remove(i)} style={style2}>[X]</span>
                        </div>
                    ))}
                </div>
            )
        }
    }

    function getSelect(){
        return (
            <select id={id} name={props.data.name} multiple={multiple}>
                {selections.map((option) => (
                    <option selected key={Math.random()} value={option.id}>{option.value}</option>
                ))}
            </select>
        )
    }

    function getSelector(){
        const ul = {padding: 0, margin: 0, border: "solid 1px #CCC", width: 255}
        const li = {cursor: "pointer", padding: 5}
        const defaultValue = initial.length>0 && initial[0]['value'] || '';
        return (
            <div>
                <input id={id2} type="text" className="form-control" onFocus={search} onChange={search} defaultValue={defaultValue}></input>
                {seaching &&
                    <ul style={ul}>
                        {false && options.length==0 && <li>Nenhuma opção encontrada.</li>}
                        {options.map((option) => (
                            <li key={Math.random()} onClick={()=>select(option)}  style={li}>{option.value}</li>
                        ))}
                    </ul>
                }
            </div>
        )
    }

    function search(e){
        setSearching(true);
        request('GET', props.data.choices+'&q='+e.target.value, function callback(options){setOptions(options)});
    }

    function select(option){
        const input = document.getElementById(id2);
        setSearching(false)
        if(multiple){
            selections.push(option);
            input.value = ''
        } else {
            selections = [option]
            input.value = option['value']
        }
        setSelections(selections);
    }

    function remove(i){
        setSelections(selections.slice(0, i).concat(selections.slice(i+1)));
    }

    function render(){
        return <>
            {getSelections()}
            {getSelect()}
            {getSelector()}
        </>
    }

    return render()
}

function Textarea(props){
    function render(){
        return (
            <textarea className="form-control" id={props.data.name} name={props.data.name} data-label={toLabelCase(props.data.label)} style={{height: 200}} defaultValue={props.data.value || ""}></textarea>
        )
    }
}

function Form(props){
    const id = Math.random();

    function getTitle(){
        return <h1>{props.data.title}</h1>
    }

    function getButtons(){
        return (
            <div className="right">
                <a className="btn" onClick={cancel} data-label={toLabelCase("Cancelar")}>
                    Cancelar
                </a>
                <a className="btn submit primary" onClick={submit} data-label={toLabelCase("Enviar")}>
                    Enviar
                </a>
            </div>
        )
    }

    function getFields(){
        return (
            <div className='form-fields'>
                {props.data.fields.map((field) => (
                    <Field key={Math.random()} data={field}/>
                ))}
            </div>
        )
    }

    function render(){
        return (
            <form id={id}>
                <p>{JSON.stringify(props.data)}</p>
                {getTitle()}
                {getFields()}
                {getButtons()}
            </form>
        )
    }

    function cancel(){

    }

    function submit(e){
        e.preventDefault();
        var form = document.getElementById(id);
        var data = new FormData(form);
        for (var pair of data.entries()) {
            console.log(pair[0]+ ', ' + pair[1]); 
        }
        var button = form.querySelector(".btn.submit");
        var label = button.innerHTML;
        button.innerHTML = 'Aguarde...'
    }

    return render()
}

export default Form