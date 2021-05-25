/*
    Dashboard.js
*/

import AbstractView from "./AbstractView.js"

export default class extends AbstractView{
    // Call the abstract function.
    constructor(){
        super();
        this.setTitle("Dashboard");
    }

    async getHTML(){
        return `
            <p>Welcome to Project Silver. This is a personal website for myself (I wonder if you can guess my name) currently hosted out of San Jose. It will initially be filled with nonsense data and will never be truly filled with proper data until I end up migrating it onto AWS. A lot of fun, no? Well, in the meanwhile, I can put some nonsense on here to fill it out a little more. Obviously this was made using a tutorial - it's been a very long time since I created a web application and I'm a little rusty :)</p>
            <img src="/static/assets/image1.png" alt="image1 location... I don't have a good alt">
        `;
    }
}