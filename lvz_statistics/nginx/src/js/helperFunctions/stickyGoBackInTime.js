// When the user scrolls the page, execute myFunction
window.onscroll = function() {addStickyClass()};

// Get the navbar
let navbar = document.getElementsByClassName('go-back-in-time-graph-content')[0];

// Get the offset position of the navbar
let sticky = navbar.offsetTop;

// Add the sticky class to the navbar when you reach its scroll position. Remove "sticky" when you leave the scroll position
function addStickyClass() {
  if (window.pageYOffset >= sticky) {
    navbar.classList.add('sticky')
  } else {
    navbar.classList.remove('sticky');
  }
}