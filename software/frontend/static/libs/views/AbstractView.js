/*
    AbstractView.js
    Basic inherited class for all views ("pages") of the application.
*/

export default class {
    constructor(){

    }

    // Simply pass the title of current view as the title of the page 
    // (since we're a single page application).
    setTitle(title){
        document.title = "Silver: " + title;
    }

    // For the abstract view, return nothing. Whenever we create a
    // view, we will be extending this abstract view to override
    // this. Async in case it's loaded server side. 
    async getHTML(){
        return ""; // Nothing. 
    }
}