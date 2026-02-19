async function uploadImage() {
    const fileInput = document.getElementById("imageInput");

    if (!fileInput.files[0]) {
        alert("Please select an image.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Get selected languages
    const selected = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
        .map(cb => cb.value);

    if (selected.length === 0) {
        alert("Please select at least one language.");
        return;
    }

    const languagesParam = selected.join(",");

    const response = await fetch(
        `http://127.0.0.1:8000/generate/?languages=${languagesParam}`,
        {
            method: "POST",
            body: formData
        }
    );

    const data = await response.json();

    // Build dynamic result HTML
    let resultHTML = `<h3>English:</h3> ${data.english}<hr/>`;

    for (const [lang, translation] of Object.entries(data.translations)) {
        resultHTML += `<h3>${lang.toUpperCase()}:</h3> ${translation}<br/>`;
    }

    document.getElementById("result").innerHTML = resultHTML;
}
