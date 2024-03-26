

import { useState, useEffect } from 'react'
import {toLabelCase} from './Utils';

const INPUT_TYPES = ["text", "password", "email", "number", "date", "datetime-regional",  "file", "image", "range", "search", "tel", "time", "url", "week", "hidden", "color"]


function formChange(form, url){
    var data = new FormData(form);
    request('POST', url, formControl, data);
}
function formHide(name){
    if(name){
        var fieldset = document.querySelector(".form-fieldset."+name);
        if(fieldset) fieldset.style.display = 'none';
        var field = document.querySelector(".form-group."+name);
        if(field) field.style.display = 'none';
    }
}
function formShow(name){
    if(name){
        var fieldset = document.querySelector(".form-fieldset."+name);
        if(fieldset) fieldset.style.display = 'block';
        var field = document.querySelector(".form-group."+name);
        if(field) field.style.display = 'inline-block';
    }
}
function formValue(name, value){
    var group = document.querySelector(".form-group."+name);
    var widget = group.querySelector('*[name="'+name+'"]');
    if(widget.tagName == "INPUT"){
        widget.value = value;
    } else {
        if(widget.tagName == "SELECT"){
            if(widget.style.display!="none"){
                widget.dispatchEvent(new CustomEvent('customchange', {detail: {value:value}}));
            } else {
                for (var i = 0; i < widget.options.length; i++) {
                    if (widget.options[i].value == value) {
                        widget.selectedIndex = i;
                        break;
                    }
                }
            }
        }
    }
}
function formControl(controls){
    if(controls){
        for (var i = 0; i < controls.hide.length; i++) formHide(controls.hide[i]);
        for (var i = 0; i < controls.show.length; i++) formShow(controls.show[i]);
        for (var k in controls.set) formValue(k, controls.set[k]);
    }
}


function Field(props){
    const id = props.data.name+Math.random();

    function get_label(){
        return <label>{props.data.label}</label>
    }
    function get_input(){
        if(INPUT_TYPES.indexOf(props.data.type)>=0) return <InputField data={props.data}/>
        else if(props.data.type=='choice' && Array.isArray(props.data.choices)) return <Select data={props.data}/>
        else if(props.data.type=='choice') return <Selector data={props.data}/>
        else if(props.data.type=='decimal') return <InputField data={props.data}/>
        else if(props.data.type=='boolean') return <Boolean data={props.data}/>
        else return <span>{props.data.name}</span> 
    }
    function render(){
        return <div id={id} className={'form-group '+props.data.name}>
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

    function onBlur(e){
        formChange(e.target.closest('form'), props.data.onchange)
    }

    function render(){
        var type = props.data.type;
        if(type=='datetime') type = 'datetime-regional'
        if(type=='decimal') type = 'text'
        return (
            <input
                className={"form-control "+className}
                type={type} name={props.data.name}
                id={id} defaultValue={props.data.value}
                data-label={toLabelCase(props.data.label)}
                readOnly={props.data.read_only}
                onBlur={props.data.onchange ? onBlur : null}
            />
        )
    }

    return render()
}

function Selector(props){
    var initial = []
    if(Array.isArray(props.data.value)){
        props.data.value.forEach(function(option, i) {
            initial.push({id:option.id, value:option.label})
        })
    } else if(props.data.value!=null) {
        initial.push({id:props.data.value.id, value:props.data.value.label})
    }
    const id = props.data.name;
    const id2 = props.data.name+'input';
    const multiple = Array.isArray(props.data.value);
    const [options, setOptions] = useState([]);
    const [selections, setSelections] = useState(initial);
    const [seaching, setSearching] = useState(false);


    useEffect(()=>{
        document.getElementById(id).addEventListener('customchange',function(e){
            select(e.detail.value)
        });
    }, [])

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
        if(multiple){
            var value = [];
            selections.forEach(function(option){value.push(option.id)});
        } else if (props.data.value) {
            var value = props.data.value;
        }
        const style = {display: "block"}
        return (
            <select id={id} name={props.data.name} multiple={multiple} readOnly value={value} style={style}>
                {selections.map((option) => (
                    <option key={Math.random()} value={option.id}>{option.value}</option>
                ))}
            </select>
        )
    }

    function getSelector(){
        const ul = {padding: 0, margin: 0, border: "solid 1px #CCC", width: 255}
        const li = {cursor: "pointer", padding: 5}
        const defaultValue = !multiple && initial.length>0 && initial[0]['value'] || '';
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

    function select(value){
        setSearching(false)
        const input = document.getElementById(id2);
        if(multiple){
            if(Array.isArray(value)){
                for(var i=0; i<value.length; i++) selections.push(value[i]);
            } else {
                selections.push(value);
            }
            input.value = ''
        } else {
            while(selections.length > 0) selections.pop()
            selections.push(value)
            input.value = value['value']
        }
        if(props.data.onchange) formChange(input.closest('form'), props.data.onchange);
        console.log(...selections)
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

function Boolean(props){
    var field = props.data;
    field['choices'] = [{id:true, text:"Sim"}, {id:false, text:"Não"}];
    return <Radio data={field}/>
}

function Radio(props){
    var key = Math.random();
    var field = props.data;

    function checked(choice){
        if(field.value!=null){
            if(field.value == choice.id){
                return true;
            } else {
                return field.value.id == choice.id
            }
        } else {
            return false;
        }
    }

    function toogle(id){
        var radio = document.getElementById(id);
        if(field['checked']) radio.checked = false;
    }

    function ischecked(id){
        var radio = document.getElementById(id);
        field['checked'] = radio.checked;
    }

    function render(){
        return (
            <div className="radio-group">
                {field.choices.map((choice, i) => (
                  <div key={key+i}>
                    <input id={field.name+key+i} type="radio" name={field.name} defaultValue={choice.id} defaultChecked={checked(choice)} data-label={toLabelCase(choice.text)} onClick={function(){toogle(field.name+key+i)}} onMouseEnter={function(){ischecked(field.name+key+i)}}/>
                    <label htmlFor={field.name+key+i}>{choice.text}</label>
                  </div>
                ))}
            </div>
        )
    }
    return render()
}

function Checkbox(props){
    var key = Math.random();
    var field = props.data;
    function checked(choice){
        var check = false;
        if(field.value){
            for(var i=0; i<field.value.length; i++){
                var value = field.value[i];
                if(value == choice.id){
                    check = true;
                } else if(value.id == choice.id){
                    check = true;
                }
            }
        }
        return check;
    }

    function render(){
        return (

            <div className="checkbox-group">
                {field.choices.map((choice, i) => (
                  <div key={key+i}>
                    <input id={field.name+key+i} type="checkbox" name={field.name} defaultValue={choice.id} defaultChecked={checked(choice)} data-label={toLabelCase(choice.text)}/>
                    <label htmlFor={field.name+key+i}>{choice.text}</label>
                  </div>
                ))}
            </div>
        )
    }
    return render()
}

function Select(props){
    var field = props.data;

    function clear(){

    }

    return (
        <>
        <select className="form-control" id={field.name} name={field.name} data-label={toLabelCase(field.label)} defaultValue={field.value}>
            {field.choices.map((choice) => (
              <option key={Math.random()} value={choice.id}>{choice.value}</option>
            ))}
        </select>
        <i className="fa-solid fa-chevron-down clearer" onClick={clear}/>
        </>
    )
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
        request('POST', props.data.url, function callback(data){
            button.innerHTML = label;
            if(data.type=="message") alert(data.text);
            else console.log(data);
        }, data);
    }

    return render()
}


export default Form