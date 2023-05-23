const urlParam = new URLSearchParams(window.location.search);
const livre = urlParam.get("livre");
const numPage = parseInt(urlParam.get("page"));
const showBox = urlParam.get("showBox") === "true";
const langue = urlParam.get("langue");
const sens = urlParam.get("sens");
const ALLOWED_EXTENTION = ["mp3", "wav"];
const MAX_NUM_PAGE = 274;

let saveChange = []
let editButton = document.querySelector("#edit");
let sendButton = document.querySelector("#send");
let checkBox = document.querySelector("#showBox");
editButton.hidden = false;
sendButton.hidden = false;


let livreBox = livre + "-rectangle";
let livreStart = livre;
if (showBox) {
    livreStart = livreBox;
}

document.querySelector("#pdfViewer").src = `static/pdf/${livreStart}.pdf#page=${numPage}`;

function createTable(data) {
    // Retrieve the table from the DOM
    const table = document.querySelector("#resultHistory");
	const head = document.querySelector("#resulthead");


    // Get the last row from data
    let lastRow = data[data.length - 1];

    // Create a new row
	let th = document.createElement("tr");
    let tr = document.createElement("tr");

	th.appendChild("Livre");
	th.appendChild("Langue");
	th.appendChild("Mot");
	th.appendChild("Page");

	head.appendChild(th);

    // Create and append 'livre' cell
    let tdLivre = document.createElement("td");
    tdLivre.textContent = livre;
    tr.appendChild(tdLivre);

    // Create and append 'langue' cell
    let tdLangue = document.createElement("td");
    tdLangue.textContent = langue;
    tr.appendChild(tdLangue);

    // Create and append 'renvoyer' cell (the second item in the lastRow)
    let tdRenvoyer = document.createElement("td");
    tdRenvoyer.textContent = lastRow[1]; // accessing the second element of the array
    tr.appendChild(tdRenvoyer);

    // Create and append 'numPage' cell
    let tdNumPage = document.createElement("td");
    tdNumPage.textContent = numPage;
    tr.appendChild(tdNumPage);

    // Append the row to the table
    table.appendChild(tr);
}



function sendButtonInit(sendButton) {
	sendButton.addEventListener("click", (_) => {
		let dataToSend = Array.from(document.querySelectorAll("#resultHistory tr")).map(tr => {
			let date = tr.children[0].innerText;
			let value = tr.children[1].innerText;
			return [date, value];
		});
		fetch("/edit", {
			method: "POST",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/json",
			},
			body: JSON.stringify(dataToSend),
		});
	});
}


function listernerOnchangeTable(table, editButton) {
	editButton.onclick = (_) => {
		for (let td of document.querySelectorAll("td")) {
			td.contentEditable = true;
			for (let elem of td.children) {
				if (elem.tagName === "BUTTON") {
					elem.remove();
				}
			}
		}
	};
	table.addEventListener("keyup", (event) => {
		if (event.target.tagName.toLowerCase() === "td") {
			let rowIndex = event.target.parentElement.rowIndex;
			let columnIndex = event.target.cellIndex;
			let text = event.target.innerText;
			if (columnIndex === 0) {
				// Update date
				saveChange[rowIndex][0] = text;
			} else {
				// Update value
				saveChange[rowIndex][1] = text;
			}
		}
	});
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
.then((resp) => {
    return resp.json();
})
.then((json) => {
    console.log(json);
    createTable(json);
    saveChange = json.slice();  // Copy the json data to saveChange
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
		popupError.innerText = `L'extention ${extention} n'est pas pris en charge.`;
		popupError.hidden = false;
		setTimeout((_) => {
			popupError.hidden = true;
		}, 5000);
	}
});

function changePdfBox(bool) {
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

listernerOnchangeTable(document.querySelector("#table"), editButton);

sendButtonInit(sendButton);

checkBox.addEventListener("click", changePdfBox);
document.querySelector("#labelBox").addEventListener("click", (_) => {
    checkBox.checked = !checkBox.checked;
    changePdfBox();
});