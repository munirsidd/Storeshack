function openNav() {
  document.getElementById("mySidebar").style.width = "175px";
  document.getElementById("main").style.marginLeft = "175px";
}

function closeNav() {
  document.getElementById("mySidebar").style.width = "0";
  document.getElementById("main").style.marginLeft= "0";
}

function myFunction() {
  document.getElementById("myDropdown").classList.toggle("show");
}

