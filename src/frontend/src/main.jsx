import React from 'react'
import ReactDOM from 'react-dom/client'
import Root from './lib/Root.jsx'

const URL = document.location.pathname.replace('/app/', '/api/')

request('GET', URL, function callback(data){
    console.log(data)
    ReactDOM.createRoot(document.getElementById('root')).render(<Root data={data}/>)  
});
