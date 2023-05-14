var i = 0;
var txt = "'If you find the right job you will never have to work a day in your life' --Will Rogers";
var speed = 120;

function typeWriter() {
if (i < txt.length) {
    document.getElementById("demo").innerHTML += txt.charAt(i);
    i++;
    setTimeout(typeWriter, speed);
}
}
setTimeout(window.onload = typeWriter, 1000);
