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


let livreBox = livre + "-rectangle";
let livreStart = livre;
if (showBox) {
    livreStart = livreBox;
}

document.querySelector("#pdfViewer").src = `static/pdf/${livreStart}.pdf#page=${numPage}`;

function createTable(json) {
	result = document.querySelector("#resultHistory");

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

function sendButtonInit(sendButton) {
	sendButton.addEventListener("click", (_) => {
		const tableData = getTableData();
		fetch("/edit", {
			method: "POST",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/json",
			},
			body: JSON.stringify(tableData),
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
			let sens = event.target.sens;
			let langue = event.target.langue;
			let text = event.target.innerText;
			updateTableData(sens, langue, text);
		}
	});
}

function getTableData() {
	const tableData = [];
	const tableRows = document.querySelectorAll("#table tr");

	tableRows.forEach((row) => {
		const rowData = [];
		const cells = row.querySelectorAll("td");

		cells.forEach((cell) => {
			const sens = cell.getAttribute("sens");
			const langue = cell.getAttribute("langue");
			const text = cell.innerText;
			rowData.push({ sens, langue, text });
		});

		tableData.push(rowData);
	});

	return tableData;
}

function updateTableData(sens, langue, text) {
	const tableData = getTableData();
	let updated = false;

	for (let i = 0; i < tableData.length; i++) {
		const rowData = tableData[i];
		for (let j = 0; j < rowData.length; j++) {
			const cellData = rowData[j];
			if (cellData.sens === sens && cellData.langue === langue) {
				tableData[i][j].text = text;
				updated = true;
				break;
			}
		}
		if (updated) {
			break;
		}
	}

	return tableData;
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
		popupError.innerText = `L'extention ${extention} n'est pas pris en charge.`;
		popupError.hidden = false;
		setTimeout((_) => {
			popupError.hidden = true;
		}, 5000);
	}
});

listernerOnchangeTable(document.querySelector("#table"), editButton);

sendButtonInit(sendButton);

checkBox.addEventListener("click", changePdfBox);
document.querySelector("#labelBox").addEventListener("click", (_) => {
    checkBox.checked = !checkBox.checked;
    changePdfBox();
});