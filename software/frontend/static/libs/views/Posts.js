/*
    Posts.js
*/

import AbstractView from "./AbstractView.js"

export default class extends AbstractView{
    // Call the abstract function.
    constructor(){
        super();
        this.setTitle("Posts");
    }

    async getHTML(){
        return `
            <p>Some useful wallpapers for my own use. All non-confidential and considered public, of course.</p>
            <img src="/static/assets/image2.jpg" alt="image2 location... I don't have a good alt">
            <img src="/static/assets/image3.jpg" alt="image3 location... I don't have a good alt">
            <img src="/static/assets/image4.jpg" alt="image4 location... I don't have a good alt">
        `;
    }
}