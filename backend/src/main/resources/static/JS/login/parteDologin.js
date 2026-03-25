function mostrarRegistro() {
    document.getElementById("login").classList.add("hidden");
    document.getElementById("register").classList.remove("hidden");
}

function mostrarLogin() {
    document.getElementById("register").classList.add("hidden");
    document.getElementById("login").classList.remove("hidden");
}

async function registrar() {
    const user = document.getElementById("registerUser").value.trim();
    const pass = document.getElementById("registerPass").value.trim();

    if (user === "" || pass === "") {
        alert("Preencha todos os campos!");
        return;
    }

    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user: user,
                pass: pass
            })
        });

        const result = await response.text();

        alert(result);

        if (result === "Registrado com sucesso") {
            document.getElementById("registerUser").value = "";
            document.getElementById("registerPass").value = "";
            mostrarLogin();
        }

    } catch (error) {
        console.error("Erro ao registrar:", error);
        alert("Erro ao conectar com o servidor.");
    }
}

async function login() {
    const user = document.getElementById("loginUser").value.trim();
    const pass = document.getElementById("loginPass").value.trim();

    if (user === "" || pass === "") {
        alert("Preencha todos os campos!");
        return;
    }

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user: user,
                pass: pass
            })
        });

        const result = await response.text();

        if (result === "Login OK") {
            alert("Login realizado com sucesso!");
            window.location.href = "/home"; // troque depois se quiser
        } else {
            alert(result);
        }

    } catch (error) {
        console.error("Erro ao fazer login:", error);
        alert("Erro ao conectar com o servidor.");
    }
}