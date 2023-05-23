const urlParam = new URLSearchParams(window.location.search);
const livre = urlParam.get("livre");
const numPage = parseInt(urlParam.get("page"));
const showBox = urlParam.get("showBox") === "true";
const langue = urlParam.get("langue");
const sens = urlParam.get("sens");
const ALLOWED_EXTENTION = ["mp3", "wav"];
const MAX_NUM_PAGE = 274;

let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let checkBox = document.querySelector("#showBox");
editButton.hidden = false;
sendButton.hidden = false;

let isEditing = false;

editButton.addEventListener("click", () => {
    if (!isEditing) {
        enableEditing();
        editButton.innerText = "Cancel";
    } else {
        disableEditing();
        editButton.innerText = "Edit";
    }
});

sendButton.addEventListener("click", () => {
    if (isEditing) {
        disableEditing();
        editButton.innerText = "Edit";
    }
    updateDatabase();
});

let livreBox = livre + "-rectangle";
let livreStart = livre;
if (showBox) {
    livreStart = livreBox;
}

document.querySelector("#pdfViewer").src = `static/pdf/${livreStart}.pdf#page=${numPage}`;

function createTable(json) {
    const result = document.querySelector("#resultHistory");

    let line = json[json.length - 1];
    let tr = document.createElement("tr");

    // Date
    let td = document.createElement("td");
    const date = new Date(line[0]);
    const hours = String(date.getHours()).padStart(2, "0");
    const min = String(date.getMinutes()).padStart(2, "0");
    const seconde = String(date.getSeconds()).padStart(2, "0");
    td.innerText = `${hours}:${min}:${seconde}, ${date.toLocaleDateString(
        "fr"
    )}`;
    tr.appendChild(td);

    // traduction
    td = document.createElement("td");
    td.innerText = line[1];
    tr.appendChild(td);

    result.appendChild(tr);
}

function changePdfBox() {
    if (checkBox.checked) {
        document.querySelector(
            "#pdfViewer"
        ).src = `static/pdf/${livreBox}.pdf#page=${numPage}`;
    } else {
        document.querySelector(
            "#pdfViewer"
        ).src = `static/pdf/${livre}.pdf#page=${numPage}`;
    }
}

function sendButtonInit() {
    sendButton.addEventListener("click", () => {
        updateDatabase();
    });
}

function enableEditing() {
    isEditing = true;

    const cells = document.querySelectorAll("#table td");
    cells.forEach((cell) => {
        cell.contentEditable = true;
    });
}

function disableEditing() {
    isEditing = false;

    const cells = document.querySelectorAll("#table td");
    cells.forEach((cell) => {
        cell.contentEditable = false;
    });
}

function updateDatabase() {
    const data = mapToArray();

    fetch("/edit", {
        method: "POST",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
        .then((response) => {
            if (response.ok) {
                console.log("Database updated successfully.");
            } else {
                console.error("Failed to update the database.");
            }
        })
        .catch((error) => {
            console.error("An error occurred:", error);
        });
}

function listernerOnchangeTable(table) {
    editButton.onclick = () => {
        if (!isEditing) {
            enableEditing();
            editButton.innerText = "Cancel";
        } else {
            disableEditing();
            editButton.innerText = "Edit";
        }
    };
    table.addEventListener("keyup", (event) => {
        if (event.target.tagName.toLowerCase() === "td") {
            let sens = event.target.sens;
            let langue = event.target.langue;
            let text = event.target.innerText;
            if (!saveChange.has(sens)) {
                saveChange.set(sens, new Map());
            }
            saveChange.get(sens).set(langue, text);
        }
    });
}

function mapToArray() {
    let res = [];
    for (let sens of saveChange) {
        let reelSens = sens[0];
        for (let element of sens[1]) {
            res.push(element.concat([reelSens]));
        }
    }
    return res;
}

fetch("/historyRequest", {
    method: "POST",
    headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
    },
    body: JSON.stringify({
        langue: langue,
        sens: sens,
    }),
})
    .then((resp) => resp.json())
    .then((json) => {
        createTable(json);
    });

const dragBox = document.querySelector(".drag-audio");
dragBox.addEventListener("dragenter", (_) => {
    dragBox.classList.add("drag-audio-enter");
});
dragBox.addEventListener("dragleave", (_) => {
    dragBox.classList.remove("drag-audio-enter");
});

document.addEventListener("dragover", (event) => {
    event.preventDefault();
});
document.addEventListener("drop", (event) => {
    event.preventDefault();
});

const popupError = document.querySelector("#unsupported-extention-popup");
dragBox.addEventListener("drop", (event) => {
    event.preventDefault();
    dragBox.classList.remove("drag-audio-enter");
    const file = event.dataTransfer.files[0];
    const name_split = file.name.split(".");
    const extention = name_split.pop();
    if (ALLOWED_EXTENTION.includes(extention.toLowerCase())) {
        const data = new FormData();
        data.append("file", file);
        data.append("sens", sens);
        data.append("langue", langue);
        console.log(data);
        fetch("/receiveAudio", {
            method: "POST",
            body: data,
        }).then((resp) => {
            console.log(resp);
        });
    } else {
        popupError.innerText = `L'extension ${extention} n'est pas prise en charge.`;
        popupError.hidden = false;
        setTimeout((_) => {
            popupError.hidden = true;
        }, 5000);
    }
});

listernerOnchangeTable(document.querySelector("#table"));

sendButtonInit();
checkBox.addEventListener("click", changePdfBox);
document.querySelector("#labelBox").addEventListener("click", () => {
    checkBox.checked = !checkBox.checked;
    changePdfBox();
});
