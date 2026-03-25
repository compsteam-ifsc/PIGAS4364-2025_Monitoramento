function MostrarRegistro() {
    document.getElementById("login").classList.add("hidden");
    document.getElementById("register").classList.remove("hidden");
}

function mostrarlogin() {
    document.getElementById("register").classList.add("hidden");
    document.getElementById("login").classList.remove("hidden");
}

function registrar() {
    const user = document.getElementById("registerUser").value;
    const pass = document.getElementById("registerPass").value;

    if (user === "" || pass === "") {
        alert("Preencha tudo!");
        return;
    }

   
}


function login() {
    const user = document.getElementById("loginUser").value;
    const pass = document.getElementById("loginPass").value;
    
}