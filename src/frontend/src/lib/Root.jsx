

import { useState, useEffect } from 'react'
import Form from './Form'

function Root(props){
    switch(props.data.type) {
        case 'form':
            return <Form data={props.data}/>
        default:
            return <div>{JSON.stringify(props.data)}</div>
    }
}

export default Root
