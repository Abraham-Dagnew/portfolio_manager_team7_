function getContainer() {

    let container = document.getElementById("toastContainer");

    if (!container) {

        container = document.createElement("div");

        container.id = "toastContainer";

        document.body.appendChild(container);
    }

    return container;
}


export function showToast(
    message,
    type = "success",
    duration = 3000
) {

    const container = getContainer();


    const toast = document.createElement("div");


    toast.className = `toast ${type}`;


    toast.textContent = message;


    container.appendChild(toast);


    // Animate in
    requestAnimationFrame(() => {
        toast.classList.add("show");
    });


    // Remove after duration
    setTimeout(() => {

        toast.classList.remove("show");


        setTimeout(() => {

            toast.remove();

        }, 250);


    }, duration);

}