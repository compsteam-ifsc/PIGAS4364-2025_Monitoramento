const getAction = document.getElementById("proLogin");

getAction.addEventListener("submit", async function(event) {
    event.preventDefault();

    const username = document.getElementById("loginName").value;
    const password = document.getElementById("loginPassword").value;

    const response = await fetch("http://localhost:8080/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user: username,
            pass: password
        })
    });

    const result = await response.text();

    if (result === "Login OK") {
        alert("Entrou!");
        window.location.href = "http://localhost:8080/dashboard";
    } else {
        alert(result);
    }
});