/*
    Settings.js
*/

import AbstractView from "./AbstractView.js"

export default class extends AbstractView{
    // Call the abstract function.
    constructor(){
        super();
        this.setTitle("Settings");
    }

    async getHTML(){
        return `
            <p>W-wait. No! STOP! DON'T ENTER THIS PAGE!!!</p>
            <img src="/static/assets/gif1.gif" alt="gif1 location... I don't have a good alt">
        `;
    }
}