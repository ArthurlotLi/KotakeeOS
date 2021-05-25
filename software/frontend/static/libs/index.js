/*
    index.js
    Homepage setup.
*/

import Dashboard from "./views/Dashboard.js";
import Posts from "./views/Posts.js";
import Settings from "./views/Settings.js";

// Navigation function. Use the standard history API so as
// to make it so that we can navigate through our website 
// without reloading. 
const navigateTo = url => {
    history.pushState(null,null,url);
    router();
}

// Router function to load the contents of all views. 
// Asynchronous to allow for views to be loaded in
// irrelevant orders (loading things before displaying
// the actual page, for example.)
const router = async () =>{
    // Define objects for our paths for simplicity.
    const routes = [
        { path: "/", view: Dashboard },
        { path: "/posts", view: Posts },
        { path: "/settings", view: Settings }
    ];

    // Method to each route for potential match. Loop through
    // each route and return a new object for each route.
    // Return new object if the route matches or not.
    // Utilize the standard location.pathname call
    // to figure out where we are. 
    const potentialMatches = routes.map(route => {
        return {
            route: route,
            isMatch: location.pathname === route.path // boolean for if we are on this page.
        };
    });

    // Get the match using the find() with .isMatch set to true. 
    let match = potentialMatches.find(potentialMatch => potentialMatch.isMatch);

    // If no match (unknown url), use the default. 
    if(!match){
        match = {
            route: routes[0],
            isMatch: true // Important to point the user back.  
        }
    }

    // As the route object view attribute is an object, assign it.
    const view = new match.route.view();

    // Get the view's contents using the defined function. Make sure
    // to call await as it is an async method. 
    document.querySelector("#app").innerHTML = await view.getHTML();

    console.log("Test.")
};

// Faciliate basic history functionality. Call router instead of
// default behavior, so don't actually refresh the website.
window.addEventListener("popstate", router);

// Once the entire dom has loaded up, run the initial function.
document.addEventListener("DOMContentLoaded", ()=> {

    // On click. 
    document.body.addEventListener("click", e => {
        // Override default following data-link behaviour. 
        if (e.target.matches("[data-link]")){
            e.preventDefault();
            navigateTo(e.target.href);
        }
    })

    router();
})